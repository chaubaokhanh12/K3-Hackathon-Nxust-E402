"""Test tầng tổng hợp — trọng tâm là guardrail neo nguồn.

Không test "câu trả lời có hay không": đó là việc của eval. Test ở đây chốt
bất biến an toàn — câu trả lời không neo được vào nguồn thì KHÔNG được trình ra.
"""

from __future__ import annotations

import pytest

from agent.synthesis import (
    INSUFFICIENT_SOURCE_TOKEN,
    build_context_block,
    build_synthesis_prompt,
    groundable_suggestions,
    synthesize_answer,
    validate_grounding,
)


class FakeGenerator:
    """Generator giả trả về đúng chuỗi được nạp sẵn."""

    model_name = "fake-model"

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.reply


def _suggestion(thread_id: str = "111", **overrides):
    base = {
        "thread_id": thread_id,
        "rank": 1,
        "title": "Phoenix không load được phần đội",
        "similarity": 88,
        "relevance": "direct",
        "excerpt": "Xoá cache rồi login lại là được.",
        "thread_url": "https://discord.com/channels/1/2/3",
        "source_tier": "VERIFIED",
        "main_answer": {
            "answer_id": "a1",
            "content": "Xoá cache trình duyệt rồi đăng nhập lại nhé.",
            "author_name": "Duy | LabCoach",
            "author_role": "LabCoach",
            "source_tier": "VERIFIED",
            "is_verified": True,
        },
        "supplementary_answer": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate_grounding
# ---------------------------------------------------------------------------


def test_accepts_answer_citing_a_known_thread() -> None:
    result = validate_grounding("Bạn xoá cache rồi login lại nhé [#111].", ["111"])
    assert result is not None
    text, cited = result
    assert cited == ["111"]
    assert "xoá cache" in text.lower()


def test_rejects_answer_without_any_citation() -> None:
    assert validate_grounding("Bạn thử khởi động lại máy xem sao.", ["111"]) is None


def test_rejects_answer_citing_a_thread_not_in_the_prompt() -> None:
    """Bịa thread_id là dấu hiệu bịa nội dung — loại cả câu trả lời."""
    assert validate_grounding("Xem thread [#999] nhé.", ["111"]) is None


def test_rejects_mixed_valid_and_invalid_citations() -> None:
    assert validate_grounding("Xoá cache [#111], rồi xem [#999].", ["111"]) is None


def test_rejects_insufficient_source_token() -> None:
    assert validate_grounding(INSUFFICIENT_SOURCE_TOKEN, ["111"]) is None


def test_rejects_empty_reply() -> None:
    assert validate_grounding("   ", ["111"]) is None


def test_deduplicates_citations_keeping_order() -> None:
    result = validate_grounding("A [#222], B [#111], C [#222].", ["111", "222"])
    assert result is not None
    assert result[1] == ["222", "111"]


# ---------------------------------------------------------------------------
# prompt building
# ---------------------------------------------------------------------------


def test_context_block_carries_verification_status() -> None:
    block = build_context_block([_suggestion()])
    assert "[#111]" in block
    assert "đã xác minh" in block
    assert "LabCoach" in block


def test_context_block_flags_unverified_community_answers() -> None:
    block = build_context_block(
        [
            _suggestion(
                main_answer={
                    "answer_id": "a2",
                    "content": "mình nghĩ tự lo á bạn",
                    "author_name": "HV24",
                    "author_role": "Learner",
                    "source_tier": "COMMUNITY_UNVERIFIED",
                    "is_verified": False,
                }
            )
        ]
    )
    assert "CHƯA xác minh" in block


def test_topic_match_is_excluded_from_the_prompt() -> None:
    """Topic match KHÔNG được vào prompt.

    Guardrail cấm trình topic match như lời giải nên nó luôn thiếu
    ``main_answer``; thứ còn lại là ``excerpt`` — vốn là CÂU HỎI của học viên
    khác. Nạp nó cho LLM sẽ sinh ra khẳng định từ một câu hỏi.
    """
    topic_match = _suggestion(
        main_answer=None,
        supplementary_answer=None,
        relevance="topic",
        excerpt="e dien form check-in xong ko thay gi het, v la e diem danh dc chua a",
    )
    assert groundable_suggestions([topic_match]) == []
    assert build_context_block(groundable_suggestions([topic_match])) == ""


def test_only_threads_with_an_answer_are_groundable() -> None:
    direct = _suggestion("111")
    topic = _suggestion("222", main_answer=None, supplementary_answer=None, relevance="topic")
    community = _suggestion(
        "333",
        main_answer=None,
        supplementary_answer={
            "answer_id": "a3",
            "content": "mình thử cách này thấy được",
            "author_name": "HV02",
            "author_role": "Learner",
            "source_tier": "COMMUNITY_UNVERIFIED",
            "is_verified": False,
        },
    )

    kept = [item["thread_id"] for item in groundable_suggestions([direct, topic, community])]
    assert kept == ["111", "333"]


def test_topic_only_result_never_reaches_the_provider() -> None:
    """Ca thật đã gây bịa: hai topic match, không lời giải nào."""
    generator = FakeGenerator("Hiện tại không có cách nào kiểm tra [#111].")
    topic_only = [
        _suggestion("111", main_answer=None, supplementary_answer=None, relevance="topic"),
        _suggestion("222", main_answer=None, supplementary_answer=None, relevance="topic"),
    ]

    assert synthesize_answer("điểm danh thế nào", topic_only, generator=generator) is None
    assert generator.calls == []


def test_citing_a_topic_match_is_rejected() -> None:
    """Thread có trong suggestions nhưng không có lời giải -> trích nó vẫn là bịa."""
    generator = FakeGenerator("Xem thêm [#222].")
    mixed = [
        _suggestion("111"),
        _suggestion("222", main_answer=None, supplementary_answer=None, relevance="topic"),
    ]

    assert synthesize_answer("phoenix lỗi", mixed, generator=generator) is None


def test_prompt_lists_allowed_thread_ids() -> None:
    prompt = build_synthesis_prompt("sao lỗi?", [_suggestion("111"), _suggestion("222")])
    assert "[#111]" in prompt and "[#222]" in prompt
    assert INSUFFICIENT_SOURCE_TOKEN in prompt


# ---------------------------------------------------------------------------
# synthesize_answer
# ---------------------------------------------------------------------------


def test_returns_payload_with_model_and_citations() -> None:
    generator = FakeGenerator("Xoá cache rồi login lại [#111].")
    result = synthesize_answer("phoenix lỗi", [_suggestion()], generator=generator)
    assert result == {
        "text": "Xoá cache rồi login lại [#111].",
        "cited_thread_ids": ["111"],
        "model": "fake-model",
    }


def test_returns_none_when_model_declares_insufficient_source() -> None:
    generator = FakeGenerator(INSUFFICIENT_SOURCE_TOKEN)
    assert synthesize_answer("câu hỏi lạ", [_suggestion()], generator=generator) is None


def test_returns_none_when_model_fabricates() -> None:
    generator = FakeGenerator("Bạn chạy `npm run reset` là xong.")
    assert synthesize_answer("phoenix lỗi", [_suggestion()], generator=generator) is None


def test_skips_provider_call_when_there_are_no_suggestions() -> None:
    generator = FakeGenerator("bất kỳ")
    assert synthesize_answer("gì đó", [], generator=generator) is None
    assert generator.calls == []

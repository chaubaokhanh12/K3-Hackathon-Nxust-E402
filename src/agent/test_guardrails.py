"""Test cho agent.guardrails — logic quyết định + validator.

Chạy: ``PYTHONPATH=src python -m pytest src/agent -q``
Không cần API key (không gọi tool thật, chỉ dùng dict mô phỏng output tool).
"""

from __future__ import annotations

import pytest

from tools.search_qa_threads.tool import (
    DIRECT_MATCH_THRESHOLD,
    TOPIC_REFERENCE_PROBLEM_THRESHOLD,
    TOPIC_REFERENCE_TOPIC_THRESHOLD,
)

#: Điểm nằm giữa hai ngưỡng: đủ để là topic reference, chưa đủ là direct match.
TOPIC_LEVEL = (TOPIC_REFERENCE_PROBLEM_THRESHOLD + DIRECT_MATCH_THRESHOLD) / 2

from agent.guardrails import (
    BUTTONS,
    MAX_MAIN_ANSWERS,
    MAX_SUGGESTED_THREADS,
    MAX_SUPPLEMENTARY_ANSWERS,
    AnswerSummary,
    BotResponse,
    ConfidenceTier,
    GuardrailViolation,
    Relevance,
    SourceTier,
    SuggestedThread,
    answer_source_tier,
    build_bot_response,
    classify_relevance,
    decide_buttons,
    decide_confidence,
    enforce,
    rank_for_display,
    select_suggestions,
    should_escalate,
    thread_source_tier,
)


# ---------------------------------------------------------------------------
# Ngưỡng đồng bộ với tools (single source of truth)
# ---------------------------------------------------------------------------


def test_thresholds_match_tools():
    """guardrails import ngưỡng từ tools -> phải khớp giá trị đặc tả."""
    from agent import guardrails as g
    assert g.DIRECT_MATCH_THRESHOLD is DIRECT_MATCH_THRESHOLD
    assert g.TOPIC_REFERENCE_PROBLEM_THRESHOLD is TOPIC_REFERENCE_PROBLEM_THRESHOLD
    assert g.TOPIC_REFERENCE_TOPIC_THRESHOLD is TOPIC_REFERENCE_TOPIC_THRESHOLD
    # Không ghim con số: ngưỡng được hiệu chỉnh lại theo thang cosine thật của
    # embedding model (xem eval/threshold_calibration.md). Chỉ ghim quan hệ.
    assert 0.0 < TOPIC_REFERENCE_PROBLEM_THRESHOLD < DIRECT_MATCH_THRESHOLD <= 1.0
    assert 0.0 < TOPIC_REFERENCE_TOPIC_THRESHOLD <= 1.0


def test_verified_roles_match_spec():
    from agent.guardrails import VERIFIED_ROLES

    assert VERIFIED_ROLES == frozenset({"Admin", "Mentor", "BTC", "LabCoach"})
    assert "Learner" not in VERIFIED_ROLES


# ---------------------------------------------------------------------------
# classify_relevance
# ---------------------------------------------------------------------------


def test_classify_direct_at_threshold():
    assert classify_relevance(DIRECT_MATCH_THRESHOLD, 0.0) is Relevance.DIRECT


def test_classify_topic_requires_both_conditions():
    assert classify_relevance(TOPIC_LEVEL, 1.0) is Relevance.TOPIC
    # thiếu topic_similarity -> loại dù problem đủ
    assert classify_relevance(TOPIC_LEVEL, 0.0) is None


def test_classify_drop_when_too_weak():
    assert classify_relevance(0.20, 0.20) is None


# ---------------------------------------------------------------------------
# source tier
# ---------------------------------------------------------------------------


def test_answer_source_tier_by_label():
    assert answer_source_tier({"verification_label": "VERIFIED"}) is SourceTier.VERIFIED
    assert (
        answer_source_tier({"verification_label": "COMMUNITY_UNVERIFIED"})
        is SourceTier.COMMUNITY_UNVERIFIED
    )


def test_answer_source_tier_fallback_on_role():
    assert (
        answer_source_tier({"author_role": "LabCoach", "is_verified": True})
        is SourceTier.VERIFIED
    )
    assert (
        answer_source_tier({"author_role": "Learner"})
        is SourceTier.COMMUNITY_UNVERIFIED
    )


def test_thread_source_tier_uses_verified_flag_first():
    assert (
        thread_source_tier({"has_verified_answer": True, "source_trust": 0.4})
        is SourceTier.VERIFIED
    )
    assert thread_source_tier({"has_verified_answer": False}) is SourceTier.COMMUNITY_UNVERIFIED


# ---------------------------------------------------------------------------
# decide_confidence
# ---------------------------------------------------------------------------


def test_confidence_high_when_direct_verified():
    assert (
        decide_confidence([{"has_verified_answer": True}], [])
        is ConfidenceTier.HIGH
    )


def test_confidence_low_when_direct_only_community():
    assert (
        decide_confidence([{"has_verified_answer": False}], [])
        is ConfidenceTier.LOW
    )


def test_confidence_low_when_only_topic():
    assert decide_confidence([], [{"problem_similarity": 0.5}]) is ConfidenceTier.LOW


def test_confidence_none_when_both_empty():
    assert decide_confidence([], []) is ConfidenceTier.NONE


# ---------------------------------------------------------------------------
# decide_buttons / should_escalate
# ---------------------------------------------------------------------------


def test_buttons_only_for_pending_high_or_low():
    assert len(decide_buttons(ConfidenceTier.HIGH, "pending")) == 2
    assert len(decide_buttons(ConfidenceTier.LOW, "pending")) == 2


def test_no_buttons_when_none():
    assert decide_buttons(ConfidenceTier.NONE, "pending") == []


def test_no_buttons_when_already_resolved_or_escalated():
    assert decide_buttons(ConfidenceTier.HIGH, "resolved") == []
    assert decide_buttons(ConfidenceTier.HIGH, "escalated") == []


def test_buttons_order_resolve_first():
    ids = [b.id for b in decide_buttons(ConfidenceTier.HIGH, "pending")]
    assert ids == ["resolve", "escalate"]
    assert {b.id for b in BUTTONS} == {"resolve", "escalate"}


def test_should_escalate_only_none():
    assert should_escalate(ConfidenceTier.NONE) is True
    assert should_escalate(ConfidenceTier.HIGH) is False


# ---------------------------------------------------------------------------
# rank_for_display — thứ tự spec §5.3
# ---------------------------------------------------------------------------


def _match(tid, problem, verified, trust=0.4):
    return {
        "thread_id": tid,
        "problem_similarity": problem,
        "source_trust": trust,
        "has_verified_answer": verified,
    }


def test_rank_direct_verified_first_then_community_then_topic():
    direct = [
        _match("d-community", 0.95, False, trust=0.40),  # direct cộng đồng
        _match("d-verified", 0.80, True, trust=0.95),  # direct đã xác minh
    ]
    topic = [
        _match("t-verified", 0.55, True, trust=0.95),  # topic đã xác minh
        _match("t-community", TOPIC_LEVEL, False, trust=0.40),  # topic cộng đồng
    ]
    ranked = rank_for_display(direct, topic)
    ids = [m["thread_id"] for _, m in ranked]
    assert ids == ["d-verified", "d-community", "t-verified", "t-community"]


# ---------------------------------------------------------------------------
# select_suggestions — chọn câu trả lời
# ---------------------------------------------------------------------------


def _detail(thread_id, answers):
    return {
        "found": True,
        "thread_id": thread_id,
        "title": f"Thread {thread_id}",
        "question": f"Câu hỏi gốc {thread_id}",
        "selected_answers": answers,
        "thread_url": f"https://discord/x/{thread_id}",
    }


def _answer(aid, role, verified, content="Nội dung giải pháp"):
    return {
        "answer_id": aid,
        "content": content,
        "author_name": f"{role}",
        "author_role": role,
        "is_verified": verified,
        "verification_label": "VERIFIED" if verified else "COMMUNITY_UNVERIFIED",
    }


def test_select_direct_picks_verified_main_plus_community_supplementary():
    ranked = [(Relevance.DIRECT, _match("d1", 0.9, True, trust=0.95))]
    details = {
        "d1": _detail(
            "d1",
            [
                _answer("a1", "LabCoach", True, "Mở terminal mới."),
                _answer("a2", "Learner", False, "Dùng file .env cũng được."),
            ],
        )
    }
    suggestions = select_suggestions(ranked, details)
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s.main_answer.source_tier is SourceTier.VERIFIED
    assert s.main_answer.content == "Mở terminal mới."
    assert s.supplementary_answer is not None
    assert s.supplementary_answer.source_tier is SourceTier.COMMUNITY_UNVERIFIED
    assert s.similarity == 90


def test_select_topic_has_no_answer():
    ranked = [(Relevance.TOPIC, _match("t1", 0.5, True))]
    suggestions = select_suggestions(ranked, {})
    s = suggestions[0]
    assert s.relevance is Relevance.TOPIC
    assert s.main_answer is None
    assert s.supplementary_answer is None


def test_select_respects_max_threads():
    ranked = [
        (Relevance.DIRECT, _match(f"d{i}", 0.9 - i * 0.01, True)) for i in range(6)
    ]
    suggestions = select_suggestions(ranked, {}, max_threads=3)
    assert len(suggestions) == MAX_SUGGESTED_THREADS
    assert [s.rank for s in suggestions] == [1, 2, 3]


# ---------------------------------------------------------------------------
# build_bot_response + enforce — tích hợp
# ---------------------------------------------------------------------------


def test_build_response_none_is_empty_and_escalates():
    response = build_bot_response({"direct_matches": [], "topic_matches": []})
    assert response.confidence is ConfidenceTier.NONE
    assert response.suggestions == []
    assert response.render_buttons is False
    assert response.buttons == []
    assert response.needs_human_review is True
    enforce(response)  # NONE sạch -> pass


def test_build_response_high_renders_buttons():
    search = {
        "direct_matches": [_match("d1", 0.9, True)],
        "topic_matches": [],
    }
    details = {"d1": _detail("d1", [_answer("a1", "LabCoach", True)])}
    response = build_bot_response(search, details, status="pending")
    assert response.confidence is ConfidenceTier.HIGH
    assert len(response.suggestions) == 1
    assert response.render_buttons is True
    assert response.needs_human_review is False
    enforce(response)


# ---------------------------------------------------------------------------
# Validator — mỗi vi phạm phải raise
# ---------------------------------------------------------------------------


def _ok_thread(tid="d1"):
    return (
        {
            "thread_id": tid,
            "rank": 1,
            "title": "T",
            "similarity": 90,
            "relevance": Relevance.DIRECT,
            "excerpt": "giải pháp",
            "thread_url": "https://x",
            "source_tier": SourceTier.VERIFIED,
            "main_answer": None,
            "supplementary_answer": None,
        }
    )


def test_enforce_rejects_missing_link():
    data = _ok_thread()
    data["thread_url"] = ""
    response = BotResponse(
        confidence=ConfidenceTier.HIGH,
        headline="h",
        note="n",
        suggestions=[SuggestedThread(**data)],
    )
    with pytest.raises(GuardrailViolation):
        enforce(response)


def test_enforce_rejects_topic_with_solution():
    data = _ok_thread()
    data["relevance"] = Relevance.TOPIC
    data["main_answer"] = AnswerSummary(
        answer_id="a",
        content="x",
        author_name="n",
        author_role="Learner",
        source_tier=SourceTier.COMMUNITY_UNVERIFIED,
        is_verified=False,
    )
    response = BotResponse(
        confidence=ConfidenceTier.LOW,
        headline="h",
        note="n",
        suggestions=[SuggestedThread(**data)],
    )
    with pytest.raises(GuardrailViolation):
        enforce(response)


def test_enforce_rejects_none_with_suggestions():
    data = _ok_thread()
    response = BotResponse(
        confidence=ConfidenceTier.NONE,  # NONE mà có gợi ý -> lỗi nặng
        headline="h",
        note="n",
        suggestions=[SuggestedThread(**data)],
    )
    with pytest.raises(GuardrailViolation):
        enforce(response)


def test_answer_limit_constants():
    assert MAX_MAIN_ANSWERS == 1
    assert MAX_SUPPLEMENTARY_ANSWERS == 1

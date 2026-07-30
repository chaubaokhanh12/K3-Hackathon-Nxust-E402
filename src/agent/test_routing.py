"""Test cho agent.routing — cổng phạm vi + định tuyến Admin/Mentor/LabCoach.

Chạy: ``PYTHONPATH=src python -m pytest src/agent -q``
Không cần API key (thuần luật, không gọi tool thật).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.guardrails import ConfidenceTier, SourceTier
from agent.routing import (
    ADMIN_TOPICS,
    LABCOACH_TOPICS,
    MENTOR_TOPICS,
    SOURCE_WARNING,
    EscalationReason,
    EscalationTarget,
    EscalationViolation,
    Scope,
    classify_scope,
    has_verified_source,
    route_escalation,
    routing_prompt_block,
    validate_escalation,
)

CORPUS = Path(__file__).resolve().parents[2] / "data" / "discord_qa_mock.json"


# ---------------------------------------------------------------------------
# Cổng phạm vi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "question",
    [
        "hom nay troi mua khong",
        "cho minh xin ty so bong da toi qua",
        "nen mua bitcoin bay gio khong",
        "tối nay xem phim gì hay",
    ],
)
def test_offtopic_questions_are_rejected(question: str) -> None:
    assert classify_scope(question) is Scope.OFF_TOPIC


@pytest.mark.parametrize(
    "question",
    [
        "viet ho em bai luan tieng anh",
        "làm hộ em bài tập tuần này với",
        "giải giùm em bài lab 2 nhé",
    ],
)
def test_do_my_homework_requests_are_rejected(question: str) -> None:
    assert classify_scope(question) is Scope.INTEGRITY


@pytest.mark.parametrize(
    "question",
    [
        # Hỏi VỀ quy định, không phải nhờ làm bài -> vẫn phải tra cứu.
        "chỉnh sửa file trong thư mục script có bị coi là gian lận không",
        "có được nhờ người khác điểm danh hộ không",
        "quy định nộp bài trễ thế nào",
    ],
)
def test_policy_questions_stay_in_scope(question: str) -> None:
    assert classify_scope(question) is Scope.IN_SCOPE


def test_scope_gate_has_no_false_positive_on_corpus() -> None:
    """Không câu hỏi thật nào trong corpus bị coi là ngoài phạm vi."""
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = [thread["title"] for thread in corpus["threads"]]
    texts += [thread["question"]["content"] for thread in corpus["threads"]]
    texts += [query["text"] for query in corpus["test_queries"]]

    flagged = [text for text in texts if classify_scope(text) is not Scope.IN_SCOPE]
    assert flagged == []


# ---------------------------------------------------------------------------
# Định tuyến
# ---------------------------------------------------------------------------


def test_out_of_scope_never_reaches_a_human() -> None:
    """Lỗi 'gọi LabCoach vô tội vạ': tỷ số bóng đá không phải việc của ai cả."""
    for scope in (Scope.OFF_TOPIC, Scope.INTEGRITY):
        decision = route_escalation(
            question="cho minh xin ty so bong da toi qua", scope=scope
        )
        assert decision.target is EscalationTarget.NONE
        assert decision.tagged is False
        assert decision.sla_minutes is None


@pytest.mark.parametrize(
    ("question", "topic_id", "expected"),
    [
        # Admin: quy định, phạm vi thành viên, sự kiện.
        ("học phí khoá này bao nhiêu", "other", EscalationTarget.ADMIN),
        ("có được mang người ngoài khoá vào nhóm không", "other", EscalationTarget.ADMIN),
        ("lễ trao giải tổ chức ở đâu", "other", EscalationTarget.ADMIN),
        ("muốn rời nhóm hiện tại", "roi_nhom", EscalationTarget.ADMIN),
        # Mentor: code, lỗi kỹ thuật, dựng dự án.
        ("set api key mà vẫn báo missing credentials", "api_key", EscalationTarget.MENTOR),
        ("lỗi font tiếng việt khi export pdf", "le_khac", EscalationTarget.MENTOR),
        ("dataset nào dùng cho bài toán này", "dataset", EscalationTarget.MENTOR),
        # LabCoach: vận hành lớp.
        ("deadline nộp sản phẩm cuối cùng là ngày nào", "other", EscalationTarget.LABCOACH),
        ("phase 2 mấy giờ vào học", "giai_doan_2", EscalationTarget.LABCOACH),
        ("quên check out có bị tính vắng không", "diem_danh", EscalationTarget.LABCOACH),
    ],
)
def test_routes_by_domain_not_always_labcoach(
    question: str, topic_id: str, expected: EscalationTarget
) -> None:
    decision = route_escalation(
        question=question, tier=ConfidenceTier.NONE, primary_topic_id=topic_id
    )
    assert decision.target is expected
    assert decision.reason is EscalationReason.NO_SOURCE
    assert decision.sla_minutes is not None


def test_topic_sets_do_not_overlap() -> None:
    """Một topic chỉ thuộc đúng một địa hạt, nếu không routing sẽ nhập nhằng."""
    assert not (ADMIN_TOPICS & MENTOR_TOPICS)
    assert not (ADMIN_TOPICS & LABCOACH_TOPICS)
    assert not (MENTOR_TOPICS & LABCOACH_TOPICS)


def test_unknown_domain_defaults_to_labcoach() -> None:
    decision = route_escalation(
        question="cái này em chưa rõ lắm ạ", tier=ConfidenceTier.NONE
    )
    assert decision.target is EscalationTarget.LABCOACH


def test_verified_answer_does_not_escalate() -> None:
    decision = route_escalation(
        question="quên check out có bị tính vắng không",
        tier=ConfidenceTier.HIGH,
        primary_topic_id="diem_danh",
        suggestions=[{"source_tier": SourceTier.VERIFIED.value}],
    )
    assert decision.target is EscalationTarget.NONE
    assert decision.reason is EscalationReason.NOT_NEEDED


def test_community_only_answer_escalates_for_verification() -> None:
    """Chỉ có học viên trả lời: vẫn hiển thị, nhưng phải nhờ người xác minh."""
    decision = route_escalation(
        question="xp trong discord dùng để làm gì vậy mn",
        tier=ConfidenceTier.LOW,
        primary_topic_id="xp_diem",
        suggestions=[{"source_tier": SourceTier.COMMUNITY_UNVERIFIED.value}],
    )
    assert decision.reason is EscalationReason.UNVERIFIED_SOURCE
    assert decision.target is EscalationTarget.LABCOACH


def test_learner_request_routes_by_domain() -> None:
    decision = route_escalation(
        question="lỗi dependency khi pip install",
        tier=ConfidenceTier.HIGH,
        primary_topic_id="deps_error",
        suggestions=[{"source_tier": SourceTier.VERIFIED.value}],
        learner_requested=True,
    )
    assert decision.reason is EscalationReason.LEARNER_REQUEST
    assert decision.target is EscalationTarget.MENTOR


def test_has_verified_source_reads_both_payload_shapes() -> None:
    assert has_verified_source([{"source_tier": "VERIFIED"}]) is True
    assert has_verified_source([{"verified": True}]) is True
    assert has_verified_source([{"verified": False}]) is False
    assert has_verified_source([]) is False


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def test_validator_blocks_escalating_out_of_scope_question() -> None:
    bogus = route_escalation(question="học phí bao nhiêu", tier=ConfidenceTier.NONE)
    with pytest.raises(EscalationViolation):
        validate_escalation(bogus, scope=Scope.OFF_TOPIC, tier=ConfidenceTier.NONE)


def test_validator_blocks_silent_drop_when_corpus_is_empty() -> None:
    silent = route_escalation(question="bất kỳ", scope=Scope.OFF_TOPIC)
    with pytest.raises(EscalationViolation):
        validate_escalation(silent, scope=Scope.IN_SCOPE, tier=ConfidenceTier.NONE)


def test_validator_blocks_unverified_answer_without_verification() -> None:
    silent = route_escalation(question="bất kỳ", scope=Scope.OFF_TOPIC)
    with pytest.raises(EscalationViolation):
        validate_escalation(
            silent,
            scope=Scope.IN_SCOPE,
            tier=ConfidenceTier.LOW,
            suggestions=[{"verified": False}],
        )


def test_prompt_block_lists_all_three_roles_and_the_warning() -> None:
    block = routing_prompt_block()
    for role in ("Admin", "Mentor", "LabCoach"):
        assert role in block
    assert SOURCE_WARNING in block

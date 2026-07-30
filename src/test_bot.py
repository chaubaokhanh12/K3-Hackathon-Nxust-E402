from __future__ import annotations

from bot import answer, load_impl


def test_local_fallback_returns_verified_corpus_source() -> None:
    result = answer("làm sao biết mình đã được ghi nhận có mặt hôm nay")

    assert result["retrieval_mode"] == "local-corpus-fallback"
    assert result["confidence"] == "high"
    assert result["has_answer"] is True
    assert result["results"][0]["thread_id"] == "1529643349835907072"
    assert result["results"][0]["verified"] is True
    assert result["results"][0]["snippet"]


def test_local_fallback_fails_closed_for_curated_no_source_query() -> None:
    result = answer("deadline nộp sản phẩm cuối cùng là ngày nào")

    assert result["confidence"] == "none"
    assert result["has_answer"] is False
    assert result["reason"] == "no_source"
    assert result["results"] == []
    assert result["tag_labcoach"] is True


def test_local_fallback_marks_unverified_direct_match_as_low_confidence() -> None:
    result = answer("chỉ số active trên server để làm gì")

    assert result["confidence"] == "low"
    assert result["results"][0]["thread_id"] == "1518345891348611072"
    assert result["results"][0]["verified"] is False
    assert result["render_buttons"] is True


def test_vague_question_asks_for_context_without_escalating() -> None:
    result = answer("em bị lỗi ạ")

    assert result["reason"] == "too_vague"
    assert result["clarifying_question"]
    assert result["tag_labcoach"] is False


def test_empty_input_asks_again_instead_of_crashing() -> None:
    for question in ("", "   "):
        result = answer(question)

        assert result["reason"] == "too_vague"
        assert result["clarifying_question"]
        assert result["results"] == []
        assert result["tag_labcoach"] is False


def test_off_topic_question_is_refused_without_bothering_anyone() -> None:
    result = answer("cho minh xin ty so bong da toi qua")

    assert result["reason"] == "out_of_scope"
    assert result["results"] == []
    assert result["render_buttons"] is False
    assert result["tag_labcoach"] is False
    assert result["escalation"]["target_role"] is None


def test_homework_request_is_refused_without_bothering_anyone() -> None:
    result = answer("viet ho em bai luan tieng anh")

    assert result["reason"] == "out_of_scope"
    assert result["has_answer"] is False
    assert result["tag_labcoach"] is False


def test_policy_question_about_cheating_still_searches_the_corpus() -> None:
    """"… có bị coi là gian lận không" là hỏi quy định, không phải nhờ làm bài."""
    result = answer("chỉnh sửa file trong thư mục script có bị coi là gian lận không")

    assert result["reason"] != "out_of_scope"


def test_no_source_question_routes_to_the_owning_role() -> None:
    admin = answer("có được mang người ngoài khoá vào nhóm không")
    labcoach = answer("deadline nộp sản phẩm cuối cùng là ngày nào")

    assert admin["escalation"]["target_role"] == "Admin"
    assert labcoach["escalation"]["target_role"] == "LabCoach"
    assert admin["tag_labcoach"] is True
    assert labcoach["tag_labcoach"] is True


def test_community_only_answer_is_shown_with_warning_and_escalated() -> None:
    result = answer("xp trong discord dùng để làm gì vậy mn")

    assert result["has_answer"] is True
    assert result["results"][0]["verified"] is False
    assert result["source_warning"]
    assert result["escalation"]["reason"] == "unverified_source"
    assert result["tag_labcoach"] is True


def test_verified_answer_does_not_page_a_human() -> None:
    result = answer("làm sao biết mình đã được ghi nhận có mặt hôm nay")

    assert result["results"][0]["verified"] is True
    assert result["tag_labcoach"] is False
    assert result["escalation"]["target_role"] is None
    assert "source_warning" not in result


def test_load_impl_defaults_to_integrated_answer() -> None:
    assert load_impl() is answer

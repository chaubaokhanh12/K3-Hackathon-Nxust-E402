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


def test_load_impl_defaults_to_integrated_answer() -> None:
    assert load_impl() is answer

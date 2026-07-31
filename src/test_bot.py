from __future__ import annotations

import re

import pytest

from bot import answer, load_impl


@pytest.fixture(autouse=True)
def force_local_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit test phải tất định và không gọi API tính phí.

    Các khẳng định trong file này pin hành vi của chế độ ``local-corpus-fallback``;
    nếu máy dev có ``OPENAI_API_KEY`` thì cùng một test lại chạy nhánh embeddings
    và đỏ vì lý do không liên quan. Nhánh embeddings được đo bằng
    ``src/test/test_cases.py``, không phải ở đây.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)



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


# ---------------------------------------------------------------------------
# Tầng tổng hợp LLM (payload["generated_answer"])
#
# Bất biến quan trọng nhất: tổng hợp là phần BỔ SUNG. Dù nó bật, tắt, hay hỏng,
# ``suggestions``/``results`` phải giữ nguyên trích đoạn nguyên văn từ corpus —
# đó là thứ bộ chấm ``src/test/test_cases.json`` kiểm tra.
# ---------------------------------------------------------------------------


class StubGenerator:
    """Generator giả: trả chuỗi nạp sẵn, hoặc ném lỗi nạp sẵn."""

    model_name = "stub-model"

    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.call_count = 0

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        if self.error:
            raise self.error
        return self.reply.format(prompt=user_prompt)


ATTENDANCE_QUERY = "làm sao biết mình đã được ghi nhận có mặt hôm nay"
ATTENDANCE_THREAD_ID = "1529643349835907072"


def test_synthesis_is_off_by_default_without_an_api_key() -> None:
    result = answer(ATTENDANCE_QUERY)

    assert result["generated_answer"] is None
    assert result["generation_mode"] == "disabled"


def test_injected_generator_attaches_a_grounded_answer() -> None:
    generator = StubGenerator(f"Bạn vào tab Điểm danh xem nhé [#{ATTENDANCE_THREAD_ID}].")
    result = answer(ATTENDANCE_QUERY, generator=generator)

    assert result["generation_mode"] == "llm-synthesis"
    assert result["generated_answer"]["cited_thread_ids"] == [ATTENDANCE_THREAD_ID]
    assert result["generated_answer"]["model"] == "stub-model"


def test_synthesis_never_rewrites_the_verbatim_excerpt() -> None:
    """Bất biến chống bịa: LLM chỉ được thêm trường mới, không sửa trích đoạn."""
    baseline = answer(ATTENDANCE_QUERY)
    generated = answer(
        ATTENDANCE_QUERY,
        generator=StubGenerator(f"Nội dung hoàn toàn khác [#{ATTENDANCE_THREAD_ID}]."),
    )

    assert generated["suggestions"] == baseline["suggestions"]
    assert generated["results"] == baseline["results"]


def test_fabricated_answer_is_dropped_instead_of_shown() -> None:
    result = answer(ATTENDANCE_QUERY, generator=StubGenerator("Bạn chạy `npm run fix` nhé."))

    assert result["generated_answer"] is None
    assert result["generation_mode"] == "ungrounded"
    assert result["has_answer"] is True  # gợi ý trích dẫn vẫn còn


def test_no_source_answer_never_calls_the_generator() -> None:
    """Tier NONE đã có copy an toàn — gọi LLM ở đó chỉ tạo cơ hội bịa."""
    generator = StubGenerator("bất kỳ [#1].")
    result = answer("deadline nộp sản phẩm cuối cùng là ngày nào", generator=generator)

    assert generator.call_count == 0
    assert result["generated_answer"] is None
    assert result["generation_mode"] == "no_source"


def test_out_of_scope_answer_never_calls_the_generator() -> None:
    generator = StubGenerator("bất kỳ [#1].")
    result = answer("hôm nay Hà Nội mưa không", generator=generator)

    assert generator.call_count == 0
    assert result["generation_mode"] == "no_source"


def test_suggestions_without_any_answer_never_reach_the_generator() -> None:
    """Regression: gợi ý không kèm lời giải thì KHÔNG được tổng hợp.

    Ca thật đã lọt: câu hỏi điểm danh trả về hai topic match không có lời giải.
    Thứ duy nhất còn lại trong chúng là ``excerpt`` — vốn là CÂU HỎI của học
    viên khác. LLM biến nỗi lo đó thành khẳng định "nếu không nhận được thông
    báo thì có thể bạn chưa được ghi nhận", trái ngược lời giải đã xác minh của
    LabCoach trong chính thread ấy.

    Ở local fallback lớp lỗi này hiện ra dưới dạng direct match rỗng lời giải;
    biến thể topic match được khoá ở ``agent/test_synthesis.py``.
    """
    generator = StubGenerator("Bạn gửi xe ở tầng hầm B1 nhé [#1].")
    result = answer("Chỗ gửi xe ở đâu ạ", generator=generator)

    assert result["suggestions"], "corpus đổi rồi — chọn lại câu hỏi có gợi ý"
    assert all(
        item["main_answer"] is None and item["supplementary_answer"] is None
        for item in result["suggestions"]
    ), "corpus đổi rồi — câu hỏi này phải ra gợi ý KHÔNG kèm lời giải"

    assert generator.call_count == 0
    assert result["generated_answer"] is None
    assert result["generation_mode"] == "no_groundable_source"
    # Gợi ý tham khảo vẫn hiện: chỉ phần tổng hợp bị chặn.
    assert result["has_answer"] is True


def test_injected_generator_failure_is_raised_not_swallowed() -> None:
    """Generator tiêm tay hỏng = bug của test. Nuốt lỗi ở đây sẽ giấu bug đó."""
    from tools._shared.generation import GenerationResponseError

    with pytest.raises(GenerationResponseError):
        answer(ATTENDANCE_QUERY, generator=StubGenerator(error=GenerationResponseError("boom")))


def test_prompt_is_built_from_the_retrieved_threads() -> None:
    """Prompt phải mang đúng thread lấy được, và chỉ cho phép trích các id đó."""

    class RecordingGenerator(StubGenerator):
        prompts: list[str] = []

        def generate(self, *, system_prompt: str, user_prompt: str) -> str:
            self.prompts.append(user_prompt)
            return super().generate(system_prompt=system_prompt, user_prompt=user_prompt)

    generator = RecordingGenerator(f"Xem thread [#{ATTENDANCE_THREAD_ID}].")
    generator.prompts = []
    result = answer(ATTENDANCE_QUERY, generator=generator)

    (prompt,) = generator.prompts
    retrieved_ids = {item["thread_id"] for item in result["suggestions"]}
    cited_in_prompt = set(re.findall(r"\[#(\d+)\]", prompt))

    assert cited_in_prompt == retrieved_ids
    assert ATTENDANCE_QUERY in prompt
    # Nội dung nguồn phải đi kèm, nếu không model chỉ có tiêu đề để đoán.
    assert result["suggestions"][0]["main_answer"]["content"][:40] in prompt

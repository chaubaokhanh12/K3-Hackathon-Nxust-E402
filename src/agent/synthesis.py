"""Tầng tổng hợp: viết câu trả lời từ các thread đã lấy được (RAG).

Vì sao tách khỏi ``guardrails.py``: guardrails bảo vệ bất biến "trích nguyên
văn" của ``suggestions`` — bất biến đó KHÔNG đổi. Module này sinh ra một trường
**bổ sung** (``generated_answer``) nằm cạnh, không thay thế, phần trích dẫn.

Ba tuyến chặn bịa đặt, theo thứ tự:

1. Prompt chỉ chứa nội dung thread lấy được. Không có kiến thức nền nào khác.
2. Model bắt buộc trích nguồn ``[#thread_id]`` cho mỗi ý, và phải trả về
   :data:`INSUFFICIENT_SOURCE_TOKEN` khi nguồn không trả lời được câu hỏi.
3. :func:`validate_grounding` kiểm tra sau: không trích nguồn, hoặc trích một
   ``thread_id`` không có trong prompt, thì cả câu trả lời bị loại bỏ.

Loại bỏ ở bước 3 là **không gây lỗi**: ``bot.py`` bỏ trường tổng hợp và trả về
payload trích dẫn như trước khi có module này.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any

from tools._shared.generation import (
    AnswerGenerator,
    GenerationResponseError,
    GeneratorConfigurationError,
)

LOGGER = logging.getLogger(__name__)

#: Model phải trả về đúng chuỗi này khi nguồn không đủ. Viết hoa không dấu để
#: không đụng nội dung tiếng Việt bình thường.
INSUFFICIENT_SOURCE_TOKEN = "KHONG_DU_NGUON"

#: Trích nguồn dạng ``[#1525590758785155072]``. Thread id trong corpus là chuỗi
#: số Discord snowflake.
CITATION_PATTERN = re.compile(r"\[#(\d+)\]")

#: Cắt nội dung mỗi câu trả lời đưa vào prompt. Thread dài không được đẩy các
#: thread khác ra khỏi context và làm model chỉ thấy một nguồn.
MAX_CONTENT_CHARS = 1200

SYNTHESIS_SYSTEM_PROMPT = f"""Bạn là DupBot, trợ lý hỏi đáp của khoá học TrustQA.

NHIỆM VỤ: đọc các thread Discord được cung cấp, rồi viết MỘT câu trả lời trực
tiếp cho câu hỏi của học viên.

RÀNG BUỘC TUYỆT ĐỐI:
1. Chỉ dùng thông tin có trong các thread được cung cấp. Bạn KHÔNG có kiến thức
   nào khác. Không suy đoán, không bổ sung kinh nghiệm chung, không tự nghĩ ra
   bước làm, tên file, lệnh, hay đường link không xuất hiện trong nguồn.
2. Mỗi ý phải kèm trích nguồn dạng [#thread_id] ngay sau ý đó, dùng đúng
   thread_id được cho. Không bịa thread_id.
3. Nếu các thread KHÔNG trả lời được câu hỏi — kể cả khi chúng cùng chủ đề —
   hãy trả về đúng một dòng: {INSUFFICIENT_SOURCE_TOKEN}
   Trả lời lệch còn tệ hơn không trả lời.
4. Nếu nguồn chỉ đến từ học viên (role Learner, chưa xác minh), nói rõ đây là
   kinh nghiệm cộng đồng chưa được LabCoach xác nhận.

VĂN PHONG: tiếng Việt, xưng "mình", gọi người hỏi là "bạn". Ngắn gọn, tối đa
6 câu hoặc 5 gạch đầu dòng. Đi thẳng vào cách xử lý, không mở bài, không chào
hỏi, không nhắc lại câu hỏi."""


def _truncate(text: str, limit: int = MAX_CONTENT_CHARS) -> str:
    collapsed = re.sub(r"\s+", " ", (text or "").strip())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[:limit].rstrip() + "…"


def _format_answer(label: str, answer: Mapping[str, Any] | None) -> list[str]:
    if not answer:
        return []
    role = answer.get("author_role") or "không rõ"
    verified = "đã xác minh" if answer.get("is_verified") else "CHƯA xác minh"
    return [f"  {label} ({role}, {verified}): {_truncate(str(answer.get('content') or ''))}"]


def groundable_suggestions(
    suggestions: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Lọc ra các thread thật sự CHỨA LỜI GIẢI để neo câu trả lời vào.

    Topic match bị loại hoàn toàn. Guardrail của repo cấm trình topic match như
    lời giải, nên nó luôn có ``main_answer = None`` — thứ duy nhất còn lại là
    ``excerpt``, mà với topic match ``excerpt`` là CÂU HỎI GỐC của học viên
    khác, không phải câu trả lời.

    Đưa câu hỏi cho LLM và bảo nó "trả lời" thì nó sẽ biến nỗi lo của người hỏi
    thành khẳng định của bot — đúng kiểu bịa mà guardrail sinh ra để chặn.
    """

    return [
        item
        for item in suggestions
        if item.get("main_answer") or item.get("supplementary_answer")
    ]


def build_context_block(suggestions: Sequence[Mapping[str, Any]]) -> str:
    """Dựng phần nguồn của prompt. Chỉ nhận thread đã qua :func:`groundable_suggestions`."""

    blocks: list[str] = []
    for item in suggestions:
        thread_id = str(item.get("thread_id") or "")
        lines = [
            f"[#{thread_id}]",
            f"  Tiêu đề: {_truncate(str(item.get('title') or ''), 200)}",
            f"  Độ khớp: {item.get('similarity')}/100 ({item.get('relevance')})",
        ]
        lines += _format_answer("Lời giải chính", item.get("main_answer"))
        lines += _format_answer("Ý kiến bổ sung", item.get("supplementary_answer"))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_synthesis_prompt(
    question: str, suggestions: Sequence[Mapping[str, Any]]
) -> str:
    allowed = ", ".join(f"[#{item.get('thread_id')}]" for item in suggestions)
    return (
        f"CÂU HỎI CỦA HỌC VIÊN:\n{question}\n\n"
        f"CÁC THREAD LẤY ĐƯỢC (nguồn duy nhất được phép dùng):\n\n"
        f"{build_context_block(suggestions)}\n\n"
        f"Thread id hợp lệ để trích nguồn: {allowed}\n\n"
        f"Viết câu trả lời, hoặc {INSUFFICIENT_SOURCE_TOKEN} nếu nguồn không đủ."
    )


def validate_grounding(
    text: str, allowed_thread_ids: Sequence[str]
) -> tuple[str, list[str]] | None:
    """Kiểm tra câu trả lời có neo vào nguồn không.

    Trả về ``(text, cited_ids)`` nếu hợp lệ, ``None`` nếu phải loại bỏ.
    """

    stripped = (text or "").strip()
    if not stripped or INSUFFICIENT_SOURCE_TOKEN in stripped:
        return None

    allowed = {str(thread_id) for thread_id in allowed_thread_ids}
    cited = CITATION_PATTERN.findall(stripped)
    if not cited:
        LOGGER.warning("Synthesis rejected: câu trả lời không trích nguồn nào.")
        return None

    unknown = sorted({item for item in cited if item not in allowed})
    if unknown:
        LOGGER.warning("Synthesis rejected: trích thread_id không có trong nguồn %s", unknown)
        return None

    # Giữ thứ tự xuất hiện, bỏ trùng.
    seen: list[str] = []
    for item in cited:
        if item not in seen:
            seen.append(item)
    return stripped, seen


def synthesize_answer(
    question: str,
    suggestions: Sequence[Mapping[str, Any]],
    *,
    generator: AnswerGenerator,
) -> dict[str, Any] | None:
    """Sinh câu trả lời có dẫn nguồn, hoặc ``None`` nếu không neo được vào nguồn.

    Không nuốt lỗi lập trình: chỉ lỗi hạ tầng của provider mới được bỏ qua, và
    việc bỏ qua đó do ``bot.py`` quyết định.
    """

    # Lọc TRƯỚC khi gọi provider: không có lời giải nào thì không có gì để neo,
    # và một lượt gọi LLM ở đây chỉ tạo cơ hội bịa.
    sources = groundable_suggestions(suggestions)
    if not sources:
        return None

    raw = generator.generate(
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        user_prompt=build_synthesis_prompt(question, sources),
    )
    # Chỉ thread có lời giải mới được trích. Trích một topic match cũng là bịa.
    grounded = validate_grounding(
        raw, [str(item.get("thread_id") or "") for item in sources]
    )
    if grounded is None:
        return None

    text, cited = grounded
    return {
        "text": text,
        "cited_thread_ids": cited,
        "model": getattr(generator, "model_name", None),
    }


#: Lỗi hạ tầng của tầng sinh được phép nuốt (bỏ phần tổng hợp, giữ trích dẫn).
SYNTHESIS_ERRORS = (GeneratorConfigurationError, GenerationResponseError)


__all__ = [
    "CITATION_PATTERN",
    "INSUFFICIENT_SOURCE_TOKEN",
    "SYNTHESIS_ERRORS",
    "SYNTHESIS_SYSTEM_PROMPT",
    "build_context_block",
    "build_synthesis_prompt",
    "groundable_suggestions",
    "synthesize_answer",
    "validate_grounding",
]

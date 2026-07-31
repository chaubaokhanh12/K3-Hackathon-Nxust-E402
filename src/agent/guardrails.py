"""Executable guardrails cho DupBot.

Module này mã hoá các quy tắc trong ``Bot_System_Instructions.md`` phần B thành
logic Python xác định, thay vì để LLM tự diễn. Có ba nhóm hàm:

1. **Phân loại / quyết định** — :func:`classify_relevance`, :func:`decide_confidence`,
   :func:`decide_buttons`, :func:`rank_for_display`.
2. **Tổng hợp phản hồi** — :func:`build_bot_response` dựng payload JSON sẵn sàng cho
   frontend/API.
3. **Validator cứng** — :func:`enforce` kiểm các bất biến (không bịa, NONE phải rỗng,
   giới hạn số lượng, link bắt buộc, topic match không được trình là lời giải).

Ngưỡng được **import trực tiếp** từ ``tools.*`` (single source of truth): nếu sau này
đổi threshold trong tool thì guardrail đi theo, không cần sửa hai chỗ.

Yêu cầu ``PYTHONPATH=src`` (giống ``tools``).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

# Single source of truth: ngưỡng thật nằm trong tools, import về để không drift.
from tools.detect_question_topics.tool import PRIMARY_TOPIC_THRESHOLD
from tools.get_qa_thread.tool import ROLE_PRIORITY, VERIFIED_ROLE_MIN_PRIORITY
from tools.search_qa_threads.tool import (
    DIRECT_MATCH_THRESHOLD,
    TOPIC_REFERENCE_PROBLEM_THRESHOLD,
    TOPIC_REFERENCE_TOPIC_THRESHOLD,
)

__all__ = [
    # constants
    "VERIFIED_ROLES",
    "MAX_SUGGESTED_THREADS",
    "MAX_MAIN_ANSWERS",
    "MAX_SUPPLEMENTARY_ANSWERS",
    "BOT_COPY",
    "DEFAULT_HUMAN_TARGET",
    "render_copy",
    "BUTTONS",
    "ANSWER_SOURCE_TIER",
    "SOURCE_TRUST_NOTE",
    # enums
    "ConfidenceTier",
    "SourceTier",
    "Relevance",
    # exceptions
    "GuardrailViolation",
    # models
    "AnswerSummary",
    "SuggestedThread",
    "ButtonSpec",
    "BotResponse",
    # decision functions
    "classify_relevance",
    "revalidate_buckets",
    "answer_source_tier",
    "thread_source_tier",
    "rank_for_display",
    "select_suggestions",
    "decide_confidence",
    "has_verified_solution",
    "tier_for_content",
    "decide_buttons",
    "should_escalate",
    "build_bot_response",
    "enforce",
]


# ---------------------------------------------------------------------------
# Phân tầng nguồn (spec §5 + data/SCHEMA.md)
# ---------------------------------------------------------------------------

#: Vai trò được coi là nguồn đã xác minh — priority >= 3 trong ROLE_PRIORITY
#: của get_qa_thread (Admin 5 / Mentor 4 / BTC 4 / LabCoach 3). Learner = 1 -> loại.
VERIFIED_ROLES: frozenset[str] = frozenset(
    role
    for role, priority in ROLE_PRIORITY.items()
    if priority >= VERIFIED_ROLE_MIN_PRIORITY
)

#: Ánh xạ verification_label của get_qa_thread -> SourceTier.
ANSWER_SOURCE_TIER: dict[str, "SourceTier"] = {}  # điền sau khi định nghĩa enum


# ---------------------------------------------------------------------------
# Giới hạn trình bày
# ---------------------------------------------------------------------------

MAX_SUGGESTED_THREADS = 3
MAX_MAIN_ANSWERS = 1
MAX_SUPPLEMENTARY_ANSWERS = 1
#: Số câu trả lời tối đa cần lấy khi gọi get_qa_thread (1 chính + 1 bổ sung).
DEFAULT_MAX_ANSWERS = MAX_MAIN_ANSWERS + MAX_SUPPLEMENTARY_ANSWERS


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------


class ConfidenceTier(str, Enum):
    """Ba tầng độ chắc chắn, đồng bộ với ``frontend/src/components/BotMessage.jsx``."""

    HIGH = "high"  #: có direct match đã xác minh -> đề xuất trực tiếp
    LOW = "low"  #: gần đúng (direct chưa xác minh, hoặc chỉ topic)
    NONE = "none"  #: không có gì đủ liên quan -> nói "không biết", tự escalate


class SourceTier(str, Enum):
    VERIFIED = "VERIFIED"  #: ✅ nguồn đã xác minh (LabCoach/Mentor/Admin/BTC)
    COMMUNITY_UNVERIFIED = "COMMUNITY_UNVERIFIED"  #: ⚠️ học viên, chưa xác minh


class Relevance(str, Enum):
    DIRECT = "direct"  #: cùng vấn đề (problem_similarity >= 0.78)
    TOPIC = "topic"  #: cùng chủ đề (không giải quyết trực tiếp)


ANSWER_SOURCE_TIER = {
    "VERIFIED": SourceTier.VERIFIED,
    "COMMUNITY_UNVERIFIED": SourceTier.COMMUNITY_UNVERIFIED,
}


# ---------------------------------------------------------------------------
# Copy (headline/note) — phản chiếu BotMessage.jsx, không đổi tinh thần
# ---------------------------------------------------------------------------

#: Vai trò mặc định khi chưa biết kết quả định tuyến. ``bot.py`` render lại copy
#: bằng vai trò thật (``escalation.target_role``) nên học viên không bao giờ đọc
#: "đã chuyển cho LabCoach" trong khi payload nói Mentor.
DEFAULT_HUMAN_TARGET = "LabCoach"

#: Template copy. ``{target}`` được điền bởi :func:`render_copy`.
BOT_COPY: dict[ConfidenceTier, dict[str, str]] = {
    ConfidenceTier.HIGH: {
        "headline": "Mình tìm thấy câu hỏi tương tự đã có lời giải",
        "note": "Đọc trước các thread này, phần lớn trường hợp là cùng một nguyên nhân.",
    },
    ConfidenceTier.LOW: {
        "headline": "Mình chỉ tìm được kết quả gần đúng",
        "note": (
            "Độ khớp không cao nên có thể không đúng ý bạn. Nếu không giải quyết được, "
            "bấm nút bên dưới để mình gọi {target}."
        ),
    },
    ConfidenceTier.NONE: {
        "headline": "Chưa có thread nào tương tự trong lịch sử kênh",
        "note": (
            "Đây là câu hỏi mới. Mình đã chuyển trực tiếp cho {target}, "
            "bạn không cần làm gì thêm."
        ),
    },
}


def render_copy(tier: ConfidenceTier, target: Any = None) -> dict[str, str]:
    """Điền vai trò người thật vào copy của một tier.

    ``target`` nhận ``EscalationTarget``, chuỗi, hoặc ``None`` (dùng mặc định).
    """
    name = getattr(target, "value", target) or DEFAULT_HUMAN_TARGET
    copy = BOT_COPY[tier]
    return {
        "headline": copy["headline"].format(target=name),
        "note": copy["note"].format(target=name),
    }

#: Ghi chú độ tin cậy để inject vào System Prompt. Phản chiếu ROLE_TRUST trong
#: tools/search_qa_threads. Chỉ dùng để HƯỚNG dẫn LLM, KHÔNG để LLM tự xếp hạng
#: (việc xếp hạng đã làm ở code).
SOURCE_TRUST_NOTE: str = (
    "- Độ tin cậy (source_trust; CHỈ phá thế hoà trong cùng nhóm độ liên quan, "
    "không đảo thứ tự liên quan): Admin/Mentor/BTC=1.0, LabCoach=0.95, "
    "học viên đã xác minh=0.85, học viên chưa xác minh=0.40."
)


class ButtonSpec(BaseModel):
    """Một nút bấm ở cuối tin nhắn bot (tương ứng dupbotService.js)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Định danh nút, dùng cho handler frontend.")
    label: str = Field(description="Text hiển thị.")
    action: str = Field(description="Tên hàm trong dupbotService.js.")
    style: str = Field(description="'green' | 'secondary'.")


#: Hai nút cố định. Thứ tự: resolve trước, escalate sau (giống BotMessage.jsx).
RESOLVE_BUTTON = ButtonSpec(
    id="resolve",
    label="Đã giải quyết được",
    action="markThreadResolved",
    style="green",
)
ESCALATE_BUTTON = ButtonSpec(
    id="escalate",
    label="Chưa đúng ý tôi",
    action="escalateToLabCoach",
    style="secondary",
)
BUTTONS: tuple[ButtonSpec, ButtonSpec] = (RESOLVE_BUTTON, ESCALATE_BUTTON)


# ---------------------------------------------------------------------------
# Models đầu ra
# ---------------------------------------------------------------------------


class AnswerSummary(BaseModel):
    """Tóm tắt một câu trả lời để hiển thị, kèm nhãn nguồn."""

    model_config = ConfigDict(extra="forbid")

    answer_id: str
    content: str = Field(description="Nguyên văn từ get_qa_thread, không diễn ý.")
    author_name: str
    author_role: str
    source_tier: SourceTier
    is_verified: bool


class SuggestedThread(BaseModel):
    """Một thread đề xuất trong danh sách kết quả."""

    model_config = ConfigDict(extra="forbid")

    thread_id: str
    rank: int = Field(ge=1, le=MAX_SUGGESTED_THREADS)
    title: str
    similarity: int = Field(ge=0, le=100, description="problem_similarity * 100.")
    relevance: Relevance
    excerpt: str = Field(description="Trích đoạn nguyên văn: câu trả lời hoặc câu hỏi gốc.")
    thread_url: str = Field(description="Link gốc từ tool, KHÔNG tự tạo.")
    source_tier: SourceTier
    #: Cờ xác minh CẤP THREAD từ corpus (``verified_answer``). Khác với
    #: ``source_tier`` — cái đó nói về câu trả lời đang được trình ra.
    thread_has_verified_answer: bool = False
    author_name: str | None = None
    author_role: str | None = None
    #: Chỉ direct match mới có lời giải. Topic match PHẢI là None (guardrail).
    main_answer: AnswerSummary | None = None
    supplementary_answer: AnswerSummary | None = None


class BotResponse(BaseModel):
    """Payload hoàn chỉnh bot trả về cho frontend / Discord."""

    model_config = ConfigDict(extra="forbid")

    confidence: ConfidenceTier
    headline: str
    note: str
    suggestions: list[SuggestedThread] = Field(default_factory=list)
    render_buttons: bool = False
    buttons: list[ButtonSpec] = Field(default_factory=list)
    #: Tín hiệu của TẦNG HIỂN THỊ: bot đã tự chuyển vì không có gì để trình
    #: (tier NONE). Quyết định "chuyển cho AI" là của ``agent.routing`` và chỉ
    #: nằm ở ``payload["escalation"]`` — không sao chép sang đây để tránh hai
    #: nguồn sự thật lệch nhau.
    needs_human_review: bool = False


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class GuardrailViolation(Exception):
    """Bất biến guardrail bị phá. Bot phải từ chối in payload này."""


# ---------------------------------------------------------------------------
# Hàm quyết định (deterministic)
# ---------------------------------------------------------------------------


def classify_relevance(
    problem_similarity: float, topic_similarity: float
) -> Relevance | None:
    """Re-validate cách phân loại của ``search_qa_threads`` tại lớp guardrail.

    Trả về ``None`` nếu thread phải bị loại (không đủ liên quan). Hàm này **phản chiếu**
    logic trong ``tools/search_qa_threads/tool.py`` — giữ ở đây để guardrail có thể
    chặn lại bất kỳ kết quả nào bị tool xếp nhầm do thay đổi ngưỡng.
    """
    if problem_similarity >= DIRECT_MATCH_THRESHOLD:
        return Relevance.DIRECT
    if (
        problem_similarity >= TOPIC_REFERENCE_PROBLEM_THRESHOLD
        and topic_similarity >= TOPIC_REFERENCE_TOPIC_THRESHOLD
    ):
        return Relevance.TOPIC
    return None


def revalidate_buckets(
    search_result: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    """Xếp lại hai rổ direct/topic bằng chính :func:`classify_relevance`.

    Guardrail không được tin rổ mà tool (hoặc fallback cục bộ) đã xếp: nếu một
    item nằm trong ``direct_matches`` nhưng điểm của nó chỉ đủ mức topic, nó bị
    hạ xuống topic — và do đó KHÔNG được trình lời giải. Item không đạt cả hai
    ngưỡng thì bị loại hẳn thay vì hiển thị.
    """
    direct: list[Mapping[str, Any]] = []
    topic: list[Mapping[str, Any]] = []
    for match in [
        *(search_result.get("direct_matches") or []),
        *(search_result.get("topic_matches") or []),
    ]:
        relevance = classify_relevance(
            float(match.get("problem_similarity") or 0.0),
            float(match.get("topic_similarity") or 0.0),
        )
        if relevance is Relevance.DIRECT:
            direct.append(match)
        elif relevance is Relevance.TOPIC:
            topic.append(match)
    return direct, topic


def answer_source_tier(answer: Mapping[str, Any]) -> SourceTier:
    """Xác định SourceTier của một câu trả lời từ get_qa_thread."""
    label = str(answer.get("verification_label") or "").upper()
    if label in ANSWER_SOURCE_TIER:
        return ANSWER_SOURCE_TIER[label]
    # Fallback: dựa vào cờ is_verified / vai trò tác giả.
    if answer.get("is_verified") is True:
        return SourceTier.VERIFIED
    role = str(answer.get("author_role") or "")
    if role in VERIFIED_ROLES:
        return SourceTier.VERIFIED
    return SourceTier.COMMUNITY_UNVERIFIED


def thread_source_tier(match: Mapping[str, Any]) -> SourceTier:
    """SourceTier cấp thread, dùng khi chưa đọc chi tiết câu trả lời."""
    if match.get("has_verified_answer") is True:
        return SourceTier.VERIFIED
    if float(match.get("source_trust") or 0.0) >= 0.85:
        return SourceTier.VERIFIED
    return SourceTier.COMMUNITY_UNVERIFIED


def rank_for_display(
    direct_matches: Iterable[Mapping[str, Any]],
    topic_matches: Iterable[Mapping[str, Any]] | None = None,
) -> list[tuple[Relevance, Mapping[str, Any]]]:
    """Trộn direct + topic theo thứ tự ưu tiên spec §5.3.

    Thứ tự: direct+verified > direct+community > topic+verified > topic+community.
    Trong từng nhóm con: ``problem_similarity`` giảm, rồi ``source_trust`` giảm.
    Trả về list (Relevance, match) để :func:`select_suggestions` cắt top-N.
    """
    topic_matches = list(topic_matches or [])

    def group_key(relevance: Relevance, match: Mapping[str, Any]) -> tuple[Any, ...]:
        verified = thread_source_tier(match) is SourceTier.VERIFIED
        # direct (0) trước topic (1); verified (0) trước community (1).
        return (
            0 if relevance is Relevance.DIRECT else 1,
            0 if verified else 1,
            -float(match.get("problem_similarity") or 0.0),
            -float(match.get("source_trust") or 0.0),
            str(match.get("thread_id") or ""),
        )

    combined: list[tuple[Relevance, Mapping[str, Any]]] = [
        (Relevance.DIRECT, m) for m in direct_matches
    ] + [(Relevance.TOPIC, m) for m in topic_matches]
    combined.sort(key=lambda item: group_key(item[0], item[1]))
    return combined


def decide_confidence(
    direct_matches: Iterable[Mapping[str, Any]],
    topic_matches: Iterable[Mapping[str, Any]] | None = None,
) -> ConfidenceTier:
    """Chọn tier confidence theo bảng tra trong Bot_System_Instructions §6.

    - HIGH : có direct match có câu trả lời đã xác minh.
    - LOW  : có direct match nhưng chưa xác minh, HOẶC chỉ có topic match.
    - NONE : cả direct và topic rỗng.
    """
    direct = list(direct_matches)
    topic = list(topic_matches or [])
    if any(m.get("has_verified_answer") for m in direct):
        return ConfidenceTier.HIGH
    if direct or topic:
        return ConfidenceTier.LOW
    return ConfidenceTier.NONE


def has_verified_solution(suggestions: Iterable["SuggestedThread"]) -> bool:
    """True nếu có ít nhất một direct match trình được lời giải đã xác minh."""
    return any(
        suggestion.relevance is Relevance.DIRECT
        and suggestion.main_answer is not None
        and suggestion.main_answer.source_tier is SourceTier.VERIFIED
        for suggestion in suggestions
    )


def tier_for_content(
    tier: ConfidenceTier, suggestions: Iterable["SuggestedThread"]
) -> ConfidenceTier:
    """Hạ tier cho khớp nội dung thật sự trình ra.

    - Không còn gợi ý nào -> NONE.
    - HIGH nhưng không gợi ý nào có lời giải đã xác minh -> LOW.
    """
    items = list(suggestions)
    if not items:
        return ConfidenceTier.NONE
    if tier is ConfidenceTier.HIGH and not has_verified_solution(items):
        return ConfidenceTier.LOW
    return tier


def decide_buttons(tier: ConfidenceTier, status: str) -> list[ButtonSpec]:
    """Hai nút chỉ xuất hiện khi ``pending`` và tier ∈ {HIGH, LOW}.

    Tier NONE đã tự escalate nên không sinh nút (spec §8).
    """
    if status != "pending":
        return []
    if tier is ConfidenceTier.NONE:
        return []
    return list(BUTTONS)


def should_escalate(tier: ConfidenceTier) -> bool:
    """Tier NONE tự động chuyển LabCoach."""
    return tier is ConfidenceTier.NONE


# ---------------------------------------------------------------------------
# Tổng hợp phản hồi
# ---------------------------------------------------------------------------


def _to_answer_summary(answer: Mapping[str, Any]) -> AnswerSummary:
    return AnswerSummary(
        answer_id=str(answer.get("answer_id") or ""),
        content=str(answer.get("content") or ""),
        author_name=str(answer.get("author_name") or ""),
        author_role=str(answer.get("author_role") or ""),
        source_tier=answer_source_tier(answer),
        is_verified=bool(answer.get("is_verified")),
    )


def _pick_answers(
    thread_detail: Mapping[str, Any],
    *,
    max_main: int = MAX_MAIN_ANSWERS,
    max_supp: int = MAX_SUPPLEMENTARY_ANSWERS,
) -> tuple[AnswerSummary | None, AnswerSummary | None]:
    """Chọn 1 câu chính (ưu tiên verified/accepted) + tối đa 1 câu bổ sung.

    Bổ sung phải là community và khác nội dung với câu chính — để bổ sung góc nhìn,
    không lặp. Nếu không có câu chính verified, lấy câu đầu tiên làm chính.
    """
    answers = [
        _to_answer_summary(raw)
        for raw in (thread_detail.get("selected_answers") or [])
    ]
    if not answers or max_main <= 0:
        return None, None

    # Chọn CHÍNH trước, rồi mới chọn BỔ SUNG từ phần còn lại. Bản cũ làm ngược:
    # câu community đầu tiên rơi vào nhánh elif thành supp, sau đó main fallback
    # về answers[0] — cùng một câu trả lời bị trình hai lần.
    main = next(
        (a for a in answers if a.source_tier is SourceTier.VERIFIED),
        answers[0],
    )
    supp: AnswerSummary | None = None
    if max_supp > 0:
        supp = next(
            (
                a
                for a in answers
                if a.source_tier is SourceTier.COMMUNITY_UNVERIFIED
                and a.answer_id != main.answer_id
                and a.content != main.content
            ),
            None,
        )
    return main, supp


def select_suggestions(
    ranked: Iterable[tuple[Relevance, Mapping[str, Any]]],
    thread_details: Mapping[str, Mapping[str, Any]],
    *,
    max_threads: int = MAX_SUGGESTED_THREADS,
) -> list[SuggestedThread]:
    """Cắt top-N thread từ danh sách đã xếp và đính kèm lời giải (nếu direct)."""
    suggestions: list[SuggestedThread] = []
    for relevance, match in ranked:
        if len(suggestions) >= max_threads:
            break
        thread_id = str(match.get("thread_id") or "")
        detail = thread_details.get(thread_id) or {}
        similarity = round(float(match.get("problem_similarity") or 0.0) * 100)

        if relevance is Relevance.DIRECT:
            main, supp = _pick_answers(detail)
            excerpt = (main.content if main else str(detail.get("question") or "")) or str(
                match.get("title") or ""
            )
            source_tier = main.source_tier if main else thread_source_tier(match)
            author_name = main.author_name if main else None
            author_role = main.author_role if main else None
        else:
            # Topic match: KHÔNG trình lời giải. Vẫn giữ trích đoạn nguyên văn là
            # CÂU HỎI gốc (không phải tiêu đề đã biên tập) và metadata tác giả
            # của thread — đó là thông tin quy chiếu, không phải nội dung giải.
            attribution, _ = _pick_answers(detail)
            main = supp = None
            excerpt = str(detail.get("question") or match.get("title") or "")
            source_tier = thread_source_tier(match)
            author_name = attribution.author_name if attribution else None
            author_role = attribution.author_role if attribution else None

        suggestions.append(
            SuggestedThread(
                thread_id=thread_id,
                rank=len(suggestions) + 1,
                title=str(match.get("title") or detail.get("title") or ""),
                similarity=similarity,
                relevance=relevance,
                excerpt=excerpt,
                thread_url=str(match.get("thread_url") or detail.get("thread_url") or ""),
                source_tier=source_tier,
                thread_has_verified_answer=bool(match.get("has_verified_answer")),
                author_name=author_name,
                author_role=author_role,
                main_answer=main,
                supplementary_answer=supp,
            )
        )
    return suggestions


def build_bot_response(
    search_result: Mapping[str, Any],
    thread_details: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    status: str = "pending",
    max_threads: int = MAX_SUGGESTED_THREADS,
) -> BotResponse:
    """Dựng :class:`BotResponse` từ output của hai tool search + get_qa_thread.

    Tham số
    ----------
    search_result
        Output của ``search_qa_threads`` (có ``direct_matches`` / ``topic_matches``).
    thread_details
        Ánh xạ ``{thread_id: get_qa_thread(thread_id)}`` cho các direct match cần
        trích lời giải. Topic match không bắt buộc có chi tiết.
    status
        ``"pending"`` | ``"resolved"`` | ``"escalated"`` — quyết định có sinh nút.
    """
    direct, topic = revalidate_buckets(search_result)
    details = thread_details or {}

    tier = decide_confidence(direct, topic)
    copy = render_copy(tier)

    if tier is ConfidenceTier.NONE:
        return BotResponse(
            confidence=tier,
            headline=copy["headline"],
            note=copy["note"],
            suggestions=[],
            render_buttons=False,
            buttons=[],
            needs_human_review=True,
        )

    # Đã có thread cùng vấn đề thì KHÔNG chèn thêm thread "cùng chủ đề". Đã thử
    # cho topic reference lấp chỗ trống: eval tụt 53->52 và rớt một P0
    # (phan_tang_nguon), vì trộn hai mức độ liên quan làm thứ tự "nguồn đã xác
    # minh xếp trước" trở nên mập mờ.
    if direct:
        topic = []
    ranked = rank_for_display(direct, topic)
    suggestions = select_suggestions(ranked, details, max_threads=max_threads)

    # Tier phải khớp thứ THẬT SỰ trình ra, không khớp cờ cấp thread. Một thread
    # có has_verified_answer=true nhưng câu trả lời đã bị get_qa_thread lọc sạch
    # (noise / trùng lặp) thì không được nói "đã có lời giải".
    tier = tier_for_content(tier, suggestions)
    copy = render_copy(tier)
    if tier is ConfidenceTier.NONE:
        return BotResponse(
            confidence=tier,
            headline=copy["headline"],
            note=copy["note"],
            suggestions=[],
            render_buttons=False,
            buttons=[],
            needs_human_review=True,
        )

    buttons = decide_buttons(tier, status)
    return BotResponse(
        confidence=tier,
        headline=copy["headline"],
        note=copy["note"],
        suggestions=suggestions,
        render_buttons=bool(buttons),
        buttons=buttons,
        needs_human_review=should_escalate(tier),
    )


# ---------------------------------------------------------------------------
# Validator cứng — chạy trước khi in payload
# ---------------------------------------------------------------------------


def _iter_suggestions(response: BotResponse) -> Iterable[SuggestedThread]:
    return response.suggestions


def validate_links_present(response: BotResponse) -> None:
    """G1/G3: mỗi đề xuất phải có thread_url gốc, không rỗng."""
    for s in response.suggestions:
        if not s.thread_url:
            raise GuardrailViolation(
                f"Thread {s.thread_id} thiếu thread_url — không được hiển thị."
            )


def validate_answer_limits(response: BotResponse) -> None:
    """§8/C.4: mỗi thread tối đa 1 câu chính + 1 câu bổ sung."""
    for s in response.suggestions:
        main_count = 1 if s.main_answer else 0
        supp_count = 1 if s.supplementary_answer else 0
        if main_count > MAX_MAIN_ANSWERS or supp_count > MAX_SUPPLEMENTARY_ANSWERS:
            raise GuardrailViolation(
                f"Thread {s.thread_id} vượt giới hạn câu trả lời "
                f"({main_count} chính / {supp_count} bổ sung)."
            )


def validate_no_duplicate_answer(response: BotResponse) -> None:
    """Câu bổ sung phải khác câu chính — không trình lại cùng một nội dung."""
    for s in response.suggestions:
        main, supp = s.main_answer, s.supplementary_answer
        if main is None or supp is None:
            continue
        if main.answer_id == supp.answer_id or main.content == supp.content:
            raise GuardrailViolation(
                f"Thread {s.thread_id} trình cùng một câu trả lời ở cả vị trí "
                "chính và bổ sung."
            )


def validate_none_is_empty(response: BotResponse) -> None:
    """B.2 (lỗi nặng nhất): tier NONE phải không có gợi ý — không bịa."""
    if response.confidence is ConfidenceTier.NONE and response.suggestions:
        raise GuardrailViolation(
            "Tier NONE nhưng vẫn có gợi ý — vi phạm 'không bịa khi không biết'."
        )


def validate_topic_not_solution(response: BotResponse) -> None:
    """G/spec §15.3: topic match không được trình main_answer như lời giải."""
    for s in response.suggestions:
        if s.relevance is Relevance.TOPIC and s.main_answer is not None:
            raise GuardrailViolation(
                f"Thread {s.thread_id} là topic match nhưng lại có lời giải — "
                "topic reference không được dùng làm câu trả lời trực tiếp."
            )


def validate_no_fabrication(response: BotResponse) -> None:
    """G1: mọi đề xuất phải có thread_id; trích đoạn phải đến từ tool."""
    for s in response.suggestions:
        if not s.thread_id:
            raise GuardrailViolation("Phát hiện đề xuất không có thread_id (bịa).")
        if not s.excerpt:
            raise GuardrailViolation(
                f"Thread {s.thread_id} có trích đoạn rỗng — không in nội dung bịa."
            )


def validate_tier_matches_content(response: BotResponse) -> None:
    """Tier HIGH bắt buộc phải có lời giải đã xác minh đi kèm."""
    if response.confidence is ConfidenceTier.HIGH and not has_verified_solution(
        response.suggestions
    ):
        raise GuardrailViolation(
            "Tier HIGH nhưng không gợi ý nào có lời giải đã xác minh — "
            "không được nói 'đã có lời giải'."
        )


def enforce(response: BotResponse) -> BotResponse:
    """Chạy toàn bộ validator. Raise :class:`GuardrailViolation` nếu vi phạm.

    Gọi hàm này ngay trước khi serialize payload ra frontend/Discord. Nếu raise,
    bot phải rơi về tin nhắn an toàn (tier NONE) thay vì in payload lỗi.
    """
    validate_links_present(response)
    validate_answer_limits(response)
    validate_no_duplicate_answer(response)
    validate_none_is_empty(response)
    validate_topic_not_solution(response)
    validate_no_fabrication(response)
    validate_tier_matches_content(response)
    return response

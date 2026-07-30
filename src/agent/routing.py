"""Phân loại phạm vi câu hỏi + định tuyến người thật (Admin / Mentor / LabCoach).

Vì sao có module này: trước đây mọi lần bot "không biết" đều `tag_labcoach=true`.
Hậu quả là LabCoach bị gọi cho cả câu hỏi tỷ số bóng đá, thời tiết, hay yêu cầu
làm bài thay — trong khi ba vai trò trong corpus có địa hạt khác nhau
(``data/discord_qa_mock.json`` → ``roles``):

* **Admin** — quy định, phạm vi được phép, trật tự cộng đồng, sự kiện/BTC.
* **Mentor** — code, lỗi kỹ thuật, dựng dự án, dataset, kiến trúc sản phẩm.
* **LabCoach** — vận hành lớp học: điểm danh, nghỉ học, XP/điểm, tài liệu, deadline.

Ba nhóm hàm:

1. **Phạm vi** — :func:`classify_scope` tách câu ngoài phạm vi (tán gẫu, tài chính,
   giải trí) và câu yêu cầu bot làm bài thay (liêm chính học thuật). Cả hai
   **không** chuyển cho người thật.
2. **Định tuyến** — :func:`route_escalation` trả về :class:`EscalationDecision`
   (vai trò đích + lý do + SLA) thay cho một cờ bool duy nhất.
3. **Validator** — :func:`validate_escalation` chặn hai lỗi: escalate khi ngoài
   phạm vi/mơ hồ, và không escalate khi corpus rỗng hoặc nguồn chưa xác minh.

Bảng ánh xạ topic → vai trò **import trực tiếp** từ
``tools.detect_question_topics.tool`` (single source of truth, cùng cách
``guardrails.py`` import ngưỡng): thêm topic mới trong tool thì routing đi theo.

Yêu cầu ``PYTHONPATH=src``.
"""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

# Single source of truth: nhóm topic thật nằm trong tool detect_question_topics.
from tools.detect_question_topics.tool import (
    COURSE_POLICY_TOPICS,
    PROJECT_TOPICS,
    RESOURCE_TOPICS,
    TEAM_TOPICS,
    TECHNICAL_TOPICS,
)

from agent.guardrails import ConfidenceTier, SourceTier

__all__ = [
    # enums
    "Scope",
    "EscalationTarget",
    "EscalationReason",
    # models
    "EscalationDecision",
    # copy
    "SCOPE_COPY",
    "SOURCE_WARNING",
    "ESCALATION_SLA_MINUTES",
    # ánh xạ vai trò
    "MENTOR_TOPICS",
    "ADMIN_TOPICS",
    "LABCOACH_TOPICS",
    "MENTOR_SIGNAL_PHRASES",
    "LABCOACH_SIGNAL_PHRASES",
    # hàm
    "ascii_fold",
    "classify_scope",
    "has_verified_source",
    "route_escalation",
    "routing_prompt_block",
    "validate_escalation",
]


# ---------------------------------------------------------------------------
# Chuẩn hoá chữ (tiếng Việt viết không dấu là chuyện thường trong kênh chat)
# ---------------------------------------------------------------------------


def ascii_fold(value: str) -> str:
    """Bỏ dấu, hạ chữ thường, ``đ`` -> ``d``. Dùng chung với ``bot.py``."""
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    ).replace("đ", "d")


def _phrase_pattern(phrases: Iterable[str]) -> re.Pattern[str]:
    """Regex khớp cả cụm, có biên từ — tránh 'mua' khớp trong 'mua khoá học'."""
    alternatives = "|".join(
        re.escape(phrase) for phrase in sorted(phrases, key=len, reverse=True)
    )
    # Nhóm alternation lại: nếu không, lookbehind chỉ áp cho nhánh đầu và lookahead
    # chỉ áp cho nhánh cuối -> "tu vi" khớp trong "tu việc", "thi ho" khớp trong "thì hỏi".
    return re.compile(rf"(?<![a-z0-9])(?:{alternatives})(?![a-z0-9])")


# ---------------------------------------------------------------------------
# Enum
# ---------------------------------------------------------------------------


class Scope(str, Enum):
    """Phạm vi câu hỏi — quyết định có được đi vào pipeline tra cứu hay không."""

    IN_SCOPE = "in_scope"  #: hỏi về khoá học -> chạy detect + search
    OFF_TOPIC = "off_topic"  #: tán gẫu/thời tiết/thể thao/tài chính -> từ chối, KHÔNG escalate
    INTEGRITY = "integrity"  #: nhờ bot làm bài thay -> từ chối, KHÔNG escalate


class EscalationTarget(str, Enum):
    """Vai trò người thật nhận câu hỏi. Tên khớp ``roles[].name`` trong corpus."""

    NONE = "none"  #: không chuyển cho ai
    LABCOACH = "LabCoach"
    MENTOR = "Mentor"
    ADMIN = "Admin"


class EscalationReason(str, Enum):
    NO_SOURCE = "no_source"  #: corpus rỗng -> cần người trả lời mới
    UNVERIFIED_SOURCE = "unverified_source"  #: chỉ có học viên trả lời -> cần xác minh
    LEARNER_REQUEST = "learner_request"  #: học viên bấm "Chưa đúng ý tôi"
    NOT_NEEDED = "not_needed"  #: đã có nguồn xác minh, hoặc câu bị từ chối


#: SLA mục tiêu theo vai trò. LabCoach 25 phút lấy từ spec §8; hai mốc còn lại là
#: **đề xuất** (Mentor/Admin không trực kênh liên tục) — sửa khi vận hành chốt.
ESCALATION_SLA_MINUTES: dict[EscalationTarget, int | None] = {
    EscalationTarget.NONE: None,
    EscalationTarget.LABCOACH: 25,
    EscalationTarget.MENTOR: 120,
    EscalationTarget.ADMIN: 240,
}

#: Nhãn cảnh báo bắt buộc khi thread chỉ có học viên trả lời (spec §5 ưu tiên 2).
SOURCE_WARNING = "⚠️ Chia sẻ từ cộng đồng — chưa được xác minh"

#: Văn án từ chối cho câu ngoài phạm vi. Không escalate, không sinh nút.
SCOPE_COPY: dict[Scope, dict[str, str]] = {
    Scope.OFF_TOPIC: {
        "headline": "Câu này nằm ngoài phạm vi hỏi đáp của khoá học",
        "note": (
            "Mình chỉ tra cứu được các thread cũ trong kênh Hỏi đáp của khoá học. "
            "Bạn thử hỏi lại về bài học, dự án hoặc quy định của khoá nhé."
        ),
    },
    Scope.INTEGRITY: {
        "headline": "Mình không làm bài thay bạn được",
        "note": (
            "Mình chỉ tìm lại thread cũ đã có lời giải, không viết bài / làm bài tập hộ. "
            "Nếu bạn đang mắc ở một bước cụ thể, gửi mình lỗi hoặc đoạn code đang vướng nhé."
        ),
    },
}


# ---------------------------------------------------------------------------
# Từ khoá phạm vi
# ---------------------------------------------------------------------------

#: Câu hỏi kiến thức chung / tán gẫu — DupBot không phải chatbot tri thức chung.
OFF_TOPIC_PHRASES: frozenset[str] = frozenset(
    {
        # thời tiết
        "troi mua", "troi nang", "thoi tiet", "co mua khong", "bao so", "nhiet do hom nay",
        # thể thao
        "bong da", "ty so", "world cup", "ngoai hang anh", "premier league",
        "doi tuyen", "the thao", "ket qua tran",
        # tài chính / đầu tư
        "bitcoin", "crypto", "tien ao", "chung khoan", "co phieu", "forex",
        "gia vang", "lai suat ngan hang",
        # giải trí / đời sống
        "xem phim", "bo phim", "choi game", "tro choi", "xo so", "quan an ngon",
        "tin tuc hom nay", "tu vi", "bong ro",
    }
)

#: Yêu cầu bot **sản xuất bài làm** thay học viên.
INTEGRITY_PHRASES: frozenset[str] = frozenset(
    {
        "viet ho", "viet gium", "viet thay", "viet luan", "viet bai luan",
        "lam ho", "lam gium", "lam thay", "lam bai thay", "lam bai tap ho",
        "lam ho bai", "lam gium bai", "lam luan van", "lam do an ho",
        "giai ho", "giai gium", "giai bai tap ho", "giai thay",
        "code ho", "code gium", "code thay", "thi ho", "lam bai kiem tra ho",
    }
)

#: Câu **hỏi về quy định** thường chứa các dấu hiệu này ("có được ... hộ không").
#: Có dấu hiệu -> KHÔNG xếp vào INTEGRITY, vì học viên đang hỏi luật chứ không
#: nhờ bot làm bài (ví dụ TC-029 "… có bị coi là gian lận không").
POLICY_MARKERS: frozenset[str] = frozenset(
    {
        "co duoc", "duoc phep", "co bi", "co hop le", "co vi pham", "co bi coi la",
        "quy dinh", "co sao khong", "co anh huong", "co tinh", "co bi tru",
    }
)

OFF_TOPIC_PATTERN = _phrase_pattern(OFF_TOPIC_PHRASES)
INTEGRITY_PATTERN = _phrase_pattern(INTEGRITY_PHRASES)
POLICY_PATTERN = _phrase_pattern(POLICY_MARKERS)


def classify_scope(question: str) -> Scope:
    """Xác định phạm vi trước khi tra cứu.

    Thứ tự kiểm: liêm chính học thuật -> ngoài phạm vi -> trong phạm vi. Câu chứa
    dấu hiệu hỏi quy định (:data:`POLICY_MARKERS`) luôn được coi là trong phạm vi,
    kể cả khi có động từ "làm hộ" — học viên đang hỏi luật, không nhờ làm bài.
    """
    folded = ascii_fold(question)
    if POLICY_PATTERN.search(folded):
        return Scope.IN_SCOPE
    if INTEGRITY_PATTERN.search(folded):
        return Scope.INTEGRITY
    if OFF_TOPIC_PATTERN.search(folded):
        return Scope.OFF_TOPIC
    return Scope.IN_SCOPE


# ---------------------------------------------------------------------------
# Ánh xạ topic -> vai trò
# ---------------------------------------------------------------------------

#: Mentor: kỹ thuật + dựng dự án (dùng nguyên hai nhóm topic của tool).
MENTOR_TOPICS: frozenset[str] = frozenset(TECHNICAL_TOPICS | PROJECT_TOPICS)

#: Admin: thành phần nhóm và trật tự cộng đồng. ``lam_viec_nhom`` (cách phối hợp
#: trong nhóm) là việc coaching nên để LabCoach, không đưa vào đây.
ADMIN_TOPICS: frozenset[str] = frozenset(TEAM_TOPICS - {"lam_viec_nhom"})

#: LabCoach: vận hành lớp, điểm/XP, tài liệu, hỗ trợ — phần còn lại của taxonomy.
LABCOACH_TOPICS: frozenset[str] = frozenset(
    COURSE_POLICY_TOPICS | RESOURCE_TOPICS | {"lam_viec_nhom", "ticket"}
)

#: Từ khoá thuộc địa hạt Admin dù topic detect ra là "other" (corpus không có
#: thread nào về mấy chuyện này — chính là nhóm câu no_source hay gặp).
ADMIN_PHRASES: frozenset[str] = frozenset(
    {
        "hoc phi", "hoan tien", "hoc bong", "chung chi", "bang tot nghiep",
        "nguoi ngoai khoa", "nguoi ngoai nhom", "khach moi", "chuyen lop",
        "quy che", "noi quy", "ky luat", "canh cao", "cam thi", "spam kenh",
        "trat tu", "bao cao vi pham", "gian lan", "sao chep bai",
        "le trao giai", "trao giai", "giai thuong", "ban to chuc", "btc",
        "doi thong tin ca nhan", "bao mat du lieu",
    }
)

#: Dấu hiệu kỹ thuật **mạnh** — đủ đặc trưng để ghi đè cả topic detect được, vì
#: topic hay bị gom vào nhóm "khác" trong khi câu hỏi rõ ràng là việc của Mentor
#: (ví dụ "lỗi font tiếng Việt khi export pdf").
MENTOR_SIGNAL_PHRASES: frozenset[str] = frozenset(
    {
        "stack trace", "traceback", "exception", "syntax error", "compile",
        "crash", "segfault", "encoding", "utf 8", "utf8", "loi font",
        "export pdf", "import error", "module not found", "npm", "pip install",
        "docker", "merge conflict", "deploy", "endpoint", "database", "sql",
    }
)

#: Từ khoá Mentor **yếu** — chỉ dùng khi topic không xếp được vào địa hạt nào.
MENTOR_PHRASES: frozenset[str] = frozenset(
    {
        "code", "debug", "build", "api", "model", "train model", "fine tune",
        "embedding", "dataset", "kien truc", "kien truc san pham", "refactor",
        "thu vien", "package", "version", "prototype", "repo", "branch",
        "cau hinh may", "cai dat moi truong", "phien ban python",
    }
)

#: Dấu hiệu vận hành lớp **mạnh** (lịch, hạn nộp, điểm danh). Ghi đè topic vì một
#: câu hỏi giờ học của Giai đoạn 2 là việc của LabCoach, không phải Mentor.
LABCOACH_SIGNAL_PHRASES: frozenset[str] = frozenset(
    {
        "may gio", "lich hoc", "lich thi", "thoi khoa bieu", "deadline",
        "han nop", "gia han", "diem danh", "nghi hoc", "vang hoc",
        "xin phep vang", "buoi hoc bu",
    }
)

#: Từ khoá vận hành lớp **yếu** — kiểm TRƯỚC Mentor yếu để "nộp sản phẩm" không bị
#: đẩy sang Mentor chỉ vì có chữ "sản phẩm".
LABCOACH_PHRASES: frozenset[str] = frozenset(
    {
        "nop bai", "nop san pham", "buoi hoc", "diem so", "bang diem", "xp",
        "slide", "tai lieu", "recording", "ghi am", "ho tro", "ticket",
    }
)

ADMIN_PHRASE_PATTERN = _phrase_pattern(ADMIN_PHRASES)
LABCOACH_SIGNAL_PATTERN = _phrase_pattern(LABCOACH_SIGNAL_PHRASES)
MENTOR_SIGNAL_PATTERN = _phrase_pattern(MENTOR_SIGNAL_PHRASES)
MENTOR_PHRASE_PATTERN = _phrase_pattern(MENTOR_PHRASES)
LABCOACH_PHRASE_PATTERN = _phrase_pattern(LABCOACH_PHRASES)

#: Intent của ``detect_question_topics`` -> vai trò. Chỉ dùng khi topic_id không
#: đủ để quyết (chế độ local fallback luôn trả intent="OTHER").
INTENT_TARGET: dict[str, EscalationTarget] = {
    "TECHNICAL_ERROR": EscalationTarget.MENTOR,
    "PROJECT_SCOPE": EscalationTarget.MENTOR,
    "TEAM_MANAGEMENT": EscalationTarget.ADMIN,
    "COURSE_POLICY": EscalationTarget.LABCOACH,
    "RESOURCE_LOOKUP": EscalationTarget.LABCOACH,
    "SUPPORT_REQUEST": EscalationTarget.LABCOACH,
}


class EscalationDecision(BaseModel):
    """Kết quả định tuyến: chuyển cho ai, vì sao, chờ bao lâu."""

    model_config = ConfigDict(extra="forbid")

    target: EscalationTarget
    reason: EscalationReason
    sla_minutes: int | None = None
    note: str | None = Field(
        default=None, description="Câu giải thích hiển thị cho học viên."
    )

    @property
    def tagged(self) -> bool:
        """Có chuyển cho người thật hay không (trường ``tag_labcoach`` cũ)."""
        return self.target is not EscalationTarget.NONE


def _target_for_domain(
    question: str, primary_topic_id: str | None, intent: str | None
) -> EscalationTarget:
    """Chọn vai trò theo địa hạt.

    Thứ tự ưu tiên: từ khoá Admin > dấu hiệu vận hành/kỹ thuật mạnh > topic >
    từ khoá vận hành yếu > từ khoá Mentor yếu > intent > LabCoach (mặc định).
    """
    folded = ascii_fold(question)

    # Quy định / trật tự / sự kiện luôn là việc của Admin, kể cả khi topic khác.
    if ADMIN_PHRASE_PATTERN.search(folded):
        return EscalationTarget.ADMIN
    if LABCOACH_SIGNAL_PATTERN.search(folded):
        return EscalationTarget.LABCOACH
    if MENTOR_SIGNAL_PATTERN.search(folded):
        return EscalationTarget.MENTOR

    topic = (primary_topic_id or "other").strip()
    if topic in ADMIN_TOPICS:
        return EscalationTarget.ADMIN
    if topic in MENTOR_TOPICS:
        return EscalationTarget.MENTOR
    if topic in LABCOACH_TOPICS:
        return EscalationTarget.LABCOACH

    if LABCOACH_PHRASE_PATTERN.search(folded):
        return EscalationTarget.LABCOACH
    if MENTOR_PHRASE_PATTERN.search(folded):
        return EscalationTarget.MENTOR

    mapped = INTENT_TARGET.get((intent or "").upper())
    if mapped is not None:
        return mapped

    # Không xác định được địa hạt -> LabCoach là cửa vào mặc định của khoá.
    return EscalationTarget.LABCOACH


_REASON_NOTE = {
    EscalationReason.NO_SOURCE: (
        "Chưa có thread nào trong kênh trả lời câu này nên mình chuyển thẳng cho {target}."
    ),
    EscalationReason.UNVERIFIED_SOURCE: (
        "Các thread trên chỉ có học viên trả lời, chưa ai xác minh — mình đã nhờ "
        "{target} xác nhận lại."
    ),
    EscalationReason.LEARNER_REQUEST: (
        "Bạn cho biết gợi ý chưa đúng ý nên mình chuyển cho {target}."
    ),
}


def route_escalation(
    *,
    question: str,
    scope: Scope = Scope.IN_SCOPE,
    tier: ConfidenceTier | None = None,
    primary_topic_id: str | None = None,
    intent: str | None = None,
    suggestions: Iterable[Mapping[str, object]] | None = None,
    learner_requested: bool = False,
) -> EscalationDecision:
    """Quyết định chuyển câu hỏi cho ai.

    Quy tắc (theo ``Bot_System_Instructions.md`` §11):

    * ``scope`` ≠ IN_SCOPE -> **không** chuyển cho ai. Đây là lỗi "gọi LabCoach vô
      tội vạ": tỷ số bóng đá không phải việc của LabCoach.
    * Học viên bấm "Chưa đúng ý tôi" -> chuyển theo địa hạt.
    * ``tier`` NONE (corpus rỗng) -> chuyển theo địa hạt, lý do ``no_source``.
    * Có gợi ý nhưng **không có nguồn xác minh** -> vẫn hiển thị, đồng thời chuyển
      để xác minh, lý do ``unverified_source``.
    * Có nguồn xác minh -> không chuyển, để hai nút cho học viên tự quyết.

    Câu mơ hồ (``too_vague``) không đi qua hàm này: bot hỏi lại trước đã.
    """
    if scope is not Scope.IN_SCOPE:
        return EscalationDecision(
            target=EscalationTarget.NONE, reason=EscalationReason.NOT_NEEDED
        )

    items = list(suggestions or [])
    if learner_requested:
        reason = EscalationReason.LEARNER_REQUEST
    elif tier is ConfidenceTier.NONE or not items:
        reason = EscalationReason.NO_SOURCE
    elif not has_verified_source(items):
        reason = EscalationReason.UNVERIFIED_SOURCE
    else:
        return EscalationDecision(
            target=EscalationTarget.NONE, reason=EscalationReason.NOT_NEEDED
        )

    target = _target_for_domain(question, primary_topic_id, intent)
    return EscalationDecision(
        target=target,
        reason=reason,
        sla_minutes=ESCALATION_SLA_MINUTES[target],
        note=_REASON_NOTE[reason].format(target=target.value),
    )


def has_verified_source(suggestions: Iterable[Mapping[str, object]]) -> bool:
    """True nếu có ít nhất một gợi ý đến từ nguồn đã xác minh.

    Nhận cả payload guardrail (``source_tier``) và payload legacy (``verified``).
    """
    for item in suggestions:
        tier = item.get("source_tier")
        if tier == SourceTier.VERIFIED or tier == SourceTier.VERIFIED.value:
            return True
        if item.get("verified") is True:
            return True
    return False


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class EscalationViolation(Exception):
    """Định tuyến sai — chặn trước khi gửi cho người thật."""


def validate_escalation(
    decision: EscalationDecision,
    *,
    scope: Scope,
    tier: ConfidenceTier,
    suggestions: Iterable[Mapping[str, object]] | None = None,
) -> EscalationDecision:
    """Chặn hai lỗi đối xứng: gọi người khi không cần, và không gọi khi cần."""
    items = list(suggestions or [])

    if scope is not Scope.IN_SCOPE and decision.tagged:
        raise EscalationViolation(
            f"Câu ngoài phạm vi ({scope.value}) nhưng vẫn chuyển cho "
            f"{decision.target.value} — không được làm mất thời gian người thật."
        )
    if scope is Scope.IN_SCOPE and tier is ConfidenceTier.NONE and not decision.tagged:
        raise EscalationViolation(
            "Corpus rỗng nhưng không chuyển cho ai — học viên sẽ không có ai trả lời."
        )
    if (
        scope is Scope.IN_SCOPE
        and items
        and not has_verified_source(items)
        and not decision.tagged
    ):
        raise EscalationViolation(
            "Chỉ có câu trả lời của học viên nhưng không nhờ ai xác minh."
        )
    return decision


# ---------------------------------------------------------------------------
# Khối prompt (để system_prompt.py inject, không viết tay lần hai)
# ---------------------------------------------------------------------------


def routing_prompt_block() -> str:
    """Bảng định tuyến dạng text, sinh từ chính các hằng số ở trên."""
    return f"""ĐỊNH TUYẾN NGƯỜI THẬT (không phải cứ bí là gọi LabCoach):
- Admin  — quy định, phạm vi được phép, trật tự cộng đồng, sự kiện/BTC. Topic: {", ".join(sorted(ADMIN_TOPICS))}.
- Mentor — code, lỗi kỹ thuật, dựng dự án, dataset, kiến trúc. Topic: {", ".join(sorted(MENTOR_TOPICS))}.
- LabCoach — vận hành lớp: điểm danh, nghỉ học, XP/điểm, tài liệu, deadline, ticket. Topic: {", ".join(sorted(LABCOACH_TOPICS))}.
- KHI NÀO CHUYỂN: corpus rỗng (no_source) · chỉ có học viên trả lời (unverified_source, vẫn hiển thị kèm "{SOURCE_WARNING}") · học viên bấm "Chưa đúng ý tôi".
- KHI NÀO KHÔNG CHUYỂN CHO AI: câu ngoài phạm vi khoá học (thời tiết, thể thao, tài chính, giải trí) · câu nhờ bot làm bài thay · câu quá mơ hồ (hỏi lại trước).

NGOÀI PHẠM VI (reason=out_of_scope, KHÔNG gợi ý, KHÔNG chuyển ai, KHÔNG sinh nút):
- Tán gẫu / kiến thức chung: "{SCOPE_COPY[Scope.OFF_TOPIC]["headline"]}".
- Nhờ làm bài thay (viết hộ, làm hộ, giải hộ, thi hộ): "{SCOPE_COPY[Scope.INTEGRITY]["headline"]}".
- Nhưng câu HỎI VỀ QUY ĐỊNH ("có được … không", "có bị coi là gian lận không") là TRONG phạm vi -> vẫn tra cứu."""

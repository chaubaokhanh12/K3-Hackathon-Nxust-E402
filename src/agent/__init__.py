"""DupBot Agent layer — System Prompt và Guardrails cho TrustQA MVP.

Package này biến tài liệu ``Bot_System_Instructions.md`` thành code chạy được:
- :mod:`agent.guardrails` — logic quyết định (tier confidence, sinh nút, xếp hạng)
  và validator cứng. Lấy ngưỡng trực tiếp từ ``tools.*`` nên không bao giờ lệch.
- :mod:`agent.system_prompt` — nội dung System Prompt, được dựng từ cùng bộ ngưỡng.

Không sửa code trong ``tools`` hay ``frontend``; layer này chỉ tiêu thụ output của
chúng qua contract JSON.
"""

from agent.guardrails import (
    ANSWER_SOURCE_TIER,
    BOT_COPY,
    BUTTONS,
    MAX_SUGGESTED_THREADS,
    AnswerSummary,
    BotResponse,
    ButtonSpec,
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
    has_verified_solution,
    rank_for_display,
    render_copy,
    revalidate_buckets,
    select_suggestions,
    should_escalate,
    thread_source_tier,
)
from agent.routing import (
    ESCALATION_SLA_MINUTES,
    SCOPE_COPY,
    SOURCE_WARNING,
    EscalationDecision,
    EscalationReason,
    EscalationTarget,
    EscalationViolation,
    Scope,
    classify_scope,
    has_verified_source,
    route_escalation,
    validate_escalation,
)
from agent.synthesis import (
    INSUFFICIENT_SOURCE_TOKEN,
    SYNTHESIS_ERRORS,
    SYNTHESIS_SYSTEM_PROMPT,
    build_synthesis_prompt,
    synthesize_answer,
    validate_grounding,
)
from agent.system_prompt import SYSTEM_PROMPT, build_system_prompt

__all__ = [
    # system prompt
    "SYSTEM_PROMPT",
    "build_system_prompt",
    # enums / constants
    "ConfidenceTier",
    "SourceTier",
    "Relevance",
    "Scope",
    "EscalationTarget",
    "EscalationReason",
    "ESCALATION_SLA_MINUTES",
    "SCOPE_COPY",
    "SOURCE_WARNING",
    "MAX_SUGGESTED_THREADS",
    "BOT_COPY",
    "render_copy",
    "BUTTONS",
    "ANSWER_SOURCE_TIER",
    # models
    "AnswerSummary",
    "SuggestedThread",
    "ButtonSpec",
    "BotResponse",
    "GuardrailViolation",
    "EscalationDecision",
    "EscalationViolation",
    # decision functions
    "classify_scope",
    "route_escalation",
    "has_verified_source",
    "validate_escalation",
    "classify_relevance",
    "revalidate_buckets",
    "answer_source_tier",
    "thread_source_tier",
    "rank_for_display",
    "select_suggestions",
    "decide_confidence",
    "has_verified_solution",
    "decide_buttons",
    "should_escalate",
    "build_bot_response",
    "enforce",
    # synthesis (RAG)
    "SYNTHESIS_SYSTEM_PROMPT",
    "SYNTHESIS_ERRORS",
    "INSUFFICIENT_SOURCE_TOKEN",
    "build_synthesis_prompt",
    "synthesize_answer",
    "validate_grounding",
]

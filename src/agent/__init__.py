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
    rank_for_display,
    select_suggestions,
    should_escalate,
    thread_source_tier,
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
    "MAX_SUGGESTED_THREADS",
    "BOT_COPY",
    "BUTTONS",
    "ANSWER_SOURCE_TIER",
    # models
    "AnswerSummary",
    "SuggestedThread",
    "ButtonSpec",
    "BotResponse",
    "GuardrailViolation",
    # decision functions
    "classify_relevance",
    "answer_source_tier",
    "thread_source_tier",
    "rank_for_display",
    "select_suggestions",
    "decide_confidence",
    "decide_buttons",
    "should_escalate",
    "build_bot_response",
    "enforce",
]

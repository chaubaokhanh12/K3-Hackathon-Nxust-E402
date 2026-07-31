"""Adapter sinh văn bản (LLM) cho tầng tổng hợp câu trả lời.

Tách riêng khỏi ``embeddings.py`` vì hai thứ này hỏng độc lập nhau: mất quyền
gọi Chat Completions **không** được kéo sập retrieval. ``bot.py`` bắt lỗi ở đây
rồi bỏ qua phần tổng hợp, gợi ý trích nguyên văn vẫn trả về bình thường.
"""

from __future__ import annotations

import os
from typing import Protocol

from openai import OpenAI

#: Placeholder ``model-llm`` trong .env cũ không phải model thật. Dùng default
#: này khi OPENAI_MODEL trống hoặc rõ ràng là chỗ điền chưa thay.
DEFAULT_GENERATION_MODEL = "gpt-4o-mini"
PLACEHOLDER_MODEL_NAMES = frozenset({"model-llm", "your-model", "changeme"})

#: Câu trả lời tổng hợp là bản tóm tắt vài gạch đầu dòng, không phải bài viết.
#: Giới hạn thấp giữ độ trễ trong ngưỡng chat và chặn LLM kể lể ngoài nguồn.
MAX_OUTPUT_TOKENS = 700
#: Nhiệm vụ là diễn đạt lại nội dung đã có, không phải sáng tác: temperature
#: thấp để cùng một câu hỏi cho ra cùng một câu trả lời giữa các lần chấm.
TEMPERATURE = 0.2
REQUEST_TIMEOUT_SECONDS = 20.0


class GeneratorConfigurationError(RuntimeError):
    """Raised when a text-generation provider is not configured."""


class GenerationResponseError(RuntimeError):
    """Raised when a text-generation provider returns malformed data."""


class AnswerGenerator(Protocol):
    model_name: str

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return the model's reply text for one prompt pair."""


def resolve_model_name(model_name: str | None = None) -> str:
    candidate = (model_name or os.getenv("OPENAI_MODEL") or "").strip()
    if not candidate or candidate.lower() in PLACEHOLDER_MODEL_NAMES:
        return DEFAULT_GENERATION_MODEL
    return candidate


class OpenAIAnswerGenerator:
    """OpenAI Chat Completions adapter."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_name: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if client is None and not resolved_key:
            raise GeneratorConfigurationError(
                "OPENAI_API_KEY is required when using the default OpenAI generator"
            )

        self.model_name = resolve_model_name(model_name)
        self._client = client or OpenAI(api_key=resolved_key)

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        completion = self._client.chat.completions.create(
            model=self.model_name,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            timeout=REQUEST_TIMEOUT_SECONDS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        choices = getattr(completion, "choices", None) or []
        if not choices:
            raise GenerationResponseError("Provider returned no choices")

        content = getattr(choices[0].message, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise GenerationResponseError("Provider returned an empty message")
        return content.strip()


__all__ = [
    "AnswerGenerator",
    "DEFAULT_GENERATION_MODEL",
    "GenerationResponseError",
    "GeneratorConfigurationError",
    "MAX_OUTPUT_TOKENS",
    "OpenAIAnswerGenerator",
    "TEMPERATURE",
    "resolve_model_name",
]

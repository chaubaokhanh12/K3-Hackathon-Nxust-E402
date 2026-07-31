"""Translation service for multilingual query support.

Module này cung cấp translation service để convert English queries sang Vietnamese,
giúp improve semantic search accuracy khi user hỏi bằng tiếng Anh.

Yêu cầu PYTHONPATH=src.
"""

from __future__ import annotations

import os
from typing import Protocol

from openai import OpenAI


__all__ = [
    "TranslationService",
    "OpenAITranslator",
    "NullTranslator",
    "create_translator",
]


class TranslationService(Protocol):
    """Protocol cho translation service."""

    def detect_language(self, text: str) -> str:
        """Detect language of input text.

        Returns:
            Language code (e.g., "vi", "en", "fr", etc.)
        """
        ...

    def translate_to_vietnamese(self, text: str, source_lang: str | None = None) -> str:
        """Translate text to Vietnamese.

        Args:
            text: Input text to translate
            source_lang: Source language code (optional, auto-detected if None)

        Returns:
            Translated text in Vietnamese
        """
        ...


class NullTranslator:
    """No-op translator used when translation is disabled."""

    def detect_language(self, text: str) -> str:
        """Always return "vi" (no-op)."""
        return "vi"

    def translate_to_vietnamese(self, text: str, source_lang: str | None = None) -> str:
        """Return original text (no-op)."""
        return text


class OpenAITranslator:
    """OpenAI-based translation service."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize OpenAI translator.

        Args:
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            model: Model name for translation (default: gpt-4o-mini)
        """
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when using OpenAI translator"
            )

        self.client = OpenAI(api_key=resolved_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def detect_language(self, text: str) -> str:
        """Detect language using simple heuristic.

        For now, uses ASCII vs non-ASCII character detection:
        - Mostly ASCII characters -> assume English ("en")
        - Contains Vietnamese characters -> assume Vietnamese ("vi")

        This is a fast, cost-effective heuristic. For production,
        consider using dedicated language detection library.
        """
        # Check for Vietnamese-specific characters
        vietnamese_chars = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
        text_lower = text.lower()

        # If text contains Vietnamese characters, it's Vietnamese
        if any(char in vietnamese_chars for char in text_lower):
            return "vi"

        # If text is mostly ASCII, assume it's English
        # (This is a simplification - could be French, Spanish, etc.)
        ascii_ratio = sum(ord(c) < 128 for c in text) / len(text) if text else 0
        if ascii_ratio > 0.8:
            return "en"

        # Default: assume Vietnamese for this course's context
        return "vi"

    def translate_to_vietnamese(self, text: str, source_lang: str | None = None) -> str:
        """Translate text to Vietnamese using OpenAI.

        Uses chat completion for high-quality translation that preserves
        technical terms and context better than literal translation.
        """
        detected = source_lang or self.detect_language(text)

        # Already Vietnamese, no need to translate
        if detected == "vi":
            return text

        try:
            system_prompt = """Bạn là bilingual translator chuyên dịch câu hỏi từ tiếng Anh sang tiếng Việt trong ngữ cảnh khóa học AI.

QUY TẂC DỊCH:
1. Dịch sát nghĩa nhưng tự nhiên tiếng Việt
2. GIỮ NGUYÊN thuật ngữ kỹ thuật: API key, embedding, dataset, model, GitHub, git, deadline, XP, LabCoach, Mentor, etc.
3. GIỮ NGUYÊM tên riêng: OpenAI, Anthropic, Claude, GPT, etc.
4. Chỉ dịch, KHÔNG giải thích hay thêm bớt nội dung
5. Trả về DUỘI CÂU ĐÃ DỊCH, không có thêm text nào khác

Ví dụ:
- "I want to ask how to take a leave of absence" → "Tôi muốn hỏi cách xin nghỉ học"
- "How to fix Missing credentials error" → "Cách fix lỗi Missing credentials"
- "When is the deadline for project submission?" → "Deadline nộp dự án là khi nào?" """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,  # Low temperature for consistent translation
                max_tokens=500,
            )

            translated = response.choices[0].message.content.strip()
            return translated

        except Exception as e:
            # Fallback: return original text if translation fails
            raise RuntimeError(f"Translation failed: {e}")


def create_translator(
    *, service: str | None = None, **kwargs
) -> TranslationService:
    """Factory function để tạo translator instance.

    Args:
        service: Service type ("openai", "null", or None)
        **kwargs: Additional arguments passed to translator constructor

    Returns:
        TranslationService instance
    """
    config = service or os.getenv("TRANSLATION_SERVICE", "null")

    if config.lower() == "openai":
        return OpenAITranslator(**kwargs)
    else:
        return NullTranslator()

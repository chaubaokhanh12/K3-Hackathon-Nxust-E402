"""Cấu hình chung cho pytest.

Tắt tầng tổng hợp LLM trong suốt test suite. Lý do: ``bot.answer`` tự dựng
``OpenAIAnswerGenerator`` khi thấy ``OPENAI_API_KEY``, nên chỉ cần lập trình
viên có ``.env`` là unit test bắt đầu gọi mạng thật — chậm, tốn tiền, và kết
quả phụ thuộc vào model.

Test nào cần kiểm tra tầng tổng hợp thì **tiêm generator giả** qua
``answer(..., generator=...)``; đường đó không đọc cờ này nên vẫn chạy.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_llm_synthesis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DUPBOT_SYNTHESIS", "0")

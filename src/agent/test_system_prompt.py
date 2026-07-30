"""Test cho agent.system_prompt — prompt dựng đúng và inject ngưỡng thật."""

from __future__ import annotations

import pytest

from agent.system_prompt import SYSTEM_PROMPT, build_system_prompt


def test_module_constant_equals_builder():
    assert SYSTEM_PROMPT == build_system_prompt()


def test_prompt_non_empty_and_bounded():
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 500
    # Guard tràn token: không nên quá dài cho system prompt.
    assert len(SYSTEM_PROMPT) < 8000


def test_prompt_contains_persona_and_role():
    assert "DupBot" in SYSTEM_PROMPT
    assert "mình" in SYSTEM_PROMPT


def test_prompt_contains_real_thresholds():
    # Ngưỡng phải được inject từ tools, không phải hardcode ước lượng.
    assert "0.78" in SYSTEM_PROMPT
    assert "0.40" in SYSTEM_PROMPT
    assert "0.50" in SYSTEM_PROMPT


def test_prompt_contains_three_tiers_and_buttons():
    for tier in ("HIGH", "LOW", "NONE"):
        assert tier in SYSTEM_PROMPT
    assert "Đã giải quyết được" in SYSTEM_PROMPT
    assert "Chưa đúng ý tôi" in SYSTEM_PROMPT


def test_prompt_forbids_fabrication_and_topic_as_answer():
    assert "KHÔNG bịa" in SYSTEM_PROMPT
    assert "topic match" in SYSTEM_PROMPT.lower() or "Topic match" in SYSTEM_PROMPT


def test_prompt_lists_verified_roles():
    # Mọi vai trò đã xác minh phải xuất hiện để LLM biết ranh giới nguồn.
    for role in ("Admin", "Mentor", "LabCoach"):
        assert role in SYSTEM_PROMPT
    assert "BTC" in SYSTEM_PROMPT


def test_prompt_contains_routing_table():
    # Prompt phải nói rõ ba địa hạt, nếu không LLM lại mặc định gọi LabCoach.
    assert "ĐỊNH TUYẾN NGƯỜI THẬT" in SYSTEM_PROMPT
    assert "unverified_source" in SYSTEM_PROMPT
    assert "out_of_scope" in SYSTEM_PROMPT
    assert "làm bài thay" in SYSTEM_PROMPT


def test_prompt_requires_tool_order():
    assert "detect_question_topics" in SYSTEM_PROMPT
    assert "search_qa_threads" in SYSTEM_PROMPT
    assert "get_qa_thread" in SYSTEM_PROMPT

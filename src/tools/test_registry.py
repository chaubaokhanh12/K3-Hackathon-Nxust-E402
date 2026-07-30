from __future__ import annotations

from tools import TOOL_REGISTRY


def test_registry_exposes_three_agent_ready_tools() -> None:
    assert [tool["name"] for tool in TOOL_REGISTRY] == [
        "detect_question_topics",
        "search_qa_threads",
        "get_qa_thread",
    ]

    for tool in TOOL_REGISTRY:
        assert isinstance(tool["description"], str)
        assert len(tool["description"]) >= 40
        assert tool["input_schema"]["type"] == "object"
        assert tool["input_schema"]["additionalProperties"] is False
        assert callable(tool["execute"])

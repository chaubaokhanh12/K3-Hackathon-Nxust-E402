"""Framework-independent TrustQA tool registry."""

from tools.detect_question_topics import (
    TOOL_DEFINITION as DETECT_QUESTION_TOPICS_TOOL,
)
from tools.get_qa_thread import TOOL_DEFINITION as GET_QA_THREAD_TOOL
from tools.search_qa_threads import TOOL_DEFINITION as SEARCH_QA_THREADS_TOOL


TOOL_REGISTRY = [
    DETECT_QUESTION_TOPICS_TOOL,
    SEARCH_QA_THREADS_TOOL,
    GET_QA_THREAD_TOOL,
]

__all__ = [
    "DETECT_QUESTION_TOPICS_TOOL",
    "GET_QA_THREAD_TOOL",
    "SEARCH_QA_THREADS_TOOL",
    "TOOL_REGISTRY",
]


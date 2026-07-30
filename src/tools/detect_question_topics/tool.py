from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tools._shared.embeddings import CachedEmbedder, Embedder, OpenAIEmbedder
from tools._shared.repository import CorpusRepository
from tools._shared.similarity import cosine_similarity


DESCRIPTION = (
    "Analyze a learner question before retrieval. Select the primary topic and "
    "optional subtopics only from the TrustQA corpus taxonomy, infer a stable "
    "intent, and return a normalized query. Use this tool before "
    "search_qa_threads."
)

PRIMARY_TOPIC_THRESHOLD = 0.35
SUBTOPIC_THRESHOLD = 0.45
SUBTOPIC_MAX_DISTANCE = 0.25

TOPIC_NAMES = {
    "ai_log_setup": "Thiết lập AI log",
    "ao_khoa": "Áo khóa học",
    "api_key": "API key",
    "brd_prd": "BRD và PRD",
    "cham_diem": "Chấm điểm",
    "dataset": "Dataset",
    "de_tai_khoa_truoc": "Đề tài khóa trước",
    "deps_error": "Lỗi thư viện và dependency",
    "diem_danh": "Điểm danh",
    "doi_ten_nhom": "Đổi tên nhóm",
    "ghep_team": "Ghép team",
    "giai_doan_2": "Giai đoạn 2",
    "git_workflow": "Quy trình Git",
    "lam_viec_nhom": "Làm việc nhóm",
    "le_khac": "Lễ và lịch nghỉ",
    "mentor_duty": "Vai trò Mentor",
    "nghi_hoc": "Nghỉ học",
    "nguon_hoc_ai": "Nguồn học AI",
    "phoenix_loi": "Lỗi Phoenix",
    "requirement_project": "Yêu cầu dự án",
    "roi_nhom": "Rời nhóm",
    "tai_lieu_buoi_hoc": "Tài liệu buổi học",
    "ticket": "Ticket hỗ trợ",
    "vlearn_slide": "Slide trên VLearn",
    "xp_diem": "Điểm XP",
    "other": "Khác",
}

TECHNICAL_TOPICS = {"api_key", "deps_error", "git_workflow", "phoenix_loi"}
PROJECT_TOPICS = {
    "brd_prd",
    "dataset",
    "de_tai_khoa_truoc",
    "giai_doan_2",
    "requirement_project",
}
TEAM_TOPICS = {"doi_ten_nhom", "ghep_team", "lam_viec_nhom", "roi_nhom"}
COURSE_POLICY_TOPICS = {
    "ao_khoa",
    "cham_diem",
    "diem_danh",
    "le_khac",
    "mentor_duty",
    "nghi_hoc",
    "xp_diem",
}
RESOURCE_TOPICS = {"nguon_hoc_ai", "tai_lieu_buoi_hoc", "vlearn_slide"}


class DetectQuestionTopicsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=8_000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        normalized = _normalize_query(value)
        if not normalized:
            raise ValueError("question must contain non-whitespace text")
        return normalized


def _normalize_query(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _topic_name(topic_id: str) -> str:
    return TOPIC_NAMES.get(topic_id, topic_id.replace("_", " ").title())


def _infer_intent(topic_id: str) -> str:
    if topic_id in TECHNICAL_TOPICS:
        return "TECHNICAL_ERROR"
    if topic_id in PROJECT_TOPICS:
        return "PROJECT_SCOPE"
    if topic_id in TEAM_TOPICS:
        return "TEAM_MANAGEMENT"
    if topic_id in COURSE_POLICY_TOPICS:
        return "COURSE_POLICY"
    if topic_id in RESOURCE_TOPICS:
        return "RESOURCE_LOOKUP"
    if topic_id == "ticket":
        return "SUPPORT_REQUEST"
    return "OTHER"


def _build_topic_profiles(
    repository: CorpusRepository,
) -> list[tuple[str, str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for thread in repository.threads:
        topic_id = str(thread.get("topic_id") or "other")
        title = str(thread.get("title") or "")
        question = str((thread.get("question") or {}).get("content") or "")
        tag = str(thread.get("tag") or "")
        grouped[topic_id].append(
            f"Chủ đề: {_topic_name(topic_id)}\n"
            f"Nhãn: {tag}\n"
            f"Tiêu đề: {title}\n"
            f"Câu hỏi: {question}"
        )
    return [
        (topic_id, "\n\n".join(grouped[topic_id]))
        for topic_id in sorted(grouped)
    ]


def _default_embedder() -> Embedder:
    return CachedEmbedder(delegate=OpenAIEmbedder())


def detect_question_topics(
    question: str,
    *,
    repository: CorpusRepository | None = None,
    embedder: Embedder | None = None,
) -> dict[str, Any]:
    """Detect corpus-backed topics for a learner question."""
    payload = DetectQuestionTopicsInput(question=question)
    resolved_repository = repository or CorpusRepository()
    resolved_embedder = embedder or _default_embedder()
    profiles = _build_topic_profiles(resolved_repository)

    if not profiles:
        return _other_result(payload.question)

    texts = [payload.question, *(profile for _, profile in profiles)]
    vectors = resolved_embedder.embed(texts)
    if len(vectors) != len(texts):
        raise ValueError("Embedder returned an unexpected number of vectors")

    query_vector = vectors[0]
    scored_topics = [
        (
            topic_id,
            max(0.0, min(1.0, cosine_similarity(query_vector, vector))),
        )
        for (topic_id, _), vector in zip(profiles, vectors[1:], strict=True)
    ]
    scored_topics.sort(key=lambda item: (-item[1], item[0]))
    primary_id, primary_score = scored_topics[0]

    if primary_score < PRIMARY_TOPIC_THRESHOLD:
        return _other_result(payload.question)

    minimum_subtopic_score = max(
        SUBTOPIC_THRESHOLD,
        primary_score - SUBTOPIC_MAX_DISTANCE,
    )
    subtopics = [
        {
            "id": topic_id,
            "name": _topic_name(topic_id),
            "confidence": round(score, 4),
        }
        for topic_id, score in scored_topics[1:]
        if score >= minimum_subtopic_score
    ][:2]

    return {
        "primary_topic": {
            "id": primary_id,
            "name": _topic_name(primary_id),
            "confidence": round(primary_score, 4),
        },
        "subtopics": subtopics,
        "intent": _infer_intent(primary_id),
        "normalized_query": payload.question,
    }


def _other_result(normalized_query: str) -> dict[str, Any]:
    return {
        "primary_topic": {
            "id": "other",
            "name": TOPIC_NAMES["other"],
            "confidence": 0.3,
        },
        "subtopics": [],
        "intent": "OTHER",
        "normalized_query": normalized_query,
    }


TOOL_DEFINITION = {
    "name": "detect_question_topics",
    "description": DESCRIPTION,
    "input_schema": DetectQuestionTopicsInput.model_json_schema(),
    "execute": detect_question_topics,
}


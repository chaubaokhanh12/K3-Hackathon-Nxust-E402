from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools._shared.repository import CorpusRepository
from tools.detect_question_topics.tool import detect_question_topics


class TopicEmbedder:
    model_name = "topic-test"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "api git combined" in lowered:
                vectors.append([0.8, 0.6, 0.0])
            elif "api" in lowered or "missing credentials" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "git" in lowered or "branch" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


@pytest.fixture
def repository(tmp_path: Path) -> CorpusRepository:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            {
                "threads": [
                    {
                        "thread_id": "api-thread",
                        "title": "Node không nhận API key",
                        "topic_id": "api_key",
                        "tag": "Kỹ thuật",
                        "link": "https://example.test/api-thread",
                        "question": {"content": "Missing credentials"},
                        "replies": [],
                        "verified_answer": True,
                        "trust": None,
                    },
                    {
                        "thread_id": "git-thread",
                        "title": "Git push bị reject",
                        "topic_id": "git_workflow",
                        "tag": "Kỹ thuật",
                        "link": "https://example.test/git-thread",
                        "question": {"content": "Branch bị conflict"},
                        "replies": [],
                        "verified_answer": False,
                        "trust": None,
                    },
                ],
                "roles": {},
                "users": [],
                "duplicate_groups": [],
                "test_queries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return CorpusRepository(corpus_path)


def test_detects_primary_topic_and_intent(repository: CorpusRepository) -> None:
    result = detect_question_topics(
        "  Node báo Missing credentials dù đã set API key  ",
        repository=repository,
        embedder=TopicEmbedder(),
    )

    assert result["primary_topic"]["id"] == "api_key"
    assert result["primary_topic"]["confidence"] == pytest.approx(1.0)
    assert result["intent"] == "TECHNICAL_ERROR"
    assert result["normalized_query"] == (
        "Node báo Missing credentials dù đã set API key"
    )


def test_returns_other_when_no_topic_is_similar(
    repository: CorpusRepository,
) -> None:
    result = detect_question_topics(
        "Một câu hỏi hoàn toàn mới",
        repository=repository,
        embedder=TopicEmbedder(),
    )

    assert result == {
        "primary_topic": {
            "id": "other",
            "name": "Khác",
            "confidence": 0.3,
        },
        "subtopics": [],
        "intent": "OTHER",
        "normalized_query": "Một câu hỏi hoàn toàn mới",
    }


def test_returns_secondary_topics_above_threshold(
    repository: CorpusRepository,
) -> None:
    result = detect_question_topics(
        "api git combined",
        repository=repository,
        embedder=TopicEmbedder(),
    )

    assert result["primary_topic"]["id"] == "api_key"
    assert [topic["id"] for topic in result["subtopics"]] == ["git_workflow"]


def test_rejects_blank_question(repository: CorpusRepository) -> None:
    with pytest.raises(ValidationError):
        detect_question_topics(
            "   ",
            repository=repository,
            embedder=TopicEmbedder(),
        )

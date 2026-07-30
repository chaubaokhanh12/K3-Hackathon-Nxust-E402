from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools._shared.repository import CorpusRepository
from tools.search_qa_threads.tool import search_qa_threads


class SearchEmbedder:
    model_name = "search-test"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "query verified" in lowered:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            elif "query community" in lowered:
                vectors.append([0.0, 1.0, 0.0, 0.0])
            elif "query none" in lowered:
                vectors.append([-1.0, -1.0, 0.0, 0.0])
            elif "verified-direct" in lowered:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            elif "community-tie" in lowered:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            elif "community-only" in lowered:
                vectors.append([0.0, 1.0, 0.0, 0.0])
            elif "topic-reference" in lowered:
                vectors.append([0.6, 0.0, 0.8, 0.0])
            else:
                vectors.append([0.0, 0.0, 0.0, 1.0])
        return vectors


def _thread(
    thread_id: str,
    marker: str,
    *,
    topic_id: str,
    verified: bool,
    trust: dict | None = None,
) -> dict:
    return {
        "thread_id": thread_id,
        "title": marker,
        "topic_id": topic_id,
        "tag": "Kỹ thuật",
        "created_at": "2026-07-01T10:00:00+07:00",
        "link": f"https://example.test/{thread_id}",
        "question": {
            "message_id": f"question-{thread_id}",
            "author_id": "learner-1",
            "author_name": "Learner",
            "author_role": "Learner",
            "author_role_id": "role-learner",
            "timestamp": "2026-07-01T10:00:00+07:00",
            "content": f"Question for {marker}",
            "has_code_block": False,
            "has_attachment": False,
            "attachment_types": [],
        },
        "replies": [],
        "reply_count": 0,
        "resolved": verified,
        "resolved_by": trust["message_id"] if trust else None,
        "verified_answer": verified,
        "trust": trust,
        "first_response_minutes": None,
        "verified_response_minutes": None,
    }


@pytest.fixture
def repository(tmp_path: Path) -> CorpusRepository:
    trusted_reply = {
        "message_id": "trusted-answer",
        "author_id": "coach-1",
        "author_name": "Coach",
        "author_role": "LabCoach",
        "trust_tag_raw": "(TRUST - LABCOACH)",
        "link": "https://example.test/verified/trusted-answer",
    }
    threads = [
        _thread(
            "verified",
            "verified-direct",
            topic_id="api_key",
            verified=True,
            trust=trusted_reply,
        ),
        _thread(
            "community-tie",
            "community-tie",
            topic_id="api_key",
            verified=False,
        ),
        _thread(
            "community-only",
            "community-only",
            topic_id="api_key",
            verified=False,
        ),
        _thread(
            "topic",
            "topic-reference",
            topic_id="api_key",
            verified=True,
        ),
        _thread(
            "unrelated",
            "unrelated-thread",
            topic_id="git_workflow",
            verified=True,
        ),
    ]
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            {
                "threads": threads,
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


def test_classifies_direct_topic_and_unrelated_before_trust(
    repository: CorpusRepository,
) -> None:
    result = search_qa_threads(
        query="query verified",
        topics=["api_key"],
        search_mode="hybrid",
        top_k=5,
        repository=repository,
        embedder=SearchEmbedder(),
    )

    assert [item["thread_id"] for item in result["direct_matches"]] == [
        "verified",
        "community-tie",
    ]
    assert [item["thread_id"] for item in result["topic_matches"]] == ["topic"]
    assert result["direct_matches"][0]["thread_url"] == (
        "https://example.test/verified/trusted-answer"
    )
    assert result["direct_matches"][0]["has_verified_answer"] is True
    assert result["direct_matches"][1]["has_verified_answer"] is False
    assert all(
        item["thread_id"] != "unrelated"
        for group in result.values()
        for item in group
    )


def test_returns_unverified_community_direct_match(
    repository: CorpusRepository,
) -> None:
    result = search_qa_threads(
        query="query community",
        topics=["api_key"],
        search_mode="hybrid",
        top_k=3,
        repository=repository,
        embedder=SearchEmbedder(),
    )

    assert [item["thread_id"] for item in result["direct_matches"]] == [
        "community-only"
    ]
    assert result["direct_matches"][0]["source_trust"] == pytest.approx(0.4)


def test_returns_empty_results_when_similarity_is_below_threshold(
    repository: CorpusRepository,
) -> None:
    result = search_qa_threads(
        query="query none",
        topics=["api_key"],
        search_mode="hybrid",
        top_k=3,
        repository=repository,
        embedder=SearchEmbedder(),
    )

    assert result == {"direct_matches": [], "topic_matches": []}


@pytest.mark.parametrize(
    ("mode", "expected_direct", "expected_topic"),
    [
        ("direct", ["verified", "community-tie"], []),
        ("topic", [], ["topic"]),
    ],
)
def test_search_mode_filters_result_groups(
    repository: CorpusRepository,
    mode: str,
    expected_direct: list[str],
    expected_topic: list[str],
) -> None:
    result = search_qa_threads(
        query="query verified",
        topics=["api_key"],
        search_mode=mode,
        top_k=5,
        repository=repository,
        embedder=SearchEmbedder(),
    )

    assert [item["thread_id"] for item in result["direct_matches"]] == (
        expected_direct
    )
    assert [item["thread_id"] for item in result["topic_matches"]] == (
        expected_topic
    )


def test_rejects_invalid_search_input(repository: CorpusRepository) -> None:
    with pytest.raises(ValidationError):
        search_qa_threads(
            query="valid query",
            topics=["api_key"],
            search_mode="unknown",
            top_k=0,
            repository=repository,
            embedder=SearchEmbedder(),
        )

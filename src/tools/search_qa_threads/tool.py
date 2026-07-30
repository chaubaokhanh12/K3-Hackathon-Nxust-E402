from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tools._shared.embeddings import CachedEmbedder, Embedder, OpenAIEmbedder
from tools._shared.repository import CorpusRepository
from tools._shared.similarity import cosine_similarity, jaccard_similarity


DESCRIPTION = (
    "Search the TrustQA Q&A corpus using OpenAI semantic embeddings and corpus "
    "topics. Return direct matches separately from topic references, classify "
    "relevance before applying source trust, and include the original thread "
    "URL for every result."
)

DIRECT_MATCH_THRESHOLD = 0.78
TOPIC_REFERENCE_PROBLEM_THRESHOLD = 0.40
TOPIC_REFERENCE_TOPIC_THRESHOLD = 0.50

ROLE_TRUST = {
    "Admin": 1.0,
    "Mentor": 1.0,
    "BTC": 1.0,
    "LabCoach": 0.95,
    "Learner": 0.40,
}


class SearchQaThreadsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=8_000)
    topics: list[str] = Field(default_factory=list, max_length=10)
    search_mode: Literal["direct", "topic", "hybrid"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_contain_text(cls, value: str) -> str:
        normalized = re.sub(r"\s+", " ", value).strip()
        if not normalized:
            raise ValueError("query must contain non-whitespace text")
        return normalized

    @field_validator("topics")
    @classmethod
    def normalize_topics(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for topic in value:
            cleaned = topic.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized


def _default_embedder() -> Embedder:
    return CachedEmbedder(delegate=OpenAIEmbedder())


def _thread_document(thread: dict[str, Any]) -> str:
    title = str(thread.get("title") or "")
    question = str((thread.get("question") or {}).get("content") or "")
    return f"{title}\n{question}"


def _thread_url(thread: dict[str, Any]) -> str:
    trust = thread.get("trust") or {}
    return str(trust.get("link") or thread.get("link") or "")


def _source_trust(thread: dict[str, Any]) -> float:
    trust = thread.get("trust") or {}
    trusted_role = str(trust.get("author_role") or "")
    if trusted_role:
        return ROLE_TRUST.get(trusted_role, 0.85)

    replies = thread.get("replies") or []
    verified_scores = [
        ROLE_TRUST.get(str(reply.get("author_role") or ""), 0.85)
        for reply in replies
        if reply.get("is_verified_source") is True
    ]
    if verified_scores:
        return max(verified_scores)
    if thread.get("verified_answer") is True:
        return 0.85
    return 0.40


def _result_item(
    thread: dict[str, Any],
    *,
    problem_similarity: float,
    topic_similarity: float,
    query_topics: set[str],
) -> dict[str, Any]:
    thread_topic = str(thread.get("topic_id") or "")
    matched_topics = sorted(
        query_topics & ({thread_topic} if thread_topic else set())
    )
    return {
        "thread_id": str(thread["thread_id"]),
        "title": str(thread.get("title") or ""),
        "problem_similarity": round(problem_similarity, 4),
        "topic_similarity": round(topic_similarity, 4),
        "matched_topics": matched_topics,
        "has_verified_answer": bool(thread.get("verified_answer")),
        "source_trust": round(_source_trust(thread), 2),
        "thread_url": _thread_url(thread),
    }


def _rank(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -item["problem_similarity"],
            -item["source_trust"],
            item["thread_id"],
        ),
    )


def search_qa_threads(
    query: str,
    topics: list[str] | None = None,
    search_mode: Literal["direct", "topic", "hybrid"] = "hybrid",
    top_k: int = 5,
    *,
    repository: CorpusRepository | None = None,
    embedder: Embedder | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return direct and topic-level matches from the TrustQA corpus."""
    payload = SearchQaThreadsInput(
        query=query,
        topics=topics or [],
        search_mode=search_mode,
        top_k=top_k,
    )
    resolved_repository = repository or CorpusRepository()
    resolved_embedder = embedder or _default_embedder()
    threads = resolved_repository.threads
    documents = [_thread_document(thread) for thread in threads]
    vectors = resolved_embedder.embed([payload.query, *documents])

    if len(vectors) != len(documents) + 1:
        raise ValueError("Embedder returned an unexpected number of vectors")

    query_vector = vectors[0]
    query_topics = set(payload.topics)
    direct_matches: list[dict[str, Any]] = []
    topic_matches: list[dict[str, Any]] = []

    for thread, vector in zip(threads, vectors[1:], strict=True):
        problem_similarity = max(
            0.0,
            min(1.0, cosine_similarity(query_vector, vector)),
        )
        thread_topic = str(thread.get("topic_id") or "")
        topic_similarity = jaccard_similarity(
            query_topics,
            {thread_topic} if thread_topic else set(),
        )
        item = _result_item(
            thread,
            problem_similarity=problem_similarity,
            topic_similarity=topic_similarity,
            query_topics=query_topics,
        )

        if problem_similarity >= DIRECT_MATCH_THRESHOLD:
            direct_matches.append(item)
        elif (
            problem_similarity >= TOPIC_REFERENCE_PROBLEM_THRESHOLD
            and topic_similarity >= TOPIC_REFERENCE_TOPIC_THRESHOLD
        ):
            topic_matches.append(item)

    ranked_direct = _rank(direct_matches)[: payload.top_k]
    ranked_topic = _rank(topic_matches)[: payload.top_k]

    if payload.search_mode == "direct":
        ranked_topic = []
    elif payload.search_mode == "topic":
        ranked_direct = []

    return {
        "direct_matches": ranked_direct,
        "topic_matches": ranked_topic,
    }


TOOL_DEFINITION = {
    "name": "search_qa_threads",
    "description": DESCRIPTION,
    "input_schema": SearchQaThreadsInput.model_json_schema(),
    "execute": search_qa_threads,
}


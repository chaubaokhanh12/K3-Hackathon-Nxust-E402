from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools._shared.embeddings import (
    CachedEmbedder,
    EmbedderConfigurationError,
    EmbeddingResponseError,
    OpenAIEmbedder,
)
from tools._shared.repository import CorpusLoadError, CorpusRepository
from tools._shared.similarity import cosine_similarity, jaccard_similarity


class CountingEmbedder:
    model_name = "fake-embedding"

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(text)), 1.0] for text in texts]


class FakeOpenAIClient:
    def __init__(self, data: list[SimpleNamespace]) -> None:
        self.embeddings = self
        self.data = data
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(data=self.data)


def _write_corpus(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "roles": {},
                "users": [],
                "threads": [
                    {
                        "thread_id": "thread-1",
                        "title": "API key error",
                        "topic_id": "api_key",
                        "tag": "Ky thuat",
                        "link": "https://example.test/thread-1",
                        "question": {"content": "Missing credentials"},
                        "replies": [],
                        "verified_answer": False,
                        "trust": None,
                    }
                ],
                "duplicate_groups": [],
                "test_queries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_repository_loads_threads_and_finds_exact_id(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    _write_corpus(corpus_path)

    repository = CorpusRepository(corpus_path)

    assert len(repository.threads) == 1
    assert repository.get_thread("thread-1")["title"] == "API key error"
    assert repository.get_thread("missing") is None


def test_repository_fails_closed_when_corpus_is_missing(tmp_path: Path) -> None:
    repository = CorpusRepository(tmp_path / "missing.json")

    with pytest.raises(CorpusLoadError, match="Cannot load TrustQA corpus"):
        _ = repository.threads


def test_openai_embedder_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(EmbedderConfigurationError, match="OPENAI_API_KEY"):
        OpenAIEmbedder()


def test_openai_embedder_restores_provider_response_order() -> None:
    client = FakeOpenAIClient(
        [
            SimpleNamespace(index=1, embedding=[0.0, 1.0]),
            SimpleNamespace(index=0, embedding=[1.0, 0.0]),
        ]
    )
    embedder = OpenAIEmbedder(
        client=client,
        model_name="embedding-test",
    )

    result = embedder.embed(["first", "second"])

    assert result == [[1.0, 0.0], [0.0, 1.0]]
    assert client.calls == [
        {
            "model": "embedding-test",
            "input": ["first", "second"],
        }
    ]


def test_openai_embedder_rejects_duplicate_response_indexes() -> None:
    client = FakeOpenAIClient(
        [
            SimpleNamespace(index=0, embedding=[1.0, 0.0]),
            SimpleNamespace(index=0, embedding=[0.0, 1.0]),
        ]
    )
    embedder = OpenAIEmbedder(client=client)

    with pytest.raises(EmbeddingResponseError, match="indexes"):
        embedder.embed(["first", "second"])


def test_cached_embedder_reuses_vectors_and_persists_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "embeddings.json"
    delegate = CountingEmbedder()
    cached = CachedEmbedder(delegate=delegate, cache_path=cache_path)

    first = cached.embed(["alpha", "beta"])
    second = cached.embed(["beta", "alpha"])

    assert first == [[5.0, 1.0], [4.0, 1.0]]
    assert second == [[4.0, 1.0], [5.0, 1.0]]
    assert delegate.calls == [["alpha", "beta"]]
    assert json.loads(cache_path.read_text(encoding="utf-8"))["entries"]


def test_cached_embedder_ignores_malformed_cached_vectors(tmp_path: Path) -> None:
    cache_path = tmp_path / "embeddings.json"
    cache_path.write_text(
        json.dumps({"entries": {"broken": ["not-a-number"]}}),
        encoding="utf-8",
    )
    delegate = CountingEmbedder()
    cached = CachedEmbedder(delegate=delegate, cache_path=cache_path)

    result = cached.embed(["alpha"])

    assert result == [[5.0, 1.0]]
    assert delegate.calls == [["alpha"]]


def test_similarity_functions_return_hand_checked_values() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([], []) == 0.0
    assert jaccard_similarity({"api_key", "node"}, {"api_key"}) == pytest.approx(0.5)
    assert jaccard_similarity(set(), set()) == 0.0

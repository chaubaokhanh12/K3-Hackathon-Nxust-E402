from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from openai import OpenAI


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
#: Số input tối đa mỗi request. Corpus lớn phải cắt lô, nếu không API từ chối cả
#: lượt tra cứu và bot tụt xuống chế độ tìm kiếm cục bộ.
MAX_BATCH_SIZE = 96
DEFAULT_CACHE_PATH = Path(__file__).resolve().parents[1] / ".cache" / "embeddings.json"


class EmbedderConfigurationError(RuntimeError):
    """Raised when an embedding provider is not configured."""


class EmbeddingResponseError(RuntimeError):
    """Raised when an embedding provider returns malformed data."""


class Embedder(Protocol):
    model_name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed texts in input order."""


class OpenAIEmbedder:
    """OpenAI Embeddings API adapter."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_name: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if client is None and not resolved_key:
            raise EmbedderConfigurationError(
                "OPENAI_API_KEY is required when using the default OpenAI embedder"
            )

        self.model_name = (
            model_name
            or os.getenv("OPENAI_EMBEDDING_MODEL")
            or DEFAULT_EMBEDDING_MODEL
        )
        self._client = client or OpenAI(api_key=resolved_key)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(items), MAX_BATCH_SIZE):
            vectors.extend(self._embed_batch(items[start : start + MAX_BATCH_SIZE]))
        if len(vectors) != len(items):
            raise EmbeddingResponseError(
                f"Expected {len(items)} embeddings, received {len(vectors)}"
            )
        return vectors

    def _embed_batch(self, items: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            model=self.model_name,
            input=items,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        indexes = [item.index for item in ordered]
        if indexes != list(range(len(items))):
            raise EmbeddingResponseError(
                "Embedding response indexes must be unique and contiguous"
            )
        return [list(item.embedding) for item in ordered]


class CachedEmbedder:
    """Persistent SHA-256 cache around another embedder."""

    def __init__(
        self,
        *,
        delegate: Embedder,
        cache_path: str | Path = DEFAULT_CACHE_PATH,
    ) -> None:
        self.delegate = delegate
        self.model_name = delegate.model_name
        self.cache_path = Path(cache_path)
        self._entries: dict[str, list[float]] | None = None
        self._write_lock = threading.Lock()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []

        entries = self._load_entries()
        keys = [self._key(text) for text in items]
        missing_texts: list[str] = []
        missing_keys: list[str] = []
        seen_missing: set[str] = set()

        for text, key in zip(items, keys, strict=True):
            if key not in entries and key not in seen_missing:
                seen_missing.add(key)
                missing_texts.append(text)
                missing_keys.append(key)

        if missing_texts:
            vectors = self.delegate.embed(missing_texts)
            if len(vectors) != len(missing_texts):
                raise EmbeddingResponseError(
                    f"Expected {len(missing_texts)} embeddings, "
                    f"received {len(vectors)}"
                )
            for key, vector in zip(missing_keys, vectors, strict=True):
                entries[key] = [float(value) for value in vector]
            self._save_entries(entries)

        return [list(entries[key]) for key in keys]

    def _key(self, text: str) -> str:
        payload = f"{self.model_name}\0{text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _read_file(self) -> dict[str, list[float]]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            raw_entries = payload.get("entries", {})
            if not isinstance(raw_entries, dict):
                raw_entries = {}
        except (OSError, json.JSONDecodeError, AttributeError):
            raw_entries = {}

        valid_entries: dict[str, list[float]] = {}
        for key, vector in raw_entries.items():
            if not isinstance(vector, list):
                continue
            try:
                valid_entries[str(key)] = [float(value) for value in vector]
            except (TypeError, ValueError):
                continue
        return valid_entries

    def _load_entries(self) -> dict[str, list[float]]:
        if self._entries is None:
            self._entries = self._read_file()
        return self._entries

    def _save_entries(self, entries: dict[str, list[float]]) -> None:
        """Ghi nguyên tử, hợp nhất với những gì tiến trình khác đã ghi.

        Hai điểm phải giữ: (1) file tạm mang tên duy nhất — dùng chung một tên
        thì hai request song song (FastAPI chạy endpoint sync trên threadpool)
        ghi đè lên nhau giữa chừng và file cache hỏng; (2) đọc lại đĩa rồi mới
        hợp nhất — mỗi request tạo một CachedEmbedder riêng nên nếu ghi đè thẳng
        thì entry của request kia bị mất.
        """
        with self._write_lock:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            merged = self._read_file()
            merged.update(entries)
            temporary_path = self.cache_path.with_name(
                f"{self.cache_path.name}.{os.getpid()}.{uuid4().hex}.tmp"
            )
            try:
                temporary_path.write_text(
                    json.dumps(
                        {"model": self.model_name, "entries": merged},
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                temporary_path.replace(self.cache_path)
            except OSError:
                temporary_path.unlink(missing_ok=True)
                raise
            self._entries = merged

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CORPUS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "discord_qa_mock.json"
)


class CorpusLoadError(RuntimeError):
    """Raised when the TrustQA corpus cannot be loaded safely."""


class CorpusRepository:
    """Read-only access to the TrustQA JSON corpus."""

    def __init__(self, corpus_path: str | Path = DEFAULT_CORPUS_PATH) -> None:
        self.corpus_path = Path(corpus_path).resolve()
        self._data: dict[str, Any] | None = None
        self._threads_by_id: dict[str, dict[str, Any]] | None = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            self._data = self._load()
        return self._data

    @property
    def threads(self) -> list[dict[str, Any]]:
        return self.data["threads"]

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        if self._threads_by_id is None:
            self._threads_by_id = {
                str(thread["thread_id"]): thread for thread in self.threads
            }
        return self._threads_by_id.get(str(thread_id))

    def _load(self) -> dict[str, Any]:
        try:
            raw = self.corpus_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise CorpusLoadError(
                f"Cannot load TrustQA corpus at {self.corpus_path}: {exc}"
            ) from exc

        if not isinstance(data, dict) or not isinstance(data.get("threads"), list):
            raise CorpusLoadError(
                f"Cannot load TrustQA corpus at {self.corpus_path}: "
                "top-level 'threads' must be a list"
            )
        return data


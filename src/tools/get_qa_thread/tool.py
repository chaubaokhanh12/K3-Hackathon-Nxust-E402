from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tools._shared.repository import CorpusRepository


DESCRIPTION = (
    "Load one TrustQA thread by exact thread_id and return its best answers. "
    "Prefer the corpus TRUST pointer and verified sources, remove noisy or "
    "duplicate replies, label community answers as unverified, and fail closed "
    "when the thread does not exist."
)

ROLE_PRIORITY = {
    "Admin": 5,
    "Mentor": 4,
    "BTC": 4,
    "LabCoach": 3,
    "Learner": 1,
}

NOISE_PATTERNS = (
    re.compile(r"^(up|up a|up nha|up nhe|\+1)$"),
    re.compile(
        r"^(e|em|minh|toi)?\s*(cung\s*)?bi(\s*(v|vay|y chang))?$"
    ),
    re.compile(r"^ban\s+gui\s+(code|anh)(\s+di)?$"),
    re.compile(r"^da\s+sua\s+duoc\s+roi$"),
)


class GetQaThreadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thread_id: str = Field(min_length=1, max_length=200)
    max_answers: int = Field(default=2, ge=1, le=3)

    @field_validator("thread_id")
    @classmethod
    def normalize_thread_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("thread_id must contain non-whitespace text")
        return normalized


def _fold_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")
    return re.sub(r"[^a-z0-9+]+", " ", without_marks).strip()


def _is_noise(content: str) -> bool:
    folded = _fold_text(content)
    if len(folded) < 4:
        return True
    return any(pattern.fullmatch(folded) for pattern in NOISE_PATTERNS)


def _is_near_duplicate(content: str, selected_contents: list[str]) -> bool:
    folded = _fold_text(content)
    for selected in selected_contents:
        selected_folded = _fold_text(selected)
        if folded == selected_folded:
            return True
        if SequenceMatcher(None, folded, selected_folded).ratio() >= 0.92:
            return True
    return False


def _rank_replies(
    thread: dict[str, Any],
) -> list[dict[str, Any]]:
    trust_message_id = str((thread.get("trust") or {}).get("message_id") or "")
    resolved_by = str(thread.get("resolved_by") or "")
    indexed_replies = list(enumerate(thread.get("replies") or []))

    def rank(item: tuple[int, dict[str, Any]]) -> tuple[int, ...]:
        index, reply = item
        message_id = str(reply.get("message_id") or "")
        role = str(reply.get("author_role") or "")
        return (
            -int(bool(trust_message_id and message_id == trust_message_id)),
            -int(reply.get("is_verified_source") is True),
            -int(bool(resolved_by and message_id == resolved_by)),
            -ROLE_PRIORITY.get(role, 0),
            -int(reply.get("reaction_count") or 0),
            index,
        )

    return [reply for _, reply in sorted(indexed_replies, key=rank)]


def _selected_answers(
    thread: dict[str, Any],
    max_answers: int,
) -> list[dict[str, Any]]:
    trust_message_id = str((thread.get("trust") or {}).get("message_id") or "")
    resolved_by = str(thread.get("resolved_by") or "")
    selected: list[dict[str, Any]] = []
    selected_contents: list[str] = []

    for reply in _rank_replies(thread):
        content = str(reply.get("content") or "").strip()
        if not content or _is_noise(content):
            continue
        if _is_near_duplicate(content, selected_contents):
            continue

        answer_id = str(reply.get("message_id") or "")
        is_trusted_answer = bool(
            trust_message_id and answer_id == trust_message_id
        )
        is_verified = bool(
            reply.get("is_verified_source") is True or is_trusted_answer
        )
        selected.append(
            {
                "answer_id": answer_id,
                "content": content,
                "author_name": str(reply.get("author_name") or ""),
                "author_role": str(reply.get("author_role") or ""),
                "is_verified": is_verified,
                "is_accepted": bool(
                    is_trusted_answer or (resolved_by and answer_id == resolved_by)
                ),
                "verification_label": (
                    "VERIFIED" if is_verified else "COMMUNITY_UNVERIFIED"
                ),
            }
        )
        selected_contents.append(content)
        if len(selected) >= max_answers:
            break

    return selected


def get_qa_thread(
    thread_id: str,
    max_answers: int = 2,
    *,
    repository: CorpusRepository | None = None,
) -> dict[str, Any]:
    """Return one thread and its best non-noisy answers."""
    payload = GetQaThreadInput(
        thread_id=thread_id,
        max_answers=max_answers,
    )
    resolved_repository = repository or CorpusRepository()
    thread = resolved_repository.get_thread(payload.thread_id)

    if thread is None:
        return {
            "found": False,
            "error": "THREAD_NOT_FOUND",
            "thread_id": payload.thread_id,
        }

    trust = thread.get("trust") or {}
    return {
        "found": True,
        "thread_id": str(thread["thread_id"]),
        "title": str(thread.get("title") or ""),
        "question": str((thread.get("question") or {}).get("content") or ""),
        "topics": [str(thread.get("topic_id"))]
        if thread.get("topic_id")
        else [],
        "selected_answers": _selected_answers(thread, payload.max_answers),
        "verified_answer": bool(thread.get("verified_answer")),
        "thread_url": str(trust.get("link") or thread.get("link") or ""),
    }


TOOL_DEFINITION = {
    "name": "get_qa_thread",
    "description": DESCRIPTION,
    "input_schema": GetQaThreadInput.model_json_schema(),
    "execute": get_qa_thread,
}


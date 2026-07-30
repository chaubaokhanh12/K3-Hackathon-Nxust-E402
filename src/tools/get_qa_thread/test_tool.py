from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools._shared.repository import CorpusRepository
from tools.get_qa_thread.tool import get_qa_thread


def _reply(
    answer_id: str,
    content: str,
    *,
    role: str = "Learner",
    verified: bool = False,
    reactions: int = 0,
) -> dict:
    return {
        "message_id": answer_id,
        "author_id": f"author-{answer_id}",
        "author_name": f"Author {answer_id}",
        "author_role": role,
        "author_role_id": f"role-{role}",
        "is_verified_source": verified,
        "timestamp": "2026-07-01T11:00:00+07:00",
        "content": content,
        "reply_to_message_id": "question-1",
        "reaction_count": reactions,
        "has_code_block": False,
        "has_attachment": False,
        "trust_tag": verified,
    }


@pytest.fixture
def repository(tmp_path: Path) -> CorpusRepository:
    trusted_content = (
        "Lệnh setx không cập nhật terminal hiện tại. Hãy mở terminal mới."
    )
    community_content = (
        "Bạn có thể dùng file .env kết hợp với dotenv để nạp API key."
    )
    replies = [
        _reply("noise-up", "up ạ"),
        _reply(
            "trusted-answer",
            trusted_content,
            role="LabCoach",
            verified=True,
            reactions=3,
        ),
        _reply("community-answer", community_content, reactions=5),
        _reply(
            "community-duplicate",
            f"  {community_content}  ",
            reactions=1,
        ),
        _reply("noise-code", "Bạn gửi code đi."),
    ]
    trust = {
        "message_id": "trusted-answer",
        "author_id": "author-trusted-answer",
        "author_name": "Author trusted-answer",
        "author_role": "LabCoach",
        "trust_tag_raw": "(TRUST - LABCOACH)",
        "link": "https://example.test/thread-1/trusted-answer",
    }
    community_thread = {
        "thread_id": "community-thread",
        "title": "Community workaround",
        "topic_id": "deps_error",
        "tag": "Kỹ thuật",
        "created_at": "2026-07-02T10:00:00+07:00",
        "link": "https://example.test/community-thread",
        "question": {"content": "Cài package bị lỗi"},
        "replies": [
            _reply(
                "community-only-answer",
                "Hãy xóa cache pip rồi cài lại package từ đầu.",
                reactions=2,
            )
        ],
        "reply_count": 1,
        "resolved": True,
        "resolved_by": "community-only-answer",
        "verified_answer": False,
        "trust": None,
        "first_response_minutes": 10,
        "verified_response_minutes": None,
    }
    trusted_thread = {
        "thread_id": "thread-1",
        "title": "Node không nhận OPENAI_API_KEY",
        "topic_id": "api_key",
        "tag": "Kỹ thuật",
        "created_at": "2026-07-01T10:00:00+07:00",
        "link": "https://example.test/thread-1",
        "question": {"content": "Node báo Missing credentials"},
        "replies": replies,
        "reply_count": len(replies),
        "resolved": True,
        "resolved_by": "trusted-answer",
        "verified_answer": True,
        "trust": trust,
        "first_response_minutes": 10,
        "verified_response_minutes": 20,
    }
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            {
                "threads": [trusted_thread, community_thread],
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


def test_selects_trusted_answer_then_unique_community_answer(
    repository: CorpusRepository,
) -> None:
    result = get_qa_thread("thread-1", repository=repository)

    assert result["found"] is True
    assert [item["answer_id"] for item in result["selected_answers"]] == [
        "trusted-answer",
        "community-answer",
    ]
    assert result["selected_answers"][0]["is_verified"] is True
    assert result["selected_answers"][0]["is_accepted"] is True
    assert result["selected_answers"][0]["verification_label"] == "VERIFIED"
    assert (
        result["selected_answers"][1]["verification_label"]
        == "COMMUNITY_UNVERIFIED"
    )
    assert result["thread_url"] == (
        "https://example.test/thread-1/trusted-answer"
    )


def test_honors_max_answers(repository: CorpusRepository) -> None:
    result = get_qa_thread(
        "thread-1",
        max_answers=1,
        repository=repository,
    )

    assert [item["answer_id"] for item in result["selected_answers"]] == [
        "trusted-answer"
    ]


def test_labels_community_only_answer_as_unverified(
    repository: CorpusRepository,
) -> None:
    result = get_qa_thread("community-thread", repository=repository)

    assert result["selected_answers"][0]["is_verified"] is False
    assert (
        result["selected_answers"][0]["verification_label"]
        == "COMMUNITY_UNVERIFIED"
    )


def test_missing_thread_fails_closed(repository: CorpusRepository) -> None:
    result = get_qa_thread("missing", repository=repository)

    assert result == {
        "found": False,
        "error": "THREAD_NOT_FOUND",
        "thread_id": "missing",
    }


@pytest.mark.parametrize("max_answers", [0, 4])
def test_rejects_answer_limit_outside_one_to_three(
    repository: CorpusRepository,
    max_answers: int,
) -> None:
    with pytest.raises(ValidationError):
        get_qa_thread(
            "thread-1",
            max_answers=max_answers,
            repository=repository,
        )

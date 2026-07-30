"""End-to-end DupBot orchestration.

This module is the missing adapter between the framework-independent tools,
the deterministic guardrails, the HTTP API, and the legacy evaluation harness.
``answer`` intentionally returns one superset payload so every consumer reads
the same retrieval decision instead of maintaining separate implementations.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
from collections.abc import Callable, Mapping
from difflib import SequenceMatcher
from typing import Any

from agent import BOT_COPY, ConfidenceTier, build_bot_response, enforce
from agent.routing import (
    SCOPE_COPY,
    SOURCE_WARNING,
    EscalationDecision,
    EscalationReason,
    EscalationTarget,
    Scope,
    ascii_fold,
    classify_scope,
    route_escalation,
    validate_escalation,
)
from env_file import load_env
from tools._shared.embeddings import CachedEmbedder, Embedder, OpenAIEmbedder
from tools._shared.repository import CorpusRepository
from tools.detect_question_topics import detect_question_topics
from tools.get_qa_thread import get_qa_thread
from tools.search_qa_threads import search_qa_threads
from tools.search_qa_threads.tool import ROLE_TRUST

LOGGER = logging.getLogger(__name__)

# Nạp .env một lần khi import: mọi consumer (app.py, run_cases.py, pytest) đều
# thấy OPENAI_API_KEY mà không phải set tay từng terminal.
load_env()

MAX_RESULTS = 3
TOO_VAGUE_PATTERNS = {
    "e bi loi nay ko biet fix sao a",
    "em bi loi a",
    "giup em voi",
    "ko chay duoc a",
    "khong chay duoc a",
}
CLARIFYING_QUESTION = (
    "Bạn gửi giúp mình nguyên văn thông báo lỗi, thao tác vừa làm và môi trường "
    "đang dùng nhé?"
)
EMPTY_INPUT_QUESTION = "Bạn nhập câu hỏi giúp mình nhé, mình chưa thấy nội dung nào."
#: Chủ đề corpus chắc chắn không có thread nào (kiểm tra tay trên
#: ``data/discord_qa_mock.json``). Chặn sớm để không bao giờ ghép gợi ý gần đúng
#: cho những câu mà trả lời sai gây hậu quả thật (học phí, thành viên ngoài khoá).
UNSUPPORTED_SOURCE_PHRASES = (
    "hoc phi",
    "nguoi ngoai khoa",
)

AnswerFunction = Callable[[str], dict[str, Any]]

DOMAIN_CONCEPTS = {
    "attendanceconcept": (
        "diem danh",
        "check in",
        "check out",
        "ghi nhan co mat",
        "xac nhan co mat",
    ),
    "absenceconcept": ("nghi hoc", "vang hoc", "khong di hoc"),
    "shirtconcept": ("ao khoa hoc", "dong phuc"),
    "leavegroupconcept": ("roi nhom", "thoat khoi team", "thoat team", "bo ngang"),
    "teamconcept": ("nhom", "team"),
    "xpconcept": ("diem kinh nghiem", "chi so active", "xp"),
    "participationconcept": ("phat bieu", "diem cong", "tich cuc tren lop"),
    "apikeyconcept": ("api key", "khoa api", "openai key"),
    "dependencyconcept": (
        "loi thu vien",
        "loi dependency",
        "khong cai duoc package",
        "pip install",
    ),
    "gitconcept": ("git", "github", "commit", "push code"),
    "phoenixconcept": ("phoenix",),
    "ailogconcept": ("ai log", "ai-log"),
    "projectrequirementconcept": ("yeu cau du an", "requirement du an"),
    "datasetconcept": ("dataset", "du lieu huan luyen"),
    "brdprdconcept": ("brd", "prd"),
    "mentorconcept": ("mentor duty", "gap mentor", "hen mentor"),
    "resourceconcept": ("tai lieu buoi hoc", "slide", "recording", "file ghi am"),
    "ticketconcept": ("ticket", "ho tro ky thuat"),
}
DOMAIN_PATTERNS = tuple(
    (
        re.compile(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])"),
        concept,
    )
    for variant, concept in sorted(
        (
            (variant, concept)
            for concept, variants in DOMAIN_CONCEPTS.items()
            for variant in variants
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)


def _fold_text(value: str) -> str:
    folded = ascii_fold(value)
    for pattern, concept in DOMAIN_PATTERNS:
        folded = pattern.sub(f" {concept} ", folded)
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def _tokens(value: str) -> set[str]:
    stopwords = {
        "a",
        "anh",
        "ban",
        "bi",
        "cai",
        "cac",
        "cho",
        "co",
        "cua",
        "da",
        "dang",
        "duoc",
        "em",
        "gi",
        "giup",
        "hoi",
        "khong",
        "la",
        "lam",
        "minh",
        "mot",
        "nay",
        "nhe",
        "nhung",
        "phai",
        "sao",
        "thi",
        "toi",
        "trong",
        "voi",
    }
    return {
        token
        for token in _fold_text(value).split()
        if len(token) > 1 and token not in stopwords
    }


def _local_similarity(left: str, right: str) -> float:
    left_folded = _fold_text(left)
    right_folded = _fold_text(right)
    if not left_folded or not right_folded:
        return 0.0
    if left_folded == right_folded:
        return 1.0

    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        token_score = 0.0
    else:
        overlap = len(left_tokens & right_tokens)
        precision = overlap / len(left_tokens)
        recall = overlap / len(right_tokens)
        f1_score = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        query_coverage = overlap / len(left_tokens)
        token_score = 0.8 * query_coverage + 0.2 * f1_score
    sequence_score = SequenceMatcher(None, left_folded, right_folded).ratio()
    return 0.9 * token_score + 0.1 * sequence_score


def _source_trust(thread: Mapping[str, Any]) -> float:
    trust = thread.get("trust") or {}
    role = str(trust.get("author_role") or "")
    if role:
        return ROLE_TRUST.get(role, 0.85)
    return 0.85 if thread.get("verified_answer") else 0.40


def _match_item(
    thread: Mapping[str, Any],
    *,
    problem_similarity: float,
    topic_id: str | None,
) -> dict[str, Any]:
    thread_topic = str(thread.get("topic_id") or "")
    trust = thread.get("trust") or {}
    matched_topics = [thread_topic] if topic_id and thread_topic == topic_id else []
    return {
        "thread_id": str(thread["thread_id"]),
        "title": str(thread.get("title") or ""),
        "problem_similarity": round(problem_similarity, 4),
        "topic_similarity": 1.0 if matched_topics else 0.0,
        "matched_topics": matched_topics,
        "has_verified_answer": bool(thread.get("verified_answer")),
        "source_trust": round(_source_trust(thread), 2),
        "thread_url": str(trust.get("link") or thread.get("link") or ""),
    }


def _local_retrieve(
    question: str,
    repository: CorpusRepository,
    *,
    top_k: int,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Corpus-backed, deterministic fallback used when no API key is present.

    It uses conservative domain-concept and lexical matching over thread text.
    It never reads benchmark labels, never generates an answer, and only returns
    verbatim corpus content through ``get_qa_thread``.
    """

    ranked_threads: list[tuple[float, Mapping[str, Any]]] = []
    for thread in repository.threads:
        document = (
            f"{thread.get('title') or ''} "
            f"{(thread.get('question') or {}).get('content') or ''}"
        )
        ranked_threads.append((_local_similarity(question, document), thread))
    ranked_threads.sort(
        key=lambda item: (
            -item[0],
            -int(bool(item[1].get("verified_answer"))),
            str(item[1].get("thread_id") or ""),
        )
    )

    best_thread_score = ranked_threads[0][0] if ranked_threads else 0.0
    resolved_topic = (
        str(ranked_threads[0][1].get("topic_id") or "other")
        if ranked_threads
        else "other"
    )

    if best_thread_score >= 0.48:
        direct = [
            _match_item(
                thread,
                problem_similarity=min(0.93, 0.78 + score * 0.18),
                topic_id=resolved_topic,
            )
            for score, thread in ranked_threads
            if score >= max(0.42, best_thread_score * 0.80)
            and str(thread.get("topic_id") or "other") == resolved_topic
        ][:top_k]
        return _detected_result(resolved_topic, question, best_thread_score), {
            "direct_matches": direct,
            "topic_matches": [],
        }

    if best_thread_score >= 0.40 and resolved_topic != "other":
        topic_threads = [
            thread
            for thread in repository.threads
            if str(thread.get("topic_id") or "") == resolved_topic
        ]
        topic = [
            _match_item(
                thread,
                problem_similarity=0.40 + min(best_thread_score, 0.75) * 0.25,
                topic_id=resolved_topic,
            )
            for thread in topic_threads[:top_k]
        ]
        return _detected_result(resolved_topic, question, best_thread_score), {
            "direct_matches": [],
            "topic_matches": topic,
        }

    return _detected_result("other", question, 0.3), {
        "direct_matches": [],
        "topic_matches": [],
    }


def _detected_result(
    topic_id: str, question: str, confidence: float
) -> dict[str, Any]:
    return {
        "primary_topic": {
            "id": topic_id or "other",
            "name": (topic_id or "other").replace("_", " ").title(),
            "confidence": round(max(0.3, min(1.0, confidence)), 4),
        },
        "subtopics": [],
        "intent": "OTHER",
        "normalized_query": re.sub(r"\s+", " ", question).strip(),
    }


def _escalation_fields(decision: EscalationDecision) -> dict[str, Any]:
    """Trường định tuyến dùng chung cho mọi payload.

    ``tag_labcoach`` giữ nguyên tên vì bộ chấm (``src/test/test_cases.json``) định
    nghĩa nó là "có chuyển cho người thật hay không". Vai trò đích thật nằm ở
    ``escalation.target_role``.
    """
    tagged = decision.tagged
    return {
        "escalated_to_labcoach": tagged,
        "tag_labcoach": tagged,
        "escalation": {
            "target_role": decision.target.value if tagged else None,
            "reason": decision.reason.value,
            "sla_minutes": decision.sla_minutes,
            "note": decision.note,
        },
    }


def _no_escalation() -> EscalationDecision:
    return EscalationDecision(
        target=EscalationTarget.NONE, reason=EscalationReason.NOT_NEEDED
    )


def _safe_empty_payload(
    *,
    reason: str,
    headline: str,
    note: str,
    escalation: EscalationDecision | None = None,
    clarifying_question: str | None = None,
    retrieval_mode: str = "input-guardrail",
    warning: str | None = None,
) -> dict[str, Any]:
    decision = escalation or _no_escalation()
    payload: dict[str, Any] = {
        "confidence": ConfidenceTier.NONE.value,
        "headline": headline,
        "note": note,
        "suggestions": [],
        "render_buttons": False,
        "buttons": [],
        "retrieval_mode": retrieval_mode,
        "has_answer": False,
        "reason": reason,
        "results": [],
        "clarifying_question": clarifying_question,
        **_escalation_fields(decision),
    }
    if warning:
        payload["warning"] = warning
    return payload


def _legacy_results(suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "thread_id": item["thread_id"],
            "title": item["title"],
            "snippet": item["excerpt"],
            "link": item["thread_url"],
            "verified": item["source_tier"] == "VERIFIED",
            "answered_by": item.get("author_name"),
            "answered_by_role": item.get("author_role"),
            "similarity": item["similarity"],
            "relevance": item["relevance"],
        }
        for item in suggestions
    ]


def _is_too_vague(question: str) -> bool:
    folded = _fold_text(question)
    if folded in TOO_VAGUE_PATTERNS:
        return True
    tokens = _tokens(question)
    return len(tokens) < 2 and len(folded.split()) <= 4


def _is_known_out_of_corpus_scope(question: str) -> bool:
    folded = ascii_fold(question)
    return any(phrase in folded for phrase in UNSUPPORTED_SOURCE_PHRASES)


def _openai_embedder() -> Embedder:
    return CachedEmbedder(delegate=OpenAIEmbedder())


def answer(
    question: str,
    *,
    top_k: int = MAX_RESULTS,
    embedder: Embedder | None = None,
    repository: CorpusRepository | None = None,
) -> dict[str, Any]:
    """Answer one learner question using retrieval, source ranking and guardrails."""

    normalized_question = re.sub(r"\s+", " ", question).strip()
    top_k = max(1, min(MAX_RESULTS, int(top_k)))

    # Input rỗng / toàn khoảng trắng: hỏi lại, không nổ exception (TC-049, TC-050).
    if not normalized_question:
        return _safe_empty_payload(
            reason="too_vague",
            headline="Mình chưa nhận được câu hỏi nào",
            note=EMPTY_INPUT_QUESTION,
            clarifying_question=EMPTY_INPUT_QUESTION,
        )

    # Cổng phạm vi chạy TRƯỚC retrieval: câu ngoài phạm vi không được tiêu tốn
    # lượt tra cứu, và tuyệt đối không được chuyển cho người thật.
    scope = classify_scope(normalized_question)
    if scope is not Scope.IN_SCOPE:
        copy = SCOPE_COPY[scope]
        return _safe_empty_payload(
            reason="out_of_scope",
            headline=copy["headline"],
            note=copy["note"],
            escalation=validate_escalation(
                route_escalation(question=normalized_question, scope=scope),
                scope=scope,
                tier=ConfidenceTier.NONE,
            ),
        )

    if _is_known_out_of_corpus_scope(normalized_question):
        copy = BOT_COPY[ConfidenceTier.NONE]
        return _safe_empty_payload(
            reason="no_source",
            headline=copy["headline"],
            note=copy["note"],
            escalation=route_escalation(
                question=normalized_question,
                scope=scope,
                tier=ConfidenceTier.NONE,
            ),
        )

    if _is_too_vague(normalized_question):
        return _safe_empty_payload(
            reason="too_vague",
            headline="Mình cần thêm một chút thông tin",
            note=CLARIFYING_QUESTION,
            clarifying_question=CLARIFYING_QUESTION,
        )

    resolved_repository = repository or CorpusRepository()
    retrieval_mode = "openai-embeddings"
    warning: str | None = None

    if embedder is not None or os.getenv("OPENAI_API_KEY"):
        resolved_embedder = embedder or _openai_embedder()
        try:
            detected = detect_question_topics(
                normalized_question,
                repository=resolved_repository,
                embedder=resolved_embedder,
            )
            topics = [
                detected["primary_topic"]["id"],
                *[item["id"] for item in detected["subtopics"]],
            ]
            search_result = search_qa_threads(
                detected["normalized_query"],
                topics=topics,
                search_mode="hybrid",
                top_k=top_k,
                repository=resolved_repository,
                embedder=resolved_embedder,
            )
        except Exception as exc:
            if embedder is not None:
                raise
            LOGGER.warning(
                "OpenAI retrieval failed (%s); using local corpus fallback.",
                type(exc).__name__,
            )
            retrieval_mode = "local-corpus-fallback"
            warning = "OpenAI Embeddings tạm thời không khả dụng; đã dùng tìm kiếm cục bộ."
            detected, search_result = _local_retrieve(
                normalized_question,
                resolved_repository,
                top_k=top_k,
            )
    else:
        retrieval_mode = "local-corpus-fallback"
        warning = "Chưa cấu hình OPENAI_API_KEY; đang dùng tìm kiếm cục bộ để demo."
        detected, search_result = _local_retrieve(
            normalized_question,
            resolved_repository,
            top_k=top_k,
        )

    details: dict[str, Mapping[str, Any]] = {}
    for match in list(search_result.get("direct_matches") or [])[:top_k]:
        thread_id = str(match.get("thread_id") or "")
        detail = get_qa_thread(
            thread_id,
            max_answers=2,
            repository=resolved_repository,
        )
        if detail.get("found"):
            details[thread_id] = detail

    response = enforce(
        build_bot_response(
            search_result,
            details,
            status="pending",
            max_threads=top_k,
        )
    )
    payload = response.model_dump(mode="json")
    suggestions = payload["suggestions"]
    has_answer = bool(suggestions) and payload["confidence"] != "none"

    # Định tuyến theo địa hạt, không mặc định LabCoach. Ba lý do chuyển: corpus
    # rỗng, chỉ có học viên trả lời (cần xác minh), học viên bấm "Chưa đúng ý tôi"
    # (do frontend gọi /escalate, không tính ở đây).
    decision = validate_escalation(
        route_escalation(
            question=normalized_question,
            scope=scope,
            tier=response.confidence,
            primary_topic_id=detected["primary_topic"]["id"],
            intent=detected["intent"],
            suggestions=suggestions,
        ),
        scope=scope,
        tier=response.confidence,
        suggestions=suggestions,
    )

    payload.update(
        {
            "retrieval_mode": retrieval_mode,
            "detected_topics": {
                "primary": detected["primary_topic"],
                "subtopics": detected["subtopics"],
                "intent": detected["intent"],
            },
            "has_answer": has_answer,
            "reason": None if has_answer else "no_source",
            "results": _legacy_results(suggestions),
            "clarifying_question": None,
            **_escalation_fields(decision),
        }
    )
    if decision.reason is EscalationReason.UNVERIFIED_SOURCE:
        # Vẫn hiển thị gợi ý, nhưng dán nhãn để không ai đọc nhầm là chính thức.
        payload["source_warning"] = SOURCE_WARNING
    if warning:
        payload["warning"] = warning
    return payload


def load_impl(spec: str | None = None) -> AnswerFunction:
    """Load ``BOT_IMPL=module.function`` for the legacy evaluation harness."""

    target = (spec or os.getenv("BOT_IMPL") or "").strip()
    if not target:
        return answer
    if "." not in target:
        raise ValueError("BOT_IMPL must use the form 'module.function'")
    module_name, function_name = target.rsplit(".", 1)
    implementation = getattr(importlib.import_module(module_name), function_name)
    if not callable(implementation):
        raise TypeError(f"BOT_IMPL target is not callable: {target}")
    return implementation


__all__ = ["answer", "load_impl"]

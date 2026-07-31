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

from openai import OpenAIError

from agent import (
    ConfidenceTier,
    GuardrailViolation,
    build_bot_response,
    enforce,
    render_copy,
)
from agent.guardrails import DEFAULT_MAX_ANSWERS
from agent.synthesis import SYNTHESIS_ERRORS, groundable_suggestions, synthesize_answer
from agent.routing import (
    SCOPE_COPY,
    SOURCE_WARNING,
    EscalationDecision,
    EscalationReason,
    EscalationTarget,
    EscalationViolation,
    Scope,
    ascii_fold,
    classify_scope,
    phrase_pattern,
    prospective_target,
    route_escalation,
    validate_escalation,
)
from env_file import load_env
from tools._shared.embeddings import (
    CachedEmbedder,
    EmbedderConfigurationError,
    EmbeddingResponseError,
    Embedder,
    OpenAIEmbedder,
)
from tools._shared.generation import (
    AnswerGenerator,
    GeneratorConfigurationError,
    OpenAIAnswerGenerator,
)
from tools._shared.repository import CorpusRepository
from tools._shared.translation import (
    TranslationService,
    OpenAITranslator,
    NullTranslator,
    create_translator,
)
from tools.detect_question_topics import detect_question_topics
from tools.get_qa_thread import get_qa_thread
from tools.search_qa_threads import search_qa_threads
from tools.search_qa_threads.tool import (
    DIRECT_MATCH_THRESHOLD,
    ROLE_TRUST,
    TOPIC_REFERENCE_PROBLEM_THRESHOLD,
    UNKNOWN_ROLE_TRUST,
    VERIFIED_FLAG_TRUST,
)

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
#: Khớp theo biên từ, không phải substring: "hoc phim hoat hinh" KHÔNG được tính
#: là câu hỏi học phí.
UNSUPPORTED_SOURCE_PATTERN = phrase_pattern(UNSUPPORTED_SOURCE_PHRASES)

#: Lỗi hạ tầng retrieval được phép rơi về tìm kiếm cục bộ. Lỗi lập trình
#: (TypeError, KeyError...) KHÔNG nằm ở đây — phải nổ ra để còn sửa, thay vì im
#: lặng tụt một bậc chất lượng.
RETRIEVAL_ERRORS = (
    EmbedderConfigurationError,
    EmbeddingResponseError,
    OpenAIError,
    OSError,
)

#: Lỗi hạ tầng của tầng sinh văn bản. Nuốt được vì tổng hợp là phần BỔ SUNG:
#: mất nó, payload vẫn còn gợi ý trích nguyên văn — đúng hành vi trước khi có
#: RAG. Không gộp vào RETRIEVAL_ERRORS: hai tầng hỏng độc lập nhau.
GENERATION_ERRORS = (*SYNTHESIS_ERRORS, GeneratorConfigurationError, OpenAIError, OSError)

#: Tắt tổng hợp bằng ``DUPBOT_SYNTHESIS=0``. Cần cho lúc chấm điểm và benchmark
#: độ trễ: bộ chấm chỉ tính phần trích dẫn, gọi LLM chỉ tốn tiền và thời gian.
SYNTHESIS_DISABLED_VALUES = frozenset({"0", "false", "no", "off"})

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
        # Fail closed: role lạ không được mặc định thành nguồn đã xác minh.
        return ROLE_TRUST.get(role, UNKNOWN_ROLE_TRUST)
    return VERIFIED_FLAG_TRUST if thread.get("verified_answer") else UNKNOWN_ROLE_TRUST


#: Cổng lexical của chế độ fallback. Đây mới là quyết định thật "cùng vấn đề" /
#: "cùng chủ đề"; ``problem_similarity`` trả ra chỉ là bản hiệu chỉnh của điểm
#: lexical sang thang mà guardrail dùng, KHÔNG phải độ tương đồng ngữ nghĩa.
LOCAL_DIRECT_GATE = 0.48
LOCAL_TOPIC_GATE = 0.40
LOCAL_DIRECT_CEILING = 0.93
#: Nhãn đi kèm mọi điểm số sinh ở chế độ fallback, để consumer (và người chấm)
#: không đọc nhầm 85% lexical thành 85% ngữ nghĩa.
LEXICAL_SIMILARITY_KIND = "lexical_calibrated"
SEMANTIC_SIMILARITY_KIND = "embedding_cosine"


def _calibrate_direct(lexical_score: float) -> float:
    """Ánh xạ tuyến tính điểm lexical [gate, 1.0] -> [DIRECT_MATCH_THRESHOLD, ceiling].

    Bản cũ dùng ``0.78 + score * 0.18`` nên mọi item lọt cổng đều >= 0.78 bất kể
    điểm thật là bao nhiêu, và thang bị nén vào một khoảng hẹp. Ở đây điểm hiển
    thị biến thiên theo đúng điểm lexical, và ``lexical_score`` được giữ nguyên
    trong item để đối chiếu.
    """
    span = max(1e-9, 1.0 - LOCAL_DIRECT_GATE)
    ratio = min(1.0, max(0.0, (lexical_score - LOCAL_DIRECT_GATE) / span))
    return DIRECT_MATCH_THRESHOLD + ratio * (
        LOCAL_DIRECT_CEILING - DIRECT_MATCH_THRESHOLD
    )


def _match_item(
    thread: Mapping[str, Any],
    *,
    problem_similarity: float,
    topic_id: str | None,
    lexical_score: float | None = None,
) -> dict[str, Any]:
    thread_topic = str(thread.get("topic_id") or "")
    trust = thread.get("trust") or {}
    matched_topics = [thread_topic] if topic_id and thread_topic == topic_id else []
    item = {
        "thread_id": str(thread["thread_id"]),
        "title": str(thread.get("title") or ""),
        "problem_similarity": round(problem_similarity, 4),
        # Cùng công thức với jaccard ở search_qa_threads trên hai tập singleton:
        # trùng topic = 1.0, khác topic = 0.0. Không phải số bịa.
        "topic_similarity": 1.0 if matched_topics else 0.0,
        "matched_topics": matched_topics,
        "has_verified_answer": bool(thread.get("verified_answer")),
        "source_trust": round(_source_trust(thread), 2),
        "thread_url": str(trust.get("link") or thread.get("link") or ""),
        "similarity_kind": LEXICAL_SIMILARITY_KIND,
    }
    if lexical_score is not None:
        item["lexical_score"] = round(lexical_score, 4)
    return item


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

    if best_thread_score >= LOCAL_DIRECT_GATE:
        direct = [
            _match_item(
                thread,
                problem_similarity=_calibrate_direct(score),
                topic_id=resolved_topic,
                lexical_score=score,
            )
            for score, thread in ranked_threads
            if score >= max(0.42, best_thread_score * 0.80)
            and str(thread.get("topic_id") or "other") == resolved_topic
        ][:top_k]
        return _detected_result(resolved_topic, question, best_thread_score), {
            "direct_matches": direct,
            "topic_matches": [],
        }

    if best_thread_score >= LOCAL_TOPIC_GATE and resolved_topic != "other":
        topic_threads = [
            thread
            for thread in repository.threads
            if str(thread.get("topic_id") or "") == resolved_topic
        ]
        topic = [
            _match_item(
                thread,
                problem_similarity=TOPIC_REFERENCE_PROBLEM_THRESHOLD
                + min(best_thread_score, 0.75) * 0.25,
                topic_id=resolved_topic,
                lexical_score=best_thread_score,
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
        # Mọi nhánh thoát sớm đều không có nguồn để neo -> không bao giờ tổng hợp.
        "generated_answer": None,
        "generation_mode": "no_source",
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
            "verified": bool(item["thread_has_verified_answer"]),
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
    return UNSUPPORTED_SOURCE_PATTERN.search(ascii_fold(question)) is not None


def _openai_embedder() -> Embedder:
    return CachedEmbedder(delegate=OpenAIEmbedder())


def _synthesis_enabled() -> bool:
    return os.getenv("DUPBOT_SYNTHESIS", "1").strip().lower() not in SYNTHESIS_DISABLED_VALUES


def _attach_generated_answer(
    payload: dict[str, Any],
    question: str,
    suggestions: list[dict[str, Any]],
    *,
    generator: AnswerGenerator | None,
) -> None:
    """Gắn câu trả lời tổng hợp vào ``payload`` (tại chỗ).

    Luôn set khoá ``generated_answer`` để frontend không phải đoán giữa "chưa
    bật" và "bị loại vì không neo được nguồn" — cả hai đều là ``None``, còn
    ``generation_mode`` nói rõ vì sao.
    """

    payload["generated_answer"] = None

    if generator is None and not (_synthesis_enabled() and os.getenv("OPENAI_API_KEY")):
        payload["generation_mode"] = "disabled"
        return

    # Chỉ có topic match = không có lời giải nào để neo. Trích đoạn của topic
    # match là CÂU HỎI của học viên khác; tổng hợp từ đó sẽ biến nỗi lo của họ
    # thành khẳng định của bot. Dừng trước khi gọi provider.
    if not groundable_suggestions(suggestions):
        payload["generation_mode"] = "no_groundable_source"
        return

    try:
        resolved = generator or OpenAIAnswerGenerator()
        generated = synthesize_answer(question, suggestions, generator=resolved)
    except GENERATION_ERRORS as exc:
        # Test tiêm generator giả thì lỗi phải nổ ra, giống cách _openai_embedder
        # được xử lý ở retrieval — im lặng ở đây sẽ giấu bug của chính test.
        if generator is not None:
            raise
        LOGGER.warning("Synthesis failed (%s); trả về gợi ý trích dẫn.", type(exc).__name__)
        payload["generation_mode"] = "unavailable"
        return

    if generated is None:
        # Model tự nhận nguồn không đủ, hoặc guardrail neo nguồn loại bỏ. Đây là
        # kết quả ĐÚNG, không phải lỗi: thà không tổng hợp còn hơn tổng hợp sai.
        payload["generation_mode"] = "ungrounded"
        return

    payload["generated_answer"] = generated
    payload["generation_mode"] = "llm-synthesis"


def answer(
    question: str,
    *,
    top_k: int = MAX_RESULTS,
    embedder: Embedder | None = None,
    repository: CorpusRepository | None = None,
    generator: AnswerGenerator | None = None,
) -> dict[str, Any]:
    """Answer one learner question using retrieval, source ranking and guardrails.

    Khi bật tổng hợp, payload có thêm ``generated_answer`` — câu trả lời do LLM
    viết, neo vào chính các thread trong ``suggestions``. Trường này là BỔ SUNG:
    ``suggestions[*].excerpt`` vẫn là trích đoạn nguyên văn, chưa từng đi qua LLM.
    """

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
        decision = route_escalation(
            question=normalized_question,
            scope=scope,
            tier=ConfidenceTier.NONE,
        )
        copy = render_copy(ConfidenceTier.NONE, decision.target)
        return _safe_empty_payload(
            reason="no_source",
            headline=copy["headline"],
            note=copy["note"],
            escalation=decision,
        )

    if _is_too_vague(normalized_question):
        return _safe_empty_payload(
            reason="too_vague",
            headline="Mình cần thêm một chút thông tin",
            note=CLARIFYING_QUESTION,
            clarifying_question=CLARIFYING_QUESTION,
        )

    # ---------------------------------------------------------------------------
    # Translation Step: Handle multilingual queries (English → Vietnamese)
    # ---------------------------------------------------------------------------
    # Inject AFTER scope classification, BEFORE topic detection.
    # This ensures:
    # - Translation only runs for IN_SCOPE questions (cost optimization)
    # - All downstream tools (topic detection, embeddings, search) work with Vietnamese
    # - Original question preserved for user-facing text
    translator: TranslationService | None = None
    translation_applied = False
    original_question = normalized_question

    if os.getenv("TRANSLATION_ENABLED", "false").lower() == "true":
        try:
            translator = create_translator()
            if not isinstance(translator, NullTranslator):
                detected_lang = translator.detect_language(normalized_question)
                if detected_lang != "vi":
                    translated = translator.translate_to_vietnamese(normalized_question)
                    normalized_question = translated
                    translation_applied = True
                    LOGGER.info(
                        "Translated query from %s to Vietnamese: %s → %s",
                        detected_lang,
                        original_question,
                        normalized_question,
                    )
        except Exception as exc:
            LOGGER.warning("Translation failed (%s); using original query.", type(exc).__name__)
            translator = None

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
        except RETRIEVAL_ERRORS as exc:
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
    matches_needing_detail = [
        *list(search_result.get("direct_matches") or [])[:top_k],
        # Topic match cũng cần chi tiết: nếu không, trích đoạn rơi về TIÊU ĐỀ —
        # thứ không nằm nguyên văn trong thread, tức là bịa nội dung.
        *list(search_result.get("topic_matches") or [])[:top_k],
    ]
    for match in matches_needing_detail:
        thread_id = str(match.get("thread_id") or "")
        detail = get_qa_thread(
            thread_id,
            max_answers=DEFAULT_MAX_ANSWERS,
            repository=resolved_repository,
        )
        if detail.get("found"):
            details[thread_id] = detail

    try:
        response = enforce(
            build_bot_response(
                search_result,
                details,
                status="pending",
                max_threads=top_k,
            )
        )
    except GuardrailViolation as exc:
        # Guardrail bắt được payload sai (bịa, thiếu link, topic match trình như
        # lời giải...). Không được ném lên HTTP thành 503: rơi về tin nhắn an toàn
        # tier NONE và chuyển cho người thật, đúng như enforce() đã hứa.
        LOGGER.error("Guardrail violation, falling back to safe reply: %s", exc)
        decision = route_escalation(
            question=normalized_question,
            scope=scope,
            tier=ConfidenceTier.NONE,
            primary_topic_id=detected["primary_topic"]["id"],
            intent=detected["intent"],
        )
        copy = render_copy(ConfidenceTier.NONE, decision.target)
        return _safe_empty_payload(
            reason="no_source",
            headline=copy["headline"],
            note=copy["note"],
            retrieval_mode=retrieval_mode,
            warning=warning,
            escalation=decision,
        )
    payload = response.model_dump(mode="json")
    suggestions = payload["suggestions"]
    has_answer = bool(suggestions) and payload["confidence"] != "none"

    # Định tuyến theo địa hạt, không mặc định LabCoach. Ba lý do chuyển: corpus
    # rỗng, chỉ có học viên trả lời (cần xác minh), học viên bấm "Chưa đúng ý tôi"
    # (do frontend gọi /escalate, không tính ở đây).
    try:
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
    except EscalationViolation as exc:
        # Kẹp về phía an toàn thay vì trả 503: trong phạm vi thì cứ chuyển cho
        # người thật (thà phiền còn hơn bỏ rơi học viên), ngoài phạm vi thì không
        # chuyển cho ai.
        LOGGER.error("Escalation violation, clamping decision: %s", exc)
        decision = (
            route_escalation(
                question=normalized_question,
                scope=scope,
                tier=ConfidenceTier.NONE,
                primary_topic_id=detected["primary_topic"]["id"],
                intent=detected["intent"],
            )
            if scope is Scope.IN_SCOPE
            else _no_escalation()
        )

    # Copy phải gọi đúng tên vai trò sẽ xử lý: đã chuyển thì nói vai trò đã nhận,
    # chưa chuyển thì nói vai trò mà nút "Chưa đúng ý tôi" sẽ gọi tới.
    copy_target = (
        decision.target
        if decision.tagged
        else prospective_target(
            normalized_question,
            detected["primary_topic"]["id"],
            detected["intent"],
        )
    )
    payload.update(render_copy(response.confidence, copy_target))
    payload.update(
        {
            "retrieval_mode": retrieval_mode,
            "similarity_kind": (
                LEXICAL_SIMILARITY_KIND
                if retrieval_mode == "local-corpus-fallback"
                else SEMANTIC_SIMILARITY_KIND
            ),
            "detected_topics": {
                "primary": detected["primary_topic"],
                "subtopics": detected["subtopics"],
                "intent": detected["intent"],
            },
            "has_answer": has_answer,
            "reason": None if has_answer else "no_source",
            "results": _legacy_results(suggestions),
            "clarifying_question": None,
            "translation_applied": translation_applied,  # Track translation usage
            **_escalation_fields(decision),
        }
    )
    if decision.reason is EscalationReason.UNVERIFIED_SOURCE:
        # Vẫn hiển thị gợi ý, nhưng dán nhãn để không ai đọc nhầm là chính thức.
        payload["source_warning"] = SOURCE_WARNING
    if warning:
        payload["warning"] = warning

    # Chỉ tổng hợp khi thật sự có nguồn để neo. Tier NONE / không gợi ý thì câu
    # trả lời an toàn đã được soạn sẵn, gọi LLM chỉ tạo cơ hội bịa.
    if has_answer:
        _attach_generated_answer(payload, normalized_question, suggestions, generator=generator)
    else:
        payload["generated_answer"] = None
        payload["generation_mode"] = "no_source"
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

"""Test hồi quy cho các lỗ hổng guardrail đã sửa.

Mỗi test dưới đây đỏ trên bản trước khi sửa. Tên test ghi kèm số hiệu lỗ hổng
trong bản review để tra ngược.
"""

from __future__ import annotations

import pytest

from agent.guardrails import (
    BotResponse,
    ConfidenceTier,
    GuardrailViolation,
    Relevance,
    SourceTier,
    SuggestedThread,
    _pick_answers,
    build_bot_response,
    enforce,
    revalidate_buckets,
    tier_for_content,
)
from agent.routing import Scope, classify_scope
from bot import _source_trust, answer
from tools.search_qa_threads.tool import (
    DIRECT_MATCH_THRESHOLD,
    TOPIC_REFERENCE_PROBLEM_THRESHOLD,
    UNKNOWN_ROLE_TRUST,
)

TOPIC_LEVEL = (TOPIC_REFERENCE_PROBLEM_THRESHOLD + DIRECT_MATCH_THRESHOLD) / 2


def _match(**overrides):
    match = {
        "thread_id": "t1",
        "title": "Lỗi cài thư viện",
        "problem_similarity": 0.90,
        "topic_similarity": 1.0,
        "has_verified_answer": True,
        "source_trust": 1.0,
        "thread_url": "https://discord.com/channels/1/2/3",
    }
    match.update(overrides)
    return match


def _detail(*answers):
    return {"question": "em bị lỗi pip install", "selected_answers": list(answers)}


# --- #1: policy marker không được gỡ cổng ngoài phạm vi --------------------


@pytest.mark.parametrize(
    "question",
    [
        "ty so tran real madrid the nao, co sao khong",
        "gia vang hom nay co anh huong gi khong",
        "toi nay co bong da khong, co bi tru gi khong",
    ],
)
def test_policy_marker_khong_go_cong_ngoai_pham_vi(question):
    assert classify_scope(question) is Scope.OFF_TOPIC


def test_policy_marker_van_go_cong_liem_chinh(question="nop bai ho ban co bi coi la gian lan khong"):
    assert classify_scope(question) is Scope.IN_SCOPE


def test_nho_lam_bai_thay_van_bi_chan():
    assert classify_scope("viet ho em bai luan tieng anh") is Scope.INTEGRITY


# --- #3: guardrail xếp lại rổ direct/topic ---------------------------------


def test_revalidate_ha_direct_khong_du_diem_xuong_topic():
    direct, topic = revalidate_buckets(
        {"direct_matches": [_match(problem_similarity=TOPIC_LEVEL, topic_similarity=1.0)]}
    )
    assert direct == []
    assert len(topic) == 1


def test_revalidate_loai_han_item_khong_dat_nguong_nao():
    direct, topic = revalidate_buckets(
        {"direct_matches": [_match(problem_similarity=0.05, topic_similarity=0.0)]}
    )
    assert (direct, topic) == ([], [])


def test_direct_bi_ha_cap_khong_duoc_trinh_loi_giai():
    response = build_bot_response(
        {"direct_matches": [_match(problem_similarity=TOPIC_LEVEL)]},
        {"t1": _detail({"answer_id": "a1", "content": "xoá cache đi bạn", "author_role": "Mentor", "verification_label": "VERIFIED"})},
    )
    assert response.suggestions[0].relevance is Relevance.TOPIC
    assert response.suggestions[0].main_answer is None


# --- #4: guardrail trip -> câu trả lời an toàn, không phải exception -------


def test_guardrail_violation_khong_thoat_ra_ngoai(monkeypatch):
    def _explode(*args, **kwargs):
        raise GuardrailViolation("mô phỏng payload sai")

    monkeypatch.setattr("bot.enforce", _explode)
    payload = answer("em quen diem danh buoi 3 thi sao a")
    assert payload["confidence"] == "none"
    assert payload["suggestions"] == []
    assert payload["tag_labcoach"] is True


# --- #5: trust fail closed -------------------------------------------------


def test_role_la_khong_duoc_coi_la_da_xac_minh():
    trust = _source_trust({"trust": {"author_role": "TA"}, "verified_answer": True})
    assert trust == UNKNOWN_ROLE_TRUST


# --- #2: điểm fallback được gán nhãn, không giả làm điểm ngữ nghĩa ---------


def test_fallback_gan_nhan_similarity_kind(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    payload = answer("em quen diem danh buoi 3 thi sao a")
    assert payload["retrieval_mode"] == "local-corpus-fallback"
    assert payload["similarity_kind"] == "lexical_calibrated"


# --- #6: tier phải khớp nội dung trình ra ----------------------------------


def test_high_khong_co_loi_giai_da_xac_minh_thi_ha_xuong_low():
    response = build_bot_response(
        {"direct_matches": [_match()]},
        {"t1": _detail()},  # mọi reply đã bị get_qa_thread lọc sạch
    )
    assert response.confidence is ConfidenceTier.LOW


def test_enforce_chan_tier_high_rong_ruot():
    response = BotResponse(
        confidence=ConfidenceTier.HIGH,
        headline="x",
        note="y",
        suggestions=[
            SuggestedThread(
                thread_id="t1",
                rank=1,
                title="t",
                similarity=90,
                relevance=Relevance.DIRECT,
                excerpt="câu hỏi gốc",
                thread_url="https://discord.com/channels/1/2/3",
                source_tier=SourceTier.VERIFIED,
            )
        ],
    )
    with pytest.raises(GuardrailViolation):
        enforce(response)


def test_tier_for_content_rong_thi_ve_none():
    assert tier_for_content(ConfidenceTier.LOW, []) is ConfidenceTier.NONE


# --- #7: câu chính và câu bổ sung không được trùng ------------------------


def test_pick_answers_khong_lap_lai_cung_mot_cau():
    main, supp = _pick_answers(
        _detail(
            {"answer_id": "a1", "content": "xoá cache", "author_role": "Learner", "verification_label": "COMMUNITY_UNVERIFIED"},
            {"answer_id": "a2", "content": "đổi python 3.11", "author_role": "Learner", "verification_label": "COMMUNITY_UNVERIFIED"},
        )
    )
    assert main.answer_id == "a1"
    assert supp is not None and supp.answer_id == "a2"


def test_pick_answers_mot_cau_duy_nhat_thi_khong_co_bo_sung():
    main, supp = _pick_answers(
        _detail({"answer_id": "a1", "content": "xoá cache", "author_role": "Learner", "verification_label": "COMMUNITY_UNVERIFIED"})
    )
    assert main.answer_id == "a1"
    assert supp is None


# --- #9: copy gọi đúng tên vai trò được định tuyến ------------------------


def test_note_goi_dung_vai_tro_thay_vi_luon_labcoach(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    payload = answer("em bi loi pip install khong cai duoc package a")
    assert "LabCoach" not in payload["note"]
    assert "Mentor" in payload["note"]


def test_render_copy_mac_dinh_van_la_labcoach():
    from agent.guardrails import render_copy

    assert "LabCoach" in render_copy(ConfidenceTier.NONE)["note"]


# --- #10: chặn chủ đề ngoài corpus theo biên từ ---------------------------


def test_hoc_phim_khong_bi_nham_thanh_hoc_phi():
    from bot import _is_known_out_of_corpus_scope

    assert _is_known_out_of_corpus_scope("hoc phi khoa nay bao nhieu") is True
    assert _is_known_out_of_corpus_scope("em muon hoc phim hoat hinh") is False


# --- #11: lỗi lập trình không bị nuốt thành "degrade êm" -------------------


def test_loi_lap_trinh_khong_bi_nuot(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def _boom(*args, **kwargs):
        raise TypeError("bug thật trong pipeline")

    monkeypatch.setattr("bot.detect_question_topics", _boom)
    with pytest.raises(TypeError):
        answer("em quen diem danh buoi 3 thi sao a")


def test_loi_ha_tang_van_rot_ve_tim_kiem_cuc_bo(monkeypatch):
    from tools._shared.embeddings import EmbedderConfigurationError

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def _unavailable(*args, **kwargs):
        raise EmbedderConfigurationError("hết quota")

    monkeypatch.setattr("bot.detect_question_topics", _unavailable)
    payload = answer("em quen diem danh buoi 3 thi sao a")
    assert payload["retrieval_mode"] == "local-corpus-fallback"


# --- #14: /escalate phân biệt học viên bấm nút và bot tự chuyển -----------


def test_escalate_ghi_dung_ly_do_khi_bot_tu_chuyen():
    from app import EscalationRequest, escalate_thread

    auto = escalate_thread(
        "thread-x",
        EscalationRequest(
            query="em bi loi pip install",
            reason="corpus rỗng",
            trigger="auto_no_source",
        ),
    )
    manual = escalate_thread(
        "thread-y",
        EscalationRequest(query="em bi loi pip install", reason="chưa đúng ý"),
    )
    assert auto["reason"] == "no_source"
    assert manual["reason"] == "learner_request"


# --- T1: vai trò nhân sự khoá học là nguồn đã xác minh --------------------


def test_cau_tra_loi_cua_mentor_la_nguon_da_xac_minh(tmp_path):
    import json

    from tools._shared.repository import CorpusRepository
    from tools.get_qa_thread import get_qa_thread

    corpus = tmp_path / "corpus.json"
    corpus.write_text(
        json.dumps(
            {
                "threads": [
                    {
                        "thread_id": "t1",
                        "title": "Lỗi pip",
                        "topic_id": "deps_error",
                        "link": "https://example.test/t1",
                        "question": {"content": "em bị lỗi pip install"},
                        "replies": [
                            {
                                "message_id": "m1",
                                "content": "Bạn nâng pip lên bản mới nhất nhé",
                                "author_name": "Khoa",
                                "author_role": "Mentor",
                            }
                        ],
                        "verified_answer": False,
                        "trust": None,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = get_qa_thread("t1", repository=CorpusRepository(corpus))
    answer_item = result["selected_answers"][0]
    assert answer_item["is_verified"] is True
    assert answer_item["verification_label"] == "VERIFIED"


# --- T2: nhiều subtopic không được làm mất kết quả cùng chủ đề ------------


def test_topic_similarity_khong_bi_pha_loang_boi_subtopic():
    from tools.search_qa_threads.tool import search_qa_threads

    class OneVector:
        model_name = "test"

        def embed(self, texts):
            return [[0.0, 1.0] for _ in texts]

    class Repo:
        threads = [
            {
                "thread_id": "t1",
                "title": "Nghỉ học",
                "topic_id": "nghi_hoc",
                "link": "https://example.test/t1",
                "question": {"content": "xin nghỉ buổi 3"},
                "replies": [],
                "verified_answer": True,
                "trust": {"author_role": "LabCoach", "link": "https://example.test/t1"},
            }
        ]

    result = search_qa_threads(
        "xin nghi buoi 3",
        topics=["nghi_hoc", "diem_danh", "xp_diem"],
        repository=Repo(),
        embedder=OneVector(),
    )
    # 3 topic truy vấn vs 1 topic thread: jaccard chỉ ra 0.33 (< 0.50) và thread
    # bị loại; theo thành viên thì vẫn là 1.0.
    matched = (result["direct_matches"] or result["topic_matches"])[0]
    assert matched["topic_similarity"] == 1.0


# --- T3 / T4: tâm cụm và cache ghi song song ------------------------------


def test_centroid_lay_trung_binh_tung_thread():
    from tools.detect_question_topics.tool import _centroid

    assert _centroid([[1.0, 0.0], [0.0, 1.0]]) == [0.5, 0.5]
    assert _centroid([]) == []


def test_cache_khong_lam_mat_entry_cua_instance_khac(tmp_path):
    from tools._shared.embeddings import CachedEmbedder

    class Fixed:
        model_name = "test"

        def __init__(self, value):
            self.value = value

        def embed(self, texts):
            return [[self.value] for _ in texts]

    path = tmp_path / "cache.json"
    first = CachedEmbedder(delegate=Fixed(1.0), cache_path=path)
    second = CachedEmbedder(delegate=Fixed(2.0), cache_path=path)
    first.embed(["câu A"])
    second.embed(["câu B"])  # instance thứ hai không được xoá entry của A

    reloaded = CachedEmbedder(delegate=Fixed(9.0), cache_path=path)
    assert reloaded.embed(["câu A"]) == [[1.0]]

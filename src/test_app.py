from __future__ import annotations

import pytest

from starlette.testclient import TestClient

from app import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def force_local_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit test phải tất định và không gọi API tính phí.

    Các khẳng định trong file này pin hành vi của chế độ ``local-corpus-fallback``;
    nếu máy dev có ``OPENAI_API_KEY`` thì cùng một test lại chạy nhánh embeddings
    và đỏ vì lý do không liên quan. Nhánh embeddings được đo bằng
    ``src/test/test_cases.py``, không phải ở đây.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_health_reports_active_retrieval_mode() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["retrieval"] in {
        "openai-embeddings",
        "local-corpus-fallback",
    }


def test_built_frontend_is_served_from_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    if response.headers["content-type"].startswith("text/html"):
        assert '<div id="root"></div>' in response.text
    else:
        assert "DupBot API is running" in response.text


def test_search_endpoint_runs_the_full_local_pipeline() -> None:
    response = client.post(
        "/api/threads/search",
        json={
            "query": "làm sao biết mình đã được ghi nhận có mặt hôm nay",
            "topK": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "high"
    assert body["suggestions"][0]["thread_id"] == "1529643349835907072"
    assert body["render_buttons"] is True


def test_feedback_and_escalation_endpoints() -> None:
    resolved = client.patch(
        "/api/threads/question-1/status",
        json={"status": "resolved"},
    )
    escalated = client.post(
        "/api/threads/question-2/escalate",
        json={
            "query": "Một câu hỏi cần LabCoach",
            "rejectedThreadIds": ["thread-1"],
            "reason": "Kết quả chưa đúng ý.",
        },
    )

    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert escalated.status_code == 200
    assert escalated.json()["status"] == "escalated"
    assert escalated.json()["queuePosition"] >= 1

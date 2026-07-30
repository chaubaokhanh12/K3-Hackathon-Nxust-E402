"""FastAPI entrypoint for the integrated DupBot prototype."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from agent.routing import classify_scope, route_escalation
from bot import answer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

app = FastAPI(
    title="DupBot API",
    version="1.0.0",
    description="TrustQA retrieval, guardrails, feedback and escalation API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=8_000)
    topK: int = Field(default=3, ge=1, le=3)


class StatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["resolved"]


class EscalationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=8_000)
    rejectedThreadIds: list[str] = Field(default_factory=list, max_length=3)
    reason: str = Field(min_length=1, max_length=2_000)


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = Field(default=None, max_length=200)
    author: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8_000)


_state_lock = Lock()
_thread_statuses: dict[str, str] = {}
_escalations: list[dict[str, Any]] = []
_messages: list[dict[str, Any]] = []


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "dupbot",
        "retrieval": (
            "openai-embeddings"
            if os.getenv("OPENAI_API_KEY")
            else "local-corpus-fallback"
        ),
        "frontend_built": (FRONTEND_DIST / "index.html").is_file(),
    }


@app.post("/api/threads/search")
def search_threads(payload: SearchRequest) -> dict[str, Any]:
    try:
        return answer(payload.query, top_k=payload.topK)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DupBot retrieval is temporarily unavailable.",
        ) from exc


@app.patch("/api/threads/{thread_id}/status")
def update_thread_status(thread_id: str, payload: StatusRequest) -> dict[str, Any]:
    with _state_lock:
        _thread_statuses[thread_id] = payload.status
    return {"ok": True, "threadId": thread_id, "status": payload.status}


@app.post("/api/threads/{thread_id}/escalate")
def escalate_thread(
    thread_id: str, payload: EscalationRequest
) -> dict[str, Any]:
    # Học viên bấm "Chưa đúng ý tôi": chuyển theo địa hạt câu hỏi (Admin / Mentor /
    # LabCoach) thay vì luôn gọi LabCoach.
    decision = route_escalation(
        question=payload.query,
        scope=classify_scope(payload.query),
        learner_requested=True,
    )
    if not decision.tagged:
        # Câu ngoài phạm vi khoá học không có nút escalate, nên đây là lời gọi sai.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Câu hỏi nằm ngoài phạm vi khoá học, không chuyển cho người thật.",
        )
    with _state_lock:
        _thread_statuses[thread_id] = "escalated"
        _escalations.append(
            {
                "threadId": thread_id,
                "targetRole": decision.target.value,
                "slaMinutes": decision.sla_minutes,
                **payload.model_dump(),
            }
        )
        queue_position = len(_escalations)
    return {
        "ok": True,
        "threadId": thread_id,
        "status": "escalated",
        "queuePosition": queue_position,
        "targetRole": decision.target.value,
        "slaMinutes": decision.sla_minutes,
    }


@app.post(
    "/api/channels/{channel_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
def create_message(channel_id: str, payload: MessageRequest) -> dict[str, Any]:
    message_id = payload.id or f"message-{uuid4().hex}"
    with _state_lock:
        _messages.append(
            {
                "id": message_id,
                "channelId": channel_id,
                **payload.model_dump(exclude={"id"}),
            }
        )
    return {"ok": True, "id": message_id, "channelId": channel_id}


if (FRONTEND_DIST / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )


@app.get("/", include_in_schema=False)
def frontend_index() -> Response:
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return Response(
        "DupBot API is running. Build the UI with: cd frontend; npm run build",
        media_type="text/plain",
    )

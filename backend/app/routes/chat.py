"""
Chat API Routes — session management + AI Q&A.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chat_service import (
    api_create_session,
    api_list_sessions,
    api_get_session,
    api_get_messages,
    api_delete_session,
    api_send_message,
)

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


# ── Request models ──

class CreateSessionRequest(BaseModel):
    title: str = ""
    province: str = ""
    subject_type: str = ""
    score: int = 0
    rank: int = 0
    selected_subjects: list[str] = Field(default_factory=list)
    preferred_majors: list[str] = Field(default_factory=list)
    preferred_cities: list[str] = Field(default_factory=list)
    preferred_tiers: list[str] = Field(default_factory=list)
    strategy: str = ""
    related_recommendation_id: str = ""


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    use_rag: bool = True
    use_recommendation_context: bool = True


# ── Routes ──

@router.post("/sessions")
async def create_chat_session(body: CreateSessionRequest) -> dict[str, Any]:
    return api_create_session(
        title=body.title,
        province=body.province,
        subject_type=body.subject_type,
        score=body.score,
        rank=body.rank,
        selected_subjects=body.selected_subjects,
        preferred_majors=body.preferred_majors,
        preferred_cities=body.preferred_cities,
        preferred_tiers=body.preferred_tiers,
        strategy=body.strategy,
        related_recommendation_id=body.related_recommendation_id,
    )


@router.get("/sessions")
async def list_chat_sessions() -> dict[str, Any]:
    return api_list_sessions()


@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str) -> dict[str, Any]:
    result = api_get_session(session_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
    return result


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str) -> dict[str, Any]:
    return api_delete_session(session_id)


@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(session_id: str) -> dict[str, Any]:
    return api_get_messages(session_id)


@router.post("/sessions/{session_id}/messages")
async def send_chat_message(session_id: str, body: SendMessageRequest) -> dict[str, Any]:
    result = await api_send_message(
        session_id=session_id,
        message=body.message,
        use_rag=body.use_rag,
        use_recommendation_context=body.use_recommendation_context,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Bad request"))
    return result

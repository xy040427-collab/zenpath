"""
CHSI RAG Chat API — general Q&A backed by CHSI evidence.

Accepts free-text questions and routes them through the RAG pipeline
with strict guardrails:
  - School profiles, admission policies, major info → CHSI evidence
  - Employment rates, admission chances → rejected with "资料不足"
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever
from rag.evidence_packer import pack_evidence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag/chat", tags=["CHSI RAG Chat"])

_retriever: ChsiVectorRetriever | None = None


def _get_retriever() -> ChsiVectorRetriever:
    global _retriever
    if _retriever is None:
        _retriever = ChsiVectorRetriever()
    return _retriever


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


@router.post("/ask")
async def ask(request: ChatRequest) -> dict[str, Any]:
    """Answer a general question using CHSI RAG evidence.

    Returns:
      - answerable: whether CHSI has data for this question
      - answer_mode: "official_evidence" or "inferential_guidance"
      - evidence: retrieved CHSI chunks (if answerable)
      - message: user-facing response or "资料不足" explanation
      - sources: source URLs from evidence
    """
    retriever = _get_retriever()
    result = retriever.search(request.question, top_k=5)
    packed = pack_evidence(result, max_items=5)

    answerable = packed.get("answerable", False)
    evidence = packed.get("evidence") or []
    intent = packed.get("intent", "unknown")

    if not answerable:
        return {
            "success": True,
            "answerable": False,
            "intent": intent,
            "message": packed.get("message", "当前 CHSI 官方库中暂无相关数据，不能可靠回答此问题。"),
            "evidence": [],
            "sources": [],
            "disclaimer": packed.get("disclaimer", ""),
        }

    # Build user-friendly answer from evidence
    if intent == "school_profile":
        fragments = []
        for ev in evidence[:3]:
            content = ev.get("content", "")[:500]
            if content:
                fragments.append(content)
        combined = "\n\n".join(fragments) if fragments else "暂无详细资料"
        message = f"根据教育部阳光高考平台官方数据：\n\n{combined}"
    else:
        # Generic: include all evidence
        parts = []
        for ev in evidence[:5]:
            title = ev.get("title", "")
            content = ev.get("content", "")[:300]
            if content:
                parts.append(f"**{title}**\n{content}")
        message = (
            "根据教育部阳光高考平台（CHSI）官方资料：\n\n"
            + "\n\n".join(parts)
            if parts
            else "已检索到相关官方资料，但内容较为简略。"
        )

    sources = [
        {"title": ev.get("title", ""), "source_url": ev.get("source_url", ""), "doc_type": ev.get("doc_type", "")}
        for ev in evidence[:5]
    ]

    return {
        "success": True,
        "answerable": True,
        "answer_mode": packed.get("answer_mode", "official_evidence"),
        "intent": intent,
        "message": message,
        "evidence": evidence,
        "sources": sources,
        "disclaimer": "数据来源：教育部阳光高考平台 (gaokao.chsi.com.cn)",
    }

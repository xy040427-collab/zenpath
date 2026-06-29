"""
Chat Service — orchestrates the full RAG + LLM pipeline for ZENPATH AI Q&A.

Pipeline:
  user query → query rewrite → intent route → cache check →
  vector search → rerank → evidence pack → prompt build → LLM call →
  post-check → save history → return
"""
from __future__ import annotations

import logging
import time
from typing import Any

from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever
from rag.evidence_packer import pack_evidence

from app.services.query_rewriter import rewrite_query
from app.services.rag_reranker import rerank_chunks
from app.services.llm_prompt_builder import build_chat_prompt, build_simple_answer
from app.services.llm_client import call_llm
from app.services.chat_post_checker import check_answer
from app.services.chat_cache_service import check_cache, save_cache
from app.services.chat_session_service import (
    create_session, list_sessions, get_session,
    archive_session, save_message, get_messages,
)

logger = logging.getLogger(__name__)

_retriever: ChsiVectorRetriever | None = None


def _get_retriever() -> ChsiVectorRetriever:
    global _retriever
    if _retriever is None:
        _retriever = ChsiVectorRetriever()
    return _retriever


# ═══════════════════════════════════════════
#  Session API
# ═══════════════════════════════════════════

def api_create_session(
    user_id: str = "anonymous",
    title: str = "",
    province: str = "",
    subject_type: str = "",
    score: int = 0,
    rank: int = 0,
    selected_subjects: list[str] | None = None,
    preferred_majors: list[str] | None = None,
    preferred_cities: list[str] | None = None,
    preferred_tiers: list[str] | None = None,
    strategy: str = "",
    related_recommendation_id: str = "",
) -> dict:
    result = create_session(
        user_id=user_id, title=title,
        province=province, subject_type=subject_type,
        score=score, rank=rank,
        selected_subjects=selected_subjects,
        preferred_majors=preferred_majors,
        preferred_cities=preferred_cities,
        preferred_tiers=preferred_tiers,
        strategy=strategy,
        related_recommendation_id=related_recommendation_id,
    )
    return {"success": True, **result}


def api_list_sessions(user_id: str = "anonymous") -> dict:
    sessions = list_sessions(user_id=user_id)
    return {"success": True, "sessions": sessions}


def api_get_session(session_id: str) -> dict:
    session = get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}
    return {"success": True, "session": session}


def api_get_messages(session_id: str) -> dict:
    messages = get_messages(session_id)
    return {"success": True, "messages": messages}


def api_delete_session(session_id: str) -> dict:
    archive_session(session_id)
    return {"success": True}


# ═══════════════════════════════════════════
#  Chat Pipeline
# ═══════════════════════════════════════════

async def api_send_message(
    session_id: str,
    message: str,
    user_id: str = "anonymous",
    use_rag: bool = True,
    use_recommendation_context: bool = True,
) -> dict:
    """Full pipeline: rewrite → intent → cache → search → rerank → evidence → prompt → LLM → post-check."""
    start_time = time.monotonic()

    # ── Load session context ──
    session = get_session(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}

    user_context = {
        "province": session.get("province", ""),
        "subject_type": session.get("subject_type", ""),
        "score": session.get("score", 0),
        "rank": session.get("rank", 0),
        "selected_subjects": _parse_list(session.get("selected_subjects")),
        "preferred_majors": _parse_list(session.get("preferred_majors")),
        "preferred_cities": _parse_list(session.get("preferred_cities")),
        "preferred_tiers": _parse_list(session.get("preferred_tiers")),
    }

    # ── Get recent messages for context ──
    history_messages = get_messages(session_id, limit=20)
    last_school = ""
    last_major_group = ""
    chat_history = []
    for m in history_messages:
        chat_history.append({"role": m["role"], "content": m["content"][:500]})
        if m.get("structured_payload"):
            try:
                import json
                sp = json.loads(m["structured_payload"]) if isinstance(m["structured_payload"], str) else m["structured_payload"]
                ents = sp.get("entities", {})
                if ents.get("school_names"):
                    last_school = ents["school_names"][0]
                if ents.get("major_names"):
                    last_major_group = ents["major_names"][0]
            except Exception:
                pass

    # 1. Save user message
    save_message(session_id, "user", message, user_id=user_id)

    # 2. Query rewrite
    rewritten = rewrite_query(
        message,
        session_context=user_context,
        last_school=last_school,
        last_major_group=last_major_group,
        user_context=user_context,
    )
    search_query = rewritten["rewritten_query"]
    entities = rewritten["entities"]

    # 3. Intent route (via retriever's built-in router)
    retriever = _get_retriever()
    routed = retriever.route(search_query) if use_rag else {"intent": "unknown", "filters": {}}
    intent = routed.get("intent", "unknown")

    # 4. Cache check
    if use_rag:
        cached = check_cache(search_query, intent=intent, user_context=user_context)
        if cached:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            save_message(
                session_id, "assistant", cached["answer"],
                intent=intent, answerable=True,
                sources=cached.get("sources"),
                latency_ms=elapsed_ms, from_cache=True,
            )
            return {
                "success": True,
                "message_id": "",
                "answer": cached["answer"],
                "intent": intent,
                "sources": cached.get("sources") or [],
                "structured": {"rewritten_query": search_query, "from_cache": True},
                "suggested_questions": [],
            }

    # 5. Vector search
    rag_results = []
    if use_rag:
        filters = dict(routed.get("filters", {}))
        school_filter = (entities.get("school_names") or [None])[0]
        major_filter = (entities.get("major_names") or [None])[0]
        if school_filter:
            filters["school_name"] = school_filter
        if major_filter:
            filters["major_name"] = major_filter
        raw_results = retriever.search(
            search_query, top_k=20, **filters,
        )
        rag_results = raw_results.get("results") or []

    # 6. Rerank
    reranked = rerank_chunks(
        rag_results, search_query, intent=intent,
        school_names=entities.get("school_names"),
        major_names=entities.get("major_names"),
        top_k=8,
    ) if rag_results else []

    # 7. Evidence pack
    evidence_result = pack_evidence({"results": reranked, "intent": intent, "query": search_query}, max_items=5)
    answerable = evidence_result.get("answerable", False)
    evidence = evidence_result.get("evidence") or []
    missing_data = evidence_result.get("missing_data") or []

    # 8. Build prompt — always include whatever evidence we found
    messages = build_chat_prompt(
        query=message,
        intent=intent,
        user_context=user_context,
        rag_evidence=evidence if evidence else None,
        answerable=answerable,
        missing_data=missing_data if not answerable else None,
        chat_history=chat_history,
    )

    # 9. LLM call
    llm_response = await call_llm(messages)
    answer = llm_response.get("answer", "")
    is_mock = llm_response.get("mock", False)

    if is_mock and evidence:
        answer = build_simple_answer(message, evidence, intent, answerable, missing_data)

    # 10. Post-check
    checked = check_answer(answer)
    answer = checked["answer"]

    # 11. Build sources
    sources = [
        {"title": ev.get("title", ""), "source_url": ev.get("source_url", ""),
         "doc_type": ev.get("doc_type", ""), "school_name": ev.get("school_name", "")}
        for ev in evidence[:5]
    ]

    # 12. Save assistant message
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    structured = {
        "rewritten_query": search_query,
        "intent": intent,
        "answerable": answerable,
        "retrieval_count": len(rag_results),
        "reranked_count": len(reranked),
        "used_evidence_count": len(evidence),
        "entities": entities,
    }
    save_message(
        session_id, "assistant", answer,
        intent=intent, answerable=answerable,
        structured_payload=structured,
        sources=sources,
        token_count=llm_response.get("token_count", 0),
        latency_ms=elapsed_ms,
    )

    # 13. Save cache
    if answerable and not is_mock:
        save_cache(search_query, answer, intent=intent, user_context=user_context, sources=sources)

    return {
        "success": True,
        "answer": answer,
        "intent": intent,
        "answerable": answerable,
        "sources": sources,
        "structured": {
            "rewritten_query": search_query,
            "retrieval_count": len(rag_results),
            "reranked_count": len(reranked),
            "used_evidence_count": len(evidence),
            "answerable": answerable,
            "warnings": checked.get("warnings", []),
        },
    }


def _parse_list(val: Any) -> list[str]:
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            import json
            return json.loads(val)
        except Exception:
            return [val]
    return []

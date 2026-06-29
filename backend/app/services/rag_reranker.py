"""
Lightweight RAG reranker for Chat pipeline.

Sorts retrieved chunks by:
  1. doc_type priority (admission_policy_clause > school_profile > department_info > ...)
  2. school_name / major_name match bonus
  3. Content length sufficiency
  4. source_url presence
  5. Original vector similarity score
"""
from __future__ import annotations

from typing import Any

DOC_TYPE_PRIORITY = {
    "admission_policy_clause": 10,
    "school_profile": 8,
    "department_info": 7,
    "major_general_profile": 6,
    "major_analysis": 5,
    "major_school_distribution": 4,
}


def rerank_chunks(
    chunks: list[dict[str, Any]],
    query: str,
    intent: str = "",
    top_k: int = 5,
    school_names: list[str] | None = None,
    major_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Rerank retrieved chunks for a query.

    Args:
        chunks: Raw retrieval results with 'score', 'content', 'metadata'
        query: The rewritten/current query
        intent: Intent from intent router
        top_k: Number of top results to return
        school_names: School names to boost
        major_names: Major names to boost

    Returns:
        Reranked list, length <= top_k
    """
    scored = []
    for item in chunks:
        score = _compute_rerank_score(item, query, intent, school_names, major_names)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def _compute_rerank_score(
    item: dict[str, Any],
    query: str,
    intent: str,
    school_names: list[str] | None,
    major_names: list[str] | None,
) -> float:
    score = float(item.get("score", item.get("rerank_score", 0.5)))
    meta = item.get("metadata") or {}
    content = item.get("content") or ""

    # 1. Doc type priority
    dt = meta.get("doc_type", "")
    priority = DOC_TYPE_PRIORITY.get(dt, 3)
    score += priority * 0.01

    # 2. School name match
    sname = meta.get("school_name", "")
    if school_names and sname:
        for sn in school_names:
            if sn in sname or sname in sn:
                score += 0.05
                break

    # 3. Major name match
    mname = meta.get("major_name", "")
    if major_names and mname:
        for mn in major_names:
            if mn in mname or mname in mn:
                score += 0.05
                break

    # 4. Content length sufficiency (>= 150 chars considered good)
    if len(content) >= 150:
        score += 0.02
    elif len(content) < 30:
        score -= 0.05

    # 5. source_url presence bonus
    if meta.get("source_url"):
        score += 0.02
    else:
        score -= 0.03

    # 6. Intent-specific bonus
    if intent == "admission_policy" and dt == "admission_policy_clause":
        score += 0.03
    elif intent == "school_profile" and dt == "school_profile":
        score += 0.03
    elif intent in ("major_profile", "major_group_risk") and dt in ("major_general_profile", "major_analysis"):
        score += 0.03

    return score

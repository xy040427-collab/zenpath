"""
Query Rewriter for Chat — expands short/vague queries using session context.
"""
from __future__ import annotations

from typing import Any

# Pronouns and vague references that need rewriting
_VAGUE_PATTERNS = [
    ("这个学校", "school"),
    ("这所学校", "school"),
    ("该校", "school"),
    ("这个专业", "major"),
    ("这个专业组", "major_group"),
    ("这个方案", "recommendation"),
    ("会不会被调剂", "major_group_risk"),
    ("怎么样", "school"),
    ("好不好", "school"),
    ("适合我吗", "school_compare"),
    ("能上吗", "admission_chance"),
    ("稳吗", "admission_chance"),
]


def rewrite_query(
    query: str,
    session_context: dict[str, Any] | None = None,
    last_school: str = "",
    last_major_group: str = "",
    user_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rewrite a user query using session context.

    Returns {original_query, rewritten_query, entities: {school_names, major_names, ...}}
    """
    rewritten = query.strip()
    entities: dict[str, list[str]] = {
        "school_names": [],
        "major_names": [],
    }

    if session_context:
        entities["province"] = session_context.get("province", "")
        entities["subject_type"] = session_context.get("subject_type", "")

    # Resolve vague references
    for pattern, ref_type in _VAGUE_PATTERNS:
        if pattern in rewritten:
            if ref_type == "school" and last_school:
                rewritten = rewritten.replace(pattern, last_school)
                entities["school_names"].append(last_school)
            elif ref_type in ("major", "major_group", "major_group_risk") and last_major_group:
                rewritten = rewritten.replace(pattern, last_major_group)
                entities["major_names"].append(last_major_group)
            break

    # If still vague, prepend context
    if rewritten == query.strip() and last_school:
        rewritten = f"{last_school} {rewritten}"
        entities["school_names"].append(last_school)

    # Add user context for search enrichment
    if user_context:
        province = user_context.get("province", "")
        score = user_context.get("score", 0)
        rank = user_context.get("rank", 0)
        if province and "省" not in rewritten and province not in rewritten:
            # Don't force province into query if not relevant
            pass

    return {
        "original_query": query.strip(),
        "rewritten_query": rewritten,
        "entities": entities,
    }

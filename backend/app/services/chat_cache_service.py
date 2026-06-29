"""
Chat cache service — wraps chat_session_service cache functions with key generation.
"""
from __future__ import annotations

import hashlib
from typing import Any

from app.services.chat_session_service import get_cached_response, set_cached_response


def cache_key(
    normalized_query: str,
    intent: str = "",
    user_context_hash: str = "",
    recommendation_context_hash: str = "",
    rag_version: str = "v2",
) -> str:
    """Generate a deterministic cache key."""
    raw = f"{normalized_query}|{intent}|{user_context_hash}|{recommendation_context_hash}|{rag_version}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def user_context_hash(user_context: dict[str, Any] | None) -> str:
    if not user_context:
        return "anon"
    parts = [
        str(user_context.get("province", "")),
        str(user_context.get("subject_type", "")),
        str(user_context.get("score", 0)),
        str(user_context.get("rank", 0)),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def check_cache(
    query: str,
    intent: str = "",
    user_context: dict[str, Any] | None = None,
) -> dict | None:
    """Check if a cached response exists for this query + context."""
    key = cache_key(
        normalized_query=query.strip().lower(),
        intent=intent,
        user_context_hash=user_context_hash(user_context),
    )
    return get_cached_response(key)


def save_cache(
    query: str,
    answer: str,
    intent: str = "",
    user_context: dict[str, Any] | None = None,
    sources: list[dict] | None = None,
    ttl_hours: int = 168,  # 7 days default
) -> None:
    """Save a response to cache."""
    key = cache_key(
        normalized_query=query.strip().lower(),
        intent=intent,
        user_context_hash=user_context_hash(user_context),
    )
    set_cached_response(
        cache_key=key,
        normalized_query=query.strip().lower(),
        answer=answer,
        context_hash=user_context_hash(user_context),
        sources=sources,
        intent=intent,
        ttl_hours=ttl_hours,
    )

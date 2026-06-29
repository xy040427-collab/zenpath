"""
CHSI School Detail API — school detail pages powered by CHSI RAG + DeepSeek AI.

GET  /api/chsi/school/{school_name}     → get or generate school detail
GET  /api/chsi/school/{school_name}/status → check cache status (lightweight)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.school_detail_generator import generate_school_detail, _read_cache

router = APIRouter(prefix="/api/chsi/school", tags=["CHSI School Detail"])


@router.get("/{school_name}")
async def get_school_detail(school_name: str) -> dict[str, Any]:
    """Get school detail. Generates via AI on first access, serves from cache after."""
    try:
        result = await generate_school_detail(school_name)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate school detail: {str(e)}")


@router.get("/{school_name}/status")
async def get_school_detail_status(school_name: str) -> dict[str, Any]:
    """Check if school detail is cached (lightweight, no AI call)."""
    cached = _read_cache(school_name)
    return {
        "success": True,
        "school_name": school_name,
        "cached": cached is not None,
    }

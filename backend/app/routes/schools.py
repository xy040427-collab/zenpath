"""
Schools API — 863 universities from the Urongda dataset.

Endpoints:
  GET  /api/v1/schools        — list / search / filter schools
  GET  /api/v1/schools/meta   — filter metadata (provinces, levels, types)
  GET  /api/v1/schools/{slug} — single school detail
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import School

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Schools"])


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def school_to_dict(s: School) -> dict:
    """Serialize a School ORM object into the standard API format."""
    return {
        "id": s.id,
        "slug": s.slug,
        "name": s.name,
        "province": s.province,
        "city": s.city,
        "type": s.type,
        "level": s.level,
        "ranking": s.ranking,
        "tags": s.tags or [],
        "description": s.description or "",
        "website": s.website or "",
        "logo_slug": s.logo_slug or s.slug,
    }


# ──────────────────────────────────────────────
# GET /api/v1/schools — list / search / filter
# ──────────────────────────────────────────────

@router.get("/schools")
async def list_schools(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Build query
    base = select(School)

    conditions = []
    if search:
        like = f"%{search}%"
        conditions.append(
            or_(
                School.name.ilike(like),
                School.province.ilike(like),
            )
        )
    if level:
        conditions.append(School.level == level)
    if type:
        conditions.append(School.type == type)
    if province:
        conditions.append(School.province == province)

    if conditions:
        base = base.where(*conditions)

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    # Fetch page — sort by ranking ASC
    offset = (page - 1) * page_size
    q = base.order_by(School.ranking.asc()).offset(offset).limit(page_size)
    result = await db.execute(q)
    schools = result.scalars().all()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "data": [school_to_dict(s) for s in schools],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ──────────────────────────────────────────────
# GET /api/v1/schools/meta — filter metadata
# ──────────────────────────────────────────────

@router.get("/schools/meta")
async def schools_meta(db: AsyncSession = Depends(get_db)):
    # Total count
    total_result = await db.execute(select(func.count()).select_from(School))
    total = total_result.scalar_one()

    # Distinct provinces with counts
    prov_result = await db.execute(
        select(School.province, func.count(School.id).label("cnt"))
        .group_by(School.province)
        .order_by(School.province.asc())
    )
    provinces = []
    province_counts = {}
    for row in prov_result.all():
        provinces.append(row[0])
        province_counts[row[0]] = row[1]

    # Distinct levels with counts
    lvl_result = await db.execute(
        select(School.level, func.count(School.id).label("cnt"))
        .group_by(School.level)
        .order_by(School.level.asc())
    )
    levels = []
    level_counts = {}
    for row in lvl_result.all():
        levels.append(row[0])
        level_counts[row[0]] = row[1]

    # Distinct types
    typ_result = await db.execute(
        select(School.type).distinct().order_by(School.type.asc())
    )
    types = [row[0] for row in typ_result.all()]

    return {
        "total": total,
        "provinces": provinces,
        "province_counts": province_counts,
        "levels": levels,
        "level_counts": level_counts,
        "types": types,
    }


# ──────────────────────────────────────────────
# GET /api/v1/schools/{slug} — single school
# ──────────────────────────────────────────────

@router.get("/schools/{slug}")
async def get_school(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.slug == slug))
    school = result.scalar_one_or_none()
    if school is None:
        raise HTTPException(status_code=404, detail=f"School not found: {slug}")
    return {"data": school_to_dict(school)}

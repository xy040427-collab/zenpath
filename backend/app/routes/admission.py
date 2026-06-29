import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/admission-lines", tags=["Admission"])

# Mock admission data for seeding
MOCK_ADMISSION_DATA = [
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "华南理工大学", "batch": "普通本科批", "min_score": 620, "min_rank": 15200, "plan_count": 260},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "暨南大学", "batch": "普通本科批", "min_score": 600, "min_rank": 21000, "plan_count": 180},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "华南师范大学", "batch": "普通本科批", "min_score": 582, "min_rank": 28000, "plan_count": 200},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "深圳大学", "batch": "普通本科批", "min_score": 575, "min_rank": 32000, "plan_count": 320},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "广东工业大学", "batch": "普通本科批", "min_score": 548, "min_rank": 46000, "plan_count": 450},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "南方医科大学", "batch": "普通本科批", "min_score": 565, "min_rank": 37000, "plan_count": 150},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "广州大学", "batch": "普通本科批", "min_score": 540, "min_rank": 51000, "plan_count": 280},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "广东外语外贸大学", "batch": "普通本科批", "min_score": 555, "min_rank": 42000, "plan_count": 190},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "汕头大学", "batch": "普通本科批", "min_score": 550, "min_rank": 45000, "plan_count": 120},
    {"year": 2024, "province": "广东省", "subject_type": "physics", "university_name": "东莞理工学院", "batch": "普通本科批", "min_score": 518, "min_rank": 62000, "plan_count": 200},
    {"year": 2024, "province": "广东省", "subject_type": "history", "university_name": "华南理工大学", "batch": "普通本科批", "min_score": 605, "min_rank": 3800, "plan_count": 80},
    {"year": 2024, "province": "广东省", "subject_type": "history", "university_name": "暨南大学", "batch": "普通本科批", "min_score": 590, "min_rank": 5200, "plan_count": 120},
    {"year": 2024, "province": "广东省", "subject_type": "history", "university_name": "华南师范大学", "batch": "普通本科批", "min_score": 575, "min_rank": 7200, "plan_count": 160},
    {"year": 2024, "province": "广东省", "subject_type": "history", "university_name": "深圳大学", "batch": "普通本科批", "min_score": 568, "min_rank": 8500, "plan_count": 150},
    {"year": 2024, "province": "广东省", "subject_type": "history", "university_name": "广东外语外贸大学", "batch": "普通本科批", "min_score": 550, "min_rank": 11000, "plan_count": 130},
    {"year": 2023, "province": "广东省", "subject_type": "physics", "university_name": "华南理工大学", "batch": "普通本科批", "min_score": 615, "min_rank": 14800, "plan_count": 260},
    {"year": 2023, "province": "广东省", "subject_type": "physics", "university_name": "暨南大学", "batch": "普通本科批", "min_score": 595, "min_rank": 20500, "plan_count": 180},
    {"year": 2023, "province": "广东省", "subject_type": "physics", "university_name": "华南师范大学", "batch": "普通本科批", "min_score": 578, "min_rank": 27500, "plan_count": 200},
    {"year": 2023, "province": "广东省", "subject_type": "physics", "university_name": "深圳大学", "batch": "普通本科批", "min_score": 570, "min_rank": 31500, "plan_count": 320},
    {"year": 2023, "province": "广东省", "subject_type": "physics", "university_name": "广东工业大学", "batch": "普通本科批", "min_score": 542, "min_rank": 45500, "plan_count": 450},
    {"year": 2025, "province": "广东省", "subject_type": "physics", "university_name": "华南理工大学", "batch": "普通本科批", "min_score": 625, "min_rank": 14900, "plan_count": 270},
    {"year": 2025, "province": "广东省", "subject_type": "physics", "university_name": "深圳大学", "batch": "普通本科批", "min_score": 580, "min_rank": 31000, "plan_count": 330},
    {"year": 2025, "province": "广东省", "subject_type": "physics", "university_name": "广东工业大学", "batch": "普通本科批", "min_score": 552, "min_rank": 45000, "plan_count": 460},
]


@router.get("/")
async def query_admission_lines(
    province: str = Query(None, description="省份"),
    year: int = Query(None, description="年份"),
    university: str = Query(None, description="院校名称"),
    subject_type: str = Query(None, description="选科类型 (physics/history)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(AdmissionLine)

    if province:
        query = query.where(AdmissionLine.province == province)
    if year:
        query = query.where(AdmissionLine.year == year)
    if university:
        query = query.where(AdmissionLine.university_name.ilike(f"%{university}%"))
    if subject_type:
        query = query.where(AdmissionLine.subject_type == subject_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(AdmissionLine.min_rank.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    lines = result.scalars().all()

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "items": [
                {
                    "id": line.id,
                    "year": line.year,
                    "province": line.province,
                    "subject_type": line.subject_type,
                    "university_name": line.university_name,
                    "batch": line.batch,
                    "min_score": line.min_score,
                    "min_rank": line.min_rank,
                    "plan_count": line.plan_count,
                }
                for line in lines
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/seed")
async def seed_admission_data(
    db: AsyncSession = Depends(get_db),
):
    """Seed mock admission data into the database."""
    # Check if data already exists
    existing = await db.execute(select(func.count()).select_from(AdmissionLine))
    count = existing.scalar() or 0
    if count > 0:
        return {
            "success": True,
            "code": "OK",
            "message": f"admission data already exists ({count} records), skipping seed",
            "data": {"records_before": count, "records_added": 0},
        }

    inserted = 0
    for item in MOCK_ADMISSION_DATA:
        line = AdmissionLine(
            year=item["year"],
            province=item["province"],
            subject_type=item["subject_type"],
            university_name=item["university_name"],
            batch=item.get("batch", "普通本科批"),
            min_score=item["min_score"],
            min_rank=item["min_rank"],
            plan_count=item.get("plan_count", 0),
            is_published=True,
        )
        db.add(line)
        inserted += 1

    await db.commit()

    return {
        "success": True,
        "code": "OK",
        "message": f"seeded {inserted} admission records",
        "data": {
            "records_before": 0,
            "records_added": inserted,
        },
    }

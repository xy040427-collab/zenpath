"""
推荐路由 — 冲稳保计算、预览、完整推荐

路由结构：
  POST /api/v1/recommendations/calculate   — 直接计算（新，前端推荐页使用）
  POST /api/v1/recommendations/preview     — 预览（基于已有 application，3条样本）
  POST /api/v1/recommendations/full        — 完整推荐（需已付款）
  GET  /api/v1/recommendations/{rec_id}    — 读取已保存的推荐结果
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *
from app.services.recommendation_service import calculate_recommendations

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/recommendations", tags=["Recommendations"])


# ────────────────────────────────────────────────
# Request / Response schemas
# ────────────────────────────────────────────────

class CalculateRequest(BaseModel):
    """直接计算冲稳保（无需 application_id）"""
    score: int = Field(..., ge=0, le=750, description="高考总分")
    rank: int = Field(..., ge=1, description="全省位次")
    province: str = Field(..., description="省份")
    subject_type: str = Field(default="physics", description="科类: physics/history")
    batch: str = "普通本科批"
    page_size: int = 50


class PreviewRequestPydantic(BaseModel):
    application_id: str
    page_size: int = 3


class FullRequestPydantic(BaseModel):
    application_id: str
    plan_code: str


# ────────────────────────────────────────────────
# POST /calculate — 直接计算（新端点）
# ────────────────────────────────────────────────

@router.post("/calculate")
async def direct_calculate(
    body: CalculateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    直接根据分数/位次/省份/科类计算冲稳保推荐。
    无需先创建 application，适用于前端推荐页快速展示。
    """
    result = await calculate_recommendations(
        score=body.score,
        rank=body.rank,
        province=body.province,
        subject_type=body.subject_type,
        db=db,
        batch=body.batch,
        page_size=body.page_size,
    )

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "id": str(uuid.uuid4().hex[:24]),
            **result,
        },
    }


# ────────────────────────────────────────────────
# POST /preview — 预览推荐（基于 application）
# ────────────────────────────────────────────────

@router.post("/preview")
async def generate_preview(
    body: PreviewRequestPydantic,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == body.application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    full_result = await calculate_recommendations(
        score=application.score,
        rank=application.rank,
        province=application.province,
        subject_type=application.subject_type,
        db=db,
        page_size=body.page_size or 3,
    )

    sample = (full_result["rush"][:1] +
              full_result["stable"][:1] +
              full_result["safe"][:1])

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "preview_id": str(uuid.uuid4().hex[:24]),
            "summary": {
                **full_result["summary"],
                "total_candidates": len(full_result["rush"]) + len(full_result["stable"]) + len(full_result["safe"]),
            },
            "sample_recommendations": sample,
            "upgrade_suggestion": {
                "show_upgrade": True,
                "message": "查看完整推荐结果请升级至付费版本",
                "full_count": (
                    len(full_result["rush"]) +
                    len(full_result["stable"]) +
                    len(full_result["safe"])
                ),
                "plans": ["basic", "advanced", "premium"],
            },
        },
    }


# ────────────────────────────────────────────────
# POST /full — 完整推荐（需已付款）
# ────────────────────────────────────────────────

@router.post("/full")
async def generate_full_recommendations(
    body: FullRequestPydantic,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == body.application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify plan exists
    from app.routes.pricing import PLANS as pricing_plans

    if body.plan_code not in pricing_plans:
        raise HTTPException(status_code=400, detail="Invalid plan code")

    # Check payment
    order_result = await db.execute(
        select(Order).where(
            Order.application_id == body.application_id,
            Order.plan_code == body.plan_code,
            Order.status == "paid",
        )
    )
    existing_order = order_result.scalar_one_or_none()
    if not existing_order:
        raise HTTPException(
            status_code=402,
            detail="Payment required. Please create and pay for an order first.",
        )

    full_result = await calculate_recommendations(
        score=application.score,
        rank=application.rank,
        province=application.province,
        subject_type=application.subject_type,
        db=db,
        page_size=100,
    )

    tier_distribution = {
        "冲刺": len(full_result["rush"]),
        "稳妥": len(full_result["stable"]),
        "保底": len(full_result["safe"]),
    }

    all_recs = full_result["rush"] + full_result["stable"] + full_result["safe"]

    # Save to DB
    rec_result = RecommendationResult(
        application_id=body.application_id,
        strategy_summary=full_result["summary"].get("strategy", ""),
        summary_data=full_result["summary"],
        recommendations=all_recs,
        not_recommended=full_result["not_recommended"],
        tier_distribution=tier_distribution,
    )
    db.add(rec_result)
    await db.commit()
    await db.refresh(rec_result)

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "id": rec_result.id,
            "strategy_summary": rec_result.strategy_summary,
            "summary_data": rec_result.summary_data,
            "recommendations": rec_result.recommendations,
            "not_recommended": rec_result.not_recommended,
            "tier_distribution": rec_result.tier_distribution,
            "created_at": rec_result.created_at.isoformat(),
        },
    }


# ────────────────────────────────────────────────
# GET /{rec_id} — 读取已保存的推荐
# ────────────────────────────────────────────────

@router.get("/{rec_id}")
async def get_recommendation(
    rec_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RecommendationResult).where(RecommendationResult.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation result not found")

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "id": rec.id,
            "application_id": rec.application_id,
            "strategy_summary": rec.strategy_summary,
            "summary_data": rec.summary_data,
            "recommendations": rec.recommendations,
            "not_recommended": rec.not_recommended,
            "tier_distribution": rec.tier_distribution,
            "created_at": rec.created_at.isoformat(),
        },
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@router.post("")
async def create_application(
    body: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == body.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    application = Application(session_id=body.session_id)
    db.add(application)
    await db.commit()
    await db.refresh(application)

    return {
        "success": True,
        "code": "OK",
        "message": "application created",
        "data": {
            "application_id": application.id,
            "session_id": application.session_id,
            "status": application.status,
        },
    }


@router.post("/{app_id}/submit")
async def submit_application(
    app_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check required fields are filled
    missing = []
    if not application.province:
        missing.append("province")
    if not application.year:
        missing.append("year")
    if not application.subject_type:
        missing.append("subject_type")
    if application.score is None:
        missing.append("score")
    if application.rank is None:
        missing.append("rank")
    if not application.priority:
        missing.append("priority")
    if not application.risk_preference:
        missing.append("risk_preference")
    if not application.school_vs_major:
        missing.append("school_vs_major")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Required fields missing: {', '.join(missing)}",
        )

    application.status = "completed"
    await db.commit()
    await db.refresh(application)

    return {
        "success": True,
        "code": "OK",
        "message": "application submitted for preview",
        "data": {
            "application_id": application.id,
            "status": application.status,
        },
    }


@router.put("/{app_id}/exam")
async def save_exam_info(
    app_id: str,
    body: ExamInfo,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.province = body.province
    application.year = body.year
    application.subject_type = body.subject_type
    application.score = body.score
    application.rank = body.rank
    application.gender = body.gender
    application.single_subject_scores = (
        body.single_subject_scores if body.single_subject_scores else None
    )
    application.target_batch = body.target_batch

    await db.commit()
    await db.refresh(application)

    return {
        "success": True,
        "code": "OK",
        "message": "exam info saved",
        "data": {
            "application_id": application.id,
            "province": application.province,
            "year": application.year,
            "subject_type": application.subject_type,
            "score": application.score,
            "rank": application.rank,
            "target_batch": application.target_batch,
        },
    }


@router.put("/{app_id}/preferences")
async def save_preferences(
    app_id: str,
    body: Preferences,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.priority = body.priority
    application.risk_preference = body.risk_preference
    application.preferred_cities = body.preferred_cities if body.preferred_cities else None
    application.accept_private_university = body.accept_private_university
    application.accept_sino_foreign = body.accept_sino_foreign
    application.accept_high_tuition = body.accept_high_tuition
    application.max_tuition_per_year = body.max_tuition_per_year
    application.school_vs_major = body.school_vs_major
    application.accept_major_adjustment = body.accept_major_adjustment
    application.preferred_major_categories = (
        body.preferred_major_categories if body.preferred_major_categories else None
    )

    await db.commit()
    await db.refresh(application)

    return {
        "success": True,
        "code": "OK",
        "message": "preferences saved",
        "data": {
            "application_id": application.id,
            "priority": application.priority,
            "risk_preference": application.risk_preference,
            "preferred_cities": application.preferred_cities,
            "school_vs_major": application.school_vs_major,
        },
    }


@router.put("/{app_id}/profile")
async def save_profile(
    app_id: str,
    body: ProfileInfo,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if body.gender is not None:
        application.gender = body.gender
    application.interests = body.interests if body.interests else None
    application.strengths = body.strengths if body.strengths else None
    application.career_goals = body.career_goals if body.career_goals else None
    application.family_budget = body.family_budget

    await db.commit()
    await db.refresh(application)

    return {
        "success": True,
        "code": "OK",
        "message": "profile saved",
        "data": {
            "application_id": application.id,
            "interests": application.interests,
            "strengths": application.strengths,
            "career_goals": application.career_goals,
        },
    }


@router.get("/{app_id}")
async def get_application_summary(
    app_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Application).where(Application.id == app_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "application_id": application.id,
            "session_id": application.session_id,
            "status": application.status,
            "exam": {
                "province": application.province,
                "year": application.year,
                "subject_type": application.subject_type,
                "score": application.score,
                "rank": application.rank,
                "gender": application.gender,
                "single_subject_scores": application.single_subject_scores,
                "target_batch": application.target_batch,
            },
            "preferences": {
                "priority": application.priority,
                "risk_preference": application.risk_preference,
                "preferred_cities": application.preferred_cities,
                "accept_private_university": application.accept_private_university,
                "accept_sino_foreign": application.accept_sino_foreign,
                "accept_high_tuition": application.accept_high_tuition,
                "max_tuition_per_year": application.max_tuition_per_year,
                "school_vs_major": application.school_vs_major,
                "accept_major_adjustment": application.accept_major_adjustment,
                "preferred_major_categories": application.preferred_major_categories,
            },
            "profile": {
                "interests": application.interests,
                "strengths": application.strengths,
                "career_goals": application.career_goals,
                "family_budget": application.family_budget,
            },
            "created_at": (
                application.created_at.isoformat() if application.created_at else None
            ),
            "updated_at": (
                application.updated_at.isoformat() if application.updated_at else None
            ),
        },
    }

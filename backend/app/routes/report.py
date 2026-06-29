"""
报告路由 — 生成、查询、导出、分享志愿报告

路由结构：
  POST /api/v1/reports/generate       — 生成报告（旧接口，保留兼容）
  POST /api/v1/reports                — 创建报告（文档 7.1）
  GET  /api/v1/reports/{report_id}    — 获取完整报告
  GET  /api/v1/reports/{id}/summary   — 网页摘要（文档 7.2）
  GET  /api/v1/reports/{id}/pdf-data  — PDF 完整数据（文档 7.4）
  GET  /api/v1/reports/{report_id}/export — 导出报告
  POST /api/v1/reports/{report_id}/share  — 分享报告
  POST /api/v1/reports/{id}/pdf/jobs  — 创建 PDF 任务（文档 7.5）
  GET  /api/v1/reports/pdf/jobs/{id}  — 查询 PDF 任务（文档 7.6）
  GET  /api/v1/reports/{id}/pdf/download — 下载 PDF（文档 7.7）
"""

import uuid
import logging
from datetime import datetime

import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *
from app.services.report_service import generate_report_data
from app.services.recommendation_service import calculate_recommendations
from app.services.report_builder import build_report_json
from app.services.report_permission_service import (
    build_summary,
    build_pdf_data,
    build_response_with_permission,
    get_permission,
)
from app.services.report_pdf_service import (
    create_pdf_job,
    get_pdf_job_status,
    get_download_info,
    run_pdf_generation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


# ═══════════════════════════════════════════════════════════════
# POST /generate — 生成报告（旧接口）
# ═══════════════════════════════════════════════════════════════

@router.post("/generate")
async def generate_report(
    body: ReportGenerate,
    db: AsyncSession = Depends(get_db),
):
    # 1. 验证 application 存在
    app_result = await db.execute(
        select(Application).where(Application.id == body.application_id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # 2. 验证推荐结果存在（或者即时计算）
    if body.recommendation_result_id:
        rec_result = await db.execute(
            select(RecommendationResult).where(
                RecommendationResult.id == body.recommendation_result_id
            )
        )
        rec = rec_result.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation result not found")
        raw_recommendations = {
            "summary": rec.summary_data or {},
            "rush": [r for r in (rec.recommendations or []) if r.get("tier") == "冲刺"],
            "stable": [r for r in (rec.recommendations or []) if r.get("tier") == "稳妥"],
            "safe": [r for r in (rec.recommendations or []) if r.get("tier") == "保底"],
            "not_recommended": rec.not_recommended or [],
        }
    else:
        raw_recommendations = await calculate_recommendations(
            score=application.score,
            rank=application.rank,
            province=application.province,
            subject_type=application.subject_type,
            db=db,
            page_size=100,
        )

    # 3. 验证 plan_code
    from app.routes.pricing import PLANS as pricing_plans
    if body.plan_code not in pricing_plans:
        raise HTTPException(status_code=400, detail="Invalid plan code")

    # 4. 检查是否已有报告
    existing_result = await db.execute(
        select(Report).where(Report.application_id == body.application_id)
    )
    existing_report = existing_result.scalar_one_or_none()
    if existing_report:
        return {
            "success": True,
            "code": "OK",
            "message": "report already exists",
            "data": {
                "report_job_id": existing_report.id,
                "status": existing_report.status,
            },
        }

    # 5. 生成报告数据（使用新 builder）
    report_json = build_report_json(
        raw_recommendations,
        application,
        plan_type=body.plan_code,
    )
    legacy_data = generate_report_data(raw_recommendations, body.application_id)

    # 6. 保存到数据库
    report = Report(
        application_id=body.application_id,
        recommendation_result_id=body.recommendation_result_id or "",
        plan_code=body.plan_code,
        status="completed",
        province=application.province,
        subject_type=application.subject_type,
        score=application.score,
        rank=application.rank,
        title=f"{application.province}{application.subject_type}志愿填报分析报告",
        report_json=report_json,
        report_data=legacy_data,
        completed_at=datetime.utcnow(),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "success": True,
        "code": "OK",
        "message": "report generated",
        "data": {
            "report_job_id": report.id,
            "status": report.status,
        },
    }


# ═══════════════════════════════════════════════════════════════
# POST / — 创建报告（文档 7.1）
# ═══════════════════════════════════════════════════════════════

@router.post("")
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a report from a recommendation_id."""
    # 1. 校验 recommendation_id
    rec_result = await db.execute(
        select(RecommendationResult).where(
            RecommendationResult.id == body.recommendation_id
        )
    )
    rec = rec_result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # 2. 获取关联的 application
    app_result = await db.execute(
        select(Application).where(Application.id == rec.application_id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    plan_type = body.report_level

    # 3. 构建推荐数据
    raw_recommendations = {
        "summary": rec.summary_data or {},
        "rush": [r for r in (rec.recommendations or []) if r.get("tier") == "冲刺"],
        "stable": [r for r in (rec.recommendations or []) if r.get("tier") == "稳妥"],
        "safe": [r for r in (rec.recommendations or []) if r.get("tier") == "保底"],
        "not_recommended": rec.not_recommended or [],
    }

    # 4. 构建 Report JSON
    report_json = build_report_json(
        raw_recommendations,
        application,
        plan_type=plan_type,
    )

    # 5. 写入 reports 表
    report = Report(
        application_id=application.id,
        recommendation_result_id=body.recommendation_id,
        plan_code=plan_type,
        status="ready",
        province=application.province,
        subject_type=application.subject_type,
        score=application.score,
        rank=application.rank,
        title=f"{application.province}{application.subject_type}志愿填报分析报告",
        report_json=report_json,
        completed_at=datetime.utcnow(),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # 6. 返回 report_id
    return {
        "success": True,
        "report_id": report.id,
        "status": report.status,
    }


# ═══════════════════════════════════════════════════════════════
# GET / — 列出所有报告
# ═══════════════════════════════════════════════════════════════

@router.get("")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all reports, newest first."""
    result = await db.execute(
        select(Report)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    reports = result.scalars().all()

    items = []
    for r in reports:
        items.append({
            "report_id": r.id,
            "title": r.title or f"{r.province}{r.subject_type}志愿填报分析报告",
            "province": r.province,
            "subject_type": r.subject_type,
            "score": r.score,
            "rank": r.rank,
            "plan_code": r.plan_code,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })

    return {
        "success": True,
        "total": len(items),
        "reports": items,
    }


# ═══════════════════════════════════════════════════════════════
# GET /{report_id} — 获取完整报告
# ═══════════════════════════════════════════════════════════════

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Use permission service to build response
    report_json = report.report_json or report.report_data or {}
    plan_type = report.plan_code or "free"
    response = build_response_with_permission(report_json, plan_type)
    response["success"] = True
    response["report_id"] = report.id
    return response


# ═══════════════════════════════════════════════════════════════
# GET /{id}/summary — 网页摘要（文档 7.2）
# ═══════════════════════════════════════════════════════════════

@router.get("/{report_id}/summary")
async def get_report_summary(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_json = report.report_json or report.report_data or {}
    plan_type = report.plan_code or "free"

    summary = build_summary(report_json, plan_type)

    return {
        "success": True,
        "report_id": report.id,
        "plan_type": plan_type,
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════
# GET /{id}/pdf-data — PDF 完整数据（文档 7.4）
# ═══════════════════════════════════════════════════════════════

@router.get("/{report_id}/pdf-data")
async def get_report_pdf_data(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_json = report.report_json or report.report_data or {}
    plan_type = report.plan_code or "free"

    pdf_data = build_pdf_data(report_json, plan_type)
    pdf_data["success"] = True

    return pdf_data


# ═══════════════════════════════════════════════════════════════
# GET /{report_id}/export — 导出报告
# ═══════════════════════════════════════════════════════════════

@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != "completed" and report.status != "ready":
        raise HTTPException(status_code=400, detail="Report is not yet completed")

    export_data = {
        "export_format": "pdf",
        "exported_at": datetime.utcnow().isoformat(),
        "report_id": report.id,
        "plan_code": report.plan_code,
        "content": report.report_json or report.report_data,
        "metadata": {
            "file_name": f"高考志愿报告_{report.id}.pdf",
            "file_size_kb": 256,
            "pages": 12,
        },
    }

    return {
        "success": True,
        "code": "OK",
        "message": "export ready",
        "data": export_data,
    }


# ═══════════════════════════════════════════════════════════════
# POST /{report_id}/share — 分享报告
# ═══════════════════════════════════════════════════════════════

@router.post("/{report_id}/share")
async def share_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    share_token = str(uuid.uuid4().hex[:16])

    return {
        "success": True,
        "code": "OK",
        "message": "share link generated",
        "data": {
            "share_token": share_token,
            "share_url": f"/shared/report/{share_token}",
            "report_id": report.id,
            "plan_code": report.plan_code,
            "created_at": datetime.utcnow().isoformat(),
        },
    }


# ═══════════════════════════════════════════════════════════════
# POST /{id}/pdf/jobs — 创建 PDF 任务（文档 7.5）
# ═══════════════════════════════════════════════════════════════

@router.post("/pdf/jobs/{job_id}")
async def query_pdf_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Must be defined BEFORE the wildcard {report_id} route."""
    pass


@router.post("/{report_id}/pdf/jobs")
async def create_report_pdf_job(
    report_id: str,
    body: PdfJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a PDF generation job and launch async rendering."""
    # Check report exists and get plan_type
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    plan_type = report.plan_code or "free"
    perm = get_permission(plan_type)

    if not perm["can_download_pdf"]:
        raise HTTPException(
            status_code=403,
            detail=f"PDF download requires basic plan or above. Current: {plan_type}",
        )

    result = await create_pdf_job(
        db,
        report_id=report_id,
        plan_type=body.pdf_type,
    )

    # If a NEW job was created (not reused), launch background generation
    if result.get("message") == "PDF job created":
        job_id = result["job_id"]
        background_tasks.add_task(run_pdf_generation, job_id, report_id)
        logger.info(f"Launched background PDF generation for job {job_id}")

    return result


# ═══════════════════════════════════════════════════════════════
# GET /pdf/jobs/{job_id} — 查询 PDF 任务（文档 7.6）
# ═══════════════════════════════════════════════════════════════

@router.get("/pdf/jobs/{job_id}")
async def get_pdf_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Query PDF job status."""
    return await get_pdf_job_status(db, job_id)


# ═══════════════════════════════════════════════════════════════
# GET /{id}/pdf/download — 下载 PDF（文档 7.7）
# ═══════════════════════════════════════════════════════════════

@router.get("/{report_id}/pdf/download")
async def download_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download the generated PDF as a real file."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    plan_type = report.plan_code or "free"
    perm = get_permission(plan_type)

    if not perm["can_download_pdf"]:
        raise HTTPException(
            status_code=403,
            detail=f"PDF download requires basic plan or above",
        )

    download_info = await get_download_info(db, report_id)
    if not download_info:
        raise HTTPException(
            status_code=404,
            detail="PDF file not yet generated. Please create a PDF job first.",
        )

    file_path = download_info["file_path"]
    file_name = download_info.get("file_name", f"择境志愿填报分析报告_{report_id}.pdf")

    # Verify file exists on disk
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file missing from disk. Please regenerate.",
        )

    # Use ASCII-safe filename for the header to avoid latin-1 encoding issues
    safe_filename = f"zenpath_report_{report_id}.pdf"

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename,
    )

"""
report_pdf_service.py — PDF 生成任务管理

Two stages:
  1. Create PDF job, mark pending, return job_id to frontend
  2. Async background task: Playwright → render PDF preview page → save real PDF

Principle:
- create_pdf_job() returns immediately with job_id (so UI shows "generating...")
- run_pdf_generation() runs in background, updates job status through its lifecycle
- Failed jobs show error_message, frontend can retry
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Report, ReportPdfJob, ReportFile
from app.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def create_pdf_job(
    db: AsyncSession,
    report_id: str,
    plan_type: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a PDF generation job. Returns immediately — actual generation is async."""

    # Verify report exists
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        return {"success": False, "message": "Report not found"}

    # Check if there's already a pending/processing job
    existing = await db.execute(
        select(ReportPdfJob).where(
            ReportPdfJob.report_id == report_id,
            ReportPdfJob.status.in_(["pending", "processing"]),
        )
    )
    existing_job = existing.scalar_one_or_none()
    if existing_job:
        return {
            "success": True,
            "job_id": existing_job.id,
            "status": existing_job.status,
            "message": "Reusing existing PDF job",
        }

    job = ReportPdfJob(
        report_id=report_id,
        user_id=user_id,
        plan_type=plan_type,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return {
        "success": True,
        "job_id": job.id,
        "status": job.status,
        "message": "PDF job created",
    }


async def run_pdf_generation(
    job_id: str,
    report_id: str,
) -> None:
    """Background task: render PDF via Playwright, update job status.

    Called from the route handler AFTER create_pdf_job() returns.
    Uses its own async DB session to avoid session conflicts.
    """

    # Late import — only the background task needs the renderer
    from app.services.report_pdf_renderer import render_pdf

    async with async_session_factory() as db:
        try:
            # 1. Mark processing
            job_result = await db.execute(
                select(ReportPdfJob).where(ReportPdfJob.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            if not job:
                logger.error(f"Job {job_id} not found in background task")
                return

            job.status = "processing"
            job.started_at = datetime.utcnow()
            await db.commit()

            # 2. Run Playwright renderer in thread pool (sync Playwright API)
            result = await asyncio.to_thread(render_pdf, report_id)

            # 3. Update job with result
            await db.refresh(job)
            job.finished_at = datetime.utcnow()

            if result["success"]:
                job.status = "completed"
                job.file_path = result["file_path"]
                job.file_url = f"/api/v1/reports/{report_id}/pdf/download"

                # Record in report_files table
                file_record = ReportFile(
                    report_id=report_id,
                    user_id=job.user_id,
                    file_type="pdf",
                    file_name=result["file_name"],
                    file_path=result["file_path"],
                    file_url=job.file_url,
                    size_bytes=(
                        __import__("os").path.getsize(result["file_path"])
                        if result["file_path"] else None
                    ),
                )
                db.add(file_record)

                logger.info(
                    f"PDF job {job_id} completed: {result['file_path']}"
                )
            else:
                job.status = "failed"
                job.error_message = result["error_message"]
                logger.error(
                    f"PDF job {job_id} failed: {result['error_message']}"
                )

            await db.commit()

        except Exception as e:
            logger.exception(f"PDF generation background task crashed for job {job_id}")
            # Try to mark as failed in a fresh session
            try:
                async with async_session_factory() as recovery_db:
                    r = await recovery_db.execute(
                        select(ReportPdfJob).where(ReportPdfJob.id == job_id)
                    )
                    failed_job = r.scalar_one_or_none()
                    if failed_job:
                        failed_job.status = "failed"
                        failed_job.error_message = f"系统错误: {str(e)[:200]}"
                        failed_job.finished_at = datetime.utcnow()
                        await recovery_db.commit()
            except Exception:
                logger.exception("Failed to mark job as failed in recovery")


async def get_pdf_job_status(
    db: AsyncSession,
    job_id: str,
) -> Dict[str, Any]:
    """Query PDF job status."""
    result = await db.execute(
        select(ReportPdfJob).where(ReportPdfJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return {"success": False, "message": "Job not found"}

    resp = {
        "success": True,
        "job_id": job.id,
        "status": job.status,
    }

    if job.status == "completed" and job.file_url:
        resp["download_url"] = job.file_url
    elif job.status == "failed":
        resp["error_message"] = job.error_message

    return resp


async def record_pdf_file(
    db: AsyncSession,
    report_id: str,
    user_id: Optional[str],
    file_path: str,
    file_name: str,
    size_bytes: Optional[int] = None,
) -> ReportFile:
    """Record a generated PDF file."""
    rf = ReportFile(
        report_id=report_id,
        user_id=user_id,
        file_type="pdf",
        file_name=file_name,
        file_path=file_path,
        file_url=f"/api/v1/reports/{report_id}/pdf/download",
        size_bytes=size_bytes,
    )
    db.add(rf)
    await db.commit()
    await db.refresh(rf)
    return rf


async def get_download_info(
    db: AsyncSession,
    report_id: str,
) -> Optional[Dict[str, Any]]:
    """Get download info for a report's PDF."""
    result = await db.execute(
        select(ReportFile).where(
            ReportFile.report_id == report_id,
            ReportFile.file_type == "pdf",
        ).order_by(ReportFile.created_at.desc())
    )
    file_record = result.scalars().first()
    if not file_record:
        return None

    return {
        "file_name": file_record.file_name,
        "file_path": file_record.file_path,
        "file_url": file_record.file_url,
        "size_bytes": file_record.size_bytes,
        "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
    }

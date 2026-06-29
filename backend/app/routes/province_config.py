"""
省份配置 API 端点

GET  /api/v1/province-config/{province}     → 返回省份配置
GET  /api/v1/province-config/list            → 返回所有省份列表（用于前端下拉）
GET  /api/v1/province-config/stats           → 各数据覆盖统计
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.province_config import (
    ALL_PROVINCE_CONFIGS, get_province_config,
    get_exam_mode, get_subject_options, get_score_max, get_year_rule,
)
from app.core.database import get_db

router = APIRouter(prefix="/api/v1/province-config", tags=["province-config"])


@router.get("/list")
async def list_provinces():
    """返回所有省份简要列表"""
    provinces = []
    for code, cfg in ALL_PROVINCE_CONFIGS.items():
        provinces.append({
            "code": code,
            "name": cfg.name,
            "exam_mode": cfg.exam_mode,
            "score_max": cfg.score_max,
            "admission_unit": cfg.admission_unit,
            "subject_options": cfg.subject_options,
            "hint_score": cfg.hint_score,
            "hint_subject": cfg.hint_subject,
        })
    return {"provinces": sorted(provinces, key=lambda x: x["code"])}


@router.get("/{province}")
async def get_config(province: str):
    """获取单个省份的完整配置"""
    cfg = get_province_config(province)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"未知省份: {province}")

    return {
        "code": cfg.code,
        "name": cfg.name,
        "exam_mode": cfg.exam_mode,
        "admission_unit": cfg.admission_unit,
        "score_max": cfg.score_max,
        "score_min": cfg.score_min,
        "subject_options": cfg.subject_options,
        "subject_options_secondary": cfg.subject_options_secondary,
        "subject_type_default": cfg.subject_type_default,
        "batches": cfg.batches,
        "reform_year": cfg.reform_year,
        "hint_score": cfg.hint_score,
        "hint_subject": cfg.hint_subject,
        "hint_batch": cfg.hint_batch,
    }


@router.get("/stats/coverage")
async def get_coverage_stats(db: AsyncSession = Depends(get_db)):
    """返回各省数据覆盖统计"""
    seg_result = await db.execute(text("""
        SELECT province, COUNT(*) as cnt, MIN(year), MAX(year)
        FROM score_rank_table GROUP BY province ORDER BY cnt DESC
    """))
    seg_data = {r[0]: {"rows": r[1], "year_min": r[2], "year_max": r[3]} for r in seg_result.fetchall()}

    adm_result = await db.execute(text("""
        SELECT province, COUNT(*) as cnt, MIN(year), MAX(year)
        FROM admission_lines GROUP BY province ORDER BY cnt DESC
    """))
    adm_data = {r[0]: {"rows": r[1], "year_min": r[2], "year_max": r[3]} for r in adm_result.fetchall()}

    provinces = []
    for code, cfg in ALL_PROVINCE_CONFIGS.items():
        s = seg_data.get(code, {})
        a = adm_data.get(code, {})
        provinces.append({
            "code": code,
            "name": cfg.name,
            "exam_mode": cfg.exam_mode,
            "score_segments_rows": s.get("rows", 0),
            "score_segments_years": f"{s.get('year_min','')}-{s.get('year_max','')}" if s.get("rows") else "—",
            "admission_lines_rows": a.get("rows", 0),
            "admission_lines_years": f"{a.get('year_min','')}-{a.get('year_max','')}" if a.get("rows") else "—",
        })

    return {"provinces": provinces, "total_provinces": len(provinces)}

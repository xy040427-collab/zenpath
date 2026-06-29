from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/pricing", tags=["Pricing"])

# Pricing plans
PLANS = {
    "free": {
        "plan_code": "free",
        "name": "免费版",
        "price": 0,
        "original_price": 0,
        "billing_cycle": "free",
        "duration_days": None,
        "features": [
            "AI 院校智能匹配（限5所）",
            "基础录取机会评估",
            "基础院校数据查询",
            "志愿填报基础指南",
            "志愿表预览（限10个志愿）",
        ],
        "is_popular": False,
        "sort_order": 1,
    },
    "basic": {
        "plan_code": "basic",
        "name": "基础版",
        "price": 49,
        "original_price": 99,
        "billing_cycle": "year",
        "duration_days": 365,
        "features": [
            "AI 院校智能匹配（不限量）",
            "录取机会评估",
            "冲稳保策略分析",
            "完整志愿表生成",
            "基础个性化分析报告",
            "支持导出 PDF / Excel",
            "会员期内可保存 3 套方案",
            "365 天有效",
        ],
        "is_popular": False,
        "sort_order": 2,
    },
    "advanced": {
        "plan_code": "advanced",
        "name": "进阶版",
        "price": 129,
        "original_price": 199,
        "billing_cycle": "year",
        "duration_days": 365,
        "features": [
            "全部基础版功能",
            "专业倾向测评",
            "专业组内专业明细分析",
            "目标专业命中度分析",
            "调剂风险评估",
            "专业就业前景解读",
            "AI 深度答疑",
            "多方案对比优化",
            "365 天有效",
        ],
        "is_popular": False,
        "sort_order": 3,
    },
    "premium": {
        "plan_code": "premium",
        "name": "尊享版",
        "price": 399,
        "original_price": 599,
        "billing_cycle": "year",
        "duration_days": 365,
        "features": [
            "全部进阶版功能",
            "人工志愿方案复核 1 次",
            "一对一咨询 30 分钟",
            "志愿方案深度优化",
            "填报前最终检查 1 次",
            "录取结果跟踪提醒",
            "大学入学建议",
            "365 天有效",
        ],
        "is_popular": True,
        "sort_order": 4,
        "note": "人工复核服务即将开放，当前可先选择进阶版生成深度方案。",
    },
}


@router.get("/plans")
async def get_pricing_plans():
    plans_list = sorted(PLANS.values(), key=lambda p: p["sort_order"])
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {"plans": plans_list},
    }


@router.get("/plans/{plan_code}")
async def get_single_plan(plan_code: str):
    plan = PLANS.get(plan_code)
    if not plan:
        raise HTTPException(status_code=404, detail="Pricing plan not found")
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": plan,
    }

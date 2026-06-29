"""
会员 API：查询/购买/状态
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.membership_service import (
    get_user_membership,
    get_user_entitlements,
    create_order,
    complete_order,
    PLAN_ENTITLEMENTS,
)

router = APIRouter(prefix="/api/v1/membership", tags=["membership"])


class CreateOrderRequest(BaseModel):
    user_id: str
    plan_type: str  # free / basic / advanced / premium


class CompleteOrderRequest(BaseModel):
    order_id: int


@router.get("/entitlements")
async def get_entitlements(user_id: str = Query(...)):
    """获取用户当前权益"""
    entitlements = get_user_entitlements(user_id)
    return {"success": True, "data": entitlements}


@router.get("/status")
async def membership_status(user_id: str = Query(...)):
    """获取用户会员状态"""
    membership = get_user_membership(user_id)
    if not membership:
        return {
            "success": True,
            "data": {
                "plan": "free",
                "plan_name": "免费版",
                "is_active": True,
                "expires_at": None,
                "days_left": None,
                "entitlements": PLAN_ENTITLEMENTS["free"],
            },
        }

    from datetime import datetime

    days_left = None
    expires_at = membership.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            delta = exp - datetime.utcnow()
            days_left = max(0, delta.days)
        except (ValueError, TypeError):
            pass

    is_expired = days_left is not None and days_left <= 0

    return {
        "success": True,
        "data": {
            "plan": membership["plan_type"],
            "plan_name": {"free": "免费版", "basic": "基础版", "advanced": "进阶版", "premium": "尊享版"}.get(
                membership["plan_type"], "免费版"
            ),
            "is_active": not is_expired,
            "starts_at": membership.get("starts_at"),
            "expires_at": expires_at,
            "days_left": days_left,
            "billing_cycle": membership.get("billing_cycle", "year"),
            "entitlements": PLAN_ENTITLEMENTS.get(membership["plan_type"], PLAN_ENTITLEMENTS["free"]),
        },
    }


@router.get("/plans")
async def list_plans():
    """列出所有会员方案"""
    return {
        "success": True,
        "data": {
            "free": {
                "name": "免费版",
                "subtitle": "快速了解志愿填报方向",
                "price": 0,
                "original_price": 0,
                "billing_cycle": "free",
                "duration_days": None,
                "features": [
                    "AI 院校智能匹配：限 5 所",
                    "基础录取机会评估",
                    "基础院校数据查询",
                    "志愿填报基础指南",
                    "志愿表预览：限 10 个志愿",
                ],
            },
            "basic": {
                "name": "基础版",
                "subtitle": "生成一份完整可用的志愿方案",
                "price": 49,
                "original_price": 99,
                "billing_cycle": "year",
                "duration_days": 365,
                "features": [
                    "AI 院校智能匹配：不限量",
                    "录取机会评估",
                    "冲稳保策略分析",
                    "完整志愿表生成",
                    "基础个性化分析报告",
                    "支持导出 PDF / Excel",
                    "会员期内可保存 3 套方案",
                    "365 天有效",
                ],
            },
            "advanced": {
                "name": "进阶版",
                "subtitle": "看清专业组与调剂风险",
                "price": 129,
                "original_price": 199,
                "billing_cycle": "year",
                "duration_days": 365,
                "features": [
                    "全部基础版功能",
                    "专业组内专业明细分析",
                    "目标专业命中度分析",
                    "调剂风险评估",
                    "专业就业前景解读",
                    "多方案对比优化",
                    "AI 深度答疑",
                    "365 天有效",
                ],
            },
            "premium": {
                "name": "尊享版",
                "subtitle": "人工复核你的最终志愿方案",
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
                    "365 天有效",
                ],
                "note": "人工复核服务即将开放，当前可先选择进阶版生成深度方案。",
            },
        },
    }


@router.post("/orders")
async def create_membership_order(body: CreateOrderRequest):
    """创建会员订单"""
    plan_prices = {"free": 0, "basic": 4900, "advanced": 12900, "premium": 39900}
    plan_originals = {"free": 0, "basic": 9900, "advanced": 19900, "premium": 59900}

    if body.plan_type not in plan_prices:
        raise HTTPException(400, f"Invalid plan_type: {body.plan_type}")

    amount = plan_prices[body.plan_type]
    original = plan_originals[body.plan_type]

    result = create_order(body.user_id, body.plan_type, amount, original)
    return {"success": True, "data": result}


@router.post("/orders/{order_id}/pay")
async def pay_order(order_id: int):
    """模拟支付（开发阶段，实际应接入支付网关）"""
    result = complete_order(order_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return {"success": True, "data": result}

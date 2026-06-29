from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def _plan_price(plan_code: str) -> float:
    """Get price for a plan code. Hardcoded for MVP."""
    prices = {
        "basic": 29.9,
        "advanced": 129,
        "premium": 399,
    }
    return prices.get(plan_code, 0)


@router.post("")
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verify application exists
    app_result = await db.execute(
        select(Application).where(Application.id == body.application_id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify plan code
    price = _plan_price(body.plan_code)
    if price == 0:
        raise HTTPException(status_code=400, detail="Invalid plan code")

    # Calculate discount
    discount = 0.0

    order = Order(
        application_id=body.application_id,
        plan_code=body.plan_code,
        original_amount=price,
        discount_amount=discount,
        pay_amount=price - discount,
        coupon_code=body.coupon_code,
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    return {
        "success": True,
        "code": "OK",
        "message": "order created",
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "plan_code": order.plan_code,
            "original_amount": order.original_amount,
            "discount_amount": order.discount_amount,
            "pay_amount": order.pay_amount,
            "status": order.status,
        },
    }


@router.get("/{order_id}")
async def get_order_status(
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "application_id": order.application_id,
            "plan_code": order.plan_code,
            "original_amount": order.original_amount,
            "discount_amount": order.discount_amount,
            "pay_amount": order.pay_amount,
            "coupon_code": order.coupon_code,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        },
    }


@router.post("/{order_id}/pay")
async def simulate_payment(
    order_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "paid":
        return {
            "success": True,
            "code": "OK",
            "message": "order already paid",
            "data": {
                "order_id": order.id,
                "status": order.status,
            },
        }

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    await db.commit()
    await db.refresh(order)

    return {
        "success": True,
        "code": "OK",
        "message": "payment successful",
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        },
    }

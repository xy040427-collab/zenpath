import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import *
from app.schemas.schemas import *

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("/anonymous")
async def create_anonymous_session(
    body: SessionCreate = None,
    db: AsyncSession = Depends(get_db),
):
    if body is None:
        body = SessionCreate()
    session_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    db_session = Session(
        session_token=session_token,
        source=body.source,
        utm_source=body.utm_source,
        utm_campaign=body.utm_campaign,
        expires_at=expires_at,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "session_id": db_session.id,
            "session_token": db_session.session_token,
            "expires_at": db_session.expires_at.isoformat(),
        },
    }

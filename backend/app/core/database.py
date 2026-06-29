from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        from app.models.models import Session, Application, RecommendationResult, Order, Report, AIConversation, AIChatMessage, AdmissionLine, PricingPlan, School, ScoreRankTable, SubjectRequirement, RagChunk
        await conn.run_sync(Base.metadata.create_all)

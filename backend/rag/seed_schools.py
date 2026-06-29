"""
Seed RAG from school_info.py — import curated Nanjing school data as rag_chunks.

This bootstraps the RAG knowledge base with verified school profiles.
Subsequent auto-crawling supplements additional data (employment, majors, etc.).
"""
import asyncio
import logging
from sqlalchemy import text
from app.core.database import get_db
from app.services.school_info import get_school_info
from rag.chunker import chunk_document
from rag.indexer import index_chunks
from rag.sources import SOURCE_CONFIDENCE

logger = logging.getLogger(__name__)

SCHOOL_NAMES = list({
    "南京大学", "东南大学", "南京航空航天大学", "南京理工大学",
    "南京邮电大学", "南京信息工程大学", "南京农业大学", "南京医科大学",
    "南京中医药大学", "南京工业大学", "南京林业大学", "南京财经大学",
    "南京审计大学", "南京师范大学", "南京工程学院", "南京晓庄学院",
    "南京艺术学院", "南京体育学院", "南京工业职业技术大学",
    "河海大学", "中国药科大学", "南京大学金陵学院", "东南大学成贤学院",
    "南京理工大学紫金学院", "南京航空航天大学金城学院",
    "南京传媒学院", "南京警察学院", "三江学院",
    "南京邮电大学通达学院", "南京医科大学康达学院",
})


async def seed_school_profiles():
    """Import all school profiles from school_info.py into rag_chunks."""
    async for db in get_db():
        all_chunks = []
        for name in SCHOOL_NAMES:
            profile = get_school_info(name)
            if not profile:
                logger.info(f"No profile for {name}")
                continue

            text = f"{name} | {profile.get('tier','')} | {profile.get('type','')}类\n"
            if profile.get('tags'):
                text += f"标签：{'、'.join(profile['tags'])}\n"
            if profile.get('intro'):
                text += profile['intro']

            chunks = chunk_document(
                text=text,
                doc_type='school_profile',
                school_name=name,
                city='南京',
                province=None,  # school profile is province-independent
                year=2025,
                source_url='https://www.nju.edu.cn' if '南京大学' in name else None,
                source_name='择境学校知识库（人工校验）',
                source_type='manual',
                data_source='manual',
                confidence='medium',
            )
            all_chunks.extend(chunks)
            logger.info(f"  {name}: {len(chunks)} chunks")

        # Index all
        stats = await index_chunks(db, all_chunks)
        logger.info(f"Seeded {stats['inserted']} school profile chunks")
        return stats


if __name__ == "__main__":
    asyncio.run(seed_school_profiles())

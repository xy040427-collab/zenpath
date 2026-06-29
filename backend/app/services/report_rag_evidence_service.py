"""
report_rag_evidence_service.py — Fetch RAG evidence for schools and report sections.

Queries the rag_chunks table for official school documentation.
Used by report_ai_writer to ground AI analysis in real data.
"""

import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)

# We use raw SQL to avoid model import issues in background tasks
RAG_QUERY = """
SELECT content, source_url, doc_type, confidence
FROM rag_chunks
WHERE school_name LIKE :name_pattern
  AND LENGTH(content) >= 150
ORDER BY LENGTH(content) DESC
LIMIT :limit
"""


async def fetch_school_evidence(
    db,
    school_name: str,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Fetch RAG evidence for a school.

    Args:
        db: SQLAlchemy async session
        school_name: School name to search for
        limit: Max number of chunks to return

    Returns:
        List of evidence dicts with title, source_url, summary
    """
    try:
        result = await db.execute(
            text(RAG_QUERY),
            {"name_pattern": f"%{school_name}%", "limit": limit},
        )
        rows = result.fetchall()
    except Exception as e:
        logger.warning(f"RAG query failed for '{school_name}': {e}")
        return []

    evidence = []
    for row in rows:
        content = row[0] if row[0] else ""
        source_url = row[1] or ""
        chunk_type = row[2] or ""
        confidence_raw = row[3] or "0.0"
        # confidence may be VARCHAR like 'high'/'medium'/'low' or numeric
        try:
            confidence_val = float(confidence_raw)
        except (ValueError, TypeError):
            conf_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            confidence_val = conf_map.get(str(confidence_raw).lower(), 0.5)

        # Extract first 300 chars as summary
        summary = content[:300].strip()

        evidence.append({
            "title": f"{school_name} · {chunk_type or '院校资料'}",
            "source_name": "CHSI 阳光高考" if "chsi" in (source_url or "").lower() else "公开院校资料",
            "source_url": source_url,
            "summary": summary,
            "confidence": float(confidence_val) if confidence_val else 0.0,
        })

    return evidence


NO_EVIDENCE_FALLBACK = (
    "当前知识库未检索到足够的官方资料。"
    "本报告中的录取与专业组分析主要基于历年投档线、一分一段表和院校专业组数据。"
    "填报前仍需以高校招生章程、省教育考试院招生计划和志愿填报系统为准。"
)

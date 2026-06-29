"""
RAG Indexer — writes chunks to rag_chunks table.

Handles: dedup, upsert, metadata validation, coverage status update.
"""
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag.sources import compute_content_hash, SOURCE_CONFIDENCE

logger = logging.getLogger(__name__)


async def index_chunks(
    db: AsyncSession,
    chunks: list[dict],
    dedup: bool = True,
) -> dict:
    """Write chunks to rag_chunks. Returns {inserted, skipped, updated}."""
    stats = {'inserted': 0, 'skipped': 0, 'updated': 0}

    now = datetime.utcnow()

    for chunk in chunks:
        content = chunk.get('content', '')
        if not content:
            stats['skipped'] += 1
            continue

        content_hash = chunk.get('content_hash') or compute_content_hash(content)
        chunk_id = chunk.get('chunk_id') or f"{chunk.get('doc_type','unknown')}_{content_hash}"

        school_name = chunk.get('school_name')
        major_name = chunk.get('major_name')
        city = chunk.get('city')
        province = chunk.get('province')
        year = chunk.get('year')
        doc_type = chunk.get('doc_type', '')
        title = chunk.get('title', '')
        section = chunk.get('section', '')
        source_url = chunk.get('source_url')
        source_name = chunk.get('source_name')
        source_type = chunk.get('source_type', 'official')
        data_source = chunk.get('data_source', 'official')
        confidence = chunk.get('confidence') or SOURCE_CONFIDENCE.get(source_type, 'medium')

        # Check for existing chunk
        existing = await db.execute(
            text("SELECT id, content_hash FROM rag_chunks WHERE chunk_id = :cid"),
            {'cid': chunk_id}
        )
        existing_row = existing.fetchone()

        if existing_row:
            if dedup and existing_row[1] == content_hash:
                stats['skipped'] += 1
                continue
            # Update
            await db.execute(text("""
                UPDATE rag_chunks SET
                    doc_type = :dt, title = :t, section = :sec, content = :c,
                    source_url = :su, source_name = :sn, source_type = :st,
                    data_source = :ds, confidence = :cf, content_hash = :ch,
                    crawled_at = :ca, updated_at = :ua
                WHERE chunk_id = :cid
            """), {
                'dt': doc_type, 't': title, 'sec': section, 'c': content,
                'su': source_url, 'sn': source_name, 'st': source_type,
                'ds': data_source, 'cf': confidence, 'ch': content_hash,
                'ca': now, 'ua': now, 'cid': chunk_id,
            })
            stats['updated'] += 1
        else:
            await db.execute(text("""
                INSERT INTO rag_chunks (
                    chunk_id, doc_type, school_name, major_name, city, province,
                    year, title, section, content,
                    source_url, source_name, source_type, data_source, confidence,
                    content_hash, crawled_at, created_at, updated_at
                ) VALUES (
                    :cid, :dt, :sn2, :mn, :ci, :pv,
                    :yr, :t, :sec, :c,
                    :su, :sn3, :st, :ds, :cf,
                    :ch, :ca, :cr, :ua
                )
            """), {
                'cid': chunk_id, 'dt': doc_type, 'sn2': school_name,
                'mn': major_name, 'ci': city, 'pv': province,
                'yr': year, 't': title, 'sec': section, 'c': content,
                'su': source_url, 'sn3': source_name, 'st': source_type,
                'ds': data_source, 'cf': confidence, 'ch': content_hash,
                'ca': now, 'cr': now, 'ua': now,
            })
            stats['inserted'] += 1

    await db.commit()
    logger.info(f"Indexed {stats['inserted']} chunks, updated {stats['updated']}, skipped {stats['skipped']}")
    return stats

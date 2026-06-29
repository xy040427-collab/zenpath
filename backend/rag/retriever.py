"""
RAG Retriever — keyword + metadata-filtered search over rag_chunks.

First version uses SQL FTS + metadata filter.
Vector search can be added later by swapping the query logic.
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DOC_TYPE_PRIORITY = {
    'major_profile': 10,
    'employment_report': 9,
    'career_path': 8,
    'city_industry': 7,
    'school_profile': 6,
    'admission_policy': 5,
    'discipline_evaluation': 5,
    'transfer_policy': 3,
    'physical_restriction': 2,
}


async def retrieve_explanation_evidence(
    db: AsyncSession,
    school_name: str | None = None,
    major_name: str | None = None,
    city: str | None = None,
    province: str | None = None,
    user_profile: dict | None = None,
    recommendation: dict | None = None,
    top_k: int = 8,
    required_doc_types: list[str] | None = None,
) -> list[dict]:
    """Retrieve RAG evidence chunks relevant to a recommendation.
    
    Args:
        required_doc_types: If set, ONLY these doc_types are returned.
    """
    conditions = ["data_source != 'mock'", "is_valid_for_rag = 1"]
    params = {}

    # Metadata filter: exact school match
    if school_name:
        conditions.append("school_name = :sn")
        params['sn'] = school_name

    # Major filter: exact or partial
    if major_name:
        conditions.append("(major_name = :mn OR major_name IS NULL)")
        params['mn'] = major_name

    # Province: only for province-specific content OR no province restriction
    if province:
        conditions.append("(province = :pv OR province IS NULL)")
        params['pv'] = province

    # Doc type constraint from intent routing
    if required_doc_types:
        placeholders = ",".join(f":dt{i}" for i in range(len(required_doc_types)))
        conditions.append(f"doc_type IN ({placeholders})")
        for i, dt in enumerate(required_doc_types):
            params[f'dt{i}'] = dt

    # Doc type priority scoring
    priority_expr = " + ".join(
        f"CASE WHEN doc_type = '{dt}' THEN {pri} ELSE 0 END"
        for dt, pri in DOC_TYPE_PRIORITY.items()
    )

    where = " AND ".join(conditions)

    query = f"""
        SELECT chunk_id, doc_type, school_name, major_name, city, province,
               title, section, content, source_url, source_name, source_type,
               data_source, confidence, year,
               ({priority_expr}) as priority_score
        FROM rag_chunks
        WHERE {where}
        ORDER BY priority_score DESC, year DESC
        LIMIT :limit
    """

    params['limit'] = top_k * 3  # oversample for rerank
    result = await db.execute(text(query), params)
    rows = result.fetchall()

    chunks = []
    for r in rows:
        chunks.append({
            'chunk_id': r[0],
            'doc_type': r[1],
            'school_name': r[2],
            'major_name': r[3],
            'city': r[4],
            'province': r[5],
            'title': r[6],
            'section': r[7],
            'content': r[8],
            'source_url': r[9],
            'source_name': r[10],
            'source_type': r[11],
            'data_source': r[12],
            'confidence': r[13],
            'year': r[14],
            'priority_score': r[15],
        })

    # Rerank: deduplicate by doc_type (keep highest priority per type)
    chunks = _rerank_by_type_priority(chunks, top_k)
    return chunks


def _rerank_by_type_priority(chunks: list[dict], top_k: int) -> list[dict]:
    """Keep top chunk per doc_type, fill remaining with next best."""
    seen_types = set()
    deduped = []
    for c in sorted(chunks, key=lambda x: x['priority_score'], reverse=True):
        if c['doc_type'] not in seen_types:
            deduped.append(c)
            seen_types.add(c['doc_type'])
        if len(deduped) >= top_k:
            break

    # If we still have room, add remaining (lower priority types)
    if len(deduped) < top_k:
        for c in sorted(chunks, key=lambda x: x['priority_score'], reverse=True):
            if c not in deduped:
                deduped.append(c)
            if len(deduped) >= top_k:
                break

    return deduped[:top_k]

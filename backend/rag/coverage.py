"""
Data coverage checker — checks which provinces/years/types have data available.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_coverage(db: AsyncSession, province: str) -> dict:
    """Return coverage status for a province across all data types."""
    result = await db.execute(text("""
        SELECT data_type, status, row_count, notes
        FROM data_coverage_status
        WHERE province = :p
        ORDER BY data_type, year DESC
    """), {'p': province})
    rows = result.fetchall()

    coverage = {
        'score_rank': 'missing',
        'admission_lines': 'missing',
        'rag_knowledge': 'missing',
        'warnings': [],
        'details': {},
    }

    for r in rows:
        data_type, status, row_count, notes = r
        coverage['details'].setdefault(data_type, {'status': status, 'years': [], 'row_count': 0})
        coverage['details'][data_type]['row_count'] += (row_count or 0)

    # Determine status for each core type
    if 'score_rank' in coverage['details']:
        coverage['score_rank'] = 'available' if coverage['details']['score_rank']['row_count'] > 0 else 'missing'

    if 'admission_line' in coverage['details']:
        coverage['admission_lines'] = 'available' if coverage['details']['admission_line']['row_count'] > 0 else 'missing'

    # Check rag_chunks
    rag_result = await db.execute(text(
        "SELECT COUNT(*) FROM rag_chunks WHERE data_source != 'mock' AND (province IS NULL OR province = :p)"
    ), {'p': province})
    rag_count = rag_result.fetchone()[0]
    coverage['rag_knowledge'] = 'available' if rag_count > 10 else ('partial' if rag_count > 0 else 'missing')

    # Generate warnings
    if coverage['score_rank'] == 'missing':
        coverage['warnings'].append(f'{province}省缺少一分一段表数据，无法进行分数→位次转换。')
    if coverage['admission_lines'] == 'missing':
        coverage['warnings'].append(f'{province}省缺少院校专业投档线数据，无法生成位次匹配推荐。')
    if coverage['rag_knowledge'] == 'missing':
        coverage['warnings'].append('RAG知识库内容不足，推荐解释可能较为简略。')

    return coverage

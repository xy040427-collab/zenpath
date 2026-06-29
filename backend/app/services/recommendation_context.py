"""
Recommendation Context — structured context builder for recommendation detail display.

Replaces the old "rag_retriever" pseudo-RAG approach.
This module does structured data lookups (SQL + Python dict), NOT AI/LLM retrieval.
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.school_info import get_school_info

logger = logging.getLogger(__name__)


async def retrieve_recommendation_context(
    db: AsyncSession,
    school_name: str,
    major_name: str | None = None,
    province: str = '山东',
) -> dict:
    """Build structured context for recommendation display (no LLM involved)."""
    context = {
        'school_profile': None,
        'admission_history': [],
        'sources': [],
    }

    # School profile from knowledge base
    profile = get_school_info(school_name)
    if profile:
        context['school_profile'] = profile
        context['sources'].append('择境学校知识库')
    else:
        # Fallback: schools table
        result = await db.execute(
            text("""SELECT name, level, type, city, is_public, description
                FROM schools WHERE name = :name LIMIT 1"""),
            {'name': school_name}
        )
        row = result.fetchone()
        if row:
            context['school_profile'] = {
                'name': row[0], 'tier': row[1] or '未知',
                'type': row[2] or '未知', 'city': row[3] or '',
                'is_public': bool(row[4]) if row[4] is not None else True,
                'intro': row[5] or '',
            }
            context['sources'].append('学校信息库')

    # Admission history
    result = await db.execute(
        text("""SELECT year, CAST(min_rank AS INTEGER), CAST(min_score AS INTEGER),
                   CAST(plan_count AS INTEGER)
            FROM admission_lines
            WHERE province = :pv AND university_name = :sn
              AND (:mj IS NULL OR major_group_name = :mj)
              AND CAST(min_rank AS INTEGER) > 0
            ORDER BY year DESC LIMIT 12"""),
        {'pv': province, 'sn': school_name, 'mj': major_name}
    )
    for row in result.fetchall():
        context['admission_history'].append({
            'year': row[0], 'min_rank': row[1], 'min_score': row[2], 'plan_count': row[3],
        })
    if context['admission_history']:
        context['sources'].append(f'{province}省教育考试院官方投档数据')

    return context


def build_recommendation_summary(
    context: dict, profile: dict, recommendation: dict
) -> str:
    """Build markdown summary from structured context and recommendation data."""
    parts = []
    sp = context.get('school_profile')
    if sp:
        tier = sp.get('tier', '')
        tags = '、'.join(sp.get('tags', []))
        intro = sp.get('intro', '')
        parts.append(f"**{sp.get('name', '')}** | {tier} | {sp.get('type', '')}类")
        if tags:
            parts.append(f"标签：{tags}")
        if intro:
            parts.append(intro)

    history = context.get('admission_history', [])
    if history:
        lines = []
        for h in history:
            lines.append(f"{h['year']}年：最低{h['min_score']}分/位次{h['min_rank']}")
        parts.append(f"\n**录取数据**：{' | '.join(lines)}")
        if history[0].get('plan_count'):
            parts.append(f"招生计划：{history[0]['plan_count']}人")

    risk = recommendation.get('risk_level', '')
    prob = recommendation.get('probability', 0)
    reason = recommendation.get('algorithm_reason', '')
    risk_labels = {'保': '🎯 保底推荐', '稳': '✅ 稳妥推荐', '冲': '⚠️ 冲刺推荐'}
    parts.append(f"\n**{risk_labels.get(risk, risk)}** — 录取概率约{prob}%")
    parts.append(f"> {reason}")

    return '\n'.join(parts)

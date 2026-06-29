"""
/api/v1/ai/gaokao/recommend — SQL-RAG 志愿推荐接口 v3

改进：
1. 基于录取年数的真实概率算法
2. 自动过滤"不推荐"结果
3. 专业相关性评分 + 中外合作标记
4. 真 RAG 知识库检索（非模板摘要）
5. 数据覆盖状态检查
6. LLM 个性化解释（可选）
7. 冲稳保分组展示
"""
import json
import logging
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.query_parser import parse_query
from app.services.rank_matcher import (
    query_rank_from_score, compute_recommendations,
)
from app.services.preference_matcher import expand_major_preferences, filter_and_strategize
from app.services.exam_config import get_exam_config, get_subject_type_for_rank_lookup
from app.services.recommendation_context import (
    retrieve_recommendation_context, build_recommendation_summary,
)
from rag.coverage import check_coverage
from rag.retriever import retrieve_explanation_evidence
from rag.prompt_builder import build_explanation_prompt
from rag.generator import generate_explanation
from rag.post_check import validate_ai_explanation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai/gaokao", tags=["SQL-RAG 推荐"])


class RecommendRequest(BaseModel):
    message: str = Field(..., description="用户自然语言输入")
    enable_ai: bool = Field(default=False, description="是否启用AI个性化解释")


@router.post("/recommend")
async def gaokao_recommend(
    body: RecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    """SQL-RAG 志愿推荐 — 基于真实录取数据 + RAG 知识库"""
    user_query = body.message

    # ── Step 1: 解析用户输入 ──
    profile = parse_query(user_query)
    province = profile.get('province')
    if not province:
        return {
            'success': True, 'project': '择境 ZENPATH',
            'message': '请说明您的省份（如"我是山东考生"）',
            'parsed_profile': profile, 'total_count': 0,
            'recommendations_by_risk': {},
            'data_coverage': {
                'score_rank': 'missing', 'admission_lines': 'missing',
                'rag_knowledge': 'missing', 'warnings': ['省份未识别'],
            },
        }

    # ── Step 2: 数据覆盖检查 ──
    coverage = await check_coverage(db, province)

    exam_config = get_exam_config(province)

    # ── Step 3: 位次查询 ──
    user_rank = profile.get('rank')
    user_score = profile.get('score')
    subjects = profile.get('subjects', [])
    subject_type = get_subject_type_for_rank_lookup(province, subjects)

    if not user_rank and user_score:
        for year in [2025, 2024, 2023]:
            rank = await query_rank_from_score(db, province, year, user_score, subject_type)
            if rank:
                user_rank = rank
                profile['rank'] = rank
                profile['rank_source'] = f'{year}年{subject_type}排名'
                break

    if not user_rank:
        return {
            'success': True, 'project': '择境 ZENPATH',
            'message': '请提供分数或位次（如"590分"或"位次32966"）',
            'parsed_profile': profile, 'total_count': 0,
            'recommendations_by_risk': {},
            'data_coverage': coverage,
        }

    profile['exam_mode'] = exam_config.get('mode')
    profile['total_score'] = exam_config.get('total_score')

    # ── Step 4: 专业扩展 ──
    major_prefs = profile.get('major_preferences', [])
    if major_prefs:
        major_prefs = expand_major_preferences(major_prefs)

    city_prefs = profile.get('city_preferences', [])

    # ── Step 5: 核心推荐计算 ──
    raw_recommendations = await compute_recommendations(
        db=db, province=province, user_rank=user_rank,
        major_preferences=major_prefs if major_prefs else None,
        city_preferences=city_prefs if city_prefs else None,
        years=[2025, 2024, 2023],
    )

    # ── Step 6: 策略过滤 ──
    risk_pref = profile.get('risk_preference', '均衡')
    recommendations = filter_and_strategize(raw_recommendations, risk_pref)

    # ── Step 7: 推荐上下文 + RAG证据（为每个推荐项） ──
    rag_ctx_cache = {}
    for rec in recommendations:
        school = rec['school_name']
        key = f"{school}|{rec.get('major_name','')}"
        if key not in rag_ctx_cache:
            rag_ctx_cache[key] = await retrieve_recommendation_context(
                db, school, rec.get('major_name'), province
            )

        ctx = rag_ctx_cache[key]
        # Structured summary (non-AI, always available)
        rec['recommendation_summary'] = build_recommendation_summary(ctx, profile, rec)
        # Backward compat
        rec['rag_summary'] = rec['recommendation_summary']

        # AI explanation (optional, only if enabled AND API key present)
        if body.enable_ai:
            city = rec.get('city', '')
            evidences = await retrieve_explanation_evidence(
                db, school_name=school, major_name=rec.get('major_name'),
                city=city, province=province, user_profile=profile,
                recommendation=rec, top_k=8,
            )
            rec['rag_evidence_count'] = len(evidences)

            if evidences:
                messages = build_explanation_prompt(rec, evidences, profile, coverage)
                ai_result = await generate_explanation(messages)
                if ai_result['status'] == 'ok' and ai_result['explanation']:
                    explanation = ai_result['explanation']
                    # Post-check
                    combined_text = json.dumps(explanation, ensure_ascii=False)
                    validation = validate_ai_explanation(combined_text, rec, evidences)
                    rec['ai_explanation'] = explanation
                    rec['rag_status'] = 'ok'
                    rec['ai_validation'] = validation
                    continue

            rec['ai_explanation'] = None
            rec['rag_status'] = 'insufficient' if body.enable_ai else 'disabled'
            rec['rag_evidence_count'] = 0
        else:
            rec['ai_explanation'] = None
            rec['rag_status'] = 'disabled'
            rec['rag_evidence_count'] = 0

    # ── Step 8: 统计与分组 ──
    risk_counts = Counter(r['risk_level'] for r in recommendations)
    grouped = {}
    for rl in ['保', '稳', '冲']:
        items = [r for r in recommendations if r['risk_level'] == rl]
        if items:
            grouped[rl] = {
                'count': len(items),
                'label': {'保': '🎯 保底推荐', '稳': '✅ 稳妥推荐', '冲': '⚠️ 冲刺推荐'}.get(rl, rl),
                'description': {
                    '保': '你的位次明显优于历年录取线，录取把握极大',
                    '稳': '你的位次与历年录取线匹配，录取概率较高',
                    '冲': '你的位次接近或略低于录取线，有录取机会但需搭配稳妥志愿',
                }.get(rl, ''),
                'items': items,
            }

    # ── Step 9: 生成总结 ──
    summary_parts = []
    for rl in ['保', '稳', '冲']:
        cnt = risk_counts.get(rl, 0)
        if cnt:
            label = {'保': '保底', '稳': '稳妥', '冲': '冲刺'}.get(rl, rl)
            summary_parts.append(f'{label}{cnt}个')
    summary = f'共{len(recommendations)}个推荐项：{"、".join(summary_parts)}。'
    summary += f'数据基于{province}省教育考试院官方投档线（2023-2025年）。'
    if city_prefs:
        summary += f'城市偏好：{"、".join(city_prefs[:5])}。'

    warnings = coverage.get('warnings', []).copy()
    sino_foreign_count = sum(1 for r in recommendations if r.get('is_sino_foreign'))
    if sino_foreign_count:
        warnings.append(f'有{sino_foreign_count}个推荐项为中外合作办学项目，学费较高，请留意。')
    if any('学院' in r['school_name'] and r.get('risk_level') == '保' for r in recommendations):
        warnings.append('保底推荐中包含独立学院/民办院校，请注意区分办学性质。')

    return {
        'success': True,
        'project': '择境 ZENPATH',
        'exam_config': {'mode': exam_config.get('mode'), 'total_score': exam_config.get('total_score')},
        'parsed_profile': profile,
        'total_count': len(recommendations),
        'risk_distribution': dict(risk_counts),
        'recommendations_by_risk': grouped,
        'summary': summary,
        'data_coverage': coverage,
        'warnings': warnings,
    }

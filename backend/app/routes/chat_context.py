"""
Chat with Context — upgraded AI chat that receives recommendation context.

When a user asks follow-up questions from the recommendation page,
the chat request carries the current recommendation state for personalized answers.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import AIConversation, AIChatMessage
from app.schemas.schemas import ConversationCreate, MessageCreate
from rag.retriever import retrieve_explanation_evidence
from rag.prompt_builder import SYSTEM_PROMPT, build_explanation_prompt
from rag.generator import generate_explanation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai/chat", tags=["AI Chat with Context"])


@router.post("/ask")
async def ask_with_context(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Ask a follow-up question with recommendation context."""
    question = body.get('question', '')
    profile = body.get('profile', {})
    recommendation = body.get('recommendation', {})
    data_coverage = body.get('data_coverage', {})

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    province = profile.get('province', '')
    school = recommendation.get('school_name', '')
    major = recommendation.get('major_name', '')

    # Retrieve RAG evidence if recommendation context is present
    evidences = []
    if school:
        evidences = await retrieve_explanation_evidence(
            db, school_name=school, major_name=major,
            province=province, user_profile=profile,
            recommendation=recommendation, top_k=8,
        )

    # Build context-aware system prompt
    context_prompt = SYSTEM_PROMPT + "\n\n## 当前推荐上下文\n"
    if recommendation:
        context_prompt += f"- 目标学校: {recommendation.get('school_name','')}\n"
        context_prompt += f"- 目标专业: {recommendation.get('major_name','')}\n"
        context_prompt += f"- 风险等级: {recommendation.get('risk_level','')}\n"
        context_prompt += f"- 录取概率: {recommendation.get('probability','')}%\n"
        context_prompt += f"- 算法理由: {recommendation.get('algorithm_reason','')}\n"
        context_prompt += f"- 近3年录取均位: {recommendation.get('rank_analysis',{}).get('avg_rank','未知')}\n"

    if profile:
        context_prompt += f"\n## 用户画像\n"
        context_prompt += f"- 省份: {profile.get('province','')}\n"
        context_prompt += f"- 位次: {profile.get('rank','')}\n"
        context_prompt += f"- 分数: {profile.get('score','')}\n"
        context_prompt += f"- 兴趣: {','.join(profile.get('major_preferences',[]))}\n"

    if evidences:
        context_prompt += "\n## RAG参考资料\n"
        for i, ev in enumerate(evidences[:5], 1):
            context_prompt += f"[{i}] {ev.get('doc_type','')}: {ev.get('content','')[:300]}...\n"

    if data_coverage.get('warnings'):
        context_prompt += "\n## 数据覆盖提示\n"
        context_prompt += '\n'.join(f"- {w}" for w in data_coverage['warnings'])

    messages = [
        {'role': 'system', 'content': context_prompt},
        {'role': 'user', 'content': question},
    ]

    ai_result = await generate_explanation(messages)

    if ai_result['status'] == 'ok' and ai_result['explanation']:
        answer = ai_result['explanation'] if isinstance(ai_result['explanation'], str) else \
                 ai_result['explanation'].get('student_version', str(ai_result['explanation']))
    else:
        answer = f"抱歉，当前无法生成个性化回答。{ai_result.get('message','')}"

    return {
        'success': True,
        'answer': answer,
        'rag_status': ai_result['status'],
        'evidences_count': len(evidences),
        'sources': [
            {
                'source_name': ev.get('source_name', ''),
                'source_url': ev.get('source_url', ''),
                'doc_type': ev.get('doc_type', ''),
            }
            for ev in evidences[:5]
        ] if evidences else [],
    }

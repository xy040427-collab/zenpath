"""
Context Assembler — 上下文组装 + LLM生成 + Citation
Step 14-16: Context Assembly, Prompt设计, LLM生成, Citation来源引用
"""

import json
import logging
import os
import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是择境（ZENPATH）高考志愿助手。

你的职责是根据系统提供的结构化算法结果和检索到的参考资料，为用户生成清晰、可信、可读的志愿推荐解释。

## 核心原则
1. 冲稳保等级、位次差、录取风险只能引用算法结果，不允许自行推测。
2. 只能基于系统提供的资料回答问题，不得编造以下任何数据：
   - 最低分、最低位次、招生计划、学费、选科要求
   - 学校排名、专业排名、录取概率
3. 如果资料不足，请明确说"当前资料不足，无法确认"。
4. 禁止使用以下绝对化表述：
   - "一定能上""保证录取""100%稳""绝对安全""不会滑档""稳赚""必录"
5. 回答风格要面向学生和家长，清晰易懂，同时体现择境定位：
   - 不仅解释能不能上，还要解释学校、专业、城市、职业路径和人生环境。

## 输出格式要求
请以自然流畅的段落输出解释，包含：
1. 推荐结论（冲稳保等级）
2. 位次依据（引用算法结果）
3. 专业适配理由（引用RAG资料）
4. 学校和城市环境说明（引用RAG资料）
5. 风险点（引用算法结果）
6. 替代建议（如有）
7. 家长版白话解释"""


def build_user_prompt(
    profile: dict,
    recommendation: dict,
    rag_evidence: list[dict],
) -> str:
    """
    构建用户侧prompt
    """
    sections = []
    
    # 用户画像
    profile_lines = [
        f"省份：{profile.get('province', '未知')}",
        f"分数：{profile.get('score', '未知')}",
        f"位次：{profile.get('rank', '未知')}",
        f"选科：{'、'.join(profile.get('subjects', [])) if profile.get('subjects') else '未知'}",
        f"专业偏好：{'、'.join(profile.get('major_preferences', [])) if profile.get('major_preferences') else '未知'}",
        f"城市偏好：{'、'.join(profile.get('city_preferences', [])) if profile.get('city_preferences') else '未知'}",
        f"风险偏好：{profile.get('risk_preference', '均衡')}",
    ]
    sections.append("【用户画像】\n" + "\n".join(profile_lines))
    
    # 算法推荐结果
    rank_analysis = recommendation.get('rank_analysis', {})
    algo_lines = [
        f"学校：{recommendation.get('school_name', '')}",
        f"专业：{recommendation.get('major_name', '')}",
        f"风险等级：{recommendation.get('risk_level', '')}",
        f"用户位次：{rank_analysis.get('user_rank', '')}",
        f"近三年平均最低位次：{rank_analysis.get('avg_min_rank', '')}",
        f"安全边际：{rank_analysis.get('rank_margin', '')} 位",
        f"算法理由：{recommendation.get('algorithm_reason', '')}",
    ]
    sections.append("【算法推荐结果】\n" + "\n".join(algo_lines))
    
    # RAG证据
    for i, chunk in enumerate(rag_evidence[:5], 1):
        evidence_lines = [
            f"来源：{chunk.get('source_url', 'mock')}",
            f"资料类型：{chunk.get('doc_type', '')}",
            f"年份：{chunk.get('year', '')}",
            f"章节：{chunk.get('section', '')}",
            f"内容：{chunk.get('content', '')[:500]}",  # 截断过长内容
        ]
        sections.append(f"【RAG 证据 {i}】\n" + "\n".join(evidence_lines))
    
    return "\n\n".join(sections)


async def call_llm(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """调用 DeepSeek API 生成解释"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    
    if not api_key:
        return _fallback_generate(user_prompt)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.6,
                'max_tokens': 1024,
            }
            resp = await client.post(
                f'{base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(f"LLM call failed: {e}, using fallback")
        return _fallback_generate(user_prompt)


def _fallback_generate(user_prompt: str) -> str:
    """LLM不可用时的回退模板"""
    # 从prompt中提取关键信息
    school_name = ""
    major_name = ""
    risk_level = ""
    
    for line in user_prompt.split('\n'):
        if line.startswith('学校：'):
            school_name = line.replace('学校：', '').strip()
        elif line.startswith('专业：'):
            major_name = line.replace('专业：', '').strip()
        elif line.startswith('风险等级：'):
            risk_level = line.replace('风险等级：', '').strip()
    
    risk_labels = {
        '保': '保底',
        '稳': '稳妥',
        '稳偏冲': '稳中带冲',
        '冲': '冲刺',
        '高风险': '高风险',
    }
    risk_cn = risk_labels.get(risk_level, risk_level)
    
    explanation = f"**{school_name}{major_name}——{risk_cn}推荐**\n\n"
    explanation += f"从位次分析来看，该专业算法判断为「{risk_cn}」。具体位次依据见算法分析部分。\n\n"
    
    if risk_level in ('保', '稳'):
        explanation += "从专业匹配角度看，该专业方向与您的偏好较为契合，可以考虑作为主要志愿填报。\n\n"
    elif risk_level in ('冲', '稳偏冲'):
        explanation += "该专业录取有一定难度，但如果当年报考热度下降或招生计划增加，仍有机会。建议搭配稳妥和保底院校。\n\n"
    
    explanation += "**风险提示**：本推荐基于历史录取数据，实际录取位次可能因当年报考热度、招生计划变化而上下浮动。建议考生和家长在填报前仔细阅读目标院校的招生章程，确认选科要求、身体条件限制等细节。"
    
    return explanation


async def generate_explanation(
    profile: dict,
    recommendation: dict,
    rag_evidence: list[dict],
) -> str:
    """为单个推荐项生成解释"""
    user_prompt = build_user_prompt(profile, recommendation, rag_evidence)
    return await call_llm(SYSTEM_PROMPT, user_prompt)


def build_sources(recommendation: dict, rag_evidence: list[dict]) -> list[dict]:
    """构建来源引用"""
    sources = []
    for chunk in rag_evidence[:5]:
        source = {
            'title': chunk.get('title', ''),
            'doc_type': chunk.get('doc_type', ''),
            'year': chunk.get('year'),
            'source_url': chunk.get('source_url', 'mock'),
        }
        if source not in sources:
            sources.append(source)
    
    return sources

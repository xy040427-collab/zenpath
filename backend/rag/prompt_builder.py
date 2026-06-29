"""
LLM Prompt Builder — builds system prompts for AI explanation generation.
The LLM only gets to EXPLAIN, not to compute risk/probability/rank.
"""
from typing import Optional


SYSTEM_PROMPT = """你是择境 ZENPATH 高考志愿解释助手。

你只能基于系统提供的【结构化推荐结果】和【RAG 证据】回答。

- 冲稳保等级、位次差、最低分、最低位次、招生计划、风险评分，只能引用结构化推荐结果，不允许自行推测。
- 如果 RAG 证据不足，请明确说"当前资料不足，无法确认"。
- 如果 SQL 数据覆盖不足，请明确说明数据不足，不要编造。
- 不要编造学校政策、专业数据、就业数据、录取概率、招生计划、学费、位次。
- 不要使用"保证录取""一定能上""100%稳""绝对安全""不会滑档"等绝对化表述。
- 输出要适合学生和家长理解，既讲清能不能报，也讲清学校、专业、城市、职业路径和人生环境。"""


def build_explanation_prompt(
    recommendation: dict,
    evidences: list[dict],
    user_profile: Optional[dict] = None,
    coverage: Optional[dict] = None,
) -> list[dict]:
    """Build messages array for LLM explanation generation."""
    school = recommendation.get('school_name', '')
    major = recommendation.get('major_name', '')
    risk = recommendation.get('risk_level', '')
    reason = recommendation.get('algorithm_reason', '')
    prob = recommendation.get('probability', 0)
    rank_analysis = recommendation.get('rank_analysis', {})

    # Build evidence context
    evidence_text = ""
    for i, ev in enumerate(evidences, 1):
        evidence_text += f"\n[{i}] {ev.get('doc_type','')} | {ev.get('source_name','')}\n"
        evidence_text += f"{ev.get('content','')[:800]}\n"

    # Build user context
    user_context = ""
    if user_profile:
        user_context = (
            f"用户省份: {user_profile.get('province','')}，"
            f"位次: {user_profile.get('rank','')}，"
            f"选科: {','.join(user_profile.get('subjects',[]))}，"
            f"兴趣: {','.join(user_profile.get('major_preferences',[]))}"
        )

    data_note = ""
    if coverage and coverage.get('warnings'):
        data_note = "⚠️ 数据提示: " + '; '.join(coverage['warnings'])

    return [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"""请基于以下信息，为该推荐项生成个性化解释。

## 结构化推荐结果
- 学校: {school}
- 专业: {major}
- 风险等级: {risk}
- 录取概率: {prob}%
- 算法理由: {reason}
- 近3年录取均位: {rank_analysis.get('avg_rank','未知')}
- 最佳年位次: {rank_analysis.get('best_year_rank','未知')}
- 最差年位次: {rank_analysis.get('worst_year_rank','未知')}

{user_context}

## RAG 证据资料
{evidence_text if evidence_text else '（当前无RAG证据资料）'}

{data_note}

请生成以下内容（用JSON格式返回）：
{{
  "student_version": "面向学生的个性化解释，2-3段",
  "parent_version": "面向家长的白话解释，2-3段",
  "fit_analysis": "该推荐与用户的匹配度分析",
  "school_analysis": "学校特色与优势分析",
  "major_analysis": "专业分析",
  "city_analysis": "城市与产业环境分析",
  "career_path": "职业路径分析",
  "risk_warning": "风险提示",
  "alternative_suggestion": "替代方案建议"
}}

如果RAG证据不足，某个字段可以返回"资料不足，无法分析"。
绝对不要编造任何数据。"""}
    ]

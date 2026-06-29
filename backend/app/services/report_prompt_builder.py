"""
report_prompt_builder.py — Build structured prompts for AI report generation.

Constructs prompts from:
- Structured recommendation data
- User profile
- Score/rank information
- School details
- RAG evidence
- Major group data

All prompts follow strict rules: no fabricated data, no absolute guarantees.
"""

from typing import Dict, Any, List, Optional

SYSTEM_ROLE = """你是择境 ZENPATH 的高考志愿顾问。你需要根据结构化数据、历年投档线、专业组信息、用户偏好和官方资料 evidence，生成适合家长和考生阅读的正式报告文字。

你必须遵守：
1. 不能承诺录取，不能说"保证录取""一定能上"
2. 不能编造精确录取概率（如"85%概率"）
3. 不能编造就业率、学校优势学科、招生章程条款
4. 不能无来源地说"该校就业很好"
5. 资料不足时要明确说明
6. 语言正式、清楚、适合家长阅读
7. 不要出现 JSON、字段名、debug 词汇
8. 每段 80-160 字，避免过短"""


def build_executive_summary_prompt(
    user_info: Dict[str, Any],
    summary: Dict[str, Any],
) -> str:
    """Build prompt for executive summary AI generation."""
    province = user_info.get("province", "")
    subject = user_info.get("subject_type", "")
    score = user_info.get("score", "")
    rank = user_info.get("rank", "")
    total = summary.get("total_candidates", 0)
    rush_n = summary.get("rush_count", 0)
    stable_n = summary.get("stable_count", 0)
    safe_n = summary.get("safe_count", 0)

    return f"""请为一份高考志愿填报分析报告撰写执行摘要（300-500字）。

考生信息：{province}省 {subject}，{score}分，位次{rank}
推荐方案：共{total}所院校，冲刺{rush_n}所、稳妥{stable_n}所、保底{safe_n}所

要求：
1. 说明当前成绩定位和位次在填报中的意义
2. 概括推荐方案的整体结构
3. 指出主要机会
4. 指出主要风险
5. 给出核心建议

请直接输出摘要正文，不要加标题、不要分段编号。"""


def build_school_analysis_prompt(
    user_info: Dict[str, Any],
    school: Dict[str, Any],
    evidence: List[Dict[str, Any]],
) -> str:
    """Build prompt for single school deep analysis."""
    province = user_info.get("province", "")
    score = user_info.get("score", "")
    rank = user_info.get("rank", "")
    interests = user_info.get("interests", "")
    region_pref = user_info.get("region_preference", "")

    school_name = school.get("school_name", "")
    city = school.get("city", "")
    bucket = school.get("bucket", "rush")
    bucket_cn = {"rush": "冲刺", "stable": "稳妥", "safe": "保底"}.get(bucket, bucket)
    ref_rank = school.get("reference_rank", "?")
    rank_gap = school.get("rank_gap", "?")
    subjects = school.get("subject_requirement", "")
    major_match = school.get("major_match_level", "")
    adj_risk = school.get("adjustment_risk_level", "")

    # Evidence summary
    evidence_text = ""
    if evidence:
        for i, ev in enumerate(evidence[:2], 1):
            evidence_text += f"\n资料{i}：{ev.get('summary', '')[:200]}（来源：{ev.get('source_name', '')}）"
    else:
        evidence_text = "\n（当前知识库未检索到该院校的官方资料）"

    return f"""请为以下院校专业组撰写深度分析（不少于600字）。

考生：{province}省 {score}分，位次{rank}，偏好{interests}，地域偏好{region_pref}

院校：{school_name}，{city}
推荐层级：{bucket_cn}
参考位次：{ref_rank}，位次差：{rank_gap}
选科要求：{subjects}
专业匹配度：{major_match}
调剂风险：{adj_risk}
{evidence_text}

请严格按以下结构输出（6段，每段不少于100字）：

【推荐结论】
一句话总结为什么推荐该校该专业组，点明该校在推荐方案中的定位和价值。

【位次适配分析】
分析用户位次{rank}与该专业组参考位次{ref_rank}的关系，说明为什么适合{ bucket_cn }层。位次差{rank_gap}意味着什么。

【学校与城市理解】
分析{school_name}的办学层次、学科特色，以及所在城市{city}对学习、实习、就业的影响。

【专业匹配分析】
分析该专业组内专业设置与学生偏好{interests}的匹配情况，指出优势和不足。

【风险分析】
分析调剂风险、选科限制、单科成绩要求等主要风险点。风险等级：{adj_risk}。

【具体操作建议】
给出填报该校时的具体操作建议，包括需要核验的事项、建议放在第几志愿、是否需要提前联系招生办等。

请直接按【标签】格式输出，不要加额外标题或编号。"""


def build_final_advice_prompt(
    user_info: Dict[str, Any],
    rush_schools: List[Dict[str, Any]],
    stable_schools: List[Dict[str, Any]],
    safe_schools: List[Dict[str, Any]],
) -> str:
    """Build prompt for final recommendations."""
    province = user_info.get("province", "")
    score = user_info.get("score", "")

    rush_names = "、".join(s.get("school_name", "") for s in rush_schools[:5])
    stable_names = "、".join(s.get("school_name", "") for s in stable_schools[:5])
    safe_names = "、".join(s.get("school_name", "") for s in safe_schools[:5])

    return f"""请为一份江苏高考志愿填报分析报告撰写最终填报建议（不少于300字）。

考生：{province}省 {score}分

冲刺候选：{rush_names}
稳妥候选：{stable_names}
保底候选：{safe_names}

要求：
1. 给出可执行的填报优先顺序建议
2. 指出需要家长重点讨论的关键决策点
3. 提醒提交前必须核验的事项
4. 说明冲刺层、稳妥层、保底层的填报策略
5. 不要使用"一定""保证"等绝对化表达

请直接输出建议正文，不要加标题。"""

"""
report_ai_writer.py — AI text generation for report narratives.

Calls LLM (DeepSeek or user's preferred model) to generate:
- Executive summary
- School deep dive analysis
- Strategy analysis
- Final advice

All output goes into report_json.ai_narratives and school_deep_dives[*].ai_analysis.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# API configuration — use DeepSeek for reliable Chinese output
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"  # Faster, cheaper for bulk AI generation

# Fallback: user's xiaomi mimo
MIMO_KEY = os.environ.get("MIMO_API_KEY", "")
MIMO_BASE = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_MODEL = "mimo-v2.5"

# How many schools get full AI analysis (rest get template)
MAX_DEEP_DIVE_SCHOOLS = 10


async def generate_ai_narratives(
    user_info: Dict[str, Any],
    recommendation_data: Dict[str, Any],
    school_evidence_map: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Generate all AI narratives for a report.

    Returns dict with:
        - executive_summary: str
        - score_positioning: str
        - strategy_analysis: str
        - final_advice: str
        - school_deep_dives: list of dict
    """
    from app.services.report_prompt_builder import (
        SYSTEM_ROLE,
        build_executive_summary_prompt,
        build_school_analysis_prompt,
        build_final_advice_prompt,
    )

    result = {
        "executive_summary": "",
        "score_positioning": "",
        "strategy_analysis": "",
        "bucket_analysis": "",
        "major_match_analysis": "",
        "adjustment_risk_analysis": "",
        "region_analysis": "",
        "final_advice": "",
        "school_deep_dives": [],
    }

    # 1. Executive summary (always generate)
    summary = recommendation_data.get("summary", {})
    prompt = build_executive_summary_prompt(user_info, summary)
    text = await _call_llm(SYSTEM_ROLE, prompt)
    if text:
        result["executive_summary"] = text

    # 2. Score positioning
    score_prompt = _build_score_positioning_prompt(user_info, summary)
    text = await _call_llm(SYSTEM_ROLE, score_prompt)
    if text:
        result["score_positioning"] = text

    # 3. Strategy analysis
    strategy_prompt = _build_strategy_prompt(user_info, summary)
    text = await _call_llm(SYSTEM_ROLE, strategy_prompt)
    if text:
        result["strategy_analysis"] = text

    # 4. School deep dives (top N schools)
    all_candidates = []
    for bucket, label in [("rush", "冲刺"), ("stable", "稳妥"), ("safe", "保底")]:
        for school in recommendation_data.get(bucket, [])[:MAX_DEEP_DIVE_SCHOOLS]:
            school["bucket"] = bucket
            all_candidates.append(school)

    for school in all_candidates[:MAX_DEEP_DIVE_SCHOOLS]:
        school_name = school.get("school_name", "")
        evidence = school_evidence_map.get(school_name, [])
        prompt = build_school_analysis_prompt(user_info, school, evidence)
        text = await _call_llm(SYSTEM_ROLE, prompt)

        deep_dive = _parse_school_analysis(text, school, evidence)
        result["school_deep_dives"].append(deep_dive)

    # 5. Final advice
    rush = recommendation_data.get("rush", [])[:5]
    stable = recommendation_data.get("stable", [])[:5]
    safe = recommendation_data.get("safe", [])[:5]
    prompt = build_final_advice_prompt(user_info, rush, stable, safe)
    text = await _call_llm(SYSTEM_ROLE, prompt)
    if text:
        result["final_advice"] = text

    return result


async def _call_llm(system: str, user_prompt: str) -> Optional[str]:
    """Call LLM API. Tries DeepSeek first, falls back to mimo."""
    import aiohttp

    # Try DeepSeek
    if DEEPSEEK_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{DEEPSEEK_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": DEEPSEEK_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2500,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return content.strip()
                    else:
                        logger.warning(f"DeepSeek API error: {resp.status}")
        except Exception as e:
            logger.warning(f"DeepSeek API call failed: {e}")

    # Fallback: mimo
    if MIMO_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{MIMO_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {MIMO_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": MIMO_MODEL,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2500,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return content.strip()
        except Exception as e:
            logger.warning(f"Mimo API call failed: {e}")

    logger.error("No LLM available for AI report generation")
    return None


def _build_score_positioning_prompt(
    user_info: Dict[str, Any],
    summary: Dict[str, Any],
) -> str:
    """Build prompt for score positioning analysis."""
    score = user_info.get("score", "")
    rank = user_info.get("rank", "")
    province = user_info.get("province", "")
    subject = user_info.get("subject_type", "")
    return f"""请撰写"成绩定位分析"段落（100-150字）。

考生：{province}省 {subject}，{score}分，位次{rank}

要求：
1. 解释为什么位次比分数更重要
2. 说明当前位次在填报中的意义
3. 不能只说"你的分数不错"，要有实质分析

直接输出正文。"""


def _build_strategy_prompt(
    user_info: Dict[str, Any],
    summary: Dict[str, Any],
) -> str:
    """Build prompt for strategy analysis."""
    rush_n = summary.get("rush_count", 0)
    stable_n = summary.get("stable_count", 0)
    safe_n = summary.get("safe_count", 0)
    total = summary.get("total_candidates", 0)
    return f"""请撰写"志愿策略分析"段落（100-150字）。

推荐方案：共{total}所，冲刺{rush_n}所、稳妥{stable_n}所、保底{safe_n}所

要求：
1. 解释冲刺层的作用和风险
2. 说明稳妥层为什么是主体
3. 说明保底层为什么不能省
4. 评价当前结构是否合理

直接输出正文。"""


def _parse_school_analysis(
    text: Optional[str],
    school: Dict[str, Any],
    evidence: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Parse LLM output into structured school deep dive."""
    if not text:
        text = "AI 解析暂不可用，请参考结构化数据。"

    # Simple section-based parsing
    sections = {
        "recommendation_conclusion": "",
        "rank_fit_analysis": "",
        "school_city_understanding": "",
        "major_group_analysis": "",
        "preference_match_analysis": "",
        "risk_analysis": "",
        "action_suggestion": "",
    }

    # Try to split by 【 markers
    markers = [
        "【推荐结论】", "【位次适配分析】", "【学校与城市理解】",
        "【专业匹配分析】", "【风险分析】", "【具体操作建议】",
    ]
    keys = [
        "recommendation_conclusion", "rank_fit_analysis",
        "school_city_understanding", "major_group_analysis",
        "risk_analysis", "action_suggestion",
    ]
    preference_match = ""

    for i, marker in enumerate(markers):
        if marker in text:
            start = text.index(marker) + len(marker)
            if i + 1 < len(markers):
                next_marker = markers[i + 1]
                if next_marker in text[start:]:
                    end = text.index(next_marker, start)
                    content = text[start:end].strip()
                else:
                    content = text[start:].strip()
            else:
                content = text[start:].strip()
            sections[keys[i]] = content

    # Merge 专业匹配 into both major_group and preference
    if sections.get("major_group_analysis"):
        preference_match = sections["major_group_analysis"]

    return {
        "school_name": school.get("school_name", ""),
        "school_logo_url": school.get("logo_url", ""),
        "school_badges": school.get("school_badges", []),
        "city": school.get("city", ""),
        "province": school.get("province", ""),
        "major_group_code": school.get("group_code", ""),
        "major_group_name": school.get("group_name", ""),
        "bucket": school.get("bucket", ""),
        "user_rank": school.get("user_rank", 0),
        "reference_rank": school.get("reference_rank", 0),
        "rank_gap": school.get("rank_gap", 0),
        "subject_requirement": school.get("subject_requirement", ""),
        "major_match_level": school.get("major_match_level", ""),
        "adjustment_risk_level": school.get("adjustment_risk_level", ""),
        "key_metrics": school.get("key_metrics", {}),
        "ai_analysis": {
            "recommendation_conclusion": sections["recommendation_conclusion"],
            "rank_fit_analysis": sections["rank_fit_analysis"],
            "school_city_understanding": sections["school_city_understanding"],
            "major_group_analysis": sections["major_group_analysis"],
            "preference_match_analysis": preference_match,
            "risk_analysis": sections["risk_analysis"],
            "action_suggestion": sections["action_suggestion"],
        },
        "rag_evidence": [
            {
                "title": ev.get("title", ""),
                "source_name": ev.get("source_name", ""),
                "source_url": ev.get("source_url", ""),
                "summary": ev.get("summary", "")[:300],
            }
            for ev in evidence[:3]
        ],
        "data_warnings": [],
    }

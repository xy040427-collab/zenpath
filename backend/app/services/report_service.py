"""
报告生成服务

将推荐结果转换为结构化报告数据，包含：
  - 基本信息摘要
  - 冲稳保策略分析
  - 推荐院校详情
  - 数据分析（分数分布、层次分布等）
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def generate_report_data(
    recommendations: Dict[str, Any],
    application_id: str,
) -> dict:
    """
    根据推荐结果生成完整报告数据。

    Args:
        recommendations: calculate_recommendations 的返回结果
        application_id: 对应的 application ID

    Returns:
        完整报告数据（JSON-serializable）
    """
    summary = recommendations.get("summary", {})
    rush = recommendations.get("rush", [])
    stable = recommendations.get("stable", [])
    safe = recommendations.get("safe", [])
    not_recommended = recommendations.get("not_recommended", [])

    all_valid = rush + stable + safe

    # ── 基本信息 ──
    basic_info = {
        "province": summary.get("province", ""),
        "subject_type": summary.get("subject_type", ""),
        "score": summary.get("user_score", 0),
        "rank": summary.get("user_rank", 0),
        "total_candidates": summary.get("total_candidates", 0),
        "match_rate": summary.get("match_rate", 0),
        "generated_at": datetime.utcnow().isoformat(),
        "application_id": application_id,
    }

    # ── 冲稳保策略 ──
    tier_distribution = {
        "冲刺": len(rush),
        "稳妥": len(stable),
        "保底": len(safe),
        "不推荐": len(not_recommended),
    }

    # ── 策略总结 ──
    strategy_summary = _build_strategy_summary(summary, rush, stable, safe)

    # ── 院校详情 ──
    school_details = all_valid[:50]  # 最多 50 条

    # ── 层次分布分析 ──
    level_distribution = _build_level_distribution(all_valid)

    # ── 省份分布 ──
    province_distribution = _build_province_distribution(all_valid)

    # ── 分数段分布 ──
    score_bands = _build_score_bands(all_valid, summary.get("user_score", 0))

    # ── RAG 官方资料摘要 ──
    rag_summary = _build_rag_summary(all_valid)

    return {
        "basic_info": basic_info,
        "strategy": {
            "summary": strategy_summary,
            "tier_distribution": tier_distribution,
            "recommended_total": len(all_valid),
        },
        "level_distribution": level_distribution,
        "province_distribution": province_distribution,
        "score_bands": score_bands,
        "rag_summary": rag_summary,
        "recommendations": school_details,
        "not_recommended": not_recommended[:10],
    }


def _build_strategy_summary(
    summary: dict,
    rush: list,
    stable: list,
    safe: list,
) -> str:
    """生成策略总结文字"""
    score = summary.get("user_score", 0)
    rank = summary.get("user_rank", 0)
    province = summary.get("province", "")
    match_rate = summary.get("match_rate", 0)

    parts = [
        f"基于您在{province}的{score}分（位次{rank}），采用位次法进行冲稳保分析。"
    ]

    if match_rate >= 80:
        parts.append("您的分数与推荐院校匹配度很高，有较大的选择空间。")
    elif match_rate >= 50:
        parts.append("匹配度良好，建议合理分配冲稳保比例。")
    else:
        parts.append("匹配度一般，建议适当降低期望，增加保底院校数量。")

    if rush:
        parts.append(f"冲刺院校{len(rush)}所，可大胆尝试略高于您位次的院校。")
    if stable:
        parts.append(f"稳妥院校{len(stable)}所，与您位次匹配度高，建议作为主力志愿。")
    if safe:
        parts.append(f"保底院校{len(safe)}所，确保有学可上。")

    parts.append("本报告仅供参考，最终请以各省教育考试院官方数据和高校招生章程为准。")
    return "".join(parts)


def _build_level_distribution(
    recommendations: List[dict],
) -> List[dict]:
    """统计各层次院校数量"""
    counts = {"985": 0, "211": 0, "双一流": 0, "普通": 0}
    for r in recommendations:
        level = r.get("school_level", "普通")
        if level in counts:
            counts[level] += 1
    return [
        {"level": k, "count": v, "label": k}
        for k, v in counts.items()
        if v > 0
    ]


def _build_province_distribution(
    recommendations: List[dict],
) -> List[dict]:
    """统计各省份院校分布"""
    from collections import Counter
    province_counts = Counter(r.get("province", "未知") for r in recommendations)
    return [
        {"province": k, "count": v}
        for k, v in province_counts.most_common(15)
    ]


def _build_score_bands(
    recommendations: List[dict],
    user_score: int,
) -> List[dict]:
    """
    按分数段分组（方便前端画图）

    band: 低于用户分数 N 分 / 等于 / 高于
    """
    bands = [
        {"label": f"+20以上", "min": user_score + 20, "max": 999, "count": 0},
        {"label": f"+10~20", "min": user_score + 10, "max": user_score + 20, "count": 0},
        {"label": f"0~+10", "min": user_score, "max": user_score + 10, "count": 0},
        {"label": f"-10~0", "min": user_score - 10, "max": user_score, "count": 0},
        {"label": f"-20~-10", "min": user_score - 20, "max": user_score - 10, "count": 0},
        {"label": f"-20以下", "min": 0, "max": user_score - 20, "count": 0},
    ]

    for r in recommendations:
        es = r.get("expected_score")
        if es is None:
            continue
        for band in bands:
            if band["min"] <= es < band["max"]:
                band["count"] += 1
                break

    return bands


def _build_rag_summary(recommendations: List[dict]) -> dict:
    """Aggregate RAG evidence from recommendation items into report summary.

    Extracts rag_evidence from each item (populated by jiangsu_recommend.py
    Phase 7) and produces:
      - data_availability: overall CHSI coverage stats
      - schools_with_profiles: schools that have school_profile in CHSI
      - schools_with_policies: schools that have admission_policy in CHSI
      - missing_schools: schools with no CHSI data at all
      - source_citations: unique CHSI source URLs found
    """
    schools_with_profile = []
    schools_with_policy = []
    schools_missing = []
    source_urls: set[str] = set()

    seen = set()
    for item in recommendations:
        school = item.get("school_name", "")
        if not school or school in seen:
            continue
        seen.add(school)

        rag = item.get("rag_evidence") or {}
        has_profile = rag.get("school_profile_available", False)
        has_policy = rag.get("admission_policy_available", False)
        sources = rag.get("sources") or []

        if not has_profile and not has_policy:
            schools_missing.append(school)
        else:
            if has_profile:
                schools_with_profile.append(school)
            if has_policy:
                schools_with_policy.append(school)

        for src in sources:
            url = src.get("source_url", "")
            if url:
                source_urls.add(url)

    return {
        "data_availability": {
            "total_unique_schools": len(seen),
            "schools_with_profile": len(schools_with_profile),
            "schools_with_policy": len(schools_with_policy),
            "schools_missing": len(schools_missing),
            "unique_source_urls": len(source_urls),
        },
        "schools_with_profiles": schools_with_profile[:20],
        "schools_with_policies": schools_with_policy[:20],
        "missing_schools": schools_missing[:20],
        "source_citations": sorted(source_urls)[:10],
        "disclaimer": "院校资料来源于教育部阳光高考平台 (gaokao.chsi.com.cn)，"
                       "仅作为院校背景参考，不参与录取机会计算。",
    }

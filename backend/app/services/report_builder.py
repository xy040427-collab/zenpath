"""
report_builder.py — 统一 Report JSON 构建器

从推荐结果、用户画像、专业组数据、趋势数据、RAG evidence 中
生成符合文档 Schema 的完整 Report JSON。

原则：
- 不编造就业率、录取概率、官方资料
- RAG 只用于官方资料解释和来源引用
- 无资料时明确提示
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.services.school_logo_service import get_school_logo

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "本报告基于历年投档线、一分一段表、招生计划、院校专业组明细、"
    "公开院校资料和 CHSI 官方信息进行分析。报告结果仅供志愿填报参考，"
    "不构成录取承诺。最终录取结果以各省教育考试院和高校实际录取结果为准。"
    "填报前请以最新招生计划、招生章程和省考试院志愿填报系统为准。"
)


def build_report_json(
    recommendation_data: Dict[str, Any],
    application: Any,
    plan_type: str = "free",
    report_id: str = "",
) -> Dict[str, Any]:
    """Build unified Report JSON per document schema.

    Args:
        recommendation_data: from recommendation_service.calculate_recommendations
        application: Application ORM object (has province, score, rank, subject_type, etc.)
        plan_type: free / basic / advanced / premium
        report_id: report identifier

    Returns:
        Full Report JSON matching document schema
    """

    # ── Extract data ──────────────────────────────────────────
    summary = recommendation_data.get("summary", {})
    rush = recommendation_data.get("rush", [])
    stable = recommendation_data.get("stable", [])
    safe = recommendation_data.get("safe", [])
    not_rec = recommendation_data.get("not_recommended", [])
    all_items = rush + stable + safe

    score = getattr(application, "score", 0) or summary.get("user_score", 0)
    rank = getattr(application, "rank", 0) or summary.get("user_rank", 0)
    province = getattr(application, "province", "") or summary.get("province", "")
    subject_type = getattr(application, "subject_type", "") or summary.get("subject_type", "")
    match_rate = summary.get("match_rate", 0)

    # ── Student Profile ───────────────────────────────────────
    student_profile = {
        "province": province,
        "subject_type": subject_type,
        "score": score,
        "rank": rank,
        "total_candidates": summary.get("total_candidates", 0),
        "strategy": summary.get("strategy", "均衡"),
        "generated_at": datetime.utcnow().isoformat(),
    }

    # ── Executive Summary ─────────────────────────────────────
    executive_summary = _build_executive_summary(score, rank, province, match_rate, rush, stable, safe)

    # ── Score Positioning ─────────────────────────────────────
    score_positioning = _build_score_positioning(score, rank, province, summary)

    # ── Volunteer Strategy ────────────────────────────────────
    volunteer_strategy = _build_strategy(rush, stable, safe, not_rec)

    # ── Bucket Summary ────────────────────────────────────────
    bucket_summary = {
        "rush": {"count": len(rush), "description": "冲刺院校 — 位次略高于你的院校，可大胆尝试"},
        "stable": {"count": len(stable), "description": "稳妥院校 — 与你位次匹配度高，建议作为主力"},
        "safe": {"count": len(safe), "description": "保底院校 — 确保有学可上"},
        "total_recommended": len(all_items),
    }

    # ── Key Candidates ────────────────────────────────────────
    key_candidates = _build_key_candidates(all_items, score)

    # ── Enrich with school logos ───────────────────────────────
    for candidate in key_candidates:
        logo = get_school_logo(
            candidate.get("school_name", ""),
            candidate.get("logo_slug", ""),
        )
        candidate["logo_url"] = logo["url"]
        candidate["logo_type"] = logo["type"]

    # ── School Deep Dives (placeholder, filled by AI writer) ──
    school_deep_dives = _build_school_deep_dives(all_items)

    # ── AI Narratives (placeholder, filled by AI writer) ───────
    ai_narratives = {
        "executive_summary": "",
        "score_positioning": "",
        "strategy_analysis": "",
        "bucket_analysis": "",
        "major_match_analysis": "",
        "adjustment_risk_analysis": "",
        "region_analysis": "",
        "final_advice": "",
    }

    # ── Major Match Analysis ──────────────────────────────────
    major_match = _build_major_match(all_items)

    # ── Adjustment Risk Analysis ──────────────────────────────
    adjustment_risk = _build_adjustment_risk(all_items)

    # ── Region Analysis ───────────────────────────────────────
    region_analysis = _build_region_analysis(all_items)

    # ── School Tier Analysis ──────────────────────────────────
    school_tier = _build_school_tier(all_items)

    # ── RAG Evidence Sections ─────────────────────────────────
    rag_sections = _build_rag_sections(all_items)

    # ── Risk Register ─────────────────────────────────────────
    risk_register = _build_risk_register(all_items, score, rank)

    # ── Final Recommendations ─────────────────────────────────
    final_recommendations = _build_final_recommendations(rush, stable, safe, score, rank)

    # ── Checklist ─────────────────────────────────────────────
    checklist = [
        "确认所有院校专业组的选科要求与你的选科是否匹配",
        "核对招生章程中是否有单科成绩、身体条件等特殊要求",
        "确认填报批次、志愿数量和投档规则",
        "冲稳保比例建议：冲 20-30%、稳 40-50%、保 20-30%",
        "至少填报 2 所保底院校，确保有学可上",
        "核对一分一段表确认位次无误",
        "最终以省教育考试院志愿填报系统为准",
    ]

    # ── Data Sources ──────────────────────────────────────────
    data_sources = [
        {"name": "历年投档线", "source": "各省教育考试院公开发布数据"},
        {"name": "一分一段表", "source": "各省教育考试院公开发布数据"},
        {"name": "院校专业组信息", "source": "招生计划与院校官网"},
        {"name": "院校资料", "source": "教育部阳光高考平台 (gaokao.chsi.com.cn)"},
        {"name": "招生章程", "source": "教育部阳光高考平台"},
    ]

    return {
        "report_id": report_id,
        "version": "v2",
        "report_type": "gaokao_volunteer_analysis",
        "plan_type": plan_type,
        "status": "ready",
        "created_at": datetime.utcnow().isoformat(),
        "student_profile": student_profile,
        "executive_summary": executive_summary,
        "score_positioning": score_positioning,
        "volunteer_strategy": volunteer_strategy,
        "bucket_summary": bucket_summary,
        "key_candidates": key_candidates,
        "school_deep_dives": school_deep_dives,
        "ai_narratives": ai_narratives,
        "major_match_analysis": major_match,
        "adjustment_risk_analysis": adjustment_risk,
        "region_analysis": region_analysis,
        "school_tier_analysis": school_tier,
        "rag_evidence_sections": rag_sections,
        "risk_register": risk_register,
        "final_recommendations": final_recommendations,
        "checklist": checklist,
        "data_sources": data_sources,
        "disclaimer": DISCLAIMER,
        "permission_snapshot": {"plan_type": plan_type},
    }


# ═══════════════════════════════════════════════════════════════
#  Private builders
# ═══════════════════════════════════════════════════════════════

def _build_executive_summary(
    score: int, rank: int, province: str, match_rate: float,
    rush: list, stable: list, safe: list,
) -> dict:
    opportunities = []
    risks = []

    if match_rate >= 80:
        opportunities.append("你的分数与推荐院校匹配度很高，有较大的选择空间")
    elif match_rate >= 50:
        opportunities.append("匹配度良好，建议合理分配冲稳保比例")
    else:
        opportunities.append("匹配度一般，建议适当降低期望")

    if rush:
        opportunities.append(f"可冲刺{rush[0].get('school_name','')}等{len(rush)}所院校")
    if stable:
        opportunities.append(f"{len(stable)}所稳妥院校可作为主力志愿")
    if safe:
        opportunities.append(f"{len(safe)}所保底院校确保录取安全")

    if len(safe) < 2:
        risks.append("保底院校不足 2 所，建议增加保底志愿")
    if match_rate < 50:
        risks.append("整体匹配度偏低，滑档风险较高")

    return {
        "headline": f"{province}考生 {score}分（位次{rank}）志愿填报分析",
        "key_finding": f"共推荐 {len(rush)+len(stable)+len(safe)} 所院校：冲刺 {len(rush)} 所、稳妥 {len(stable)} 所、保底 {len(safe)} 所",
        "opportunities": opportunities,
        "risks": risks,
        "next_step": "建议优先审阅稳妥区院校，确认专业组内专业是否可接受，并关注调剂风险",
    }


def _build_score_positioning(score: int, rank: int, province: str, summary: dict) -> dict:
    return {
        "score": score,
        "rank": rank,
        "province": province,
        "percentile": summary.get("percentile", ""),
        "total_candidates": summary.get("total_candidates", 0),
        "available_batch": "本科普通批",
        "note": "位次是志愿填报的核心依据，分数仅作参考",
    }


def _build_strategy(rush: list, stable: list, safe: list, not_rec: list) -> dict:
    return {
        "strategy_name": "位次法冲稳保",
        "description": "以你的位次为基准，向上冲、居中稳、向下保，形成阶梯式志愿结构",
        "ratio": f"冲{len(rush)} : 稳{len(stable)} : 保{len(safe)}",
        "tiers": {
            "rush": {"count": len(rush), "schools": [r.get("school_name","") for r in rush[:5]]},
            "stable": {"count": len(stable), "schools": [s.get("school_name","") for s in stable[:5]]},
            "safe": {"count": len(safe), "schools": [s.get("school_name","") for s in safe[:5]]},
        },
    }


def _build_key_candidates(items: list, user_score: int) -> list:
    result = []
    for item in items[:8]:
        es = item.get("expected_score", 0)
        tier = item.get("tier", "")
        result.append({
            "school_name": item.get("school_name", ""),
            "tier": tier,
            "group_name": item.get("major_group_name", ""),
            "estimated_score": es,
            "score_gap": es - user_score if es else 0,
            "school_level": item.get("school_level", ""),
            "province": item.get("province", ""),
            "city": item.get("city", ""),
            "logo_slug": item.get("logo_slug", ""),
            "rag_summary": (item.get("rag_evidence") or {}).get("school_profile_summary", "")[:200],
        })
    return result


def _build_major_match(items: list) -> dict:
    majors_found = set()
    for item in items:
        for m in item.get("majors", []) or []:
            if isinstance(m, str):
                majors_found.add(m)
    return {
        "major_directions": sorted(majors_found)[:20],
        "analysis_note": "以上为推荐专业组中包含的专业方向，请结合个人兴趣和就业前景综合判断",
        "data_disclaimer": "专业匹配分析基于院校专业组公开数据，如有疑问请查阅高校招生章程" if not majors_found else "",
    }


def _build_adjustment_risk(items: list) -> dict:
    risky = []
    for item in items:
        plan = item.get("major_group_plan_summary", {}) or {}
        adjust_rate = plan.get("adjustment_risk", "")
        if adjust_rate and adjust_rate != "低":
            risky.append({
                "school_name": item.get("school_name", ""),
                "group_name": item.get("major_group_name", ""),
                "risk_level": adjust_rate,
                "note": plan.get("adjustment_note", "建议关注招生章程中的调剂规则"),
            })
    return {
        "risk_groups": risky[:5],
        "summary": f"共 {len(risky)} 个专业组存在调剂风险" if risky else "未发现显著调剂风险",
        "disclaimer": "调剂风险基于专业组内专业录取数据估算，仅供参考。最终以高校招生章程和实际录取为准。",
        "insufficient_data_note": (
            "资料不足，建议以高校官网和省考试院公布信息为准" if not items else ""
        ),
    }


def _build_region_analysis(items: list) -> dict:
    from collections import Counter
    region_counter = Counter()
    for item in items:
        p = item.get("province", "未知")
        region_counter[p] += 1
    return {
        "province_distribution": [
            {"province": k, "count": v} for k, v in region_counter.most_common(15)
        ],
        "top_3_regions": [k for k, _ in region_counter.most_common(3)],
    }


def _build_school_tier(items: list) -> dict:
    from collections import Counter
    tier_counter = Counter()
    for item in items:
        level = item.get("school_level", "普通")
        tier_counter[level] += 1
    return {
        "tier_distribution": [
            {"tier": k, "count": v} for k, v in tier_counter.items()
        ],
        "total": len(items),
    }


def _build_rag_sections(items: list) -> list:
    sections = []
    seen = set()
    for item in items:
        school = item.get("school_name", "")
        if not school or school in seen:
            continue
        seen.add(school)
        rag = item.get("rag_evidence") or {}
        profile = rag.get("school_profile_summary", "")
        policy = rag.get("admission_policy_summary", "")
        if profile or policy:
            sections.append({
                "school_name": school,
                "profile": profile[:300],
                "policy": policy[:300],
                "sources": rag.get("sources", [])[:3],
            })
    if not sections:
        sections.append({
            "school_name": "",
            "profile": "资料不足，建议以高校官网和省考试院公布信息为准",
            "policy": "",
            "sources": [],
        })
    return sections[:10]


def _build_risk_register(items: list, score: int, rank: int) -> list:
    risks = []
    if len(items) < 10:
        risks.append({
            "risk_type": "推荐数量不足",
            "severity": "高",
            "description": f"仅匹配到 {len(items)} 条推荐，建议扩大院校选择范围",
            "mitigation": "降低分数线范围或放宽地区限制",
        })
    if rank > 50000:
        risks.append({
            "risk_type": "位次竞争激烈",
            "severity": "中",
            "description": f"位次 {rank} 处于竞争激烈区，需重点关注保底",
            "mitigation": "确保至少 3 所保底院校，关注新增院校和扩招信息",
        })
    # Check for RAG coverage
    schools_with_rag = sum(1 for item in items if item.get("rag_evidence"))
    if schools_with_rag < len(items) * 0.5:
        risks.append({
            "risk_type": "院校资料不完整",
            "severity": "低",
            "description": f"{len(items)-schools_with_rag} 所院校缺少官方资料，建议自行查阅",
            "mitigation": "访问 gaokao.chsi.com.cn 或各高校官网查询",
        })
    return risks


def _build_final_recommendations(rush: list, stable: list, safe: list, score: int, rank: int) -> list:
    recs = []
    recs.append({
        "step": 1,
        "heading": "优先审阅稳妥区",
        "description": f"稳妥区 {len(stable)} 所院校是最适合你位次的主力志愿，建议逐一核对专业组内专业",
    })
    recs.append({
        "step": 2,
        "heading": "合理配置冲刺志愿",
        "description": f"冲刺区 {len(rush)} 所院校可大胆尝试，但不要全部填冲刺，建议不超过 30%",
    })
    recs.append({
        "step": 3,
        "heading": "确保保底安全",
        "description": f"保底区 {len(safe)} 所院校，建议至少 2 所以上，确保不滑档",
    })
    recs.append({
        "step": 4,
        "heading": "最终以官方为准",
        "description": "所有推荐基于历史数据，最终请以省教育考试院志愿填报系统为准",
    })
    return recs


def _build_school_deep_dives(items: list) -> list:
    """Build school_deep_dives skeleton. AI writer fills ai_analysis later."""
    dives = []
    for item in items[:10]:
        logo = get_school_logo(
            item.get("school_name", ""),
            item.get("logo_slug", ""),
        )
        plan = item.get("major_group_plan_summary", {}) or {}
        dives.append({
            "school_name": item.get("school_name", ""),
            "school_logo_url": logo["url"],
            "school_logo_type": logo["type"],
            "school_badges": [item.get("school_level", "")] if item.get("school_level") else [],
            "city": item.get("city", ""),
            "province": item.get("province", ""),
            "major_group_code": item.get("group_code", ""),
            "major_group_name": item.get("major_group_name", ""),
            "bucket": item.get("tier", ""),
            "user_rank": 0,
            "reference_rank": item.get("reference_rank", 0),
            "rank_gap": item.get("rank_gap", 0),
            "subject_requirement": item.get("subject_requirement", ""),
            "major_match_level": item.get("major_match_level", ""),
            "adjustment_risk_level": plan.get("adjustment_risk", ""),
            "key_metrics": {
                "target_major_count": plan.get("target_major_count", 0),
                "total_major_count": plan.get("total_major_count", 0),
                "target_plan_count": plan.get("target_plan_count", 0),
                "total_plan_count": plan.get("total_plan_count", 0),
            },
            "ai_analysis": {
                "recommendation_conclusion": "",
                "rank_fit_analysis": "",
                "school_city_understanding": "",
                "major_group_analysis": "",
                "preference_match_analysis": "",
                "risk_analysis": "",
                "action_suggestion": "",
            },
            "rag_evidence": [],
            "data_warnings": [],
        })
    return dives

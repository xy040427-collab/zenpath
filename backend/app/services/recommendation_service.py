"""
冲稳保推荐算法服务 (Reach-Match-Safe Recommendation Engine)

核心逻辑（位次法）：
  1. 从 admission_lines 取该省份/科类的历年录取数据
  2. 对有数据的学校做精确概率计算
  3. 对无数据的学校按院校层次/排名做估算
  4. 概率分级：冲刺 30%-50% / 稳妥 50%-80% / 保底 ≥80%

用法：
  result = await calculate_recommendations(score, rank, province, subject_type, db)
"""

import uuid
import math
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AdmissionLine, School
from app.services.province_config import get_province_config

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────
# 院校层次基准位次估算（全国通用，各省可调）
# ────────────────────────────────────────────
# 这些是默认基准值，当缺少该省录取数据时用作回退估算
LEVEL_BASE_RANK_PERCENTILES = {
    "985": 0.05,      # 985 院校：全省前 5%
    "211": 0.15,      # 211 院校：全省前 15%
    "双一流": 0.25,   # 双一流：全省前 25%
    "普通": 0.60,     # 普通本科：全省前 60%
}

# 位次浮动范围（基于 ranking 在同层次内的位置微调）
RANKING_SPREAD_WITHIN_LEVEL = 0.5  # ±25%


def _estimate_admission_rank(
    school_ranking: int,
    school_level: str,
    total_candidates: int,
) -> int:
    """
    根据院校排名和层次估算录取位次（无录取数据时的回退方案）

    Args:
        school_ranking: 院校综合排名 (1-865)
        school_level: 985/211/双一流/普通
        total_candidates: 该省考生总数（估算）

    Returns:
        预估录取最低位次
    """
    base_percentile = LEVEL_BASE_RANK_PERCENTILES.get(school_level, 0.5)

    # 在同层次内微调：ranking 越小（排名越高）录取位次越前
    # 不同层次 ranking 范围不同，取 rank/max_rank 作为层次内相对位置
    level_max = {
        "985": 40,
        "211": 115,
        "双一流": 120,
        "普通": 900,
    }
    max_r = level_max.get(school_level, 900)
    position = min(school_ranking / max_r, 1.0) if max_r > 0 else 0.5

    # base_percentile 为中心，在 ±25% 范围内浮动
    p_min = base_percentile * (1 - RANKING_SPREAD_WITHIN_LEVEL / 2)
    p_max = base_percentile * (1 + RANKING_SPREAD_WITHIN_LEVEL / 2)
    p = p_min + (p_max - p_min) * position

    return max(1, int(total_candidates * p))


def _calc_probability_and_tier(
    user_rank: int,
    estimated_min_rank: int,
) -> tuple:
    """
    计算录取概率并分类

    概率模型（位次法）：
      - 用户位次 < 院校预估位次 → 用户更优秀 → 概率高
      - 用户位次 > 院校预估位次 → 院校更难进 → 概率低

    Args:
        user_rank: 用户省排名
        estimated_min_rank: 院校录取最低位次

    Returns:
        (probability_0_1, tier_name, match_score_0_100)
    """
    if estimated_min_rank <= 0:
        estimated_min_rank = 1

    # 用户位次 < 院校最低位次 → 用户排名更靠前 → 更容易录取
    if user_rank < estimated_min_rank:
        # 用户在最低位次之上，很有希望
        ratio = user_rank / estimated_min_rank
        # ratio ∈ (0, 1)，值越小越有把握
        probability = 1.0 - ratio * 0.3  # 最低 70%
    else:
        # 用户位次 >= 院校最低位次，有一定差距
        gap = (user_rank - estimated_min_rank) / max(estimated_min_rank, 1)
        probability = max(0.0, 1.0 - gap)

    probability = max(0.0, min(1.0, probability))

    # 分级
    if probability >= 0.80:
        tier = "保底"
    elif probability >= 0.50:
        tier = "稳妥"
    elif probability >= 0.30:
        tier = "冲刺"
    else:
        tier = "不推荐"

    # 匹配分 = 概率映射到 0-100
    match_score = round(probability * 100)

    return probability, tier, match_score


async def calculate_recommendations(
    score: int,
    rank: int,
    province: str,
    subject_type: str,
    db: AsyncSession,
    batch: str = "普通本科批",
    page: int = 1,
    page_size: int = 50,
) -> Dict[str, Any]:
    """
    核心推荐算法入口

    1. 先查 admission_lines 获取有历史数据的学校 → 精确匹配
    2. 再补充分数段内其他学校 → 估算匹配
    3. 合并结果，按概率降序排列，分类到 冲/稳/保
    """
    # ── 估算全省考生数（用于回退估算） ──
    # 从 admission_lines 最高位次推测
    rank_count_result = await db.execute(
        select(AdmissionLine.min_rank)
        .where(
            and_(
                AdmissionLine.province == province,
                AdmissionLine.subject_type == subject_type,
            )
        )
        .order_by(AdmissionLine.min_rank.desc())
        .limit(1)
    )
    known_max_rank = rank_count_result.scalar_one_or_none()
    total_candidates = known_max_rank * 3 if known_max_rank else 400000

    # ── Step 1: 查该省/科类的历年录取数据 ──
    line_q = select(AdmissionLine).where(
        and_(
            AdmissionLine.province == province,
            AdmissionLine.subject_type == subject_type,
            AdmissionLine.batch == batch,
        )
    )
    line_result = await db.execute(line_q)
    admission_lines = line_result.scalars().all()

    # 按学校名聚合取最新年份的最小位次
    school_admission_map: Dict[str, dict] = {}
    for al in admission_lines:
        name = al.university_name
        key = f"{name}|{al.major_group_name or ''}"
        if key not in school_admission_map or al.year > school_admission_map[key].get("year", 0):
            school_admission_map[key] = {
                "year": al.year,
                "min_score": al.min_score,
                "min_rank": al.min_rank,
                "major_group_name": al.major_group_name or "",
                "plan_count": al.plan_count or 0,
                "batch": al.batch or "普通本科批",
            }

    # ── Step 2: 获取所有学校 ──
    school_result = await db.execute(
        select(School).order_by(School.ranking.asc())
    )
    all_schools = school_result.scalars().all()

    # ── Step 3: 计算每所学校的录取概率 ──
    recommendations = []
    for school in all_schools:
        # 看是否有精确录取数据
        admission = school_admission_map.get(school.name, None)
        if not admission:
            # 没有精确数据也处理（部分匹配 major）
            for key, val in school_admission_map.items():
                if val["major_group_name"] == "" and key.startswith(school.name):
                    admission = val
                    break

        if admission and admission.get("min_rank"):
            estimated_min_rank = admission["min_rank"]
            has_exact_data = True
        else:
            # 回退估算
            estimated_min_rank = _estimate_admission_rank(
                school.ranking, school.level, total_candidates
            )
            has_exact_data = False

        probability, tier, match_score = _calc_probability_and_tier(
            rank, estimated_min_rank
        )

        # 只推荐概率 > 5% 的学校（太离谱的不显示）
        if probability < 0.05:
            continue

        item = {
            "id": str(uuid.uuid4().hex[:12]),
            "school_id": school.id,
            "school_name": school.name,
            "school_logo": school.logo_slug or school.slug,
            "province": school.province,
            "city": school.city,
            "school_type": school.type,
            "school_level": school.level,
            "school_ranking": school.ranking,
            "major_name": admission["major_group_name"] if admission else "",
            "tier": tier,
            "probability": round(probability, 2),
            "match_score": match_score,
            "expected_rank": estimated_min_rank,
            "expected_score": admission["min_score"] if admission else None,
            "reason": _generate_reason(tier, has_exact_data, admission),
            "has_exact_data": has_exact_data,
            "year": admission["year"] if admission else datetime.now().year,
            "tags": school.tags or [],
            "website": school.website or "",
        }
        recommendations.append(item)

    # ── Step 4: 按概率降序排列 ──
    recommendations.sort(key=lambda x: x["probability"], reverse=True)

    # ── Step 5: 分类 ──
    rush = [r for r in recommendations if r["tier"] == "冲刺"]
    stable = [r for r in recommendations if r["tier"] == "稳妥"]
    safe = [r for r in recommendations if r["tier"] == "保底"]
    not_recommended = [r for r in recommendations if r["tier"] == "不推荐"]

    # 限制每类数量
    rush = rush[:30]
    stable = stable[:30]
    safe = safe[:30]
    not_recommended = not_recommended[:15]

    # ── Step 6: 汇总统计 ──
    all_valid = rush + stable + safe
    match_rate = round(
        (len(stable) + len(safe)) / max(len(all_valid), 1) * 100
    )

    # 计算分数范围
    scores = [r["expected_score"] for r in all_valid if r["expected_score"]]
    max_score = max(scores) if scores else score + 15
    min_score = min(scores) if scores else score - 30

    summary = {
        "total_candidates": len(all_valid),
        "rush_count": len(rush),
        "stable_count": len(stable),
        "safe_count": len(safe),
        "max_score": max_score,
        "min_score": min_score,
        "estimated_rank_range": _format_rank_range(stable),
        "match_rate": match_rate,
        "user_score": score,
        "user_rank": rank,
        "province": province,
        "subject_type": subject_type,
    }

    return {
        "summary": summary,
        "rush": rush,
        "stable": stable,
        "safe": safe,
        "not_recommended": not_recommended,
    }


def _generate_reason(tier: str, has_exact_data: bool, admission: Optional[dict]) -> str:
    """生成推荐理由"""
    if tier == "保底":
        base = "录取概率较高，建议作为保底选择"
    elif tier == "稳妥":
        base = "录取概率适中，与你的位次较为匹配"
    elif tier == "冲刺":
        base = "有一定难度但值得尝试冲刺"
    else:
        base = "录取概率较低"

    if has_exact_data and admission:
        year = admission.get("year", "")
        min_rank = admission.get("min_rank", "")
        plan = admission.get("plan_count", "")
        detail = f"（参考{year}年最低位次{min_rank}）"
        if plan:
            detail += f"，计划招生{plan}人"
        base += detail + "）"
    else:
        base += "（基于院校层次估算，建议进一步查询官方数据）"

    return base


def _format_rank_range(stable: list) -> str:
    """格式化位次范围"""
    if not stable:
        return "暂无数据"
    ranks = [r["expected_rank"] for r in stable if r["expected_rank"]]
    if not ranks:
        return "暂无数据"
    return f"{min(ranks)}-{max(ranks)}"


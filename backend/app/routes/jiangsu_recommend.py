"""
POST /api/gaokao/jiangsu/recommend — 江苏院校专业组推荐 v2

重构目标：
- 大候选池先取再分层（不用 LIMIT 卡死）
- 位次驱动 + 综合评分公式
- 冲/稳/保/垫 四层 + 多样化解
- 选科匹配、专业偏好、风险标签、顾问式reason
- 策略模式：balanced / school_first / major_first / safe
- 无组内专业数据时正确标注 missing，不编造
- 所有推荐可溯源 source_url
"""

import asyncio
import json
import logging
from pathlib import Path
from functools import lru_cache
import math
import re
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rank_matcher import clean_school_name
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gaokao/jiangsu", tags=["江苏推荐"])


# ═══════════════════════════════════════════
#  Request / Response models
# ═══════════════════════════════════════════

class JiangsuRecommendRequest(BaseModel):
    year: int = Field(default=2025, ge=2022, le=2025, description="查询年份")
    subject_type: str = Field(
        default="物理等科目类",
        description="物理等科目类 | 历史等科目类（不允许其他值）",
    )
    score: int = Field(ge=100, le=750, description="高考分数")
    rank: Optional[int] = Field(default=None, ge=1, description="用户自填的全省位次（可选，优先级高于分数估算）")
    selected_subjects: list[str] = Field(
        default_factory=list, description="再选科目列表，如 [化学,生物]"
    )
    preferred_majors: list[str] = Field(
        default_factory=list, description="专业偏好，如 [计算机,人工智能]"
    )
    preferred_cities: list[str] = Field(
        default_factory=list, description="城市偏好，如 [南京,苏州]"
    )
    preferred_tiers: list[str] = Field(
        default_factory=list, description="学校层次偏好，如 [985,211,双一流]"
    )
    strategy: str = Field(
        default="balanced",
        description="推荐策略: balanced | school_first | major_first | city_first | safe",
    )
    top_n: int = Field(default=200, ge=50, le=500)
    user_id: Optional[str] = Field(default=None, description="用户ID，用于会员权限控制")


class JiangsuRecommendResponse(BaseModel):
    success: bool
    province: str = "江苏"
    subject_type: str = ""
    score: int = 0
    estimated_rank: Optional[int] = None
    recommendations: dict = Field(default_factory=dict)
    summary: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    data_note: str = ""
    debug: Optional[dict] = None


# ═══════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════

ELECTIVE_PARSE_MAP = {
    "不限":          {"required": [], "label": "不限"},
    "化学":          {"required": ["化学"], "label": "化学"},
    "生物":          {"required": ["生物"], "label": "生物"},
    "政治":          {"required": ["政治"], "label": "政治"},
    "地理":          {"required": ["地理"], "label": "地理"},
    "化学或生物":    {"required_any": ["化学", "生物"], "label": "化学或生物"},
    "化学和生物":    {"required": ["化学", "生物"], "label": "化学和生物"},
    "思想政治":      {"required": ["政治"], "label": "思想政治"},
}

MAJOR_CATEGORIES = {
    "计算机":    ["计算机科学与技术", "软件工程", "人工智能", "网络工程",
                  "信息安全", "物联网工程", "数字媒体技术", "数据科学与大数据技术"],
    "电子信息":  ["电子信息工程", "通信工程", "微电子", "光电信息", "集成电路", "电磁场", "自动化", "测控"],
    "医学":      ["临床医学", "口腔医学", "基础医学", "预防医学", "药学", "护理学", "中医学", "中药学"],
    "金融经济":  ["金融学", "经济学", "财政学", "保险学", "会计学", "财务管理", "国际经济与贸易", "审计学"],
    "法学":      ["法学", "知识产权", "政治学", "行政管理"],
    "机械":      ["机械工程", "车辆工程", "工业设计", "智能制造工程", "能源与动力工程"],
    "土木建筑":  ["土木工程", "建筑学", "城乡规划", "风景园林", "给排水科学与工程"],
    "数学物理":  ["数学与应用数学", "物理学", "统计学", "工程力学", "天文学"],
    "化学材料":  ["化学", "材料科学与工程", "化学工程与工艺", "高分子材料", "环境工程"],
    "生命科学":  ["生物科学", "生态学", "农学", "食品科学与工程", "生物医学工程"],
    "文学传媒":  ["汉语言文学", "新闻学", "传播学", "广告学", "英语", "日语", "翻译"],
    "管理":      ["工商管理", "人力资源管理", "市场营销", "物流管理", "公共管理"],
    "师范教育":  ["教育学", "小学教育", "学前教育", "特殊教育"],
}

# Broad fallback terms for matching when full major names aren't found
MAJOR_CATEGORY_FALLBACK = {
    "计算机":    ["计算机", "软件", "人工智能", "网络", "信息安全", "物联网", "数据科学"],
    "电子信息":  ["电子", "通信", "微电子", "光电", "集成电路", "自动化"],
    "医学":      ["临床", "口腔", "医学", "药学", "护理", "中医"],
    "金融经济":  ["金融", "经济", "财政", "保险", "会计", "财务", "国贸", "审计"],
    "法学":      ["法学", "知识产权", "政治"],
    "机械":      ["机械", "车辆", "智能制造", "能动"],
    "土木建筑":  ["土木", "建筑", "城乡规划", "风景园林", "给排水"],
    "数学物理":  ["数学", "物理", "统计", "力学", "天文"],
    "化学材料":  ["化学", "材料", "化工", "高分子", "环境"],
    "生命科学":  ["生物", "生态", "农学", "食品", "生物医学"],
    "文学传媒":  ["中文", "新闻", "传播", "广告", "英语", "日语", "翻译"],
    "管理":      ["管理", "工商", "人力", "市场", "物流", "公共"],
    "师范教育":  ["师范", "教育", "小学教育", "学前", "特殊教育"],
}

# 985 / 211 / 双一流 学校代码（江苏）
SCHOOL_TIERS = {
    "南京大学":          ("985", 1.0),
    "东南大学":          ("985", 1.0),
    "南京航空航天大学":  ("211", 0.9),
    "南京理工大学":      ("211", 0.9),
    "河海大学":          ("211", 0.85),
    "南京农业大学":      ("211", 0.8),
    "中国药科大学":      ("211", 0.8),
    "南京师范大学":      ("211", 0.8),
    "苏州大学":          ("211", 0.8),
    "江南大学":          ("211", 0.8),
    "中国矿业大学":      ("211", 0.8),
    "南京医科大学":      ("双一流", 0.78),
    "南京邮电大学":      ("双一流", 0.7),
    "南京信息工程大学":  ("双一流", 0.7),
    "南京林业大学":      ("双一流", 0.68),
    "南京中医药大学":    ("双一流", 0.68),
}

# 985 group pattern (non-Jiangsu schools detected by name prefix)
SCHOOL_TIER_PREFIXES = [
    ("北京大学", "985", 1.0), ("清华大学", "985", 1.0), ("复旦大学", "985", 0.95),
    ("上海交通大学", "985", 0.95), ("浙江大学", "985", 0.95), ("中国科学技术大学", "985", 0.95),
    ("中国人民大学", "985", 0.95), ("哈尔滨工业大学", "985", 0.9),
    ("西安交通大学", "985", 0.9), ("武汉大学", "985", 0.9), ("华中科技大学", "985", 0.9),
    ("中山大学", "985", 0.9), ("四川大学", "985", 0.88), ("山东大学", "985", 0.88),
    ("南开大学", "985", 0.88), ("天津大学", "985", 0.88), ("厦门大学", "985", 0.88),
    ("吉林大学", "985", 0.85), ("中南大学", "985", 0.85), ("湖南大学", "985", 0.85),
    ("重庆大学", "985", 0.85), ("电子科技大学", "985", 0.85), ("西北工业大学", "985", 0.85),
    ("兰州大学", "985", 0.8), ("东北大学", "985", 0.8), ("中国海洋大学", "985", 0.8),
    ("西北农林科技大学", "985", 0.78), ("中央民族大学", "985", 0.78),
    ("北京航空航天大学", "985", 0.92), ("北京理工大学", "985", 0.92),
    ("北京师范大学", "985", 0.9), ("华东师范大学", "985", 0.9),
]


def _get_school_tier(school_name: str) -> tuple[str, float]:
    """Return (tier_label, tier_score) for a school."""
    if school_name in SCHOOL_TIERS:
        return SCHOOL_TIERS[school_name]
    for prefix, tier, score in SCHOOL_TIER_PREFIXES:
        if school_name.startswith(prefix):
            return (tier, score)
    if "大学" in school_name and (school_name.startswith("南京") or school_name.startswith("江苏")):
        return ("省内公办", 0.55)
    return ("其他", 0.5)


# ═══════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════

def parse_elective(req_str: str) -> dict:
    """Parse elective_requirement string into structured form."""
    if not req_str:
        return {"required": [], "label": "需人工核验", "unparseable": True}
    req_str = req_str.strip()
    if req_str in ELECTIVE_PARSE_MAP:
        return dict(ELECTIVE_PARSE_MAP[req_str])
    if "和" in req_str:
        parts = re.split(r'[和、]', req_str)
        return {"required": [p.strip() for p in parts if p.strip()], "label": req_str}
    if "或" in req_str:
        parts = re.split(r'[或、]', req_str)
        return {"required_any": [p.strip() for p in parts if p.strip()], "label": req_str}
    if "不限" in req_str:
        return {"required": [], "label": "不限"}
    return {"required": [], "label": "需人工核验", "unparseable": True}


def check_elective_match(parsed: dict, user_subjects: list[str]) -> tuple[bool, str]:
    """Check if user's selected subjects satisfy elective requirement.
    Returns (matched: bool, note: str)."""
    if parsed.get("unparseable"):
        return True, "选科要求需人工核验"
    if parsed.get("required", []) or parsed.get("required_any", []):
        user_set = set(user_subjects)
        if "required" in parsed and parsed["required"]:
            if all(s in user_set for s in parsed["required"]):
                return True, "满足"
            missing = [s for s in parsed["required"] if s not in user_set]
            return False, f"缺少: {', '.join(missing)}"
        if "required_any" in parsed and parsed["required_any"]:
            if any(s in user_set for s in parsed["required_any"]):
                return True, "满足(任一)"
            return False, f"需任一: {', '.join(parsed['required_any'])}"
    return True, "不限"


def match_majors(
    mg_full_name: str, school_name: str, preferred_majors: list[str],
    actual_majors: list[str] | None = None,
) -> list[dict]:
    """Match user's major preferences against actual major names and group name."""
    if not preferred_majors:
        return []

    # If mg_full_name itself is a specific major name (not a group code like "XX专业组"),
    # treat it as a singleton actual_majors list for direct matching.
    # This handles the case where admission_lines stores specific majors in major_group_name.
    is_specific_major = ("专业组" not in (mg_full_name or ""))
    effective_majors = list(actual_majors) if actual_majors else []
    if is_specific_major and mg_full_name:
        effective_majors.append(mg_full_name)

    results = []

    # First: match against actual major names (from jiangsu_group_majors or from group name)
    if effective_majors:
        for pm in preferred_majors:
            for am in effective_majors:
                # Direct match
                if pm in am or am in pm:
                    results.append({
                        "major_name": am,
                        "match_score": 0.90,
                        "match_type": "exact_major_match",
                        "reason": f"专业'{am}'精确匹配用户偏好'{pm}'",
                    })
                    break
                # Category-level match — try primary keywords first, then fallback
                for kw_list, match_score, match_type in [
                    (MAJOR_CATEGORIES, 0.70, "category_major_match"),
                    (MAJOR_CATEGORY_FALLBACK, 0.55, "category_fallback_match"),
                ]:
                    matched = False
                    for cat, kws in kw_list.items():
                        if pm in cat or cat in pm or any(pm in kw or kw in pm for kw in kws[:4]):
                            if any(kw in am for kw in kws):
                                results.append({
                                    "major_name": am,
                                    "match_score": match_score,
                                    "match_type": match_type,
                                    "reason": f"专业'{am}'属于'{cat}'大类，匹配用户偏好'{pm}'",
                                })
                                matched = True
                                break
                    if matched:
                        break

    # Fallback: match against group name + school context
    search_text = (mg_full_name or "") + " " + (school_name or "")
    for pm in preferred_majors:
        if pm in search_text:
            # Avoid duplicate if already matched via actual majors
            if not any(r["major_name"] == pm for r in results):
                results.append({
                    "major_name": pm,
                    "match_score": 0.70,
                    "match_type": "group_name_match",
                    "reason": f"专业组名称或院校名称包含'{pm}'",
                })
            continue
        # Category match
        for kw_list in [MAJOR_CATEGORIES, MAJOR_CATEGORY_FALLBACK]:
            for cat, kws in kw_list.items():
                if pm in cat or cat in pm or any(pm in kw or kw in pm for kw in kws[:4]):
                    matched_kw = [kw for kw in kws if kw in search_text]
                    if matched_kw and not any(r["major_name"] == pm for r in results):
                        results.append({
                            "major_name": pm,
                            "match_score": 0.45,
                            "match_type": "category_inferred",
                            "reason": f"专业方向'{cat}'匹配（关键词: {', '.join(matched_kw[:3])})",
                        })
                        break
    return results


async def fetch_group_majors_batch(
    db: AsyncSession,
    groups: list[tuple[str, str]],  # [(school_name, major_group_full_name), ...]
) -> dict[tuple[str, str], dict]:
    """
    Batch-fetch actual majors for trend groups from jiangsu_group_majors.
    Returns dict keyed by (school_name_clean, major_group_title): {plan_count, majors: [...]}
    Only fetches 2022 data (complete) for reliable major lists.
    Uses multiple matching strategies: exact school name, stripped-location school name.
    """
    if not groups:
        return {}

    # Deduplicate groups
    unique_groups = list(dict.fromkeys(groups))

    # Build conditions: try exact school name + LIKE pattern for location-stripped matching
    conditions = []
    params = {}
    for i, (sn, mgfn) in enumerate(groups):
        conditions.append(
            f"((m.major_group_title = :mgfn{i} OR m.major_group_title LIKE :mgfn_like{i}) AND "
            f"(m.school_name_clean = :sn{i} OR m.school_name_clean LIKE :snlike{i}))"
        )
        params[f"sn{i}"] = sn
        params[f"mgfn{i}"] = mgfn
        params[f"mgfn_like{i}"] = mgfn + "%"  # match "XX专业组(不限)" → "XX专业组(不限)(南京校区)"
        params[f"snlike{i}"] = sn + "%"  # match "中国药科大学" → "中国药科大学(南京)"

    batch_size = 500
    result = {}
    # search_key_map: maps (school_name, search_group_name) → DB (school_name_clean, major_group_title)
    # so the caller can look up using the original search key
    search_key_map: dict[tuple, tuple] = {}
    for i, (sn, mgfn) in enumerate(groups):
        search_key_map[(sn, mgfn)] = None  # will be populated when matched

    for batch_start in range(0, len(conditions), batch_size):
        batch_conds = conditions[batch_start:batch_start + batch_size]
        where_clause = " OR ".join(batch_conds)

        rows = await db.execute(text(f"""
            SELECT m.school_name_clean, m.major_group_title,
                   m.major_name, m.major_plan_count, m.group_plan_count,
                   m.major_name_clean
            FROM jiangsu_group_majors m
            WHERE m.year = 2022
              AND ({where_clause})
            ORDER BY m.school_name_clean, m.major_group_title, m.major_code
        """), params)
        for row in rows.fetchall():
            db_sn, db_mgt = row[0], row[1]
            key = (db_sn, db_mgt)
            if key not in result:
                result[key] = {"plan_count": row[4] or 0, "majors": []}
            result[key]["majors"].append({
                "major_name": row[2] or "",
                "plan_count": row[3] or 0,
                "major_name_clean": row[5] or "",
            })
            # Record search-key → DB-key mapping for caller lookup
            for (s_sn, s_mgfn), _ in search_key_map.items():
                if (db_sn == s_sn or db_sn.startswith(s_sn)) and (db_mgt == s_mgfn or db_mgt.startswith(s_mgfn)):
                    search_key_map[(s_sn, s_mgfn)] = key

    # Copy result entries under search keys so caller finds them
    for search_key, db_key in search_key_map.items():
        if db_key and db_key in result and search_key not in result:
            result[search_key] = result[db_key]

    return result


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))

def _safe_div(a, b, default=0.0):
    return a / b if b else default


# ═══════════════════════════════════════════
#  Bucketing
#  rank-aware adjustment)
# ═══════════════════════════════════════════

def classify_bucket(
    rank_delta_ratio: float, user_rank: int, strategy: str
) -> Optional[str]:
    """
    Classify into 冲/稳/保/垫 based on rank_delta_ratio.
    Adjust thresholds for high-score users where rank numbers are small.
    """
    # Base thresholds
    if strategy == "safe":
        chong_hi, wen_hi, bao_hi, dian_hi = -0.05, 0.15, 0.40, 0.80
    else:
        chong_hi, wen_hi, bao_hi, dian_hi = -0.03, 0.12, 0.35, 0.65

    # High-score adjustment: when user_rank <= 10000, widen windows
    if user_rank <= 5000:
        chong_hi = -0.06
        wen_hi = 0.18
        bao_hi = 0.45
        dian_hi = 0.85
    elif user_rank <= 10000:
        chong_hi = -0.04
        wen_hi = 0.15
        bao_hi = 0.40
        dian_hi = 0.75

    if rank_delta_ratio < -0.35:
        return None  # too far
    elif rank_delta_ratio <= chong_hi:
        return "冲"
    elif rank_delta_ratio <= wen_hi:
        return "稳"
    elif rank_delta_ratio <= bao_hi:
        return "保"
    elif rank_delta_ratio <= dian_hi:
        return "垫"
    return None


# ═══════════════════════════════════════════
#  Scoring
# ═══════════════════════════════════════════

def compute_total_score(
    rank_delta_ratio: float,
    rank_volatility: Optional[float],
    years_available: int,
    elective_match: bool,
    major_match_count: int,
    major_match_max: float,
    city_match: float,
    school_tier_score: float,
    tier_match: float = 0.0,
    strategy: str = "balanced",
) -> dict:
    """
    Composite scoring. Weights adjust dynamically based on strategy:
      balanced:   rank 0.38 + trend 0.22 + elective 0.15 + major 0.08 + city 0.05 + confidence 0.12
      school_first: rank 0.30 + trend 0.18 + elective 0.12 + major 0.05 + city 0.03 + tier 0.20 + confidence 0.12
      major_first: rank 0.25 + trend 0.15 + elective 0.12 + major 0.25 + city 0.03 + confidence 0.20
      city_first:  rank 0.28 + trend 0.15 + elective 0.12 + major 0.08 + city 0.22 + confidence 0.15
    """
    # rank_fit: closer to 0 = better (稳)
    abs_ratio = abs(rank_delta_ratio)
    if abs_ratio <= 0.03:
        rank_fit = 0.95
    elif abs_ratio <= 0.10:
        rank_fit = 0.80
    elif abs_ratio <= 0.20:
        rank_fit = 0.60
    elif abs_ratio <= 0.35:
        rank_fit = 0.40
    else:
        rank_fit = 0.20

    # trend_stability
    if rank_volatility is None:
        trend_stability = 0.5
    else:
        trend_stability = _clamp(1.0 - rank_volatility * 2.5, 0.1, 1.0)

    subject_match = 1.0 if elective_match else 0.0
    major_match = min(major_match_max / 0.85, 1.0) if major_match_max > 0 else 0.0
    # Use tier_match (user preference match) when available, else fall back to raw school tier score
    tier_score_val = tier_match if tier_match > 0 else school_tier_score

    if years_available >= 4: data_confidence = 1.0
    elif years_available == 3: data_confidence = 0.85
    elif years_available == 2: data_confidence = 0.65
    else: data_confidence = 0.35

    # Strategy-dependent weights
    if strategy == "school_first":
        w_rank, w_trend, w_elective, w_major, w_city, w_tier, w_conf = 0.25, 0.15, 0.10, 0.05, 0.05, 0.30, 0.10
    elif strategy == "major_first":
        w_rank, w_trend, w_elective, w_major, w_city, w_tier, w_conf = 0.25, 0.15, 0.12, 0.25, 0.03, 0.05, 0.15
    elif strategy == "city_first":
        w_rank, w_trend, w_elective, w_major, w_city, w_tier, w_conf = 0.25, 0.15, 0.12, 0.08, 0.22, 0.05, 0.13
    else:  # balanced
        w_rank, w_trend, w_elective, w_major, w_city, w_tier, w_conf = 0.34, 0.20, 0.14, 0.08, 0.05, 0.08, 0.11

    total = (
        rank_fit * w_rank
        + trend_stability * w_trend
        + subject_match * w_elective
        + major_match * w_major
        + city_match * w_city
        + tier_score_val * w_tier
        + data_confidence * w_conf
    )

    return {
        "total_score": round(total, 4),
        "score_breakdown": {
            "rank_fit": round(rank_fit, 4),
            "trend_stability": round(trend_stability, 4),
            "subject_match": round(subject_match, 4),
            "major_match": round(major_match, 4),
            "city_match": round(city_match, 4),
            "data_confidence": round(data_confidence, 4),
            "school_tier": round(tier_score_val, 4),
        },
    }


# ═══════════════════════════════════════════
#  Risk tags
# ═══════════════════════════════════════════

def generate_risk_tags(
    bucket: str,
    elective_match: bool,
    elective_note: str,
    years_available: int,
    rank_volatility: Optional[float],
    has_majors: bool,
    rank_delta_ratio: float,
) -> list[str]:
    tags = []
    if years_available == 1:
        tags.append("仅一年数据，参考价值有限")
    if rank_volatility is not None:
        if rank_volatility > 0.15:
            tags.append("位次波动较大")
        elif rank_volatility < 0.05 and years_available >= 3:
            tags.append("位次波动较小")
    if not elective_match:
        tags.append("选科不满足")
    elif "需人工核验" in elective_note:
        tags.append("选科要求需人工核验")
    if not has_majors:
        tags.append("缺少组内专业清单")
        tags.append("可能存在调剂风险")
    if bucket == "冲":
        tags.append("冲刺风险较高")
        if rank_delta_ratio < -0.15:
            tags.append("录取难度较大")
    elif bucket == "稳":
        if rank_volatility and rank_volatility > 0.10:
            tags.append("稳妥但有波动")
        else:
            tags.append("稳妥匹配")
    elif bucket in ("保", "垫"):
        tags.append("保底安全度较高")
    return tags


def risk_level(bucket: str, elective_match: bool, rank_volatility: Optional[float]) -> str:
    if not elective_match:
        return "high"
    if bucket == "冲":
        return "high"
    if bucket == "垫":
        return "low"
    if rank_volatility and rank_volatility > 0.15:
        return "medium"
    return "low" if bucket == "保" else "medium"


# ═══════════════════════════════════════════
#  Reason generation (data-driven, consultant style)
# ═══════════════════════════════════════════

def generate_reason(
    bucket: str,
    school_name: str,
    mg_full_name: str,
    rank_delta: int,
    rank_delta_ratio: float,
    user_rank: int,
    latest_year: int,
    latest_min_rank: int,
    latest_min_score: int,
    years_available: int,
    rank_volatility: Optional[float],
    rank_best: Optional[int],
    rank_worst: Optional[int],
    elective_match: bool,
    elective_note: str,
    matched_majors: list,
    has_majors: bool,
    school_tier: str,
) -> str:
    parts = []

    # 1. Why this bucket
    delta_pct = abs(int(rank_delta_ratio * 100))
    if rank_delta < 0:
        parts.append(
            f"该专业组{latest_year}年最低投档位次约{latest_min_rank}，"
            f"你当前位次约{user_rank}，需前进约{delta_pct}%才能达到往年最低线，"
            f"因此归入「{bucket}」"
        )
    elif bucket == "稳":
        parts.append(
            f"该专业组{latest_year}年最低投档位次约{latest_min_rank}，"
            f"与你当前位次{user_rank}接近，归入「稳」"
        )
    else:
        parts.append(
            f"该专业组{latest_year}年最低投档位次约{latest_min_rank}，"
            f"你当前位次{user_rank}优于往年最低位次，"
            f"因此归入「{bucket}」"
        )

    # 2. Trend
    if years_available >= 3 and rank_volatility is not None:
        if rank_volatility < 0.05:
            parts.append(f"近{years_available}年位次波动较小，趋势稳定")
        elif rank_volatility < 0.15:
            parts.append(f"近{years_available}年位次有一定波动，但整体可参考")
        else:
            parts.append(f"近{years_available}年位次波动较大，需注意趋势变化")
    elif years_available == 2:
        parts.append("仅两年数据，趋势参考有限")
    else:
        parts.append("仅一年数据，趋势参考有限")

    # 3. Elective
    if elective_match:
        if elective_note not in ("满足", "满足(任一)", "不限"):
            parts.append(f"选科: {elective_note}")
    else:
        parts.append(f"⚠️ 选科不满足: {elective_note}")

    # 4. Major match
    if matched_majors:
        major_names = [m["major_name"] for m in matched_majors[:3]]
        parts.append(f"你偏好的{'/'.join(major_names)}方向有匹配")
    elif not has_majors:
        parts.append("缺少组内完整专业清单，暂不能确认是否包含你偏好的专业方向")

    # 5. School tier context
    if school_tier in ("985", "211"):
        parts.append(f"该院校为{school_tier}高校")

    # 6. Risk note
    if not has_majors:
        parts.append("建议结合招生计划核验组内具体专业和调剂风险")

    return "；".join(parts)


# ═══════════════════════════════════════════
#  Main endpoint
# ═══════════════════════════════════════════

@router.post("/recommend")
async def jiangsu_recommend(
    body: JiangsuRecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    江苏院校专业组推荐 — 冲/稳/保/垫 四层

    流程：分数→位次→大候选池→选科过滤→分层→评分→去重→排序→返回
    """
    year = body.year
    subj = body.subject_type
    score = body.score
    user_rank_input = body.rank  # user-provided rank (optional)
    user_subjects = set(body.selected_subjects or [])
    preferred_majors = body.preferred_majors or []
    preferred_cities = [c.strip() for c in (body.preferred_cities or []) if c.strip()]
    preferred_tiers = [t.strip() for t in (body.preferred_tiers or []) if t.strip()]
    strategy = body.strategy if body.strategy in ("balanced", "school_first", "major_first", "safe", "city_first") else "balanced"

    # ── Validate subject_type ──
    if subj not in ("物理等科目类", "历史等科目类"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"subject_type 必须是「物理等科目类」或「历史等科目类」，收到: {subj}",
            },
        )

    debug = defaultdict(int)

    # ── Step 1: 分数 → 位次（一次查询，用于参考和兜底）──
    rank_result = await db.execute(
        text("""
            SELECT score, cumulative_rank
            FROM gaokao_score_segments
            WHERE year = :y AND subject_type = :s AND score <= :sc
            ORDER BY score DESC LIMIT 1
        """),
        {"y": year, "s": subj, "sc": score},
    )
    rank_row = rank_result.fetchone()
    estimated_score, estimated_rank_from_score = None, None
    if rank_row:
        estimated_score, estimated_rank_from_score = rank_row[0], rank_row[1]

    # Determine final user_rank and rank_source
    rank_source = ""
    rank_warning = None
    if user_rank_input and user_rank_input > 0:
        user_rank = user_rank_input
        rank_source = "user_input"
        # Check discrepancy if we have an estimate
        if estimated_rank_from_score and estimated_rank_from_score > 0:
            ratio = abs(user_rank - estimated_rank_from_score) / estimated_rank_from_score
            if ratio > 0.05:
                rank_warning = (
                    f"你输入的位次（{user_rank}）与一分一段表估算位次（{estimated_rank_from_score}）"
                    f"差异较大（{ratio*100:.1f}%），请确认科类、年份或位次是否填写正确。"
                )
        user_score = estimated_score or score
    elif estimated_rank_from_score:
        user_rank = estimated_rank_from_score
        rank_source = "score_segment_estimated"
        user_score = estimated_score
    else:
        return {
            "success": False,
            "message": f"未找到{year}年{subj}{score}分对应的位次数据",
            "province": "江苏",
        }

    debug["user_rank"] = user_rank
    debug["rank_source"] = rank_source

    # ── Step 2: 大候选池（不 LIMIT）──
    # 取所有同 subject_type 且 latest_min_rank > 0 的记录
    trends_result = await db.execute(
        text("""
            SELECT t.school_code, t.school_name, t.major_group_code,
                   t.major_group_full_name, t.elective_requirement,
                   t.years_available, t.latest_year, t.latest_min_score,
                   t.latest_min_rank, t.rank_avg, t.rank_best, t.rank_worst,
                   t.rank_change_latest_vs_prev, t.rank_volatility,
                   t.score_avg, t.score_best, t.score_worst,
                   r.source_url
            FROM jiangsu_group_trends t
            LEFT JOIN jiangsu_admission_group_rank r
              ON r.school_code = t.school_code
             AND r.major_group_code = t.major_group_code
             AND r.year = t.latest_year
             AND r.subject_type = t.subject_type
            WHERE t.subject_type = :subj
              AND t.latest_min_rank > 0
        """),
        {"subj": subj},
    )
    all_trends = trends_result.fetchall()
    debug["candidate_pool"] = len(all_trends)

    if not all_trends:
        return {
            "success": False,
            "message": f"未找到{subj}的院校专业组数据",
            "province": "江苏",
        }

    # ── Step 2.5: 批量拉取组内专业数据 ──
    # Build lookup keyed by (school_name_clean, major_group_title)
    # Also try stripped school names (without parenthetical annotations)
    group_keys = []
    for row in all_trends:
        sc_name = clean_school_name(row[1] or "")
        mg_full = clean_school_name(row[3] or "")
        group_keys.append((sc_name, mg_full))

    major_lookup = await fetch_group_majors_batch(db, group_keys)

    # Build secondary lookup: map stripped-school-name keys for use in the loop
    # (DB returns keys with original school_name_clean, but trends use stripped names)
    major_lookup_stripped = {}
    for (sn, mgt), data in major_lookup.items():
        sn_stripped = re.sub(r'[（(][^）)]*[）)]$', '', sn).strip()
        if sn_stripped and sn_stripped != sn:
            key = (sn_stripped, mgt)
            if key not in major_lookup_stripped:
                major_lookup_stripped[key] = data

    # ── Step 2.6: Build school→city mapping for accurate city matching ──
    school_city_map: dict[str, str] = {}
    school_province_map: dict[str, str] = {}
    schools_result = await db.execute(
        text("SELECT name, city, province FROM schools WHERE city IS NOT NULL AND city != ''")
    )
    for row in schools_result.fetchall():
        sn, city, province = row[0], row[1], row[2]
        if sn:
            school_city_map[sn] = city
            school_province_map[sn] = province
    # Also index by clean name (strip parenthetical suffixes)
    schools_stripped = {}
    for sn in list(school_city_map.keys()):
        stripped = re.sub(r'[（(][^）)]*[）)]$', '', sn).strip()
        if stripped and stripped != sn and stripped not in school_city_map:
            schools_stripped[stripped] = school_city_map[sn]
    school_city_map.update(schools_stripped)

    def _lookup_school_city(school_name: str) -> str | None:
        """Look up city for a school name, trying exact, stripped, and prefix matches."""
        if not school_name:
            return None
        # Exact match
        if school_name in school_city_map:
            return school_city_map[school_name]
        # Stripped match (remove parenthetical)
        stripped = re.sub(r'[（(][^）)]*[）)]$', '', school_name).strip()
        if stripped in school_city_map:
            return school_city_map[stripped]
        # Longest prefix match among canonical names (for医学院/校区 cases)
        best, best_len = None, 0
        for cname, ccity in school_city_map.items():
            if school_name.startswith(cname) and len(cname) > best_len:
                best, best_len = ccity, len(cname)
        return best

    has_majors = len(major_lookup) > 0
    debug["groups_with_major_data"] = len(major_lookup)

    # ── Step 3: 分类 + 过滤 + 评分 ──
    recommendations = {"冲": [], "稳": [], "保": [], "垫": []}
    not_matched_items = []  # elective不满足的放入这里

    for row in all_trends:
        (sc_code, sc_name, mg_code, mg_full, elective_req,
         yrs, lyr, lms, lmr, ravg, rbest, rworst, rchg, rvol,
         savg, sbest, sworst, source_url) = row

        # Normalize corrupted school names (both school_name and major_group_name)
        sc_name = clean_school_name(sc_name or "")
        mg_full = clean_school_name(mg_full or "")

        if not lmr or lmr <= 0:
            continue

        rank_delta = lmr - user_rank
        rank_delta_ratio = _safe_div(rank_delta, user_rank)

        # Bucket
        bucket = classify_bucket(rank_delta_ratio, user_rank, strategy)
        if bucket is None:
            debug["filtered_by_bucket"] += 1
            continue

        # Elective
        elective_parsed = parse_elective(elective_req or "")
        elective_ok, elective_note = check_elective_match(elective_parsed, list(user_subjects))

        # Major matching — use actual major names if available
        group_major_data = major_lookup.get((sc_name, mg_full)) or major_lookup_stripped.get((sc_name, mg_full))
        actual_major_names = [m["major_name"] for m in group_major_data["majors"]] if group_major_data else None
        group_plan_count = group_major_data["plan_count"] if group_major_data else 0
        matched = match_majors(mg_full or "", sc_name or "", preferred_majors, actual_major_names)
        major_max = max((m["match_score"] for m in matched), default=0)

        # City matching — use database school→city lookup
        city_match = 0.0
        if preferred_cities:
            school_city = _lookup_school_city(sc_name or "")
            if school_city and school_city in preferred_cities:
                city_match = 0.9  # direct city match
            elif school_city:
                # Check province-level match
                school_prov = school_province_map.get(sc_name or "", "")
                province_cities = {
                    "北京": ["北京"], "天津": ["天津"], "上海": ["上海"], "重庆": ["重庆"],
                    "江苏": ["南京","苏州","无锡","常州","镇江","扬州","南通","徐州","泰州","盐城","淮安","连云港","宿迁"],
                    "浙江": ["杭州","宁波","温州","嘉兴","湖州","绍兴","金华","台州"],
                    "广东": ["广州","深圳","珠海","佛山","东莞","中山"],
                    "湖北": ["武汉","宜昌","襄阳"],
                    "四川": ["成都","绵阳","宜宾"],
                    "陕西": ["西安","咸阳","宝鸡"],
                    "湖南": ["长沙","株洲","湘潭"],
                    "山东": ["济南","青岛","烟台","威海"],
                    "辽宁": ["沈阳","大连","鞍山","抚顺"],
                    "黑龙江": ["哈尔滨"],
                    "吉林": ["长春","吉林"],
                    "福建": ["福州","厦门"],
                    "安徽": ["合肥"],
                    "河南": ["郑州"],
                    "河北": ["石家庄","保定","唐山"],
                    "江西": ["南昌"],
                    "甘肃": ["兰州"],
                    "新疆": ["乌鲁木齐"],
                    "云南": ["昆明"],
                    "贵州": ["贵阳"],
                    "广西": ["南宁"],
                    "海南": ["海口"],
                    "宁夏": ["银川"],
                    "青海": ["西宁"],
                    "西藏": ["拉萨"],
                    "内蒙古": ["呼和浩特"],
                    "山西": ["太原"],
                }
                prov_cities = province_cities.get(school_prov, [])
                if any(c in preferred_cities for c in prov_cities):
                    city_match = 0.6  # same province, different city
                else:
                    city_match = 0.2  # not in preferred region
        else:
            city_match = 0.5  # no preference = neutral

        # ── Hard city filter ──
        # When user explicitly selected preferred cities, only keep schools
        # in those cities (or same-province fallback). Exclude everything else.
        if preferred_cities and city_match < 0.5:
            debug["filtered_by_city"] += 1
            continue

        # School tier
        tier_label, tier_score = _get_school_tier(sc_name or "")
        # Compute tier_match based on user's preferred tiers
        tier_match = 0.0
        if preferred_tiers:
            if tier_label in preferred_tiers or (tier_label == "双一流" and "双一流" in preferred_tiers):
                tier_match = 1.0
            elif tier_label == "省重点" and "省重点" in preferred_tiers:
                tier_match = 0.8
            elif tier_label == "公办本科" and "公办本科" in preferred_tiers:
                tier_match = 0.5

        # Score
        scoring = compute_total_score(
            rank_delta_ratio, rvol, yrs or 1,
            elective_ok, len(matched), major_max,
            city_match, tier_score, tier_match, strategy,
        )

        # ── Major preference penalty ──
        # When user has explicit major preferences but this group matched zero,
        # apply a penalty to push it below groups that DO match.
        if preferred_majors and len(matched) == 0:
            penalty = 0.65  # keep 65% of original score
            scoring["total_score"] = round(scoring["total_score"] * penalty, 4)
            scoring["score_breakdown"]["major_penalty"] = round(penalty, 4)

        # Risk
        risk_tags = generate_risk_tags(
            bucket, elective_ok, elective_note, yrs or 1,
            rvol, has_majors, rank_delta_ratio,
        )
        risk_lvl = risk_level(bucket, elective_ok, rvol)

        # Reason
        reason = generate_reason(
            bucket, sc_name or "", mg_full or "",
            rank_delta, rank_delta_ratio, user_rank,
            lyr or year, lmr, lms or 0, yrs or 1, rvol,
            rbest, rworst, elective_ok, elective_note,
            matched, has_majors, tier_label,
        )

        item = {
            "school_code": sc_code,
            "school_name": sc_name,
            "school_tier": tier_label,
            "major_group_code": mg_code,
            "major_group_full_name": mg_full,
            "elective_requirement": elective_req,
            "bucket": bucket,
            "latest_min_score": lms,
            "latest_min_rank": lmr,
            "user_score": user_score,
            "user_rank": user_rank,
            "rank_delta": rank_delta,
            "rank_delta_ratio": round(rank_delta_ratio, 4),
            "years_available": yrs,
            "rank_avg": round(ravg) if ravg else None,
            "rank_best": rbest,
            "rank_worst": rworst,
            "rank_volatility": round(rvol, 4) if rvol is not None else None,
            "rank_change_latest_vs_prev": rchg,
            "score_avg": round(savg, 1) if savg else None,
            "score_best": sbest,
            "score_worst": sworst,
            "subject_match_status": "matched" if elective_ok else (
                "need_review" if "需人工核验" in elective_note else "not_matched"
            ),
            "subject_match_note": elective_note,
            "matched_majors": matched,
            "majors": group_major_data["majors"] if group_major_data else [],
            "group_major_status": (
                "complete" if group_major_data and len(group_major_data["majors"]) > 0
                else "partial" if group_major_data
                else "missing"
            ),
            "group_plan_count": group_plan_count,
            "risk_tags": risk_tags,
            "risk_level": risk_lvl,
            "reason": reason,
            "source_url": source_url or "https://www.jseea.cn/",
            **scoring,  # total_score, score_breakdown
        }

        if not elective_ok and "需人工核验" not in elective_note:
            # Elective not matched → put in not_matched, don't recommend
            not_matched_items.append(item)
            debug["filtered_by_elective"] += 1
            continue

        recommendations[bucket].append(item)

    # ── Step 4: Sort within each bucket ──
    if strategy == "school_first":
        sort_key_fn = lambda x: (
            -x.get("total_score", 0),
            -(SCHOOL_TIERS.get(x.get("school_name", ""), ("", 0))[1]),
        )
    elif strategy == "major_first":
        sort_key_fn = lambda x: (
            -len(x.get("matched_majors", [])),
            -x.get("total_score", 0),
        )
    elif strategy == "safe":
        # Prefer lower risk, higher score
        sort_key_fn = lambda x: (
            0 if x.get("risk_level") == "low" else (1 if x.get("risk_level") == "medium" else 2),
            -x.get("total_score", 0),
        )
    else:  # balanced
        sort_key_fn = lambda x: -x.get("total_score", 0)

    for bucket in recommendations:
        recommendations[bucket].sort(key=sort_key_fn)
        debug[f"bucket_{bucket}_before_dedup"] = len(recommendations[bucket])

    # ── Step 5: Diversity — limit same school per bucket ──
    MAX_PER_SCHOOL_PER_BUCKET = 3
    MAX_PER_SCHOOL_TOTAL = 6
    school_total_count = defaultdict(int)

    for bucket in list(recommendations.keys()):
        seen_schools = defaultdict(int)
        filtered = []
        for item in recommendations[bucket]:
            sname = item["school_name"]
            if seen_schools[sname] >= MAX_PER_SCHOOL_PER_BUCKET:
                debug["deduplicated"] += 1
                continue
            if school_total_count[sname] >= MAX_PER_SCHOOL_TOTAL:
                debug["deduplicated"] += 1
                continue
            seen_schools[sname] += 1
            school_total_count[sname] += 1
            filtered.append(item)
        recommendations[bucket] = filtered

    # ── Step 6: Limit per bucket (top_n distributed by bucket) ──
    per_bucket = {
        "冲": max(int(body.top_n * 0.35), 30),
        "稳": max(int(body.top_n * 0.40), 40),
        "保": max(int(body.top_n * 0.40), 40),
        "垫": max(int(body.top_n * 0.35), 30),
    }
    for bucket in recommendations:
        recommendations[bucket] = recommendations[bucket][:per_bucket.get(bucket, 30)]

    # ── Step 7: Warnings ──
    warnings = []
    all_items = [r for b in recommendations.values() for r in b]
    total = len(all_items)
    if total < 50:
        warnings.append(f"当前候选结果较少（{total}条），建议放宽城市或专业偏好以扩大候选范围")

    if any("仅一年数据" in (r.get("risk_tags") or []) for r in all_items):
        warnings.append("部分专业组仅有一年数据，参考价值有限")
    if not has_majors:
        warnings.append(
            "当前缺少专业组内具体专业清单，暂不能确认组内专业与调剂风险。"
            "后续接入招生计划后可进一步判断。"
        )
    if not_matched_items:
        warnings.append(
            f"有{len(not_matched_items)}个专业组因选科不满足已过滤，"
            "如需查看请在selected_subjects中补全选科"
        )

# ── Step 8: Attach RAG evidence to each recommendation ──
    rag_cache = _get_rag_evidence_batch(recommendations)
    for bucket_name, items in recommendations.items():
        for item in items:
            school = item.get("school_name", "")
            item["rag_evidence"] = rag_cache.get(school, {
                "school_profile_available": False,
                "admission_policy_available": False,
                "source_count": 0,
                "sources": [],
            })
    debug["rag_schools_checked"] = len(rag_cache)
    debug["rag_schools_with_data"] = sum(1 for v in rag_cache.values() if v["source_count"] > 0)

    # ── Step 9: Debug + Save Report ──
    debug["final_candidates"] = total
    for b in ["冲", "稳", "保", "垫"]:
        debug[f"bucket_{b}_final"] = len(recommendations.get(b, []))

    # ── Save Report to DB ──
    report_id = await _save_jiangsu_report(
        db=db,
        request_body=body,
        recommendations=recommendations,
        user_rank=user_rank,
        rank_source=rank_source,
        subj=subj,
        score=score,
    )

    return {
        "success": True,
        "province": "江苏",
        "subject_type": subj,
        "score": score,
        "user_rank": user_rank,
        "estimated_rank_from_score": estimated_rank_from_score,
        "rank_source": rank_source,
        "rank_warning": rank_warning,
        "report_id": report_id,
        "recommendations": recommendations,
        "summary": {
            "total_candidates": total,
            "冲": len(recommendations.get("冲", [])),
            "稳": len(recommendations.get("稳", [])),
            "保": len(recommendations.get("保", [])),
            "垫": len(recommendations.get("垫", [])),
            "candidate_pool": debug["candidate_pool"],
            "filtered_by_elective": debug.get("filtered_by_elective", 0),
            "filtered_by_city": debug.get("filtered_by_city", 0),
            "filtered_by_bucket": debug.get("filtered_by_bucket", 0),
            "deduplicated": debug.get("deduplicated", 0),
        },
        "warnings": warnings,
        "data_note": (
            "数据来源：江苏省教育考试院官方发布的一分一段表和院校专业组投档线"
            "（2022-2025年）。江苏普通类本科批按院校专业组投档，不等同于具体专业录取。"
            "择境基于历年投档线、位次、招生计划、专业组信息和公开资料进行智能分析，"
            "结果仅供志愿填报参考，不构成录取承诺。"
        ),
        "debug": dict(debug),
        # ── Membership-based field control ──
        "membership_controls": _get_membership_controls(body.user_id or "anonymous"),
    }


def _get_membership_controls(user_id: str) -> dict:
    """Return membership-based display controls for the frontend."""
    try:
        from app.services.membership_service import get_user_entitlements
        entitlements = get_user_entitlements(user_id)
    except Exception:
        entitlements = {"plan": "free", "can_view_group_major_details": False, "can_view_adjustment_risk": False,
                        "can_view_major_match_rate": False, "can_use_deep_ai_qa": False,
                        "max_ai_matches": 5, "max_volunteer_items": 10, "can_export": False,
                        "can_generate_full_report": False}

    return {
        "plan": entitlements.get("plan", "free"),
        "can_view_group_major_details": entitlements.get("can_view_group_major_details", False),
        "can_view_adjustment_risk": entitlements.get("can_view_adjustment_risk", False),
        "can_view_major_match_rate": entitlements.get("can_view_major_match_rate", False),
        "can_use_deep_ai_qa": entitlements.get("can_use_deep_ai_qa", False),
        "can_export": entitlements.get("can_export", False),
        "can_generate_full_report": entitlements.get("can_generate_full_report", False),
        "max_ai_matches": entitlements.get("max_ai_matches"),
        "max_volunteer_items": entitlements.get("max_volunteer_items"),
        "can_use_human_review": entitlements.get("can_use_human_review", False),
        # ── RAG ──
        "can_view_rag_school_profile": entitlements.get("can_view_rag_school_profile", True),
        "can_view_rag_admission_policy": entitlements.get("can_view_rag_admission_policy", False),
        "can_view_rag_deep_analysis": entitlements.get("can_view_rag_deep_analysis", False),
        "can_view_rag_report_section": entitlements.get("can_view_rag_report_section", False),
        "locked_features": {
            "group_major_details": "进阶版可查看专业组内专业明细",
            "adjustment_risk": "进阶版可查看调剂风险评估",
            "major_match_rate": "进阶版可查看专业命中度分析",
            "deep_ai_qa": "进阶版可使用AI深度答疑",
            "export_report": "基础版支持导出PDF/Excel",
            "full_report": "基础版可生成完整分析报告",
            "human_review": "尊享版可使用人工方案复核",
            "rag_admission_policy": "基础版可查看招生章程",
            "rag_deep_analysis": "进阶版可查看官方资料深度解读",
            "rag_report_section": "进阶版可查看报告中的官方资料来源",
        },
    }


# ═══════════════════════════════════════════
#  RAG evidence batch checker (lazy-loaded retriever)
# ═══════════════════════════════════════════

@lru_cache(maxsize=1)
def _get_rag_docstore():
    # Availability checks need document metadata, not embeddings or a model.
    path = Path(__file__).resolve().parents[3] / "rag_output/chsi/export/vector_store/faiss/docstore.jsonl"
    try:
        with path.open(encoding="utf8") as source:
            return [json.loads(line) for line in source if line.strip()]
    except (OSError, ValueError):
        logger.warning("RAG document metadata unavailable")
        return []


def _get_rag_evidence_batch(recommendations: dict) -> dict:
    """Batch-check CHSI RAG availability for all school names in recommendations.

    Scans the FAISS docstore (in-memory list of 57k chunks) to find
    school_profile and admission_policy_clause documents for each school.
    Returns a dict keyed by school_name with availability flags and up to
    3 source URLs per school.
    """
    schools: set[str] = set()
    for items in recommendations.values():
        for item in items:
            name = item.get("school_name", "")
            if name:
                schools.add(name)

    if not schools:
        return {}

    docstore = _get_rag_docstore()

    result: dict = {}
    for school in schools:
        result[school] = {
            "school_profile_available": False,
            "admission_policy_available": False,
            "source_count": 0,
            "sources": [],
        }

    for row in docstore:
        meta = row.get("metadata") or {}
        school = meta.get("school_name", "")
        if school not in schools:
            continue
        dt = meta.get("doc_type", "")
        url = meta.get("source_url", "")
        title = meta.get("title", "")
        if not url:
            continue
        entry = result[school]
        if dt == "school_profile":
            entry["school_profile_available"] = True
            if len(entry["sources"]) < 3:
                entry["sources"].append({"title": title or "", "doc_type": dt, "source_url": url})
        elif dt == "admission_policy_clause":
            entry["admission_policy_available"] = True
            if len(entry["sources"]) < 3:
                entry["sources"].append({"title": title or "", "doc_type": dt, "source_url": url})
        entry["source_count"] += 1

    return result


async def _save_jiangsu_report(
    db: AsyncSession,
    request_body,
    recommendations: dict,
    user_rank: int,
    rank_source: str,
    subj: str,
    score: int,
) -> str:
    """Save Jiangsu recommendation as Application + RecommendationResult + Report.

    Maps Jiangsu-specific recommendation items to the generic format expected
    by build_report_json, then persists the full chain to the database.
    Returns the report_id (or empty string on failure).
    """
    import uuid
    import json as _json
    from datetime import datetime, timedelta
    from sqlalchemy import text as sa_text
    from app.services.report_builder import build_report_json

    try:
        now = datetime.utcnow()

        # ── 3. Map Jiangsu items → generic format ──
        def map_item(item: dict, bucket_label: str) -> dict:
            rag = item.get("rag_evidence", {}) or {}
            majors = []
            for m in (item.get("matched_majors") or []):
                if isinstance(m, dict):
                    majors.append(m.get("major_name", ""))
                elif isinstance(m, str):
                    majors.append(m)
            for m in (item.get("majors") or []):
                if isinstance(m, dict):
                    name = m.get("major_name", "")
                    if name and name not in majors:
                        majors.append(name)

            return {
                "school_name": item.get("school_name", ""),
                "school_id": item.get("school_code", ""),
                "school_logo": "",
                "province": "江苏",
                "city": "",
                "school_type": "",
                "school_level": item.get("school_tier", "") or item.get("school_level", ""),
                "major_name": item.get("major_group_full_name", ""),
                "major_group_name": item.get("major_group_full_name", ""),
                "tier": bucket_label,
                "probability": round(item.get("total_score", 50) / 100, 2),
                "match_score": int(item.get("total_score", 50)),
                "expected_rank": item.get("latest_min_rank", 0),
                "expected_score": item.get("latest_min_score", 0),
                "majors": majors[:10],
                "rag_evidence": rag,
                "major_group_plan_summary": {},
            }

        rush = [map_item(item, "冲刺") for item in recommendations.get("冲", [])]
        stable = [map_item(item, "稳妥") for item in recommendations.get("稳", [])]
        safe = [map_item(item, "保底") for item in recommendations.get("保", [])]
        pad = [map_item(item, "兜底") for item in recommendations.get("垫", [])]

        all_items = rush + stable + safe

        summary_data = {
            "user_score": score,
            "user_rank": user_rank,
            "province": "江苏",
            "subject_type": subj,
            "total_candidates": len(all_items),
            "match_rate": 80 if len(all_items) > 20 else 50,
            "strategy": request_body.strategy or "balanced",
            "rank_source": rank_source,
        }

        # ── 5. Build Report JSON & save ──
        recommendation_data = {
            "summary": summary_data,
            "rush": rush,
            "stable": stable,
            "safe": safe,
            "not_recommended": [],
        }

        class AppProxy:
            pass
        app = AppProxy()
        app.province = "江苏"
        app.subject_type = subj
        app.score = score
        app.rank = user_rank

        report_json = build_report_json(
            recommendation_data=recommendation_data,
            application=app,
            plan_type="free",
        )

        # ── AI Content Generation ───────────────────────────────
        # Retrieve RAG evidence and generate AI narratives
        try:
            from app.services.report_rag_evidence_service import fetch_school_evidence
            from app.services.report_ai_writer import generate_ai_narratives

            # Gather school names for evidence retrieval
            school_names = [s["school_name"] for s in report_json.get("school_deep_dives", [])[:10]]
            evidence_map = {}
            for name in school_names:
                evidence_map[name] = await fetch_school_evidence(db, name, limit=3)

            # Build user info for AI prompts
            user_info = {
                "province": app.province,
                "score": app.score,
                "rank": app.rank,
                "subject_type": app.subject_type,
                "interests": getattr(app, "interests", "") or "",
                "region_preference": getattr(app, "region_preference", "") or "",
            }

            # Release the read transaction before waiting for external services.
            await db.rollback()
            ai_result = await asyncio.wait_for(
                generate_ai_narratives(user_info, recommendation_data, evidence_map),
                timeout=20.0,
            )

            # Merge AI narratives into report JSON
            if ai_result:
                report_json["ai_narratives"] = {
                    k: v for k, v in ai_result.items()
                    if k != "school_deep_dives"
                }
                if ai_result.get("school_deep_dives"):
                    report_json["school_deep_dives"] = ai_result["school_deep_dives"]
                logger.info(
                    f"AI content generated: {len(ai_result.get('school_deep_dives', []))} school deep dives"
                )
        except asyncio.TimeoutError:
            report_json["ai_generation_status"] = "timeout"
            logger.warning("AI supplement exceeded 20s; retaining the data-based report")
        except Exception as ai_err:
            logger.warning(f"AI content generation failed (report will still be saved): {ai_err}")

        # Begin a short write-only transaction after all slow enrichment.
        # End the previous read snapshot, then serialize SQLite writers before
        # checking the shared default session (prevents read-to-write races).
        await db.rollback()
        if db.get_bind().dialect.name == "sqlite":
            await db.execute(sa_text("BEGIN IMMEDIATE"))
        # ── 1. Ensure a default session exists ──
        session_id = "jiangsu_default"
        existing = await db.execute(
            sa_text("SELECT id FROM sessions WHERE id = :sid"),
            {"sid": session_id},
        )
        if not existing.fetchone():
            await db.execute(
                sa_text(
                    "INSERT INTO sessions (id, session_token, source, created_at, expires_at) "
                    "VALUES (:id, :token, :source, :created, :expires)"
                ),
                {
                    "id": session_id,
                    "token": f"jiangsu_{uuid.uuid4().hex[:16]}",
                    "source": "jiangsu_recommend",
                    "created": now,
                    "expires": now + timedelta(days=365),
                },
            )

        # ── 2. Create Application ──
        app_id = uuid.uuid4().hex[:22]
        await db.execute(
            sa_text(
                "INSERT INTO applications (id, session_id, status, province, year, "
                "subject_type, score, rank, priority, preferred_cities, preferred_major_categories, "
                "created_at, updated_at) "
                "VALUES (:id, :sid, :status, :province, :year, :subj, :score, :rank, "
                ":priority, :cities, :majors, :created, :updated)"
            ),
            {
                "id": app_id,
                "sid": session_id,
                "status": "completed",
                "province": "江苏",
                "year": request_body.year,
                "subj": subj,
                "score": score,
                "rank": user_rank,
                "priority": request_body.strategy or "balanced",
                "cities": _json.dumps(request_body.preferred_cities or []),
                "majors": _json.dumps(request_body.preferred_majors or []),
                "created": now,
                "updated": now,
            },
        )

        # ── 4. Create RecommendationResult ──
        rec_id = uuid.uuid4().hex[:22]
        await db.execute(
            sa_text(
                "INSERT INTO recommendation_results (id, application_id, summary_data, "
                "recommendations, tier_distribution, created_at) "
                "VALUES (:id, :app_id, :summary, :recs, :tiers, :created)"
            ),
            {
                "id": rec_id,
                "app_id": app_id,
                "summary": _json.dumps(summary_data),
                "recs": _json.dumps(all_items),
                "tiers": _json.dumps({
                    "冲": len(rush), "稳": len(stable),
                    "保": len(safe), "垫": len(pad),
                }),
                "created": now,
            },
        )

        report_id = uuid.uuid4().hex[:22]
        await db.execute(
            sa_text(
                "INSERT INTO reports (id, application_id, recommendation_result_id, "
                "plan_code, status, province, subject_type, score, rank, title, "
                "report_json, created_at, completed_at) "
                "VALUES (:id, :app_id, :rec_id, :plan, :status, :province, :subj, "
                ":score, :rank, :title, :json, :created, :completed)"
            ),
            {
                "id": report_id,
                "app_id": app_id,
                "rec_id": rec_id,
                "plan": "premium",
                "status": "ready",
                "province": "江苏",
                "subj": subj,
                "score": score,
                "rank": user_rank,
                "title": f"江苏{subj}志愿填报分析报告",
                "json": _json.dumps(report_json),
                "created": now,
                "completed": now,
            },
        )

        await db.commit()
        logger.info(f"Report saved: {report_id} (app={app_id}, items={len(all_items)})")
        return report_id

    except Exception as e:
        logger.error(f"Failed to save Jiangsu report: {e}", exc_info=True)
        await db.rollback()
        return ""
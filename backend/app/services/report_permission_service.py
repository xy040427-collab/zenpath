"""
report_permission_service.py — 会员权限裁剪

根据 membership plan_type 裁剪 Report JSON 内容。

权限规则：
  free      — 只返回摘要预览，不允许下载 PDF
  basic     — 返回基础报告，允许基础 PDF，不展示调剂风险和完整 RAG
  advanced  — 返回深度报告，允许高级 PDF，展示专业组明细、调剂风险、RAG
  premium   — 返回尊享报告，可展示人工复核入口
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# ── 字段级权限映射 ──
# 每个字段对应的最低 plan_type
FIELD_PERMISSIONS: Dict[str, str] = {
    "student_profile": "free",
    "executive_summary": "free",
    "score_positioning": "free",
    "bucket_summary": "free",
    "risk_preview": "free",
    "key_candidates_preview": "free",
    # basic+
    "volunteer_strategy": "basic",
    "key_candidates": "basic",
    "region_analysis": "basic",
    "school_tier_analysis": "basic",
    # advanced+
    "major_match_analysis": "advanced",
    "adjustment_risk_analysis": "advanced",
    "rag_evidence_sections": "advanced",
    "risk_register": "advanced",
    "final_recommendations": "advanced",
    # premium only
    "premium_review": "premium",
}

PLAN_LEVELS = {"free": 0, "basic": 1, "advanced": 2, "premium": 3}


def get_permission(plan_type: str) -> Dict[str, Any]:
    """Get permission snapshot for a plan type."""
    level = PLAN_LEVELS.get(plan_type, 0)
    return {
        "plan_type": plan_type,
        "level": level,
        "can_download_pdf": level >= PLAN_LEVELS["basic"],
        "can_view_adjustment_risk": level >= PLAN_LEVELS["advanced"],
        "can_view_rag_evidence": level >= PLAN_LEVELS["advanced"],
        "can_view_premium_review": level >= PLAN_LEVELS["premium"],
    }


def build_summary(report_json: Dict[str, Any], plan_type: str) -> Dict[str, Any]:
    """Build summary data (stripped) for /report/:id page.

    Per doc: free users only see summary preview.
    """
    base = {
        "student_profile": report_json.get("student_profile", {}),
        "executive_summary": report_json.get("executive_summary", {}),
        "score_positioning": report_json.get("score_positioning", {}),
        "bucket_summary": report_json.get("bucket_summary", {}),
    }

    level = PLAN_LEVELS.get(plan_type, 0)

    # Risk preview — simplified for all plans
    risks = report_json.get("risk_register", [])
    base["risk_preview"] = [
        {"risk_type": r["risk_type"], "severity": r["severity"]}
        for r in risks[:3]
    ]

    # Key candidates preview — simplified
    candidates = report_json.get("key_candidates", [])
    base["key_candidates_preview"] = [
        {
            "school_name": c.get("school_name", ""),
            "tier": c.get("tier", ""),
            "school_level": c.get("school_level", ""),
            "score_gap": c.get("score_gap", 0),
        }
        for c in candidates[:5]
    ]

    # Permission info
    perm = get_permission(plan_type)
    base["download_permission"] = {
        "can_download_pdf": perm["can_download_pdf"],
        "required_plan": None if perm["can_download_pdf"] else "basic",
    }

    base["plan_type"] = plan_type

    return base


def build_pdf_data(report_json: Dict[str, Any], plan_type: str) -> Dict[str, Any]:
    """Build full data for PDF preview / download.

    Includes all sections that the user's plan allows.
    """
    level = PLAN_LEVELS.get(plan_type, 0)
    pdf_type = plan_type if plan_type != "free" else "basic"

    report = dict(report_json)  # shallow copy

    # Remove sections not allowed for this plan
    if level < PLAN_LEVELS["advanced"]:
        report.pop("adjustment_risk_analysis", None)
        report.pop("rag_evidence_sections", None)
        report.pop("risk_register", None)
    if level < PLAN_LEVELS["premium"]:
        report.pop("premium_review", None)

    return {
        "report_id": report_json.get("report_id", ""),
        "pdf_type": pdf_type,
        "report": report,
        "branding": {
            "product_name": "择境 ZENPATH",
            "theme": "premium_education",
            "primary_color": "#1A2E22",
            "accent_color": "#A8883C",
            "bg_color": "#F5F0E8",
        },
        "print_settings": {
            "page_size": "A4",
            "orientation": "portrait",
            "margin": "14mm",
        },
    }


def build_response_with_permission(
    report_json: Dict[str, Any],
    plan_type: str,
) -> Dict[str, Any]:
    """Return full report with permission metadata.

    Sections that the user cannot access are replaced with a locked placeholder.
    """
    level = PLAN_LEVELS.get(plan_type, 0)
    locked_sections = []
    result = dict(report_json)

    for field, required in FIELD_PERMISSIONS.items():
        if PLAN_LEVELS.get(required, 99) > level:
            if field in result:
                result[field] = {
                    "locked": True,
                    "required_plan": required,
                    "message": f"此内容需要 {required} 及以上版本",
                }
                locked_sections.append(field)

    return {
        "report": result,
        "permission": {
            "plan_type": plan_type,
            "locked_sections": locked_sections,
        },
    }

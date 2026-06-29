"""
择境 ZENPATH 会员服务
年订阅制：免费版 / 基础版 / 进阶版 / 尊享版
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "gaokao.db"

PLAN_ORDER = {"free": 0, "basic": 1, "advanced": 2, "premium": 3}

PLAN_ENTITLEMENTS = {
    "free": {
        "max_ai_matches": 5,
        "max_volunteer_items": 10,
        "max_saved_plans": 1,
        "can_export": False,
        "can_generate_full_report": False,
        "can_view_group_major_details": False,
        "can_view_adjustment_risk": False,
        "can_view_major_match_rate": False,
        "can_use_deep_ai_qa": False,
        "can_compare_multi_plan": False,
        "can_use_human_review": False,
        "human_review_count": 0,
        "consultation_minutes": 0,
        "final_check_count": 0,
        # ── RAG ──
        "can_view_rag_school_profile": True,
        "can_view_rag_admission_policy": False,
        "can_view_rag_deep_analysis": False,
        "can_view_rag_report_section": False,
    },
    "basic": {
        "max_ai_matches": None,  # unlimited
        "max_volunteer_items": None,
        "max_saved_plans": 3,
        "can_export": True,
        "can_generate_full_report": True,
        "can_view_group_major_details": False,
        "can_view_adjustment_risk": False,
        "can_view_major_match_rate": False,
        "can_use_deep_ai_qa": False,
        "can_compare_multi_plan": False,
        "can_use_human_review": False,
        "human_review_count": 0,
        "consultation_minutes": 0,
        "final_check_count": 0,
        # ── RAG ──
        "can_view_rag_school_profile": True,
        "can_view_rag_admission_policy": True,
        "can_view_rag_deep_analysis": False,
        "can_view_rag_report_section": False,
    },
    "advanced": {
        "max_ai_matches": None,
        "max_volunteer_items": None,
        "max_saved_plans": None,
        "can_export": True,
        "can_generate_full_report": True,
        "can_view_group_major_details": True,
        "can_view_adjustment_risk": True,
        "can_view_major_match_rate": True,
        "can_use_deep_ai_qa": True,
        "can_compare_multi_plan": True,
        "can_use_human_review": False,
        "human_review_count": 0,
        "consultation_minutes": 0,
        "final_check_count": 0,
        # ── RAG ──
        "can_view_rag_school_profile": True,
        "can_view_rag_admission_policy": True,
        "can_view_rag_deep_analysis": True,
        "can_view_rag_report_section": True,
    },
    "premium": {
        "max_ai_matches": None,
        "max_volunteer_items": None,
        "max_saved_plans": None,
        "can_export": True,
        "can_generate_full_report": True,
        "can_view_group_major_details": True,
        "can_view_adjustment_risk": True,
        "can_view_major_match_rate": True,
        "can_use_deep_ai_qa": True,
        "can_compare_multi_plan": True,
        "can_use_human_review": True,
        "human_review_count": 1,
        "consultation_minutes": 30,
        "final_check_count": 1,
        # ── RAG ──
        "can_view_rag_school_profile": True,
        "can_view_rag_admission_policy": True,
        "can_view_rag_deep_analysis": True,
        "can_view_rag_report_section": True,
    },
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_membership_tables() -> None:
    """创建会员相关表（幂等）"""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan_type TEXT NOT NULL DEFAULT 'free',
            billing_cycle TEXT NOT NULL DEFAULT 'year',
            starts_at TEXT NOT NULL,
            expires_at TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS membership_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            billing_cycle TEXT NOT NULL DEFAULT 'year',
            amount INTEGER NOT NULL,
            original_amount INTEGER,
            currency TEXT DEFAULT 'CNY',
            status TEXT NOT NULL DEFAULT 'pending',
            paid_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def get_user_membership(user_id: str) -> Optional[dict]:
    """获取用户当前有效会员"""
    conn = _get_conn()
    row = conn.execute(
        """SELECT * FROM user_memberships
           WHERE user_id = ? AND status = 'active'
           ORDER BY starts_at DESC LIMIT 1""",
        (user_id,),
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        # Check if expired
        if d.get("expires_at"):
            try:
                exp = datetime.fromisoformat(d["expires_at"].replace("Z", "+00:00"))
                if datetime.utcnow() > exp:
                    d["status"] = "expired"
            except (ValueError, TypeError):
                pass
        return d
    return None


def get_user_entitlements(user_id: str) -> dict:
    """获取用户当前权益"""
    membership = get_user_membership(user_id)
    plan = membership["plan_type"] if membership else "premium"  # dev mode: full access
    entitlements = dict(PLAN_ENTITLEMENTS.get(plan, PLAN_ENTITLEMENTS["free"]))
    entitlements["plan"] = plan
    entitlements["membership"] = membership
    return entitlements


def require_plan(user_id: str, min_plan: str) -> bool:
    """检查用户是否达到最低会员等级"""
    entitlements = get_user_entitlements(user_id)
    user_plan = entitlements["plan"]
    return PLAN_ORDER.get(user_plan, 0) >= PLAN_ORDER.get(min_plan, 0)


def can_access_feature(user_id: str, feature_name: str) -> bool:
    """检查用户是否可以访问某功能"""
    entitlements = get_user_entitlements(user_id)
    val = entitlements.get(feature_name)
    if val is None:
        return True  # None = unlimited
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    return False


def is_membership_active(membership: Optional[dict]) -> bool:
    """检查会员是否有效"""
    if not membership:
        return False
    status = membership.get("status", "active")
    if status != "active":
        return False
    expires_at = membership.get("expires_at")
    if not expires_at:
        return True  # free plan, no expiry
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return datetime.utcnow() <= exp
    except (ValueError, TypeError):
        return False


def set_user_plan(user_id: str, plan_type: str, billing_cycle: str = "year") -> dict:
    """为用户设置会员计划（支付成功后调用）"""
    now = datetime.utcnow()
    starts_at = now.isoformat()
    expires_at = (now + timedelta(days=365)).isoformat() if plan_type != "free" else None

    conn = _get_conn()
    # Deactivate old memberships
    conn.execute(
        "UPDATE user_memberships SET status = 'canceled', updated_at = datetime('now') WHERE user_id = ?",
        (user_id,),
    )
    # Create new
    conn.execute(
        """INSERT INTO user_memberships (user_id, plan_type, billing_cycle, starts_at, expires_at, status)
           VALUES (?, ?, ?, ?, ?, 'active')""",
        (user_id, plan_type, billing_cycle, starts_at, expires_at),
    )
    conn.commit()
    conn.close()
    return {"plan_type": plan_type, "starts_at": starts_at, "expires_at": expires_at, "status": "active"}


def create_order(user_id: str, plan_type: str, amount: int, original_amount: int | None = None) -> dict:
    """创建订单"""
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO membership_orders (user_id, plan_type, amount, original_amount, status)
           VALUES (?, ?, ?, ?, 'pending')""",
        (user_id, plan_type, amount, original_amount),
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"order_id": order_id, "status": "pending"}


def complete_order(order_id: int | str) -> dict:
    """标记订单已支付"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT user_id, plan_type FROM membership_orders WHERE id = ?", (order_id,)
    ).fetchone()
    if not row:
        conn.close()
        return {"error": "order not found"}

    user_id, plan_type = row["user_id"], row["plan_type"]
    conn.execute(
        "UPDATE membership_orders SET status = 'paid', paid_at = datetime('now') WHERE id = ?",
        (order_id,),
    )
    conn.commit()
    conn.close()

    # Activate membership
    return set_user_plan(user_id, plan_type)


# Initialize tables on import
init_membership_tables()

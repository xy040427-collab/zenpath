"""
Chat session & message DB tables for ZENPATH AI Q&A.
Creates tables idempotently — safe to run on every startup.
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "chat.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_chat_tables() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL DEFAULT 'anonymous',
            title TEXT,
            province TEXT,
            subject_type TEXT,
            score INTEGER,
            rank INTEGER,
            selected_subjects TEXT,
            preferred_majors TEXT,
            preferred_cities TEXT,
            preferred_tiers TEXT,
            strategy TEXT,
            related_recommendation_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            archived INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT 'anonymous',
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content TEXT NOT NULL,
            intent TEXT,
            answerable INTEGER,
            structured_payload TEXT,
            sources TEXT,
            token_count INTEGER,
            latency_ms INTEGER,
            from_cache INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS chat_response_cache (
            cache_key TEXT PRIMARY KEY,
            normalized_query TEXT NOT NULL,
            context_hash TEXT,
            answer TEXT NOT NULL,
            sources TEXT,
            intent TEXT,
            hit_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_chat_messages_session
            ON chat_messages(session_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
            ON chat_sessions(user_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_cache_expires
            ON chat_response_cache(expires_at);
    """)
    conn.commit()
    conn.close()


# ── Session CRUD ──

def create_session(
    user_id: str = "anonymous",
    title: str = "",
    province: str = "",
    subject_type: str = "",
    score: int = 0,
    rank: int = 0,
    selected_subjects: list[str] | None = None,
    preferred_majors: list[str] | None = None,
    preferred_cities: list[str] | None = None,
    preferred_tiers: list[str] | None = None,
    strategy: str = "",
    related_recommendation_id: str = "",
) -> dict:
    sid = str(uuid.uuid4())
    if not title:
        parts = []
        if province:
            parts.append(province)
        if subject_type:
            parts.append(subject_type.replace("等科目类", ""))
        if score:
            parts.append(f"{score}分")
        title = " ".join(parts) + " 志愿咨询" if parts else "新对话"
    conn = _get_conn()
    conn.execute(
        """INSERT INTO chat_sessions
           (id, user_id, title, province, subject_type, score, rank,
            selected_subjects, preferred_majors, preferred_cities,
            preferred_tiers, strategy, related_recommendation_id)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (sid, user_id, title, province, subject_type, score, rank,
         _list_str(selected_subjects), _list_str(preferred_majors),
         _list_str(preferred_cities), _list_str(preferred_tiers),
         strategy, related_recommendation_id),
    )
    conn.commit()
    conn.close()
    return {"session_id": sid, "title": title}


def list_sessions(user_id: str = "anonymous", limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        """SELECT s.*, (SELECT COUNT(*) FROM chat_messages m WHERE m.session_id = s.id) AS message_count
           FROM chat_sessions s
           WHERE s.user_id = ? AND s.archived = 0
           ORDER BY s.updated_at DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_session(session_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_session_title(session_id: str, title: str) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE chat_sessions SET title = ?, updated_at = datetime('now') WHERE id = ?",
        (title, session_id),
    )
    conn.commit()
    conn.close()


def archive_session(session_id: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE chat_sessions SET archived = 1, updated_at = datetime('now') WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def touch_session(session_id: str) -> None:
    conn = _get_conn()
    conn.execute("UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


# ── Message CRUD ──

def save_message(
    session_id: str,
    role: str,
    content: str,
    user_id: str = "anonymous",
    intent: str = "",
    answerable: bool | None = None,
    structured_payload: dict | None = None,
    sources: list[dict] | None = None,
    token_count: int = 0,
    latency_ms: int = 0,
    from_cache: bool = False,
) -> dict:
    mid = str(uuid.uuid4())
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO chat_messages
               (id, session_id, user_id, role, content, intent, answerable,
                structured_payload, sources, token_count, latency_ms, from_cache)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (mid, session_id, user_id, role, content, intent,
             1 if answerable else (0 if answerable is not None else None),
             _json.dumps(structured_payload, ensure_ascii=False) if structured_payload else None,
             _json.dumps(sources, ensure_ascii=False) if sources else None,
             token_count, latency_ms, 1 if from_cache else 0),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"message_id": mid}


def get_messages(session_id: str, limit: int = 100) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [_msg_to_dict(r) for r in rows]


# ── Cache ──

def get_cached_response(cache_key: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM chat_response_cache WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))",
        (cache_key,),
    ).fetchone()
    if row:
        conn.execute("UPDATE chat_response_cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (cache_key,))
        conn.commit()
    conn.close()
    if row:
        d = _row_to_dict(row)
        d["sources"] = _json.loads(d["sources"]) if d.get("sources") else []
        return d
    return None


def set_cached_response(
    cache_key: str,
    normalized_query: str,
    answer: str,
    context_hash: str = "",
    sources: list[dict] | None = None,
    intent: str = "",
    ttl_hours: int = 168,
) -> None:
    conn = _get_conn()
    expires = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat() if ttl_hours else None
    conn.execute(
        """INSERT OR REPLACE INTO chat_response_cache
           (cache_key, normalized_query, context_hash, answer, sources, intent, expires_at)
           VALUES (?,?,?,?,?,?,?)""",
        (cache_key, normalized_query, context_hash, answer,
         _json.dumps(sources, ensure_ascii=False) if sources else None,
         intent, expires),
    )
    conn.commit()
    conn.close()


# ── Helpers ──

import json as _json


def _list_str(lst: list[str] | None) -> str | None:
    return _json.dumps(lst, ensure_ascii=False) if lst else None


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _msg_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("sources"):
        try:
            d["sources"] = _json.loads(d["sources"])
        except Exception:
            pass
    if d.get("structured_payload"):
        try:
            d["structured_payload"] = _json.loads(d["structured_payload"])
        except Exception:
            pass
    return d


# Auto-init on import
init_chat_tables()

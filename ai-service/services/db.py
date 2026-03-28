import os
import sqlite3
from typing import Optional

_SQLITE_PATH = "traderwise_dev.db"


# ---------------------------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------------------------

def _pg_conn():
    import psycopg
    from psycopg.rows import dict_row
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(url, row_factory=dict_row)


# ---------------------------------------------------------------------------
# SQLite fallback
# ---------------------------------------------------------------------------

def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_sqlite_schema(conn)
    return conn


def _ensure_sqlite_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS traders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL UNIQUE,
            language TEXT DEFAULT 'twi',
            goods_type TEXT DEFAULT '',
            market TEXT,
            working_cap REAL,
            susu_day TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trader_phone TEXT NOT NULL,
            incoming_message TEXT,
            transcription TEXT,
            claude_input TEXT,
            claude_output TEXT,
            final_reply TEXT,
            distress_flag INTEGER NOT NULL DEFAULT 0,
            fraud_flag INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Public API — tries PostgreSQL first, falls back to SQLite
# ---------------------------------------------------------------------------

def get_trader_profile(phone: str) -> dict:
    # Try PostgreSQL
    try:
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM traders WHERE phone = %s LIMIT 1", (phone,))
                row = cur.fetchone()
        if row:
            return dict(row)
        return {"phone": phone, "language": "twi"}
    except Exception:
        pass

    # Fall back to SQLite
    try:
        with _sqlite_conn() as conn:
            cur = conn.execute("SELECT * FROM traders WHERE phone = ? LIMIT 1", (phone,))
            row = cur.fetchone()
        if row:
            result = dict(row)
            raw = result.get("goods_type") or ""
            result["goods_type"] = [g.strip() for g in raw.split(",") if g.strip()]
            return result
    except Exception:
        pass

    return {"phone": phone, "language": "twi"}


def get_recent_interactions(phone: str, limit: int = 3) -> list[dict]:
    # Try PostgreSQL
    try:
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT claude_input, final_reply, created_at
                    FROM interactions
                    WHERE trader_phone = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (phone, limit),
                )
                rows = cur.fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception:
        pass

    # Fall back to SQLite
    try:
        with _sqlite_conn() as conn:
            cur = conn.execute(
                """
                SELECT claude_input, final_reply, created_at
                FROM interactions
                WHERE trader_phone = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (phone, limit),
            )
            rows = cur.fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception:
        return []


def save_interaction(
    phone: str,
    transcription: Optional[str],
    claude_input: str,
    claude_output: str,
    final_reply: str,
    distress_flag: bool = False,
    fraud_flag: bool = False,
) -> None:
    # Try PostgreSQL
    try:
        with _pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO interactions
                        (trader_phone, transcription, claude_input, claude_output, final_reply,
                         distress_flag, fraud_flag)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, transcription, claude_input, claude_output, final_reply,
                     distress_flag, fraud_flag),
                )
            conn.commit()
        return
    except Exception:
        pass

    # Fall back to SQLite
    try:
        with _sqlite_conn() as conn:
            conn.execute(
                """
                INSERT INTO interactions
                    (trader_phone, transcription, claude_input, claude_output, final_reply,
                     distress_flag, fraud_flag)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (phone, transcription, claude_input, claude_output, final_reply,
                 int(distress_flag), int(fraud_flag)),
            )
            conn.commit()
    except Exception:
        pass

"""
Audit logging module: stores all interactions in SQLite with redacted PII.
"""

import sqlite3
import logging
from datetime import datetime, timezone

DB_PATH = "./audit_log.db"
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create the audit log table if it does not exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            session_id      TEXT,
            user_input_raw  TEXT,
            user_input_redacted TEXT,
            pii_types_detected  TEXT,
            topic_verdict   TEXT,
            llm_response    TEXT,
            was_blocked     INTEGER DEFAULT 0,
            block_reason    TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_interaction(
    session_id: str,
    user_input_raw: str,
    user_input_redacted: str,
    pii_types: list[str],
    topic_verdict: str,
    llm_response: str | None,
    was_blocked: bool = False,
    block_reason: str | None = None,
) -> None:
    """Log a single interaction to the audit database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO audit_log
            (timestamp, session_id, user_input_raw, user_input_redacted, pii_types_detected,
             topic_verdict, llm_response, was_blocked, block_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            session_id,
            user_input_raw,
            user_input_redacted,
            ", ".join(pii_types) if pii_types else None,
            topic_verdict,
            llm_response,
            int(was_blocked),
            block_reason,
        ),
    )
    conn.commit()
    conn.close()
    logger.info("Logged interaction for session %s | blocked=%s", session_id, was_blocked)


def get_recent_logs(limit: int = 50) -> list[dict]:
    """Retrieve the most recent audit log entries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

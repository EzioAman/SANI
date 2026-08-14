"""SANI SQLite Database Management."""

import sqlite3
from pathlib import Path
from sani.config import get_config


def get_db_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get SQLite database connection with row factory configured."""
    if db_path is None:
        db_path = get_config().db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Initialize SQLite database schema."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                verification_state TEXT NOT NULL DEFAULT 'UNVERIFIED',
                superseded_by TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_owner ON memories(owner_id);
        """)
    conn.close()

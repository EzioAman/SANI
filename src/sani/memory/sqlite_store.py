"""SQLite Implementation of MemoryProvider."""

import json
from datetime import datetime, timezone
from pathlib import Path
from sani.memory.db import get_db_connection, init_db
from sani.models import MemoryItem
from sani.providers.memory_provider import MemoryProvider


class SQLiteMemoryStore(MemoryProvider):
    """SQLite-backed persistent memory store with owner-scoping and provenance metadata."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def store_memory(self, item: MemoryItem) -> str:
        conn = get_db_connection(self.db_path)
        with conn:
            conn.execute(
                """
                INSERT INTO memories (
                    memory_id, owner_id, memory_type, content, confidence,
                    verification_state, superseded_by, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.memory_id,
                    item.owner_id,
                    item.memory_type,
                    item.content,
                    item.confidence,
                    item.verification_state,
                    item.superseded_by,
                    item.created_at.isoformat(),
                    json.dumps(item.metadata),
                ),
            )
        conn.close()
        return item.memory_id

    def get_memory(self, memory_id: str) -> MemoryItem | None:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE memory_id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return MemoryItem(
            memory_id=row["memory_id"],
            owner_id=row["owner_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            confidence=row["confidence"],
            verification_state=row["verification_state"],
            superseded_by=row["superseded_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def search_memories(self, owner_id: str, query: str = "", memory_type: str | None = None) -> list[MemoryItem]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        sql = "SELECT * FROM memories WHERE owner_id = ? AND superseded_by IS NULL"
        params: list[str] = [owner_id]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)

        if query:
            sql += " AND content LIKE ?"
            params.append(f"%{query}%")

        sql += " ORDER BY created_at DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            MemoryItem(
                memory_id=r["memory_id"],
                owner_id=r["owner_id"],
                memory_type=r["memory_type"],
                content=r["content"],
                confidence=r["confidence"],
                verification_state=r["verification_state"],
                superseded_by=r["superseded_by"],
                created_at=datetime.fromisoformat(r["created_at"]),
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
            )
            for r in rows
        ]

    def update_memory(self, memory_id: str, content: str, confidence: float = 1.0) -> bool:
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                "UPDATE memories SET content = ?, confidence = ? WHERE memory_id = ?",
                (content, confidence, memory_id),
            )
            updated = cursor.rowcount > 0
        conn.close()
        return updated

    def supersede_memory(self, old_memory_id: str, new_memory_id: str) -> bool:
        conn = get_db_connection(self.db_path)
        with conn:
            cursor = conn.execute(
                "UPDATE memories SET superseded_by = ? WHERE memory_id = ?",
                (new_memory_id, old_memory_id),
            )
            superseded = cursor.rowcount > 0
        conn.close()
        return superseded

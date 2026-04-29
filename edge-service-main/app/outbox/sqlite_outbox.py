import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass
class OutboxItem:
    id: int
    local_media_path: str
    bucket: str
    object_key: str
    payload_json: str
    state: str
    attempt_count: int
    next_attempt_at: float


class SqliteOutbox:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                local_media_path TEXT NOT NULL,
                bucket TEXT NOT NULL,
                object_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_error TEXT,
                attempt_count INTEGER DEFAULT 0,
                next_attempt_at REAL DEFAULT 0
            )
            """
        )
        self._ensure_column("next_attempt_at", "REAL DEFAULT 0")
        self.conn.commit()

    def _ensure_column(self, name: str, spec: str) -> None:
        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(outbox)")}
        if name not in columns:
            self.conn.execute(f"ALTER TABLE outbox ADD COLUMN {name} {spec}")

    def add(
        self,
        local_media_path: str,
        bucket: str,
        object_key: str,
        payload: dict,
        state: str,
        next_attempt_at: float = 0.0,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO outbox(local_media_path, bucket, object_key, payload_json, state, next_attempt_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (local_media_path, bucket, object_key, json.dumps(payload), state, next_attempt_at),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_pending(self, limit: int = 50, now_ts: float | None = None) -> list[OutboxItem]:
        ready_at = time.time() if now_ts is None else now_ts
        cur = self.conn.execute(
            """
            SELECT id, local_media_path, bucket, object_key, payload_json, state, attempt_count, next_attempt_at
            FROM outbox
            WHERE state IN ('pending_upload', 'uploaded_pending_kafka')
              AND next_attempt_at <= ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (ready_at, limit),
        )
        return [OutboxItem(**dict(row)) for row in cur.fetchall()]

    def update_state(
        self,
        item_id: int,
        state: str,
        last_error: str | None = None,
        increment_attempt: bool = True,
        next_attempt_at: float | None = None,
        payload: dict | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE outbox
            SET state = ?,
                last_error = ?,
                attempt_count = attempt_count + ?,
                next_attempt_at = COALESCE(?, next_attempt_at),
                payload_json = COALESCE(?, payload_json)
            WHERE id = ?
            """,
            (
                state,
                last_error,
                1 if increment_attempt else 0,
                next_attempt_at,
                json.dumps(payload) if payload is not None else None,
                item_id,
            ),
        )
        self.conn.commit()

    def pending_count(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) AS cnt FROM outbox WHERE state IN ('pending_upload', 'uploaded_pending_kafka')")
        return int(cur.fetchone()["cnt"])

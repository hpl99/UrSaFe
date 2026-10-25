"""
Persistent Outbox with Priority Queueing and Exponential Backoff
Uses SQLite for crash-resilient durable queueing.
"""
from __future__ import annotations
import time
import json
import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from packages.protocol.envelope import MessageEnvelope
from packages.protocol.types import Priority, DeliveryState

@dataclass
class QueuedMessage:
    envelope: MessageEnvelope
    retry_count: int = 0
    next_retry_at: int = 0
    status: DeliveryState = DeliveryState.QUEUED_LOCAL

class PersistentOutbox:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox (
                    message_id TEXT PRIMARY KEY,
                    priority INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_retry_at INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    envelope_json TEXT NOT NULL
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_prio ON outbox(priority, next_retry_at, created_at)")

    def enqueue(self, envelope: MessageEnvelope) -> bool:
        """Enqueues an envelope. Deduplicates if message_id already exists."""
        now = int(time.time() * 1000)
        envelope_json = envelope.to_json()
        try:
            with self._conn:
                self._conn.execute("""
                    INSERT OR IGNORE INTO outbox (
                        message_id, priority, created_at, expires_at,
                        retry_count, next_retry_at, status, envelope_json
                    ) VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                """, (
                    envelope.message_id,
                    int(envelope.priority),
                    envelope.created_at,
                    envelope.expires_at,
                    now,
                    DeliveryState.QUEUED_LOCAL.value,
                    envelope_json,
                ))
            return True
        except Exception:
            return False

    def peek_next(self, current_time_ms: Optional[int] = None) -> Optional[MessageEnvelope]:
        """
        Pulls the highest priority message eligible for transmission.
        Strict ordering: Priority (1=EMERGENCY first), then next_retry_at, then created_at.
        Automatically purges expired messages.
        """
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
        self.purge_expired(now)

        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT envelope_json FROM outbox
            WHERE status IN ('QUEUED_LOCAL', 'FAILED')
              AND next_retry_at <= ?
              AND expires_at > ?
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
        """, (now, now))
        row = cursor.fetchone()
        if row:
            return MessageEnvelope.from_json(row[0])
        return None

    def mark_transmitted(self, message_id: str):
        with self._conn:
            self._conn.execute("""
                UPDATE outbox SET status = ? WHERE message_id = ?
            """, (DeliveryState.TRANSMITTED_MESH.value, message_id))

    def mark_acknowledged(self, message_id: str):
        with self._conn:
            self._conn.execute("""
                UPDATE outbox SET status = ? WHERE message_id = ?
            """, (DeliveryState.ACKNOWLEDGED.value, message_id))

    def record_retry_failure(self, message_id: str, base_delay_ms: int = 1000, max_delay_ms: int = 60000):
        """Applies exponential backoff with ceiling."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT retry_count FROM outbox WHERE message_id = ?", (message_id,))
        row = cursor.fetchone()
        if not row:
            return

        retries = row[0] + 1
        now = int(time.time() * 1000)
        delay = min(base_delay_ms * (2 ** (retries - 1)), max_delay_ms)
        next_retry = now + delay

        with self._conn:
            self._conn.execute("""
                UPDATE outbox
                SET retry_count = ?, next_retry_at = ?, status = ?
                WHERE message_id = ?
            """, (retries, next_retry, DeliveryState.FAILED.value, message_id))

    def purge_expired(self, current_time_ms: Optional[int] = None) -> int:
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
        with self._conn:
            cursor = self._conn.execute("DELETE FROM outbox WHERE expires_at <= ?", (now,))
            return cursor.rowcount

    def count(self) -> int:
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM outbox")
        return cursor.fetchone()[0]

    def clear(self):
        with self._conn:
            self._conn.execute("DELETE FROM outbox")

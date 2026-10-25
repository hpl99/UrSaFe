"""
Persistent Inbox with Deduplication Cache
"""
from __future__ import annotations
import time
import sqlite3
from typing import Optional, List, Dict, Any
from packages.protocol.envelope import MessageEnvelope

class PersistentInbox:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS inbox (
                    message_id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    received_at INTEGER NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    envelope_json TEXT NOT NULL
                )
            """)

    def has_seen(self, message_id: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM inbox WHERE message_id = ?", (message_id,))
        return cursor.fetchone() is not None

    def ingest(self, envelope: MessageEnvelope) -> bool:
        """Ingests envelope. Returns True if accepted (new), False if duplicate."""
        if self.has_seen(envelope.message_id):
            return False

        now = int(time.time() * 1000)
        with self._conn:
            self._conn.execute("""
                INSERT INTO inbox (message_id, sender_id, message_type, received_at, processed, envelope_json)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (
                envelope.message_id,
                envelope.sender_id,
                envelope.message_type.value,
                now,
                envelope.to_json(),
            ))
        return True

    def get_unprocessed(self) -> List[MessageEnvelope]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT envelope_json FROM inbox WHERE processed = 0 ORDER BY received_at ASC")
        return [MessageEnvelope.from_json(row[0]) for row in cursor.fetchall()]

    def mark_processed(self, message_id: str):
        with self._conn:
            self._conn.execute("UPDATE inbox SET processed = 1 WHERE message_id = ?", (message_id,))

    def get_inventory_ids(self) -> List[str]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT message_id FROM inbox")
        return [row[0] for row in cursor.fetchall()]

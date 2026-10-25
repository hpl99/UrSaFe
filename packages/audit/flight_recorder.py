"""
Flight Recorder
Append-only cryptographic hash chain recording all state transitions.
"""
from __future__ import annotations
import json
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

GENESIS_PREVIOUS_HASH = "0" * 64

@dataclass
class AuditEvent:
    event_id: str
    timestamp: int
    previous_hash: str
    actor: str
    action: str
    target_object: str
    reason: str
    payload_hash: str
    signature: str = ""
    event_hash: str = ""

    def compute_hash(self) -> str:
        """Computes deterministic SHA-256 hash of event components."""
        data_str = (
            f"{self.event_id}:{self.timestamp}:{self.previous_hash}:"
            f"{self.actor}:{self.action}:{self.target_object}:{self.reason}:"
            f"{self.payload_hash}:{self.signature}"
        )
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEvent:
        return cls(**data)

class FlightRecorder:
    """Manages append-only sequence of AuditEvents with SHA-256 chain verification."""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._events: List[AuditEvent] = []

    @property
    def events(self) -> List[AuditEvent]:
        return list(self._events)

    @property
    def latest_hash(self) -> str:
        if not self._events:
            return GENESIS_PREVIOUS_HASH
        return self._events[-1].event_hash

    def record_event(
        self,
        actor: str,
        action: str,
        target_object: str,
        reason: str = "",
        payload: Optional[Dict[str, Any]] = None,
        signature: str = "",
        timestamp: Optional[int] = None,
    ) -> AuditEvent:
        now = timestamp if timestamp is not None else int(time.time() * 1000)
        prev_hash = self.latest_hash
        event_id = str(uuid.uuid4())

        payload_bytes = json.dumps(payload or {}, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        event = AuditEvent(
            event_id=event_id,
            timestamp=now,
            previous_hash=prev_hash,
            actor=actor,
            action=action,
            target_object=target_object,
            reason=reason,
            payload_hash=payload_hash,
            signature=signature,
        )
        event.event_hash = event.compute_hash()
        self._events.append(event)
        return event

    def export_chain(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._events]

    def load_chain(self, raw_events: List[Dict[str, Any]]):
        self._events = [AuditEvent.from_dict(d) for d in raw_events]

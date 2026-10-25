"""
State-Based CRDTs for Distributed Emergency State
Satisfies mathematical properties:
  - Idempotence:     A ⊔ A = A
  - Commutativity:   A ⊔ B = B ⊔ A
  - Associativity:   (A ⊔ B) ⊔ C = A ⊔ (B ⊔ C)
"""
from __future__ import annotations
from typing import Dict, Any, Set, Tuple, Optional, Generic, TypeVar
from dataclasses import dataclass, field
from .vector_clock import VectorClock

T = TypeVar("T")

@dataclass
class LWWRegister(Generic[T]):
    """Last-Write-Wins Register with timestamp and deterministic node tie-breaker."""
    value: T
    timestamp: int
    node_id: str

    def merge(self, other: LWWRegister[T]) -> LWWRegister[T]:
        if self.timestamp > other.timestamp:
            return LWWRegister(self.value, self.timestamp, self.node_id)
        elif other.timestamp > self.timestamp:
            return LWWRegister(other.value, other.timestamp, other.node_id)
        else:
            # Deterministic tie-break on node_id string
            winner_node = max(self.node_id, other.node_id)
            val = self.value if self.node_id == winner_node else other.value
            return LWWRegister(val, self.timestamp, winner_node)

@dataclass
class ORSet:
    """Observed-Remove Set: elements tagged with unique add tokens and tombstone set."""
    entries: Set[Tuple[str, str]] = field(default_factory=set) # (element, token)
    tombstones: Set[str] = field(default_factory=set)          # token

    def add(self, element: str, token: str):
        self.entries.add((element, token))

    def remove(self, element: str):
        for elem, tok in list(self.entries):
            if elem == element:
                self.tombstones.add(tok)

    def read(self) -> Set[str]:
        return {elem for elem, tok in self.entries if tok not in self.tombstones}

    def merge(self, other: ORSet) -> ORSet:
        merged_entries = self.entries.union(other.entries)
        merged_tombstones = self.tombstones.union(other.tombstones)
        return ORSet(entries=merged_entries, tombstones=merged_tombstones)

class IncidentCRDTState:
    """
    CRDT representation of an Emergency Incident replicated across mesh nodes.
    Combines VectorClock, LWWRegisters for status/assignments, and ORSet for responder tags.
    """
    def __init__(
        self,
        incident_id: str,
        creator_node: str,
        initial_status: str = "REPORTED",
        initial_timestamp: int = 0,
    ):
        self.incident_id = incident_id
        self.clock = VectorClock()
        self.clock.increment(creator_node)
        self.status = LWWRegister(initial_status, initial_timestamp, creator_node)
        self.assigned_responder = LWWRegister("", initial_timestamp, creator_node)
        self.people_affected = LWWRegister(1, initial_timestamp, creator_node)
        self.acknowledged_by = ORSet()

    def update_status(self, new_status: str, timestamp: int, node_id: str):
        self.clock.increment(node_id)
        candidate = LWWRegister(new_status, timestamp, node_id)
        self.status = self.status.merge(candidate)

    def assign_responder(self, responder_id: str, timestamp: int, node_id: str):
        self.clock.increment(node_id)
        candidate = LWWRegister(responder_id, timestamp, node_id)
        self.assigned_responder = self.assigned_responder.merge(candidate)

    def update_people(self, count: int, timestamp: int, node_id: str):
        self.clock.increment(node_id)
        candidate = LWWRegister(count, timestamp, node_id)
        self.people_affected = self.people_affected.merge(candidate)

    def merge(self, other: IncidentCRDTState) -> IncidentCRDTState:
        """State-based CRDT join merge."""
        merged = IncidentCRDTState(self.incident_id, self.status.node_id)
        merged.clock = self.clock.merge(other.clock)
        merged.status = self.status.merge(other.status)
        merged.assigned_responder = self.assigned_responder.merge(other.assigned_responder)
        merged.people_affected = self.people_affected.merge(other.people_affected)
        merged.acknowledged_by = self.acknowledged_by.merge(other.acknowledged_by)
        return merged

    def to_snapshot(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "clock": self.clock.to_dict(),
            "status": self.status.value,
            "assigned_responder": self.assigned_responder.value,
            "people_affected": self.people_affected.value,
            "acknowledged_by": sorted(list(self.acknowledged_by.read())),
        }

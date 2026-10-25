"""
Vector Clock Implementation
Tracks causal history across distributed nodes in partitioned mesh networks.
"""
from __future__ import annotations
from typing import Dict, Any, Optional

class VectorClock:
    def __init__(self, clock_dict: Optional[Dict[str, int]] = None):
        self._clock: Dict[str, int] = dict(clock_dict) if clock_dict else {}

    @property
    def clock(self) -> Dict[str, int]:
        return dict(self._clock)

    def increment(self, node_id: str) -> VectorClock:
        """Increments the local logical counter for the given node."""
        self._clock[node_id] = self._clock.get(node_id, 0) + 1
        return self

    def get(self, node_id: str) -> int:
        return self._clock.get(node_id, 0)

    def merge(self, other: VectorClock) -> VectorClock:
        """Pointwise maximum merge (least upper bound join)."""
        all_nodes = set(self._clock.keys()).union(other._clock.keys())
        merged = {node: max(self.get(node), other.get(node)) for node in all_nodes}
        return VectorClock(merged)

    def dominates(self, other: VectorClock) -> bool:
        """Returns True if self is strictly greater than or equal to other in all dimensions."""
        all_nodes = set(self._clock.keys()).union(other._clock.keys())
        greater_or_equal = all(self.get(n) >= other.get(n) for n in all_nodes)
        strictly_greater = any(self.get(n) > other.get(n) for n in all_nodes)
        return greater_or_equal and strictly_greater

    def is_concurrent_with(self, other: VectorClock) -> bool:
        """Returns True if neither vector clock dominates the other (parallel partition updates)."""
        return not self.dominates(other) and not other.dominates(self) and self._clock != other._clock

    def to_dict(self) -> Dict[str, int]:
        return dict(self._clock)

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> VectorClock:
        return cls(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorClock):
            return False
        all_nodes = set(self._clock.keys()).union(other._clock.keys())
        return all(self.get(n) == other.get(n) for n in all_nodes)

    def copy(self) -> VectorClock:
        return VectorClock(dict(self._clock))

"""
Multi-Signal Sybil and Anomaly Detection
Identifies phantom identity clusters, broadcast flooding, lure relays, and impossible velocity leaps.
"""
from __future__ import annotations
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from packages.protocol.envelope import Location

@dataclass
class SybilAnomalyFlag:
    anomaly_type: str
    severity: str        # WARNING, CRITICAL
    evidence: str
    detected_at: int = field(default_factory=lambda: int(time.time() * 1000))

class SybilDetector:
    def __init__(
        self,
        max_rate_per_minute: int = 30,
        max_velocity_kmh: float = 180.0,
        max_identities_per_mac: int = 3,
    ):
        self.max_rate = max_rate_per_minute
        self.max_velocity_kmh = max_velocity_kmh
        self.max_identities_per_mac = max_identities_per_mac

        # Tracking state
        self._tx_timestamps: Dict[str, List[int]] = {}          # node_id -> timestamps
        self._last_locations: Dict[str, Location] = {}          # node_id -> Location
        self._mac_to_identities: Dict[str, Set[str]] = {}       # physical_radio_id -> Set[node_id]
        self._witness_history: Dict[str, Set[str]] = {}         # node_id -> Set[witness_node_ids]

    def record_transmission(
        self,
        node_id: str,
        physical_radio_id: str,
        witness_id: str,
        location: Optional[Location] = None,
        timestamp: Optional[int] = None,
    ) -> List[SybilAnomalyFlag]:
        now = timestamp if timestamp is not None else int(time.time() * 1000)
        flags: List[SybilAnomalyFlag] = []

        # 1. Physical MAC Sybil Cluster Check
        if physical_radio_id:
            mac_nodes = self._mac_to_identities.setdefault(physical_radio_id, set())
            mac_nodes.add(node_id)
            if len(mac_nodes) > self.max_identities_per_mac:
                flags.append(SybilAnomalyFlag(
                    anomaly_type="SYBIL_CLUSTER",
                    severity="CRITICAL",
                    evidence=f"Physical radio '{physical_radio_id}' is generating {len(mac_nodes)} distinct node identities."
                ))

        # 2. Transmission Rate Flooding Check
        history = self._tx_timestamps.setdefault(node_id, [])
        one_min_ago = now - 60000
        recent = [t for t in history if t > one_min_ago]
        recent.append(now)
        self._tx_timestamps[node_id] = recent

        if len(recent) > self.max_rate:
            flags.append(SybilAnomalyFlag(
                anomaly_type="BROADCAST_FLOODING",
                severity="CRITICAL",
                evidence=f"Node emitted {len(recent)} packets in 60s (threshold: {self.max_rate})."
            ))

        # 3. Witness Diversity Tracking
        if witness_id:
            witnesses = self._witness_history.setdefault(node_id, set())
            witnesses.add(witness_id)

        # 4. Movement Kinematic Check (Impossible Velocity Leap)
        if location:
            prev_loc = self._last_locations.get(node_id)
            if prev_loc:
                time_diff_sec = (location.timestamp - prev_loc.timestamp) / 1000.0
                if time_diff_sec > 0:
                    # Approx distance in km (1 deg ~ 111 km)
                    dlat = (location.latitude - prev_loc.latitude) * 111.0
                    dlon = (location.longitude - prev_loc.longitude) * 111.0
                    distance_km = (dlat**2 + dlon**2)**0.5
                    velocity_kmh = (distance_km / time_diff_sec) * 3600.0
                    if velocity_kmh > self.max_velocity_kmh:
                        flags.append(SybilAnomalyFlag(
                            anomaly_type="TELEPORTATION_ANOMALY",
                            severity="WARNING",
                            evidence=f"Node moved {distance_km:.1f} km in {time_diff_sec:.1f}s ({velocity_kmh:.0f} km/h)."
                        ))
            self._last_locations[node_id] = location

        return flags

    def get_witness_count(self, node_id: str) -> int:
        return len(self._witness_history.get(node_id, set()))

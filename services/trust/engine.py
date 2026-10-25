"""
Multi-Signal Trust Engine
Evaluates orthogonal trust vectors and outputs discrete operational tiers.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .sybil_detector import SybilDetector, SybilAnomalyFlag

class TrustTier(str, Enum):
    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    ISOLATED = "ISOLATED"

@dataclass
class TrustAssessment:
    node_id: str
    tier: TrustTier
    composite_score: float
    identity_trust: float
    credential_trust: float
    behavioral_trust: float
    network_trust: float
    reputation_score: float
    active_flags: List[SybilAnomalyFlag]
    rationale: str

class MultiSignalTrustEngine:
    def __init__(self, sybil_detector: Optional[SybilDetector] = None):
        self.detector = sybil_detector or SybilDetector()
        self._node_creation_times: Dict[str, int] = {}
        self._manual_isolations: Set[str] = set()

    def register_node(self, node_id: str, created_at: Optional[int] = None):
        if node_id not in self._node_creation_times:
            self._node_creation_times[node_id] = created_at or int(time.time() * 1000)

    def isolate_node(self, node_id: str):
        self._manual_isolations.add(node_id)

    def assess_node(
        self,
        node_id: str,
        has_valid_credential: bool = False,
        recent_flags: Optional[List[SybilAnomalyFlag]] = None,
        verified_rescues: int = 0,
        current_time_ms: Optional[int] = None,
    ) -> TrustAssessment:
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
        flags = recent_flags or []

        if node_id in self._manual_isolations:
            return TrustAssessment(
                node_id=node_id,
                tier=TrustTier.ISOLATED,
                composite_score=0.0,
                identity_trust=0.0,
                credential_trust=0.0,
                behavioral_trust=0.0,
                network_trust=0.0,
                reputation_score=0.0,
                active_flags=[],
                rationale="Manually isolated by incident commander.",
            )

        # 1. Identity Trust (Age of cryptographic identity)
        created_at = self._node_creation_times.get(node_id, now)
        age_hours = (now - created_at) / 3600000.0
        identity_trust = min(1.0, max(0.2, age_hours / 24.0))

        # 2. Credential Trust (W3C Passport validity)
        credential_trust = 1.0 if has_valid_credential else 0.4

        # 3. Behavioral Trust (Penalized by active Sybil/flooding flags)
        critical_flags = [f for f in flags if f.severity == "CRITICAL"]
        warning_flags = [f for f in flags if f.severity == "WARNING"]
        behavioral_trust = 1.0 - (len(critical_flags) * 0.45) - (len(warning_flags) * 0.15)
        behavioral_trust = max(0.0, min(1.0, behavioral_trust))

        # 4. Network Trust (Witness diversity)
        witness_count = self.detector.get_witness_count(node_id)
        network_trust = min(1.0, max(0.3, witness_count / 3.0))

        # 5. Reputation Score (Verified dual-signed rescues)
        reputation_score = min(1.0, max(0.1, 0.1 + (verified_rescues * 0.15)))

        # Weighted composite score
        composite = (
            (0.15 * identity_trust) +
            (0.25 * credential_trust) +
            (0.35 * behavioral_trust) +
            (0.15 * network_trust) +
            (0.10 * reputation_score)
        )

        # Tier assignment
        if len(critical_flags) >= 2 or composite < 0.25:
            tier = TrustTier.ISOLATED
            rationale = "CRITICAL: Multiple critical behavioral or Sybil anomalies detected. Node isolated."
        elif len(critical_flags) == 1 or composite < 0.50:
            tier = TrustTier.HIGH_RISK
            rationale = "HIGH RISK: Severe anomaly detected (e.g. broadcast flooding or MAC clustering)."
        elif len(warning_flags) > 0 or composite < 0.70:
            tier = TrustTier.SUSPICIOUS
            rationale = "SUSPICIOUS: Minor velocity or rate anomalies observed."
        else:
            tier = TrustTier.NORMAL
            rationale = "NORMAL: Healthy operating profile and verified trust signals."

        return TrustAssessment(
            node_id=node_id,
            tier=tier,
            composite_score=round(composite, 3),
            identity_trust=round(identity_trust, 2),
            credential_trust=round(credential_trust, 2),
            behavioral_trust=round(behavioral_trust, 2),
            network_trust=round(network_trust, 2),
            reputation_score=round(reputation_score, 2),
            active_flags=flags,
            rationale=rationale,
        )

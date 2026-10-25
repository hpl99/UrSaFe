"""
Mesh Link Metrics and Explainable Route Scoring Function
"""
from typing import Dict, Any
from dataclasses import dataclass
from packages.protocol.types import Priority

@dataclass
class LinkMetrics:
    neighbor_id: str
    rssi_dbm: int             # Typically -120 to -40 dBm
    snr_db: float             # Typically -10 to +15 dB
    packet_loss_rate: float   # 0.0 to 1.0
    battery_level: float      # 0.0 to 1.0
    queue_pressure: float     # 0.0 to 1.0 (ratio of filled buffer)
    etx: float = 1.0          # Expected Transmission Count

    def __post_init__(self):
        # ETX = 1 / (1 - packet_loss_rate)
        if self.packet_loss_rate < 0.99:
            self.etx = 1.0 / max(0.01, (1.0 - self.packet_loss_rate))
        else:
            self.etx = 100.0

@dataclass
class RouteScore:
    score: float
    is_viable: bool
    breakdown: Dict[str, float]
    explanation: str

class RouteScorer:
    @staticmethod
    def score_route(
        metrics: LinkMetrics,
        hop_count: int,
        priority: Priority,
        trust_score: float = 1.0,
    ) -> RouteScore:
        """
        Explainable route scoring function:
          Score = w_etx * (1/ETX) + w_rssi * RSSI_norm + w_snr * SNR_norm
                  + w_bat * Battery + w_trust * Trust - w_hop * Hops - w_queue * Queue
        Higher score represents a superior forwarding candidate.
        """
        # Normalized RSSI: -120 dBm (0.0) to -40 dBm (1.0)
        rssi_norm = max(0.0, min(1.0, (metrics.rssi_dbm + 120.0) / 80.0))

        # Normalized SNR: -10 dB (0.0) to +15 dB (1.0)
        snr_norm = max(0.0, min(1.0, (metrics.snr_db + 10.0) / 25.0))

        # Reliability factor (inverse ETX)
        inv_etx = max(0.0, min(1.0, 1.0 / metrics.etx))

        # Hop penalty (normalized over max 7 hops)
        hop_penalty = min(1.0, hop_count / 7.0)

        # Weights
        w_etx = 0.30
        w_rssi = 0.15
        w_snr = 0.15
        w_bat = 0.15
        w_trust = 0.15
        w_queue = 0.10

        composite = (
            (w_etx * inv_etx) +
            (w_rssi * rssi_norm) +
            (w_snr * snr_norm) +
            (w_bat * metrics.battery_level) +
            (w_trust * trust_score) -
            (0.10 * hop_penalty) -
            (w_queue * metrics.queue_pressure)
        )

        # Emergency boost: Emergency packets tolerate lower battery or higher queue pressure
        if priority == Priority.EMERGENCY:
            composite += 0.20

        is_viable = metrics.etx < 10.0 and metrics.battery_level > 0.05 and trust_score >= 0.2

        explanation = (
            f"Route Score {composite:.2f} (ETX: {metrics.etx:.1f}, RSSI: {metrics.rssi_dbm}dBm, "
            f"SNR: {metrics.snr_db}dB, Battery: {int(metrics.battery_level*100)}%, Hops: {hop_count}, "
            f"Priority: {priority.name})"
        )

        return RouteScore(
            score=round(composite, 3),
            is_viable=is_viable,
            breakdown={
                "inv_etx": inv_etx,
                "rssi_norm": rssi_norm,
                "snr_norm": snr_norm,
                "battery": metrics.battery_level,
                "trust": trust_score,
                "hop_penalty": hop_penalty,
                "queue_pressure": metrics.queue_pressure,
            },
            explanation=explanation,
        )

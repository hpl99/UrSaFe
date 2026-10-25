"""
Unit Tests for Multi-Signal Trust Engine and Sybil Defense
"""
import pytest
from packages.protocol.envelope import Location
from services.trust.sybil_detector import SybilDetector
from services.trust.engine import MultiSignalTrustEngine, TrustTier

def test_normal_node_trust_assessment():
    detector = SybilDetector()
    engine = MultiSignalTrustEngine(detector)

    engine.register_node("resp_alpha", created_at=1000)

    # Clean transmissions with independent witnesses
    flags = detector.record_transmission("resp_alpha", "RADIO_01", "WITNESS_TOWER_A")
    detector.record_transmission("resp_alpha", "RADIO_01", "WITNESS_TOWER_B")
    detector.record_transmission("resp_alpha", "RADIO_01", "WITNESS_TOWER_C")

    assert len(flags) == 0

    assessment = engine.assess_node("resp_alpha", has_valid_credential=True, verified_rescues=3)
    assert assessment.tier == TrustTier.NORMAL
    assert assessment.composite_score >= 0.70
    assert assessment.credential_trust == 1.0

def test_sybil_cluster_detection():
    detector = SybilDetector(max_identities_per_mac=2)
    engine = MultiSignalTrustEngine(detector)

    # Single physical radio emits 3 different node identities
    detector.record_transmission("fake_node_1", "ROGUE_RADIO_MAC_FF", "TOWER_A")
    detector.record_transmission("fake_node_2", "ROGUE_RADIO_MAC_FF", "TOWER_A")
    flags_3 = detector.record_transmission("fake_node_3", "ROGUE_RADIO_MAC_FF", "TOWER_A")

    assert any(f.anomaly_type == "SYBIL_CLUSTER" for f in flags_3)

    assessment = engine.assess_node("fake_node_3", recent_flags=flags_3)
    assert assessment.tier in (TrustTier.HIGH_RISK, TrustTier.ISOLATED)

def test_broadcast_flooding_detection():
    detector = SybilDetector(max_rate_per_minute=5)
    engine = MultiSignalTrustEngine(detector)

    flags = []
    for _ in range(7):
        flags.extend(detector.record_transmission("flood_bot", "RADIO_X", "TOWER_A"))

    assert any(f.anomaly_type == "BROADCAST_FLOODING" for f in flags)
    assessment = engine.assess_node("flood_bot", recent_flags=flags)
    assert assessment.tier in (TrustTier.HIGH_RISK, TrustTier.ISOLATED)

def test_impossible_velocity_leap():
    detector = SybilDetector(max_velocity_kmh=150.0)

    # Location 1: Mumbai at t=0
    loc1 = Location(latitude=19.0760, longitude=72.8777, timestamp=100000)
    detector.record_transmission("teleport_node", "R1", "W1", location=loc1)

    # Location 2: Pune (150km away) at t=60 seconds later (impossible 9000 km/h)
    loc2 = Location(latitude=18.5204, longitude=73.8567, timestamp=160000)
    flags = detector.record_transmission("teleport_node", "R1", "W1", location=loc2)

    assert any(f.anomaly_type == "TELEPORTATION_ANOMALY" for f in flags)

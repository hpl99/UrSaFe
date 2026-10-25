"""
UrSafe Red Team Automated Attack and Security Defense Test Suite
Executes controlled attacks:
  1. Packet Tampering Attack
  2. Packet Replay Attack
  3. Credential Forgery Attack
  4. Revoked Credential Stale Attack
  5. Sybil Cluster Attack
  6. Message Broadcast Flooding Attack
  7. Impossible Teleportation Location Spoofing Attack
  8. Rescue Receipt Collusion Attack
Each test verifies: INJECT -> DETECT -> MITIGATE -> LOG.
"""
import time
import pytest
from packages.crypto.keys import KeyPair, Ed25519KeyPair
from packages.crypto.replay import ReplayFilter
from packages.crypto.keystore import CryptoKeystore
from packages.protocol.envelope import MessageEnvelope, Location
from services.credential.passport import PassportIssuer, OfflinePassportVerifier, CredentialStatus
from services.credential.revocation import RevocationList
from services.receipts.receipt_engine import RescueReceiptEngine
from services.trust.sybil_detector import SybilDetector
from services.trust.engine import MultiSignalTrustEngine, TrustTier

def test_attack_1_packet_tampering():
    """Attack: Adversary intercepts packet on radio mesh and modifies victim count."""
    keystore = CryptoKeystore()
    loc = Location(latitude=19.0, longitude=72.8)
    env = MessageEnvelope.create_sos(keystore.node_id, "FLOOD", "CRITICAL", 2, loc)
    keystore.sign_envelope(env)

    # MITM Attack: Alter payload from 2 to 50 victims
    env.payload["people_affected"] = 50

    # Defense: Keystore verification rejects the tampered packet
    is_valid = keystore.verify_envelope(env, keystore.public_signing_bytes)
    assert is_valid is False, "MITIGATION: Tampered envelope must be rejected"

def test_attack_2_packet_replay():
    """Attack: Adversary captures legitimate SOS packet and continuously replays it."""
    replay_filter = ReplayFilter(window_size=32)
    sender = "victim_station_01"

    # Packet seq 1 arrives
    assert replay_filter.is_valid_and_update(sender, 1) is True
    # Replay of packet seq 1 arrives
    assert replay_filter.is_valid_and_update(sender, 1) is False, "MITIGATION: Replay must be dropped"

def test_attack_3_credential_forgery():
    """Attack: Rogue volunteer creates a self-signed or tampered Responder Passport claiming SURGEON role."""
    rogue_issuer = Ed25519KeyPair.generate()
    forged_passport = PassportIssuer("fake_authority", rogue_issuer).issue_passport(
        subject_id="rogue_user",
        roles=["TRAUMA_SURGEON"],
        skills=["SURGERY"],
        certifications=["FORGED_CERT"],
    )

    verifier = OfflinePassportVerifier()
    # Verifier only trusts official NDRF authority
    official_authority = Ed25519KeyPair.generate()
    verifier.add_trusted_issuer("official_ndrf", official_authority.public_bytes)

    res = verifier.verify_passport(forged_passport, RevocationList())
    assert res["valid"] is False
    assert res["status"] == CredentialStatus.UNKNOWN.value, "MITIGATION: Forged authority must be UNKNOWN"

def test_attack_4_revoked_credential():
    """Attack: Expelled responder attempts to use previously issued credential."""
    official_authority = Ed25519KeyPair.generate()
    issuer = PassportIssuer("official_ndrf", official_authority)
    passport = issuer.issue_passport("bad_actor", ["MEDIC"], ["FIRST_AID"], ["CERT_01"])

    verifier = OfflinePassportVerifier()
    verifier.add_trusted_issuer("official_ndrf", official_authority.public_bytes)

    revocation_list = RevocationList()
    revocation_list.revoke(passport.credential_id)

    res = verifier.verify_passport(passport, revocation_list)
    assert res["valid"] is False
    assert res["status"] == CredentialStatus.REVOKED.value, "MITIGATION: Revoked credential must be blocked"

def test_attack_5_sybil_cluster():
    """Attack: Single radio hardware spins up multiple virtual identities to swamp the mesh."""
    detector = SybilDetector(max_identities_per_mac=2)
    engine = MultiSignalTrustEngine(detector)

    flags = []
    flags.extend(detector.record_transmission("phantom_1", "HARDWARE_RADIO_AA", "TOWER_1"))
    flags.extend(detector.record_transmission("phantom_2", "HARDWARE_RADIO_AA", "TOWER_1"))
    flags.extend(detector.record_transmission("phantom_3", "HARDWARE_RADIO_AA", "TOWER_1"))

    assert any(f.anomaly_type == "SYBIL_CLUSTER" for f in flags)
    assessment = engine.assess_node("phantom_3", recent_flags=flags)
    assert assessment.tier in (TrustTier.HIGH_RISK, TrustTier.ISOLATED), "MITIGATION: Sybil cluster isolated"

def test_attack_6_broadcast_flooding():
    """Attack: Malicious node attempts Denial of Service by broadcasting hundreds of packets."""
    detector = SybilDetector(max_rate_per_minute=10)
    flags = []
    for _ in range(15):
        flags.extend(detector.record_transmission("flooder", "RADIO_DOS", "TOWER_1"))

    assert any(f.anomaly_type == "BROADCAST_FLOODING" for f in flags), "MITIGATION: Flooding detected"

def test_attack_7_teleportation_spoofing():
    """Attack: Adversary injects false location jumps thousands of kilometers in seconds."""
    detector = SybilDetector(max_velocity_kmh=160.0)
    loc_start = Location(latitude=19.0, longitude=72.8, timestamp=1000)
    detector.record_transmission("spoof_node", "RADIO_1", "TOWER_1", location=loc_start)

    loc_teleport = Location(latitude=28.6, longitude=77.2, timestamp=2000) # Mumbai to Delhi in 1 second!
    flags = detector.record_transmission("spoof_node", "RADIO_1", "TOWER_1", location=loc_teleport)

    assert any(f.anomaly_type == "TELEPORTATION_ANOMALY" for f in flags), "MITIGATION: Spoofed leap flagged"

def test_attack_8_rescue_receipt_collusion():
    """Attack: Two colluding nodes repeatedly generate fake rescue receipts to artificially boost reputation."""
    v_kp = Ed25519KeyPair.generate()
    r_kp = Ed25519KeyPair.generate()
    engine = RescueReceiptEngine(max_pair_frequency_per_day=2)
    loc = Location(latitude=19.0, longitude=72.8)

    # 1st rescue: OK
    r1 = engine.create_and_sign_receipt("i1", "v1", "r1", v_kp, r_kp, loc, "EVACUATED")
    assert engine.verify_receipt(r1, v_kp.public_bytes, r_kp.public_bytes)["reputation_awarded"] is True

    # 2nd rescue: OK
    r2 = engine.create_and_sign_receipt("i2", "v1", "r1", v_kp, r_kp, loc, "EVACUATED")
    assert engine.verify_receipt(r2, v_kp.public_bytes, r_kp.public_bytes)["reputation_awarded"] is True

    # 3rd rescue on same day: Collusion detected, reputation award denied!
    r3 = engine.create_and_sign_receipt("i3", "v1", "r1", v_kp, r_kp, loc, "EVACUATED")
    v3 = engine.verify_receipt(r3, v_kp.public_bytes, r_kp.public_bytes)
    assert v3["collusion_risk"] is True
    assert v3["reputation_awarded"] is False, "MITIGATION: Fake colluding reputation denied"

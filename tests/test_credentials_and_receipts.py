"""
Unit Tests for W3C Responder Passports and Rescue Receipts
"""
import time
import pytest
from packages.crypto.keys import Ed25519KeyPair
from packages.protocol.envelope import Location
from services.credential.passport import (
    PassportIssuer, OfflinePassportVerifier, CredentialStatus
)
from services.credential.revocation import RevocationList
from services.receipts.receipt_engine import RescueReceiptEngine

def test_passport_lifecycle_and_verification():
    org_keypair = Ed25519KeyPair.generate()
    issuer = PassportIssuer("ndrf_india_org", org_keypair)

    passport = issuer.issue_passport(
        subject_id="responder_ramesh",
        roles=["MEDIC", "SEARCH_AND_RESCUE"],
        skills=["ADVANCED_TRAUMA_CARE", "WATER_RESCUE"],
        certifications=["NDRF_CERT_2026_A1"],
        validity_days=30,
    )

    verifier = OfflinePassportVerifier()
    verifier.add_trusted_issuer("ndrf_india_org", org_keypair.public_bytes)

    revocation_list = RevocationList()

    # 1. Active valid passport
    res = verifier.verify_passport(passport, revocation_list)
    assert res["status"] == CredentialStatus.VERIFIED.value
    assert res["valid"] is True

    # 2. Stale revocation list (>24 hours old)
    now = int(time.time() * 1000)
    stale_rev_list = RevocationList(last_updated_at=now - (36 * 3600 * 1000))
    res_stale = verifier.verify_passport(passport, stale_rev_list)
    assert res_stale["status"] == CredentialStatus.VERIFIED_REVOCATION_STALE.value
    assert res_stale["valid"] is True

    # 3. Explicitly revoked credential
    revocation_list.revoke(passport.credential_id)
    res_revoked = verifier.verify_passport(passport, revocation_list)
    assert res_revoked["status"] == CredentialStatus.REVOKED.value
    assert res_revoked["valid"] is False

    # 4. Expired credential
    expired_time = passport.expires_at + 1000
    res_expired = verifier.verify_passport(passport, RevocationList(), current_time_ms=expired_time)
    assert res_expired["status"] == CredentialStatus.EXPIRED.value
    assert res_expired["valid"] is False

    # 5. Tampered role
    passport.roles.append("PILOT")
    res_tampered = verifier.verify_passport(passport, RevocationList())
    assert res_tampered["valid"] is False

def test_dual_confirmed_rescue_receipt_and_collusion():
    victim_kp = Ed25519KeyPair.generate()
    responder_kp = Ed25519KeyPair.generate()
    engine = RescueReceiptEngine(max_pair_frequency_per_day=2)

    loc = Location(latitude=19.0760, longitude=72.8777)

    # First legitimate rescue
    r1 = engine.create_and_sign_receipt(
        incident_id="inc_01",
        victim_id="vic_01",
        responder_id="resp_01",
        victim_keypair=victim_kp,
        responder_keypair=responder_kp,
        location=loc,
        outcome="EVACUATED",
    )

    v1 = engine.verify_receipt(r1, victim_kp.public_bytes, responder_kp.public_bytes)
    assert v1["valid"] is True
    assert v1["collusion_risk"] is False
    assert v1["reputation_awarded"] is True

    # Second legitimate rescue
    r2 = engine.create_and_sign_receipt(
        incident_id="inc_02",
        victim_id="vic_01",
        responder_id="resp_01",
        victim_keypair=victim_kp,
        responder_keypair=responder_kp,
        location=loc,
        outcome="STABILIZED",
    )
    v2 = engine.verify_receipt(r2, victim_kp.public_bytes, responder_kp.public_bytes)
    assert v2["valid"] is True
    assert v2["collusion_risk"] is False

    # Third rapid rescue on same day triggers anti-collusion protection
    r3 = engine.create_and_sign_receipt(
        incident_id="inc_03",
        victim_id="vic_01",
        responder_id="resp_01",
        victim_keypair=victim_kp,
        responder_keypair=responder_kp,
        location=loc,
        outcome="SHELTERED",
    )
    v3 = engine.verify_receipt(r3, victim_kp.public_bytes, responder_kp.public_bytes)
    assert v3["valid"] is True
    assert v3["collusion_risk"] is True
    assert v3["reputation_awarded"] is False
    assert "COLLUSION SUSPECTED" in v3["reason"]

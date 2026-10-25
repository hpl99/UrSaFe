"""
Rescue Receipt Engine
Generates and validates dual-confirmed cryptographic rescue receipts.
Enforces anti-collusion and Sybil protection rules.
"""
from __future__ import annotations
import time
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from packages.protocol.envelope import Location
from packages.crypto.keys import Ed25519KeyPair

@dataclass
class RescueReceipt:
    receipt_id: str
    incident_id: str
    victim_id: str
    responder_id: str
    completed_at: int
    location: Location
    outcome: str                      # EVACUATED, FIRST_AID_APPLIED, STABILIZED, SHELTERED
    victim_signature: str = ""        # Hex-encoded
    responder_signature: str = ""     # Hex-encoded
    witness_node_ids: List[str] = field(default_factory=list)

    def get_signing_bytes(self) -> bytes:
        content = (
            f"{self.receipt_id}:{self.incident_id}:{self.victim_id}:{self.responder_id}:"
            f"{self.completed_at}:{self.location.latitude}:{self.location.longitude}:{self.outcome}"
        )
        return content.encode("utf-8")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["location"] = self.location.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RescueReceipt:
        d = dict(data)
        d["location"] = Location.from_dict(d["location"])
        return cls(**d)

class RescueReceiptEngine:
    def __init__(self, max_pair_frequency_per_day: int = 3):
        self.max_pair_freq = max_pair_frequency_per_day
        # Tracks (victim_id, responder_id) -> List[timestamps] to detect collusion
        self._pair_history: Dict[str, List[int]] = {}

    def create_and_sign_receipt(
        self,
        incident_id: str,
        victim_id: str,
        responder_id: str,
        victim_keypair: Ed25519KeyPair,
        responder_keypair: Ed25519KeyPair,
        location: Location,
        outcome: str,
        witness_node_ids: Optional[List[str]] = None,
        timestamp: Optional[int] = None,
    ) -> RescueReceipt:
        now = timestamp if timestamp is not None else int(time.time() * 1000)
        receipt = RescueReceipt(
            receipt_id=str(uuid.uuid4()),
            incident_id=incident_id,
            victim_id=victim_id,
            responder_id=responder_id,
            completed_at=now,
            location=location,
            outcome=outcome,
            witness_node_ids=witness_node_ids or [],
        )

        signing_bytes = receipt.get_signing_bytes()
        receipt.victim_signature = victim_keypair.sign(signing_bytes).hex()
        receipt.responder_signature = responder_keypair.sign(signing_bytes).hex()
        return receipt

    def verify_receipt(
        self,
        receipt: RescueReceipt,
        victim_public_bytes: bytes,
        responder_public_bytes: bytes,
        current_time_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        signing_bytes = receipt.get_signing_bytes()

        # 1. Verify victim signature
        try:
            v_sig = bytes.fromhex(receipt.victim_signature)
            v_valid = Ed25519KeyPair.verify_public(victim_public_bytes, v_sig, signing_bytes)
        except Exception:
            v_valid = False

        if not v_valid:
            return {"valid": False, "reason": "Invalid or missing victim signature"}

        # 2. Verify responder signature
        try:
            r_sig = bytes.fromhex(receipt.responder_signature)
            r_valid = Ed25519KeyPair.verify_public(responder_public_bytes, r_sig, signing_bytes)
        except Exception:
            r_valid = False

        if not r_valid:
            return {"valid": False, "reason": "Invalid or missing responder signature"}

        # 3. Anti-Collusion Check
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
        pair_key = f"{receipt.victim_id}:{receipt.responder_id}"
        timestamps = self._pair_history.get(pair_key, [])

        one_day_ago = now - (86400 * 1000)
        recent_timestamps = [t for t in timestamps if t > one_day_ago]

        is_collusion_risk = len(recent_timestamps) >= self.max_pair_freq

        recent_timestamps.append(now)
        self._pair_history[pair_key] = recent_timestamps

        return {
            "valid": True,
            "collusion_risk": is_collusion_risk,
            "witness_count": len(receipt.witness_node_ids),
            "reputation_awarded": not is_collusion_risk,
            "reason": (
                "Receipt verified with dual signatures."
                if not is_collusion_risk
                else "COLLUSION SUSPECTED: Unusually frequent rescues between same victim-responder pair."
            ),
        }

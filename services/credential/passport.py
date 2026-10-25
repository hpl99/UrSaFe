"""
W3C-Inspired Verifiable Credential Responder Passport
Allows offline validation of qualifications, certifications, and disaster response roles.
"""
from __future__ import annotations
import time
import uuid
import json
import hashlib
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from packages.crypto.keys import Ed25519KeyPair

class CredentialStatus(str, Enum):
    VERIFIED = "VERIFIED"
    VERIFIED_REVOCATION_STALE = "VERIFIED_REVOCATION_STALE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"

@dataclass
class ResponderPassport:
    credential_id: str
    issuer_id: str
    subject_id: str
    roles: List[str]
    skills: List[str]
    certifications: List[str]
    issued_at: int
    expires_at: int
    signature: str = ""

    def get_canonical_bytes(self) -> bytes:
        roles_str = ",".join(sorted(self.roles))
        skills_str = ",".join(sorted(self.skills))
        certs_str = ",".join(sorted(self.certifications))
        content = (
            f"{self.credential_id}:{self.issuer_id}:{self.subject_id}:"
            f"{roles_str}:{skills_str}:{certs_str}:{self.issued_at}:{self.expires_at}"
        )
        return content.encode("utf-8")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResponderPassport:
        return cls(**data)

class PassportIssuer:
    """Accredited issuing authority (e.g. Civil Defense, Red Cross, Disaster Management)."""
    def __init__(self, issuer_id: str, keypair: Ed25519KeyPair):
        self.issuer_id = issuer_id
        self.keypair = keypair

    def issue_passport(
        self,
        subject_id: str,
        roles: List[str],
        skills: List[str],
        certifications: List[str],
        validity_days: int = 30,
    ) -> ResponderPassport:
        now = int(time.time() * 1000)
        passport = ResponderPassport(
            credential_id=str(uuid.uuid4()),
            issuer_id=self.issuer_id,
            subject_id=subject_id,
            roles=roles,
            skills=skills,
            certifications=certifications,
            issued_at=now,
            expires_at=now + (validity_days * 86400 * 1000),
        )
        sig = self.keypair.sign(passport.get_canonical_bytes())
        passport.signature = sig.hex()
        return passport

class OfflinePassportVerifier:
    """Verifies passports completely offline using cached issuer public keys and local revocation delta list."""
    def __init__(self):
        self._trusted_issuers: Dict[str, bytes] = {} # issuer_id -> public_bytes

    def add_trusted_issuer(self, issuer_id: str, public_bytes: bytes):
        self._trusted_issuers[issuer_id] = public_bytes

    def verify_passport(
        self,
        passport: ResponderPassport,
        revocation_list, # RevocationList instance
        current_time_ms: Optional[int] = None,
        max_revocation_stale_ms: int = 86400 * 1000, # 24 hours
    ) -> Dict[str, Any]:
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)

        # 1. Check Issuer Trust
        issuer_pub = self._trusted_issuers.get(passport.issuer_id)
        if not issuer_pub:
            return {
                "status": CredentialStatus.UNKNOWN.value,
                "reason": f"Issuer '{passport.issuer_id}' is not in trusted authority keystore.",
                "valid": False,
            }

        # 2. Check Cryptographic Signature
        try:
            sig_bytes = bytes.fromhex(passport.signature)
            is_valid_sig = Ed25519KeyPair.verify_public(
                issuer_pub, sig_bytes, passport.get_canonical_bytes()
            )
            if not is_valid_sig:
                return {
                    "status": CredentialStatus.UNKNOWN.value,
                    "reason": "Cryptographic signature verification failed (tampered credential).",
                    "valid": False,
                }
        except Exception as e:
            return {
                "status": CredentialStatus.UNKNOWN.value,
                "reason": f"Malformed signature: {e}",
                "valid": False,
            }

        # 3. Check Expiration
        if now >= passport.expires_at:
            return {
                "status": CredentialStatus.EXPIRED.value,
                "reason": "Credential validity period has expired.",
                "valid": False,
            }

        # 4. Check Revocation Delta
        if revocation_list.is_revoked(passport.credential_id):
            return {
                "status": CredentialStatus.REVOKED.value,
                "reason": "Credential was revoked by issuing authority.",
                "valid": False,
            }

        # 5. Check Revocation Freshness
        is_stale = (now - revocation_list.last_updated_at) > max_revocation_stale_ms
        if is_stale:
            return {
                "status": CredentialStatus.VERIFIED_REVOCATION_STALE.value,
                "reason": "Signature and validity verified, but local revocation list has not synced in >24 hours.",
                "valid": True,
            }

        return {
            "status": CredentialStatus.VERIFIED.value,
            "reason": "Credential mathematically valid, unexpired, and verified against recent revocation list.",
            "valid": True,
        }

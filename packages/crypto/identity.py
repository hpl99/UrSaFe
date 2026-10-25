"""
Identity Layer Segregation
Defines distinct identity domains: Device, User, Responder, and Organization.
A compromise of a user or responder account must not compromise physical device hardware or mesh network keys.
"""
from __future__ import annotations
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .keys import KeyPair, Ed25519KeyPair

@dataclass
class DeviceIdentity:
    """Hardware device identity anchored to physical secure enclave/keystore."""
    device_id: str
    hardware_model: str
    keypair: KeyPair
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

    @property
    def public_signing_hex(self) -> str:
        return self.keypair.signing.public_hex

    @property
    def public_encryption_hex(self) -> str:
        return self.keypair.encryption.public_hex

@dataclass
class UserIdentity:
    """Civilian or general user identity."""
    user_id: str
    display_name: str
    keypair: KeyPair
    device_id: str
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

@dataclass
class ResponderIdentity:
    """Accredited responder identity linked to field qualifications and passports."""
    responder_id: str
    callsign: str
    organization_id: str
    keypair: KeyPair
    device_id: str
    roles: List[str] = field(default_factory=list)
    credential_id: Optional[str] = None
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

@dataclass
class OrganizationIdentity:
    """Civil defense, disaster management authority, or recognized NGO issuing authority."""
    org_id: str
    name: str
    signing_keypair: Ed25519KeyPair
    jurisdiction: str
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))

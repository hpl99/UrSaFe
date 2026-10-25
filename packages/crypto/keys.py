"""
Cryptographic Key Management (Ed25519 & X25519)
"""
from __future__ import annotations
import os
import hashlib
from typing import Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization

@dataclass
class Ed25519KeyPair:
    private_key: ed25519.Ed25519PrivateKey
    public_key: ed25519.Ed25519PublicKey

    @classmethod
    def generate(cls) -> Ed25519KeyPair:
        priv = ed25519.Ed25519PrivateKey.generate()
        return cls(private_key=priv, public_key=priv.public_key())

    @classmethod
    def from_private_bytes(cls, raw_bytes: bytes) -> Ed25519KeyPair:
        priv = ed25519.Ed25519PrivateKey.from_private_bytes(raw_bytes)
        return cls(private_key=priv, public_key=priv.public_key())

    @property
    def public_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    @property
    def public_hex(self) -> str:
        return self.public_bytes.hex()

    @property
    def destination_id(self) -> str:
        """16-byte truncated hexadecimal destination address derived from public key."""
        return hashlib.sha256(self.public_bytes).hexdigest()[:32]

    def sign(self, data: bytes) -> bytes:
        return self.private_key.sign(data)

    def verify(self, signature: bytes, data: bytes) -> bool:
        try:
            self.public_key.verify(signature, data)
            return True
        except Exception:
            return False

    @staticmethod
    def verify_public(public_bytes: bytes, signature: bytes, data: bytes) -> bool:
        try:
            pub = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
            pub.verify(signature, data)
            return True
        except Exception:
            return False

@dataclass
class X25519KeyPair:
    private_key: x25519.X25519PrivateKey
    public_key: x25519.X25519PublicKey

    @classmethod
    def generate(cls) -> X25519KeyPair:
        priv = x25519.X25519PrivateKey.generate()
        return cls(private_key=priv, public_key=priv.public_key())

    @classmethod
    def from_private_bytes(cls, raw_bytes: bytes) -> X25519KeyPair:
        priv = x25519.X25519PrivateKey.from_private_bytes(raw_bytes)
        return cls(private_key=priv, public_key=priv.public_key())

    @property
    def public_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    @property
    def public_hex(self) -> str:
        return self.public_bytes.hex()

    def exchange(self, peer_public_bytes: bytes) -> bytes:
        """Diffie-Hellman key exchange producing a 32-byte shared secret."""
        peer_pub = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        return self.private_key.exchange(peer_pub)

class KeyPair:
    """Composite sovereign identity keypair (Ed25519 signing + X25519 encryption)."""
    def __init__(self, signing_kp: Ed25519KeyPair, enc_kp: X25519KeyPair):
        self.signing = signing_kp
        self.encryption = enc_kp

    @classmethod
    def generate(cls) -> KeyPair:
        return cls(Ed25519KeyPair.generate(), X25519KeyPair.generate())

    @property
    def node_id(self) -> str:
        return self.signing.destination_id

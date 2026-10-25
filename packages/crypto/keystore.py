"""
Crypto Keystore
Manages local hardware/software key storage and signs MessageEnvelopes securely.
"""
from typing import Optional, Dict
from .keys import KeyPair, Ed25519KeyPair
from packages.protocol.envelope import MessageEnvelope

class CryptoKeystore:
    def __init__(self, primary_keypair: Optional[KeyPair] = None):
        self.keypair = primary_keypair or KeyPair.generate()
        self._trusted_issuers: Dict[str, bytes] = {}

    @property
    def node_id(self) -> str:
        return self.keypair.node_id

    @property
    def public_signing_bytes(self) -> bytes:
        return self.keypair.signing.public_bytes

    @property
    def public_signing_hex(self) -> str:
        return self.keypair.signing.public_hex

    def sign_envelope(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Signs the canonical signing bytes of the envelope with this keystore's private key."""
        signing_bytes = envelope.get_signing_bytes()
        sig = self.keypair.signing.sign(signing_bytes)
        envelope.signature = sig.hex()
        envelope.sender_id = self.keypair.signing.destination_id
        return envelope

    def verify_envelope(self, envelope: MessageEnvelope, sender_public_bytes: Optional[bytes] = None) -> bool:
        """Verifies envelope payload hash and Ed25519 signature."""
        if not envelope.signature:
            return False
        # First verify payload integrity against payload_hash
        if envelope.payload_hash != envelope.compute_payload_hash():
            return False
        try:
            sig_bytes = bytes.fromhex(envelope.signature)
            signing_bytes = envelope.get_signing_bytes()
            pub_bytes = sender_public_bytes or self.public_signing_bytes
            return Ed25519KeyPair.verify_public(pub_bytes, sig_bytes, signing_bytes)
        except Exception:
            return False

    def add_trusted_issuer(self, org_id: str, public_key_bytes: bytes):
        self._trusted_issuers[org_id] = public_key_bytes

    def get_trusted_issuer(self, org_id: str) -> Optional[bytes]:
        return self._trusted_issuers.get(org_id)

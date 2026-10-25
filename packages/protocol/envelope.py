"""
UrSafe Message Envelope
Durable binary-compatible envelope for offline emergency communication.
"""
from __future__ import annotations
import json
import time
import uuid
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from .types import Priority, MessageType, DeliveryState

@dataclass
class Location:
    latitude: float
    longitude: float
    altitude: float = 0.0
    accuracy_meters: float = 10.0
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Location:
        return cls(**data)

@dataclass
class EncryptionMetadata:
    cipher: str = "PLAINTEXT"         # "ChaCha20-Poly1305", "AES-256-GCM", or "PLAINTEXT"
    nonce: str = ""                   # Hex-encoded nonce
    recipient_key_id: str = "BROADCAST"
    disclosure_level: int = 1         # Level 0 to Level 4

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EncryptionMetadata:
        return cls(**data)

@dataclass
class MessageEnvelope:
    message_id: str
    sender_id: str
    recipient_id: str
    created_at: int
    expires_at: int
    priority: Priority
    message_type: MessageType
    sequence: int
    hop_limit: int
    origin: str
    current_hop: str
    payload: Dict[str, Any]
    payload_hash: str = ""
    signature: str = ""               # Hex-encoded signature
    encryption: EncryptionMetadata = field(default_factory=EncryptionMetadata)
    delivery_state: DeliveryState = DeliveryState.QUEUED_LOCAL

    def __post_init__(self):
        if not self.payload_hash:
            self.payload_hash = self.compute_payload_hash()

    def compute_payload_hash(self) -> str:
        """Computes deterministic SHA-256 hash of the payload dictionary."""
        payload_bytes = json.dumps(self.payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload_bytes).hexdigest()

    def get_signing_bytes(self) -> bytes:
        """Returns the canonical byte sequence over which the sender signature is computed."""
        signing_content = (
            f"{self.message_id}:{self.sender_id}:{self.recipient_id}:"
            f"{self.created_at}:{self.expires_at}:{int(self.priority)}:"
            f"{self.message_type.value}:{self.sequence}:{self.origin}:{self.payload_hash}"
        )
        return signing_content.encode("utf-8")

    def is_expired(self, current_time_ms: Optional[int] = None) -> bool:
        """Checks if the message has passed its Time-To-Live."""
        now = current_time_ms if current_time_ms is not None else int(time.time() * 1000)
        return now >= self.expires_at

    def decrement_hop(self, next_hop_id: str) -> bool:
        """Decrements hop limit. Returns True if envelope can still be forwarded."""
        if self.hop_limit <= 1:
            self.hop_limit = 0
            return False
        self.hop_limit -= 1
        self.current_hop = next_hop_id
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "priority": int(self.priority),
            "message_type": self.message_type.value,
            "sequence": self.sequence,
            "hop_limit": self.hop_limit,
            "origin": self.origin,
            "current_hop": self.current_hop,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "signature": self.signature,
            "encryption": self.encryption.to_dict(),
            "delivery_state": self.delivery_state.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MessageEnvelope:
        return cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            priority=Priority(data["priority"]),
            message_type=MessageType(data["message_type"]),
            sequence=data["sequence"],
            hop_limit=data["hop_limit"],
            origin=data["origin"],
            current_hop=data["current_hop"],
            payload=data["payload"],
            payload_hash=data.get("payload_hash", ""),
            signature=data.get("signature", ""),
            encryption=EncryptionMetadata.from_dict(data.get("encryption", {})),
            delivery_state=DeliveryState(data.get("delivery_state", DeliveryState.QUEUED_LOCAL.value)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> MessageEnvelope:
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def create_sos(
        cls,
        sender_id: str,
        category: str,
        urgency: str,
        people_affected: int,
        location: Location,
        text: str = "",
        ttl_seconds: int = 86400,
        sequence: int = 1,
    ) -> MessageEnvelope:
        """Factory method to construct a canonical SOS_CREATED envelope."""
        now = int(time.time() * 1000)
        msg_id = str(uuid.uuid4())
        payload = {
            "emergency_id": msg_id,
            "category": category,
            "urgency": urgency,
            "people_affected": people_affected,
            "location": location.to_dict(),
            "text": text,
            "timestamp": now,
        }
        return cls(
            message_id=msg_id,
            sender_id=sender_id,
            recipient_id="BROADCAST",
            created_at=now,
            expires_at=now + (ttl_seconds * 1000),
            priority=Priority.EMERGENCY,
            message_type=MessageType.SOS_CREATED,
            sequence=sequence,
            hop_limit=7,
            origin=sender_id,
            current_hop=sender_id,
            payload=payload,
        )

"""
Delay-Tolerant Networking (DTN) Data Mule Synchronization Protocol
Enables physical couriers (responders, vehicles, drones) to bridge isolated network partitions.
"""
from __future__ import annotations
import time
import uuid
import hashlib
from typing import List, Set, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from packages.protocol.envelope import MessageEnvelope

@dataclass
class InventoryVector:
    node_id: str
    message_ids: List[str]
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InventoryVector:
        return cls(**data)

@dataclass
class DTNBundle:
    bundle_id: str
    custodian_id: str
    envelopes: List[MessageEnvelope]
    created_at: int
    expires_at: int
    bundle_hash: str = ""
    signature: str = ""

    def __post_init__(self):
        if not self.bundle_hash:
            self.bundle_hash = self.compute_hash()

    def compute_hash(self) -> str:
        ids_concat = ":".join(sorted(e.message_id for e in self.envelopes))
        content = f"{self.bundle_id}:{self.custodian_id}:{ids_concat}:{self.created_at}:{self.expires_at}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "custodian_id": self.custodian_id,
            "envelopes": [e.to_dict() for e in self.envelopes],
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "bundle_hash": self.bundle_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DTNBundle:
        return cls(
            bundle_id=data["bundle_id"],
            custodian_id=data["custodian_id"],
            envelopes=[MessageEnvelope.from_dict(d) for d in data["envelopes"]],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            bundle_hash=data.get("bundle_hash", ""),
            signature=data.get("signature", ""),
        )

class DataMuleSync:
    """Manages bundle creation, inventory comparison, and custody transfer between nodes."""
    @staticmethod
    def calculate_missing_ids(local_known_ids: Set[str], remote_inventory: InventoryVector) -> List[str]:
        """Identifies messages known by the local node that the remote peer does NOT yet have."""
        remote_set = set(remote_inventory.message_ids)
        return list(local_known_ids - remote_set)

    @staticmethod
    def package_bundle(
        custodian_id: str,
        envelopes: List[MessageEnvelope],
        ttl_seconds: int = 86400,
    ) -> DTNBundle:
        now = int(time.time() * 1000)
        return DTNBundle(
            bundle_id=str(uuid.uuid4()),
            custodian_id=custodian_id,
            envelopes=envelopes,
            created_at=now,
            expires_at=now + (ttl_seconds * 1000),
        )

    @staticmethod
    def ingest_bundle(
        bundle: DTNBundle,
        inbox_verifier, # function or Inbox instance that accepts envelope
    ) -> Dict[str, Any]:
        """Ingests a received bundle, verifies each envelope, and tracks acceptances."""
        accepted: List[str] = []
        duplicates: List[str] = []
        rejected: List[str] = []

        now = int(time.time() * 1000)
        if now >= bundle.expires_at:
            return {"status": "EXPIRED", "accepted": [], "rejected": [e.message_id for e in bundle.envelopes]}

        for env in bundle.envelopes:
            if env.is_expired(now):
                rejected.append(env.message_id)
                continue
            is_new = inbox_verifier(env)
            if is_new:
                accepted.append(env.message_id)
            else:
                duplicates.append(env.message_id)

        return {
            "bundle_id": bundle.bundle_id,
            "accepted_count": len(accepted),
            "duplicate_count": len(duplicates),
            "rejected_count": len(rejected),
            "accepted_ids": accepted,
        }

"""
Revocation Delta List
Caches revoked credential IDs and tracks synchronization age.
"""
import time
from typing import Set, Dict, Any, Optional

class RevocationList:
    def __init__(self, last_updated_at: Optional[int] = None):
        self.last_updated_at = last_updated_at if last_updated_at is not None else int(time.time() * 1000)
        self._revoked_ids: Set[str] = set()

    def revoke(self, credential_id: str, timestamp: Optional[int] = None):
        self._revoked_ids.add(credential_id)
        if timestamp:
            self.last_updated_at = max(self.last_updated_at, timestamp)

    def is_revoked(self, credential_id: str) -> bool:
        return credential_id in self._revoked_ids

    def update_delta(self, revoked_ids: Set[str], update_timestamp: int):
        self._revoked_ids.update(revoked_ids)
        self.last_updated_at = update_timestamp

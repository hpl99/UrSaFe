"""
Audit Verifier
Validates hash chain continuity, event hashes, and tamper detection.
"""
from typing import List, Tuple
from .flight_recorder import AuditEvent, GENESIS_PREVIOUS_HASH

class AuditVerifier:
    @staticmethod
    def verify_chain(events: List[AuditEvent]) -> Tuple[bool, str]:
        """
        Verifies that:
          1. The first event links to GENESIS_PREVIOUS_HASH.
          2. Each event's event_hash matches recomputed hash.
          3. Each event links to the exact previous_hash of its predecessor.
        Returns (is_valid, error_reason).
        """
        if not events:
            return True, "Empty chain is valid"

        expected_prev = GENESIS_PREVIOUS_HASH

        for idx, event in enumerate(events):
            # Check link to predecessor
            if event.previous_hash != expected_prev:
                return (
                    False,
                    f"Broken chain link at index {idx} (event {event.event_id}): "
                    f"expected prev {expected_prev}, got {event.previous_hash}"
                )

            # Check self-consistency of event hash
            recomputed = event.compute_hash()
            if event.event_hash != recomputed:
                return (
                    False,
                    f"Tampered event at index {idx} (event {event.event_id}): "
                    f"recorded hash {event.event_hash} != recomputed {recomputed}"
                )

            expected_prev = event.event_hash

        return True, "Chain intact and cryptographically verified"

"""
Anti-Replay Protection Filter
Maintains sliding-window sequence tracking to protect against packet replay attacks.
"""
from typing import Dict, Set

class ReplayFilter:
    """
    Sliding window replay filter per sender node.
    Accepts packets if:
      1. Sequence number > highest seen (window advances)
      2. Sequence number is within window (window_size) and hasn't been seen yet.
    Rejects packets if:
      1. Sequence number has already been processed (replay).
      2. Sequence number is older than (highest_seen - window_size).
    """
    def __init__(self, window_size: int = 128):
        self.window_size = window_size
        self._highest_seq: Dict[str, int] = {}
        self._seen_seqs: Dict[str, Set[int]] = {}

    def is_valid_and_update(self, sender_id: str, sequence: int) -> bool:
        if sequence <= 0:
            return False

        if sender_id not in self._highest_seq:
            self._highest_seq[sender_id] = sequence
            self._seen_seqs[sender_id] = {sequence}
            return True

        highest = self._highest_seq[sender_id]
        seen = self._seen_seqs[sender_id]

        if sequence > highest:
            self._highest_seq[sender_id] = sequence
            seen.add(sequence)
            # Prune sequence numbers outside the sliding window
            cutoff = sequence - self.window_size
            self._seen_seqs[sender_id] = {s for s in seen if s > cutoff}
            return True

        # Sequence is within or below window
        if sequence <= (highest - self.window_size):
            # Packet is too old; rejected
            return False

        if sequence in seen:
            # Replay detected; rejected
            return False

        # Valid out-of-order packet within window
        seen.add(sequence)
        return True

    def reset_sender(self, sender_id: str):
        self._highest_seq.pop(sender_id, None)
        self._seen_seqs.pop(sender_id, None)

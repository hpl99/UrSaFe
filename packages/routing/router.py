"""
Mesh Router
Implements managed flooding, loop elimination, hop-limit bounding, and deduplication.
"""
from typing import Dict, Any, Optional, Set, List
from packages.protocol.envelope import MessageEnvelope
from hardware.transport_interface import Transport
from .metrics import LinkMetrics, RouteScorer, RouteScore

class MeshRouter:
    def __init__(self, node_id: str, transport: Transport):
        self.node_id = node_id
        self.transport = transport
        self.seen_messages: Set[str] = set()
        self.neighbor_metrics: Dict[str, LinkMetrics] = {}

    def update_neighbor_metric(self, neighbor_id: str, metrics: LinkMetrics):
        self.neighbor_metrics[neighbor_id] = metrics

    def handle_incoming_envelope(self, envelope: MessageEnvelope) -> Dict[str, Any]:
        """
        Processes incoming packet:
          1. Checks deduplication: if already seen, DROP.
          2. Records message_id in seen set.
          3. Checks recipient: if addressed to self or BROADCAST, delivers locally.
          4. If hop_limit allows and not origin, rebroadcasts to mesh.
        """
        # Deduplication check
        if envelope.message_id in self.seen_messages:
            return {"action": "DROP_DUPLICATE", "message_id": envelope.message_id}

        self.seen_messages.add(envelope.message_id)

        # Check TTL
        if envelope.is_expired():
            return {"action": "DROP_EXPIRED", "message_id": envelope.message_id}

        is_for_me = envelope.recipient_id in (self.node_id, "BROADCAST")
        is_originator = envelope.origin == self.node_id

        forwarded = False
        if not is_originator and envelope.hop_limit > 1:
            # Decrement hop and forward
            envelope_copy = MessageEnvelope.from_json(envelope.to_json())
            can_forward = envelope_copy.decrement_hop(self.node_id)
            if can_forward:
                self.transport.send(envelope_copy)
                forwarded = True

        return {
            "action": "DELIVERED_LOCAL" if is_for_me else "ROUTED_ONLY",
            "message_id": envelope.message_id,
            "forwarded": forwarded,
            "remaining_hops": envelope.hop_limit,
        }

    def score_forwarding_candidate(self, neighbor_id: str, envelope: MessageEnvelope) -> Optional[RouteScore]:
        metrics = self.neighbor_metrics.get(neighbor_id)
        if not metrics:
            return None
        return RouteScorer.score_route(
            metrics=metrics,
            hop_count=7 - envelope.hop_limit,
            priority=envelope.priority,
        )

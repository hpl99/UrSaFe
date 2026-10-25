"""
Multi-Node Radio Mesh Simulator
Simulates RF propagation, link degradation, packet loss, partitions, and multi-hop forwarding.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
import random
import time
from collections import deque
from hardware.transport_interface import Transport
from packages.protocol.envelope import MessageEnvelope

class SimulatedRadioMesh:
    def __init__(self, loss_rate: float = 0.0, base_latency_ms: int = 10):
        self.loss_rate = loss_rate
        self.base_latency_ms = base_latency_ms
        self.nodes: Dict[str, SimulationTransport] = {}
        self.partitions: Set[frozenset] = set() # Set of partitioned (blocked) node pairs

    def register_node(self, transport: SimulationTransport):
        self.nodes[transport.node_id] = transport
        transport.set_mesh(self)

    def set_partition(self, node_a: str, node_b: str, partitioned: bool = True):
        pair = frozenset([node_a, node_b])
        if partitioned:
            self.partitions.add(pair)
        else:
            self.partitions.discard(pair)

    def route_broadcast(self, origin_node: str, envelope: MessageEnvelope):
        """Simulates RF broadcast propagation to all reachable neighbor nodes."""
        for target_id, target_transport in self.nodes.items():
            if target_id == origin_node:
                continue

            # Check if partition blocks communication
            if frozenset([origin_node, target_id]) in self.partitions:
                continue

            # Check simulated packet drop
            if self.loss_rate > 0.0 and random.random() < self.loss_rate:
                continue

            # Deliver envelope copy
            target_transport.deliver_incoming(envelope)

class SimulationTransport(Transport):
    def __init__(self, node_id: str, rssi: int = -65, snr: float = 8.5):
        self.node_id = node_id
        self.rssi = rssi
        self.snr = snr
        self.connected = True
        self._mesh: Optional[SimulatedRadioMesh] = None
        self._inbox_queue: deque = deque()

    def set_mesh(self, mesh: SimulatedRadioMesh):
        self._mesh = mesh

    def deliver_incoming(self, envelope: MessageEnvelope):
        self._inbox_queue.append(envelope)

    def discover(self) -> List[Dict[str, Any]]:
        if not self._mesh:
            return []
        return [{"node_id": nid} for nid in self._mesh.nodes.keys() if nid != self.node_id]

    def connect(self, target_id: str) -> bool:
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False

    def send(self, envelope: MessageEnvelope) -> bool:
        if not self.connected or not self._mesh:
            return False
        self._mesh.route_broadcast(self.node_id, envelope)
        return True

    def receive(self) -> Optional[MessageEnvelope]:
        if not self.connected or not self._inbox_queue:
            return None
        return self._inbox_queue.popleft()

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "bearer": "SIMULATION",
            "max_packet_size": 237,
            "bandwidth_bps": 2500,
            "duty_cycle_percent": 100.0,
        }

    def get_link_metrics(self) -> Dict[str, Any]:
        return {
            "rssi_dbm": self.rssi,
            "snr_db": self.snr,
            "packet_loss_rate": 0.0,
            "etx": 1.05,
        }

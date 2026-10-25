"""
UrSafe End-to-End Physical & Simulation Acceptance Test Suite (Mandate Section 63)
Tests the complete offline emergency lifecycle:
  A. Device 1 offline
  B. Device 2 offline
  C. Radio A paired with Device 1
  D. Radio B paired with Device 2
  E. Zero Internet
  F. Device 1 creates SOS
  G. Radio A transmits
  H. Radio B receives
  I. Device 2 receives notification
  J. Responder accepts
  K. Responder sends ACK
  L. Device 1 receives ACK
  M. Disconnect central server -> Repeat
  N. Create partition (Island A and Island B)
  O. Generate messages on both sides
  P. Move Data Mule between partitions
  Q. Reconnect and synchronize
  R. Verify full state convergence
"""
import time
import pytest
from hardware.simulator.mesh_sim import SimulatedRadioMesh, SimulationTransport
from packages.crypto.keystore import CryptoKeystore
from packages.sync.engine import SyncEngine
from packages.routing.router import MeshRouter
from packages.protocol.envelope import MessageEnvelope, Location
from packages.protocol.types import Priority, MessageType
from packages.crdt.crdt_state import IncidentCRDTState

class SimulatedFieldNode:
    """Represents a physical field device (e.g. Android phone + paired Meshtastic radio)."""
    def __init__(self, node_id: str, mesh: SimulatedRadioMesh):
        self.node_id = node_id
        self.keystore = CryptoKeystore()
        self.transport = SimulationTransport(node_id)
        mesh.register_node(self.transport)
        self.sync_engine = SyncEngine(node_id)
        self.router = MeshRouter(self.keystore.node_id, self.transport)
        self.notifications: list = []
        self.incident_crdts: dict = {}

    def poll_radio(self):
        """Polls incoming radio packets, feeds router, and handles deliveries."""
        while True:
            env = self.transport.receive()
            if not env:
                break
            res = self.router.handle_incoming_envelope(env)
            if res["action"] in ("DELIVERED_LOCAL", "ROUTED_ONLY"):
                is_new = self.sync_engine.receive_incoming(env)
                if is_new and res["action"] == "DELIVERED_LOCAL":
                    self.on_local_delivery(env)

    def on_local_delivery(self, env: MessageEnvelope):
        # Trigger native notification
        self.notifications.append(env)

        # Update local CRDT state
        inc_id = env.payload.get("emergency_id", env.message_id)
        if inc_id not in self.incident_crdts:
            self.incident_crdts[inc_id] = IncidentCRDTState(inc_id, env.origin)

        crdt = self.incident_crdts[inc_id]
        if env.message_type == MessageType.SOS_CREATED:
            crdt.update_status("REPORTED", env.created_at, env.sender_id)
        elif env.message_type == MessageType.SOS_ACCEPTED:
            resp_id = env.payload.get("responder_id", env.sender_id)
            crdt.update_status("ACCEPTED", env.created_at, env.sender_id)
            crdt.assign_responder(resp_id, env.created_at, env.sender_id)

    def create_and_broadcast_sos(self, category: str, urgency: str, people: int, location: Location) -> MessageEnvelope:
        env = MessageEnvelope.create_sos(self.node_id, category, urgency, people, location)
        self.keystore.sign_envelope(env)
        self.sync_engine.queue_message(env)
        self.transport.send(env)
        return env

    def accept_emergency(self, emergency_env: MessageEnvelope) -> MessageEnvelope:
        now = int(time.time() * 1000)
        ack_payload = {
            "emergency_id": emergency_env.message_id,
            "responder_id": self.node_id,
            "action": "ACCEPT",
            "timestamp": now,
        }
        ack_env = MessageEnvelope(
            message_id=f"ack_{emergency_env.message_id}",
            sender_id=self.node_id,
            recipient_id=emergency_env.sender_id, # Target original victim or broadcast
            created_at=now,
            expires_at=now + 86400000,
            priority=Priority.EMERGENCY,
            message_type=MessageType.SOS_ACCEPTED,
            sequence=1,
            hop_limit=7,
            origin=self.node_id,
            current_hop=self.node_id,
            payload=ack_payload,
        )
        self.keystore.sign_envelope(ack_env)
        self.on_local_delivery(ack_env)
        self.sync_engine.queue_message(ack_env)
        self.transport.send(ack_env)
        return ack_env

def test_complete_section_63_acceptance_flow():
    # A, B, C, D, E: Disconnected from central server, Zero Internet, LoRa mesh
    mesh = SimulatedRadioMesh()

    # Device 1 + Radio A (Victim Phone)
    victim_node = SimulatedFieldNode("victim_phone_alpha", mesh)

    # Device 2 + Radio B (Responder Phone)
    responder_node = SimulatedFieldNode("responder_phone_bravo", mesh)

    # F, G: Victim creates SOS offline and Radio A transmits
    loc = Location(latitude=18.5204, longitude=73.8567)
    sos_env = victim_node.create_and_broadcast_sos("FLOOD", "CRITICAL", 3, loc)
    assert sos_env.message_id != ""

    # H, I: Radio B receives and Responder Phone triggers local notification
    responder_node.poll_radio()
    assert len(responder_node.notifications) == 1
    received_sos = responder_node.notifications[0]
    assert received_sos.message_id == sos_env.message_id
    assert received_sos.payload["people_affected"] == 3

    # J, K: Responder accepts and transmits ACK over mesh
    ack_env = responder_node.accept_emergency(received_sos)
    assert ack_env.message_type == MessageType.SOS_ACCEPTED

    # L: Victim phone receives ACK via mesh
    victim_node.poll_radio()
    victim_acks = [n for n in victim_node.notifications if n.message_type == MessageType.SOS_ACCEPTED]
    assert len(victim_acks) == 1
    assert victim_acks[0].payload["emergency_id"] == sos_env.message_id

    # N: Create Network Partition (Island A and Island B)
    mesh.set_partition("victim_phone_alpha", "responder_phone_bravo", partitioned=True)

    # O: Generate concurrent messages on both sides
    sos_2 = victim_node.create_and_broadcast_sos("MEDICAL", "HIGH", 1, loc)
    # Responder on Island B cannot hear sos_2 due to mountain ridge partition
    responder_node.poll_radio()
    assert not any(n.message_id == sos_2.message_id for n in responder_node.notifications)

    # P: Move Data Mule (Radio C / Vehicle) between partitions
    mule = SimulatedFieldNode("vehicle_mule_charlie", mesh)

    # Mule visits Island A
    inv_mule = mule.sync_engine.generate_inventory_vector()
    bundle_a = victim_node.sync_engine.prepare_sync_bundle_for_peer(inv_mule)
    mule.sync_engine.ingest_peer_bundle(bundle_a)
    for e in bundle_a.envelopes:
        mule.sync_engine.outbox.enqueue(e)

    # Mule travels to Island B
    inv_b = responder_node.sync_engine.generate_inventory_vector()
    bundle_for_b = mule.sync_engine.prepare_sync_bundle_for_peer(inv_b)
    responder_node.sync_engine.ingest_peer_bundle(bundle_for_b)

    # Island B now has sos_2 delivered via the physical Data Mule!
    assert responder_node.sync_engine.inbox.has_seen(sos_2.message_id) is True

    # Q, R: Reconnect mesh & verify state convergence
    mesh.set_partition("victim_phone_alpha", "responder_phone_bravo", partitioned=False)

    # Verify CRDT state convergence
    crdt_v = victim_node.incident_crdts[sos_env.message_id]
    crdt_r = responder_node.incident_crdts[sos_env.message_id]
    merged_v = crdt_v.merge(crdt_r)
    merged_r = crdt_r.merge(crdt_v)

    assert merged_v.to_snapshot() == merged_r.to_snapshot()
    assert merged_v.status.value == "ACCEPTED"
    assert merged_v.assigned_responder.value == "responder_phone_bravo"

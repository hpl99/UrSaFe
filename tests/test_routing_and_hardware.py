"""
Unit Tests for Hardware Adapters and Mesh Routing
"""
import pytest
from hardware.simulator.mesh_sim import SimulatedRadioMesh, SimulationTransport
from hardware.meshtastic.adapter import MeshtasticTransport
from hardware.ble.adapter import BleTransport
from packages.routing.metrics import LinkMetrics, RouteScorer
from packages.routing.router import MeshRouter
from packages.protocol.envelope import MessageEnvelope, Location
from packages.protocol.types import Priority

def test_meshtastic_adapter_capabilities_and_packing():
    transport = MeshtasticTransport(port_or_mac="BLE:TEST", region="IN865")
    assert transport.connect("MESHTASTIC_01") is True
    assert transport.get_capabilities()["max_packet_size"] == 237

    loc = Location(latitude=13.0827, longitude=80.2707)
    env = MessageEnvelope.create_sos("victim_01", "FIRE", "CRITICAL", 2, loc)

    assert transport.send(env) is True
    assert len(transport.outbox_buffer) == 1
    assert transport.outbox_buffer[0].startswith(b"MESH:1:")

def test_simulated_mesh_multi_node_broadcast():
    mesh = SimulatedRadioMesh()
    node_a = SimulationTransport("node_a")
    node_b = SimulationTransport("node_b")
    node_c = SimulationTransport("node_c")

    mesh.register_node(node_a)
    mesh.register_node(node_b)
    mesh.register_node(node_c)

    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FLOOD", "CRITICAL", 1, loc)

    # Node A transmits broadcast
    node_a.send(env)

    # Node B and Node C both receive it
    rec_b = node_b.receive()
    rec_c = node_c.receive()

    assert rec_b is not None
    assert rec_b.message_id == env.message_id
    assert rec_c is not None
    assert rec_c.message_id == env.message_id

def test_simulated_mesh_partition_isolation():
    mesh = SimulatedRadioMesh()
    node_a = SimulationTransport("node_a")
    node_b = SimulationTransport("node_b")

    mesh.register_node(node_a)
    mesh.register_node(node_b)

    # Cut off link between A and B (partition)
    mesh.set_partition("node_a", "node_b", partitioned=True)

    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FLOOD", "CRITICAL", 1, loc)
    node_a.send(env)

    # Node B should receive NOTHING due to active partition
    assert node_b.receive() is None

    # Heal partition
    mesh.set_partition("node_a", "node_b", partitioned=False)
    node_a.send(env)

    # Now Node B receives it
    assert node_b.receive() is not None

def test_router_deduplication_and_forwarding():
    sim = SimulationTransport("router_01")
    router = MeshRouter(node_id="router_01", transport=sim)

    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("origin_node", "MEDICAL", "HIGH", 1, loc)

    # First arrival: processed and forwarded
    res1 = router.handle_incoming_envelope(env)
    assert res1["action"] == "DELIVERED_LOCAL"

    # Second arrival of identical message_id: dropped as duplicate
    res2 = router.handle_incoming_envelope(env)
    assert res2["action"] == "DROP_DUPLICATE"

def test_explainable_route_scoring():
    good_link = LinkMetrics(
        neighbor_id="tower_alpha",
        rssi_dbm=-60,
        snr_db=10.0,
        packet_loss_rate=0.02,
        battery_level=0.90,
        queue_pressure=0.10,
    )

    bad_link = LinkMetrics(
        neighbor_id="handheld_beta",
        rssi_dbm=-115,
        snr_db=-8.0,
        packet_loss_rate=0.50,
        battery_level=0.08,
        queue_pressure=0.85,
    )

    score_good = RouteScorer.score_route(good_link, hop_count=1, priority=Priority.EMERGENCY)
    score_bad = RouteScorer.score_route(bad_link, hop_count=3, priority=Priority.ROUTINE)

    assert score_good.is_viable is True
    assert score_good.score > score_bad.score
    assert "Route Score" in score_good.explanation
    assert "ETX: 1.0" in score_good.explanation

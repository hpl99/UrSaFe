"""
Unit Tests for Data Mule Inter-Island Partition Synchronization
"""
import pytest
from packages.sync.engine import SyncEngine
from packages.protocol.envelope import MessageEnvelope, Location
from packages.protocol.types import Priority

def test_data_mule_inter_island_sync():
    # Island Alpha (disconnected from Island Beta)
    node_alpha = SyncEngine(node_id="station_alpha")

    # Island Beta (disconnected from Island Alpha)
    node_beta = SyncEngine(node_id="station_beta")

    # Data Mule (e.g. mobile rescue vehicle moving between valleys)
    mule = SyncEngine(node_id="vehicle_mule_01")

    # 1. On Island Alpha: Victim creates an offline SOS
    loc = Location(latitude=15.123, longitude=75.456)
    sos_alpha = MessageEnvelope.create_sos("victim_alpha_01", "FLOOD", "CRITICAL", 3, loc)
    node_alpha.queue_message(sos_alpha)

    # 2. Mule arrives at Island Alpha: exchanges inventory vectors
    inv_mule_at_alpha = mule.generate_inventory_vector()
    bundle_alpha_to_mule = node_alpha.prepare_sync_bundle_for_peer(inv_mule_at_alpha)

    # Mule ingests Island Alpha's pending bundle
    ingest_res = mule.ingest_peer_bundle(bundle_alpha_to_mule)
    assert ingest_res["accepted_count"] == 1
    assert sos_alpha.message_id in ingest_res["accepted_ids"]
    assert mule.inbox.has_seen(sos_alpha.message_id) is True

    # Also put in mule's outbox for onward propagation
    for env in bundle_alpha_to_mule.envelopes:
        mule.outbox.enqueue(env)

    # 3. Mule physically travels across mountain pass to Island Beta
    # Island Beta has zero knowledge of sos_alpha yet
    assert node_beta.inbox.has_seen(sos_alpha.message_id) is False

    # 4. Mule arrives at Island Beta: exchanges inventory vectors
    inv_beta = node_beta.generate_inventory_vector()
    bundle_mule_to_beta = mule.prepare_sync_bundle_for_peer(inv_beta)

    # Island Beta ingests the bundle carried by the mule
    beta_ingest = node_beta.ingest_peer_bundle(bundle_mule_to_beta)
    assert beta_ingest["accepted_count"] == 1
    assert sos_alpha.message_id in beta_ingest["accepted_ids"]

    # Island Beta now has the SOS!
    assert node_beta.inbox.has_seen(sos_alpha.message_id) is True

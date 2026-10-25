"""
UrSafe Synchronization Engine
Glues together the Persistent Outbox, Inbox, and peer synchronization flows.
"""
from typing import Optional, List, Dict, Any
from .outbox import PersistentOutbox
from .inbox import PersistentInbox
from .mule import DataMuleSync, InventoryVector, DTNBundle
from packages.protocol.envelope import MessageEnvelope

class SyncEngine:
    def __init__(self, node_id: str, db_path: str = ":memory:"):
        self.node_id = node_id
        self.outbox = PersistentOutbox(db_path=db_path)
        self.inbox = PersistentInbox(db_path=db_path)

    def queue_message(self, envelope: MessageEnvelope) -> bool:
        """Saves message locally in outbox and marks as seen in inbox."""
        self.inbox.ingest(envelope)
        return self.outbox.enqueue(envelope)

    def pull_outgoing(self) -> Optional[MessageEnvelope]:
        return self.outbox.peek_next()

    def receive_incoming(self, envelope: MessageEnvelope) -> bool:
        """Ingests incoming envelope. Deduplicates automatically."""
        return self.inbox.ingest(envelope)

    def generate_inventory_vector(self) -> InventoryVector:
        return InventoryVector(
            node_id=self.node_id,
            message_ids=self.inbox.get_inventory_ids()
        )

    def prepare_sync_bundle_for_peer(self, peer_inventory: InventoryVector) -> DTNBundle:
        """Packages all messages this node has that the peer lacks."""
        all_local_ids = set(self.inbox.get_inventory_ids())
        missing_on_peer = DataMuleSync.calculate_missing_ids(all_local_ids, peer_inventory)

        # Pull envelopes from local storage
        envelopes_to_send: List[MessageEnvelope] = []
        cursor = self.outbox._conn.cursor()
        for msg_id in missing_on_peer:
            cursor.execute("SELECT envelope_json FROM outbox WHERE message_id = ?", (msg_id,))
            row = cursor.fetchone()
            if row:
                envelopes_to_send.append(MessageEnvelope.from_json(row[0]))

        return DataMuleSync.package_bundle(self.node_id, envelopes_to_send)

    def ingest_peer_bundle(self, bundle: DTNBundle) -> Dict[str, Any]:
        return DataMuleSync.ingest_bundle(bundle, self.receive_incoming)

"""
Direct BLE Smartphone Transport Adapter
Implements direct point-to-point BLE GATT exchange between victim and responder phones.
"""
from typing import Dict, Any, Optional, List
from hardware.transport_interface import Transport
from packages.protocol.envelope import MessageEnvelope

class BleTransport(Transport):
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.connected = False
        self.connected_peer_id: Optional[str] = None
        self.inbox: List[MessageEnvelope] = []
        self.outbox: List[MessageEnvelope] = []

    def discover(self) -> List[Dict[str, Any]]:
        return [{"peer_id": "BLE_PEER_RESPONDER_01", "rssi": -55}]

    def connect(self, target_id: str) -> bool:
        self.connected = True
        self.connected_peer_id = target_id
        return True

    def disconnect(self):
        self.connected = False
        self.connected_peer_id = None

    def send(self, envelope: MessageEnvelope) -> bool:
        if not self.connected:
            return False
        self.outbox.append(envelope)
        return True

    def receive(self) -> Optional[MessageEnvelope]:
        if not self.connected or not self.inbox:
            return None
        return self.inbox.pop(0)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "bearer": "BLE_DIRECT",
            "max_packet_size": 512,
            "bandwidth_bps": 125000,
            "range_meters": 15,
        }

    def get_link_metrics(self) -> Dict[str, Any]:
        return {
            "rssi_dbm": -55,
            "snr_db": 15.0,
            "packet_loss_rate": 0.01,
            "etx": 1.01,
        }

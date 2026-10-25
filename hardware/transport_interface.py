"""
Abstract Hardware Transport Interface
Enables upper layers to operate agnostically over LoRa, BLE, USB, or Simulated bearers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from packages.protocol.envelope import MessageEnvelope

class Transport(ABC):
    @abstractmethod
    def discover(self) -> List[Dict[str, Any]]:
        """Scans and discovers available peers, radios, or peripherals."""
        pass

    @abstractmethod
    def connect(self, target_id: str) -> bool:
        """Establishes link with radio or peer."""
        pass

    @abstractmethod
    def disconnect(self):
        """Tears down active link."""
        pass

    @abstractmethod
    def send(self, envelope: MessageEnvelope) -> bool:
        """Transmits an envelope across the bearer."""
        pass

    @abstractmethod
    def receive(self) -> Optional[MessageEnvelope]:
        """Polls for next received envelope from bearer."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Returns bearer constraints (max_packet_size, mtu, bandwidth_bps, duty_cycle)."""
        pass

    @abstractmethod
    def get_link_metrics(self) -> Dict[str, Any]:
        """Returns physical link metrics (rssi_dbm, snr_db, packet_loss_rate, etx)."""
        pass

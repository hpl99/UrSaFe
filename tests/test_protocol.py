"""
Unit Tests for UrSafe Protocol Envelope and Types
"""
import time
import pytest
from packages.protocol.types import Priority, MessageType, DeliveryState
from packages.protocol.envelope import MessageEnvelope, Location, EncryptionMetadata

def test_sos_envelope_creation():
    loc = Location(latitude=18.5204, longitude=73.8567, altitude=560.0, accuracy_meters=5.0)
    envelope = MessageEnvelope.create_sos(
        sender_id="node_victim_01",
        category="FLOOD",
        urgency="CRITICAL",
        people_affected=4,
        location=loc,
        text="Water level rising above 2 meters",
        ttl_seconds=3600,
        sequence=1,
    )

    assert envelope.priority == Priority.EMERGENCY
    assert envelope.message_type == MessageType.SOS_CREATED
    assert envelope.recipient_id == "BROADCAST"
    assert envelope.payload["people_affected"] == 4
    assert envelope.payload_hash != ""
    assert envelope.hop_limit == 7
    assert not envelope.is_expired()

def test_envelope_serialization_roundtrip():
    loc = Location(latitude=19.0760, longitude=72.8777)
    original = MessageEnvelope.create_sos(
        sender_id="node_alpha",
        category="MEDICAL",
        urgency="HIGH",
        people_affected=1,
        location=loc,
    )
    json_str = original.to_json()
    reconstructed = MessageEnvelope.from_json(json_str)

    assert reconstructed.message_id == original.message_id
    assert reconstructed.sender_id == original.sender_id
    assert reconstructed.priority == original.priority
    assert reconstructed.payload_hash == original.payload_hash
    assert reconstructed.payload["location"]["latitude"] == loc.latitude

def test_hop_limit_decrement():
    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FIRE", "HIGH", 2, loc)
    env.hop_limit = 2

    can_forward = env.decrement_hop("node_b")
    assert can_forward is True
    assert env.hop_limit == 1
    assert env.current_hop == "node_b"

    # Next decrement should exhaust hop limit
    can_forward_again = env.decrement_hop("node_c")
    assert can_forward_again is False
    assert env.hop_limit == 0

def test_message_expiration():
    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FIRE", "HIGH", 2, loc, ttl_seconds=10)
    assert not env.is_expired(current_time_ms=env.created_at + 5000)
    assert env.is_expired(current_time_ms=env.created_at + 15000)

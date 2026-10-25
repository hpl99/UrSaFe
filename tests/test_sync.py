"""
Unit Tests for UrSafe Persistent Outbox, Inbox, and Priority Queueing
"""
import time
import pytest
from packages.sync.outbox import PersistentOutbox
from packages.sync.inbox import PersistentInbox
from packages.protocol.envelope import MessageEnvelope, Location
from packages.protocol.types import Priority, MessageType

def test_outbox_strict_priority_ordering():
    outbox = PersistentOutbox(db_path=":memory:")
    loc = Location(latitude=10.0, longitude=10.0)

    # 1. Enqueue low priority Telemetry
    telemetry_env = MessageEnvelope.create_sos("node_a", "FIRE", "LOW", 1, loc)
    telemetry_env.message_id = "msg_telemetry"
    telemetry_env.priority = Priority.TELEMETRY
    outbox.enqueue(telemetry_env)

    # 2. Enqueue Routine update
    routine_env = MessageEnvelope.create_sos("node_a", "FIRE", "MEDIUM", 1, loc)
    routine_env.message_id = "msg_routine"
    routine_env.priority = Priority.ROUTINE
    outbox.enqueue(routine_env)

    # 3. Enqueue Critical Life-Safety Emergency SOS
    sos_env = MessageEnvelope.create_sos("node_a", "FLOOD", "CRITICAL", 5, loc)
    sos_env.message_id = "msg_critical_sos"
    sos_env.priority = Priority.EMERGENCY
    outbox.enqueue(sos_env)

    # Strict priority verification: Emergency MUST be pulled first!
    first = outbox.peek_next()
    assert first is not None
    assert first.message_id == "msg_critical_sos"
    assert first.priority == Priority.EMERGENCY

    outbox.mark_acknowledged("msg_critical_sos")

    # Second MUST be Routine
    second = outbox.peek_next()
    assert second is not None
    assert second.message_id == "msg_routine"
    assert second.priority == Priority.ROUTINE

    outbox.mark_acknowledged("msg_routine")

    # Third is Telemetry
    third = outbox.peek_next()
    assert third is not None
    assert third.message_id == "msg_telemetry"
    assert third.priority == Priority.TELEMETRY

def test_outbox_exponential_backoff():
    outbox = PersistentOutbox(db_path=":memory:")
    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FIRE", "HIGH", 1, loc)
    outbox.enqueue(env)

    # First retry failure: delay 1000ms
    outbox.record_retry_failure(env.message_id, base_delay_ms=1000)

    # Immediately after, peek_next with now should find nothing (held in backoff)
    now = int(time.time() * 1000)
    assert outbox.peek_next(current_time_ms=now) is None

    # After backoff expires, peek_next returns the envelope
    ready_time = now + 1500
    assert outbox.peek_next(current_time_ms=ready_time) is not None

def test_inbox_deduplication():
    inbox = PersistentInbox(db_path=":memory:")
    loc = Location(latitude=0.0, longitude=0.0)
    env = MessageEnvelope.create_sos("node_a", "FIRE", "HIGH", 1, loc)

    # First ingest succeeds
    assert inbox.ingest(env) is True
    assert inbox.has_seen(env.message_id) is True

    # Duplicate ingest is rejected
    assert inbox.ingest(env) is False

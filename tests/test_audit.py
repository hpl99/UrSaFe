"""
Unit Tests for UrSafe Tamper-Evident Flight Recorder
"""
import pytest
from packages.audit.flight_recorder import FlightRecorder
from packages.audit.verifier import AuditVerifier

def test_flight_recorder_chain_integrity():
    recorder = FlightRecorder(node_id="station_bravo")

    e1 = recorder.record_event(
        actor="victim_101",
        action="SOS_CREATED",
        target_object="incident_001",
        reason="Flood water entry",
        payload={"level": 2.5},
    )

    e2 = recorder.record_event(
        actor="responder_404",
        action="SOS_ACCEPTED",
        target_object="incident_001",
        reason="Closest qualified unit",
    )

    e3 = recorder.record_event(
        actor="responder_404",
        action="ARRIVED",
        target_object="incident_001",
        reason="On-scene at GPS coordinates",
    )

    assert len(recorder.events) == 3
    is_valid, msg = AuditVerifier.verify_chain(recorder.events)
    assert is_valid is True
    assert "intact" in msg

def test_flight_recorder_tamper_detection():
    recorder = FlightRecorder(node_id="station_bravo")
    recorder.record_event(actor="victim_101", action="SOS_CREATED", target_object="incident_001")
    recorder.record_event(actor="responder_404", action="SOS_ACCEPTED", target_object="incident_001")
    recorder.record_event(actor="responder_404", action="RESCUE_COMPLETED", target_object="incident_001")

    events = recorder.events

    # Attempt to tamper with second event action
    events[1].action = "SOS_DECLINED"

    is_valid, msg = AuditVerifier.verify_chain(events)
    assert is_valid is False
    assert "Tampered event at index 1" in msg

def test_flight_recorder_deletion_detection():
    recorder = FlightRecorder(node_id="station_bravo")
    recorder.record_event(actor="victim_101", action="SOS_CREATED", target_object="incident_001")
    recorder.record_event(actor="coordinator_01", action="ASSIGNMENT_OVERRIDE", target_object="incident_001")
    recorder.record_event(actor="responder_404", action="ARRIVED", target_object="incident_001")

    events = recorder.events
    # Delete middle event
    tampered_chain = [events[0], events[2]]

    is_valid, msg = AuditVerifier.verify_chain(tampered_chain)
    assert is_valid is False
    assert "Broken chain link at index 1" in msg

"""
Unit Tests for Domain Models, Progressive Disclosure, and CRDT State Convergence
"""
import pytest
from packages.protocol.envelope import Location
from packages.domain.models import EmergencyIncident, IncidentStatus
from packages.domain.disclosure import ProgressiveDisclosureEngine, DisclosureLevel
from packages.crdt.vector_clock import VectorClock
from packages.crdt.crdt_state import IncidentCRDTState, LWWRegister, ORSet
from packages.crdt.safety_guard import DomainSafetyGuard

def test_progressive_disclosure_filtering():
    loc = Location(latitude=28.6139, longitude=77.2090)
    incident = EmergencyIncident(
        incident_id="inc_999",
        victim_id="victim_42",
        category="MEDICAL",
        urgency="CRITICAL",
        people_affected=2,
        location=loc,
        description="Elderly patient with severe dyspnea",
        contact_info="+91-9876543210",
        medical_notes="History of coronary artery disease, requires oxygen immediately",
    )

    # Public peer should only see Level 1 (category, people count, coarse location)
    pub_view = ProgressiveDisclosureEngine.filter_incident(incident, viewer_role="PUBLIC")
    assert pub_view["disclosure_level"] == DisclosureLevel.LEVEL_1_COARSE
    assert pub_view["category"] == "MEDICAL"
    assert "precise_location" not in pub_view
    assert "medical_notes" not in pub_view
    assert "contact_info" not in pub_view
    assert pub_view["coarse_location"]["latitude"] == 28.61

    # Dispatched (unaccepted) responder sees Level 2
    disp_view = ProgressiveDisclosureEngine.filter_incident(incident, viewer_role="DISPATCHED_RESPONDER")
    assert disp_view["disclosure_level"] == DisclosureLevel.LEVEL_2_ASSIGNED
    assert "precise_location" not in disp_view

    # Accepted responder sees Level 3 (precise GPS + contact info)
    resp_view = ProgressiveDisclosureEngine.filter_incident(
        incident, viewer_role="RESPONDER", is_assigned_to_viewer=True
    )
    assert resp_view["disclosure_level"] == DisclosureLevel.LEVEL_3_PRECISE
    assert resp_view["precise_location"]["latitude"] == loc.latitude
    assert resp_view["contact_info"] == "+91-9876543210"
    assert "medical_notes" not in resp_view

    # Medical officer sees Level 4
    med_view = ProgressiveDisclosureEngine.filter_incident(
        incident, viewer_role="MEDICAL_OFFICER", is_assigned_to_viewer=True
    )
    assert med_view["disclosure_level"] == DisclosureLevel.LEVEL_4_MEDICAL
    assert "History of coronary artery disease" in med_view["medical_notes"]

def test_vector_clock_causality():
    v1 = VectorClock()
    v1.increment("node_a")

    v2 = v1.copy()
    v2.increment("node_b")

    # v2 causally dominates v1
    assert v2.dominates(v1) is True
    assert v1.dominates(v2) is False
    assert v1.is_concurrent_with(v2) is False

    # Parallel mutation
    v1.increment("node_a")
    # Now v1 has {node_a: 2}, v2 has {node_a: 1, node_b: 1} -> concurrent
    assert v1.is_concurrent_with(v2) is True

    # Merge takes least upper bound
    v_merged = v1.merge(v2)
    assert v_merged.get("node_a") == 2
    assert v_merged.get("node_b") == 1
    assert v_merged.dominates(v1) is True
    assert v_merged.dominates(v2) is True

def test_crdt_algebraic_properties():
    # Test Idempotence: A ⊔ A = A
    state_a = IncidentCRDTState("inc_01", "node_a", initial_status="REPORTED", initial_timestamp=100)
    state_a.update_status("ASSIGNED", 150, "node_a")

    merged_idempotent = state_a.merge(state_a)
    assert merged_idempotent.to_snapshot() == state_a.to_snapshot()

    # Test Commutativity: A ⊔ B = B ⊔ A
    state_b = IncidentCRDTState("inc_01", "node_b", initial_status="REPORTED", initial_timestamp=100)
    state_b.update_status("ACCEPTED", 200, "node_b")

    ab = state_a.merge(state_b)
    ba = state_b.merge(state_a)
    assert ab.to_snapshot() == ba.to_snapshot()

    # Test Associativity: (A ⊔ B) ⊔ C = A ⊔ (B ⊔ C)
    state_c = IncidentCRDTState("inc_01", "node_c", initial_status="REPORTED", initial_timestamp=100)
    state_c.update_people(5, 250, "node_c")

    ab_c = (state_a.merge(state_b)).merge(state_c)
    a_bc = state_a.merge(state_b.merge(state_c))
    assert ab_c.to_snapshot() == a_bc.to_snapshot()

def test_domain_safety_guardrails():
    # If local status is ARRIVED, incoming CANCELLED must be blocked
    resolved_st, resolved_resp, conflict, reason = DomainSafetyGuard.evaluate_transition(
        current_local_status="ARRIVED",
        incoming_merged_status="CANCELLED",
        current_assigned_responder="medic_01",
        incoming_assigned_responder="",
    )
    assert resolved_st == "ARRIVED"
    assert resolved_resp == "medic_01"
    assert conflict is True
    assert "SAFETY OVERRIDE" in reason

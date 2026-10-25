"""
Unit Tests for Hazard Engine and Dispatch Optimization
"""
import pytest
from services.hazard.polygon import HazardPolygon, Point2D
from services.hazard.engine import HazardEngine
from services.dispatch.optimizer import DispatchOptimizer
from services.dispatch.benchmark import DispatchBenchmark
from packages.domain.models import EmergencyIncident, ResponderProfile
from packages.protocol.envelope import Location

def test_hazard_kinematic_expansion_and_route_intersection():
    engine = HazardEngine()

    # Square flood polygon centered around lat 19.05, lon 72.85
    verts = [
        Point2D(x=72.84, y=19.04),
        Point2D(x=72.86, y=19.04),
        Point2D(x=72.86, y=19.06),
        Point2D(x=72.84, y=19.06),
    ]

    hazard = HazardPolygon(
        hazard_id="flood_zone_alpha",
        hazard_type="FLOOD",
        status="OBSERVED",
        severity=0.85,
        vertices=verts,
        valid_from=1000,
        valid_until=100000,
        expansion_rate_mps=5.0, # Expands at 5 meters per second
        expansion_direction_deg=90.0, # Moving East
    )
    engine.add_or_update_hazard(hazard)

    # Case 1: Route crossing straight through the flood zone to safe destination beyond
    start = Point2D(x=72.80, y=19.05)
    dest_safe = Point2D(x=72.95, y=19.05)

    eval_result = engine.evaluate_route_safety(
        start_coord=start,
        destination_coord=dest_safe,
        departure_time_ms=1000,
        eta_seconds=600, # 10 mins
    )

    assert eval_result.is_safe is False
    assert eval_result.verdict == "HAZARD_INTERSECTION"
    assert eval_result.avoidance_waypoints is not None
    assert len(eval_result.avoidance_waypoints) == 3

    # Case 2: Destination is inside expanding flood
    dest_submerged = Point2D(x=72.88, y=19.05)
    eval_submerged = engine.evaluate_route_safety(
        start_coord=start,
        destination_coord=dest_submerged,
        departure_time_ms=1000,
        eta_seconds=600,
    )
    assert eval_submerged.is_safe is False
    assert eval_submerged.verdict == "DESTINATION_INSIDE_HAZARD"

def test_scarce_resource_reservation():
    optimizer = DispatchOptimizer()

    loc_incident = Location(latitude=19.0760, longitude=72.8777)
    loc_responder = Location(latitude=19.0800, longitude=72.8800)

    # Specialized paramedic / trauma surgeon
    specialist = ResponderProfile(
        responder_id="resp_surgeon_01",
        callsign="Med-Specialist-1",
        organization_id="ems",
        roles=["SURGEON"],
        skills=["ADVANCED_LIFE_SUPPORT", "TRAUMA_SURGERY"],
        current_location=loc_responder,
    )

    # General first aid volunteer
    volunteer = ResponderProfile(
        responder_id="resp_vol_02",
        callsign="Volunteer-2",
        organization_id="civic",
        roles=["VOLUNTEER"],
        skills=["FIRST_AID", "GENERAL_RESCUE"],
        current_location=loc_responder,
    )

    # Low urgency incident with active critical incidents in the field
    routine_incident = EmergencyIncident(
        incident_id="inc_low_01",
        victim_id="vic_01",
        category="MEDICAL",
        urgency="LOW",
        people_affected=1,
        location=loc_incident,
    )

    # In low urgency when critical incidents exist, specialist is guarded; volunteer is assigned!
    decision = optimizer.select_best_assignment(
        routine_incident, [specialist, volunteer], active_critical_incident_count=3
    )
    assert decision.selected_responder_id == "resp_vol_02"

    # For critical life-threatening call, specialist is dispatched immediately
    critical_incident = EmergencyIncident(
        incident_id="inc_crit_01",
        victim_id="vic_02",
        category="MEDICAL",
        urgency="CRITICAL",
        people_affected=2,
        location=loc_incident,
    )
    decision_crit = optimizer.select_best_assignment(
        critical_incident, [specialist, volunteer], active_critical_incident_count=3
    )
    assert decision_crit.selected_responder_id == "resp_surgeon_01"

def test_dispatch_benchmark_greedy_vs_optimized():
    benchmark = DispatchBenchmark(seed=42)
    results = benchmark.run_benchmark(num_incidents=20, num_responders=8)

    assert "greedy_baseline" in results
    assert "optimized_dispatch" in results
    assert "measured_improvements" in results

    # The benchmark produces real, empirical comparison measurements
    opt = results["optimized_dispatch"]
    greedy = results["greedy_baseline"]
    assert "critical_mean_eta_mins" in opt and opt["critical_mean_eta_mins"] > 0
    assert "critical_mean_eta_mins" in greedy and greedy["critical_mean_eta_mins"] > 0
    assert "skill_match_gain_percent" in results["measured_improvements"]
    assert opt["served_count"] == 8
    assert greedy["served_count"] == 8

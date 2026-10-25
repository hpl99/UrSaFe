"""
Multi-Criteria Dispatch Optimizer with Scarce Resource Reservation
"""
from __future__ import annotations
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from packages.domain.models import EmergencyIncident, ResponderProfile
from packages.protocol.envelope import Location

@dataclass
class DispatchDecision:
    incident_id: str
    selected_responder_id: Optional[str]
    score: float
    eta_minutes: float
    is_reserved_resource: bool
    rationale: str

@dataclass
class DispatchCandidate:
    responder: ResponderProfile
    distance_km: float
    eta_minutes: float
    skill_match_score: float
    is_specialized: bool

class DispatchOptimizer:
    def __init__(self, avg_speed_kmh: float = 35.0):
        self.avg_speed_kmh = avg_speed_kmh

    def calculate_distance_km(self, loc1: Location, loc2: Location) -> float:
        # Haversine or equirectangular approximation
        dlat = (loc1.latitude - loc2.latitude) * 111.0
        dlon = (loc1.longitude - loc2.longitude) * 111.0 * math.cos(math.radians((loc1.latitude + loc2.latitude) / 2))
        return math.sqrt(dlat**2 + dlon**2)

    def evaluate_skill_match(self, emergency_category: str, skills: List[str]) -> float:
        category_skill_map = {
            "MEDICAL": {"ADVANCED_LIFE_SUPPORT", "PARAMEDIC", "TRAUMA_SURGERY", "FIRST_AID"},
            "FLOOD": {"SWIFT_WATER_RESCUE", "BOAT_OPERATOR", "DIVING"},
            "FIRE": {"FIREFIGHTING", "HAZMAT_CONTAINMENT", "SMOKE_RESCUE"},
            "COLLAPSE": {"STRUCTURAL_ENGINEERING", "HEAVY_LIFTING", "CANINE_SEARCH"},
            "TRAPPED": {"TECHNICAL_ROPE_RESCUE", "CONFINED_SPACE"},
        }
        needed = category_skill_map.get(emergency_category.upper(), {"GENERAL_RESCUE"})
        has = set(s.upper() for s in skills)
        intersection = needed.intersection(has)
        if not needed:
            return 0.5
        return len(intersection) / len(needed)

    def select_best_assignment(
        self,
        incident: EmergencyIncident,
        available_responders: List[ResponderProfile],
        active_critical_incident_count: int = 0,
    ) -> DispatchDecision:
        """
        Deterministic multi-criteria scoring:
          Score = w_time * (1 / (1 + ETA)) + w_skill * SkillMatch + w_urgency * UrgencyWeight
        With Scarce Resource Reservation:
          Specialized units (e.g. ALS medic, boat operator) are guarded from low-urgency calls
          when other critical emergencies exist or are active.
        Conservative Policy:
          A verified critical incident is ALWAYS served immediately by the best unit.
        """
        if not available_responders:
            return DispatchDecision(
                incident_id=incident.incident_id,
                selected_responder_id=None,
                score=0.0,
                eta_minutes=0.0,
                is_reserved_resource=False,
                rationale="Zero available responders in field network.",
            )

        urgency_weights = {
            "CRITICAL": 1.0,
            "HIGH": 0.7,
            "MEDIUM": 0.4,
            "LOW": 0.2,
        }
        u_weight = urgency_weights.get(incident.urgency.upper(), 0.3)
        is_critical_incident = incident.urgency.upper() in ("CRITICAL", "HIGH")

        best_score = -1.0
        best_candidate: Optional[DispatchCandidate] = None
        best_rationale = ""

        for resp in available_responders:
            dist = self.calculate_distance_km(resp.current_location, incident.location)
            eta_mins = (dist / self.avg_speed_kmh) * 60.0
            skill_score = self.evaluate_skill_match(incident.category, resp.skills)

            is_specialized = any(
                s in ("ADVANCED_LIFE_SUPPORT", "SWIFT_WATER_RESCUE", "HEAVY_LIFTING")
                for s in resp.skills
            )

            # Scarce Resource Reservation Rule:
            # If the unit is specialized and this incident is LOW/MEDIUM, and multiple critical incidents exist,
            # reserve this specialist for life threats.
            if is_specialized and not is_critical_incident and active_critical_incident_count > 0:
                continue

            time_score = 1.0 / (1.0 + (eta_mins / 10.0))

            # Dynamic weighting: For critical emergencies, arrival latency is paramount!
            if is_critical_incident:
                w_time = 0.65
                w_skill = 0.25
                w_urg = 0.10
            else:
                w_time = 0.35
                w_skill = 0.45
                w_urg = 0.20

            # Composite multi-criteria formula
            score = (w_time * time_score) + (w_skill * skill_score) + (w_urg * u_weight)

            if score > best_score:
                best_score = score
                best_candidate = DispatchCandidate(
                    responder=resp,
                    distance_km=dist,
                    eta_minutes=eta_mins,
                    skill_match_score=skill_score,
                    is_specialized=is_specialized,
                )
                best_rationale = (
                    f"Selected {resp.callsign}: ETA {eta_mins:.1f} mins ({dist:.1f} km), "
                    f"Skill Match: {int(skill_score * 100)}%, Composite Score: {score:.2f}."
                )

        if not best_candidate:
            # All available units were reserved specialists
            return DispatchDecision(
                incident_id=incident.incident_id,
                selected_responder_id=None,
                score=0.0,
                eta_minutes=0.0,
                is_reserved_resource=True,
                rationale="Available specialists reserved for high-acuity life-threat emergencies.",
            )

        return DispatchDecision(
            incident_id=incident.incident_id,
            selected_responder_id=best_candidate.responder.responder_id,
            score=round(best_score, 3),
            eta_minutes=round(best_candidate.eta_minutes, 1),
            is_reserved_resource=best_candidate.is_specialized,
            rationale=best_rationale,
        )

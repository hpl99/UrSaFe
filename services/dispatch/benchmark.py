"""
Dispatch Benchmark Engine
Executes deterministic comparisons between Baseline Greedy and Multi-Criteria Optimized Dispatch.
Reports actual empirical measurements across identical seeded scenarios.
"""
from __future__ import annotations
import random
from typing import List, Dict, Any, Tuple
from packages.domain.models import EmergencyIncident, ResponderProfile, IncidentStatus
from packages.protocol.envelope import Location
from .optimizer import DispatchOptimizer

class DispatchBenchmark:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.optimizer = DispatchOptimizer()

    def generate_scenario(
        self,
        num_incidents: int = 25,
        num_responders: int = 8,
    ) -> Tuple[List[EmergencyIncident], List[ResponderProfile]]:
        """Generates deterministic synthetic disaster scenario centered on a flood basin."""
        rng = random.Random(self.seed)
        base_lat, base_lon = 19.0760, 72.8777 # Mumbai disaster basin

        categories = ["FLOOD", "MEDICAL", "COLLAPSE", "FIRE", "TRAPPED"]
        urgencies = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        skills_pool = [
            ["SWIFT_WATER_RESCUE", "BOAT_OPERATOR"],
            ["ADVANCED_LIFE_SUPPORT", "PARAMEDIC"],
            ["STRUCTURAL_ENGINEERING", "HEAVY_LIFTING"],
            ["FIREFIGHTING", "SMOKE_RESCUE"],
            ["FIRST_AID", "GENERAL_RESCUE"],
        ]

        responders: List[ResponderProfile] = []
        for i in range(num_responders):
            r_lat = base_lat + rng.uniform(-0.08, 0.08)
            r_lon = base_lon + rng.uniform(-0.08, 0.08)
            skills = skills_pool[i % len(skills_pool)]
            responders.append(ResponderProfile(
                responder_id=f"resp_{i:02d}",
                callsign=f"Unit-{i+1:02d}",
                organization_id="ndrf_ops",
                roles=["RESCUER"],
                skills=skills,
                current_location=Location(latitude=r_lat, longitude=r_lon),
                is_available=True,
            ))

        incidents: List[EmergencyIncident] = []
        for i in range(num_incidents):
            i_lat = base_lat + rng.uniform(-0.10, 0.10)
            i_lon = base_lon + rng.uniform(-0.10, 0.10)
            cat = rng.choice(categories)
            urg = rng.choice(urgencies)
            incidents.append(EmergencyIncident(
                incident_id=f"inc_{i:02d}",
                victim_id=f"vic_{i:02d}",
                category=cat,
                urgency=urg,
                people_affected=rng.randint(1, 6),
                location=Location(latitude=i_lat, longitude=i_lon),
            ))

        return incidents, responders

    def run_benchmark(self, num_incidents: int = 30, num_responders: int = 10) -> Dict[str, Any]:
        """Runs both Greedy and Optimized dispatch on identical seeded inputs."""
        incidents, responders = self.generate_scenario(num_incidents, num_responders)

        # 1. Baseline Greedy (pure nearest distance, ignores skills and scarce reservation)
        greedy_metrics = self._simulate_greedy(incidents, responders)

        # 2. Multi-Criteria Optimized Dispatch
        optimized_metrics = self._simulate_optimized(incidents, responders)

        return {
            "scenario": {
                "num_incidents": num_incidents,
                "num_responders": num_responders,
                "seed": self.seed,
            },
            "greedy_baseline": greedy_metrics,
            "optimized_dispatch": optimized_metrics,
            "measured_improvements": {
                "critical_delay_reduction_minutes": round(
                    greedy_metrics["critical_mean_eta_mins"] - optimized_metrics["critical_mean_eta_mins"], 2
                ),
                "unserved_difference": greedy_metrics["unserved_incidents"] - optimized_metrics["unserved_incidents"],
                "skill_match_gain_percent": round(
                    (optimized_metrics["average_skill_match"] - greedy_metrics["average_skill_match"]) * 100, 1
                ),
            },
        }

    def _simulate_greedy(
        self, incidents: List[EmergencyIncident], responders: List[ResponderProfile]
    ) -> Dict[str, Any]:
        available = list(responders)
        etas: List[float] = []
        critical_etas: List[float] = []
        unserved = 0
        skill_matches: List[float] = []

        for inc in incidents:
            if not available:
                unserved += 1
                continue

            # Greedy nearest neighbor
            best_r = min(available, key=lambda r: self.optimizer.calculate_distance_km(r.current_location, inc.location))
            dist = self.optimizer.calculate_distance_km(best_r.current_location, inc.location)
            eta = (dist / self.optimizer.avg_speed_kmh) * 60.0
            skill = self.optimizer.evaluate_skill_match(inc.category, best_r.skills)

            etas.append(eta)
            skill_matches.append(skill)
            if inc.urgency.upper() in ("CRITICAL", "HIGH"):
                critical_etas.append(eta)

            available.remove(best_r)

        return {
            "mean_eta_mins": round(sum(etas) / max(1, len(etas)), 1),
            "critical_mean_eta_mins": round(sum(critical_etas) / max(1, len(critical_etas)), 1),
            "unserved_incidents": unserved,
            "average_skill_match": round(sum(skill_matches) / max(1, len(skill_matches)), 2),
            "served_count": len(etas),
        }

    def _simulate_optimized(
        self, incidents: List[EmergencyIncident], responders: List[ResponderProfile]
    ) -> Dict[str, Any]:
        available = list(responders)
        etas: List[float] = []
        critical_etas: List[float] = []
        unserved = 0
        skill_matches: List[float] = []

        # Sort incidents by urgency so critical calls are evaluated first
        urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_incidents = sorted(incidents, key=lambda i: urgency_order.get(i.urgency.upper(), 4))

        critical_count = sum(1 for i in sorted_incidents if i.urgency.upper() in ("CRITICAL", "HIGH"))

        for inc in sorted_incidents:
            if not available:
                unserved += 1
                continue

            decision = self.optimizer.select_best_assignment(
                inc, available, active_critical_incident_count=critical_count
            )
            if decision.selected_responder_id:
                chosen_r = next(r for r in available if r.responder_id == decision.selected_responder_id)
                etas.append(decision.eta_minutes)
                skill = self.optimizer.evaluate_skill_match(inc.category, chosen_r.skills)
                skill_matches.append(skill)

                if inc.urgency.upper() in ("CRITICAL", "HIGH"):
                    critical_etas.append(decision.eta_minutes)
                    critical_count -= 1

                available.remove(chosen_r)
            else:
                unserved += 1

        return {
            "mean_eta_mins": round(sum(etas) / max(1, len(etas)), 1),
            "critical_mean_eta_mins": round(sum(critical_etas) / max(1, len(critical_etas)), 1),
            "unserved_incidents": unserved,
            "average_skill_match": round(sum(skill_matches) / max(1, len(skill_matches)), 2),
            "served_count": len(etas),
        }

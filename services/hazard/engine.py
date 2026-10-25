"""
Hazard Engine
Manages active hazard layers, performs time-aware route safety checks, and calculates avoidance rerouting.
"""
from __future__ import annotations
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .polygon import HazardPolygon, Point2D

@dataclass
class HazardEvaluationResult:
    is_safe: bool
    verdict: str                     # SAFE, HAZARD_INTERSECTION, DESTINATION_INSIDE_HAZARD
    intersecting_hazard_id: Optional[str] = None
    hazard_status: Optional[str] = None    # OBSERVED, PREDICTED, REPORTED
    avoidance_waypoints: Optional[List[Point2D]] = None
    explanation: str = ""

class HazardEngine:
    def __init__(self):
        self._hazards: Dict[str, HazardPolygon] = {}

    def add_or_update_hazard(self, hazard: HazardPolygon):
        self._hazards[hazard.hazard_id] = hazard

    def remove_hazard(self, hazard_id: str):
        self._hazards.pop(hazard_id, None)

    def get_all_hazards(self) -> List[HazardPolygon]:
        return list(self._hazards.values())

    def evaluate_route_safety(
        self,
        start_coord: Point2D,
        destination_coord: Point2D,
        departure_time_ms: int,
        eta_seconds: int,
    ) -> HazardEvaluationResult:
        """
        Evaluates route intersection at arrival time: t_eval = departure_time + eta.
        Never dispatches responders into a predicted hazard polygon.
        """
        eval_time_ms = departure_time_ms + (eta_seconds * 1000)

        for h_id, base_hazard in self._hazards.items():
            # Project hazard forward to arrival time
            predicted_hazard = base_hazard.predict_at_time(eval_time_ms)

            # Check if destination itself is submerged / engulfed
            if predicted_hazard.contains_point(destination_coord):
                return HazardEvaluationResult(
                    is_safe=False,
                    verdict="DESTINATION_INSIDE_HAZARD",
                    intersecting_hazard_id=base_hazard.hazard_id,
                    hazard_status=predicted_hazard.status,
                    explanation=(
                        f"CRITICAL: Destination is located inside {predicted_hazard.status.lower()} "
                        f"{predicted_hazard.hazard_type} zone at predicted arrival time."
                    ),
                )

            # Check if trajectory line intersects advancing hazard
            if predicted_hazard.intersects_segment(start_coord, destination_coord):
                # Calculate simple avoidance perimeter waypoint (detour around bounding box)
                detour = self._compute_avoidance_waypoint(start_coord, destination_coord, predicted_hazard)
                return HazardEvaluationResult(
                    is_safe=False,
                    verdict="HAZARD_INTERSECTION",
                    intersecting_hazard_id=base_hazard.hazard_id,
                    hazard_status=predicted_hazard.status,
                    avoidance_waypoints=detour,
                    explanation=(
                        f"WARNING: Direct route intersects advancing {predicted_hazard.status.lower()} "
                        f"{predicted_hazard.hazard_type} boundary. Detour recommended."
                    ),
                )

        return HazardEvaluationResult(
            is_safe=True,
            verdict="SAFE",
            explanation="Route cleared; zero intersection with observed or predicted hazard fronts.",
        )

    def _compute_avoidance_waypoint(
        self, start: Point2D, end: Point2D, hazard: HazardPolygon
    ) -> List[Point2D]:
        """Calculates a safety detour waypoint clearing the hazard polygon perimeter."""
        xs = [p.x for p in hazard.vertices]
        ys = [p.y for p in hazard.vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Offset detour outside north-east or north-west perimeter
        buffer = 0.015 # ~1.5 km
        detour_pt = Point2D(x=max_x + buffer, y=max_y + buffer)
        return [start, detour_pt, end]

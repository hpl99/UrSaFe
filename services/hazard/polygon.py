"""
Hazard Polygon Geometry and Kinematic Expansion Modeling
"""
from __future__ import annotations
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class Point2D:
    x: float # Longitude or X coordinate in meters
    y: float # Latitude or Y coordinate in meters

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> Point2D:
        return cls(**data)

@dataclass
class HazardPolygon:
    hazard_id: str
    hazard_type: str         # FLOOD, FIRE, LANDSLIDE, ROAD_CLOSURE, TOXIC_ZONE
    status: str              # OBSERVED, PREDICTED, REPORTED
    severity: float          # 0.0 to 1.0
    vertices: List[Point2D]
    valid_from: int
    valid_until: int
    expansion_rate_mps: float = 0.0     # meters per second or deg per sec
    expansion_direction_deg: float = 0.0 # 0=North, 90=East, 180=South, 270=West

    def predict_at_time(self, target_time_ms: int) -> HazardPolygon:
        """Projects polygon vertices forward in time using kinematic expansion vector."""
        if target_time_ms <= self.valid_from or self.expansion_rate_mps <= 0.0:
            return self

        elapsed_sec = (target_time_ms - self.valid_from) / 1000.0
        dist = self.expansion_rate_mps * elapsed_sec

        # 1 degree lat approx 111,000 meters
        rad = math.radians(self.expansion_direction_deg)
        dx_deg = (dist * math.sin(rad)) / 111000.0
        dy_deg = (dist * math.cos(rad)) / 111000.0

        projected_vertices = [
            Point2D(x=p.x + dx_deg, y=p.y + dy_deg) for p in self.vertices
        ]

        return HazardPolygon(
            hazard_id=f"{self.hazard_id}_pred",
            hazard_type=self.hazard_type,
            status="PREDICTED",
            severity=min(1.0, self.severity * (1.0 + (elapsed_sec * 0.0001))),
            vertices=projected_vertices,
            valid_from=target_time_ms,
            valid_until=self.valid_until + int(elapsed_sec * 1000),
            expansion_rate_mps=self.expansion_rate_mps,
            expansion_direction_deg=self.expansion_direction_deg,
        )

    def contains_point(self, pt: Point2D) -> bool:
        """Ray-casting algorithm to test whether pt is inside polygon."""
        inside = False
        n = len(self.vertices)
        if n < 3:
            return False

        p1 = self.vertices[0]
        for i in range(1, n + 1):
            p2 = self.vertices[i % n]
            if pt.y > min(p1.y, p2.y):
                if pt.y <= max(p1.y, p2.y):
                    if pt.x <= max(p1.x, p2.x):
                        if p1.y != p2.y:
                            x_inters = (pt.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        if p1.x == p2.x or pt.x <= x_inters:
                            inside = not inside
            p1 = p2
        return inside

    def intersects_segment(self, start: Point2D, end: Point2D) -> bool:
        """Tests if line segment (start -> end) intersects any polygon edge or lies inside."""
        if self.contains_point(start) or self.contains_point(end):
            return True

        n = len(self.vertices)
        for i in range(n):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % n]
            if lines_intersect(start, end, v1, v2):
                return True
        return False

def ccw(A: Point2D, B: Point2D, C: Point2D) -> bool:
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)

def lines_intersect(A: Point2D, B: Point2D, C: Point2D, D: Point2D) -> bool:
    """Returns True if line segment AB intersects line segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

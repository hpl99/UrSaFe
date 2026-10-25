"""
Domain Models for Emergencies, Responders, and Assignments
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from packages.protocol.envelope import Location

class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    RESCUE_IN_PROGRESS = "RESCUE_IN_PROGRESS"
    RESCUED = "RESCUED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"

@dataclass
class EmergencyIncident:
    incident_id: str
    victim_id: str
    category: str
    urgency: str
    people_affected: int
    location: Location
    status: IncidentStatus = IncidentStatus.REPORTED
    assigned_responder_id: Optional[str] = None
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    description: str = ""
    immediate_needs: List[str] = field(default_factory=list)
    medical_notes: str = ""
    contact_info: str = ""
    receipt_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmergencyIncident:
        d = dict(data)
        d["location"] = Location.from_dict(d["location"])
        d["status"] = IncidentStatus(d["status"])
        return cls(**d)

@dataclass
class ResponderProfile:
    responder_id: str
    callsign: str
    organization_id: str
    roles: List[str]
    skills: List[str]
    current_location: Location
    is_available: bool = True
    assigned_incident_id: Optional[str] = None
    credential_id: Optional[str] = None
    reputation_score: float = 1.0
    trust_tier: str = "NORMAL"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ResponderProfile:
        d = dict(data)
        d["current_location"] = Location.from_dict(d["current_location"])
        return cls(**d)

@dataclass
class AssignmentState:
    incident_id: str
    responder_id: str
    assigned_at: int
    accepted_at: Optional[int] = None
    arrived_at: Optional[int] = None
    completed_at: Optional[int] = None
    status: str = "ASSIGNED"          # ASSIGNED, ACCEPTED, DECLINED, ARRIVED, COMPLETED, CANCELLED

"""
Progressive Information Disclosure Engine (5-Tier Privacy Filter)
Levels:
  LEVEL 0: Anonymous emergency exists (presence only, no coordinates, no category)
  LEVEL 1: Approximate area (coarse geohash / ~2km radius) + emergency category
  LEVEL 2: Assignment details (broad vector for dispatched responders)
  LEVEL 3: Precise GPS location + contact info (strictly for accepted responder)
  LEVEL 4: Sensitive medical & special-needs data (under authorized medical policy)
"""
from enum import IntEnum
from typing import Dict, Any, Optional
import math
from .models import EmergencyIncident

class DisclosureLevel(IntEnum):
    LEVEL_0_PRESENCE = 0
    LEVEL_1_COARSE = 1
    LEVEL_2_ASSIGNED = 2
    LEVEL_3_PRECISE = 3
    LEVEL_4_MEDICAL = 4

class ProgressiveDisclosureEngine:
    @staticmethod
    def filter_incident(
        incident: EmergencyIncident,
        viewer_role: str,                 # "PUBLIC", "DISPATCHED_RESPONDER", "ACCEPTED_RESPONDER", "MEDICAL_OFFICER", "COORDINATOR"
        is_assigned_to_viewer: bool = False
    ) -> Dict[str, Any]:
        """Filters an EmergencyIncident dictionary to the maximum permissible disclosure level."""
        level = ProgressiveDisclosureEngine.determine_allowed_level(viewer_role, is_assigned_to_viewer)
        return ProgressiveDisclosureEngine.render_at_level(incident, level)

    @staticmethod
    def determine_allowed_level(viewer_role: str, is_assigned: bool) -> DisclosureLevel:
        if viewer_role in ("COORDINATOR", "ADMIN"):
            return DisclosureLevel.LEVEL_4_MEDICAL
        if viewer_role == "MEDICAL_OFFICER" and is_assigned:
            return DisclosureLevel.LEVEL_4_MEDICAL
        if viewer_role == "RESPONDER" and is_assigned:
            return DisclosureLevel.LEVEL_3_PRECISE
        if viewer_role == "DISPATCHED_RESPONDER":
            return DisclosureLevel.LEVEL_2_ASSIGNED
        if viewer_role == "RESPONDER" and not is_assigned:
            return DisclosureLevel.LEVEL_1_COARSE
        # Public or unknown peer on the open mesh
        return DisclosureLevel.LEVEL_1_COARSE

    @staticmethod
    def render_at_level(incident: EmergencyIncident, level: DisclosureLevel) -> Dict[str, Any]:
        base = {
            "incident_id": incident.incident_id,
            "disclosure_level": int(level),
            "status": incident.status.value,
        }

        if level == DisclosureLevel.LEVEL_0_PRESENCE:
            base["emergency_exists"] = True
            return base

        # Level 1+: Category, people affected, coarse location (rounded to ~2km / 0.02 deg)
        coarse_lat = round(incident.location.latitude, 2)
        coarse_lon = round(incident.location.longitude, 2)
        base.update({
            "category": incident.category,
            "urgency": incident.urgency,
            "people_affected": incident.people_affected,
            "coarse_location": {"latitude": coarse_lat, "longitude": coarse_lon, "radius_meters": 2000},
            "created_at": incident.created_at,
        })

        if level == DisclosureLevel.LEVEL_1_COARSE:
            return base

        # Level 2+: Broad vector and assigned responder
        base.update({
            "assigned_responder_id": incident.assigned_responder_id,
            "immediate_needs": incident.immediate_needs,
        })

        if level == DisclosureLevel.LEVEL_2_ASSIGNED:
            return base

        # Level 3+: Precise GPS location, description, and contact info
        base.update({
            "precise_location": incident.location.to_dict(),
            "description": incident.description,
            "contact_info": incident.contact_info,
        })

        if level == DisclosureLevel.LEVEL_3_PRECISE:
            return base

        # Level 4: Medical notes & special needs
        base.update({
            "medical_notes": incident.medical_notes,
        })
        return base

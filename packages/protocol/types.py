"""
UrSafe Message and State Enumerations
"""
from enum import Enum, IntEnum

class Priority(IntEnum):
    """Priority levels: lower numeric value represents strictly higher delivery priority."""
    EMERGENCY = 1   # Life-safety SOS, Acceptances, Critical alerts
    HIGH = 2        # Assignments, active hazard progression
    ROUTINE = 3     # Status updates, mutual acknowledgments
    TELEMETRY = 4   # Node announcements, battery metrics, link pings

class MessageType(str, Enum):
    # SOS Lifecycle
    SOS_CREATED = "SOS_CREATED"
    SOS_UPDATED = "SOS_UPDATED"
    SOS_CANCELLED = "SOS_CANCELLED"
    SOS_ACKNOWLEDGED = "SOS_ACKNOWLEDGED"
    SOS_ASSIGNED = "SOS_ASSIGNED"
    SOS_ACCEPTED = "SOS_ACCEPTED"
    SOS_DECLINED = "SOS_DECLINED"

    # Responder Lifecycle
    RESPONDER_STATUS = "RESPONDER_STATUS"
    RESPONDER_LOCATION = "RESPONDER_LOCATION"
    ARRIVED = "ARRIVED"
    RESCUE_STARTED = "RESCUE_STARTED"
    RESCUE_COMPLETED = "RESCUE_COMPLETED"
    RESCUE_RECEIPT = "RESCUE_RECEIPT"

    # Credentials & Security
    CREDENTIAL_ISSUED = "CREDENTIAL_ISSUED"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"
    SECURITY_ALERT = "SECURITY_ALERT"

    # Network Topology & Routing
    ROUTE_UPDATE = "ROUTE_UPDATE"
    NODE_ANNOUNCEMENT = "NODE_ANNOUNCEMENT"
    NODE_STATUS = "NODE_STATUS"
    PARTITION_DETECTED = "PARTITION_DETECTED"
    PARTITION_HEALED = "PARTITION_HEALED"

    # Hazards
    HAZARD_UPDATE = "HAZARD_UPDATE"

    # Synchronization
    SYNC_REQUEST = "SYNC_REQUEST"
    SYNC_RESPONSE = "SYNC_RESPONSE"

class DeliveryState(str, Enum):
    QUEUED_LOCAL = "QUEUED_LOCAL"
    TRANSMITTED_MESH = "TRANSMITTED_MESH"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DELIVERED = "DELIVERED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"

class EmergencyCategory(str, Enum):
    FLOOD = "FLOOD"
    FIRE = "FIRE"
    MEDICAL = "MEDICAL"
    TRAPPED = "TRAPPED"
    COLLAPSE = "COLLAPSE"
    EVACUATION = "EVACUATION"
    HAZMAT = "HAZMAT"
    GENERAL = "GENERAL"

class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

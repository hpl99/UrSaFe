# UrSafe Emergency Incident Lifecycle Specification

## 1. Overview

UrSafe replaces superficial UI status flags with a deterministic, role-enforced domain state machine. Every emergency incident moves through verified stages persisted atomically in the local SQLite database and synchronized across peers.

---

## 2. Complete 18-State Lifecycle Pipeline

```text
DRAFT
  ↓
SOS_CREATED
  ↓
SAVED_LOCALLY
  ↓
QUEUED
  ↓
TRANSMITTING
  ↓
RECEIVED
  ↓
RESPONDER_NOTIFIED
  ↓
RESPONDER_ASSIGNED
  ↓
MISSION_ACCEPTED
  ↓
EN_ROUTE
  ↓
ARRIVED_ON_SCENE
  ↓
RESCUE_IN_PROGRESS
  ↓
RESCUE_COMPLETED
  ↓
EVIDENCE_REQUIRED
  ↓
EVIDENCE_SUBMITTED
  ↓
VERIFICATION_PENDING
  ↓
VERIFIED
  ↓
CLOSED
```

### Controlled Exceptional States

- `CANCELLED`: Citizen safely cancels distress beacon prior to arrival.
- `REJECTED`: Responder or Authority rejects assignment or evidence with mandatory audit reason.
- `FAILED`: Radio transmission or physical rescue failure recorded.
- `EXPIRED`: Operational TTL reached without confirmation.
- `DUPLICATE`: Redundant distress beacon merged into primary incident.
- `REOPENED`: Historical closed case reactivated by Authority for post-incident investigation.

---

## 3. Transition Envelope Schema

Every state transition generates an immutable event record:

```json
{
  "incident_id": "inc-2026-000042",
  "from_status": "MISSION_ACCEPTED",
  "to_status": "EN_ROUTE",
  "actor_user_id": "usr-responder-01",
  "actor_role": "RESPONDER",
  "timestamp": 1729898520000,
  "device_id": "dev-android-82a1",
  "reason": "Medic deploying with ALS watercraft kit",
  "latitude": 28.650805,
  "longitude": 77.230014,
  "evidence_reference": null,
  "receipt_reference": null
}
```

---

## 4. Role Authorization Matrix

| Action | Permitted Roles | Notes |
| :--- | :--- | :--- |
| Create SOS | `CITIZEN` | Immediately persists locally in SQLite outbox queue |
| Cancel SOS | `CITIZEN`, `AUTHORITY` | Permitted prior to rescue completion |
| Assign Responder | `AUTHORITY`, `ADMIN` | Sets incident status to `RESPONDER_ASSIGNED` / `DISPATCHED` |
| Accept Mission | `RESPONDER` | Updates responder availability to `BUSY` |
| Reject Mission | `RESPONDER` | **Mandatory reason required**; frees incident for re-dispatch |
| Mark En Route | `RESPONDER` | Initiates real-time location streaming to coordinator |
| Arrived On Scene | `RESPONDER` | GNSS proximity verified against incident coordinates |
| Start Rescue | `RESPONDER` | Marks tactical field extraction underway |
| Complete Rescue | `RESPONDER` | Flags status as `EVIDENCE_REQUIRED` |
| Upload Evidence | `RESPONDER` | Generates SHA-256 hash and verifies against duplicate collisions |
| Verify Evidence | `AUTHORITY`, `ADMIN` | Co-signs rescue clearance certificate (`VERIFIED`) |
| Reject Evidence | `AUTHORITY`, `ADMIN` | **Mandatory audit reason required** |
| Close Incident | `AUTHORITY`, `ADMIN` | Moves incident from active list to permanent Emergency History |
| Reopen Incident | `AUTHORITY`, `ADMIN` | **Mandatory audit reason required**; re-adds case to active queue |

---

## 5. Emergency History Archive & Reopening

1. **Separation of Concerns**: Closed, verified, and cancelled cases are archived in a dedicated portal (`#view-emergency-history`) and filtered out of active dispatch queues.
2. **Case Detail Modal**: Historical cases retain their full 18-state chronological timeline, attached evidence gallery, exact GPS coordinates, and decision audit logs.
3. **Audited Reopening**: If secondary complications or aftershocks occur, an Authority can reopen the historical case (`POST /api/v1/incidents/:id/reopen`) with an explicit operational reason.

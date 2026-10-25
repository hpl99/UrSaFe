# UrSafe Backend Control Plane & Data Architecture

## 1. Subsystem Architecture

The UrSafe Backend (`apps/api`) provides the authoritative central coordination hub, authentication gateway, incident dispatch registry, and cryptographic verification authority.

```text
HTTP / WebSocket Clients
          │
          ▼
[ Node.js API Gateway (apps/api/server.js) ]
  ├── /api/v1/health (Comprehensive Subsystem Status)
  ├── /api/v1/auth/* (PBKDF2 Login, Token Verification, Logout)
  ├── /api/v1/incidents/* (Triage, Dispatch, Evidence, Verification)
  ├── /api/v1/responders/* (Profiles, Online State, Credentials)
  ├── /api/v1/mesh/* (Topology, Nodes, Packets)
  └── /api/v1/audit/* (Flight Recorder Merkle-like Hash Chain)
          │
          ▼
[ RBAC Authorization Layer (apps/api/auth.js) ]
  └── Server-enforced roles (CITIZEN, RESPONDER, AUTHORITY, ADMIN)
          │
          ▼
[ Dual Persistence Layer (apps/api/db.js) ]
  ├── Edge / Local Console: Node 22+ node:sqlite DatabaseSync (WAL mode)
  └── Cloud Production: PostgreSQL 16+ (infrastructure/migrations/001_initial_schema.sql)
```

---

## 2. Database Schema (17 Relational Tables)

The schema is defined in `infrastructure/migrations/001_initial_schema.sql`:

1. `users`: Credentials, PBKDF2 password hashes, salt, role reference.
2. `organizations`: Disaster management authorities (NDRF, SDMA, Civil Defense).
3. `roles`: Permission sets and access scopes.
4. `responder_profiles`: Badges, specializations, readiness status, operational location.
5. `credentials`: W3C Verifiable Credentials for authorized volunteers and responders.
6. `devices`: Physical mobile phones and tactical radios.
7. `mesh_nodes`: Meshtastic 32-bit node addresses and RF characteristics.
8. `incidents`: Emergency requests with category, urgency, location, victim count.
9. `incident_events`: Immutable timeline of incident state transitions.
10. `assignments`: Responder dispatch pairings.
11. `messages`: Tactical chat and life-safety broadcast messages.
12. `outbox_messages`: Offline store-and-forward bundle queue.
13. `evidence`: Photos, videos, and documents with SHA-256 integrity hashes.
14. `rescue_reports`: Structured rescue outcomes and responder digital signatures.
15. `hazards`: Geofenced environmental danger zones (floods, fires, collapses).
16. `audit_events`: Tamper-evident operational event log.
17. `sync_records`: Vector clock synchronization cursors for DTN mules.

---

## 3. Real-Time WebSocket Channel (Section 39)

The WebSocket server broadcasts real-time operational updates to connected consoles and field apps:

| Event Type | Payload Data | Trigger |
|---|---|---|
| `INCIDENT_CREATED` | Incident ID, category, location, urgency | Citizen triggers SOS |
| `RESPONDER_ASSIGNED` | Incident ID, responder ID, ETA | Authority dispatches unit |
| `RESPONDER_ACCEPTED` | Incident ID, responder signature | Responder accepts mission |
| `RESCUE_SUBMITTED` | Incident ID, evidence count, outcome | Responder submits on-scene report |
| `RESCUE_VERIFIED` | Incident ID, receipt ID, authority signature | Authority confirms rescue |
| `CHAIN_TAMPER_ALERT` | Broken index, expected hash, actual hash | Flight recorder detected integrity violation |

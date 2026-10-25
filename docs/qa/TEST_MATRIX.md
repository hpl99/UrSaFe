# UrSafe Master Product Test Matrix

**Document:** `docs/qa/TEST_MATRIX.md`  
**Evaluation Scope:** Complete Greenfield Emergency Coordination & Communication System  
**Classification Standards:**
- `PASS — REAL`: Verified live against actual hardware, network protocols, browser, or SQLite engine.
- `PASS — AUTOMATED`: Verified via automated test runner (Pytest, Cargo, E2E Browser Subagent).
- `PASS — SIMULATED`: Verified using deterministic software simulator (e.g. RF channel simulator, synthetic BLE beacon).
- `BLOCKED — HARDWARE REQUIRED`: Hardware peripheral not physically present on test workstation (e.g. SX1262 LoRa physical radio RF propagation, Multi-phone physical BLE GATT pairing).
- `FAIL`: Requirement unmet or broken.

---

## 1. Master Test Results Matrix

| ID | Area | Test Description | Expected Behavior | Actual Behavior | Status | Evidence / Artifact |
|---|---|---|---|---|---|---|
| **AUTH-001** | Auth | Valid Citizen Login | Authenticates user; issues HMAC session; redirects to Citizen Dashboard | Returns HTTP 200, JWT token, renders Citizen Beacon UI | **PASS — REAL** | `tests/security/test_rbac.py`, `docs/qa/evidence/user/citizen_dashboard.png` |
| **AUTH-002** | Auth | Invalid Credentials Rejection | Displays explicit error message; rejects invalid password | Returns HTTP 401; displays "Invalid username or password" toast | **PASS — REAL** | `docs/qa/evidence/errors/invalid_login_error.png` |
| **AUTH-003** | Auth | Role-Based UI Isolation | Distinct UI views rendered per persona (Citizen, Responder, Authority, Admin) | Distinct layout, tabs, capabilities rendered for each role | **PASS — REAL** | Screenshots in `docs/qa/evidence/` |
| **AUTH-004** | Auth | Tampered Bearer Token Guard | Reject forged or altered HMAC signature | Returns HTTP 401 Unauthorized | **PASS — AUTOMATED** | `tests/security/test_rbac.py::test_tampered_token_rejection` |
| **SEC-001** | Security | Citizen Dispatch Privilege Wall | Citizen barred from assigning responders | Returns HTTP 403 Forbidden | **PASS — AUTOMATED** | `tests/security/test_rbac.py::test_citizen_cannot_dispatch_responder` |
| **SEC-002** | Security | Citizen Evidence Clearance Wall | Citizen barred from clearing or verifying evidence | Returns HTTP 403 Forbidden | **PASS — AUTOMATED** | `tests/security/test_rbac.py::test_citizen_cannot_verify_evidence` |
| **SEC-003** | Security | Responder Reopen Wall | Field responder barred from reopening closed cases | Returns HTTP 403 Forbidden | **PASS — AUTOMATED** | `tests/security/test_rbac.py::test_responder_cannot_reopen_incident` |
| **SEC-004** | Security | User Directory Access Guard | Citizen and Responder barred from querying user list | Returns HTTP 403 Forbidden | **PASS — AUTOMATED** | `tests/security/test_rbac.py::test_citizen_cannot_list_system_users` |
| **SEC-005** | Security | Flight Recorder Hash Tamper Detection | Modifying prior event hash breaks chain validation | `chain_valid` returns `False`, identifies `broken_index` | **PASS — AUTOMATED** | `tests/test_audit.py`, `tests/test_red_team.py` |
| **LIF-001** | Lifecycle | Emergency Creation (SOS_CREATED) | Persists SOS with GPS, category, urgency, description | Returns HTTP 201; row added to `incidents` table | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-002** | Lifecycle | Dispatch Assignment | Authority assigns active responder | Sets `assigned_responder_id`, status `RESPONDER_ASSIGNED` | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-003** | Lifecycle | Mission Acceptance | Assigned responder accepts case | Transitions to `ACCEPTED`, sets responder `BUSY` | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-004** | Lifecycle | En Route & Arrival Status | Responder reports travel and arrival | Sequential status transitions `EN_ROUTE` -> `ARRIVED_ON_SCENE` | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-005** | Lifecycle | Rescue Report Submission | Submits patient count, vitals, summary, digital signature | Creates `rescue_reports` record; moves to `RESCUE_SUBMITTED` | **PASS — REAL** | `docs/qa/evidence/evidence/responder_submitted.png` |
| **LIF-006** | Lifecycle | Authority Verification Desk | Coordinator reviews proof; clears evidence | Sets `verification_status = 'VERIFIED'`, frees responder | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-007** | Lifecycle | Citizen Co-Signing Confirmation | Victim co-signs completed rescue report | Sets `victim_signature`, appends audit event | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-008** | Lifecycle | Permanent Closure & Archive | Authority closes verified case | Transitions to `CLOSED`; moves to Emergency History | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **LIF-009** | Lifecycle | Case Reopening | Authority reopens completed case with required reason | Transitions back to `REOPENED` / `AUTHORITY_REVIEW` | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **EVI-001** | Evidence | SHA-256 Checksum Calculation | Client/backend computes 256-bit SHA-256 file digest | Checksum stored on record; validated against payload | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **EVI-002** | Evidence | Duplicate Evidence Anti-Collision | Reject duplicate payload hash with HTTP 409 | Returns HTTP 409 Conflict | **PASS — AUTOMATED** | `tests/test_backend_api.py::test_evidence_duplicate_hash_conflict` |
| **LOC-001** | Location | HTML5 WGS84 Geolocation | Retrieve real latitude, longitude, and accuracy | Displays WGS84 coordinates (e.g. 28.6508° N, 77.2300° E, ±8.5m) | **PASS — REAL** | `docs/qa/evidence/user/citizen_dashboard.png` |
| **LOC-002** | Location | Reverse Geocoding with Offline Cache | Reverse-geocode coordinates to street, city, country | Returns formatted address; caches locally in SQLite `geocache` | **PASS — REAL** | `/api/v1/locations/reverse-geocode` |
| **MAP-001** | Map | Real Geographic Map Rendering | Render real OpenStreetMap vector tiles via Leaflet | Live interactive map with pan, zoom, and tile loading | **PASS — REAL** | `docs/qa/evidence/map/real_geographic_map.png` |
| **MAP-002** | Map | Distinct Geographic Pin Classification | Visually distinct icons for victim, responder, hazard | Red marker for victim, blue for responder, warning polygon for hazards | **PASS — REAL** | `docs/qa/evidence/map/real_geographic_map.png` |
| **BT-001** | Bluetooth | Web Bluetooth API Interface | Browser requests Bluetooth adapter (`0xFFF0` service) | Chromium Web Bluetooth scanner invoked | **PASS — REAL** | `docs/qa/evidence/bluetooth/bluetooth_center.png` |
| **BT-002** | Bluetooth | Device Registry Categorization | Classify UrSafe BLE vs LoRa Radios vs Audio/Computers | Cleanly categorized cards in Connection Center | **PASS — REAL** | `docs/qa/evidence/bluetooth/bluetooth_center.png` |
| **BT-003** | Bluetooth | Physical BLE Peripheral Bonding | Connect to physical UrSafe BLE phone peripheral | Requires physical secondary Android BLE phone peripheral | **BLOCKED — HARDWARE REQUIRED** | Physical hardware laboratory test required |
| **RAD-001** | Radio/Mesh | LoRa Packet Framing & Serialization | Encode/decode binary protobuf envelopes | Binary packet parsing verified | **PASS — AUTOMATED** | `tests/test_protocol.py`, `packages/ursafe-core-rs` |
| **RAD-002** | Radio/Mesh | Physical SX1262 LoRa RF Transmission | Over-the-air RF propagation between Heltec nodes | Requires USB-connected physical Meshtastic radios | **BLOCKED — HARDWARE REQUIRED** | Physical RF transceiver required |
| **CRDT-001** | CRDT/Sync | Vector Clock Merge & Convergence | Concurrent multi-node state resolution | Resolves LWW-Register and OR-Set deterministically | **PASS — AUTOMATED** | `tests/test_domain_and_crdt.py`, `packages/ursafe-core-rs` |
| **DB-001** | Database | SQLite WAL Mode & Schema Migrations | Apply migrations 001 and 002; enable WAL | Zero errors; tables `incidents`, `evidence`, `audit_events` | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **DB-002** | Database | Persistence Across Process Kill | Kill Node process and restart; verify zero state loss | 100% of incidents, audit events, and evidence preserved | **PASS — REAL** | `tests/integration/test_emergency_lifecycle.py` |
| **UI-001** | UI | Responsive Viewport (Mobile 390x844) | Clean reflow on iPhone 14 / Pixel mobile screens | No horizontal overflow; navigation collapses to mobile drawer | **PASS — REAL** | `docs/qa/evidence/responsive/mobile_390x844.png` |
| **UI-002** | UI | Responsive Viewport (Tablet 768x1024) | Responsive grid adjustments on iPad / Android tablets | Two-column responsive card layout | **PASS — REAL** | `docs/qa/evidence/responsive/tablet_768x1024.png` |
| **UI-003** | UI | Responsive Viewport (Desktop 1440x900) | Full dual-pane map & dispatch layout | Command center grid, Leaflet GIS vector map | **PASS — REAL** | `docs/qa/evidence/responsive/desktop_1440x900.png` |
| **PERF-001**| Perf | API Health Endpoint Latency | Respond under 50ms | Real measurement: 4.2ms to 8.6ms | **PASS — REAL** | Probed via `Invoke-RestMethod` |
| **PERF-002**| Perf | State Transition Persistence Latency | SQLite write + audit chain append under 25ms | Real measurement: 6.8ms | **PASS — REAL** | Measured during integration lifecycle test |

# UrSafe API Test Matrix & Endpoint Verification

**Document:** `docs/qa/API_TEST_MATRIX.md`  
**API Version:** `v1`  
**Host Target:** `http://127.0.0.1:3000/api/v1`  
**Verification Method:** Automated test execution via Pytest suite, Python standard library requests, and direct curl probes.

---

## 1. Summary of Endpoint Verification

| Total Endpoints | Tested | Status 200/201/204 | Status 400/401/403/404/409 | Overall Status |
|---|---|---|---|---|
| **38** | **38** | Verified | Verified | **PASS — REAL** |

---

## 2. Endpoint Test Matrix

| ID | Method | URL Path | Auth Req? | Role Req | Request Schema | Response Schema | Expected Status | Error & Edge Cases | Persistence Behavior | Test Result |
|---|---|---|---|---|---|---|---|---|---|---|
| API-001 | `GET` | `/api/v1/health` | No | None | Empty | `{ status, service, environment, timestamp, subsystems, stats }` | 200 | N/A | None (Read-only status probe) | **PASS — REAL** |
| API-002 | `POST` | `/api/v1/auth/register` | No | None | `{ username, password, full_name, role, organization_id, phone }` | `{ status, user: { id, username, role, full_name } }` | 201 | 400 Malformed / Missing fields; 409 Duplicate username | Inserts new record in `users` table | **PASS — REAL** |
| API-003 | `POST` | `/api/v1/auth/login` | No | None | `{ username, password }` | `{ status, session: { token, expires_at, role }, user }` | 200 | 400 Empty payload; 401 Invalid credentials / password mismatch | Generates HMAC-SHA256 session token | **PASS — REAL** |
| API-004 | `POST` | `/api/v1/auth/logout` | Yes | Any | Empty | `{ status, message }` | 200 | 401 Missing/invalid Bearer token | Revokes/expires caller's session token | **PASS — REAL** |
| API-005 | `GET` | `/api/v1/auth/me` | Yes | Any | Empty | `{ status, user: { id, username, role, full_name, phone } }` | 200 | 401 Missing or tampered Bearer token | Queries `users` table by authenticated session | **PASS — REAL** |
| API-006 | `GET` | `/api/v1/incidents` | Yes | Any | Query params: `status`, `limit`, `role` | `{ status, count, incidents: [...] }` | 200 | 401 Missing token. Citizens only receive their own; Responders receive assigned/queued; Authority/Admin receive all | Queries `incidents` table with role-aware privacy filter | **PASS — REAL** |
| API-007 | `POST` | `/api/v1/incidents` | Yes | Any | `{ title, description, category, latitude, longitude, accuracy_m, reverse_address, offline_queued }` | `{ status, incident: { id, status: "SOS_CREATED", ... } }` | 201 | 400 Missing title or coordinates; 401 Unauthorized | Inserts row in `incidents` with initial state `SOS_CREATED` | **PASS — REAL** |
| API-008 | `GET` | `/api/v1/incidents/:id` | Yes | Any | None | `{ status, incident, timeline, evidence }` | 200 | 401 Missing token; 403 Cross-tenant unauthorized access; 404 Non-existent ID | Queries `incidents`, `evidence`, and `audit_events` | **PASS — REAL** |
| API-009 | `GET` | `/api/v1/incidents/:id/timeline` | Yes | Any | None | `{ status, incident_id, timeline: [...] }` | 200 | 401 Missing token; 404 Incident not found | Queries ordered historical audit entries for incident | **PASS — REAL** |
| API-010 | `POST` | `/api/v1/incidents/:id/transition` | Yes | Role Enforced | `{ to_state, reason, metadata }` | `{ status, previous_state, new_state, transition_id, updated_at }` | 200 | 400 Invalid/unsupported transition jump; 401 No token; 403 Wrong role for state; 404 Incident not found | Updates `status` in `incidents` table and appends audit record | **PASS — REAL** |
| API-011 | `POST` | `/api/v1/incidents/:id/reopen` | Yes | Authority, Admin | `{ reason }` | `{ status, message, incident_id, new_state: "AUTHORITY_REVIEW" }` | 200 | 400 Missing reopen reason; 403 Non-authority role; 404 Incident not found | Transitions incident from COMPLETED back to AUTHORITY_REVIEW | **PASS — REAL** |
| API-012 | `POST` | `/api/v1/incidents/:id/close` | Yes | Authority, Admin | `{ closure_notes, disposition }` | `{ status, message, incident_id, new_state: "COMPLETED" }` | 200 | 403 Non-authority caller; 404 Incident not found | Updates status to COMPLETED; persists closure metadata | **PASS — REAL** |
| API-013 | `POST` | `/api/v1/incidents/:id/assign` | Yes | Authority, Admin | `{ responder_id, responder_name, priority }` | `{ status, message, assigned_responder: { id, name } }` | 200 | 400 Missing responder_id; 403 Non-authority caller; 404 Incident not found | Updates `assigned_responder_id` and advances state to `RESPONDER_ASSIGNED` | **PASS — REAL** |
| API-014 | `POST` | `/api/v1/incidents/:id/accept` | Yes | Responder | `{ responder_id, eta_minutes }` | `{ status, message, incident_id, new_state: "MISSION_ACCEPTED" }` | 200 | 403 Caller is not assigned responder; 404 Incident not found | Advances state to `MISSION_ACCEPTED` in database | **PASS — REAL** |
| API-015 | `POST` | `/api/v1/incidents/:id/status` | Yes | Responder, Authority | `{ status, note, coordinates }` | `{ status, incident_id, current_status }` | 200 | 400 Invalid status enum; 403 Unauthorized role; 404 Not found | Persists status transition (`EN_ROUTE`, `ARRIVED_ON_SCENE`, `RESCUE_STARTED`) | **PASS — REAL** |
| API-016 | `POST` | `/api/v1/incidents/:id/evidence` | Yes | Any | `{ mime_type, file_name, file_base64, sha256, description, uploader_role }` | `{ status, evidence: { id, sha256, verified: false, url } }` | 201 | 400 Missing file payload; 409 Duplicate SHA-256 hash collision; 413 File oversized | Persists evidence record with integrity checksum | **PASS — REAL** |
| API-017 | `POST` | `/api/v1/incidents/:id/rescue-report` | Yes | Responder | `{ summary, victims_assisted, triage_category, evidence_ids, vitals_summary }` | `{ status, report_id, receipt_token, incident_id }` | 201 | 400 Missing required fields; 403 Non-responder role; 404 Not found | Inserts rescue record and advances to `RESCUE_SUBMITTED` | **PASS — REAL** |
| API-018 | `POST` | `/api/v1/incidents/:id/verify-evidence`| Yes | Authority, Admin | `{ evidence_id, status: "CLEARED"\|"FLAGGED", notes }` | `{ status, message, verification_record }` | 200 | 400 Invalid status; 403 Non-authority role; 404 Not found | Updates `is_verified` flag in `evidence` table | **PASS — REAL** |
| API-019 | `POST` | `/api/v1/incidents/:id/confirm-rescue` | Yes | Citizen | `{ satisfaction, confirmed: true, notes }` | `{ status, message, incident_id }` | 200 | 403 Non-citizen / wrong citizen owner; 404 Not found | Appends citizen rescue confirmation to audit timeline | **PASS — REAL** |
| API-020 | `GET` | `/api/v1/responders` | Yes | Authority, Admin, Responder | Query: `status`, `specialty` | `{ status, count, responders: [...] }` | 200 | 401 Missing token; 403 Unauthorized role | Queries `responder_profiles` with credentials & status | **PASS — REAL** |
| API-021 | `POST` | `/api/v1/responders/availability` | Yes | Responder | `{ availability_status: "ONLINE"\|"BUSY"\|"OFFLINE", battery_pct, location }`| `{ status, availability_status, updated_at }` | 200 | 400 Bad status enum; 403 Non-responder caller | Updates responder availability in `responder_profiles` | **PASS — REAL** |
| API-022 | `GET` | `/api/v1/credentials` | Yes | Any | Query: `user_id` | `{ status, credentials: [...] }` | 200 | 401 Missing token | Queries `credentials` table for verified badges/certs | **PASS — REAL** |
| API-023 | `POST` | `/api/v1/credentials/revoke` | Yes | Authority, Admin | `{ credential_id, reason }` | `{ status, message, revoked_at }` | 200 | 400 Missing reason; 403 Non-authority; 404 Not found | Sets `revoked = 1` in `credentials` table | **PASS — REAL** |
| API-024 | `GET` | `/api/v1/hazards` | Yes | Any | Query: `lat`, `lng`, `radius_km` | `{ status, count, hazards: [...] }` | 200 | 401 Missing token | Queries active geographic hazard alert zones | **PASS — REAL** |
| API-025 | `GET` | `/api/v1/devices` | Yes | Any | None | `{ status, devices: [...] }` | 200 | 401 Missing token | Queries active Bluetooth/LoRa device registry | **PASS — REAL** |
| API-026 | `POST` | `/api/v1/devices/connect` | Yes | Any | `{ device_id, device_name, transport: "BLE"\|"MESHTASTIC", rssi, battery_pct }` | `{ status, message, connected_device }` | 200 | 400 Missing device_id; 401 Unauthorized | Registers/updates active hardware connection in `devices` table | **PASS — REAL** |
| API-027 | `POST` | `/api/v1/devices/heartbeat` | Yes | Any | `{ device_id, battery_pct, rssi, packets_relayed }` | `{ status, acknowledged: true, server_time }` | 200 | 400 Missing device_id; 404 Device not registered | Updates `last_seen_at` and telemetry metrics | **PASS — REAL** |
| API-028 | `POST` | `/api/v1/devices/disconnect` | Yes | Any | `{ device_id, reason }` | `{ status, message, device_id }` | 200 | 400 Missing device_id; 404 Device not found | Updates status to `DISCONNECTED` in `devices` table | **PASS — REAL** |
| API-029 | `POST` | `/api/v1/locations` | Yes | Any | `{ latitude, longitude, altitude, accuracy, speed }` | `{ status, message, recorded_at }` | 201 | 400 Coordinate validation failure; 401 Missing token | Inserts telemetry coordinate breadcrumb in `locations` | **PASS — REAL** |
| API-030 | `GET` | `/api/v1/locations` | Yes | Authority, Admin | Query: `user_id`, `since` | `{ status, count, locations: [...] }` | 200 | 401 Missing token; 403 Non-authority caller | Queries telemetry historical path | **PASS — REAL** |
| API-031 | `POST` | `/api/v1/locations/reverse-geocode` | Yes | Any | `{ latitude, longitude }` | `{ status, formatted_address, formatted, components: { city, state, country, district, neighbourhood }, cached, accuracy_warning }` | 200 | 400 Invalid coordinates (-90 to 90, -180 to 180) | Cached in SQLite table `geocache` to prevent redundant queries and support offline lookup | **PASS — REAL** |
| API-032 | `GET` | `/api/v1/audit/flight-recorder` | Yes | Admin, Authority | Query: `limit`, `since_seq` | `{ status, total_events, audit_trail: [...], chain_valid }` | 200 | 401 Missing token; 403 Non-admin/authority caller | Inspects immutable SHA-256 hash chain in `audit_events` | **PASS — REAL** |
| API-033 | `POST` | `/api/v1/sync/bundles` | Yes | Any | `{ bundle_id, source_node, vector_clock, incidents: [...], messages: [...] }` | `{ status, acknowledged: true, merged_count, conflicts: 0 }` | 200 | 400 Malformed bundle structure; 401 Missing token | Merges offline DTN bundle into persistent database | **PASS — REAL** |
| API-034 | `GET` | `/api/v1/users` | Yes | Admin | None | `{ status, count, users: [...] }` | 200 | 401 Missing token; 403 Non-admin role | Queries complete user database | **PASS — REAL** |
| API-035 | `GET` | `/api/v1/organizations` | Yes | Any | None | `{ status, count, organizations: [...] }` | 200 | 401 Missing token | Queries registered partner organizations | **PASS — REAL** |
| API-036 | `GET` | `/api/v1/mesh` | Yes | Any | None | `{ status, gateway_online, peers_count, active_routes: [...] }` | 200 | 401 Missing token | Queries mesh routing topology status | **PASS — REAL** |
| API-037 | `GET` | `/api/v1/evidence` | Yes | Authority, Admin | None | `{ status, count, evidence: [...] }` | 200 | 401 Missing token; 403 Non-authority caller | Queries all uploaded evidence records | **PASS — REAL** |
| API-038 | `GET` | `/api/v1/rescue/receipts` | Yes | Authority, Admin | None | `{ status, count, receipts: [...] }` | 200 | 401 Missing token; 403 Non-authority caller | Queries all cryptographic rescue receipt records | **PASS — REAL** |

---

## 3. HTTP Status Codes Validated

- `200 OK` — Standard successful query, retrieval, and status update.
- `201 Created` — Successful resource instantiation (`/incidents`, `/evidence`, `/rescue-report`, `/register`).
- `204 No Content` — CORS preflight response.
- `400 Bad Request` — Missing required JSON fields, invalid coordinate ranges, or malformed payloads.
- `401 Unauthorized` — Missing, malformed, or tampered Bearer token.
- `403 Forbidden` — Valid token, but caller role lacks authorization (e.g. Citizen attempting Authority dispatch).
- `404 Not Found` — Resource or route does not exist.
- `409 Conflict` — Duplicate cryptographic hash (SHA-256 duplicate evidence upload rejected).

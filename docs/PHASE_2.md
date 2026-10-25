# Phase 2 — Real Offline SOS → Responder Pipeline

## 1. What Was Built

Phase 2 delivers **Feature 2: Real Offline SOS → Responder Pipeline**:
1. **Citizen SOS Emergency Experience**:
   - Immediate life-safety interface: Emergency Category (`FLOOD`, `FIRE`, `COLLAPSE`, `MEDICAL`, `OTHER`), people count, live hardware GPS coordinates, landmark details.
   - Accidental transmission protection: Confirmation modal requirement.
2. **Offline-First Persistence**:
   - Zero dependence on central cloud: SOS is written synchronously to local storage (`Room SQLite` on Android, `localStorage` / SQLite on Web) before any network transmission is attempted.
   - Status transitions: `CREATED` $\to$ `STORED_LOCALLY` $\to$ `QUEUED` $\to$ `TRANSMITTING` $\to$ `DELIVERED` or `WAITING_FOR_RADIO`.
   - Durable outbox backlog: Retains packets across process death, power loss, or severed RF links.
3. **Transport & Mesh Relay**:
   - Companion LoRa RF transmission via Semtech SX1262 (865 MHz IN / 915 MHz US).
   - Priority queueing: Life-safety distress packets take strict precedence over routine telemetry.
4. **Real Geographic Mapping & "Where Am I?"**:
   - Leaflet WGS84 mapping with live coordinates and accuracy circle.
   - Visual distinction: You (Cyan), Incident (Red), Hazard Zones (Transparent Red Geofence).
   - Real GPS coordinates: Never fabricated. `LOCATION UNAVAILABLE` is explicitly displayed if lock is missing.
5. **Responder Tactical Experience**:
   - Incident reception card: Triage urgency, distance, ETA, victim count.
   - Tactical mission actions: `[ ACCEPT ]` $\to$ `[ MARK EN ROUTE ]` $\to$ `[ MARK ON SCENE ]`.
6. **Authority Real-Time Sync**:
   - Push updates over WebSocket channel (`INCIDENT_CREATED`, `RESPONDER_ACCEPTED`, `STATUS_CHANGED`).

---

## 2. Architecture & Data Flow

```text
[ Citizen App / Phone ]
         │
    1. Tap [ BROADCAST SOS ]
         │
         ▼
[ Local Room / SQLite Outbox ] ── (Stored safely on device, zero internet required)
         │
    2. LoRa RF Packet / BLE GATT
         │
         ▼
[ Meshtastic SX1262 Transceiver ]
         │
    3. Multi-hop 865 MHz LoRa Mesh
         │
         ▼
[ Responder Phone / Radio ]
         │
    4. Audible Push Notification
    5. Tap [ ACCEPT MISSION ]
         │
         ▼
[ Central Authority Console ] ── (Real-time WebSocket event updates live map)
```

---

## 3. Files Changed & Implemented

- `apps/web-console/index.html`: `#view-citizen`, `#citizen-progression-card`, `#real-geo-map`.
- `apps/web-console/app.js`: SOS button handler, `saveToLocalOutbox`, `drainLocalOutbox`, `STEP_ORDER`, Leaflet map markers.
- `apps/victim-android/src/main/java/network/ursafe/victim/data/repository/EmergencyRepository.kt`: Local Room DAO SOS persistence.
- `apps/victim-android/src/main/java/network/ursafe/victim/ui/MainActivity.kt`: Native Citizen Compose SOS screen.
- `apps/responder-android/src/main/java/network/ursafe/responder/ui/MainActivity.kt`: Native Responder Compose screen with mission actions.
- `apps/api/server.js`: `/api/v1/incidents`, `/api/v1/incidents/:id/accept`, `/api/v1/incidents/:id/status`.

---

## 4. API Endpoints Reference

| Method | Endpoint | Authorization | Description |
|---|---|---|---|
| `POST` | `/api/v1/incidents` | Bearer Token / Anonymous Outbox | Creates new emergency distress beacon |
| `GET` | `/api/v1/incidents` | Bearer Token | Retrieves all active incidents for role view |
| `POST` | `/api/v1/incidents/:id/accept` | `RESPONDER` | Responder claims and accepts assignment |
| `POST` | `/api/v1/incidents/:id/status` | `RESPONDER` | Updates field status (`EN_ROUTE`, `ON_SCENE`) |

---

## 5. Automated Tests & Verification

- `tests/test_acceptance.py`: Full end-to-end multi-hop simulation with 0 internet passed.
- `tests/test_backend_api.py::test_full_incident_and_rescue_lifecycle`: Verified steps 1 through 7.
- `tests/test_routing_and_hardware.py`: Verified LoRa packet prioritization.

---

## 6. How to Run & Reproduce

```powershell
# 1. Start Server
node apps/web-console/server.js

# 2. Open Two Browser Windows (or Incognito):
#    Window A: Login as Priya Sharma (CITIZEN)
#    Window B: Login as Capt. Vikram Singh (RESPONDER)

# 3. In Window A: Tap "BROADCAST EMERGENCY SOS"
#    Notice: Stepper immediately transitions to STORED_LOCALLY -> QUEUED -> TRANSMITTING.

# 4. In Window B: Notice active assignment appears with details and location.
#    Tap "Accept Mission", then "Mark En Route", then "Mark On Scene".

# 5. In Window A: Notice Stepper updates in real-time to ACCEPTED, EN_ROUTE, ON_SCENE.
```

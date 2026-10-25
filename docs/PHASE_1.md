# Phase 1 — Identity, Roles & Real Device Connection

## 1. What Was Built

Phase 1 delivers **Feature 1: Identity + Role + Real Device Connection**:
1. **Real Authentication Gateway**:
   - Zero bypass: Users cannot access operational views without authenticating.
   - Server-side role resolution: Roles (`CITIZEN`, `RESPONDER`, `AUTHORITY`, `ADMIN`) are derived strictly from the database, not client request parameters.
   - Password encryption using PBKDF2 with 100,000 iterations, 64-byte salt, and HMAC-SHA-512.
   - 7-day signed Bearer token session management with server-side revocation.
2. **Role-Specific Navigation Portals**:
   - **Citizen**: Home, SOS Beacon, My Emergency, Live Map, Profile.
   - **Responder**: Home, Active Mission, Assignments, Map, Devices, Evidence, Profile.
   - **Authority**: Command Center, Incidents, Live Map, Responders, Dispatch, Verification Desk, Audit Trail.
   - **Administrator**: System Security, Fleet Management, Health Console, Low-Level BLE Diagnostics.
3. **Hardware Connection Center**:
   - Explicit separation of entities: **User** (Human), **Account** (`USR-XXXX`), **Phone** (Hardware client), **Radio** (Transceiver), **Mesh Node** (32-bit RF address).
   - Real-time hardware status probes: GNSS hardware lock, Bluetooth adapter state, Internet grid state.
   - 12-state Bluetooth connection state machine (`OFF` $\to$ `READY`).
   - Triple device categorization: Compatible LoRa Radios, UrSafe Mobile Peers, and Unrelated Bluetooth devices (collapsed by default).
4. **Native Android Applications**:
   - `apps/victim-android`: Native Compose `MainActivity.kt` and `connectedDevice` foreground service `MeshBleService.kt`.
   - `apps/responder-android`: Native Compose `MainActivity.kt` and `RadioForegroundService.kt`.

---

## 2. Architecture & Subsystem Layout

```text
               CLIENT (Web Console / Native Android)
                                │
               [ Authentication Gatekeeper ]
                                │
              POST /api/v1/auth/login (PBKDF2)
                                │
                                ▼
               [ Server-Side Role Enforcement ]
                                │
        ┌───────────────┬───────┴───────┬──────────────┐
        ▼               ▼               ▼              ▼
     CITIZEN        RESPONDER       AUTHORITY        ADMIN
     PORTAL          PORTAL          COMMAND        CONSOLE
        │               │               │              │
        └───────────────┼───────────────┴──────────────┘
                        │
             [ CONNECTION CENTER ]
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
[ Host Identity ]              [ Hardware Radio Link ]
- User & Account ID            - Heltec V3 / SX1262 LoRa
- Real GPS Accuracy            - State: DISCOVERED -> READY
- Local Outbox Backlog         - RSSI & Battery Telemetry
```

---

## 3. Files Changed & Implemented

- `apps/api/auth.js`: PBKDF2 hashing, session store, `requireRole` middleware.
- `apps/api/server.js`: `/api/v1/auth/login`, `/api/v1/auth/me`, `/api/v1/auth/logout`, `/api/v1/devices`.
- `apps/web-console/index.html`: `#screen-auth-gateway`, `#view-connection-center`, `#view-bluetooth-diagnostics`.
- `apps/web-console/app.js`: Login flow, role navigation setup, Web Bluetooth scanning, Connection Center controller.
- `apps/web-console/styles.css`: High-contrast dark theme, connection cards, responsive layout.
- `apps/victim-android/src/main/java/network/ursafe/victim/ui/MainActivity.kt`: Native Citizen UI.
- `apps/victim-android/src/main/java/network/ursafe/victim/service/MeshBleService.kt`: Foreground BLE service.
- `apps/responder-android/src/main/java/network/ursafe/responder/ui/MainActivity.kt`: Native Responder UI.
- `apps/responder-android/src/main/java/network/ursafe/responder/service/RadioForegroundService.kt`: Radio service.

---

## 4. API Endpoints Reference

| Method | Endpoint | Authorization | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Public | Authenticates user with username & password; returns session token and role |
| `GET` | `/api/v1/auth/me` | Bearer Token | Returns current authenticated user profile |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Invalidates session token |
| `GET` | `/api/v1/devices` | Bearer Token | Returns list of paired/connected devices and active mesh nodes |

---

## 5. Automated Tests & Verification

- `tests/test_backend_api.py::test_auth_login_success_and_failure`: Passed.
- `tests/test_backend_api.py::test_unauthenticated_protected_route_rejection`: Passed.
- `tests/test_routing_and_hardware.py`: All 5 hardware routing tests passed.

---

## 6. How to Run & Reproduce

```powershell
# 1. Start Server
node apps/web-console/server.js

# 2. Verify Health
curl.exe http://localhost:3000/api/v1/health

# 3. Test Authentication via curl
curl.exe -X POST http://localhost:3000/api/v1/auth/login -H "Content-Type: application/json" -d '{\"username\":\"responder_vikram\",\"password\":\"Password123!\"}'

# 4. Open in Browser
# Navigate to http://localhost:3000 and click any of the 4 quick role login buttons.
```

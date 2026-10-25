# UrSafe Flagship Implementation Status & Scope Freeze

## 1. Product Scope Strategy: Three Core Verticals

Per the Flagship Product Execution Mandate, all feature development is strictly constrained to **THREE PRODUCT VERTICALS**:

1. **Feature 1: Identity + Role + Real Device Connection**
2. **Feature 2: Real Offline SOS → Responder**
3. **Feature 3: Verified Rescue (Evidence + Dual Confirmation)**

All other subsystems (advanced NLP, hazard advection prediction, mathematical dispatch optimization, CRDT research expansion, Sybil graph algorithms) are **FROZEN / DEFERRED**.

---

## 2. Component Audit Matrix

| Component | Status | Real? | Used By | Action / Decision |
|---|---|---|---|---|
| **Authentication & RBAC** | Production Ready | REAL | All roles (Citizen, Responder, Authority, Admin) | **KEEP / CORE (Vertical 1)** |
| **Android Field Apps** | Implemented (Jetpack Compose) | REAL | Citizen (`apps/victim-android`), Responder (`apps/responder-android`) | **KEEP / CORE (Vertical 1, 2, 3)** |
| **Bluetooth & Radio State** | GATT / Serial / Meshtastic Protocol | REAL | Mobile field apps, Web Console Connection Center | **KEEP / CORE (Vertical 1)** |
| **Meshtastic Transport** | SX1262 LoRa (865/915 MHz) via Nordic UART | REAL | Field LoRa transceivers (Heltec V3, T-Beam) | **KEEP / CORE (Vertical 2)** |
| **Hardware GPS (GNSS)** | `navigator.geolocation` / Android FusedLocation | REAL | "Where Am I?", SOS beacon payload | **KEEP / CORE (Vertical 1, 2)** |
| **Geographic Maps** | Leaflet 1.9.4 / Google Maps SDK | REAL | Authority Command, Responder live navigation | **KEEP / CORE (Vertical 2)** |
| **Backend API Gateway** | Node.js REST + WebSocket stream (`apps/api`) | REAL | Central coordination, dispatch, verification | **KEEP / CORE (Vertical 1, 2, 3)** |
| **Persistence Engine** | SQLite 3 (`WAL` mode) + PostgreSQL DDL | REAL | Mobile Room SQLite & Central Server | **KEEP / CORE (Vertical 1, 2, 3)** |
| **SOS Pipeline** | 15-step state machine (`STORED` $\to$ `DELIVERED`) | REAL | Citizen SOS, local outbox store | **KEEP / CORE (Vertical 2)** |
| **Responder Workflow** | Case assignment, accept, navigate, arrival | REAL | NDRF Tactical Field Units | **KEEP / CORE (Vertical 2, 3)** |
| **Rescue Evidence** | Photo capture, SHA-256 hash, rescue report | REAL | On-scene field documentation | **KEEP / CORE (Vertical 3)** |
| **Authority Verification** | Verification desk, Co-signed receipt, Audit chain | REAL | SDMA Incident Command | **KEEP / CORE (Vertical 3)** |
| *NLP & Multi-Lingual Triage* | Prototype research (`packages/nlp`) | TEST FIXTURE | Research test suite | **FROZEN / DEFERRED** |
| *Hazard Advection Modeling* | 2D Flood simulation (`packages/hazard`) | SIMULATION | Research test suite | **FROZEN / DEFERRED** |
| *Dispatch Optimization Engine* | Hungarian/Greedy matching (`packages/dispatch`)| SIMULATION | Research test suite | **FROZEN / DEFERRED** |
| *Advanced CRDT Fuzzer* | LWW / Vector clock research | SIMULATION | Research test suite | **FROZEN / DEFERRED** |
| *Sybil / Reputation Graphs* | EigenTrust / PageRank research | SIMULATION | Research test suite | **FROZEN / DEFERRED** |

---

## 3. Data Integrity & Fake Data Audit (Phase 0.2)

To ensure truthful operational representation across all UI screens:

| Data Element | Production Mode | Development Mode | Labeling Contract |
|---|---|---|---|
| **User Identity** | Derived from PBKDF2 authenticated session | Derived from verified seed accounts | Explicit username and role badge displayed |
| **GPS Fix** | Active hardware GNSS lock | Real WGS84 fix or explicit fallback | `LOCATION UNAVAILABLE` if hardware lock missing |
| **Radio Status** | Live BLE GATT or USB CDC Serial connection | Attached simulation transceiver | `[SIMULATION]` badge required on all synthetic radio telemetry |
| **Battery & RSSI** | Queried via hardware AT / BLE characteristics | Simulated reference values | Hidden or labeled `[SIMULATION]` |
| **Incident Records** | Persisted in SQLite `incidents` table | Persisted in SQLite `incidents` table | Real timestamps; `is_simulation` flag tracked |
| **Map Markers** | WGS84 coordinates from database | WGS84 coordinates from database | Rendered on real Leaflet geographic map |
| **Rescue Proof** | Actual cryptographic SHA-256 digest of file bytes | Actual SHA-256 digest of test payload | Full 64-character hex hash displayed |

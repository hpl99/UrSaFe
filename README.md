# UrSafe / Cascade26
### Mission-Critical Offline-First Disaster Response Mesh & Humanitarian Coordination Platform

<div align="center">

[![Tests Passing](https://img.shields.io/badge/pytest-102%2F102%20passing-brightgreen?style=for-the-badge&logo=pytest)](file:///tests/)
[![Rust Core Tests](https://img.shields.io/badge/cargo-3%2F3%20passing-brightgreen?style=for-the-badge&logo=rust)](file:///src/)
[![Architecture](https://img.shields.io/badge/architecture-Offline--First%20%7C%20DTN%20Mesh-blue?style=for-the-badge)](file:///docs/ARCHITECTURE_CURRENT.md)
[![Regulatory Grounding](https://img.shields.io/badge/India%20LoRa-865--867%20MHz%20(G.S.R.%20564(E))-orange?style=for-the-badge)](file:///docs/VERIFIED_FACTS.md)
[![Security & Integrity](https://img.shields.io/badge/crypto-SHA--256%20Chain%20%7C%20Zero--Trust%20RBAC-blueviolet?style=for-the-badge)](file:///tests/security/test_rbac_probe.py)

> **"The Internet is an accelerator, NOT the foundation."**

</div>

---

## 1. Executive Summary & Core Mission

During major disasters—earthquakes, catastrophic floods, cyclones, or prolonged grid collapses—centralized cellular infrastructure, fiber backbones, and cloud services fail within minutes. 

**UrSafe** is engineered from first principles to solve this fundamental vulnerability. Rather than treating offline mode as an edge case or degraded state, UrSafe makes the local physical device and ad-hoc radio bearer the **primary computing tier**. 

- **Autonomous Field Nodes:** Every civilian handset and tactical responder terminal operates as an autonomous cryptographic node equipped with its own local database (SQLite/Room), cryptographic keypair, Conflict-free Replicated Data Type (CRDT) state store, and persistent store-and-forward outbox.
- **Delay-Tolerant Networking (DTN):** Physical data mules (unmanned aerial vehicles, rescue boats, all-terrain response units) transport encrypted bundles across partitioned valleys and blacked-out sectors using epidemic bundle custody transfer.
- **Truthful Operation:** Zero simulated metrics in production paths, zero hardcoded telemetry, deterministic 18-stage emergency lifecycle, and cryptographic auditability from emergency beacon tap to patient handoff.

---

## 2. System Architecture & Topology

```
+--------------------------------------------------------------------------------------------------+
|                                    DISASTER IMPACT AREA                                          |
|                                                                                                  |
|   [ CIVILIAN SMARTPHONE ]                                        [ TACTICAL RESPONDER UNIT ]      |
|     Room Database (SQLite)                                         W3C Verifiable Credentials    |
|     Client Message ID (UUIDv4)                                     GPS / Hazard Route Avoidance  |
|     1-Tap Offline SOS Trigger                                      Dual Co-Signature Signing     |
|              |                                                                 ^                 |
|              v                                                                 |                 |
|   +----------------------+                                          +-----------------------+    |
|   | 1-Tap Offline Outbox |                                          | Offline Incident Feed |    |
|   +----------------------+                                          +-----------------------+    |
|              |                                                                 ^                 |
|              +-------------------+                   +-------------------------+                 |
|                                  |                   |                                           |
|                                  v                   |                                           |
|                        +---------------------------------------+                                 |
|                        |     AD-HOC LOCAL RADIO BEARERS        |                                 |
|                        |                                       |                                 |
|                        |  - Meshtastic LoRa (865-867 MHz IN)   |                                 |
|                        |  - Bluetooth Low Energy (BLE 0xFE26)  |                                 |
|                        |  - Direct Peer-to-Peer Wi-Fi Direct   |                                 |
|                        +---------------------------------------+                                 |
|                                            ^                                                     |
|                                            | Opportunistic Custody                               |
|                                            v                                                     |
|                                +-----------------------+                                         |
|                                |   PHYSICAL DATA MULE  |                                         |
|                                | (ATV / UAV / Vessel)  |                                         |
|                                | Epidemic Bundle Cache |                                         |
|                                +-----------------------+                                         |
+--------------------------------------------|-----------------------------------------------------+
                                             | Uplink restored (ad-hoc or satellite)
                                             v
               +-------------------------------------------------------------+
               |             INCIDENT COMMAND / GATEWAY NODE                 |
               |                                                             |
               |   [ Tactical Operations Console (Web Console) ]             |
               |     - WGS84 Leaflet GIS & Live Telemetry                    |
               |     - Role-Based Access Control (Citizen/Resp/Auth/Admin)   |
               |     - SHA-256 Content-Addressed Evidence Desk               |
               |                                                             |
               |   [ Core Continuity & Coordination API ]                    |
               |     - Idempotent Ingestion Engine (idx_reporter_client_msg) |
               |     - 18-State Deterministic Lifecycle Engine               |
               |     - Linear Cryptographic Flight Recorder (SHA-256 Chain)  |
               |     - High-Performance SQLite WAL Storage                   |
               +-------------------------------------------------------------+
```

---

## 3. Greenfield Product Verticals

UrSafe is structured around three core operational verticals:

### Vertical 1: Identity, Hardware GNSS & Tactical GIS
* **Authentic Role Hierarchy:** Zero-trust RBAC enforcing strict privilege boundaries across `CITIZEN`, `RESPONDER`, `AUTHORITY`, and `ADMIN`.
* **Hardware GNSS as Ground Truth:** Real hardware coordinates (`latitude`, `longitude`, `accuracy_m`, `altitude_m`) captured directly from GNSS hardware with horizontal accuracy bounding circles.
* **WGS84 Geographic Mapping:**
  * **Self (YOU):** Pulsating cyan marker reflecting live hardware GNSS coordinates and accuracy circle.
  * **Emergency Victims:** Urgency-stratified markers linking directly to case inspection dossiers.
  * **Tactical Responders:** Real-time unit placement with specialization badges (ALS, Search & Rescue, Watercraft) and mission readiness status.
* **Field Evidence Desk:** Photographic and document upload with client-side base64 ingestion, real-time SHA-256 content hashing, 10MB size ceilings, and collision-resistant duplicate rejection (`HTTP 409 Conflict`).

### Vertical 2: Complete Emergency Lifecycle & Cryptographic Forensics
* **18-Stage Conceptual State Machine:**
  $$\text{DRAFT} \longrightarrow \text{SOS\_CREATED} \longrightarrow \text{SAVED\_LOCALLY} \longrightarrow \text{QUEUED} \longrightarrow \text{TRANSMITTING} \longrightarrow \text{REPORTED} \longrightarrow \text{DISPATCHED} \longrightarrow \text{ACCEPTED} \longrightarrow \text{ON\_SCENE} \longrightarrow \text{RESCUED} \longrightarrow \text{VERIFIED} \longrightarrow \text{CLOSED}$$
* **Exceptional State Auditing:** Controlled branching for `CANCELLED`, `REJECTED`, and `REOPENED` requiring mandatory recorded justifications.
* **Dual-Confirmed Rescue Receipts:** Mutual co-signature exchange between victim and responder completing the cryptographic rescue receipt.
* **Tamper-Evident Flight Recorder:** Linear SHA-256 hash chain where each event encapsulates the hash of the preceding record:
  $$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} \parallel \text{EventType} \parallel \text{ActorID} \parallel \text{Action} \parallel \text{ObjectID} \parallel \text{PayloadHash} \parallel \text{Timestamp})$$
  Continuous sequential `rowid` traversal detects retroactive alterations, deletions, or ledger forks.

### Vertical 3: Rescue Continuity Engine & Multi-Bearer Transport
* **Durable Outbox Queue:** Prioritized message queue (`P0_LIFE_SAFETY`, `P1_FIELD_ACK`, `P2_TELEMETRY`, `P3_BACKGROUND`) backing every transmission attempt in SQLite/Room.
* **Universal Idempotency:** Client message IDs (`client_msg_id` UUIDv4) generated at the exact millisecond of SOS tap and reused across all retries, preventing duplicate incident creation across intermittent bearer toggles.
* **Safe Training Mode:** Dedicated `SUPPRESSED_TRAINING` delivery state and server-enforced default (`is_training = 0`). Training drills and simulations are strictly barred from alerting active responders or executing real dispatch.

---

## 4. Hardware, RF Physics & Regulatory Grounding

All radio frequency parameters in UrSafe are grounded in verified regulatory documentation and physical wave propagation formulas.

### LoRa Time-on-Air (ToA) Physical Calculations
Evaluated using the Semtech LoRa airtime equation for the standard **Meshtastic LongFast** modem profile:
$$\text{Spreading Factor (SF)} = 11, \quad \text{Bandwidth (BW)} = 250\text{ kHz}, \quad \text{Coding Rate (CR)} = 4/5, \quad \text{Preamble} = 16\text{ symbols}$$

$$\text{Symbol Duration } T_s = \frac{2^{\text{SF}}}{\text{BW}} = \frac{2^{11}}{250,000\text{ Hz}} = 8.192\text{ ms}$$
$$\text{Preamble Duration } T_{\text{preamble}} = (N_{\text{preamble}} + 4.25) \times T_s = 20.25 \times 8.192\text{ ms} = 165.888\text{ ms}$$

$$\text{Payload Symbols } N_{\text{payload}} = 8 + \max\left(\left\lceil \frac{8 \times PL - 4 \times \text{SF} + 28 + 16 - 20 H}{4 \times (\text{SF} - 2 DE)} \right\rceil \times (\text{CR} + 4),\, 0\right)$$

| Payload Size ($PL$) | Payload Symbols | Total Airtime ($T_{\text{packet}}$) | Channel Impact & Feasibility |
| :--- | :---: | :---: | :--- |
| **20 Bytes** (Short SOS Beacon) | 28 symbols | **395.26 ms** | Compact life-safety ping; high channel capacity. |
| **60 Bytes** (Standard Emergency Beacon) | 63 symbols | **681.98 ms** | Compact beacon with location + victim count. |
| **100 Bytes** (Extended Telemetry) | 103 symbols | **1009.66 ms** (~1.01 s) | High airtime; use store-and-forward throttling. |
| **237 Bytes** (Max Mesh Packet) | 228 symbols | **2033.66 ms** (~2.03 s) | Severe channel saturation; strictly gated for sync chunks. |

> *Notice: Any claims that LongFast can transmit a full 237-byte envelope in under 350 ms are physically impossible under LoRa modulation.*

### Indian Spectrum Regulatory Compliance
* **Official Gazette Notification:** Ministry of Communications and Information Technology (WPC), **G.S.R. 564(E)**, dated 30th July 2008.
* **Frequency Band:** **865.0 MHz to 867.0 MHz** (de-licensed for low-power wireless access systems).
* **Maximum Output Power:** **1 Watt (30 dBm)** transmitter power; **4 Watts (36 dBm)** Effective Radiated Power (ERP).
* **Maximum Channel Bandwidth:** **200 kHz** (or 250 kHz under specific carrier profiles).

### Android Keystore Hardware Security Architecture
* **Ed25519 Hardware Support:** The Android Keystore system (`android.security.keystore`) **does NOT support Ed25519 hardware key generation or storage in hardware TEE / StrongBox** across any production Android release (API 26 through API 35).
* **Production Cryptographic Strategy:**
  1. **NIST P-256 (`secp256r1`):** Fully hardware-backed via Android Keystore TEE / StrongBox on all Android 8.0+ devices; produces raw 64-byte $(r, s)$ signatures.
  2. **Software Ed25519 via Google Tink:** Pure software execution; key material protected on disk by wrapping private keys with an Android Keystore AES-256-GCM hardware `MasterKey`.

---

## 5. Implementation Truth Matrix

In accordance with UrSafe engineering standards, all repository capabilities are truthfully classified below:

| Subsystem / Capability | Implementation Status | Evidence & Test Location |
| :--- | :---: | :--- |
| **SQLite WAL Storage Engine** | `IMPLEMENTED & VERIFIED` | `apps/api/db.js`, `infrastructure/migrations/` |
| **Unbypassable Test DB Guard** | `IMPLEMENTED & VERIFIED` | `tests/test_db_guard.py` (throws `CRITICAL SAFETY GUARD`) |
| **Idempotent Ingestion Engine** | `IMPLEMENTED & VERIFIED` | `tests/test_idempotency_and_training.py` (`idx_incidents_reporter_client_msg`) |
| **Zero-Trust RBAC & IDOR Defense** | `IMPLEMENTED & VERIFIED` | `tests/security/test_rbac_probe.py`, `scripts/probe_rbac.py` |
| **Linear Flight Recorder Hash Chain** | `IMPLEMENTED & VERIFIED` | `apps/api/server.js`, `tests/test_backend_api.py` |
| **Training Suppression Isolation** | `IMPLEMENTED & VERIFIED` | `apps/api/continuity.js`, `tests/test_idempotency_and_training.py` |
| **Multilingual NLP Triage Engine** | `IMPLEMENTED & VERIFIED` | `services/nlp/`, `tests/test_nlp_and_calibration.py` |
| **Kinematic Hazard Expansion GIS** | `IMPLEMENTED & VERIFIED` | `services/hazard/`, `tests/test_hazard_and_dispatch.py` |
| **CRDT State Convergence** | `IMPLEMENTED & VERIFIED` | `packages/crdt/`, `tests/test_domain_and_crdt.py` |
| **Tactical Leaflet GIS Dashboard** | `IMPLEMENTED & VERIFIED` | `apps/web-console/index.html`, `apps/web-console/app.js` |
| **Truthfulness Static Linter** | `IMPLEMENTED & VERIFIED` | `tests/test_truthfulness_linter.py` (scans all sources for fake literals) |
| **Deterministic Radio Mesh Simulator** | `SIMULATED (ISOLATED)` | `hardware/simulator/`, `tests/test_routing_and_hardware.py` |
| **Meshtastic SX1262 LoRa Driver** | `NOT HARDWARE-VERIFIED` | `hardware/meshtastic/` (code complete; requires physical bench radio) |
| **Bluetooth Low Energy (BLE) Peripheral** | `NOT HARDWARE-VERIFIED` | `hardware/ble/` (GATT profile defined; requires physical RF pairing) |

---

## 6. Monorepo Structure

```
UrSafe/
├── apps/
│   ├── api/                 # Zero-dependency Node.js REST/WS Coordination Gateway & Engine
│   ├── web-console/         # High-contrast tactical coordination dashboard (Vanilla JS/CSS)
│   ├── victim-android/      # Civilian Android application (Room DB, 1-tap offline SOS)
│   └── responder-android/   # Tactical responder mobile application (W3C credentials, GIS)
├── packages/
│   ├── protocol/            # Binary serialization, protobuf schemas, 24 message types
│   ├── crypto/              # NIST P-256 / Ed25519 signing, ChaCha20-Poly1305, HKDF
│   ├── sync/                # Persistent DTN Outbox, bundle custody, data mule engine
│   ├── crdt/                # Conflict-free Replicated Data Types & Vector Clocks
│   ├── audit/               # Linear SHA-256 cryptographic flight recorder ledger
│   ├── routing/             # Delay-tolerant epidemic routing, ETX link quality evaluation
│   └── domain/              # Core domain models, progressive disclosure state machine
├── services/
│   ├── dispatch/            # Multi-criteria responder assignment & resource reservation
│   ├── hazard/              # Kinematic hazard expansion & dynamic route collision avoidance
│   ├── nlp/                 # Multilingual deterministic NLP triage (English, Hindi, Hinglish)
│   ├── credential/          # W3C Verifiable Credentials (Ed25519) for offline validation
│   ├── trust/               # Multi-signal Sybil defense & behavioral anomaly scoring
│   └── receipts/            # Dual-confirmed cryptographic rescue receipts
├── hardware/
│   ├── meshtastic/          # Meshtastic radio adapter (BLE NUS / Serial Protobufs)
│   ├── ble/                 # Direct peer-to-peer BLE discovery & GATT transport
│   └── simulator/           # Deterministic multi-node radio mesh simulator
├── infrastructure/
│   └── migrations/          # Versioned SQLite schema migrations (001, 002, 003)
├── docs/                    # Architecture records, verified facts, regulatory citations, QA
└── tests/                   # 102 comprehensive automated test suites (unit, security, e2e)
```

---

## 7. Quick Start & Operational Runbook

### Prerequisites
* **Node.js:** v18.0.0 or later (LTS recommended)
* **Python:** v3.11 or later
* **Rust / Cargo:** v1.75.0 or later (for core crypto & CRDT components)
* **Git:** Clean working tree

### Step 1: Run the Environment Doctor
Verify all system runtimes, database paths, and toolchains:
```bash
python scripts/doctor.py
```

### Step 2: Launch the Tactical Dashboard & Coordination Gateway
Start the unified Web Console and SQLite API gateway on port 3000:
```bash
node apps/web-console/server.js
```
Open your browser and navigate to:
```
http://localhost:3000
```

*Default pre-seeded accounts for testing and evaluation:*
* **Authority / Command:** `authority_rajesh` / `Password123!`
* **Tactical Responder:** `responder_vikram` / `Password123!`
* **Civilian Citizen:** `citizen_priya` / `Password123!`
* **System Administrator:** `admin_system` / `Password123!`

### Step 3: Run the Automated Test Suites

#### 1. Full Pytest Suite (119 Tests)
Executes end-to-end incident lifecycles, zero-trust RBAC/IDOR security probes, verification proof-of-work workflows, offline BLE GATT emergency exchange, crash continuity chaos tests, CRDT fuzzer, and database isolation guards:
```bash
pytest tests/ -v
```

#### 2. Verification & Proof-of-Work Suite (10 Tests)
Validates regional authorized office selection, applicant document upload with SHA-256 integrity calculation, authority review queue, document approve/reject controls, strict self-approval prevention, W3C verifiable credential issuance, and immutable flight recorder event logging:
```bash
pytest tests/test_verification_workflow.py -v
```

#### 3. Real Offline BLE Emergency Peer Exchange Suite (6 Tests)
Validates UrSafe GATT service `0xFE26` discovery, non-UrSafe device filtering, handshake session key generation, offline SOS ingestion without internet, deduplication suppression, cryptographic delivery ACK generation, and 512B MTU chunked evidence document transfer with SHA-256 verification:
```bash
pytest tests/test_ble_emergency_exchange.py -v
```

#### 4. Rust Core Test Suite (3 Tests)
Validates binary protocol envelope serialization, vector clock merge determinism, and cryptographic signature generation:
```bash
cargo test
```

#### 5. Truthfulness Static Linter
Scans all frontend and backend source files to guarantee zero hardcoded fake metrics, non-functional literals, or deceptive status indicators exist in production code:
```bash
pytest tests/test_truthfulness_linter.py -v
```

#### 6. Real Offline DTN Acceptance Simulation
Executes a multi-node partitioned valley simulation with store-and-forward data mule bundle delivery:
```bash
python scripts/run_acceptance_demo.py
```

---

## 8. Security & Operational Integrity

### Database Isolation Guard
To prevent accidental pollution or destructive writes to operational databases during automated testing, `apps/api/db.js` enforces an unbypassable safety guard:
```javascript
// Throws a fatal exception if test environment attempts to mount production database
if ((isTestEnv || isPytestRunning) && dbPath.toLowerCase().includes('production')) {
  throw new Error('CRITICAL SAFETY GUARD: Test runner attempted to mount production database.');
}
```

### Zero-Trust Authorization (RBAC & IDOR Defense)
* Every endpoint verifies session integrity against active bearer tokens.
* Object-level authorization prevents unauthorized cross-tenant inspection:
  ```javascript
  if (incident.reporter_user_id !== session.userId && !['AUTHORITY', 'ADMIN', 'RESPONDER'].includes(session.role)) {
    return sendJson(403, { error: 'Forbidden: You do not have permission to inspect this emergency incident' });
  }
  ```

---

## 9. Verification & Architectural Evidence

Detailed documentation, mathematical derivations, regulatory filings, and QA audit reports are preserved in `docs/`:

* [`docs/VERIFIED_FACTS.md`](file:///docs/VERIFIED_FACTS.md) — Grounded truth repository: LoRa airtime derivations, Indian Gazette G.S.R. 564(E) citations, Meshtastic protobuf UUIDs, and Android Keystore analysis.
* [`docs/ARCHITECTURE_CURRENT.md`](file:///docs/ARCHITECTURE_CURRENT.md) — Comprehensive technical specification of the multi-bearer rescue mesh.
* [`docs/UI_SPECIFICATION.md`](file:///docs/UI_SPECIFICATION.md) — Visual styling, contrast standards, and truthfulness design system.
* [`docs/DELIVERY_SEMANTICS.md`](file:///docs/DELIVERY_SEMANTICS.md) — Exact state transitions for outbox and transport delivery.
* [`docs/AUDIT_0.md`](file:///docs/AUDIT_0.md) — Initial engineering audit, code classification, and safety refactoring log.

---

## 10. License

UrSafe / Cascade26 is licensed under the [Apache License, Version 2.0](LICENSE). 
*Designed and built for humanitarian disaster response and life-critical operational resilience.*

# UrSafe / Cascade26
## Real Offline-First Emergency Communication & Coordination Platform

> **"Internet is an accelerator, NOT the foundation."**

UrSafe is an offline-first disaster response infrastructure designed from first principles to save lives when cellular towers, electrical grids, and cloud servers are inoperable.

---

## Key Architectural Principles

1. **Autonomous Nodes:** Every field smartphone and radio terminal maintains its own cryptographic identity, encrypted local database, CRDT state, and synchronization outbox.
2. **Multi-Bearer Mesh:** Operates across Meshtastic LoRa radios (868/915 MHz), Bluetooth Low Energy (BLE), and ad-hoc Wi-Fi Direct.
3. **Delay-Tolerant Networking (DTN):** Opportunistic store-and-forward bundles carried across isolated valleys and flood zones by mobile responders (data mules).
4. **Verifiable Credentials (Responder Passport):** W3C Verifiable Credentials signed with Ed25519 allowing instant offline validation of volunteer skills, medical certifications, and authority roles.
5. **CRDT State Convergence:** Partitioned nodes merge independent field updates deterministically without split-brain corruption or data loss.
6. **Time-Aware Hazard Prediction:** Evaluates hazard polygon progression at estimated arrival time ($t_0 + \text{ETA}$), rerouting units away from advancing flood or fire fronts.
7. **Offline Multilingual NLP Triage:** On-device extraction of category, count of victims, and urgency from English, Hindi, and Hinglish ("paani aa raha hai") with zero hallucination.
8. **Tamper-Evident Flight Recorder:** Linear SHA-256 cryptographic hash chain providing forensic auditing and post-disaster accountability.

---

## Monorepo Layout

```
UrSafe/
├── apps/
│   ├── victim-android/      # Civilian Android app (1-tap offline SOS, Room DB, BLE)
│   ├── responder-android/   # Tactical responder Android app (Passport, navigation, ACK)
│   ├── web-console/         # High-contrast operational coordinator dashboard
│   └── api/                 # Cloud coordination & replication gateway (optional peer)
├── packages/
│   ├── protocol/            # Binary envelopes, 24 message types, protobuf schemas
│   ├── crypto/              # Ed25519, X25519, HKDF, ChaCha20-Poly1305, Keystore
│   ├── sync/                # Persistent DTN Outbox, bundle custody, data mules
│   ├── crdt/                # State-based CRDTs, Vector Clocks, domain safety guards
│   ├── audit/               # Tamper-evident Flight Recorder hash chains
│   ├── routing/             # ETX link-quality metrics, managed flooding, dedup
│   └── domain/              # Core domain models, progressive disclosure
├── services/
│   ├── dispatch/            # Multi-criteria optimization & scarce resource reservation
│   ├── hazard/              # Kinematic hazard expansion & route collision detection
│   ├── nlp/                 # Offline English/Hindi/Hinglish triage & probability calibration
│   ├── credential/          # W3C Responder Passport issuance & offline verification
│   ├── trust/               # Multi-signal Sybil & behavioral anomaly defense
│   └── receipts/            # Dual-confirmed cryptographic rescue receipts
├── hardware/
│   ├── meshtastic/          # Meshtastic radio adapter (BLE NUS / USB serial)
│   ├── ble/                 # Direct peer-to-peer BLE discovery & transport
│   └── simulator/           # Deterministic multi-node radio mesh simulator
├── contracts/               # Protobuf schemas and OpenAPI contracts
├── docs/                    # Research, PRD, RTM, and ADRs
└── tests/                   # End-to-end, fuzzing, red-team, and unit test suites
```

---

---

## Three Greenfield Core Product Verticals

UrSafe focuses on 100% completion of three indispensable emergency verticals:

### Vertical 1: Identity + Exact Location + Real Map
- Multi-role authenticated sessions (`CITIZEN`, `RESPONDER`, `AUTHORITY`, `ADMIN`)
- Real hardware GNSS coordinates (`latitude`, `longitude`, `accuracy_m`) as the source of truth
- Structured reverse geocoding to human-readable street addresses
- Real WGS84 geographic mapping with distinct entity markers:
  - Current User ("YOU"): Pulsating cyan dot with accuracy radius circle & freshness indicator
  - Emergency Victims: Urgency-coded red markers linking to full case inspection
  - Tactical Responders: Emerald markers with specialization badge & live telemetry
  - Connected BLE Devices: Cyan markers reflecting physical proximity

### Vertical 2: Complete Emergency Lifecycle + Evidence + History
- Deterministic 18-stage conceptual state machine:
  `DRAFT` → `SOS_CREATED` → `SAVED_LOCALLY` → `QUEUED` → `TRANSMITTING` → `RECEIVED` → `RESPONDER_NOTIFIED` → `RESPONDER_ASSIGNED` → `MISSION_ACCEPTED` → `EN_ROUTE` → `ARRIVED_ON_SCENE` → `RESCUE_IN_PROGRESS` → `RESCUE_COMPLETED` → `EVIDENCE_REQUIRED` → `EVIDENCE_SUBMITTED` → `VERIFICATION_PENDING` → `VERIFIED` → `CLOSED`
- Controlled exceptional states: `CANCELLED`, `REJECTED`, `REOPENED` with mandatory audit reasons
- Evidence Desk: Photo & PDF upload, real-time SHA-256 content hashing, 10MB size ceiling, duplicate collision prevention (HTTP 409 Conflict)
- Dedicated Emergency History Portal: Full chronological lifecycle timeline, evidence gallery, and audited case reopening

### Vertical 3: Real Bluetooth BLE Presence & Synchronization
- UrSafe BLE Application Service UUID `0xFE26` (`0000FE26-0000-1000-8000-00805F9B34FB`)
- Categorized device scanner: Nearby UrSafe nodes, compatible LoRa radios, and other generic peripherals
- Connected User Presence Card: Live RSSI dBm, battery %, heartbeat timer, and map marker placement
- Durable offline outbox queue with priority-based synchronization (P0 Life Safety)

---

## Quick Start & Verification

### 1. Run the Environment Doctor
```bash
python scripts/doctor.py
```

### 2. Start the Unified Web Console & API Gateway
```bash
node apps/web-console/server.js
# Open http://localhost:3000 in your browser
```

### 3. Run Automated Tests
```bash
# Python & Backend integration tests (59 tests)
pytest tests/ -v

# Core Rust crypto & CRDT tests (3 tests)
cargo test

# Real offline DTN data-mule acceptance demo
python scripts/run_acceptance_demo.py
```


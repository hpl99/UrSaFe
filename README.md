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

## Quick Start & Verification

### Run the Complete Test Suite
```bash
pytest tests/ -v
```

### Run the Web Coordinator Console
```bash
node apps/web-console/server.js
# Access at http://localhost:3000
```

### Run the Physical & Multi-Node Acceptance Demo
```bash
python scripts/run_acceptance_demo.py
```

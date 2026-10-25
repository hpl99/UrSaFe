# UrSafe Requirements Traceability Matrix (RTM)

This matrix establishes bidirectional traceability between system requirements, architecture decision records (ADRs), source implementation packages, automated test suites, and demonstration scenarios in accordance with the UrSafe Engineering Mandate.

| Requirement ID | Description | PRD Ref | ADR Ref | Source Implementation | Test Verification | Demo / Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-MSG-001** | Durable binary message envelope with cryptographic header | §4.1 | ADR-004 | `packages/protocol/envelope.py`, `envelope.ts` | `tests/test_protocol_envelope.py` | Offline SOS broadcast |
| **REQ-MSG-002** | Versioned message types (24 core emergency types) | §4.1 | ADR-004 | `packages/protocol/types.py`, `messages.proto` | `tests/test_protocol_types.py` | State machine progression |
| **REQ-MSG-003** | Priority queueing (Emergency SOS over Telemetry) | §4.1 | ADR-005 | `packages/sync/outbox.py` | `tests/test_priority_queue.py` | High-load mesh stress test |
| **REQ-MSG-004** | Deterministic deduplication & hop-limit bounding | §4.1 | ADR-002 | `packages/routing/router.py` | `tests/test_dedup_routing.py` | Multi-hop loop simulation |
| **REQ-SEC-001** | Ed25519 & X25519 hardware-backed key generation | §4.2 | ADR-003 | `packages/crypto/keys.py`, `keystore.py` | `tests/test_crypto_identity.py` | Keypair lifecycle demo |
| **REQ-SEC-002** | Identity segregation (Device, User, Responder, Org) | §4.2 | ADR-003 | `packages/crypto/identity.py` | `tests/test_identity_separation.py` | Rogue responder test |
| **REQ-SEC-003** | AEAD payload encryption with ephemeral nonces | §4.2 | ADR-003 | `packages/crypto/encryption.py` | `tests/test_aead_encryption.py` | Eavesdropper inspection |
| **REQ-SEC-004** | Anti-replay protection with sequence sliding windows | §4.2 | ADR-003 | `packages/crypto/replay.py` | `tests/test_replay_defense.py` | Red-team packet replay |
| **REQ-DAT-001** | Local durable offline storage (SQLite / Room) | §4.3 | ADR-001 | `packages/domain/database.py`, Android DAOs | `tests/test_local_storage.py` | Device reboot survival |
| **REQ-DAT-002** | State-based CRDT state convergence | §4.3 | ADR-006 | `packages/crdt/state.py`, `vector_clock.py` | `tests/test_crdt_convergence.py` | Partition merge fuzzer |
| **REQ-DAT-003** | Domain safety guards (on-scene rescue preservation) | §4.3 | ADR-006 | `packages/crdt/safety_guard.py` | `tests/test_domain_safety.py` | Conflicting cancel scenario |
| **REQ-DAT-004** | Asynchronous, resumable, idempotent sync engine | §4.3 | ADR-005 | `packages/sync/engine.py` | `tests/test_sync_engine.py` | Intermittent link demo |
| **REQ-HW-001** | Abstract Transport interface | §4.4 | ADR-002 | `hardware/transport_interface.py` | `tests/test_transport_interface.py` | Mock bearer swap |
| **REQ-HW-002** | Meshtastic LoRa Protobuf adapter | §4.4 | ADR-002 | `hardware/meshtastic/adapter.py` | `tests/test_meshtastic_adapter.py` | Physical radio loopback |
| **REQ-HW-003** | Multi-node mesh network simulator | §4.4 | ADR-002 | `hardware/simulator/mesh_sim.py` | `tests/test_mesh_simulator.py` | 5-node island topology |
| **REQ-HW-004** | Link quality metric collection (RSSI/SNR/ETX) | §4.4 | ADR-002 | `packages/routing/metrics.py` | `tests/test_link_metrics.py` | Degraded link reroute |
| **REQ-TRU-001** | W3C Verifiable Credentials Responder Passport | §4.5 | ADR-009 | `services/credential/passport.py` | `tests/test_responder_passport.py` | Offline passport verification |
| **REQ-TRU-002** | Explicit offline revocation freshness evaluation | §4.5 | ADR-009 | `services/credential/revocation.py` | `tests/test_revocation_status.py` | Stale vs revoked alert |
| **REQ-TRU-003** | Multi-signal Sybil & anomaly risk scoring | §4.5 | ADR-008 | `services/trust/sybil_detector.py` | `tests/test_sybil_defense.py` | Red-team Sybil cluster attack |
| **REQ-TRU-004** | Dual-confirmed signed Rescue Receipts | §4.5 | ADR-010 | `services/receipts/receipt_engine.py` | `tests/test_rescue_receipts.py` | Collusion & fake rescue test |
| **REQ-DIS-001** | Dynamic hazard polygons with time-expansion | §4.6 | ADR-011 | `services/hazard/engine.py` | `tests/test_hazard_engine.py` | Advancing flood simulation |
| **REQ-DIS-002** | Hazard-at-arrival route intersection evaluation | §4.6 | ADR-011 | `services/hazard/intersector.py` | `tests/test_hazard_rerouting.py` | Dynamic avoidance reroute |
| **REQ-DIS-003** | Deterministic multi-criteria dispatch optimizer | §4.6 | ADR-012 | `services/dispatch/optimizer.py` | `tests/test_dispatch_optimizer.py` | Resource contention run |
| **REQ-DIS-004** | Greedy vs. Optimized empirical benchmark | §4.6 | ADR-012 | `services/dispatch/benchmark.py` | `tests/test_dispatch_benchmark.py` | Benchmark comparison run |
| **REQ-NLP-001** | Offline multilingual emergency classifier | §4.7 | ADR-013 | `services/nlp/triage.py` | `tests/test_multilingual_nlp.py` | Hindi/Hinglish distress demo |
| **REQ-NLP-002** | Entity, slot, and source span extraction | §4.7 | ADR-013 | `services/nlp/extractor.py` | `tests/test_nlp_extraction.py` | Structured triage output |
| **REQ-NLP-003** | Zero hallucination clarification trigger | §4.7 | ADR-013 | `services/nlp/clarification.py` | `tests/test_nlp_ambiguity.py` | Ambiguous distress text |
| **REQ-NLP-004** | Calibrated probabilities (Brier score & ECE) | §4.7 | ADR-013 | `services/nlp/calibration.py` | `tests/test_calibration_metrics.py` | Calibration curve generation |
| **REQ-PRV-001** | 5-tier progressive location & info disclosure | §4.8 | ADR-014 | `packages/domain/disclosure.py` | `tests/test_progressive_disclosure.py`| Eavesdropper privacy test |
| **REQ-AUD-001** | Cryptographic hash-chain Flight Recorder | §4.9 | ADR-007 | `packages/audit/flight_recorder.py` | `tests/test_flight_recorder.py` | Tamper-detection validation |
| **REQ-AUD-002** | Audit log verification and export | §4.9 | ADR-007 | `packages/audit/verifier.py` | `tests/test_audit_verification.py` | Forensic verification demo |
| **REQ-MOB-001** | Android Victim Application (Offline UI, Room) | §2.1 | ADR-015 | `apps/victim-android/` | Android test harnesses | One-tap offline SOS |
| **REQ-MOB-002** | Android Responder Application (Passport, Nav) | §2.2 | ADR-015 | `apps/responder-android/` | Android test harnesses | Offline accept & navigate |
| **REQ-WEB-001** | High-contrast Coordinator Web Console | §2.3 | ADR-016 | `apps/web-console/` | Console verification tests | Full incident operations |
| **REQ-DTN-001** | Data Mule bundle custody & opportunistic sync | §3 | ADR-005 | `packages/sync/mule.py` | `tests/test_data_mule.py` | Island A to Island B bridge |
| **REQ-CONT-001** | Durable Outbox (Never Send Before Save) | §5 | ADR-018 | `apps/api/continuity.js`, `infrastructure/migrations/003_continuity_engine.sql` | `tests/test_continuity_engine.py` | Outbox crash recovery |
| **REQ-CONT-002** | P0 Life Critical Preemption over P1-P5 | §8 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | Priority scheduler test |
| **REQ-CONT-003** | 13-State Delivery FSM | §9 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | State progression test |
| **REQ-CONT-004** | 5-Tier Acknowledgement Semantics | §10 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | Explicit ACK verification |
| **REQ-CONT-005** | Multi-Bearer Selection & Fallback | §16,17 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | BLE to LoRa fallback |
| **REQ-CONT-006** | Bounded Exponential Backoff with Jitter | §19 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | Retry storm prevention |
| **REQ-CONT-007** | Inbound Idempotency & Deduplication | §14 | ADR-018 | `apps/api/continuity.js`, `continuity_deduplication` | `tests/test_continuity_engine.py` | Duplicate packet suppression |
| **REQ-CONT-008** | Crash Recovery on Startup | §13 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | Process kill survival |
| **REQ-CONT-009** | Battery-Aware Transmission Deferral | §34 | ADR-018 | `apps/api/continuity.js` | `tests/test_continuity_engine.py` | Low-battery preemption |
| **REQ-CONT-010** | Connectivity Cockpit Real Telemetry | §22-25 | ADR-018 | `apps/web-console/index.html`, `app.js` | `tests/test_continuity_engine.py` | Live cockpit score & states |
| **REQ-CONT-011** | Failure Injection Controls | §64 | ADR-018 | `apps/api/server.js`, `app.js` | `tests/test_continuity_engine.py` | Bearer toggle failure test |
| **REQ-CONT-012** | Deterministic Chaos Harness | §66 | ADR-018 | `tests/test_continuity_chaos.py` | `tests/test_continuity_chaos.py` | 50-packet chaos convergence |


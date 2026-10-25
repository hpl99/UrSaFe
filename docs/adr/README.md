# UrSafe Architecture Decision Records (ADRs)

This directory contains the immutable Architecture Decision Records for the UrSafe Offline-First Emergency Communication and Coordination System.

## Architectural Decision Log

| ADR ID | Title | Status | Date |
| :--- | :--- | :--- | :--- |
| [ADR-001](decisions/ADR-001-offline-first-architecture.md) | Offline-First Architecture & Asynchronous Sync Engine | Approved | 2026-10 |
| [ADR-002](decisions/ADR-002-transport-abstraction-and-mesh.md) | Multi-Bearer Transport Abstraction & Meshtastic LoRa Integration | Approved | 2026-10 |
| [ADR-003](decisions/ADR-003-cryptography-identity-key-management.md) | Cryptographic Identity, Ed25519/X25519 & Hardware Keystore | Approved | 2026-10 |
| [ADR-004](decisions/ADR-004-schema-first-binary-protocol.md) | Schema-First Binary Envelope & Versioned Emergency Protocol | Approved | 2026-10 |
| [ADR-005](decisions/ADR-005-dtn-store-forward-outbox.md) | Delay-Tolerant Networking (DTN) Outbox & Data Mule Custody | Approved | 2026-10 |
| [ADR-006](decisions/ADR-006-crdt-state-convergence-safety-guards.md) | CRDT State Convergence & Domain Semantic Safety Guardrails | Approved | 2026-10 |
| [ADR-007](decisions/ADR-007-tamper-evident-flight-recorder.md) | Tamper-Evident Flight Recorder Cryptographic Hash Chains | Approved | 2026-10 |
| [ADR-008](decisions/ADR-008-multisignal-trust-sybil-defense.md) | Multi-Signal Behavioral Trust Engine & Sybil Anomaly Defense | Approved | 2026-10 |
| [ADR-009](decisions/ADR-009-verifiable-credentials-responder-passport.md) | W3C Verifiable Credentials Responder Passport & Revocation States | Approved | 2026-10 |
| [ADR-010](decisions/ADR-010-dual-confirmed-rescue-receipts.md) | Dual-Confirmed Cryptographic Rescue Receipts & Anti-Collusion | Approved | 2026-10 |
| [ADR-011](decisions/ADR-011-hazard-prediction-dynamic-rerouting.md) | Time-Aware Hazard Prediction & Dynamic Responder Rerouting | Approved | 2026-10 |
| [ADR-012](decisions/ADR-012-dispatch-optimization-resource-reservation.md) | Deterministic Multi-Criteria Dispatch & Scarce Resource Reservation | Approved | 2026-10 |
| [ADR-013](decisions/ADR-013-offline-multilingual-nlp-triage.md) | Offline Multilingual NLP Triage & Calibrated Probability Validation | Approved | 2026-10 |
| [ADR-014](decisions/ADR-014-progressive-disclosure-privacy.md) | 5-Tier Progressive Location Disclosure & Privacy Architecture | Approved | 2026-10 |
| [ADR-015](decisions/ADR-015-mobile-architecture-kotlin-android.md) | Native Android Mobile Architecture (Kotlin, Room, Coroutines) | Approved | 2026-10 |
| [ADR-016](decisions/ADR-016-coordinator-web-console.md) | High-Contrast Operational Web Console & MapLibre Offline Vector Maps | Approved | 2026-10 |
| [ADR-017](decisions/ADR-017-polyglot-multitier-architecture-selection.md) | Polyglot Multi-Tier Architecture & Technology Selection | Approved | 2026-10 |

## Validation Policy
ADRs in this repository are permanent records. Once approved, decisions are never overwritten; amendments are recorded as subsequent superseding ADRs.

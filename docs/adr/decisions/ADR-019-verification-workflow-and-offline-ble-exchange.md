# ADR-019: Verification Workflow, Proof-of-Qualification, and Offline BLE Peer Emergency Exchange

## Status
Accepted (Production Milestone Deliverable)

## Context
In life-critical disaster coordination, two fundamental vulnerabilities undermine civilian response networks:
1. **Unverified Impersonation and Rogue Responders**: Anyone could claim volunteer or responder privileges without proof of physical identity, qualification, training, or organizational backing. In an emergency, rogue actors or unverified personnel handling medical triages or rescue operations create severe safety, legal, and operational risks.
2. **Superficial Bluetooth Pairing**: Conventional Bluetooth discovery treats all RF devices indiscriminately (PCs, smart TVs, earbuds, audio accessories) and terminates at generic transport pairing without establishing an authenticated application session, message priority envelope, offline storage, delivery acknowledgements, or chunked document transport.

## Problem Statement
How to design and implement:
1. A real, authority-controlled, physical-office-anchored **Verification and Proof-of-Qualification workflow** that transitions through a formal state machine (`NOT_STARTED` -> `PROFILE_SUBMITTED` -> `OFFICE_SELECTED` -> `VISIT_PENDING` -> `DOCUMENTS_SUBMITTED` -> `UNDER_REVIEW` -> `VERIFIED` / `REJECTED` / `EXPIRED` / `SUSPENDED`), strictly prohibits client-side self-approval, audits all document verifications with cryptographic hashes, and issues durable W3C Verifiable Credentials;
2. A real **UrSafe-to-UrSafe Offline BLE Emergency Exchange** operating over standard service UUID `0xFE26` that filters out non-UrSafe devices, executes an authenticated GATT handshake, persists SOS envelopes into the local database without internet, returns cryptographic delivery ACKs (`ack_hash`), deduplicates retransmitted messages, and transfers 512B MTU chunked evidence documents with SHA-256 integrity verification.

## Decision

### 1. Verification & Proof-of-Qualification Subsystem
- **Physical Office Anchor (`verification_offices`)**:
  - Responders cannot be verified purely online or client-side. The user must be guided to an authorized regional verification office (e.g. Bandra BKC NDRF, Mantralaya SDMA, Fort Red Cross) created and authorized server-side by an admin (`authorized = 1`).
- **Finite State Machine (`verification_requests`)**:
  - States: `NOT_STARTED`, `PROFILE_SUBMITTED`, `OFFICE_SELECTED`, `APPOINTMENT_INSTRUCTION`, `VISIT_PENDING`, `DOCUMENTS_SUBMITTED`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `EXPIRED`, `SUSPENDED`.
  - Self-approval strictly blocked: A normal user or applicant calling `/approve` receives HTTP 403 Forbidden. Only authorized roles (`AUTHORITY`, `ADMIN`) can review and decide.
- **Durable Proof Documents with Cryptographic Hashes (`verification_documents`)**:
  - Each uploaded credential (Identity Proof, Training Certificate, Medical ALS/BLS, Organization ID) is hashed using SHA-256 (`sha256_hash`).
  - Private documents are stored under authenticated access control (`/api/v1/verification/documents/:id/download`). Third-party or cross-tenant access is strictly blocked (HTTP 403).
  - Verifiers independently approve or reject each document; rejections require a mandatory human justification reason.
- **W3C Verifiable Credential Issuance**:
  - Upon full approval, the authority issues an Ed25519-signed credential (`credentials` table) containing decentralized identifier (`did:ursafe:authority_rajesh`), authorization scopes, issuance/expiry timestamps, and tamper-proof signature.
- **Tamper-Evident Flight Recorder Integration**:
  - Every transition (`VERIFICATION_REQUEST_CREATED`, `DOCUMENT_UPLOADED`, `DOCUMENT_VERIFIED`, `DOCUMENT_REJECTED`, `RESPONDER_VERIFIED`, `RESPONDER_REJECTED`) is recorded into the SQLite WAL cryptographic hash chain (`audit_events`).

### 2. UrSafe-to-UrSafe Offline BLE Peer Transport
- **Service & Characteristic Allocation**:
  - UrSafe 16-bit SIG assigned GATT Service UUID: `0xFE26` (`0000FE26-0000-1000-8000-00805F9B34FB`).
  - Device Identity Characteristic: `0xFE27`.
  - Handshake Characteristic: `0xFE28`.
  - Data / Envelope Characteristic: `0xFE29`.
  - ACK Characteristic: `0xFE2A`.
  - Status Characteristic: `0xFE2B`.
- **Non-UrSafe Device Filtering**:
  - Hardware scan filter `ScanFilter.Builder().setServiceUuid(ParcelUuid(0xFE26)).build()` ignores generic Bluetooth accessories, PCs, and earbuds. Non-matching devices are never presented as actionable emergency peers.
- **Application-Level Device Identity**:
  - Stable application identities (`USF-8A42-VIKRAM`, `USF-3C19-ANITA`, `USF-9F81-PRIYA`) coupled with Ed25519 public keys, decoupled from volatile BLE MAC addresses.
- **Connection & Session State Machine**:
  - Transitions: `DISCOVERED` -> `CONNECTING` -> `CONNECTED` -> `AUTHENTICATED` -> `READY` -> `DISCONNECTED`.
  - Handshake exchanges protocol version (`1.0`), node identity, ephemeral session keys, and credential status.
- **Offline SOS Delivery & Deduplication**:
  - Inbound SOS messages are validated, cryptographically hashed, and written into local SQLite `incidents` and `incident_events` without any internet requirement.
  - Senders receive an authenticated delivery ACK hash (`ack_hash`).
  - Retransmitted messages matching existing `message_id` in `continuity_deduplication` immediately receive an ACK while suppressing duplicate business incidents.
- **Chunked Evidence Document Transfer (512B MTU)**:
  - Large photographic or triage evidence is split into 512-byte MTU chunks.
  - Per-chunk tracking in `ble_document_transfers`; if connection drops mid-transfer, reconnection resumes from the missing chunk index.
  - Final reassembly verifies full SHA-256 hash before completing.

## Consequences & Tradeoffs
- **Positive**:
  - Responders possess verified trust rooted in physical inspection and cryptographic signatures.
  - Complete operational autonomy during total cellular/internet blackouts.
  - Real UrSafe-to-UrSafe transport replaces generic Bluetooth pairing.
  - Strict privacy protections safeguard sensitive medical documents from unauthorized broadcast.
- **Tradeoff**:
  - Physical verification requires candidates to visit authorized regional centres.
  - Chunked BLE document transfers over 512B MTU require multiple roundtrips and are prioritized behind P0 life-critical distress control packets.

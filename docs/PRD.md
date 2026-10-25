# UrSafe Product Requirements Document (PRD)

**Version:** 1.0.0-PROD  
**Status:** Approved Architecture Baseline  
**Date:** October 2026  
**System:** UrSafe / Cascade26 Offline-First Emergency Mesh & Coordination Platform  

---

## 1. Executive Summary & Vision

### 1.1 The Reality of Disaster Communications
During severe natural or humanitarian crises—floods, earthquakes, hurricanes, grid collapses, and conflict events—traditional centralized telecommunications infrastructure fails. Cell towers lose power, fiber trunks sever, and cloud data centers become unreachable. In this blackout environment, victims cannot dial emergency services, responders cannot coordinate, and coordinators operate blindly.

### 1.2 The UrSafe Vision
**UrSafe is an offline-first emergency communication and coordination product.** It guarantees that life-saving emergency distress signals (SOS), responder dispatch, field acknowledgements, navigation, and rescue receipts function seamlessly without internet, cellular service, or central server availability.

The central cloud is an **accelerator**, NOT the foundation. Every smartphone and radio node maintains its own identity, encrypted local database, CRDT state, trust metrics, and synchronization outbox. Information propagates across local wireless ad-hoc meshes (LoRa, BLE, Wi-Fi Direct) and physical data mules, synchronizing with the central cloud only when intermittent connectivity emerges.

---

## 2. User Personas & Roles

### 2.1 Role A: Person Seeking Help (Victim / Field Civilian)
- **Profile:** Individuals in distress, injured, stranded, trapped by rising floodwaters, or experiencing medical trauma.
- **Physical Context:** Extreme stress, low smartphone battery, intermittent or zero network, loud/harsh environmental conditions.
- **Key Capabilities:**
  - One-tap SOS creation with automated sensor telemetry (battery, approximate GPS).
  - Offline transmission over BLE/LoRa radio or direct peer broadcast.
  - Specifying emergency category (Flood, Medical, Fire, Trapped, Structural Collapse, Evacuation).
  - Indicating count of affected individuals and immediate urgent needs (Infant, Elderly, Bleeding, Oxygen).
  - Attaching brief text notes in English, Hindi, or Hinglish with local multilingual extraction.
  - Viewing real-time delivery status: `CREATED` $\rightarrow$ `QUEUED_OFFLINE` $\rightarrow$ `TRANSMITTED_MESH` $\rightarrow$ `ACKNOWLEDGED_BY_MESH` $\rightarrow$ `RESPONDER_ASSIGNED` $\rightarrow$ `RESPONDER_EN_ROUTE` $\rightarrow$ `HELP_ARRIVED`.
  - Updating or cancelling emergency with local verification.
  - Receiving push safety instructions and responder proximity alerts locally.

### 2.2 Role B: Field Responder / Volunteer
- **Profile:** Professional rescue personnel (NDRF, Fire, EMS) and certified civilian disaster volunteers.
- **Physical Context:** Operating in hostile field terrain, wearing gloves, limited visibility, relying on battery-powered radios and ruggedized mobile devices.
- **Key Capabilities:**
  - Creating and storing cryptographic identity (Ed25519) on-device.
  - Carrying digitally signed **Responder Passports** (W3C Verifiable Credentials) validating skills and certifications.
  - Receiving emergency alerts directly via LoRa mesh or BLE without internet.
  - Reviewing incident cards with severity, distance, estimated travel time, capability match, hazard risk, and network reliability.
  - Accepting, holding, or declining assignments with signed acknowledgements propagating through the mesh.
  - Offline navigation using local vector maps, hazard overlay polygons, and dynamic reroute advice.
  - Emitting real-time responder telemetry (`RESPONDER_LOCATION`, `EN_ROUTE`, `ARRIVED`, `RESCUE_STARTED`, `RESCUE_COMPLETED`).
  - Generating dual-confirmed cryptographic **Rescue Receipts** upon mission completion.

### 2.3 Role C: Incident Coordinator (Emergency Operations Center / Field Command)
- **Profile:** Field commanders and regional dispatch officers managing multiple incident clusters.
- **Physical Context:** Operating from a forward operating base, command vehicle, or regional headquarters with intermittent satellite, local Wi-Fi mesh, or radio gateway access.
- **Key Capabilities:**
  - High-contrast, operational Web Console visualizing global and partitioned incident states.
  - Monitoring mesh network health, radio links, signal-to-noise ratios (SNR), and network partitions.
  - Inspecting automated dispatch recommendations and overriding assignments manually when tactical conditions dictate.
  - Tracking time-aware hazard progression (floods, fires) and predicted intersection with responder routes.
  - Monitoring security alerts, Sybil anomalies, lure relays, and credential revocation status.
  - Reviewing the immutable Flight Recorder audit hash chain.

### 2.4 Role D: Organization Administrator
- **Profile:** Government agencies, civil defense headquarters, and accredited NGO directors.
- **Key Capabilities:**
  - Issuing digitally signed Verifiable Credentials (Responder Passports) to qualified personnel.
  - Managing credential lifecycle, skill taxonomies, and publishing signed revocation delta lists.
  - Configuring regional emergency policies, geofences, and progressive disclosure rules.
  - Performing forensic audits of emergency operations and cryptographic receipts.

---

## 3. User Journeys & End-to-End Scenarios

### Journey 1: Fully Offline SOS & Field Rescue
1. **Trigger:** A flood breaches a river embankment in a remote valley; all cellular towers are dead.
2. **Victim Action:** Victim opens the UrSafe Victim App on Android. Taps large red "I NEED HELP" button. App captures GPS coordinates, prompts for emergency type (selects FLOOD) and people count (3).
3. **Local Encryption & Queue:** App creates an `SOS_CREATED` envelope, signs it with the victim's Ed25519 key, encrypts sensitive payload under progressive disclosure level 1, and saves it in the local SQLite Room outbox.
4. **Mesh Transmission:** The phone connects via BLE to a companion Meshtastic LoRa radio (868/915 MHz). Radio transmits the compact binary Protobuf packet over LoRa.
5. **Multi-Hop Propagation:** Stationary repeater nodes on hilltops receive the packet, verify hop limit, decrement TTL, and rebroadcast it across the valley.
6. **Responder Reception:** A volunteer responder's radio 6 km away picks up the packet. The responder's phone receives it over BLE, triggers a local audible alarm, and renders the incident card.
7. **Acceptance & ACK:** The responder taps "ACCEPT". The responder's app signs an `SOS_ACCEPTED` message and transmits it over LoRa.
8. **Victim Notification:** The victim's phone receives the ACK via the mesh. UI updates: *"Help is on the way. Unit Alpha-1 accepted. ETA ~15 min."*
9. **Rescue & Receipt:** The responder arrives (`ARRIVED`), conducts the evacuation (`RESCUE_COMPLETED`), and generates a dual-signed `RESCUE_RECEIPT` exchanged locally over BLE.

### Journey 2: Partitioned Valley & Data Mule Synchronization
1. **Context:** Sector A and Sector B are completely separated by a mountain ridge exceeding direct LoRa range.
2. **Action:** A responder in an all-terrain vehicle travels from Sector A toward Sector B.
3. **Mule Ingestion:** The vehicle's onboard UrSafe node exchanges bundle inventory vectors with Sector A's gateway, taking custody of 14 pending encrypted bundles.
4. **Transit:** Vehicle crosses the ridge into Sector B.
5. **Mule Propagation:** Upon detecting Sector B's radio mesh, the node automatically transfers the missing bundles.
6. **Convergence:** Sector B's coordinators receive the queued SOS reports and status updates, merging state via CRDT logic without data loss or duplicate collisions.

---

## 4. Functional Requirements

### 4.1 Message Architecture & Protocol (REQ-MSG)
- **REQ-MSG-001:** All communication MUST be encapsulated in a schema-first binary message envelope containing globally unique `message_id`, `sender_id`, `recipient_id`, `created_at`, `expires_at`, `priority`, `message_type`, `sequence`, `hop_limit`, `origin`, `current_hop`, `payload`, `payload_hash`, `signature`, and `encryption_metadata`.
- **REQ-MSG-002:** The system MUST support versioned message types: `SOS_CREATED`, `SOS_UPDATED`, `SOS_CANCELLED`, `SOS_ACKNOWLEDGED`, `SOS_ASSIGNED`, `SOS_ACCEPTED`, `SOS_DECLINED`, `RESPONDER_STATUS`, `RESPONDER_LOCATION`, `ARRIVED`, `RESCUE_STARTED`, `RESCUE_COMPLETED`, `RESCUE_RECEIPT`, `CREDENTIAL_ISSUED`, `CREDENTIAL_REVOKED`, `ROUTE_UPDATE`, `NODE_ANNOUNCEMENT`, `NODE_STATUS`, `HAZARD_UPDATE`, `PARTITION_DETECTED`, `PARTITION_HEALED`, `SYNC_REQUEST`, `SYNC_RESPONSE`, `SECURITY_ALERT`.
- **REQ-MSG-003:** High-priority emergency messages (`SOS_CREATED`, `SOS_ACCEPTED`) MUST strictly bypass low-priority telemetry queues in both local outbox and radio transmission buffers.
- **REQ-MSG-004:** Message envelopes MUST feature deterministic deduplication via `message_id` and payload hashes, preventing infinite broadcast storms.

### 4.2 Cryptography & Identity (REQ-SEC)
- **REQ-SEC-001:** Every device MUST generate and manage an Ed25519 signing keypair and X25519 key-exchange keypair stored in hardware-backed secure storage (Android Keystore / Secure Enclave).
- **REQ-SEC-002:** The system MUST strictly segregate Device Identity, User Identity, Responder Identity, and Organization Identity.
- **REQ-SEC-003:** Payloads containing privacy-sensitive data MUST be encrypted with authenticated symmetric ciphers (ChaCha20-Poly1305 or AES-256-GCM) with distinct ephemeral nonces.
- **REQ-SEC-004:** The protocol MUST implement anti-replay mechanisms utilizing monotonically increasing sequence numbers and sliding-window replay caches.

### 4.3 Offline Storage & CRDT Synchronization (REQ-DAT)
- **REQ-DAT-001:** Every mobile and server node MUST persist application state in a local, durable, encrypted database (SQLite / Room on mobile, PostgreSQL on server).
- **REQ-DAT-002:** Distributed mutable state MUST converge using mathematically sound Conflict-Free Replicated Data Types (CRDTs) satisfying idempotence, commutativity, and associativity.
- **REQ-DAT-003:** The system MUST enforce semantic domain safety guardrails: on-scene responder state transitions (`ARRIVED`, `RESCUE_STARTED`) MUST take precedence over stale remote cancellations.
- **REQ-DAT-004:** The sync engine MUST operate asynchronously, supporting store-and-forward outbox queues, partial transfers, and resumable transfers across disconnections.

### 4.4 Hardware Abstraction & Mesh Transport (REQ-HW)
- **REQ-HW-001:** The core application logic MUST NOT couple directly to vendor hardware APIs. It MUST communicate through a unified `Transport` interface (`discover`, `connect`, `disconnect`, `send`, `receive`, `getCapabilities`, `getLinkMetrics`).
- **REQ-HW-002:** Implement a production `MeshtasticTransport` interfacing with Meshtastic radios via BLE and USB Serial using Protobuf wire contracts.
- **REQ-HW-003:** Implement simulated and local loopback transports capable of executing automated multi-node acceptance tests without physical radios attached.
- **REQ-HW-004:** Link quality metrics (RSSI, SNR, packet error rate) MUST be continuously gathered and supplied to routing algorithms.

### 4.5 Trust Engine & Verifiable Credentials (REQ-TRU)
- **REQ-TRU-001:** Responder credentials MUST follow W3C Verifiable Credential data models, digitally signed by recognized authorities.
- **REQ-TRU-002:** Field verifiers MUST evaluate credential validity offline, displaying explicit statuses: `VERIFIED`, `VERIFIED_REVOCATION_STALE`, `EXPIRED`, `REVOKED`, or `UNKNOWN`.
- **REQ-TRU-003:** Implement multi-signal Sybil and anomaly detection, scoring nodes into `NORMAL`, `SUSPICIOUS`, `HIGH_RISK`, and `ISOLATED` with detailed evidence reasons.
- **REQ-TRU-004:** Completed rescues MUST generate dual-signed `RescueReceipt` records containing victim confirmation, responder confirmation, timestamp, location, and witness observations.

### 4.6 Hazard Prediction & Predictive Dispatch (REQ-DIS)
- **REQ-DIS-001:** The hazard engine MUST model spatial hazard polygons (floods, fires, landslides) with time-expansion vectors and distinguish `OBSERVED`, `PREDICTED`, and `REPORTED` states.
- **REQ-DIS-002:** Dispatch calculations MUST evaluate `hazard_at_arrival` at $t = t_0 + \text{ETA}$, dynamically rerouting or holding units if route intersections are detected.
- **REQ-DIS-003:** Dispatch optimization MUST balance arrival time, capability match, critical incident delay, and scarce resource reservation.
- **REQ-DIS-004:** The system MUST benchmark optimized dispatch against baseline greedy dispatch using identical deterministic seeds, reporting concrete empirical measurements.

### 4.7 Offline Multilingual NLP & Triage (REQ-NLP)
- **REQ-NLP-001:** Emergency triage classification MUST execute 100% on-device without cloud APIs for English, Hindi, and Hinglish.
- **REQ-NLP-002:** Extraction MUST output category, count of affected people, urgency level, confidence score, and exact source substring span.
- **REQ-NLP-003:** Low-confidence (<0.65) or ambiguous inputs MUST prompt for clarification rather than hallucinating categories.
- **REQ-NLP-004:** Model probabilities MUST be empirically calibrated, reporting Brier score and Expected Calibration Error (ECE).

### 4.8 Progressive Disclosure & Privacy (REQ-PRV)
- **REQ-PRV-001:** Location and victim identities MUST be protected via 5-tier progressive disclosure:
  - Level 0: Anonymous notification that an emergency exists.
  - Level 1: Approximate sector / region (e.g., 2 km geohash) + emergency category.
  - Level 2: Assignment details available to assigned responder.
  - Level 3: Precise GPS coordinates and phone/contact details upon accepted assignment.
  - Level 4: Sensitive medical / special-needs data disclosed strictly under authorized policy.

### 4.9 Flight Recorder Audit Trail (REQ-AUD)
- **REQ-AUD-001:** Every state mutation MUST generate an immutable, cryptographically hashed audit entry linked to the previous entry via SHA-256 hash chains.
- **REQ-AUD-002:** Audit logs MUST be exportable, verifiable offline, and resistant to retroactive alteration.

---

## 5. Non-Functional Requirements

### 5.1 Reliability & Resilience
- Zero single points of failure. Failure or absence of the central cloud MUST NOT disrupt local emergency operations.
- Process crashes, Android OS task kills, or battery exhaustion MUST NOT corrupt local databases or lose pending outbox messages.
- The system MUST survive arbitrary network partitions and converge automatically upon reconnection.

### 5.2 Performance Benchmarks
- Local SOS creation and disk persistence: $< 50\text{ ms}$.
- Message serialization and cryptographic signing: $< 15\text{ ms}$.
- Local triage NLP classification latency: $< 10\text{ ms}$ on mobile CPU.
- CRDT merge latency for 100 concurrent operations: $< 25\text{ ms}$.
- Web Console rendering under 1,000 active nodes: $> 55\text{ fps}$.

### 5.3 Radio Bandwidth & Airtime Budget
- LoRa payload size MUST NOT exceed 237 bytes per packet.
- Binary envelopes MUST utilize compact Protobuf encodings.
- Node announcements MUST adhere to regional regulatory duty cycles (1% in 868 MHz band; $< 400\text{ ms}$ dwell time in 915 MHz band).

### 5.4 Usability & Accessibility
- High-contrast, dark-mode-first visual presentation adhering to WCAG 2.1 Level AA standards.
- Minimum touch target size: $48 \times 48\text{ dp}$ on mobile screens.
- Color MUST NOT be the sole indicator of critical status; icons and textual labels are mandatory.
- Web Console fully responsive across desktop ($1920\times1080$, $1366\times768$), tablet ($1280\times800$), and mobile widths.

---

## 6. Known Physical Limitations & Explicit Anti-Goals

### 6.1 Physical Limitations
- **LoRa Bandwidth:** LoRa is designed for short telemetry and text; real-time video or high-resolution imagery CANNOT be transmitted over multi-hop LoRa. High-bandwidth assets require Wi-Fi Direct or physical data mule transport.
- **Physical Line-of-Sight & Obstacles:** Extreme mountainous terrain or heavy reinforced concrete structures attenuate radio signals; deployment requires elevated repeater nodes.
- **Stale Revocation:** An offline node cannot know if a credential was revoked 5 minutes ago if no revocation list has reached that network island.

### 6.2 Anti-Goals (What UrSafe Is NOT)
- UrSafe is **NOT** a diagnostic medical tool and makes zero claims of medical treatment.
- UrSafe does **NOT** guarantee physical rescue; it is emergency communication and coordination infrastructure.
- UrSafe does **NOT** rely on centralized cloud push notifications (APNs / FCM) as a mandatory delivery pipeline.

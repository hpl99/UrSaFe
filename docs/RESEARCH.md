# UrSafe Research & Technical Foundations

This document details the scientific, algorithmic, and engineering research underlying the UrSafe offline-first emergency communication and coordination system. In accordance with the UrSafe Engineering Mandate, every key architectural and technological decision is documented with its source, problem statement, proposed solution, evaluated alternatives, selection justification, known physical/systemic limitations, licensing implications, and implementation impact.

---

## 1. Meshtastic: Open-Source Mesh & LoRa Telemetry

- **Source**: [Meshtastic Firmware](https://github.com/meshtastic/firmware), [Meshtastic Android](https://github.com/meshtastic/Meshtastic-Android), [Protobuf Definitions](https://github.com/meshtastic/protobufs), [Documentation](https://meshtastic.org/docs/)
- **Problem**: In natural disasters (floods, earthquakes, hurricanes), cellular base stations and fiber backhauls suffer catastrophic structural collapse or grid failure within minutes. Devices need to transmit short, urgent telemetry and rescue requests without pre-existing network infrastructure across distances of 1–15 km using low-power radios.
- **Proposed Solution**: Adopt Meshtastic's channel-utilization principles, managed flooding routing model with hop-limit bounding, NodeDB discovery semantics, and Protocol Buffer wire encoding. Interface UrSafe mobile and stationary node layers with Meshtastic hardware devices via BLE (Nordic UART Service / Protobuf serial streams) and direct USB serial.
- **Alternatives Evaluated**:
  - *Disaster Radio*: Lacks active development, lacks hardware ecosystem diversity, no standardized Android SDK.
  - *Gotenna Pro*: Proprietary protocol, expensive vendor lock-in, closed source, cannot be audited or integrated into field smartphones freely.
  - *Custom Semtech SX1262 LoRa Driver*: Reinventing PHY/MAC firmware diverts focus from emergency coordination logic and misses out on 100,000+ deployed open nodes worldwide.
- **Why Selected**: Meshtastic provides mature, off-the-shelf COTS hardware (Heltec V3, T-Beam, RAK Wireless WisBlock), cross-platform protobuf bindings (TypeScript, Python, Kotlin/Java), automated channel hopping, regulatory duty-cycle awareness, and an active global open-source community.
- **Limitations**:
  - Very low bandwidth: 100 bps to 5.4 kbps depending on spreading factor (SF7 to SF12) and bandwidth (125 kHz to 500 kHz).
  - Maximum payload size is restricted to 237 bytes per LoRa packet; large media payloads require fragmentation or DTN data mule transport.
  - Regulatory duty-cycle restrictions (e.g., 1% in EU868, FCC Part 15 dwell limits in US915).
  - High packet collision rates under unmanaged channel flooding.
- **License**: GPL-3.0 (firmware/Android), MIT (protobuf definitions). Protobuf schema reuse and wire-protocol interop preserve clean license boundaries without GPL infection of UrSafe core libraries.
- **Implementation Impact**: UrSafe defines a clean `Transport` hardware abstraction. The `MeshtasticTransport` implements protobuf framing, handles BLE MTU slicing (typically 20-512 bytes), manages local ACK timers, and extracts SNR/RSSI telemetry for link-quality routing.

---

## 2. Reticulum Network Stack: Cryptographic Identity & Low-Bandwidth Transport

- **Source**: [Reticulum Network](https://reticulum.network/), [Manual](https://reticulum.network/manual/), [GitHub](https://github.com/markqvist/Reticulum)
- **Problem**: Traditional ad-hoc networks rely on IP addresses, centralized DNS, or unauthenticated MAC addresses, making them vulnerable to IP spoofing, routing poisoning, and man-in-the-middle attacks across untrusted physical radios.
- **Proposed Solution**: Implement a destination-centric cryptographic addressing scheme inspired by Reticulum. Endpoints in UrSafe are addressed by the cryptographic hash of their public keys (16-byte Destination IDs derived from Ed25519 signing keys and X25519 encryption keys via HKDF-SHA256). Every packet header is cryptographically verifiable, links are treated as untrusted physical bearers, and ephemeral session keys protect payload confidentiality.
- **Alternatives Evaluated**:
  - *Standard IPv6 over LoRaWAN (6LoWPAN)*: Too much protocol overhead (40-byte IPv6 headers), relies on central gateways and Join Servers not present in partitioned disaster zones.
  - *Yggdrasil Network*: Requires global cryptographic routing tree convergence; unstable under extreme network partitioning and high node churn.
  - *CJDNS*: Complex DHT overlay, requires significant memory and bandwidth unsuitable for microcontrollers and intermittent BLE.
- **Why Selected**: Reticulum's design proves that cryptographic security can exist within 100-byte packets. Destination hashes prevent source tracking by eavesdroppers, while signed announcements allow trustless route discovery.
- **Limitations**: Reticulum is primarily Python-based and uses custom packet formats that require specialized packet parsers. UrSafe extracts its mathematical identity primitives (Ed25519 + X25519 + HKDF + truncated destination hashes) into schema-first Protobuf envelopes.
- **License**: MIT License.
- **Implementation Impact**: `packages/crypto` implements Ed25519 signature verification, X25519 Diffie-Hellman key agreement, and ChaCha20-Poly1305 / AES-256-GCM AEAD encryption, separating device, responder, and organization identity keys.

---

## 3. Briar: Delay-Tolerant Direct Peer Synchronization & Adversarial Defense

- **Source**: [Briar Project](https://briarproject.org/how-it-works/), [GitHub](https://github.com/briar/briar)
- **Problem**: When infrastructure completely fails, nodes may never have a simultaneous end-to-end path to each other. Communication must happen peer-to-peer via opportunistic encounters (Bluetooth, Wi-Fi Direct, Local Wi-Fi), while resisting coercion, surveillance, and sybil insertion.
- **Proposed Solution**: Adopt Briar's direct synchronization model using Bramble Transport and Message protocols: peer-to-peer authenticated handshakes, locally encrypted databases (SQLCipher/SQLite), append-only signed record graphs, and opportunistic local sync over available interfaces without internet relay servers.
- **Alternatives Evaluated**:
  - *Signal Protocol / Double Ratchet*: Requires an online central server for pre-key bundle storage and distribution. Unusable when network is isolated.
  - *Secure Scuttlebutt (SSB)*: High storage requirements (unbounded append-only logs for all followed feeds), difficult to purge or prioritize urgent emergency updates.
- **Why Selected**: Briar demonstrates robust, field-tested Android peer-to-peer communication under oppressive and degraded environments.
- **Limitations**: Heavy CPU and battery usage if Bluetooth scanning is unbounded; Android OS background execution limits throttle scanning intervals.
- **License**: GPL-3.0. UrSafe utilizes Briar's architectural design patterns (outbox queue, contact exchange, local encryption) in a clean-room modular architecture.
- **Implementation Impact**: The UrSafe Sync Engine (`packages/sync`) implements an asynchronous, idempotent, resume-capable Outbox and Inbox pattern with priority-tiered queues (SOS emergency packets bypass synchronization backlogs).

---

## 4. Delay-Tolerant Networking (DTN) & Data Mules (RFC 4838)

- **Source**: [RFC 4838: Delay-Tolerant Networking Architecture](https://www.rfc-editor.org/rfc/rfc4838.html), [RFC 5050 Bundle Protocol](https://www.rfc-editor.org/rfc/rfc5050.html)
- **Problem**: Disasters create disconnected "network islands" (e.g., Valley A and Valley B separated by a collapsed bridge or mountain). Neither radio nor cellular can bridge the gap directly.
- **Proposed Solution**: Implement an opportunistic Store-and-Forward Data Mule architecture. Mobile responders, emergency vehicles, or drones traveling between disconnected sectors carry encrypted, signed bundle archives in their local storage. When physical proximity is detected with another island via BLE or local Wi-Fi, mutual inventory vector exchanges occur, missing bundles are transmitted, cryptographically verified, and merged into the destination island's mesh.
- **Alternatives Evaluated**:
  - *Satellite Uplinks (Starlink/Iridium)*: High hardware cost, requires power generators, fragile dishes vulnerable to wind/rain/smoke, cannot be assumed available at every victim cluster.
  - *Epidemic Flooding*: Exhausts device storage and LoRa airtime rapidly, causing catastrophic packet drops.
- **Why Selected**: DTN bundle architecture provides deterministic lifecycle guarantees: Bundle IDs, explicit Time-To-Live (TTL), custodian handoffs, cryptographic delivery receipts, and anti-replay caches.
- **Limitations**: High end-to-end latency (minutes to hours depending on physical courier transit times). Real-time telemetry cannot rely solely on mules, but life-saving SOS bundles and incident logs can traverse partitions safely.
- **License**: IETF Open Standards.
- **Implementation Impact**: `packages/sync` implements `BundleCustodian`, `InventoryVector`, and `MuleSyncProtocol`, managing on-disk bundle persistence, hop-limit decrementing, and cryptographic validation before propagation.

---

## 5. Verifiable Credentials & Offline Responder Passport (W3C VC)

- **Source**: [W3C Verifiable Credentials Data Model v2.0](https://www.w3.org/TR/vc-data-model/)
- **Problem**: In chaotic disaster areas, malicious actors, unqualified volunteers, or looters may pose as authorized medical personnel or search-and-rescue teams. Furthermore, official relief agencies (NDRF, FEMA, Red Cross) issue credentials when internet is active, but responders must verify each other's credentials in deep offline zones where central directory servers are unreachable.
- **Proposed Solution**: Implement the UrSafe Responder Passport based on cryptographic Verifiable Credentials. An issuing authority (e.g., Civil Defense Organization) signs a compact, structured credential with its Ed25519 private key. The credential contains subject ID, authorized roles (MEDIC, SEARCH_AND_RESCUE, FIREFIGHTER, STRUCTURAL_ENGINEER), certified skills, geographic bounds, and expiration timestamps. Any field responder or coordinator device can verify the signature and validity offline using cached public keys.
- **Alternatives Evaluated**:
  - *X.509 PKI Certificates*: Extremely verbose, rigid parsing, poor JSON/Protobuf interoperability, complex CRL/OCSP revocation requirements incompatible with offline mesh.
  - *Central OAuth / JWT Bearer Tokens*: Require online introspection endpoints or central token refresh servers.
- **Why Selected**: W3C VC principles offer lightweight, human-readable yet cryptographically rigorous credential envelopes. Revocation semantics in UrSafe are made explicit: `VERIFIED`, `VERIFIED_REVOCATION_STALE` (when revocation delta list has not been refreshed within configured threshold), `EXPIRED`, `REVOKED`, or `UNKNOWN`.
- **Limitations**: Real-time revocation is mathematically impossible in an offline partition; if a credential is revoked after a responder enters a disconnected zone, nearby nodes cannot know until a revocation list update is delivered via mesh or data mule. The UI must honestly convey revocation status freshness.
- **License**: W3C Royalty-Free Patent Policy.
- **Implementation Impact**: `services/credential` provides credential issuance, offline verification, status evaluation, and revocation delta propagation.

---

## 6. Conflict-Free Replicated Data Types (CRDT) for Partitioned State Convergence

- **Source**: Shapiro et al., *Conflict-free Replicated Data Types* (INRIA Research Report 7687, 2011); Kleppmann et al., *Conflict-Free Replicated Data Types for Collaborative Applications*.
- **Problem**: In an emergency mesh with network partitions, concurrent status updates happen independently on multiple nodes (e.g., Coordinator A assigns Unit 4 to Victim 12, while Responder 4 accepts Victim 12 directly in the field; Responder updates status to ARRIVED while cloud marks CANCELLED). Traditional distributed consensus (Raft, Paxos, 2PC) requires synchronous quorum and fails completely during partitions.
- **Proposed Solution**: Implement state-based and delta-state CRDTs (LWW-Element-Set, Observed-Remove Set with Vector Clocks, and Multi-Value Registers) for incident state, responder location, and resource allocation. All mutations satisfy mathematical idempotence, commutativity, and associativity ($A \sqcup B = B \sqcup A$ and $(A \sqcup B) \sqcup C = A \sqcup (B \sqcup C)$).
- **Domain Policy Guardrails**: In emergency management, mathematical convergence is necessary but not sufficient. UrSafe separates CRDT state convergence from domain safety policies:
  - *Semantic Rule*: If a responder has flagged `ARRIVED` or `RESCUE_STARTED` on-scene, a stale or concurrent `ASSIGNMENT_CANCELLED` operation merged from an isolated partition must NOT trigger abandonment of the rescue. The system flags the conflict for human review while preserving on-scene safety priority.
- **Alternatives Evaluated**:
  - *Eventual Consistency via Timestamp-only (LWW)*: Prone to clock skew and clock tampering on mobile devices; can silently drop vital rescue updates.
  - *Centralized Relational Locks*: Fails 100% of the time when disconnected from the central server.
- **Why Selected**: CRDTs guarantee that whenever any two partitions exchange messages (whether after 10 seconds or 10 hours), their emergency databases converge deterministically without manual conflict resolution modals.
- **Limitations**: Vector clocks grow linearly with the number of participating nodes if unbounded; requires periodic garbage collection and epoch compaction.
- **License**: Open scientific literature.
- **Implementation Impact**: `packages/crdt` implements State-based CRDTs, Vector Clocks, domain safety guards, and includes an automated Monte-Carlo Fuzzing harness executing thousands of randomized network partition and message interleaving permutations.

---

## 7. Tamper-Evident Flight Recorder: Cryptographic Hash Chains

- **Source**: Haber and Stornetta, *How to Time-Stamp a Digital Document* (Journal of Cryptology, 1991); Git Object Model.
- **Problem**: Post-disaster inquiries, insurance claims, and humanitarian investigations require indisputable proof of who issued an SOS, which responder accepted it, when units arrived, and whether any orders were manipulated. Centralized server logs are vulnerable to retroactive tampering by system administrators or unauthorized access.
- **Proposed Solution**: Implement a local and distributed append-only Flight Recorder. Every state transition emits an immutable audit event:
  $$\text{EventHash}_i = \text{SHA256}(\text{EventID}_i \parallel \text{Timestamp}_i \parallel \text{EventHash}_{i-1} \parallel \text{ActorID} \parallel \text{Action} \parallel \text{PayloadHash} \parallel \text{Signature})$$
  This forms a lightweight, linear cryptographic hash chain. Any modification, insertion, or deletion of past events breaks the chain integrity immediately.
- **Alternatives Evaluated**:
  - *Public Blockchain (Ethereum/Solana)*: Requires continuous high-speed internet, high transaction gas fees, unacceptable latency, and leaks public emergency metadata.
  - *Plain File Logs*: Trivial to truncate, delete, or fabricate without detection.
- **Why Selected**: Zero network overhead, verifiable offline on any mobile device, tamper-evident, and auditable by external oversight bodies.
- **Limitations**: Hash chains detect tampering but do not prevent a malicious node with root access from generating an alternate branch from scratch. Mitigation: periodic peer cross-signing and anchor receipts.
- **License**: Open cryptographic standard.
- **Implementation Impact**: `packages/audit` implements `FlightRecorder`, event chaining, signature verification, and audit export tools.

---

## 8. Multi-Signal Sybil & Behavioral Trust Defense

- **Source**: Douceur, *The Sybil Attack* (IPTPS 2002); EigenTrust Algorithm (Kamvar et al., Stanford 2003).
- **Problem**: In an open ad-hoc wireless mesh, an adversary can spin up hundreds of virtual nodes to flood the network with fake emergencies, hijack rescue assignments, or black-hole legitimate traffic (Sybil attacks and lure relays).
- **Proposed Solution**: UrSafe deploys a multi-signal risk scoring engine. Trust is decomposed into orthogonal components:
  1. *Identity Trust*: Cryptographic key age, binding to verified credentials.
  2. *Credential Trust*: Valid W3C Verifiable Credential from an accredited organization.
  3. *Behavioral Trust*: Consistency of transmission frequency, rate-limit adherence, route forwarding compliance.
  4. *Network Trust*: Diverse witness confirmations (packet observed by multiple independent radios).
  5. *Rescue Reputation*: Dual-confirmed, closed-loop rescue receipts.
  Nodes are scored into discrete states: `NORMAL`, `SUSPICIOUS`, `HIGH_RISK`, `ISOLATED`.
- **Alternatives Evaluated**:
  - *Proof-of-Work (PoW)*: Drains mobile batteries and radio airtime; penalizes low-power victim devices.
  - *Centralized Identity Whitelist*: Completely breaks ad-hoc volunteer participation in disaster zones.
- **Why Selected**: Multi-signal scoring prevents any single compromised vector from compromising the mesh, allowing untrusted spontaneous volunteers to communicate while prioritizing verified channels for critical dispatch.
- **Limitations**: Sybil attacks cannot be 100% prevented in an open physical topology without centralized authority; the engine isolates malicious clusters through statistical divergence and neighbor diversity metrics.
- **License**: Open algorithmic design.
- **Implementation Impact**: `services/trust` implements `SybilDetector`, `MultiSignalTrustEngine`, anomaly alert propagation, and visual security alerts on the coordinator console.

---

## 9. Dynamic Hazard Progression & Predictive Dispatch Optimization

- **Source**: [Sahana Eden Disaster Management](https://github.com/sahana/eden); Miller et al., *Time-Expanded Networks for Dynamic Evacuation Planning* (Transportation Science); NOAA / Copernicus Flood Inundation Modeling.
- **Problem**: Disaster environments are dynamic: floodwaters rise, wildfires spread, and landslides block roads. Dispatching a responder based solely on static shortest path ($t=t_0$) can route the responder directly into an expanding hazard zone, endangering the rescuer and failing the victim.
- **Proposed Solution**: Implement a Time-Aware Hazard Engine and Predictive Dispatch Optimizer. Hazards are modeled with geographic polygons, severity ratings, validity windows, and deterministic kinematic expansion vectors:
  $$P(t) = P(t_0) + \vec{v}_{\text{expansion}} \cdot (t - t_0)$$
  For any candidate responder with estimated arrival time $\text{ETA}$, UrSafe evaluates the intersection of the proposed route and destination against the predicted hazard polygon at $t = t_0 + \text{ETA}$:
  $$\text{SafetyCheck} = \text{Route}(t) \cap \text{Hazard}(t_0 + \text{ETA}) == \emptyset$$
  If an intersection is predicted, the system calculates alternative avoidance routes, places a temporary safety hold, or dispatches an alternative unit from a safe vector.
- **Scarce Resource Reservation**: When multiple emergencies compete for limited specialized resources (e.g., single advanced cardiac life support medic), assignment optimizes global survival probability using deterministic multi-criteria scoring (severity weight, arrival latency, resource match, replacement probability) while strictly prioritizing verified life-threatening incidents.
- **Alternatives Evaluated**:
  - *Greedy Nearest-Neighbor Dispatch*: Causes cascading failures, high unserved critical incident rates, and routes responders into advancing hazard fronts.
  - *Black-Box Neural Policy Models*: Unexplainable decisions, high hallucination risk under unprecedented disaster conditions, impossible to verify offline on embedded edge devices.
- **Why Selected**: Deterministic mathematical modeling provides explainable, reproducible, and verifiable dispatch recommendations with manual human coordinator overrides.
- **Limitations**: Hazard expansion parameters require initial sensor/report inputs; under unpredicted catastrophic flash floods, real-time field reports must override predicted vectors.
- **License**: MIT / Open Source.
- **Implementation Impact**: `services/hazard` and `services/dispatch` provide real-time hazard evaluation, routing avoidance, and an automated benchmark comparing baseline greedy vs. optimized dispatch.

---

## 10. Offline Multilingual NLP & Hindi/Hinglish Emergency Triage

- **Source**: Joshi et al., *Unsung Challenges of Under-Resourced Languages* (ACL 2020); fastText character n-grams; Rule-Based Emergency Ontologies (HAZMAT, FEMA ICS-201).
- **Problem**: Victims in distress often submit panicky, fragmented, code-mixed text (e.g., *"paani aa raha hai ghar mein bahut tez bachao"*, *"chhat par 3 log phanse hain, medical help urgently needed"*). Cloud translation APIs (Google Cloud Translate, OpenAI) are completely unavailable offline.
- **Proposed Solution**: Implement an offline multilingual triage classifier operating on lightweight character n-grams, phonological normalization, and a curated emergency ontology for English, Hindi, and Hinglish. It extracts:
  - `category`: `FLOOD`, `FIRE`, `MEDICAL`, `COLLAPSE`, `EVACUATION`, `TRAPPED`
  - `people_affected`: integer count
  - `urgency`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
  - `confidence`: calibrated probability $[0.0, 1.0]$
  - `source_span`: exact character substring triggering the classification.
  *Zero Hallucination Rule*: If confidence falls below 0.65 or critical slots are ambiguous, the engine flags `NEEDS_CLARIFICATION` and generates targeted follow-up prompts instead of guessing.
- **Alternatives Evaluated**:
  - *Large Language Models (Llama-3, Mistral 7B)*: Require 4–16 GB RAM and heavy GPU/NPU compute; cannot run on low-end Android field devices or embedded gateways.
  - *Cloud NLP Services*: Zero availability without internet.
- **Why Selected**: Sub-millisecond execution, runs on any smartphone CPU, zero network dependency, deterministic output, completely explainable.
- **Limitations**: Nuanced metaphorical expressions or regional dialects outside the vocabulary set require operator clarification.
- **License**: Apache 2.0 / MIT.
- **Implementation Impact**: `services/nlp` provides offline multilingual extraction, confidence calibration, and automated test suites for English, Hindi, and Hinglish distress messages.

---

## 11. Calibrated Probabilities & Scientific Evaluation

- **Source**: Brier, *Verification of forecasts expressed in terms of probability* (Monthly Weather Review, 1950); Guo et al., *On Calibration of Modern Neural Networks* (ICML 2017).
- **Problem**: Raw classifier scores often suffer from overconfidence (e.g., claiming 99% certainty on an ambiguous distress call). In emergency systems, equating raw confidence with true probability leads to disastrous misallocations. Furthermore, probability and trust must never be conflated.
- **Proposed Solution**: Implement empirical probability calibration using Platt Scaling and Isotonic Regression, evaluated through:
  - **Brier Score**: Mean squared difference between predicted probabilities and actual binary outcomes:
    $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$
  - **Expected Calibration Error (ECE)**: Weighted average difference between bin accuracy and bin confidence across $M$ equal-width probability bins:
    $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
  - **Distinction**: `Probability` measures likelihood under evaluated empirical data; `Trust` measures multi-dimensional cryptographic, behavioral, and structural integrity.
- **Implementation Impact**: `services/nlp` and `services/dispatch` include calibration validation suites computing Brier scores and ECE metrics across standard disaster benchmark sets.

---

## 12. Offline Maps & Vector Cartography

- **Source**: MapLibre GL, OpenStreetMap Foundation, Protomaps (PMTiles specification).
- **Problem**: Traditional web maps fetch raster or vector tiles from online CDN servers (Mapbox, Google Maps). In an offline disaster zone, standard maps show a blank grey grid, rendering navigation impossible.
- **Proposed Solution**: Utilize self-contained offline vector tile packages (PMTiles / MBTiles) cached locally on mobile and coordinator storage. The client renders terrain, streets, building footprints, and hazard overlays entirely on-device via WebGL / Canvas / MapLibre Native without making external network requests.
- **Alternatives Evaluated**:
  - *Static Raster Screenshots*: Rigid, cannot zoom or rotate, high storage footprint, no dynamic layer styling.
  - *Online Tile Fetching*: Fails immediately when disconnected.
- **Why Selected**: PMTiles allows single-file archive deployment, efficient range-request reads, compact vector compression, and full offline styling.
- **Implementation Impact**: `apps/web-console` and mobile applications integrate offline vector rendering with dynamic SVG/Canvas fallback overlays for hazard polygons, responder paths, and geofences.

---

## Summary Matrix of Key Technology Decisions

| Subsystem | Selected Architecture | Primary Alternative | Why Selected | Trade-offs & Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Mesh Transport** | Meshtastic Protobuf + BLE / USB / LoRa | Reticulum RNS | Rich COTS hardware ecosystem, mobile SDKs, regulatory compliance | Restricted payload (<237B), low data rate |
| **Identity & Crypto** | Ed25519 + X25519 + HKDF + AEAD | X.509 PKI / RSA | Ultra-compact public keys (32B), high performance, no central CA | Manual trust root / credential exchange |
| **Outbox & DTN** | Idempotent Bundle Queue + Custody | Epidemic Flooding | Zero duplicate loops, priority-aware, explicit TTL expiry | Eventual delivery latency across mule hops |
| **State Sync** | State-Based CRDT + Safety Guards | Raft / Paxos / 2PC | Partition-tolerant ($AP$), deterministic convergence | Vector clock overhead; requires semantic guards |
| **Credentials** | W3C Verifiable Credentials | OAuth2 / JWT online | Fully verifiable offline, cryptographically tamper-proof | Revocation freshness requires explicit state |
| **Hazard Prediction** | Dynamic Kinematic Polygons | Static Shortest Path | Prevents dispatching rescuers into expanding floods/fires | Requires initial hazard parameter estimation |
| **Triage NLP** | Character N-Grams + Emergency Ontology | Cloud LLM (GPT-4) | 100% offline, zero hallucination, sub-millisecond | Limited to domain vocabulary without internet |
| **Audit Log** | Linear Hash Chain (Flight Recorder) | Ethereum / Public Chain | Zero gas cost, offline verifiable, tamper-evident | Chain branch detection requires peer cross-signing |

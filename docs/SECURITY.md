# UrSafe Cryptographic Security & STRIDE Threat Model

## 1. STRIDE Threat Model

| Threat | Disaster Attack Vector | UrSafe Countermeasure |
|---|---|---|
| **Spoofing** | Adversary broadcasts fake SOS beacons to divert rescue helicopters | Ed25519 digital signatures on all Protobuf envelopes; unauthenticated packets marked UNTRUSTED |
| **Tampering** | Man-in-the-middle alters victim count or GPS coordinates | SHA-256 payload integrity hash included in signature coverage |
| **Repudiation** | Responder falsely claims victim was rescued without arriving | Strict Rescue Proof workflow (Section 27): on-scene photo/video SHA-256 hash + citizen co-signing |
| **Information Disclosure** | Adversary eavesdrops on citizen medical conditions via LoRa | Field beacons transmit only operational triage categories; sensitive records encrypted with AES-256-GCM |
| **Denial of Service** | Malicious RF jammer or packet flooder depletes LoRa bandwidth | Sliding-window replay filter, rate limiting, and packet deduplication |
| **Elevation of Privilege** | Citizen attempts to dispatch responders by sending `role=ADMIN` | Server-enforced RBAC; roles derived exclusively from authenticated server database |

---

## 2. Replay Attack Mitigation

Because LoRa mesh packets are broadcast omnidirectionally over RF, an attacker could capture a valid signed emergency packet and retransmit it hours or days later.

### Sliding-Window Nonce Filter:
1. Every packet envelope contains:
   - `sender_public_key` (32 bytes)
   - `sequence_number` (64-bit strictly monotonic integer)
   - `epoch_timestamp_ms` (64-bit Unix timestamp)
   - `random_nonce` (16 bytes)
2. Receiving nodes maintain an in-memory bitmask window of the last 1,024 sequence numbers per sender.
3. Packets with timestamps older than the maximum skew window (e.g., 30 minutes) or matching seen nonces are **instantly dropped before parsing payload data**.

---

## 3. Flight Recorder Hash Chain Audit Trail (Section 54)

Every security-sensitive operation (Login, Incident Creation, Dispatch, Evidence Upload, Rescue Verification) is appended to an immutable append-only hash chain:

$$H_0 = \text{SHA-256}(\text{"GENESIS\_URSAFE\_AUDIT\_BLOCK\_2026"})$$
$$H_n = \text{SHA-256}(H_{n-1} \parallel \text{Timestamp} \parallel \text{ActorID} \parallel \text{Action} \parallel \text{ObjectID})$$

If an attacker modifies a database record post-facto, the Merkle verification check detects the broken link index immediately and alerts the Authority Command Console (`CHAIN_TAMPER_ALERT`).

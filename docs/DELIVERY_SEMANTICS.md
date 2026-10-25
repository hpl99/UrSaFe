# UrSafe Delivery Semantics & Reliability Guarantees
## Formal Distributed Systems Delivery Model

---

## 1. Core Guarantee
UrSafe provides:
$$\text{At-Least-Once Physical Transport} + \text{Idempotent Application Processing} = \text{Effectively-Once Logical Processing}$$

In distributed mesh networks characterized by lossy RF channels, packet retransmissions, and network partitions, mathematically guaranteed "exactly-once physical delivery" is impossible (Two Generals' Problem). UrSafe avoids false exactly-once claims and instead implements:
1. **Durable Local Storage**: Every message is committed to disk before radio transmission.
2. **Aggressive Store-and-Forward Retries**: Unacknowledged messages retry across alternate bearers with bounded exponential backoff and jitter.
3. **Application-Level Deduplication**: The receiver deduplicates on unique `message_id` and `payload_hash` in `continuity_deduplication`.
4. **Replay & Reordering Defense**: Packets outside validity windows or with duplicate monotonic sequences are rejected or merged commutatively via CRDT logic.

---

## 2. Distinction Between States
UrSafe rigorously separates transport acknowledgement from operational lifecycle events:
```text
Radio Accepted Frame (TRANSPORT_ACK)
       ≠
Mesh Node Received Packet (NODE_ACK)
       ≠
Responder Phone Parsed Packet (APPLICATION_ACK)
       ≠
Responder Human Accepted Mission (HUMAN_ACK)
```
Under no circumstances will the incident business status transition to `MISSION_ACCEPTED` merely because a packet was delivered over radio. An explicit authenticated responder action is mandatory.

---

## 3. Data Mule Guarantees (Section 37)
When responders or emergency vehicles physically traverse partitioned network islands:
1. Messages are bundled into a signed store-and-forward bundle.
2. The carrier node injects the bundle into the disconnected island via `POST /api/v1/continuity/sync`.
3. Receiving nodes execute inbound deduplication:
   - Duplicates are recorded in the sync receipt and suppressed.
   - New messages are enqueued into the recipient's local database and dispatched to local responders.
4. An immutable audit record is committed to the Flight Recorder hash chain.

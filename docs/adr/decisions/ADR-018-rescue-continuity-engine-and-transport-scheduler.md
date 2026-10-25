# ADR-018: Rescue Continuity Engine, Priority Scheduler, and Multi-Bearer Transport

## Status
Accepted (Phase 4 Production Implementation)

## Context
In catastrophic disaster environments, commercial telecommunication infrastructures (cellular towers, fiber backbones, DNS, and cloud endpoints) fail completely or become severely fragmented. Previous prototypes relied either on direct HTTP cloud requests or on an unprioritized radio loop. Under heavy load or battery degradation, low-priority telemetry packets (P5) could saturate limited LoRa radio bandwidth (approx. 250 bps - 5.4 kbps) and starve life-critical distress signals (P0). Furthermore, process death or phone reboots during packet transmission risked message loss or state ambiguity.

## Problem Statement
How to guarantee that an emergency message continues attempting delivery through every viable communication path (BLE, Meshtastic LoRa, Local Wi-Fi, Internet Cloud, Data Mule) until its delivery policy is satisfied or its validity period expires, without losing, duplicating, corrupting, falsely acknowledging, or silently abandoning the emergency, and while ensuring P0 traffic strictly preempts all lower-priority traffic.

## Decision
1. **Durable Outbox Pattern (Never Send Before Save)**:
   - All outbound communication must be persisted to SQLite WAL storage (`continuity_messages`) within an atomic transaction before any radio or network transmission is attempted.
   - Enforce sequence: `CREATE -> VALIDATE -> PERSIST TO DB -> COMMIT -> QUEUE -> ATTEMPT TRANSPORT`.

2. **13-State Delivery FSM & 5-Tier Acknowledgement Semantics**:
   - Distinct separation between Incident Lifecycle and Delivery Lifecycle.
   - Delivery FSM: `CREATED`, `QUEUED`, `SCHEDULED`, `TRANSMITTING`, `SENT`, `DELIVERED`, `ACKNOWLEDGED`, `RETRY_WAIT`, `DEFERRED`, `EXPIRED`, `FAILED`, `CANCELLED`, `DEAD_LETTER`.
   - Acknowledgement Levels: `NONE`, `TRANSPORT_ACK` (radio frame accepted), `NODE_ACK` (mesh relay received), `APPLICATION_ACK` (UrSafe app parsed), `HUMAN_ACK` (explicit responder action).

3. **Strict Priority Preemption (P0 - P5)**:
   - Queue scheduler prioritizes traffic strictly:
     - `P0`: Life Critical (SOS, imminent danger, trapped person, responder distress)
     - `P1`: Emergency Control (cancellation, escalation, assignment)
     - `P2`: Responder Operation (acceptance, en route, on scene)
     - `P3`: Safety & Location (coordinates, hazard updates, check-ins)
     - `P4`: Normal Message (operational chat)
     - `P5`: Telemetry (link pings, battery updates, node announcements)
   - When device battery drops <= 15%, the engine automatically defers P3-P5 while preserving continuous delivery attempts for P0-P1.

4. **Multi-Transport Selection & Fallback**:
   - Policy-based selection evaluating bearer constraints, link metrics, and battery.
   - P0 fallback order: BLE -> Meshtastic LoRa -> Local Ad-Hoc Wi-Fi -> Central Cloud -> Data Mule.
   - Automatic transport degradation and failover without manual user intervention.

5. **Bounded Exponential Backoff with Jitter**:
   - P0 backoff: 2s base, 1.5x factor, 15s max ceiling with +/- 20% random jitter to avoid mesh broadcast storms.
   - P5 backoff: 5s base, 2.0x factor, 120s max ceiling.

6. **Crash Recovery on Startup**:
   - Engine sweeps database on boot for any message stuck in `TRANSMITTING` or `SCHEDULED` due to ungraceful shutdown and resets them safely to `RETRY_WAIT` with zero message loss.

7. **Inbound Idempotency & Replay Protection**:
   - Dedicated `continuity_deduplication` table tracks `(message_id, sender_device_id, payload_hash)`.
   - Inbound duplicate packets are safely acknowledged without re-executing domain mutations.

## Consequences & Tradeoffs
- **Positive**: Complete offline-first resilience; zero message loss across reboots; zero starvation of SOS traffic; complete transparency and auditable failure logs.
- **Tradeoff**: Bounded retry ceiling ensures that unrecoverable messages enter `DEAD_LETTER` after maximum attempts rather than looping infinitely and draining battery.

# ADR-010: Dual-Confirmed Cryptographic Rescue Receipts & Anti-Collusion

## Status
Approved

## Context
Reputation systems in distributed environments can be gamed: a bad actor could generate fake rescues to inflate reputation, or claim credit for rescues that never took place. Single-party assertions cannot be trusted in high-stakes emergency auditing.

## Decision
1. Introduce **Rescue Receipts** requiring dual cryptographic confirmation:
   - **Victim Confirmation**: Victim signs receipt on their device confirming physical assistance.
   - **Responder Confirmation**: Responder signs receipt with their Responder Passport key.
   - **Witness Telemetry**: Proximity evidence (BLE handshake, GPS match within allowable radius, radio packet observation by nearby mesh repeaters).
2. The receipt contains: `receipt_id`, `incident_id`, `victim_id`, `responder_id`, `timestamp`, `location`, `outcome` (`EVACUATED`, `STABILIZED`, `FIRST_AID_APPLIED`), `signatures`.
3. Anti-Collusion: Repeated pairs of victim-responder keys over short intervals trigger Sybil anomaly flags and do not confer cumulative reputation without coordinator confirmation.

## Consequences
- **Positive:** Unfalsifiable evidence of rescue operations for disaster analytics and volunteer commendations.
- **Trade-off:** In cases where victim devices are completely destroyed or dead, fallback coordinator witness signing is required.

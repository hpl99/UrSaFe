# ADR-008: Multi-Signal Behavioral Trust Engine & Sybil Anomaly Defense

## Status
Approved

## Context
In open wireless emergency meshes, malicious or rogue actors can create hundreds of phantom nodes (Sybil attack) to broadcast fake mass-casualty events, divert rescue ambulances away from real victims (lure relays), or flood radio channels. Trust cannot be a single binary boolean or simple numeric score.

## Decision
1. Decompose trust into distinct orthogonal vectors:
   - `Identity Trust`: Age of cryptographic key, verification against known identity anchors.
   - `Credential Trust`: Cryptographically signed W3C Verifiable Credentials issued by authorized agencies.
   - `Behavioral Trust`: Packet transmission frequency, route compliance, absence of broadcast flooding.
   - `Network Trust`: Observation and corroboration by geographically diverse radio neighbors.
   - `Rescue Reputation`: Historical dual-signed rescue completions.
2. The trust engine evaluates signals and categorizes nodes into:
   - `NORMAL`: Standard operating profile.
   - `SUSPICIOUS`: Minor anomalies; alerts coordinator; rate-limits routing priority.
   - `HIGH_RISK`: Significant anomalies (e.g. hundreds of keys originating from single radio MAC); isolates traffic.
   - `ISOLATED`: Blocked from mesh forwarding.

## Consequences
- **Positive:** Protects against mesh manipulation while still allowing spontaneous civilian volunteers to broadcast SOS calls.
- **Trade-off:** Heuristic anomaly detection requires tuning to prevent false positives during intense disaster spikes.

# ADR-007: Tamper-Evident Flight Recorder Cryptographic Hash Chains

## Status
Approved

## Context
Post-incident after-action reports, coroner inquiries, and relief auditing require tamper-evident proof of critical events: who called for help, when responders were notified, who accepted, and when units arrived. Simple application logs can be altered or erased by malicious or defensive actors. Full public blockchains are unusable due to bandwidth, latency, internet requirements, and privacy violations.

## Decision
1. Implement a lightweight local and distributed append-only Flight Recorder based on cryptographic hash chains.
2. Every significant state change produces an immutable audit record:
   - `event_id`: Unique identifier
   - `timestamp`: UTC timestamp
   - `previous_hash`: SHA-256 hash of the preceding event in the chain
   - `event_hash`: $\text{SHA256}(\text{event\_id} \parallel \text{timestamp} \parallel \text{previous\_hash} \parallel \text{actor} \parallel \text{action} \parallel \text{payload\_hash})$
   - `actor_signature`: Ed25519 signature of the committing actor
3. Chains are verified locally; any deletion, retro-dating, or alteration breaks cryptographic continuity immediately.

## Consequences
- **Positive:** Tamper-evident forensics with negligible CPU and zero token/gas cost. Runs 100% offline.
- **Trade-off:** Fork detection requires periodic peer cross-hash synchronization.

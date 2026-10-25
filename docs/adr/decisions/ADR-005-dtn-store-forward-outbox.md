# ADR-005: Delay-Tolerant Networking (DTN) Outbox & Data Mule Custody

## Status
Approved

## Context
When geographical obstacles or distance prevent simultaneous end-to-end radio paths between disaster sectors, continuous connected routing fails. Traditional networking protocols throw timeout errors and drop packets. In an emergency, packets must be retained on disk, carried across physical gaps by mobile vehicles/responders (data mules), and forwarded opportunistically.

## Decision
1. Implement a persistent Delay-Tolerant Outbox based on RFC 4838 principles.
2. Messages queued in the Outbox have:
   - Explicit Time-to-Live (`expires_at`)
   - Strict Priority Queuing (`EMERGENCY` > `HIGH` > `ROUTINE` > `TELEMETRY`)
   - Custody transfer acknowledgment semantics
   - Resumable state markers (`QUEUED`, `IN_FLIGHT`, `ACKNOWLEDGED`, `DELIVERED`, `EXPIRED`)
3. Data mules maintain local bundle custody caches. Upon peer discovery, nodes exchange compact Inventory Vectors (Bloom filter / message ID hash lists) and synchronize missing bundles.

## Consequences
- **Positive:** Enables inter-island communication without satellite or cellular links.
- **Trade-off:** High end-to-end latency (bounded by courier physical movement).

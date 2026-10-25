# ADR-001: Offline-First Architecture & Asynchronous Sync Engine

## Status
Approved

## Context
Standard emergency dispatch and mobile applications operate under an "online-first, offline-tolerant" assumption: when internet connectivity is severed, actions fail or block until the central cloud server becomes reachable. In major disasters, cellular networks and central infrastructure can remain destroyed for days or weeks. Emergency SOS signals, responder notifications, assignments, and acknowledgements cannot depend on an online server.

## Decision
1. Invert the dependency hierarchy: **Every device is an autonomous, self-sovereign node**.
2. All local state mutations (creating SOS, accepting missions, status transitions) write immediately to the local encrypted SQLite/Room database and are queued in a persistent Outbox.
3. The central cloud is an optional coordination and analytics node that acts as a peer in the replication graph, never a single point of failure.
4. Synchronization operates asynchronously: nodes emit and consume idempotent bundles across whichever transport is currently active (LoRa mesh, BLE, local Wi-Fi, or DTN data mules).

## Consequences
- **Positive:** Victims can trigger SOS and responders can accept missions even if the central server has completely burned down.
- **Trade-off:** Requires robust conflict-free replication (CRDTs), vector clocks, and asynchronous state convergence rather than simple relational database transactions.

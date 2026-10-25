# UrSafe Offline-First Synchronization & DTN Protocol

## 1. Delay-Tolerant Networking (DTN) Architecture

Disasters frequently destroy microwave towers and fiber backhauls, partitioning regions into isolated network islands. UrSafe implements an RFC 5050 / RFC 9171 inspired **Bundle Protocol & Data Mule Architecture**:

```text
[ Valley Alpha (Isolated) ]                 [ Valley Beta (Isolated) ]
 ├── Civilian SOS Beacon                     ├── Response Base Station
 └── Persisted in Local Room SQLite          └── Awaiting Field Reports
             │                                           ▲
             ▼ Custody Transfer                          │ Custody Delivery
      ┌─────────────────────────────────────────────────────┐
      │  DTN DATA MULE (All-Terrain Vehicle / First Responder)│
      │  - Physical transport across severed terrain        │
      │  - Stores cryptographic bundles in flash memory     │
      └─────────────────────────────────────────────────────┘
```

---

## 2. Durable Local Outbox Pattern (Section 38)

Messages, SOS beacons, and rescue reports are NEVER kept in ephemeral UI state or volatile JavaScript/Kotlin memory.

### Outbox Guarantees:
- **Write-Ahead Logging (WAL)**: All transactions are synchronously flushed to disk.
- **Process Death Resilience**: Survived OS task killing, battery exhaustion, and reboot.
- **Deduplication**: Every bundle is indexed by its SHA-256 content hash.
- **Expiration & TTL**: Stale requests are automatically retired after a configurable TTL (e.g., 72 hours).

---

## 3. Conflict-Free Replicated Data Types (CRDTs)

Replicas in partitioned sectors must merge state deterministically without a central coordinator:

| Subsystem | CRDT Primitive | Merge Rule |
|---|---|---|
| **Incident Status** | LWW-Register (Last-Write-Wins) | Highest timestamp wins; node ID string comparison breaks ties |
| **Active Responders** | ORSet (Observed-Removed Set) | Adds take precedence over removes with unique tag identifiers |
| **Tactical Chat** | G-Counter / Merkle DAG | Causal delivery ordering via Vector Clock parent hashes |

### Mathematical Convergence Proof:
Given replicas $A$ and $B$, for any two states $S_A$ and $S_B$:
$$Merge(S_A, S_B) = Merge(S_B, S_A) \quad (\text{Commutative})$$
$$Merge(Merge(S_A, S_B), S_C) = Merge(S_A, Merge(S_B, S_C)) \quad (\text{Associative})$$
$$Merge(S_A, S_A) = S_A \quad (\text{Idempotent})$$

Replicas can exchange updates in any order, over any transport (LoRa, BLE, USB flash drive, Internet), and always converge to the identical state.

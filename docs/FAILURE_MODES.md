# UrSafe Failure Modes & Recovery Matrix
## Production Reliability Analysis

---

| Failure ID | Failure Mode | Trigger / Condition | Impact | Engine Mitigation & Recovery Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **FAIL-001** | Process Termination Mid-Transmission | App force-killed or battery died during RF send | Message could be lost or permanently stuck in `TRANSMITTING` | On restart, `recoverOutboxOnBoot()` resets all in-flight messages to `RETRY_WAIT`. Retry loop resumes immediately with zero data loss. |
| **FAIL-002** | Total Internet / Cloud Outage | Cell towers destroyed; fiber cuts | Cloud REST endpoints return 503/timeout | Cockpit transitions to `OFFLINE_FIRST_MESH_ACTIVE`. Engine halts cloud retries and redirects all traffic to local BLE and Meshtastic LoRa bearers. |
| **FAIL-003** | Radio Disconnect / Serial Error | Meshtastic USB or BLE link severed | LoRa radio unavailable | Transport status marked `DISCONNECTED`. Fallback policy redirects traffic to Ad-Hoc Wi-Fi or queues in device SQLite storage until radio link reconnects. |
| **FAIL-004** | Duplicate Packet Flooding | Multiple mesh hops retransmit same packet | Potential duplicate incidents or state corruption | Inbound filter checks `continuity_deduplication`. Identical `message_id` returns idempotent receipt with zero state mutation. |
| **FAIL-005** | Delayed / Out-of-Order Packets | Slow multi-hop LoRa route delivers A, C, B | Potential rollback of emergency lifecycle | Causal vector clocks and 18-state FSM validation reject invalid backward transitions while preserving audit history. |
| **FAIL-006** | Battery Depletion (<= 15%) | Prolonged field operation without recharging | Device risks sudden shutdown | Battery preemption immediately defers P3-P5 background telemetry. Power is strictly reserved for P0 life-critical SOS dispatch. |
| **FAIL-007** | Network Partition (Split-Brain) | Physical barriers separate Sector A from HQ | Incidents isolated in local island | Local nodes continue local coordination. Upon contact with a Data Mule or link restoration, bundles synchronize and reconcile commutatively. |
| **FAIL-008** | Max Retry Exhaustion | Destination peer out of range across all bearers | Message cannot be confirmed | After reaching `max_attempts` (10 for P0, 5 for normal), message transitions to `DEAD_LETTER`. Retained in persistent store for manual commander review. |
| **FAIL-009** | Message TTL Expiration | Disaster scenario extends past 24-48 hours | Stale packets circulating in mesh | Expiration sweeper transitions message to `EXPIRED`. Stale packets are never resurrected or falsely acknowledged. |
| **FAIL-010** | Replay Attack / Malicious Packet | Rogue radio injects recorded past emergency | Unauthorized dispatch or resource waste | Packets must match valid Ed25519 signature, nonces, and unexpired creation timestamps. Replayed sequence numbers are rejected. |

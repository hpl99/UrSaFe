# UrSafe Connectivity Cockpit Specification
## Real-Time System Connectivity State, Diagnostics & Failure Injection

---

## 1. Principles
1. **Never Fake Connectivity**: The cockpit never reports `CONNECTED` based on mock variables. All status indicators derive from real observed bearer health, socket connections, and radio link metrics.
2. **Transparent Limitations**: If the cloud is offline, the cockpit explicitly communicates:
   > *"Internet unavailable. Cloud synchronization paused. Emergency mesh (LoRa/BLE) remains 100% operational."*
3. **No False Confidence**: The system distinguishes between packet transmission, mesh relay, and human responder acknowledgement.

---

## 2. Deterministic Connectivity Score
The score is computed using an objective formula rather than an arbitrary percentage:
$$\text{Score} = \left(\frac{\text{Active Transports}}{\text{Total Transports}} \times 50\right) + (\text{Mesh Reachable} \times 30) + \left(\frac{\text{Battery Reserve \%}}{100} \times 20\right)$$

- **Total Range**: 0 to 100.
- **Mesh Reachable**: Evaluates if either Meshtastic LoRa radio or BLE peer is connected and operational.
- **Battery Factor**: Scales from 0 to 20 points based on device power reserve.

---

## 3. Portal Presentations

### A. Citizen Portal (Victim)
- **Top Reassurance Card**: Explains offline durability clearly:
  > *"● Offline — Emergency Mesh Active: Your distress signal will be saved locally on this device and dispatched across all viable nearby communication paths."*
- **Active Path Pills**: Visual pills for BLE, LoRa, Wi-Fi, and Cloud.
- **Dynamic 10-Step Lifecycle Stepper**:
  1. Reported
  2. Stored locally in SQLite WAL
  3. Queued in priority outbox
  4. Radio Transmitting (BLE / 868MHz LoRa)
  5. Mesh Relay Node Receipt
  6. Responder Notified
  7. Mission Accepted by Responder
  8. Unit En Route (GPS Tracking)
  9. Unit Arrived on Scene
  10. Verified & Co-Signed

### B. Responder Portal
- **Tactical Bearer Link Diagnostics Card**: Exposes physical link metrics:
  - LoRa RSSI (dBm) and SNR (dB)
  - BLE 0xFFF0 GATT status
  - Outbox pending queue depth
  - Battery reserve percentage
  - Latency and roundtrip metrics

### C. Authority / Incident Commander Dashboard
- **System-Wide Connectivity Cockpit**:
  - Global Connectivity Score badge.
  - Active Transports cards with failure injection toggles (`Toggle Link (Failure Injection)`).
  - Outbox & Dead Letter Queue Table:
    - Lists priority, message ID, type, state, transport, attempts, status, and actions (`Retry`, `Cancel`).
    - Dedicated Dead Letter inspector for manual triage of exhausted messages.

---

## 4. Failure Injection & Chaos Testing
The cockpit provides an interactive testing mechanism for operators:
- Clicking **"Disconnect (Failure Injection)"** issues `POST /api/v1/continuity/transports/:id/status` with `{"status":"DISCONNECTED","link_quality":"OFFLINE"}`.
- The engine automatically recalculates the connectivity score, updates the human-readable summary, and redirects pending traffic to the next viable transport (e.g. falling back from BLE to LoRa or Data Mule).
- Reconnection restores score and resumes normal preference order.

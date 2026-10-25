# UrSafe Transport Architecture
## Multi-Bearer Physical & Network Layer Stack

---

## 1. Transport Hierarchy
UrSafe does not rely on any single physical communication bearer. The transport layer abstracts heterogeneous hardware into a common interface:

```text
                  +-----------------------------------+
                  |      Rescue Continuity Engine     |
                  +-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
     [Local Bearers]         [Radio Mesh]            [Wide Area]
            |                       |                       |
    +-------+-------+       +-------+-------+       +-------+-------+
    | BLE Transport |       | Meshtastic    |       | Wi-Fi Ad-Hoc  |
    | (0xFFF0 GATT) |       | LoRa (SX1262) |       | Local Subnet  |
    +---------------+       +---------------+       +---------------+
            |                       |                       |
    +---------------+       +---------------+       +---------------+
    | Data Mule     |       | Central Cloud |       | Simulated     |
    | Store-Carry   |       | (Cellular/ISP)|       | Harness (CI)  |
    +---------------+       +---------------+       +---------------+
```

---

## 2. Bearer Profiles & Constraints

| Bearer | Bandwidth | Typical Range | MTU / Payload Limit | Latency | Battery Cost | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BLE (0xFFF0)** | 1 - 2 Mbps | 10 - 50 meters | 512 bytes (GATT MTU) | 15 - 40 ms | Very Low | Phone-to-phone direct rescue |
| **Meshtastic LoRa** | 0.25 - 5.4 kbps | 2 - 15 km | ~168 bytes per frame | 100 - 600 ms | Low | Long-range off-grid disaster mesh |
| **Local Wi-Fi** | 54 - 300 Mbps | 50 - 150 meters | 1500 bytes (Ethernet) | 5 - 20 ms | Medium | Incident Command Post local cluster |
| **Data Mule** | Physical travel | Infinite | Unlimited | Minutes to hours | Zero RF | Partitioned island bridging |
| **Central Cloud** | Variable | Global | Unlimited | 50 - 500 ms | High | Backhaul reporting & sync |

---

## 3. Radio Packet Compliance & Fragmentation (Section 32)
1. **LoRa Constraints**:
   - The wire envelope conforms to Meshtastic LoRa binary constraints (~168 bytes).
   - Payloads exceeding 168 bytes are fragmented with headers: `(message_id, fragment_index, fragment_count, crc16)`.
   - Incomplete fragment sets are held in a bounded in-memory reassembly buffer with a 120-second timeout to prevent memory exhaustion.
2. **Duty-Cycle Compliance**:
   - Transmissions in the 868MHz band respect European ETSI 1% duty cycle limitations.
   - P0 messages utilize regulatory emergency burst allowances where applicable.

---

## 4. Policy-Based Transport Selection
The engine evaluates viable bearers using dynamic multi-factor scoring:
- For **P0 (Life Critical)**: Local Direct BLE -> Meshtastic LoRa -> Local Wi-Fi -> Central Cloud -> Data Mule.
- For **P5 (Telemetry)**: Central Cloud -> Local Wi-Fi -> BLE -> Meshtastic LoRa -> Data Mule.
- If device battery reserve drops below 15%, energy-intensive broad scans are throttled, and non-critical traffic is deferred.

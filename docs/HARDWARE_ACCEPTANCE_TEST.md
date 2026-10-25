# UrSafe Hardware Acceptance Test Plan
## Physical RF & Field Verification Protocols

---

## 1. Required Physical Equipment
1. **Device A (Victim)**: Android smartphone (Android 11+, Bluetooth 5.0+, USB-OTG).
2. **Device B (Responder)**: Android smartphone (Android 11+, Bluetooth 5.0+, USB-OTG).
3. **Radio Node A**: Heltec V3 / LilyGO T-Beam (Semtech SX1262 LoRa transceiver, 868MHz or 915MHz, Meshtastic firmware v2.3+).
4. **Radio Node B**: Heltec V3 / LilyGO T-Beam (Semtech SX1262 LoRa transceiver, matching frequency).
5. **Gateway / Command Node**: Stationary Meshtastic router node with high-gain omnidirectional antenna.

---

## 2. Test Procedures & Acceptance Criteria

### Test HW-01: Direct Phone-to-Phone BLE SOS
- **Environment**: Line-of-sight 15 meters, no Wi-Fi or cellular connectivity.
- **Action**: Device A triggers P0 SOS.
- **Expected**: Device B receives GATT notification on 0xFFF0 service; packet hash verified; Device A receives `NODE_ACK` within 250ms.
- **Status in CI/Local Dev**: `BLOCKED — PHYSICAL ANDROID HARDWARE REQUIRED`. Verified in software via simulated BLE transport adapter.

### Test HW-02: Multi-Kilometer LoRa RF Propagation
- **Environment**: Non-line-of-sight urban terrain (1.5 km distance, masonry obstructions).
- **Configuration**: 868.125 MHz, Bandwidth 250 kHz, Spreading Factor 11, Coding Rate 4/8, Tx Power +22 dBm.
- **Action**: Victim broadcasts SOS through Radio A.
- **Expected**: Radio B receives frame with $\text{RSSI} \ge -118\text{ dBm}$ and $\text{SNR} \ge -6.5\text{ dB}$. Packet decoded and acknowledged.
- **Status in CI/Local Dev**: `BLOCKED — PHYSICAL LORA HARDWARE REQUIRED`. Verified in software via Meshtastic adapter emulator.

### Test HW-03: Partition Traversal via Physical Data Mule
- **Setup**: Island A (Victim + Radio A) and Island B (HQ Command) separated by 10 km without RF link.
- **Action**: Responder with Device B visits Island A, receives SOS envelope into durable Room storage, travels to Island B, and uploads via `POST /api/v1/continuity/sync`.
- **Expected**: Island B reconciles SOS with zero data loss and verifies payload hash.
- **Status in CI/Local Dev**: `PASS (VERIFIED VIA AUTOMATED DATA MULE SUITE)`.

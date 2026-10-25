# UrSafe Bluetooth & Wireless Radio Engineering Specification

## 1. Core Reality: The Four Android Bluetooth States

A critical flaw in consumer emergency applications is conflating radio presence with application connectivity. Android documentation explicitly distinguishes four disjoint states:

```text
1. BLUETOOTH ENABLED
   └── Adapter is powered on and receiving RF, but not discoverable to peers.

2. DISCOVERABLE
   └── Adapter actively transmits inquiry scan responses (requires explicit user intent; times out in 120s).

3. PAIRED (BONDED)
   └── OS stores link encryption keys (LTK). Does NOT mean device is connected or in range!

4. CONNECTED
   └── Active L2CAP channel or GATT bearer open between host and peripheral.
```

**UrSafe Rule (Section 18):** Pairing is NEVER shown as "Connected". A device is only reported as `CONNECTED` when an active GATT connection is established and the application-level cryptographic handshake succeeds.

---

## 2. Bluetooth Device Categorization (Section 57)

The presence of generic Bluetooth devices (headphones, televisions, laptops) during an active scan is expected behavior. The UrSafe interface cleanly segregates discovered hardware into four distinct categories:

| Category | Filter Criteria | UI Presentation | Primary Transport |
|---|---|---|---|
| **1. Emergency Radios** | Advertises Nordic UART Service (`6E400001-...`) or Meshtastic ID | Displayed prominently at top with battery % and RSSI | BLE GATT / USB Serial |
| **2. UrSafe Mobile Peers** | Advertises UrSafe Custom Service UUID `0000FE26-0000-1000-8000-00805F9B34FB` | Highlighted with role pill (CITIZEN / RESPONDER) | BLE Direct Peer |
| **3. Paired Hardware** | Bonded in Android Bluetooth Settings | Listed under "Paired Radios" with connect button | Cached Bond |
| **4. Unrelated Hardware** | Audio devices, wearables, PCs | **Collapsed by default** under expandable toggle | None |

---

## 3. UrSafe Mobile-to-Mobile Discovery Protocol (Section 16)

When direct phone-to-phone discovery is required without an intermediate LoRa radio, UrSafe utilizes BLE Advertising with strict privacy safeguards.

### Advertising Packet Specification
- **Service UUID**: `0xFE26` (UrSafe Life-Safety Service)
- **Manufacturer Data**:
  - `Bytes 0-1`: 0x02FE (UrSafe Company Identifier)
  - `Bytes 2-5`: Pseudonymous Device Token (rotated every 15 minutes to prevent tracking)
  - `Byte 6`: Role Flag (`0x01` Citizen, `0x02` Tactical Responder, `0x03` Authority Node)
  - `Byte 7`: Emergency Status (`0x00` Normal, `0x01` Active Distress SOS)
  - `Byte 8`: RF Power Reference for RSSI distance approximation

> [!CAUTION]
> **Privacy Mandate:** No personal identification, real names, phone numbers, or medical records are ever included in BLE advertisement packets. Sensitive emergency data is only transmitted after authenticated cryptographic session establishment.

---

## 4. Meshtastic Companion Radio Protocol (Section 17)

The primary physical link between the Android field application and the Semtech SX1262 LoRa mesh is the Meshtastic Companion Protocol:

```text
[ Android App ]
      │
      ▼ BLE GATT or USB-CDC Serial (115200 baud)
[ Nordic UART Service ]
  ├── RX Characteristic: 6e400002-b5a3-f393-e0a9-e50e24dcca9e (Write Without Response)
  └── TX Characteristic: 6e400003-b5a3-f393-e0a9-e50e24dcca9e (Notify)
      │
      ▼
[ Meshtastic Radio Firmware (Heltec V3 / LilyGO T-Beam) ]
      │
      ▼ Semtech SX1262 / SX1276 RF Transceiver
[ 865 MHz IN / 915 MHz US LoRa Physical Layer ]
```

### Negotiated Parameters
- **MTU Size**: Requested 247 bytes (Payload data: 244 bytes per GATT chunk).
- **Connection Interval**: 15 ms (Fast initial exchange) -> 100 ms (Power conservation).
- **Supervision Timeout**: 4,000 ms (Triggers automatic reconnection retry).

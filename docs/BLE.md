# UrSafe Bluetooth Low Energy (BLE) Specification & Architecture

## 1. Overview

UrSafe defines a custom BLE Application Profile enabling peer-to-peer discovery, encrypted communication, and presence detection between phones and hardware radios without requiring pre-existing cellular connectivity.

---

## 2. UrSafe Service Definition

- **Primary Service UUID**: `0000FE26-0000-1000-8000-00805F9B34FB` (16-bit alias: `0xFE26`)
- **Nordic UART LoRa Fallback**: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`

### GATT Characteristics

| Characteristic | UUID | Properties | Description |
| :--- | :--- | :--- | :--- |
| `DEVICE_INFO` | `0000FE27-...` | Read | Device ID, model, firmware, protocol version (`v1`) |
| `PAIRING_AUTH` | `0000FE28-...` | Write, Read | Mutual cryptographic handshake & session key exchange |
| `HEARTBEAT` | `0000FE29-...` | Notify, Write | Telemetry (RSSI dBm, battery %, presence status) |
| `EMERGENCY_SYNC` | `0000FE2A-...` | Write, Notify | P0 life-safety incident packet exchange |
| `LOCATION_EXCHANGE`| `0000FE2B-...` | Read, Notify | Authorized WGS84 GPS coordinates (`lat`, `lon`, `acc`) |
| `OUTBOX_SYNC` | `0000FE2C-...` | Write, Notify | Durable offline outbox bundle synchronization |

---

## 3. Peripheral Advertising Payload

UrSafe devices in advertising mode transmit a compact, privacy-preserving advertisement:

```text
Field 1: Flags (LE General Discoverable Mode)
Field 2: Complete 16-bit Service UUIDs: 0xFE26
Field 3: Service Data:
  - Protocol Version: 0x01
  - Device Short ID: e.g. 0x7F3A ("URSAFE-7F3A")
  - Role: CITIZEN (0x01), RESPONDER (0x02), AUTHORITY (0x03)
  - Capabilities: SOS | LOCATION | SYNC (Bitmask)
  - Ephemeral Session ID: 4 bytes
```

> **Privacy Rule**: Full names, medical notes, phone numbers, and emergency descriptions are **NEVER** broadcasted in unencrypted BLE advertisements.

---

## 4. Categorized Scanner Architecture

The device discovery engine classifies detected devices into three categories:

1. **Nearby UrSafe Nodes**: Recognized peers broadcasting UrSafe Service `0xFE26` with UrSafe protocol v1. Eligible for direct peer connection.
2. **Compatible Hardware Radios**: LoRa transceivers (Heltec V3, Meshtastic T-Beam) communicating over Nordic UART Service or USB-CDC Serial.
3. **Other Bluetooth Peripherals**: Commercial devices (headphones, laptops, keyboards) detected during scanning but labeled explicitly as **"Not compatible with UrSafe protocol"**.

---

## 5. Connected Peer Presence & Map Synchronization

When two UrSafe nodes establish an authenticated session:
1. The **CONNECTED URSAFE USER** card activates immediately:
   - Displays peer name, role badge, BLE CONNECTED status
   - Live RSSI (e.g. `-61 dBm`), battery percentage (e.g. `74%`), and heartbeat timer
2. If location sharing is authorized, the peer's exact coordinates update the local database.
3. A cyan device marker is rendered on the real WGS84 Leaflet map at the peer's actual coordinates.
4. Heartbeat packets are exchanged every 10 seconds. Disconnection cleans up the UI and resets map presence.

---

## 6. Android 12+ Runtime Permissions

UrSafe explicitly handles modern Android Bluetooth permission requirements:
- `android.permission.BLUETOOTH_SCAN`: Scanning without location lookup (`neverForLocation` flag where applicable)
- `android.permission.BLUETOOTH_CONNECT`: Connecting to paired or discovered devices
- `android.permission.BLUETOOTH_ADVERTISE`: Advertising as an UrSafe peripheral beacon

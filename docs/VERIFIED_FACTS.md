# UrSafe / Cascade26 Emergency Mesh — Verified Facts (docs/VERIFIED_FACTS.md)

**Date:** 2026-10-26  
**Status:** Canonical Engineering Ground Truth  
**Rule:** Every constant, UUID, and parameter must be verified from primary official sources with citations. Unverified items must be explicitly marked `NOT VERIFIED`.

---

## 1. Meshtastic BLE Service & Characteristic UUIDs

### Primary Communication Service: `MeshBluetoothService`
* **Status:** **VERIFIED**
* **Service UUID:** `6ba1b218-15a8-461f-9fa8-5dcae273eafd`
* **Official Source:** [Meshtastic BLE Client API Documentation](https://meshtastic.org/docs/development/device/client-api/ble-client-api/) and [Meshtastic Android Repository](https://github.com/meshtastic/Meshtastic-Android).
* **Role:** The primary Bluetooth Low Energy service exposed by Meshtastic firmware for radio control, session synchronization, and packet I/O via Protocol Buffers.
* **Characteristics under `MeshBluetoothService`:**
  1. **`ToRadio` Characteristic:**
     * **UUID:** `f75c76d2-129e-4dad-a1dd-7866124401e7`
     * **Properties:** Write (`PROPERTY_WRITE`, `PROPERTY_WRITE_NO_RESPONSE`)
     * **Function:** Used by client applications to transmit serialized `ToRadio` protobuf packets to the radio node.
  2. **`FromRadio` Characteristic:**
     * **UUID:** `2c55e69e-4993-11ed-b878-0242ac120002`
     * **Properties:** Read (`PROPERTY_READ`)
     * **Function:** Used by client applications to read incoming serialized `FromRadio` protobuf packets from the radio queue. Clients read iteratively until an empty payload is returned.
  3. **`FromNum` Characteristic:**
     * **UUID:** `ed9da18c-a800-4f66-a670-aa7547e34453`
     * **Properties:** Notify (`PROPERTY_NOTIFY`)
     * **Function:** Signals to the client via BLE notification that new packets have arrived in the radio's `FromRadio` buffer, indicating a read is ready.

### Disambiguation Note: Why `cb0b9a0b-a84c-4c0d-bdbb-442e3144ee30` Appeared in Prior Audits
* **UUID:** `cb0b9a0b-a84c-4c0d-bdbb-442e3144ee30` is **NOT** the radio communication service.
* It is the Meshtastic **`SoftwareUpdateService`**, used exclusively for device firmware over-the-air (OTA) updates and MCU flashing routines. It must **not** be used for emergency message transport.

---

## 2. Meshtastic Payload Size Constraints & Airtime

* **Status:** **VERIFIED**
* **Official Source:** [Meshtastic Architecture Overview](https://meshtastic.org/docs/overview/mesh-algo/) and Semtech SX1262 LoRa PHY Specification.
* **Maximum PHY Packet Size:** **255 bytes** (absolute physical maximum supported by Semtech SX1262/SX1276 transceivers).
* **Header & Transport Overhead:**
  * Mesh Packet Header: ~16 bytes (Sender node ID, Packet ID, Flags, Channel Hash, Next-hop, Relay Node).
  * Payload CRC: 2 bytes.
* **Maximum Usable Application Payload:** **237 bytes** (`Constants.DATA_PAYLOAD_LEN = 237`).
* **Client App Text Limit:** **200 bytes** (`Constants.MAX_TEXT_LEN = 200` enforced in official Meshtastic Android / iOS clients).
* **Recommended Practical Size for Emergency Beacons:**
  * For P0 Life-Critical SOS beacons operating on `LongFast` / `LongModerate`, the payload must be kept **under 64–100 bytes**.
  * **Airtime Reasoning:** Because Time-on-Air (ToA) scales directly with byte length, smaller packets dramatically reduce channel occupancy, prevent packet collisions on uncoordinated CSMA channels, and improve delivery probability across multi-hop relays.

---

## 3. India Regional Configuration: `IN_865`

* **Status:** **VERIFIED**
* **Official Source:** [Meshtastic Radio Configuration](https://meshtastic.org/docs/configuration/radio/lora/) and Ministry of Communications, Government of India (G.S.R. 564(E) unlicensed 865–867 MHz band).
* **Region Code:** `IN_865` (or `IN` in newer firmware profile definitions).
* **Frequency Range:** **865.0 MHz to 867.0 MHz**.
* **Default Preset:** `LongFast` (Bandwidth 250 kHz, Spreading Factor 11, Coding Rate 4/5).
* **Frequency Slot:** Meshtastic calculates frequency slot `0` dynamically from the primary channel name hash (`LongFast`).
* **Maximum Transmit Power Limit:** Up to 30 dBm (1 Watt) ERP.
* **Wording Compliance:** Transmitting on US915 (902–928 MHz) or EU868 (868 MHz) is **not the correct region for India** and will not communicate with India-configured Meshtastic emergency nodes.

---

## 4. Meshtastic Port Numbers & Private Channel Carrying Strategy

* **Status:** **VERIFIED**
* **Official Source:** [meshtastic/protobufs portnums.proto](https://github.com/meshtastic/protobufs/blob/master/meshtastic/portnums.proto).
* **Port Numbers:**
  * `TEXT_MESSAGE_APP = 1`: Standard cleartext UTF-8 messages (range `0–63` for core system apps).
  * `ATAK_PLUGIN = 72` (and `ATAK_PLUGIN_V2 = 78`): Android Team Awareness Kit payloads (range `64–127` for registered 3rd-party apps).
  * `PRIVATE_APP = 256`: Reserved for custom application payloads (range `256–511` for private applications).
* **Application Port Selection for UrSafe:**
  * UrSafe P0 Tier 1 Beacons and Tier 2 Envelopes must use **`PortNum.PRIVATE_APP (256)`**.
* **Channel & Encryption Architecture:**
  * Default Channel 0 (`LongFast`) uses the well-known public PSK `1` (`AQ==`), meaning cleartext messages can be decrypted by any receiver within RF range.
  * Meshtastic routers forward packets based on the cleartext outer header and 8-bit channel hash, regardless of whether the routing node possesses the channel decryption key.
  * **Architectural Decision:** UrSafe emergency traffic must be carried on a **dedicated UrSafe secondary channel** configured with a non-default 256-bit AES PSK. Standard third-party Meshtastic nodes in the region will relay the packets as blind hops without being able to read personal or medical details.

---

## 5. Android Keystore & Ed25519 Support

* **Status:** **VERIFIED**
* **Official Source:** [Android Developers AndroidKeyStore Documentation](https://developer.android.com/reference/java/security/KeyPairGenerator) and [Android 13 API 33 Changes](https://developer.android.com/about/versions/13/features).
* **Native Keystore Ed25519 Support:**
  * Hardware-backed Ed25519 (`EdDSA`) in `AndroidKeyStore` was introduced in **Android 13 (API level 33)**.
* **Project Status (`minSdk = 26`):**
  * Our project's `minSdk` is **26** (Android 8.0 Oreo). Therefore, devices running Android 8.0 through 12.1 (API 26–32) **cannot** generate or sign with Ed25519 keys directly inside `AndroidKeyStore`.
* **Standard Verified Fallback Strategy:**
  1. **Dual-Path Strategy:**
     * **API $\ge$ 33:** Generate and store Ed25519 keypair directly inside `AndroidKeyStore` with `KeyGenParameterSpec.Builder("ursafe_beacon_key", KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY).build()`.
     * **API 26–32 Fallback:** Generate Ed25519 keypair in software (using Bouncy Castle, Tink, or libsodium), and encrypt the private key at rest using an AES-256-GCM key managed by `AndroidKeyStore` (`MasterKey` via `androidx.security.crypto.EncryptedSharedPreferences`).
  2. **ECDSA Alternative:**
     * If hardware-backed signing is strictly mandated on all devices $\ge$ API 26 without software key derivation, the fallback algorithm is `EC` with curve `secp256r1` (`SHA256withECDSA`), which has been native to `AndroidKeyStore` since API 18. Both Ed25519 and ECDSA P-256 produce 64-byte signatures.

---

## 6. Summary of Verified Constants for Code Implementation

| Entity | Verified Value | Purpose |
| :--- | :--- | :--- |
| **BLE Service UUID** | `6ba1b218-15a8-461f-9fa8-5dcae273eafd` | Meshtastic radio BLE connection |
| **BLE `ToRadio` Characteristic** | `f75c76d2-129e-4dad-a1dd-7866124401e7` | Send protobufs to radio |
| **BLE `FromRadio` Characteristic** | `2c55e69e-4993-11ed-b878-0242ac120002` | Read protobufs from radio |
| **BLE `FromNum` Characteristic** | `ed9da18c-a800-4f66-a670-aa7547e34453` | Notification of pending radio packets |
| **Meshtastic Application Port** | `256` (`PRIVATE_APP`) | Custom UrSafe beacon & envelope packets |
| **Radio Regulatory Region** | `IN_865` | Frequency 865.0–867.0 MHz |
| **Max Physical Payload** | `237 bytes` | Maximum LoRa wire payload budget |
| **Recommended P0 Beacon Size** | `\le 64–96 bytes` | Minimal Time-on-Air (ToA) for multi-hop resilience |
| **Android Keystore Ed25519 Min API** | `API 33` | Native hardware signing; fallback to AES-wrapped on API 26–32 |

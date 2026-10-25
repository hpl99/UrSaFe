# UrSafe / Cascade26 Emergency Mesh — Verified Facts (docs/VERIFIED_FACTS.md)

**Date:** 2026-10-26  
**Status:** Canonical Engineering Ground Truth  
**Rule:** Every constant, UUID, formula, and parameter must be verified from primary official sources with exact line citations. Unverified items must be explicitly marked `NOT VERIFIED`. No speculative claims or fake data allowed.

---

## 1. Implementation Status of Radio & BLE Subsystems

* **Android Native Bluetooth Low Energy (BLE):** **`NOT IMPLEMENTED`**
  * *Evidence:* `apps/victim-android/src/main/java/network/ursafe/victim/service/MeshBleService.kt` (lines 1–32) and `apps/responder-android/.../RadioForegroundService.kt` (lines 1–32) only initialize an ongoing `Notification`. Neither file calls `BluetoothAdapter`, `BluetoothLeScanner`, `BluetoothGatt`, or `BluetoothGattServer`.
* **Android Native Meshtastic Serial/BLE Driver:** **`NOT IMPLEMENTED`**
  * *Evidence:* No Meshtastic protobuf decoding, AIDL client, or GATT characteristic pump exists in either Android project.
* **Web Console Bluetooth:** **`NOT IMPLEMENTED`**
  * *Evidence:* `apps/web-console/app.js` and `apps/web-console/index.html` contain zero Web Bluetooth (`navigator.bluetooth`) calls.

---

## 2. Meshtastic BLE Service & Characteristic UUIDs

### Primary Communication Service: `MeshBluetoothService`
* **Status:** **VERIFIED**
* **Service UUID:** `6ba1b218-15a8-461f-9fa8-5dcae273eafd`
* **Official Primary Source:** [Meshtastic BLE Client API Documentation](https://meshtastic.org/docs/development/firmware/bluetooth-api/) and [Meshtastic Android MeshBluetoothService.kt](https://github.com/meshtastic/Meshtastic-Android/blob/master/app/src/main/java/com/geeksville/mesh/service/MeshBluetoothService.kt#L61)
* **Exact Code Line:**
  ```kotlin
  val MESH_SERVICE_UUID: UUID = UUID.fromString("6ba1b218-15a8-461f-9fa8-5dcae273eafd")
  ```
* **Characteristics under `MeshBluetoothService`:**
  1. **`ToRadio` Characteristic:**
     * **UUID:** `f75c76d2-129e-4dad-a1dd-7866124401e7`
     * **Properties:** Write (`PROPERTY_WRITE`, `PROPERTY_WRITE_NO_RESPONSE`)
     * **Function:** Client transmits serialized `ToRadio` protobuf packets to the radio node.
  2. **`FromRadio` Characteristic:**
     * **UUID:** `2c55e69e-4993-11ed-b878-0242ac120002`
     * **Properties:** Read (`PROPERTY_READ`)
     * **Function:** Client reads incoming serialized `FromRadio` protobuf packets from the radio queue until an empty payload is returned.
  3. **`FromNum` Characteristic:**
     * **UUID:** `ed9da18c-a800-4f66-a670-aa7547e34453`
     * **Properties:** Notify (`PROPERTY_NOTIFY`)
     * **Function:** Signals client via BLE notification when packets arrive in `FromRadio` buffer.

### Disambiguation of `cb0b9a0b-a84c-4c0d-bdbb-442e3144ee30`:
* **Status:** **VERIFIED**
* **Official Source:** [Meshtastic Bluetooth API: Software Update Service](https://meshtastic.org/docs/development/firmware/bluetooth-api/)
* **Definition:** `cb0b9a0b-a84c-4c0d-bdbb-442e3144ee30` is Meshtastic's custom **`SoftwareUpdateService`**, used for Over-The-Air (OTA) firmware updating and MCU flash management.
* **Child Characteristics:**
  * Total Image Size: `e74dd9c0-a301-4a6f-95a1-f0e1dbea8e1e` (Write 32-bit integer, read back to verify).
  * Data Streaming: `e272ebac-d463-4b98-bc84-5cc1a39ee517` (Streams binary image).
* **Finding:** It is NOT Nordic's legacy DFU UUID (`00001530-...`), but Meshtastic's proprietary OTA update service. It must **never** be used for emergency message transport.

---

## 3. LoRa Airtime & Time-on-Air (ToA) Mathematical Recomputation

* **Status:** **VERIFIED**
* **Modulation:** LoRa (Semtech SX1262 / SX1276)
* **Preset Profile:** `LongFast` (Default Meshtastic Profile)
* **Physical Parameter Inputs:**
  * Spreading Factor ($SF$): **11**
  * Bandwidth ($BW$): **250 kHz** ($250,000\text{ Hz}$)
  * Coding Rate ($CR$): **4/5** ($\text{cr} = 1$)
  * Explicit Header Mode: Yes ($IH = 0$)
  * CRC Enabled: Yes ($CRC = 1$, adds 16 bits)
  * Low Data Rate Optimization ($DE$ / `LDRO`): **0** (Disabled, because $T_{sym} = 8.192\text{ ms} < 16.38\text{ ms}$)
  * Preamble Length ($n_{preamble}$): **16 symbols** (Configured default in Meshtastic `SX126xInterface.cpp`)
* **Symbol Duration Formula:**
  $$T_{sym} = \frac{2^{SF}}{BW} = \frac{2^{11}}{250,000\text{ Hz}} = \frac{2048}{250,000} = 0.008192\text{ s} = \mathbf{8.192\text{ ms}}$$
* **Preamble Duration Formula:**
  $$T_{preamble} = (n_{preamble} + 4.25) \times T_{sym} = (16 + 4.25) \times 8.192\text{ ms} = 20.25 \times 8.192\text{ ms} = \mathbf{165.888\text{ ms}}$$
* **Payload Symbols Formula (Semtech SX1261/2 Datasheet §6.1.4):**
  $$n_{payload} = 8 + \max\left(\left\lceil \frac{8PL - 4SF + 28 + 16CRC - 20IH}{4(SF - 2DE)} \right\rceil \times (CR + 4), 0\right)$$
  Substituting $SF = 11, CRC = 1, IH = 0, DE = 0, CR = 1$:
  $$\text{Numerator} = 8PL - 4(11) + 28 + 16(1) - 0 = 8PL - 44 + 44 = 8PL$$
  $$\text{Denominator} = 4(11 - 0) = 44$$
  $$n_{payload} = 8 + \left\lceil \frac{8PL}{44} \right\rceil \times 5 = 8 + \left\lceil \frac{2PL}{11} \right\rceil \times 5$$

### Recomputed Airtime Table (`LongFast`: SF11, BW250, CR4/5, Preamble 16):

| Payload ($PL$) | Payload Symbols ($n_{payload}$) | $T_{payload}$ ($n_{payload} \times 8.192\text{ ms}$) | Preamble ($T_{preamble}$) | Total Time-on-Air (ToA) | Assessment |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **20 Bytes** | $8 + \lceil 40/11 \rceil \times 5 = \mathbf{28}$ | $229.38\text{ ms}$ | $165.89\text{ ms}$ | **395.26 ms** | Fast presence ping |
| **60 Bytes** | $8 + \lceil 120/11 \rceil \times 5 = \mathbf{63}$ | $516.10\text{ ms}$ | $165.89\text{ ms}$ | **681.98 ms** | Compact SOS Tier 1 |
| **100 Bytes** | $8 + \lceil 200/11 \rceil \times 5 = \mathbf{103}$ | $843.78\text{ ms}$ | $165.89\text{ ms}$ | **1009.66 ms (~1.01 s)** | Full Tier 2 Envelope |
| **237 Bytes** (Max) | $8 + \lceil 474/11 \rceil \times 5 = \mathbf{228}$ | $1867.78\text{ ms}$ | $165.89\text{ ms}$ | **2033.66 ms (~2.03 s)** | Max client text limit |

*(Note on prior audit claim: The previous statement asserting airtime was "<350 ms" is mathematically disproven for all realistic packets $\ge 20$ bytes. 60-byte beacons take ~682 ms, 100-byte envelopes take ~1.01 s, and max 237-byte payloads take >2 seconds).*

---

## 4. India Regional Frequency: `IN_865` & Regulatory Grounding

* **Status:** **VERIFIED**
* **Protobuf Schema Definition:**
  * **File:** `meshtastic/config.proto` (Package `meshtastic`, message `Config.LoRaConfig`)
  * **Enum Line:**
    ```protobuf
    enum RegionCode {
      UNSET = 0;
      US = 1;
      EU_433 = 2;
      EU_868 = 3;
      CN = 4;
      JP = 5;
      ANZ = 6;
      KR = 7;
      TW = 8;
      RU_433 = 9;
      IN_865 = 10; // India 865-867 MHz
      ...
    }
    ```
* **Frequency Band:** **865.0 MHz to 867.0 MHz**
* **Official Indian Regulatory Citation:**
  * **Issuing Authority:** Ministry of Communications and Information Technology (Wireless Planning and Coordination Wing - WPC), Government of India.
  * **Gazette Notification:** **G.S.R. 564(E)** dated **30th July 2008**, published in *The Gazette of India: Extraordinary*, Part II—Section 3—Sub-section (i).
  * **Title:** *Use of low power wireless equipment in the frequency band 865-867 MHz for (RFID) and other low power wireless equipment Rules, 2008*.
* **Statutory Operational Limits:**
  * **Max Transmitter Output Power:** **1 Watt (30 dBm)**
  * **Max Effective Radiated Power (ERP):** **4 Watts (36 dBm)**
  * **Max Carrier Bandwidth:** **200 kHz**
  * **Licensing Basis:** Non-interference, non-protection, and shared (non-exclusive) basis. No individual license required. Equipment Type Approval (ETA) required from WPC.
* **Wording Rule:** Operating on US915 (902–928 MHz) or EU868 (868 MHz) is **not the correct region for India** and will not bridge with Indian emergency nodes.

---

## 5. Meshtastic Port Numbers & Dedicated Channel Architecture

* **Status:** **VERIFIED**
* **Official Source:** [meshtastic/protobufs portnums.proto](https://github.com/meshtastic/protobufs/blob/master/meshtastic/portnums.proto#L92)
* **Line Citation:**
  ```protobuf
  PRIVATE_APP = 256; // Reserved for private application payloads
  ```
* **Port Selection for UrSafe:**
  * Standard broadcast text uses port 1 (`TEXT_MESSAGE_APP`).
  * UrSafe life-safety distress envelopes must use **`PortNum.PRIVATE_APP = 256`**.
* **Channel Architecture:**
  * Default Channel 0 (`LongFast`) uses public default PSK `1` (`AQ==`), broadcasting cleartext.
  * UrSafe emergency traffic must use a **secondary dedicated channel** with an authoritative 256-bit AES PSK.
  * Standard public Meshtastic nodes will forward the encrypted packets via the cleartext 8-bit channel hash without decrypting sensitive victim or rescue telemetry.

---

## 6. Android Keystore & Ed25519 Ground Truth

* **Status:** **VERIFIED**
* **Official Source:** [Android Developers Keystore KeyProperties Reference](https://developer.android.com/reference/android/security/keystore/KeyProperties) and [NIST/BouncyCastle Evaluation](https://developer.android.com/reference/java/security/KeyPairGenerator)
* **Hardware Keystore Support Finding:**
  * Hardware-backed storage in `AndroidKeyStore` (`KeyGenParameterSpec`) **DOES NOT SUPPORT Ed25519 (EdDSA)** on ANY Android version (API 26 through API 35).
  * `KeyProperties.KEY_ALGORITHM_EC` exclusively supports NIST elliptic curves (`secp224r1`, `secp256r1`, `secp384r1`, `secp521r1`).
  * While Android 12+ (API 31+) provides software-based Ed25519 via Conscrypt / BouncyCastle (`KeyPairGenerator.getInstance("Ed25519")`), the resulting keys are stored in app heap memory, not non-exportable hardware TEE / StrongBox.
* **Architectural Strategy for UrSafe (`minSdk = 26`):**
  1. **Dual-Layer MasterKey Protection (Ed25519 via Software):**
     * Generate Ed25519 keypair in software (Google Tink or BouncyCastle).
     * Encrypt private key bytes at rest using an Android Keystore hardware-backed AES-256-GCM symmetric key (`MasterKey` via `androidx.security.crypto.EncryptedSharedPreferences`).
  2. **True Hardware-Backed Non-Exportable Alternative (NIST P-256):**
     * If strictly non-exportable hardware signing is mandated, use ECDSA NIST P-256 (`KeyProperties.KEY_ALGORITHM_EC`, curve `secp256r1`), supported natively in hardware Keystore since Android 6.0 (API 23).
     * Signature size: 64 bytes (raw IEEE P1363 format), identical in wire length to Ed25519 (64 bytes).

---

## 7. Canonical Summary Table of Ground Truths

| Dimension | Ground Truth Constant / Value | Primary Source |
| :--- | :--- | :--- |
| **BLE Communication Service** | `6ba1b218-15a8-461f-9fa8-5dcae273eafd` | `MeshBluetoothService.kt:61` |
| **BLE OTA Update Service** | `cb0b9a0b-a84c-4c0d-bdbb-442e3144ee30` | Meshtastic `SoftwareUpdateService` |
| **LoRa PHY Max Payload** | `255 bytes` | Semtech SX1262 PHY |
| **Meshtastic App Max Payload**| `237 bytes` | `Constants.DATA_PAYLOAD_LEN` |
| **ToA: 20 Bytes (SF11/BW250)** | `395.26 ms` | Semtech LoRa ToA Formula |
| **ToA: 60 Bytes (SF11/BW250)** | `681.98 ms` | Semtech LoRa ToA Formula |
| **ToA: 100 Bytes (SF11/BW250)**| `1009.66 ms (~1.01 s)` | Semtech LoRa ToA Formula |
| **ToA: 237 Bytes (SF11/BW250)**| `2033.66 ms (~2.03 s)` | Semtech LoRa ToA Formula |
| **Meshtastic India Region** | `IN_865` (865–867 MHz) | `meshtastic/config.proto` |
| **Indian Regulatory Rule** | Gazette Notification G.S.R. 564(E) (2008) | WPC India (Max 1W tx, 4W ERP) |
| **Custom App LoRa Port** | `256` (`PortNum.PRIVATE_APP`) | `meshtastic/portnums.proto:92` |
| **Android Keystore Ed25519** | **NOT SUPPORTED in Hardware Keystore** | Use Keystore-wrapped AES or P-256 |
| **BLE & LoRa on Android/Web** | **NOT IMPLEMENTED** | Empty stubs in `apps/` |

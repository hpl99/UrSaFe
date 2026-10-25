# UrSafe Hardware Testing & Acceptance Runbook

## 1. Supported Physical Hardware Targets

| Hardware Device | Microcontroller | RF Transceiver | Frequency Bands | Companion Link |
|---|---|---|---|---|
| **Heltec WiFi LoRa 32 V3** | ESP32-S3 (Dual Core 240MHz) | Semtech SX1262 | 865 MHz IN, 915 MHz US | BLE 5.0 / USB-C |
| **LilyGO T-Beam Supreme** | ESP32-S3 | Semtech SX1262 + GNSS | 865 MHz IN, 915 MHz US | BLE 5.0 / USB-C |
| **RAK Wireless WisBlock 4631** | Nordic nRF52840 | Semtech SX1262 | 865 MHz IN, 433 MHz EU | BLE 5.0 / Low Power |

---

## 2. 23-Step Hardware Acceptance Procedure (Section 45)

Execute this mandatory test suite before releasing any firmware or client build:

1. **Adapter Disabled**: Turn off Bluetooth on the Android test device.
2. **State Detection**: App immediately renders `BLUETOOTH DISABLED` banner.
3. **User Guidance**: Tapping "Enable Bluetooth" prompts system adapter activation.
4. **Permission Denial**: Deny `BLUETOOTH_SCAN` in system dialog.
5. **Permission Education**: App displays rationale card explaining why life-safety scanning is required.
6. **Permission Grant**: Re-open settings and grant `BLUETOOTH_SCAN` and `BLUETOOTH_CONNECT`.
7. **Scan Initiation**: Tap "Scan Bluetooth Radios" in Connection Center.
8. **Radio Discovery**: Real Heltec V3 appears with radio icon and hardware tag.
9. **Name & Identity**: Device name matches `URSAFE-RADIO-01` or `Meshtastic-XXXX`.
10. **Device Classification**: Radio appears in "Compatible Radios" group, NOT generic audio.
11. **Pairing Handshake**: System prompts pairing bond; link keys exchanged.
12. **GATT Connection**: L2CAP channel opens; Nordic UART Service discovered.
13. **State Transition**: UI flips from `PAIRED` to `● CONNECTED`.
14. **UrSafe Identity Handshake**: Device public key exchanged and verified.
15. **Ready State**: UI displays `● READY` badge with negotiated MTU (247 bytes).
16. **Telemetry Stream**: RSSI updates (e.g. `-65 dBm`), battery % updates (`91%`).
17. **Intentional Disconnect**: Power off the Heltec radio.
18. **Disconnect Detection**: UI detects GATT link loss within 4 seconds; transitions to `DISCONNECTED`.
19. **Auto-Reconnect**: Power the radio back on; client automatically reconnects without user intervention.
20. **Outbox Transmission**: Send an SOS message; packet is transmitted over LoRa RF.
21. **Inbound Reception**: Second test device receives packet over RF and triggers notification.
22. **App Process Death**: Force-stop application via Android settings; restart app; bond and outbox state remain intact.
23. **Background Execution**: Lock device screen for 10 minutes; radio connection persists via Foreground Service.

---

## 3. Mobile-to-Mobile Direct BLE Acceptance Test (Section 46)

For testing phone-to-phone direct peer links without an external radio:

```text
[ Phone A: Citizen ]                        [ Phone B: Tactical Responder ]
 ├── Advertises UrSafe UUID 0xFE26          ├── Listens with BLE Scanner
 └── Role: CITIZEN (USR-CIT-01)             └── Discovers Phone A as Available Citizen
             │                                           ▲
             └──────── Cryptographic Peer Handshake ─────┘
                                  │
                       Authenticated Session
                                  ▼
             Emergency SOS Packet delivered directly via BLE GATT
             Received on Phone B with audible notification alert
```

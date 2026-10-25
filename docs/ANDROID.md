# UrSafe Android Native Application Architecture

## 1. Architectural Principles

UrSafe's Android applications (`apps/victim-android` and `apps/responder-android`) are built in strict accordance with modern **Android Architecture Guidance** (Layered Architecture, Unidirectional Data Flow):

```text
[ Composable UI Screen ]
          │  ▲
   User   │  │ Immutable
   Intent │  │ StateFlow<UiState>
          ▼  │
   [ ViewModel ]
          │  ▲
  Execute │  │ Coroutines Flow
  Use Case│  │ 
          ▼  │
   [ EmergencyRepository ]
          │  ▲
   SQLite │  │ BLE Packets
   Queries│  │ / Network
          ▼  │
   [ Room DAO / Local Store ] ─── [ MeshBleService (Foreground) ]
```

---

## 2. Android Runtime Permissions Matrix (Android 12+ / 14+)

To operate reliably without crashes or security exceptions on modern Android devices, UrSafe declares and requests the following runtime permissions:

| Permission | API Level | Purpose | Graceful Degradation Strategy |
|---|---|---|---|
| `BLUETOOTH_SCAN` | API 31+ | Scanning for Meshtastic radios and mobile peers | Guides user to grant permission; falls back to USB Serial CDC |
| `BLUETOOTH_CONNECT` | API 31+ | Establishing GATT connection and reading RSSI/battery | Warns user that wireless mesh hardware cannot be linked |
| `ACCESS_FINE_LOCATION` | API 23+ | Acquiring high-precision GNSS fix for SOS distress beacon | Uses cell/Wi-Fi coarse location; clearly labels accuracy |
| `POST_NOTIFICATIONS` | API 33+ | Alerting responders to critical emergency assignments | In-app alerts remain active; banners shown when opened |
| `FOREGROUND_SERVICE_CONNECTED_DEVICE` | API 34+ | Maintaining persistent BLE GATT companion link | Notifies user if Android battery optimization terminates link |

---

## 3. Background Execution & Foreground Services (Section 21)

Android power-saving mechanisms (Doze mode, App Standby buckets) will terminate ordinary background threads. For an emergency life-safety platform, radio connectivity must be preserved while the screen is off.

### Solution: `ConnectedDevice` Foreground Service
- **Service Name**: `network.ursafe.victim.service.MeshBleService` / `network.ursafe.responder.service.RadioForegroundService`
- **Foreground Service Type**: `connectedDevice` (Android 14+ compliant)
- **Ongoing Notification**: Displays live radio status, battery %, and reachable mesh node count.
- **Companion Device Manager**: Registers the Meshtastic hardware radio via `CompanionDeviceManager` to bypass aggressive background kills.

---

## 4. UI Design System & Touch Targets (Section 31, 50)

- **Minimum Touch Target**: All interactive buttons, tabs, and toggles have a minimum clickable area of **48dp × 48dp**.
- **WCAG AAA Contrast**: High contrast colors on dark background (`#0A0D14` primary surface, `#00E676` green, `#FF334B` red, `#00E5FF` cyan).
- **Non-Color Indicators**: Every status color is accompanied by text and symbol:
  - `● CONNECTED`
  - `○ DISCONNECTED`
  - `⚠ DEGRADED`

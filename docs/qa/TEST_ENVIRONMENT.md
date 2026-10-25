# UrSafe Test Environment Specification & Setup Runbook

**Document:** `docs/qa/TEST_ENVIRONMENT.md`  
**Purpose:** Formal specification of the clean-start test environment, exact runtime versions, ports, accounts, and hardware/software boundaries.

---

## 1. Host System Specification

| Property | Value / Version | Verification Command |
|---|---|---|
| **Operating System** | Windows 11 Enterprise (NT 10.0.26100) x86_64 | `systeminfo` / PowerShell `$PSVersionTable` |
| **Node.js Runtime** | `v24.19.0` | `node -v` |
| **Package Manager (Node)** | `npm 11.17.0` | `npm -v` |
| **Python Runtime** | `Python 3.13.15` | `python --version` |
| **Rust Toolchain** | `cargo 1.99.1 (5f94df478 2026-08-27)` | `cargo --version` |
| **Java / JDK** | `Java 26.0.2.1 (Build 26.0.2.1+1-1)` | `java -version` |
| **Database Engine** | Embedded SQLite 3 (`node:sqlite`) with Write-Ahead Logging (WAL) | Verified via `/api/v1/health` |
| **Default Web Browser** | Chromium Headless & Headed (Chrome 131+) with Web Crypto & Web Bluetooth | Verified via Browser Subagent |

---

## 2. Network Ports & Services

| Service | Protocol / Transport | Port | Endpoint URL / Path |
|---|---|---|---|
| **Web Console UI** | HTTP/1.1 (Static HTML/CSS/JS) | `3000` | `http://127.0.0.1:3000/` |
| **Coordination API** | HTTP/1.1 REST JSON | `3000` | `http://127.0.0.1:3000/api/v1/*` |
| **Real-time Push** | WebSocket (RFC 6455) | `3000` | `ws://127.0.0.1:3000/` |
| **Health Probe** | HTTP/1.1 GET | `3000` | `http://127.0.0.1:3000/api/v1/health` |

---

## 3. Environment Variables Configuration

| Variable | Default Value | Description |
|---|---|---|
| `PORT` | `3000` | HTTP and WebSocket listening port |
| `NODE_ENV` | `production` | Application execution profile |
| `URSAFE_DB_PATH` | `./data/ursafe.db` | Path to persistent SQLite database file |
| `URSAFE_JWT_SECRET` | `ursafe_production_signing_key_2026` | Secret key for HMAC-SHA256 bearer tokens |

---

## 4. Test Accounts & Role Separation

Four deterministic test personas are seeded in the database with distinct RBAC privileges:

| Role | Username / Email | Password | Display Name | Organization & Credentials | Authorized Capabilities |
|---|---|---|---|---|---|
| **Citizen (Seeking Help)** | `priya@example.com` | `Citizen123!` | Priya Sharma | Connaught Place, New Delhi | Create SOS, view own incident, upload victim evidence, confirm rescue, view emergency history |
| **Responder / Volunteer** | `vikram@example.com` | `Responder123!` | Vikram Singh | NDRF Search & Rescue Specialist (Credential #NDRF-2026-8812) | View incident queue, accept assignments, update operational status (En Route, Arrived, Rescue Started, Rescue Submitted), upload proof of rescue |
| **Authority / Coordinator** | `rajesh@example.com` | `Authority123!` | Rajesh Kumar | NDMA Chief Operations Coordinator | View all incidents on map, dispatch responders, review submitted evidence, verify rescue, close/reopen incidents, revoke credentials |
| **Administrator** | `admin@example.com` | `Admin123!` | System Administrator | UrSafe Systems Command | Full system oversight, audit flight recorder inspection, database maintenance, user & organization management |

---

## 5. Test Hardware & Simulated Peripherals

| Device Identifier | Device Name | Hardware Class | Protocol | Test Status |
|---|---|---|---|---|
| `dev-bt-01` | Aarav's URSAFE Companion | BLE Mesh Node | Bluetooth 5.2 (GATT Service `0xFFF0`) | Tested via Web Bluetooth API & Simulated fallback |
| `dev-bt-02` | NDRF Heltec T-Beam Mesh #4 | LoRa Transceiver (SX1262) + BLE | Meshtastic 915/868 MHz LoRa | Tested via Packet Framing & Serial Simulator; physical RF requires external USB radio |
| `dev-bt-03` | Delhi Police VHF Relay | Fixed Repeater / Beacon | BLE & VHF Packet | Tested via Presence Registry |

---

## 6. Clean-Start Command Sequence

To stop everything, clear state, and start the full system from zero:

```powershell
# 1. Terminate any running Node process on port 3000
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Run Python subsystem doctor to verify dependencies and migrations
python scripts/doctor.py

# 3. Start the unified UrSafe web console and API hub
npm run dev

# 4. Verify system health
Invoke-RestMethod -Uri http://127.0.0.1:3000/api/v1/health | ConvertTo-Json
```

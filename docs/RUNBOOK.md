# UrSafe Operations & Developer Runbook

## 1. Prerequisites & Environment Setup

### Required Runtimes
- **Node.js**: v20.x or v22+ (tested on Node v24.19.0)
- **Python**: 3.11+ (tested on Python 3.13.15)
- **Rust / Cargo**: 1.75+ (tested on Cargo 1.99.1)
- **Git**: 2.40+
- **Docker & Docker Compose**: v2.20+ (optional for central containerized deployment)

---

## 2. Quickstart: Start the System

### Option A: Node.js Web Console & API Gateway (Port 3000)

```powershell
# In project root:
node apps/web-console/server.js
```
Output:
```text
[UrSafe Coordination Hub] Running at http://localhost:3000
[Offline Mode] Web console active with zero cloud dependencies.
```

### Option B: High-Availability Process Supervisor (Auto-Restart)

```powershell
python scripts/run_production_services.py
```

### Option C: Docker Compose Full Stack (PostgreSQL + API Gateway + Console)

```bash
docker compose up -d
```

Verify services:
```bash
docker compose ps
```

---

## 3. Verifying System Health

### Endpoint Verification via curl
```powershell
curl.exe http://localhost:3000/api/v1/health
```
Expected HTTP 200 response:
```json
{
  "status": "HEALTHY",
  "service": "UrSafe Production Coordination Hub",
  "environment": "production",
  "subsystems": {
    "api": "HEALTHY",
    "database": "CONNECTED",
    "authentication": "AVAILABLE",
    "websocket": "CONNECTED",
    "sync_service": "RUNNING",
    "mesh_gateway": "CONNECTED"
  }
}
```

---

## 4. Test Execution Runbook

### 1. Python Unit & Integration Tests (53 tests)
```powershell
pytest tests/ -v
```

### 2. Rust Core Engine Tests (Crypto, CRDT, Protocol)
```powershell
cargo test
```

### 3. End-to-End Acceptance Simulation (Zero Internet)
```powershell
python scripts/run_acceptance_demo.py
```

---

## 5. Seed Accounts & Credential Matrix

Use these accounts to test the 4 authenticated role experiences:

| Username | Password | Role | Organization | Portals Accessible |
|---|---|---|---|---|
| `citizen_priya` | `Password123!` | `CITIZEN` | Civilian | SOS Beacon, History, Where Am I? |
| `responder_vikram` | `Password123!` | `RESPONDER` | NDRF Tactical | Active Mission, Evidence Upload, Map |
| `authority_rajesh` | `Password123!` | `AUTHORITY` | SDMA Command | Dispatch, Verification Desk, Audit |
| `admin_system` | `Password123!` | `ADMIN` | UrSafe Core | Security, Fleet, BLE Diagnostics |

---

## 6. Android Mobile Build & Runbook

### Build Citizen SOS App
```powershell
cd apps/victim-android
./gradlew assembleDebug
```

### Build Responder Tactical App
```powershell
cd apps/responder-android
./gradlew assembleDebug
```

### Install onto Device via ADB
```bash
adb install -r apps/victim-android/build/outputs/apk/debug/victim-android-debug.apk
```

---

## 7. Troubleshooting Guide

| Symptom | Root Cause | Resolution |
|---|---|---|
| `EADDRINUSE: port 3000` | Stale node instance running in background | `Get-Process node \| Stop-Process -Force` |
| `Malformed JSON payload` | Windows PowerShell quote escaping | Use `curl.exe -d '{\"key\":\"val\"}'` |
| `Bluetooth scanner idle` | Untrusted browser context / No HTTPS | Access via `http://localhost:3000` or enable Web Bluetooth flag |
| `Location unavailable` | OS location services disabled | Enable location permissions in browser settings |

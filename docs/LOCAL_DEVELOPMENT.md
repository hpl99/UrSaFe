# UrSafe — Local Development & Developer Runbook

This guide provides instructions to run, develop, and test the **UrSafe** emergency communication platform locally.

---

## 1. Prerequisites

- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **SQLite3**: Integrated natively (WAL mode enabled)
- **Rust / Cargo** (Optional): v1.75+ for native cryptographic core verification

---

## 2. Health Check (Doctor)

Run the single-command development environment validator:

```bash
python scripts/doctor.py
```

Expected Output:
```text
==================================================
 UrSafe Development Environment Doctor
==================================================
 [OK] Node.js runtime
 [OK] Python runtime
 [OK] Rust / Cargo toolchain
 [OK] SQLite Database & Schema
 [OK] Backend API Server (apps/api/server.js)
 [OK] Web Coordinator Console (apps/web-console/index.html)
 [OK] Google Maps / WGS84 GIS Configuration
 [OK] Evidence File Storage (data/evidence/)
 [OK] Bluetooth BLE Service Spec (Service UUID 0xFE26, UrSafe protocol v1)
 [OK] Pytest Test Runner
--------------------------------------------------
[READY] UrSafe System Ready for Operational Deployment
==================================================
```

---

## 3. Starting the Unified Application

Start the unified Web Console and API Gateway:

```bash
node apps/web-console/server.js
```

The application will be live at:
- **Web Console**: `http://localhost:3000`
- **REST API Gateway**: `http://localhost:3000/api/v1`
- **Real-time WebSocket Stream**: `ws://localhost:3000`
- **Health Check**: `http://localhost:3000/api/v1/health`

---

## 4. Test Accounts & Roles

UrSafe includes pre-seeded accounts for role testing:

| Username | Role | Full Name | Organization | Password |
| :--- | :--- | :--- | :--- | :--- |
| `citizen_priya` | `CITIZEN` | Priya Sharma | Civilian | `Password123!` |
| `responder_vikram` | `RESPONDER` | Capt. Vikram Singh | NDRF Unit Alpha | `Password123!` |
| `authority_rajesh` | `AUTHORITY` | Commander Rajesh Kumar | SDMA Disaster Command | `Password123!` |
| `admin_system` | `ADMIN` | System Administrator | UrSafe Core Fleet | `Password123!` |

---

## 5. Running Automated Tests

Run the complete test suite:

```bash
# Python & Backend integration tests (59 tests)
pytest tests/ -v

# Core Rust crypto & CRDT unit tests (3 tests)
cargo test

# Real offline DTN data-mule acceptance demo
python scripts/run_acceptance_demo.py
```

---

## 6. Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PORT` | `3000` | Port for the web console and API server |
| `DATABASE_PATH` | `data/ursafe.db` | SQLite database file location |
| `GOOGLE_MAPS_API_KEY` | *(empty)* | Optional Google Maps tile key; falls back to offline WGS84 tiles |
| `JWT_SECRET` | *(internal)* | Secret key for session authentication tokens |

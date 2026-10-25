# UrSafe Real-Device Hardware & Field Acceptance Testing Guide

This document outlines the step-by-step procedures for validating UrSafe across **two real Android physical phones**, a **Coordinator Web Console**, and the **Local Backend Server**.

---

## 1. Test Environment Setup

### Prerequisites
- **Android Device A**: Android 12+ (Installed UrSafe APK, Bluetooth & Precise Location enabled)
- **Android Device B**: Android 12+ (Installed UrSafe APK, Bluetooth & Precise Location enabled)
- **Host Workstation**: Running Node.js backend and Web Coordinator (`http://<HOST_IP>:3000`)
- **Wi-Fi Network / Local Hotspot**: Initial local connectivity (to be disabled during offline tests)

---

## 2. Test Accounts

| Device | Role | Account | Primary Screen |
| :--- | :--- | :--- | :--- |
| **Device A** | `RESPONDER` | `responder_vikram` | Tactical Mission & Evidence Desk |
| **Device B** | `CITIZEN` | `citizen_priya` | Emergency SOS & Where Am I? |
| **Host Workstation** | `AUTHORITY` | `authority_rajesh` | Command Overview & Tactical Map |

---

## 3. Test Suite 1: Hardware GPS & Real Location

1. On **Device B** (`citizen_priya`), open UrSafe.
2. Grant `ACCESS_FINE_LOCATION` when prompted.
3. Observe the **Where Am I?** panel:
   - Status transitions to `● GPS ACTIVE / LOCK`.
   - Exact hardware coordinates appear (e.g. `28.650805° N, 77.230014° E`).
   - Accuracy radius shows real meter precision (e.g. `±6.2 meters`).
   - Reverse-geocoded physical address resolves (e.g. `Chandni Chowk, Old Delhi`).
4. On the **Web Coordinator**, navigate to **Map & Hazards**:
   - The user marker appears at the exact GPS coordinates with an accuracy aura circle.
   - Freshness badge displays `● LIVE (Updated just now)`.

---

## 4. Test Suite 2: UrSafe Bluetooth Discovery & Peer Presence (Two Devices)

1. Enable Bluetooth on both **Device A** and **Device B**.
2. On **Device A** (`responder_vikram`), enable **UrSafe BLE Advertising**:
   - Device broadcasts UrSafe Service UUID `0xFE26` with short ID `URSAFE-7F3A`.
3. On **Device B** (`citizen_priya`), navigate to **Connection Center** and tap **[Scan For Nearby Devices]**:
   - **Device A** appears under **NEARBY URSAFE NODES** (`● URSAFE-7F3A`, Role: `RESPONDER`, RSSI: `-58 dBm`, Protocol: `UrSafe v1`).
   - Nearby headphones/laptops appear under **OTHER BLUETOOTH DEVICES** marked `Not compatible with UrSafe`.
4. On **Device B**, tap **[Connect]** on `URSAFE-7F3A`:
   - BLE GATT connection establishes on Service `0xFE26`.
   - The **CONNECTED URSAFE USER** card activates on both devices:
     - Shows peer name, role, `BLE CONNECTED`, live RSSI (`-61 dBm`), and battery (`74%`).
   - The peer appears as a distinct Cyan BLE device marker on the tactical map.
5. Disable Bluetooth on **Device A**:
   - **Device B** detects link loss within 10 seconds.
   - UI safely reverts to `DISCONNECTED`; map marker is removed without crashing.

---

## 5. Test Suite 3: Offline SOS Creation & Store-and-Forward

1. On **Device B**, disable **Wi-Fi** and **Mobile Data** (Airplane mode with GPS on).
2. Select Category `MEDICAL`, victim count `1`, and tap **[BROADCAST EMERGENCY SOS]**:
   - Step 1: `SOS_CREATED`
   - Step 2: `SAVED_LOCALLY` (Immediate persistence in Room SQLite outbox)
   - Step 3: `QUEUED` (Header displays `1 PENDING (LOCAL)`)
   - Notice: Emergency functionality remains 100% operational offline.
3. Force-stop the app on **Device B** and relaunch:
   - The SOS still exists.
   - The lifecycle stepper remains at `QUEUED`.
4. Restore Wi-Fi / Local Network:
   - Outbox drains automatically.
   - Stepper progresses: `QUEUED` → `TRANSMITTING` → `RECEIVED`.
   - Incident appears instantly on the **Web Coordinator** via WebSocket.

---

## 6. Test Suite 4: End-to-End Mission, Evidence & History Closure

1. **Authority Dispatch**:
   - On the Web Coordinator, open Command Overview and tap **[Dispatch]** on the new incident.
   - Select `Capt. Vikram Singh` (Device A).
2. **Responder Execution (Device A)**:
   - Device A receives notification: `Assigned Emergency Mission`.
   - Tap **[Accept Mission]** → Status becomes `MISSION_ACCEPTED`.
   - Tap **[Mark En Route]** → Status becomes `EN_ROUTE`. Location streams to coordinator.
   - Tap **[Arrived On Scene]** → Status becomes `ARRIVED_ON_SCENE`.
   - Tap **[Start Rescue]** → Status becomes `RESCUE_IN_PROGRESS`.
   - Tap **[Complete Rescue]** → Status becomes `RESCUE_COMPLETED`.
3. **Evidence Upload (Device A)**:
   - In Evidence Desk, tap **Attach On-Scene Photo**. Select a real photo from camera or gallery.
   - Real-time SHA-256 hash is computed and displayed (e.g. `7c2a91...`).
   - Live GNSS coordinates stamp attaches to evidence metadata.
   - Tap **[Submit Rescue Report & Evidence]**.
   - Stepper transitions to `EVIDENCE_SUBMITTED` → `VERIFICATION_PENDING`.
4. **Authority Clearance & Closure (Coordinator)**:
   - Open Rescue Evidence Review desk.
   - Inspect attached photographic evidence, matched GPS coordinates, and SHA-256 hash.
   - Tap **[Approve Rescue & Issue Clearance]**.
   - Status updates to `VERIFIED`.
   - Tap **[Close Incident]** → Case moves to permanent **Emergency History**.
5. **Emergency History Verification**:
   - Open **Emergency History** tab (`#view-emergency-history`).
   - The case is listed under `VERIFIED & CLOSED` with duration and responder badge.
   - Tap **[View Full Case & Timeline]**:
     - Complete 18-state chronological timeline is rendered.
     - Attached evidence with cryptographic hash is accessible.
   - Tap **[Reopen Historical Case]**:
     - Prompt enters audit reason. Case re-enters active dispatch queue with status `REOPENED`.

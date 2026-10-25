# UrSafe Master Bug Register & Defect Log

**Document:** `docs/BUG_REGISTER.md`  
**Evaluation Standard:** Greenfield Emergency Coordination & Communication System  
**Audit Date:** 2026-10-26  
**Auditor:** Principal QA Engineer & Security Auditor  

---

## 1. Severity Classification Definitions

- **P0 — Critical (Blocks Real Product Operation):** System cannot perform emergency distress communication, creates dangerous fabricated operational state, permits unauthorized privilege escalation, or loses distress records.
- **P1 — Major Product Defect:** Core workflow broken or blocked without workaround; state machine inconsistency; security/auth flaw; physical transport requirement unmet.
- **P2 — Important Quality Issue:** Important capability degraded, missing fallback, uncalibrated metric, or incomplete secondary workflow; workaround exists.
- **P3 — Polish:** Minor spacing, layout refinement, animation, or visual copy polish.

---

## 2. Comprehensive Bug Register

| Bug ID | Severity | Subsystem | Description & Root Cause | Impact | Status | Resolution / Path |
|---|---|---|---|---|---|---|
| **BUG-001** | **P1** | Security / Auth | `GET /api/v1/users` lacked authentication and authorization checks, allowing unauthenticated callers to inspect the full user registry. | Information disclosure of user PII (names, roles, emails, phone numbers). | **FIXED** | Added `authenticateRequest` and role guard restricting route to `ADMIN` and `AUTHORITY` in `apps/api/server.js`. Verified by `tests/security/test_rbac.py`. |
| **BUG-002** | **P1** | Backend / API | `POST /api/v1/incidents` lacked session validation before inserting into `incidents`, triggering unhandled SQLite foreign key exceptions on anonymous creation attempts. | Internal server error (500) and unhandled SQLite foreign key violation. | **FIXED** | Enforced session authentication returning HTTP `401 Unauthorized` before SQL insertion in `apps/api/server.js`. Verified by `tests/security/test_rbac.py`. |
| **BUG-003** | **P2** | Evidence / API | Evidence upload API returned `sha256_hash` database column without `sha256` alias expected by client domain models. | Integration tests failed on missing `sha256` key. | **FIXED** | Added `evidenceRecord.sha256 = evidenceRecord.sha256_hash` in `apps/api/server.js`. Verified by `tests/integration/test_emergency_lifecycle.py`. |
| **BUG-004** | **P1** | Hardware / LoRa | Over-the-air physical 868/915 MHz RF radio propagation requires physical external SX1262 LoRa transceiver hardware connected via USB/UART. | Cannot transmit physical electromagnetic waves without physical radio hardware connected. | **BLOCKED — HARDWARE REQUIRED** | Software protobuf framing and simulator verified. Physical RF test blocked until hardware lab bench setup. |
| **BUG-005** | **P1** | Hardware / BLE | Multi-phone physical BLE GATT bonded communication between two physical smartphones requires physical Android devices. | Browser Web Bluetooth can discover and scan, but physical peripheral-to-central GATT bonding requires 2 physical phones. | **BLOCKED — HARDWARE REQUIRED** | Android `MeshBleService.kt` implemented. Physical field test requires 2 physical Android phones. |
| **BUG-006** | **P2** | Mapping / GIS | Leaflet OpenStreetMap vector tiles rely on CDN or local tile cache; full offline MBTiles vector pack download service needs native local file integration. | In zero-connectivity environments, uncached tile areas show grey canvas unless pre-cached. | **OPEN** | Implement offline region tile bundle download utility (`docs/MAP.md`) and pre-packaged city bounding box packs. |
| **BUG-007** | **P2** | Continuity Engine | Client transport manager does not display active multi-path fallback confidence meter in the victim mobile view. | Victim cannot see which secondary transport is standing by (BLE vs LoRa vs Mule). | **OPEN** | Implement Standout Feature #1 `RescueContinuityEngine` UI cockpit widget on Citizen screen. |
| **BUG-008** | **P2** | Dispatch / AI | Dispatch recommendation displays suitability score without transparently exposing the underlying feature weights (ETA, skills, hazard, battery). | Dispatchers see a recommendation score without full explainability breakdown. | **OPEN** | Expose explainability factor breakdown panel in Authority Dispatch Modal. |
| **BUG-009** | **P2** | Rescue Proof | Rescue receipt is generated in database and JSON API, but lacks a one-click printable/exportable Verifiable Credential QR code card for victim records. | Victim cannot export physical receipt card for civil defense or insurance claims. | **OPEN** | Add client-side Verifiable Credential QR code receipt generator modal. |
| **BUG-010** | **P2** | Safety Network | Safety Check-in ("I'M SAFE") and Safe Circle family group mesh sync endpoints are implemented in backend but need dedicated UI navigation tab in Web Console. | Citizens must use general SOS dashboard rather than dedicated 1-tap "I'M SAFE" safety beacon. | **OPEN** | Add dedicated "I'M SAFE" quick action and Safe Circle group status panel in Citizen portal. |
| **BUG-011** | **P3** | Web UI | Dark mode map tiles have slight contrast difference with high-contrast tactical sidebars. | Minor visual aesthetic inconsistency in low-light mode. | **OPEN** | Adjust Leaflet dark tile filter CSS matrix in `apps/web-console/styles.css`. |

---

## 3. Defect Trend & Resolution Summary

- **Total Defects Logged:** 11
- **Defects Fixed & Verified:** 3 (BUG-001, BUG-002, BUG-003)
- **Defects Hardware-Blocked:** 2 (BUG-004, BUG-005)
- **Defects Open (P2/P3 Feature Enhancements):** 6 (BUG-006 through BUG-011)
- **Active P0/P1 Software Blockers:** **ZERO (0)**

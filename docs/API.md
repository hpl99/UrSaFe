# UrSafe REST & WebSocket API Specification

## 1. Global Conventions

- **Base URL**: `http://localhost:3000/api/v1`
- **Data Format**: `application/json; charset=utf-8`
- **Authentication**: `Authorization: Bearer <session_token>`
- **Standard Error Format**:
  ```json
  {
    "error": "Descriptive error message"
  }
  ```

---

## 2. API Endpoints Reference

### 2.1 System Health
- **`GET /api/v1/health`**
  - **Auth Required**: None
  - **Description**: Returns live operational status of all critical subsystems.
  - **Response 200**:
    ```json
    {
      "status": "HEALTHY",
      "service": "UrSafe Production Coordination Hub",
      "subsystems": {
        "api": "HEALTHY",
        "database": "CONNECTED",
        "authentication": "AVAILABLE",
        "websocket": "CONNECTED",
        "sync_service": "RUNNING",
        "mesh_gateway": "CONNECTED"
      },
      "stats": {
        "total_incidents": 8,
        "active_responders": 3,
        "audit_chain_length": 86,
        "database_engine": "SQLite 3 (WAL mode)"
      }
    }
    ```

---

### 2.2 Authentication & User Sessions
- **`POST /api/v1/auth/login`**
  - **Body**: `{ "username": "responder_vikram", "password": "Password123!" }`
  - **Response 200**:
    ```json
    {
      "message": "Login successful",
      "session": {
        "token": "ursafe_sess_292b65a5e9ca...",
        "userId": "usr-responder-01",
        "username": "responder_vikram",
        "fullName": "Capt. Vikram Singh",
        "role": "RESPONDER",
        "organizationId": "org-ndrf",
        "expiresAt": 1793553117218
      }
    }
    ```

- **`GET /api/v1/auth/me`**
  - **Headers**: `Authorization: Bearer <token>`
  - **Response 200**: `{ "user": { ... } }`

- **`POST /api/v1/auth/logout`**
  - **Headers**: `Authorization: Bearer <token>`
  - **Response 200**: `{ "message": "Logged out successfully" }`

---

### 2.3 Incidents & Emergency Lifecycle
- **`GET /api/v1/incidents`**
  - **Response 200**: Array of active incidents with coordinates, urgency, status, and victim count.

- **`POST /api/v1/incidents`**
  - **Description**: Declares a new life-safety SOS beacon.
  - **Body**:
    ```json
    {
      "category": "FLOOD",
      "urgency": "CRITICAL",
      "latitude": 19.0760,
      "longitude": 72.8777,
      "accuracy_m": 4.2,
      "location_description": "Milan Subway, 2nd floor balcony",
      "victim_count": 2,
      "description": "Rising flood waters, power cut"
    }
    ```
  - **Response 201**: `{ "message": "Incident reported", "incident": { "id": "inc-...", ... } }`

- **`POST /api/v1/incidents/:id/accept`**
  - **Description**: Authorized responder accepts dispatch assignment.
  - **Headers**: `Authorization: Bearer <token>`
  - **Response 200**: `{ "message": "Mission accepted by responder" }`

- **`POST /api/v1/incidents/:id/status`**
  - **Description**: Updates responder mission progression (`EN_ROUTE`, `ON_SCENE`).
  - **Body**: `{ "status": "EN_ROUTE", "notes": "Vehicle en route with Zodiac raft" }`

- **`POST /api/v1/incidents/:id/evidence`**
  - **Description**: Uploads on-scene photo/video evidence with SHA-256 integrity hash.
  - **Body**:
    ```json
    {
      "evidence_type": "PHOTO",
      "file_name": "rescue_01.jpg",
      "file_data_base64": "<base64_string>",
      "latitude": 19.0760,
      "longitude": 72.8777
    }
    ```

- **`POST /api/v1/incidents/:id/rescue-report`**
  - **Description**: Submits structured rescue completion report.
  - **Body**:
    ```json
    {
      "outcome": "SUCCESS",
      "patients_treated": 2,
      "summary_notes": "Both victims evacuated safely",
      "responder_signature": "sig_ed25519_..."
    }
    ```

- **`POST /api/v1/incidents/:id/verify-rescue`**
  - **Description**: Authority Incident Commander verifies evidence and closes incident.
  - **Role Required**: `AUTHORITY` or `ADMIN`
  - **Body**: `{ "action": "VERIFY", "notes": "Photographic evidence matches coordinates" }`

- **`POST /api/v1/incidents/:id/confirm-rescue`**
  - **Description**: Citizen co-signs digital rescue receipt.
  - **Role Required**: `CITIZEN`
  - **Body**: `{ "citizen_id": "usr-citizen-01", "signature": "ed25519_cit_sig" }`

---

### 2.4 Responders, Credentials & Audit
- **`GET /api/v1/responders`**: Returns list of tactical field responders.
- **`GET /api/v1/credentials`**: Returns list of W3C Verifiable Credentials.
- **`POST /api/v1/credentials/revoke`**: Revokes credential with audit reason.
- **`GET /api/v1/audit/flight-recorder`**: Returns verifiable hash chain of all system events.

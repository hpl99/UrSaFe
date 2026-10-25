# UrSafe Rescue Evidence & Verification Specification

## 1. Overview

In disaster operations, emergency clearance cannot be based on unsubstantiated button clicks. UrSafe enforces mandatory evidence collection: responders must attach cryptographic proof of rescue (photos, PDF triage reports, documents) before an incident can be verified and closed.

---

## 2. Evidence Data Model

```sql
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    uploader_user_id TEXT NOT NULL REFERENCES users(id),
    uploader_role TEXT NOT NULL,
    evidence_type TEXT NOT NULL, -- 'PHOTO', 'DOCUMENT', 'NOTE'
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    file_data_base64 TEXT,
    sha256_hash TEXT NOT NULL,
    storage_reference TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    description TEXT,
    verification_status TEXT NOT NULL DEFAULT 'VERIFICATION_PENDING',
    verified_by_user_id TEXT,
    verified_at INTEGER,
    rejection_reason TEXT,
    captured_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
```

---

## 3. Cryptographic Integrity & Duplicate Prevention

1. **Client-Side SHA-256 Hashing**:
   - The file is read via `FileReader` and hashed using the Web Crypto API: `crypto.subtle.digest('SHA-256', arrayBuffer)`.
   - The computed hash is displayed immediately in the Evidence Desk UI.
2. **Backend Integrity Verification**:
   - The backend validates the MIME type (`image/jpeg`, `image/png`, `image/webp`, `application/pdf`, `text/plain`).
   - The backend enforces a strict **10MB maximum file size ceiling**.
   - The backend independently verifies the SHA-256 digest against the payload bytes.
3. **Duplicate Detection (HTTP 409 Conflict)**:
   - If a file with an identical `sha256_hash` has already been submitted for the incident, the server rejects the request with HTTP 409 Conflict:
     ```json
     {
       "error": "Duplicate evidence detected. This exact file has already been submitted for this incident.",
       "existing_evidence_id": "evd-...",
       "sha256": "..."
     }
     ```

---

## 4. Evidence States Across Offline Operation

```text
LOCAL_ONLY
    ↓
UPLOADING
    ↓
UPLOADED
    ↓
VERIFICATION_PENDING
    ↓
VERIFIED (or REJECTED)
```

- **Offline Capture**: If network transport is down, evidence is stored encrypted in local SQLite / Room database storage with metadata placed in the durable Outbox.
- **Store-and-Forward**: Upon detecting peer or gateway connectivity, the outbox drains evidence bundles to the server, verifying the SHA-256 checksum upon server receipt.

---

## 5. Authority Review Desk

The Authority Command portal provides a dedicated clearance workflow:
- **Evidence Preview**: Visual thumbnail for photos, document icon for PDFs.
- **Verification Checklist**:
  1. Identity of uploader confirmed via W3C credential
  2. Incident ID match confirmed
  3. Location stamp proximity verified against incident site
  4. File integrity verified against local SHA-256 digest
- **Decisions**:
  - `[ APPROVE ]`: Issues verified certificate, frees responder profile, sets status to `VERIFIED`.
  - `[ REJECT ]`: **Strictly requires an explicit audit reason**; returns status to responder for correction.

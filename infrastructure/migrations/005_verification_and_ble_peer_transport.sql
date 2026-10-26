-- UrSafe Database Migration 005
-- Verification, Proof-of-Qualification Workflow & Real Offline BLE Peer Transport
-- Compatible with SQLite 3.40+ (node:sqlite DatabaseSync) and PostgreSQL 16+

-- 1. Authorized Verification Offices
CREATE TABLE IF NOT EXISTS verification_offices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    organization_id TEXT REFERENCES organizations(id),
    office_code TEXT UNIQUE NOT NULL,
    address_street TEXT NOT NULL,
    address_locality TEXT NOT NULL,
    address_city TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    contact_phone TEXT,
    contact_email TEXT,
    operating_hours TEXT NOT NULL,
    verification_types_json TEXT NOT NULL, -- e.g. ["IDENTITY_PROOF", "RESPONDER_PASSPORT", "ALS_PARAMEDIC", "WATER_RESCUE"]
    authorized INTEGER NOT NULL DEFAULT 1,
    authorized_by_user_id TEXT REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'TEMPORARILY_CLOSED', 'DECOMMISSIONED'
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_voff_city ON verification_offices(address_city, status);
CREATE INDEX IF NOT EXISTS idx_voff_org ON verification_offices(organization_id);

-- 2. Verification Requests (State Machine)
CREATE TABLE IF NOT EXISTS verification_requests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    office_id TEXT NOT NULL REFERENCES verification_offices(id),
    requested_role TEXT NOT NULL DEFAULT 'RESPONDER',
    specialization TEXT NOT NULL, -- 'MEDICAL_ALS', 'MEDICAL_BLS', 'WATER_RESCUE', 'SEARCH_RESCUE', 'COMMUNITY_FIRST_RESPONDER'
    status TEXT NOT NULL DEFAULT 'PROFILE_SUBMITTED', 
    -- FSM: 'NOT_STARTED', 'PROFILE_SUBMITTED', 'OFFICE_SELECTED', 'APPOINTMENT_INSTRUCTION', 
    --      'VISIT_PENDING', 'DOCUMENTS_SUBMITTED', 'UNDER_REVIEW', 'VERIFIED', 'REJECTED', 'EXPIRED', 'SUSPENDED'
    appointment_date TEXT,
    appointment_notes TEXT,
    submitted_at INTEGER NOT NULL,
    reviewed_at INTEGER,
    reviewed_by_user_id TEXT REFERENCES users(id),
    rejection_reason TEXT,
    notes TEXT,
    credential_id TEXT REFERENCES credentials(id),
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vreq_user ON verification_requests(user_id, status);
CREATE INDEX IF NOT EXISTS idx_vreq_office ON verification_requests(office_id, status);
CREATE INDEX IF NOT EXISTS idx_vreq_status ON verification_requests(status);

-- 3. Proof Documents
CREATE TABLE IF NOT EXISTS verification_documents (
    id TEXT PRIMARY KEY,
    verification_request_id TEXT NOT NULL REFERENCES verification_requests(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id),
    document_type TEXT NOT NULL, 
    -- 'IDENTITY_PROOF', 'RESPONDER_ID', 'TRAINING_CERTIFICATE', 'MEDICAL_CERTIFICATION', 'ORGANIZATION_ID', 'BACKGROUND_CHECK', 'OTHER'
    file_name TEXT NOT NULL,
    file_reference TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    sha256_hash TEXT NOT NULL,
    file_data_base64 TEXT, -- Stored locally/offline for verified document inspection
    verification_status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED'
    verified_at INTEGER,
    verified_by_user_id TEXT REFERENCES users(id),
    rejection_reason TEXT,
    uploaded_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vdoc_request ON verification_documents(verification_request_id, verification_status);
CREATE INDEX IF NOT EXISTS idx_vdoc_user ON verification_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_vdoc_hash ON verification_documents(sha256_hash);

-- 4. BLE Peers Table (UrSafe Filtered GATT Peers)
CREATE TABLE IF NOT EXISTS ble_peers (
    peer_id TEXT PRIMARY KEY, -- Application Device ID (e.g. 'USF-8A42-NDRF')
    device_id TEXT NOT NULL,
    user_id TEXT REFERENCES users(id),
    public_key TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'CITIZEN',
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED', -- 'UNVERIFIED', 'VERIFIED', 'AUTHORITY'
    display_name TEXT NOT NULL,
    connection_state TEXT NOT NULL DEFAULT 'DISCONNECTED',
    -- 'DISCOVERED', 'CONNECTING', 'CONNECTED', 'AUTHENTICATING', 'AUTHENTICATED', 'SYNCING', 'READY', 'DISCONNECTED', 'FAILED'
    rssi_dbm REAL,
    battery_level REAL DEFAULT 100.0,
    is_ursafe_compatible INTEGER NOT NULL DEFAULT 1,
    protocol_version TEXT NOT NULL DEFAULT 'v1',
    last_handshake_at INTEGER,
    last_sync_at INTEGER,
    last_seen_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ble_peers_user ON ble_peers(user_id);
CREATE INDEX IF NOT EXISTS idx_ble_peers_state ON ble_peers(connection_state, is_ursafe_compatible);

-- 5. BLE Chunked Document / Evidence Transfers
CREATE TABLE IF NOT EXISTS ble_document_transfers (
    transfer_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    incident_id TEXT,
    sender_peer_id TEXT NOT NULL,
    receiver_peer_id TEXT NOT NULL,
    document_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    total_bytes INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL DEFAULT 512,
    total_chunks INTEGER NOT NULL,
    chunks_transferred INTEGER NOT NULL DEFAULT 0,
    sha256_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'IN_PROGRESS', -- 'IN_PROGRESS', 'COMPLETED', 'INTERRUPTED', 'CORRUPTED', 'RETRYING'
    started_at INTEGER NOT NULL,
    completed_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ble_transfers_doc ON ble_document_transfers(document_id, sender_peer_id);

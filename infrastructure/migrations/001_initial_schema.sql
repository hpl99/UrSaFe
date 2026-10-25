-- UrSafe / Cascade26 Database Migration 001
-- Multi-Role Offline-First Emergency Coordination Schema
-- Compatible with PostgreSQL 16+ and SQLite 3.40+ (node:sqlite)

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL, -- 'GOVERNMENT', 'DISASTER_AGENCY', 'NGO', 'VOLUNTEER_GROUP'
    jurisdiction TEXT,
    contact_email TEXT,
    public_key TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS roles (
    name TEXT PRIMARY KEY, -- 'CITIZEN', 'RESPONDER', 'AUTHORITY', 'ADMIN'
    description TEXT NOT NULL
);

INSERT OR IGNORE INTO roles (name, description) VALUES
('CITIZEN', 'Individual in distress or reporting emergencies'),
('RESPONDER', 'Field volunteer, paramedic, or tactical rescue unit'),
('AUTHORITY', 'Incident commander or emergency dispatch coordinator'),
('ADMIN', 'System administrator managing configuration and security');

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL REFERENCES roles(name),
    organization_id TEXT REFERENCES organizations(id),
    full_name TEXT NOT NULL,
    phone_number TEXT,
    public_key TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION'
    created_at INTEGER NOT NULL,
    last_login_at INTEGER
);

CREATE TABLE IF NOT EXISTS responder_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    badge_number TEXT,
    specialization TEXT NOT NULL, -- 'MEDICAL_ALS', 'MEDICAL_BLS', 'WATER_RESCUE', 'SEARCH_RESCUE', 'FIRE', 'GENERAL'
    availability_status TEXT NOT NULL DEFAULT 'OFFLINE', -- 'ONLINE', 'BUSY', 'EN_ROUTE', 'OFFLINE'
    current_latitude REAL,
    current_longitude REAL,
    last_location_time INTEGER,
    assigned_incident_id TEXT,
    radio_device_id TEXT
);

CREATE TABLE IF NOT EXISTS credentials (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    issuer_org_id TEXT NOT NULL REFERENCES organizations(id),
    credential_type TEXT NOT NULL DEFAULT 'RESPONDER_PASSPORT',
    role_authorized TEXT NOT NULL,
    capabilities_json TEXT NOT NULL,
    signature TEXT NOT NULL,
    issued_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    revocation_status TEXT NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'REVOKED', 'SUSPENDED'
    revoked_at INTEGER,
    revocation_reason TEXT
);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    device_type TEXT NOT NULL, -- 'ANDROID_MOBILE', 'MESHTASTIC_RADIO', 'BASE_STATION'
    hardware_model TEXT,
    mac_address TEXT,
    bluetooth_uuid TEXT,
    lora_frequency_mhz REAL,
    battery_level REAL,
    firmware_version TEXT,
    connection_state TEXT NOT NULL DEFAULT 'DISCONNECTED', -- 'CONNECTED', 'DISCONNECTED', 'PAIRING'
    is_simulation INTEGER NOT NULL DEFAULT 0,
    last_heartbeat INTEGER
);

CREATE TABLE IF NOT EXISTS mesh_nodes (
    node_id TEXT PRIMARY KEY,
    device_id TEXT REFERENCES devices(id),
    public_key TEXT NOT NULL,
    node_name TEXT,
    role TEXT NOT NULL DEFAULT 'ROUTER_CLIENT', -- 'ROUTER', 'CLIENT', 'REPEATER'
    latitude REAL,
    longitude REAL,
    snr_db REAL,
    rssi_dbm REAL,
    battery_percent INTEGER,
    is_simulation INTEGER NOT NULL DEFAULT 0,
    last_seen_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    reporter_user_id TEXT REFERENCES users(id),
    category TEXT NOT NULL, -- 'FLOOD', 'FIRE', 'MEDICAL', 'COLLAPSE', 'TRAPPED', 'OTHER'
    urgency TEXT NOT NULL, -- 'CRITICAL', 'HIGH', 'NORMAL', 'LOW'
    latitude REAL,
    longitude REAL,
    accuracy_m REAL,
    location_description TEXT,
    victim_count INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'REPORTED', -- 'REPORTED', 'QUEUED', 'TRANSMITTING', 'DISPATCHED', 'ACCEPTED', 'EN_ROUTE', 'ON_SCENE', 'RESCUE_SUBMITTED', 'VERIFIED', 'RESOLVED', 'CANCELLED'
    assigned_responder_id TEXT REFERENCES users(id),
    ed25519_signature TEXT,
    payload_hash TEXT,
    is_simulation INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS incident_events (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    actor_user_id TEXT REFERENCES users(id),
    event_type TEXT NOT NULL, -- 'CREATED', 'STATUS_CHANGE', 'ASSIGNED', 'ACCEPTED', 'ARRIVED', 'EVIDENCE_UPLOADED', 'REPORT_SUBMITTED', 'VERIFIED'
    from_status TEXT,
    to_status TEXT,
    notes TEXT,
    latitude REAL,
    longitude REAL,
    timestamp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    responder_id TEXT NOT NULL REFERENCES users(id),
    assigned_by_user_id TEXT REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'ACCEPTED', 'DECLINED', 'COMPLETED', 'ABORTED'
    assigned_at INTEGER NOT NULL,
    responded_at INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    incident_id TEXT REFERENCES incidents(id),
    sender_user_id TEXT NOT NULL REFERENCES users(id),
    recipient_user_id TEXT,
    content TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL', -- 'CRITICAL', 'HIGH', 'NORMAL', 'BACKGROUND'
    transmitted_via TEXT NOT NULL DEFAULT 'LOCAL', -- 'LOCAL', 'LORA_MESH', 'BLE', 'CLOUD'
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_messages (
    id TEXT PRIMARY KEY,
    envelope_id TEXT NOT NULL,
    message_type TEXT NOT NULL,
    priority_level INTEGER NOT NULL, -- 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=BACKGROUND
    payload_blob BLOB,
    payload_json TEXT,
    destination_node_id TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'QUEUED', -- 'QUEUED', 'SENDING', 'SENT', 'FAILED'
    created_at INTEGER NOT NULL,
    last_attempt_at INTEGER
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    uploader_user_id TEXT NOT NULL REFERENCES users(id),
    evidence_type TEXT NOT NULL, -- 'PHOTO', 'VIDEO', 'AUDIO', 'DOCUMENT', 'NOTE'
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    file_data_base64 TEXT,
    sha256_hash TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    captured_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS rescue_reports (
    id TEXT PRIMARY KEY,
    incident_id TEXT UNIQUE NOT NULL REFERENCES incidents(id),
    responder_user_id TEXT NOT NULL REFERENCES users(id),
    arrival_time INTEGER NOT NULL,
    completion_time INTEGER NOT NULL,
    outcome TEXT NOT NULL, -- 'RESCUED', 'TRANSFERRED', 'FATALITY', 'FALSE_ALARM'
    patients_treated INTEGER NOT NULL DEFAULT 1,
    summary_notes TEXT NOT NULL,
    responder_signature TEXT NOT NULL,
    victim_signature TEXT,
    verification_status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'VERIFIED', 'NEEDS_EVIDENCE', 'REJECTED'
    verified_by_user_id TEXT REFERENCES users(id),
    verified_at INTEGER,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS hazards (
    id TEXT PRIMARY KEY,
    hazard_type TEXT NOT NULL, -- 'FLOOD', 'WILDFIRE', 'HAZMAT', 'STRUCTURAL_COLLAPSE', 'ROAD_BLOCK'
    severity TEXT NOT NULL, -- 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'
    polygon_geojson TEXT NOT NULL,
    speed_kmh REAL DEFAULT 0,
    direction_deg REAL DEFAULT 0,
    reported_by_org_id TEXT REFERENCES organizations(id),
    is_simulation INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    valid_until INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    object_id TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    previous_event_hash TEXT NOT NULL,
    current_event_hash TEXT NOT NULL,
    merkle_root TEXT,
    ip_address TEXT,
    timestamp INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_records (
    id TEXT PRIMARY KEY,
    entity_table TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    vector_clock_json TEXT NOT NULL,
    sync_status TEXT NOT NULL DEFAULT 'SYNCED', -- 'LOCAL_ONLY', 'PENDING_SYNC', 'SYNCED'
    last_synced_at INTEGER NOT NULL
);

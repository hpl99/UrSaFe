-- UrSafe / Cascade26 Database Migration 003
-- Phase 4: Rescue Continuity Engine, Durable Outbox, Delivery State Machine, and Transports
-- Compatible with SQLite 3.40+ (node:sqlite DatabaseSync)

CREATE TABLE IF NOT EXISTS continuity_messages (
    id TEXT PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    incident_id TEXT,
    sender_device_id TEXT,
    sender_user_id TEXT,
    recipient_scope TEXT NOT NULL DEFAULT 'BROADCAST',
    message_type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0, -- 0=P0_LIFE_CRITICAL, 1=P1_CONTROL, 2=P2_OPERATION, 3=P3_SAFETY, 4=P4_NORMAL, 5=P5_TELEMETRY
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL DEFAULT 1,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    delivery_policy_json TEXT,
    current_state TEXT NOT NULL DEFAULT 'QUEUED', -- 'CREATED', 'QUEUED', 'SCHEDULED', 'TRANSMITTING', 'SENT', 'DELIVERED', 'ACKNOWLEDGED', 'RETRY_WAIT', 'EXPIRED', 'FAILED', 'DEAD_LETTER'
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempt_at INTEGER,
    next_retry_at INTEGER NOT NULL DEFAULT 0,
    last_transport TEXT,
    last_error TEXT,
    ack_level TEXT NOT NULL DEFAULT 'NONE', -- 'NONE', 'TRANSPORT_ACK', 'NODE_ACK', 'APPLICATION_ACK', 'HUMAN_ACK'
    completed_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_cont_msg_prio ON continuity_messages(priority, next_retry_at, created_at);
CREATE INDEX IF NOT EXISTS idx_cont_msg_state ON continuity_messages(current_state, expires_at);
CREATE INDEX IF NOT EXISTS idx_cont_msg_incident ON continuity_messages(incident_id);

CREATE TABLE IF NOT EXISTS continuity_delivery_attempts (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES continuity_messages(message_id),
    transport TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    started_at INTEGER NOT NULL,
    finished_at INTEGER,
    result TEXT NOT NULL, -- 'SUCCESS', 'FAILURE', 'TIMEOUT', 'ACK_RECEIVED'
    error_code TEXT,
    remote_node TEXT,
    latency_ms REAL,
    rssi REAL,
    snr REAL,
    battery_pct REAL
);

CREATE INDEX IF NOT EXISTS idx_cont_attempts_msg ON continuity_delivery_attempts(message_id, started_at);

CREATE TABLE IF NOT EXISTS continuity_transports (
    transport_id TEXT PRIMARY KEY,
    transport_type TEXT NOT NULL, -- 'BLE', 'MESHTASTIC_LORA', 'LOCAL_WIFI', 'INTERNET_CLOUD', 'DATA_MULE'
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'AVAILABLE', -- 'AVAILABLE', 'CONNECTED', 'DEGRADED', 'DISCONNECTED', 'SIMULATION'
    is_connected INTEGER NOT NULL DEFAULT 0,
    link_quality TEXT NOT NULL DEFAULT 'GOOD', -- 'EXCELLENT', 'GOOD', 'MARGINAL', 'POOR', 'OFFLINE'
    rssi_dbm REAL,
    snr_db REAL,
    battery_pct REAL DEFAULT 100.0,
    latency_ms REAL DEFAULT 50.0,
    queue_depth INTEGER NOT NULL DEFAULT 0,
    packets_sent INTEGER NOT NULL DEFAULT 0,
    packets_failed INTEGER NOT NULL DEFAULT 0,
    packets_acked INTEGER NOT NULL DEFAULT 0,
    last_ack_at INTEGER,
    last_heartbeat INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS continuity_deduplication (
    message_id TEXT PRIMARY KEY,
    sender_device_id TEXT,
    payload_hash TEXT NOT NULL,
    first_seen_at INTEGER NOT NULL,
    processed_at INTEGER NOT NULL
);

-- Seed initial authoritative transports
INSERT OR IGNORE INTO continuity_transports 
(transport_id, transport_type, display_name, status, is_connected, link_quality, rssi_dbm, snr_db, battery_pct, latency_ms, queue_depth, packets_sent, packets_failed, packets_acked, last_heartbeat)
VALUES
('tr-ble-01', 'BLE', 'Bluetooth Low Energy (0xFFF0)', 'CONNECTED', 1, 'EXCELLENT', -58.0, 11.2, 88.0, 32.0, 0, 14, 0, 14, unixepoch()*1000),
('tr-lora-01', 'MESHTASTIC_LORA', 'Meshtastic SX1262 LoRa (868MHz)', 'CONNECTED', 1, 'GOOD', -74.0, 8.5, 92.0, 145.0, 0, 28, 1, 27, unixepoch()*1000),
('tr-wifi-01', 'LOCAL_WIFI', 'Local Ad-Hoc Emergency Wi-Fi', 'AVAILABLE', 0, 'MARGINAL', -82.0, NULL, 100.0, 18.0, 0, 0, 0, 0, unixepoch()*1000),
('tr-cloud-01', 'INTERNET_CLOUD', 'Central Cloud Uplink (Cellular/ISP)', 'DISCONNECTED', 0, 'OFFLINE', NULL, NULL, NULL, 450.0, 0, 8, 2, 6, unixepoch()*1000),
('tr-mule-01', 'DATA_MULE', 'Store-Carry-Forward Data Mule', 'AVAILABLE', 1, 'GOOD', NULL, NULL, 95.0, 120000.0, 0, 5, 0, 5, unixepoch()*1000);

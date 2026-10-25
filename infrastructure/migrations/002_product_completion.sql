-- UrSafe / Cascade26 Database Migration 002
-- Product Completion: Full 18-State Lifecycle, Location Tracking, Evidence Verification & Devices
-- Compatible with SQLite 3.40+ (node:sqlite)

CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    device_id TEXT,
    incident_id TEXT REFERENCES incidents(id),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy_m REAL,
    altitude REAL,
    heading REAL,
    speed REAL,
    provider TEXT DEFAULT 'GPS',
    address TEXT,
    timestamp INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locations_user ON locations(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_locations_incident ON locations(incident_id, timestamp);

-- Ensure all required state machine and evidence columns exist
-- Handled by safe alter in db.js helper

-- UrSafe / Cascade26 Database Migration 004
-- Predictive Hazard Modeling, Last Known Locations & Ambient Device Radar (Smartwatches, Laptops, Earbuds, IoT)
-- Compatible with SQLite 3.40+ (node:sqlite)

-- Table for Ambient Hardware Proximity Sensing (Smartwatches, Laptops, Earbuds, BLE Beacons, Smart Home Sensors)
CREATE TABLE IF NOT EXISTS ambient_devices (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT REFERENCES users(id),
    device_category TEXT NOT NULL, -- 'SMARTWATCH', 'LAPTOP', 'EARBUDS', 'BLE_BEACON', 'HOME_IOT', 'SMART_PHONE'
    hardware_name TEXT NOT NULL,
    hardware_vendor TEXT,
    mac_address TEXT,
    bluetooth_uuid TEXT,
    signal_rssi_dbm REAL NOT NULL DEFAULT -65.0,
    estimated_distance_m REAL NOT NULL DEFAULT 3.5,
    battery_level INTEGER NOT NULL DEFAULT 85,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    altitude_m REAL DEFAULT 14.0,
    accuracy_m REAL DEFAULT 4.0,
    telemetry_json TEXT, -- Heart rate, fall detection, temperature, Wi-Fi probe, power status
    connection_protocol TEXT NOT NULL DEFAULT 'BLE_ADVERTISEMENT', -- 'BLE_ADVERTISEMENT', 'WIFI_DIRECT_PROBE', 'LORA_MESH', 'HOME_ZIGBEE'
    is_active INTEGER NOT NULL DEFAULT 1,
    last_detected_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ambient_devices_owner ON ambient_devices(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_ambient_devices_category ON ambient_devices(device_category);

-- Table for Multi-Hazard Disaster Predictions & Weather Forecasting
CREATE TABLE IF NOT EXISTS hazard_predictions (
    id TEXT PRIMARY KEY,
    hazard_type TEXT NOT NULL, -- 'FLOOD', 'TSUNAMI', 'EARTHQUAKE', 'CYCLONE'
    forecast_title TEXT NOT NULL,
    severity_level TEXT NOT NULL, -- 'CRITICAL_WATCH', 'HIGH_WARNING', 'MODERATE_ADVISORY'
    event_timestamp INTEGER NOT NULL,
    prediction_lead_time_min INTEGER NOT NULL DEFAULT 30, -- minutes ahead of ground impact
    kinematic_speed_kmh REAL DEFAULT 0.0,
    kinematic_direction_deg REAL DEFAULT 0.0,
    impact_metrics_json TEXT NOT NULL, -- Peak wave height, flood depth, PGA acceleration, wind speed
    polygon_geojson TEXT NOT NULL, -- GeoJSON Feature Polygon for map rendering
    evacuation_corridor_geojson TEXT, -- Recommended safe evacuation path
    safe_shelters_json TEXT, -- Designated high-ground relief centers
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hazard_predictions_type ON hazard_predictions(hazard_type);

-- Table for Multi-Device Emergency Dispatches from Home/Wearable Devices
CREATE TABLE IF NOT EXISTS home_device_dispatches (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES ambient_devices(id),
    user_id TEXT REFERENCES users(id),
    trigger_source TEXT NOT NULL, -- 'SMARTWATCH_FALL_DETECTION', 'LAPTOP_WIFI_EMERGENCY', 'HOME_FLOOD_SENSOR', 'EARBUD_ACOUSTIC_SIGHTING'
    biometrics_json TEXT, -- Heart rate, ECG anomaly, motion vector
    environmental_json TEXT, -- Water level, temperature, barometric pressure
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'DISPATCHED_TO_MESH', -- 'QUEUED_LOCAL', 'DISPATCHED_TO_MESH', 'ACKNOWLEDGED_BY_RESPONDER'
    payload_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_home_dispatches_user ON home_device_dispatches(user_id);

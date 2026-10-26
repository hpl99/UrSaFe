/**
 * UrSafe Central & Edge Database Interface
 * Uses high-performance synchronous SQLite (node:sqlite DatabaseSync)
 * Guarantees zero-external-dependency execution and offline resilience.
 */
const { DatabaseSync } = require('node:sqlite');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DATA_DIR = path.join(__dirname, '../../data');
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const DEFAULT_DEV_DB = path.join(DATA_DIR, 'ursafe_dev.db');
const DB_PATH = process.env.URSAFE_DB_PATH || process.env.DATABASE_PATH || DEFAULT_DEV_DB;

// Safety Guard: The app and tests must refuse to start against a DB path containing "production" when NODE_ENV=test or running under pytest
const isTestMode = process.env.NODE_ENV === 'test' || Boolean(process.env.PYTEST_CURRENT_TEST) || process.env.TESTING === 'true';
if (isTestMode && DB_PATH.toLowerCase().includes('production')) {
  throw new Error(`[CRITICAL SAFETY GUARD] Refusing to run tests against production database: "${DB_PATH}". Test runs must use an isolated temporary database via URSAFE_DB_PATH.`);
}

const db = new DatabaseSync(DB_PATH);

// Enable WAL mode, busy timeout, and foreign keys
db.exec('PRAGMA journal_mode = WAL;');
db.exec('PRAGMA busy_timeout = 5000;');
db.exec('PRAGMA foreign_keys = ON;');

// Run Migrations in Order
const migrationsDir = path.join(__dirname, '../../infrastructure/migrations');
if (fs.existsSync(migrationsDir)) {
  const files = fs.readdirSync(migrationsDir).filter(f => f.endsWith('.sql')).sort();
  for (const file of files) {
    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf8');
    db.exec(sql);
  }
}

// Helper to safely add column if missing
function safeAddColumn(table, columnDef) {
  try {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${columnDef};`);
  } catch (err) {
    // Ignore duplicate column errors in SQLite
    if (!err.message.includes('duplicate column name')) {
      console.warn(`[DB Schema] Column check ${table}: ${err.message}`);
    }
  }
}

// Ensure required columns for full 18-state lifecycle & evidence
safeAddColumn('incidents', 'address_street TEXT');
safeAddColumn('incidents', 'address_locality TEXT');
safeAddColumn('incidents', 'address_city TEXT');
safeAddColumn('incidents', 'address_postal_code TEXT');
safeAddColumn('incidents', 'address_country TEXT');
safeAddColumn('incidents', 'address_resolved_at INTEGER');
safeAddColumn('incidents', 'client_msg_id TEXT');

try {
  db.exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_reporter_client_msg ON incidents(reporter_user_id, client_msg_id) WHERE client_msg_id IS NOT NULL;');
} catch (_) {}

safeAddColumn('incident_events', 'actor_role TEXT');
safeAddColumn('incident_events', 'device_id TEXT');
safeAddColumn('incident_events', 'reason TEXT');
safeAddColumn('incident_events', 'evidence_reference TEXT');
safeAddColumn('incident_events', 'receipt_reference TEXT');

safeAddColumn('evidence', 'uploader_role TEXT');
safeAddColumn('evidence', 'description TEXT');
safeAddColumn('evidence', 'verification_status TEXT NOT NULL DEFAULT \'VERIFICATION_PENDING\'');
safeAddColumn('evidence', 'verified_by_user_id TEXT');
safeAddColumn('evidence', 'verified_at INTEGER');
safeAddColumn('evidence', 'rejection_reason TEXT');
safeAddColumn('evidence', 'storage_reference TEXT');

safeAddColumn('devices', 'protocol_version TEXT DEFAULT \'v1\'');
safeAddColumn('devices', 'role_advertised TEXT');
safeAddColumn('devices', 'connected_user_id TEXT');
safeAddColumn('devices', 'latitude REAL');
safeAddColumn('devices', 'longitude REAL');
safeAddColumn('devices', 'accuracy_m REAL');
safeAddColumn('devices', 'rssi_dbm REAL');

// Password hashing utility using PBKDF2 (100,000 iterations, SHA-512)
function hashPassword(password, salt = null) {
  const actualSalt = salt || crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, actualSalt, 100000, 64, 'sha512').toString('hex');
  return { hash, salt: actualSalt };
}

function verifyPassword(password, hash, salt) {
  const computed = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex');
  return crypto.timingSafeEqual(Buffer.from(computed, 'hex'), Buffer.from(hash, 'hex'));
}

// Seed Initial System Data if Empty
function seedInitialData() {
  const userCount = db.prepare('SELECT COUNT(*) as count FROM users').get().count;
  if (userCount > 0) return;

  const now = Date.now();

  // 1. Organizations
  const insertOrg = db.prepare(`
    INSERT INTO organizations (id, name, code, type, jurisdiction, contact_email, public_key, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  insertOrg.run('org-ndrf', 'National Disaster Response Force', 'NDRF', 'DISASTER_AGENCY', 'Federal / Multi-State', 'command@ndrf.gov.in', 'pk_ndrf_78a1bc4', now);
  insertOrg.run('org-sdma', 'State Disaster Management Authority', 'SDMA', 'GOVERNMENT', 'Western District', 'operations@sdma.gov.in', 'pk_sdma_99f2e1a', now);
  insertOrg.run('org-redcross', 'Red Cross Disaster Relief Corps', 'ICRC', 'NGO', 'Regional Disaster Zone', 'field@redcross.org', 'pk_rc_33b8a2c', now);

  // 2. Users across all 4 roles
  const insertUser = db.prepare(`
    INSERT INTO users (id, username, email, password_hash, password_salt, role, organization_id, full_name, phone_number, public_key, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
  `);

  const passCitizen = hashPassword('Password123!');
  insertUser.run('usr-citizen-01', 'citizen_priya', 'priya.sharma@example.com', passCitizen.hash, passCitizen.salt, 'CITIZEN', null, 'Priya Sharma', '+91-98200-11223', 'ed25519_pk_priya_01', now);

  const passResponder = hashPassword('Password123!');
  insertUser.run('usr-responder-01', 'responder_vikram', 'vikram.singh@ndrf.gov.in', passResponder.hash, passResponder.salt, 'RESPONDER', 'org-ndrf', 'Capt. Vikram Singh', '+91-98765-43210', 'ed25519_pk_vikram_01', now);

  const passAuthority = hashPassword('Password123!');
  insertUser.run('usr-authority-01', 'authority_rajesh', 'rajesh.kumar@sdma.gov.in', passAuthority.hash, passAuthority.salt, 'AUTHORITY', 'org-sdma', 'Commander Rajesh Kumar', '+91-98111-22334', 'ed25519_pk_rajesh_01', now);

  const passAdmin = hashPassword('Password123!');
  insertUser.run('usr-admin-01', 'admin_system', 'admin@ursafe.org', passAdmin.hash, passAdmin.salt, 'ADMIN', null, 'System Administrator', '+91-99999-00000', 'ed25519_pk_admin_01', now);

  // 3. Responder Profile
  db.prepare(`
    INSERT INTO responder_profiles (user_id, badge_number, specialization, availability_status, current_latitude, current_longitude, last_location_time)
    VALUES (?, ?, ?, 'ONLINE', 19.0780, 72.8790, ?)
  `).run('usr-responder-01', 'NDRF-B-108', 'MEDICAL_ALS', now);

  // 4. W3C Responder Passport Credential
  db.prepare(`
    INSERT INTO credentials (id, user_id, issuer_org_id, credential_type, role_authorized, capabilities_json, signature, issued_at, expires_at, revocation_status)
    VALUES (?, ?, ?, 'RESPONDER_PASSPORT', 'TACTICAL_ALS_PARAMEDIC', ?, ?, ?, ?, 'ACTIVE')
  `).run(
    'cred-ndrf-vikram-01',
    'usr-responder-01',
    'org-ndrf',
    JSON.stringify(['ALS_TRIAGE', 'WATER_RESCUE', 'DRONE_RECON', 'TRAUMA_MANAGEMENT']),
    'sig_ed25519_ndrf_passport_valid',
    now - 86400000 * 30,
    now + 86400000 * 335
  );

  // 5. Initial Real Seed Incidents
  const insertIncident = db.prepare(`
    INSERT INTO incidents (id, reporter_user_id, category, urgency, latitude, longitude, accuracy_m, location_description, victim_count, description, status, assigned_responder_id, is_simulation, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
  `);

  insertIncident.run(
    'inc-2026-001',
    'usr-citizen-01',
    'FLOOD',
    'CRITICAL',
    19.0760,
    72.8777,
    4.5,
    'S V Road, Near Milan Subway, Santacruz West',
    4,
    'Rising floodwaters trapped 4 people including a 7-month infant on first floor terrace. Power lines downed.',
    'ACCEPTED',
    'usr-responder-01',
    now - 1800000,
    now - 600000
  );

  insertIncident.run(
    'inc-2026-002',
    null,
    'COLLAPSE',
    'HIGH',
    19.0820,
    72.8830,
    8.2,
    'Building 4B, Nehru Nagar Industrial Estate',
    2,
    'Partial stairwell collapse after structural tremor. 2 factory workers trapped in lower basement.',
    'REPORTED',
    null,
    now - 900000,
    now - 900000
  );

  // 6. Assignment for Incident 001
  db.prepare(`
    INSERT INTO assignments (id, incident_id, responder_id, assigned_by_user_id, status, assigned_at, responded_at, notes)
    VALUES (?, ?, ?, ?, 'ACCEPTED', ?, ?, ?)
  `).run(
    'asg-001',
    'inc-2026-001',
    'usr-responder-01',
    'usr-authority-01',
    now - 1200000,
    now - 900000,
    'Unit NDRF-B-108 deployed with inflatable watercraft and ALS trauma pack.'
  );

  // 7. Initial Flight Recorder Audit Root
  db.prepare(`
    INSERT INTO audit_events (id, event_type, actor_id, action, object_id, payload_hash, previous_event_hash, current_event_hash, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    'evt-genesis',
    'SYSTEM_BOOT',
    'system',
    'DATABASE_GENESIS_INITIALIZED',
    'global_state',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    '0000000000000000000000000000000000000000000000000000000000000000',
    crypto.createHash('sha256').update('GENESIS_EVENT_' + now).digest('hex'),
    now
  );
}

seedInitialData();

// Seed Predictive Hazard & Ambient Device Radar Data
function seedPredictiveData() {
  const now = Date.now();

  // 1. Seed additional community citizens if missing
  const insertUser = db.prepare(`
    INSERT OR IGNORE INTO users (id, username, email, password_hash, password_salt, role, full_name, phone_number, public_key, status, created_at)
    VALUES (?, ?, ?, ?, ?, 'CITIZEN', ?, ?, ?, 'ACTIVE', ?)
  `);
  const pass = hashPassword('Password123!');
  insertUser.run('usr-citizen-02', 'citizen_amit', 'amit.verma@example.com', pass.hash, pass.salt, 'Amit Verma', '+91-98201-99881', 'ed25519_pk_amit_02', now);
  insertUser.run('usr-citizen-03', 'citizen_sunita', 'sunita.rao@example.com', pass.hash, pass.salt, 'Sunita Rao', '+91-98334-55667', 'ed25519_pk_sunita_03', now);
  insertUser.run('usr-citizen-04', 'citizen_aarav', 'aarav.mehta@example.com', pass.hash, pass.salt, 'Aarav Mehta', '+91-98199-44332', 'ed25519_pk_aarav_04', now);
  insertUser.run('usr-citizen-05', 'citizen_neha', 'neha.patel@example.com', pass.hash, pass.salt, 'Neha Patel', '+91-98205-11778', 'ed25519_pk_neha_05', now);

  // 2. Seed User Last Known Locations into locations table
  const insertLocation = db.prepare(`
    INSERT OR IGNORE INTO locations (id, user_id, device_id, incident_id, latitude, longitude, accuracy_m, altitude, heading, speed, provider, address, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  insertLocation.run('loc-seed-01', 'usr-citizen-01', 'dev-amb-01', 'inc-2026-001', 19.0760, 72.8777, 3.2, 8.5, 45, 0.2, 'GPS', 'S V Road, Near Milan Subway, Santacruz West, Mumbai', now - 180000);
  insertLocation.run('loc-seed-02', 'usr-responder-01', 'dev-amb-04', 'inc-2026-001', 19.0780, 72.8790, 2.5, 12.0, 180, 4.5, 'GPS', 'Tactical Response Base Sector 4, Santacruz East', now - 120000);
  insertLocation.run('loc-seed-03', 'usr-authority-01', 'dev-amb-08', null, 19.0880, 72.8890, 4.0, 25.0, 0, 0, 'FIXED_TERMINAL', 'Emergency Operations Center, Bandra Kurla Complex', now - 60000);
  insertLocation.run('loc-seed-04', 'usr-admin-01', 'dev-amb-08', null, 19.0910, 72.8850, 5.0, 30.0, 0, 0, 'ETHERNET_GATEWAY', 'Disaster IT Gateway Station, BKC Sector 1', now - 30000);
  insertLocation.run('loc-seed-05', 'usr-citizen-02', 'dev-amb-05', null, 19.0735, 72.8745, 4.8, 3.2, 90, 0.8, 'LORA_MESH', 'Juhu Coastal Road Sector, Santacruz West, Mumbai', now - 240000);
  insertLocation.run('loc-seed-06', 'usr-citizen-03', 'dev-amb-07', 'inc-2026-002', 19.0840, 72.8815, 6.2, 11.5, 270, 0.0, 'BLE_BEACON', 'Nehru Industrial Area, Block 7, Kurla West, Mumbai', now - 360000);
  insertLocation.run('loc-seed-07', 'usr-citizen-04', null, null, 19.0950, 72.8920, 3.0, 48.0, 0, 0, 'GPS', 'Chembur High-Ground Relief Shelter, Chembur, Mumbai', now - 420000);
  insertLocation.run('loc-seed-08', 'usr-citizen-05', null, null, 19.0710, 72.8680, 3.8, 2.1, 135, 1.2, 'CELLULAR_CACHE', 'Khar Danda Coastal Pier, Fisherman Settlement, Mumbai', now - 480000);

  // 3. Seed Ambient Active Devices (Smartwatches, Laptops, Earbuds, BLE Beacons, Home IoT)
  const ambientCount = db.prepare('SELECT COUNT(*) as count FROM ambient_devices').get().count;
  if (ambientCount === 0) {
    const insertAmbient = db.prepare(`
      INSERT INTO ambient_devices (
        id, owner_user_id, device_category, hardware_name, hardware_vendor, mac_address, bluetooth_uuid,
        signal_rssi_dbm, estimated_distance_m, battery_level, latitude, longitude, altitude_m, accuracy_m,
        telemetry_json, connection_protocol, is_active, last_detected_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
    `);

    // ⌚ Smartwatch - Apple Watch Ultra 2 (Priya Sharma)
    insertAmbient.run(
      'dev-amb-01', 'usr-citizen-01', 'SMARTWATCH', 'Apple Watch Ultra 2 (Cellular+BLE)', 'Apple Inc.',
      'E4:5F:01:99:A2:4B', '0xFE26', -58.0, 1.8, 79, 19.0760, 72.8777, 8.5, 3.2,
      JSON.stringify({
        heart_rate_bpm: 114,
        fall_detected: false,
        pulse_ox_percent: 97,
        skin_conductance: 'ELEVATED_STRESS',
        emergency_sos_armed: true,
        steps_today: 4210
      }),
      'BLE_ADVERTISEMENT', now - 45000
    );

    // 💻 Laptop - MacBook Pro M3 (Priya Sharma)
    insertAmbient.run(
      'dev-amb-02', 'usr-citizen-01', 'LAPTOP', 'MacBook Pro 16" (M3 Max - Local Node)', 'Apple Inc.',
      '3C:22:FB:4A:11:88', '0xFE26', -62.0, 2.8, 88, 19.0761, 72.8778, 9.0, 3.5,
      JSON.stringify({
        wifi_direct_mesh: 'ACTIVE',
        outbox_cached_packets: 4,
        storage_free_gb: 240,
        ac_power: 'DISCONNECTED_BATTERY',
        battery_health: 'OPTIMAL_100%'
      }),
      'WIFI_DIRECT_PROBE', now - 60000
    );

    // 🎧 Earbuds - AirPods Pro 2 (Priya Sharma)
    insertAmbient.run(
      'dev-amb-03', 'usr-citizen-01', 'EARBUDS', 'AirPods Pro 2 (Precision Find My)', 'Apple Inc.',
      '90:CD:B6:77:21:E0', '0xFE26', -69.0, 4.2, 92, 19.0760, 72.8776, 8.5, 4.0,
      JSON.stringify({
        in_ear_status: 'IN_CASE_NEARBY',
        acoustic_beacon: 'PULSING_1000HZ',
        find_my_ble: 'BROADCASTING',
        ambient_noise_db: 74
      }),
      'BLE_ADVERTISEMENT', now - 90000
    );

    // ⌚ Smartwatch - Garmin Fenix 7 Solar (Capt. Vikram Singh)
    insertAmbient.run(
      'dev-amb-04', 'usr-responder-01', 'SMARTWATCH', 'Garmin Fenix 7X Solar Tactical', 'Garmin Ltd.',
      '00:1B:44:11:3C:99', '0xFE26', -54.0, 1.2, 94, 19.0780, 72.8790, 12.0, 2.5,
      JSON.stringify({
        heart_rate_bpm: 82,
        pulse_ox_percent: 99,
        barometric_pressure_hpa: 986.2,
        emergency_beacon: 'ARMED',
        solar_charging_active: false
      }),
      'BLE_ADVERTISEMENT', now - 30000
    );

    // 🏷️ BLE / LoRa Safety Tag (Amit Verma)
    insertAmbient.run(
      'dev-amb-05', 'usr-citizen-02', 'BLE_BEACON', 'UrSafe LoRa Life-Safety Tag v2', 'UrSafe Open Hardware',
      'F8:32:E4:00:2B:12', '0xFE26', -76.0, 7.4, 68, 19.0735, 72.8745, 3.2, 4.8,
      JSON.stringify({
        panic_button_state: 'READY',
        lora_865_uplink: 'SYNCHRONIZED',
        motion: 'STATIONARY',
        water_resistant_rating: 'IP68'
      }),
      'LORA_MESH', now - 110000
    );

    // 🏠 Home IoT - Disaster Inverter & Flood Sentry (Household Priya Sharma)
    insertAmbient.run(
      'dev-amb-06', 'usr-citizen-01', 'HOME_IOT', 'Disaster Power Gateway & Sentry Hub', 'Schneider/UrSafe IoT',
      '74:D0:2B:88:99:AA', '0xFE26', -51.0, 0.9, 96, 19.0762, 72.8775, 7.0, 2.0,
      JSON.stringify({
        solar_battery_kwh: 12.4,
        water_leak_sensor_ground: 'TRIGGERED_WATER_DEPTH_42CM',
        grid_ac_power: 'BLACKOUT',
        backup_inverter: 'ON_ISLAND_MODE',
        smoke_detector: 'CLEAR'
      }),
      'HOME_ZIGBEE', now - 20000
    );

    // 🎧 Earbuds - Galaxy Buds 2 Pro (Sunita Rao)
    insertAmbient.run(
      'dev-amb-07', 'usr-citizen-03', 'EARBUDS', 'Samsung Galaxy Buds 2 Pro', 'Samsung Electronics',
      '44:6D:57:12:33:AA', '0xFE26', -72.0, 5.6, 65, 19.0840, 72.8815, 11.5, 5.5,
      JSON.stringify({
        ambient_noise_db: 78,
        ble_chirp_active: true,
        wearing_state: 'DETECTED_IN_LEFT_EAR'
      }),
      'BLE_ADVERTISEMENT', now - 150000
    );

    // 💻 Laptop - ThinkPad P16 Tactical Command Terminal (Rajesh Kumar / SDMA)
    insertAmbient.run(
      'dev-amb-08', 'usr-authority-01', 'LAPTOP', 'Lenovo ThinkPad P16 Tactical Mobile EOC', 'Lenovo Group',
      '50:7B:9D:66:82:11', '0xFE26', -48.0, 0.6, 100, 19.0880, 72.8890, 25.0, 3.0,
      JSON.stringify({
        local_sqlite_wal_synced: true,
        mesh_gateway_role: 'SUPER_ROUTER',
        tx_power_mw: 500,
        active_rf_channels: ['IN_865_LORA', 'BLE_NUS', 'WIFI_DIRECT_5GHZ']
      }),
      'WIFI_DIRECT_PROBE', now - 10000
    );
  }

  // 4. Seed Multi-Hazard Predictions & Weather Forecasting Models
  const hazardCount = db.prepare('SELECT COUNT(*) as count FROM hazard_predictions').get().count;
  if (hazardCount === 0) {
    const insertPrediction = db.prepare(`
      INSERT INTO hazard_predictions (
        id, hazard_type, forecast_title, severity_level, event_timestamp, prediction_lead_time_min,
        kinematic_speed_kmh, kinematic_direction_deg, impact_metrics_json, polygon_geojson,
        evacuation_corridor_geojson, safe_shelters_json, is_active, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    `);

    // Hazard 1: FLOOD Inundation & Hydrological Surge
    insertPrediction.run(
      'haz-pred-flood-01',
      'FLOOD',
      'Mithi Basin & Milan Subway Hydrological Inundation',
      'CRITICAL_WATCH',
      now,
      25,
      1.8,
      135.0,
      JSON.stringify({
        peak_flood_depth_m: 2.4,
        current_water_level_m: 1.6,
        rate_of_rise_cm_per_hr: 45,
        river_discharge_cumec: 280,
        inundated_structures_est: 1840,
        impassable_roads: ['S V Road Underpass', 'Milan Subway', 'Vakola Nullah Bridge', 'Nehru Road Crossing'],
        weather_trigger: 'Torrential Monsoon Downpour (185 mm / 6 hrs)'
      }),
      JSON.stringify({
        type: 'Polygon',
        coordinates: [[
          [72.8700, 19.0700],
          [72.8860, 19.0710],
          [72.8890, 19.0820],
          [72.8740, 19.0845],
          [72.8680, 19.0780],
          [72.8700, 19.0700]
        ]]
      }),
      JSON.stringify({
        type: 'LineString',
        coordinates: [
          [72.8760, 19.0760],
          [72.8820, 19.0800],
          [72.8900, 19.0870],
          [72.8950, 19.0920]
        ]
      }),
      JSON.stringify([
        { name: 'Santacruz High School Safe Shelter', lat: 19.0840, lon: 72.8880, capacity: 650, current_occupancy: 142, status: 'OPEN_SUPPLIES_STOCKED' },
        { name: 'BKC Sports Complex High-Ground Center', lat: 19.0890, lon: 72.8920, capacity: 1200, current_occupancy: 280, status: 'OPEN_MEDICAL_ON_SITE' }
      ]),
      now, now
    );

    // Hazard 2: TSUNAMI Coastal Wave Front & Storm Surge
    insertPrediction.run(
      'haz-pred-tsunami-02',
      'TSUNAMI',
      'Arabian Sea Continental Subduction Tsunami Inundation',
      'HIGH_WARNING',
      now,
      22,
      38.0,
      95.0,
      JSON.stringify({
        estimated_arrival_eta_min: 22,
        crest_wave_height_m: 3.8,
        coastal_runup_elevation_m: 5.2,
        inundation_depth_onshore_m: 1.8,
        danger_band_width_km: 1.2,
        tidal_buoy_reading_m: '+3.4m over Mean High Water',
        affected_coastal_settlements: ['Juhu Fishermen Colony', 'Khar Danda Beach Front', 'Bandra Carter Promenade']
      }),
      JSON.stringify({
        type: 'Polygon',
        coordinates: [[
          [72.8120, 19.0550],
          [72.8360, 19.0550],
          [72.8420, 19.0980],
          [72.8180, 19.0980],
          [72.8120, 19.0550]
        ]]
      }),
      JSON.stringify({
        type: 'LineString',
        coordinates: [
          [72.8250, 19.0700],
          [72.8500, 19.0720],
          [72.8750, 19.0780],
          [72.8950, 19.0900]
        ]
      }),
      JSON.stringify([
        { name: 'Mount Mary Ridge Safe Refuge', lat: 19.0510, lon: 72.8280, capacity: 400, current_occupancy: 95, status: 'OPEN_HIGH_ELEVATION' },
        { name: 'University Campus Hill Shelter', lat: 19.0780, lon: 72.8980, capacity: 1500, current_occupancy: 310, status: 'OPEN_TRIAGE_READY' }
      ]),
      now, now
    );

    // Hazard 3: EARTHQUAKE & Seismic Shakemap Modeling
    insertPrediction.run(
      'haz-pred-quake-03',
      'EARTHQUAKE',
      'Western Continental Margin Fault Rupture (Shakemap)',
      'CRITICAL_WATCH',
      now,
      5,
      0.0,
      0.0,
      JSON.stringify({
        richter_magnitude: 6.6,
        epicenter_lat: 19.072,
        epicenter_lon: 72.870,
        depth_km: 11.4,
        peak_ground_acceleration_g: 0.52,
        peak_ground_velocity_cms: 48.6,
        modified_mercalli_intensity: 'VIII (Destructive Shaking)',
        liquefaction_susceptibility: 'VERY_HIGH along soft coastal sediment',
        aftershock_probability_24h: '78%'
      }),
      JSON.stringify({
        type: 'Polygon',
        coordinates: [[
          [72.8580, 19.0620],
          [72.8950, 19.0620],
          [72.9020, 19.0980],
          [72.8520, 19.0920],
          [72.8580, 19.0620]
        ]]
      }),
      JSON.stringify({
        type: 'LineString',
        coordinates: [
          [72.8700, 19.0750],
          [72.8800, 19.0850],
          [72.8920, 19.0950]
        ]
      }),
      JSON.stringify([
        { name: 'BKC Open Grounds Seismic Gathering Zone', lat: 19.0680, lon: 72.8680, capacity: 5000, current_occupancy: 820, status: 'OPEN_ZERO_OVERHEAD_COLLAPSE_RISK' }
      ]),
      now, now
    );

    // Hazard 4: CYCLONE & Severe Weather Storm Track
    insertPrediction.run(
      'haz-pred-cyclone-04',
      'CYCLONE',
      'Very Severe Cyclonic Storm "Cascade" Doppler Radar Vector',
      'HIGH_WARNING',
      now,
      60,
      26.0,
      48.0,
      JSON.stringify({
        central_pressure_hpa: 968.0,
        sustained_wind_speed_kmh: 135,
        peak_wind_gusts_kmh: 165,
        doppler_radar_reflectivity_dbz: 56.5,
        hourly_rainfall_rate_mm: 58.0,
        storm_surge_coastal_m: 2.8,
        eye_diameter_km: 26.0,
        forward_motion: '26 km/h heading North-East (48°)'
      }),
      JSON.stringify({
        type: 'Polygon',
        coordinates: [[
          [72.8350, 19.0420],
          [72.9150, 19.0460],
          [72.9250, 19.1180],
          [72.8280, 19.1120],
          [72.8350, 19.0420]
        ]]
      }),
      JSON.stringify({
        type: 'LineString',
        coordinates: [
          [72.8500, 19.0500],
          [72.8800, 19.0800],
          [72.9100, 19.1100]
        ]
      }),
      JSON.stringify([
        { name: 'Chembur Concrete Relief Bunker', lat: 19.0960, lon: 72.8940, capacity: 800, current_occupancy: 210, status: 'OPEN_STORM_RATED_REINFORCED' }
      ]),
      now, now
    );
  }
}

seedPredictiveData();

module.exports = {
  db,
  hashPassword,
  verifyPassword,
  seedPredictiveData
};


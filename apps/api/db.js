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

module.exports = {
  db,
  hashPassword,
  verifyPassword
};

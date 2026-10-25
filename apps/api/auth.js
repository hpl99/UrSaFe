/**
 * UrSafe Authentication & Role-Based Authorization Engine
 * Secure token management, PBKDF2 verification, and RBAC middleware.
 */
const crypto = require('crypto');
const { db, hashPassword, verifyPassword } = require('./db');

// In-Memory active session cache: token -> { userId, username, role, orgId, expiresAt }
const activeSessions = new Map();

// Helper to log audit events into flight recorder
function logAuditEvent(eventType, actorId, action, objectId, payload = {}) {
  const now = Date.now();
  const payloadStr = JSON.stringify(payload);
  const payloadHash = crypto.createHash('sha256').update(payloadStr).digest('hex');

  const lastEvent = db.prepare('SELECT current_event_hash FROM audit_events ORDER BY timestamp DESC LIMIT 1').get();
  const prevHash = lastEvent ? lastEvent.current_event_hash : '0000000000000000000000000000000000000000000000000000000000000000';
  const currentHash = crypto.createHash('sha256').update(prevHash + eventType + actorId + action + objectId + payloadHash + now).digest('hex');

  const eventId = 'evt-' + crypto.randomUUID();
  db.prepare(`
    INSERT INTO audit_events (id, event_type, actor_id, action, object_id, payload_hash, previous_event_hash, current_event_hash, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(eventId, eventType, actorId, action, objectId, payloadHash, prevHash, currentHash, now);

  return eventId;
}

// Generate secure session token
function createSession(user) {
  const token = 'ursafe_sess_' + crypto.randomBytes(32).toString('hex');
  const expiresAt = Date.now() + 86400000 * 7; // 7 days

  const sessionData = {
    token,
    userId: user.id,
    username: user.username,
    fullName: user.full_name,
    role: user.role,
    organizationId: user.organization_id,
    expiresAt
  };

  activeSessions.set(token, sessionData);

  // Update last login
  db.prepare('UPDATE users SET last_login_at = ? WHERE id = ?').run(Date.now(), user.id);
  logAuditEvent('AUTH_LOGIN', user.id, 'USER_LOGIN_SUCCESS', user.id, { role: user.role });

  return sessionData;
}

// Register new user
function registerUser({ username, email, password, role, fullName, phoneNumber, organizationId }) {
  if (!username || !password || !role || !fullName) {
    throw new Error('Missing required registration fields (username, password, role, fullName)');
  }

  const validRoles = ['CITIZEN', 'RESPONDER', 'AUTHORITY', 'ADMIN'];
  if (!validRoles.includes(role)) {
    throw new Error(`Invalid role '${role}'. Must be one of: ${validRoles.join(', ')}`);
  }

  const existing = db.prepare('SELECT id FROM users WHERE username = ? OR (email IS NOT NULL AND email = ?)').get(username, email || '');
  if (existing) {
    throw new Error(`Username '${username}' or email already in use`);
  }

  const { hash, salt } = hashPassword(password);
  const userId = 'usr-' + crypto.randomUUID();
  const now = Date.now();

  db.prepare(`
    INSERT INTO users (id, username, email, password_hash, password_salt, role, organization_id, full_name, phone_number, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
  `).run(userId, username, email || null, hash, salt, role, organizationId || null, fullName, phoneNumber || null, now);

  // If responder, initialize profile
  if (role === 'RESPONDER') {
    db.prepare(`
      INSERT INTO responder_profiles (user_id, badge_number, specialization, availability_status, last_location_time)
      VALUES (?, ?, 'GENERAL', 'ONLINE', ?)
    `).run(userId, 'VOL-' + Math.floor(1000 + Math.random() * 9000), now);
  }

  logAuditEvent('AUTH_REGISTER', userId, 'USER_REGISTERED', userId, { role, username });

  const newUser = db.prepare('SELECT id, username, role, full_name, organization_id FROM users WHERE id = ?').get(userId);
  return createSession(newUser);
}

// Authenticate with username and password
function loginUser(username, password) {
  const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
  if (!user) {
    logAuditEvent('AUTH_FAILURE', 'unknown', 'LOGIN_FAILED_NO_USER', username);
    throw new Error('Invalid username or password');
  }

  if (user.status !== 'ACTIVE') {
    logAuditEvent('AUTH_FAILURE', user.id, 'LOGIN_FAILED_INACTIVE', user.id);
    throw new Error(`Account status is ${user.status}. Please contact an administrator.`);
  }

  const isValid = verifyPassword(password, user.password_hash, user.password_salt);
  if (!isValid) {
    logAuditEvent('AUTH_FAILURE', user.id, 'LOGIN_FAILED_BAD_PASSWORD', user.id);
    throw new Error('Invalid username or password');
  }

  return createSession(user);
}

// Invalidate session
function logoutUser(token) {
  const session = activeSessions.get(token);
  if (session) {
    logAuditEvent('AUTH_LOGOUT', session.userId, 'USER_LOGOUT', session.userId);
    activeSessions.delete(token);
  }
}

// Middleware: Authenticate request token
function authenticateRequest(req) {
  const authHeader = req.headers['authorization'] || '';
  if (!authHeader.startsWith('Bearer ')) {
    return null;
  }

  const token = authHeader.slice(7).trim();
  const session = activeSessions.get(token);
  if (!session) {
    return null;
  }

  if (Date.now() > session.expiresAt) {
    activeSessions.delete(token);
    return null;
  }

  return session;
}

// Enforce role authorization
function authorizeRoles(session, allowedRoles) {
  if (!session) {
    return { authorized: false, status: 401, error: 'Authentication required. Missing or invalid Bearer token.' };
  }

  if (!allowedRoles.includes(session.role)) {
    logAuditEvent('ACCESS_DENIED', session.userId, 'UNAUTHORIZED_ROLE_ACCESS', session.role, { allowedRoles });
    return { authorized: false, status: 403, error: `Forbidden: role '${session.role}' is not authorized for this operation.` };
  }

  return { authorized: true };
}

module.exports = {
  createSession,
  registerUser,
  loginUser,
  logoutUser,
  authenticateRequest,
  authorizeRoles,
  logAuditEvent,
  activeSessions
};

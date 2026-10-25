# UrSafe Authentication, Authorization & Identity Specification

## 1. Security Threat Model & OWASP MASVS Principles

In a disaster scenario, communication infrastructure is compromised and malicious actors may attempt to forge emergency calls, divert rescue personnel, impersonate authorities, or alter audit logs.

UrSafe adheres to **OWASP Mobile Application Security Verification Standard (MASVS)**:
- **MASVS-AUTH**: Mandatory authentication prior to accessing operational command features.
- **MASVS-CRYPTO**: Industry-standard cryptographic primitives (Ed25519, SHA-256, PBKDF2-HMAC-SHA512).
- **MASVS-STORAGE**: Zero plain-text credentials stored in client memory or local databases.

---

## 2. Password Hashing & Key Derivation

All stored passwords use PBKDF2 with high computational cost parameters to resist offline brute-force attacks:

- **Algorithm**: `PBKDF2` (Password-Based Key Derivation Function 2)
- **Hash Function**: `HMAC-SHA-512`
- **Iterations**: `100,000` rounds
- **Salt Length**: `64 bytes` cryptographically random per user (CSPRNG)
- **Key Length**: `64 bytes` derived key

---

## 3. Strict Server-Side Role Enforcement (Section 12)

Clients can NEVER supply their own role (e.g. `role = ADMIN`) to gain escalated privileges.

### Authentication Flow:
1. Client submits `{ username, password }` to `/api/v1/auth/login`.
2. API Gateway verifies password against PBKDF2 hash and salt in `users` table.
3. API Gateway retrieves the assigned role from `roles` table:
   - `CITIZEN` (Civilian, Help Seeker)
   - `RESPONDER` (Authorized Tactical Field Volunteer)
   - `AUTHORITY` (Disaster Management Authority Dispatcher)
   - `ADMIN` (System Security & Fleet Administrator)
4. A signed 7-day Bearer token is issued: `ursafe_sess_<64-hex-token>`.
5. Role permissions are enforced on every subsequent request by `requireRole(...)` middleware.

---

## 4. Hardware Keystore & Ed25519 Device Keys

For offline operation without internet or central servers, each field device generates a local asymmetric keypair in the hardware security module (Android Keystore / StrongBox):

- **Algorithm**: `Ed25519` (RFC 8032)
- **Public Key**: Broadcast in Protobuf envelope headers for message attribution.
- **Private Key**: Never leaves the hardware keystore; used to sign SOS envelopes, dispatch acceptances, and evidence integrity metadata.

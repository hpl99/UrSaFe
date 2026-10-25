# ADR-009: W3C Verifiable Credentials Responder Passport & Revocation States

## Status
Approved

## Context
Responders must present credentials proving their medical, firefighting, or technical certifications to coordinators and victims offline. Online identity providers (OAuth, OpenID Connect) are unreachable during blackouts. Traditional PKI (X.509) is too heavy and assumes online CRL/OCSP servers.

## Decision
1. Implement the UrSafe **Responder Passport** using W3C Verifiable Credentials principles signed with Ed25519.
2. The credential payload specifies:
   - `credential_id`, `issuer_id`, `subject_id`, `roles` (`MEDIC`, `SEARCH_AND_RESCUE`, `FIREFIGHTER`, `LOGISTICS`), `skills`, `certifications`, `issued_at`, `expires_at`, `signature`.
3. Offline verifiers validate signature integrity against cached authority public keys.
4. Revocation semantics in offline environments are explicitly categorized in the UI:
   - `VERIFIED`: Valid signature, not expired, recent revocation delta list checked.
   - `VERIFIED_REVOCATION_STALE`: Valid signature, but revocation list age exceeds threshold ($>24\text{ hours}$).
   - `EXPIRED`: Timestamp has elapsed.
   - `REVOKED`: Listed on received revocation delta list.
   - `UNKNOWN`: Unrecognized issuing authority.

## Consequences
- **Positive:** Unambiguous, fraud-resistant proof of skills without internet access.
- **Trade-off:** Responders must pre-cache credentials or carry signed QR/NFC/BLE tokens.

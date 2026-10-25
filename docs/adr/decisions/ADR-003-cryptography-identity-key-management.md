# ADR-003: Cryptographic Identity, Ed25519/X25519 & Hardware Keystore

## Status
Approved

## Context
Ad-hoc emergency networks are vulnerable to impersonation, packet spoofing, eavesdropping, and tampering. Demo-grade shared symmetric keys provide zero authentication and allow any single compromised node to forge messages across the entire mesh. Furthermore, user identity must be clearly segregated from physical device identity.

## Decision
1. Identity is cryptographic and decentralized:
   - **Signing Key**: Ed25519 (256-bit elliptic curve) for signing messages and credentials.
   - **Key Agreement**: X25519 for Diffie-Hellman ephemeral key derivation.
   - **Symmetric Encryption**: ChaCha20-Poly1305 / AES-256-GCM AEAD for authenticated payload encryption.
2. Segregate identities into four distinct layers:
   - `Device Identity`: Unique hardware cryptographic key stored in Android Keystore / TPM.
   - `User Identity`: Sovereign keypair associated with civilian account.
   - `Responder Identity`: Keypair linked to verified responder certifications.
   - `Organization Identity`: Recognized issuing authority public keys.
3. Private keys are generated on-device and NEVER transmitted in plaintext.

## Consequences
- **Positive:** Mathematically sound authentication, replay resistance, and confidentiality across untrusted physical radios.
- **Trade-off:** Small signature overhead (64 bytes for Ed25519) on constrained radio packets; addressed by compact binary framing.

# ADR-004: Schema-First Binary Envelope & Versioned Emergency Protocol

## Status
Approved

## Context
Emergency communications across LoRa and BLE cannot afford bloated JSON payloads. A typical 200-byte JSON structure consumes nearly the entire LoRa payload capacity (237 bytes max) for a single packet without leaving room for signatures or routing headers. Furthermore, untyped ad-hoc dictionary passing causes silent field mismatch bugs across heterogeneous clients (Android, Web, API).

## Decision
1. Standardize on a schema-first Protocol Buffer / compact binary wire envelope.
2. The envelope defines:
   - Header: `message_id` (UUID/16B), `sender_id` (16B truncated hash), `recipient_id` (broadcast or unicast), `created_at` (epoch timestamp), `expires_at` (epoch timestamp), `priority` (EMERGENCY=0, HIGH=1, ROUTINE=2, TELEMETRY=3), `message_type` (Enum), `sequence` (uint32), `hop_limit` (uint8), `origin` (16B), `current_hop` (16B).
   - Integrity & Security: `payload_hash` (SHA-256), `signature` (Ed25519 64B), `encryption_metadata` (cipher, nonce, key_id).
   - Body: Serialized typed payload.
3. Establish 24 explicit versioned emergency message types covering lifecycle from `SOS_CREATED` to `RESCUE_RECEIPT`.

## Consequences
- **Positive:** Sub-100 byte overhead, strict type safety, zero wire ambiguity, forward and backward compatibility.
- **Trade-off:** Requires schema compilation tooling (`protoc` / TypeScript & Python bindings).

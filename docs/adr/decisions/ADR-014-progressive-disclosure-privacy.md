# ADR-014: 5-Tier Progressive Location Disclosure & Privacy Architecture

## Status
Approved

## Context
Broadcasting high-precision GPS coordinates and personal health data in plaintext over an open radio mesh invites hostile actors, looters, or stalkers to target vulnerable victims. However, responders and coordinators need accurate data to conduct rescues.

## Decision
1. Implement a 5-tier Progressive Information Disclosure architecture:
   - **Level 0 (Public Mesh)**: Anonymous signal indicating an active emergency exists in a sector.
   - **Level 1 (Regional Mesh)**: Coarse geohash (~2 km area) + emergency category (e.g., FLOOD).
   - **Level 2 (Dispatched Responders)**: Unit assignment and broad navigational vector.
   - **Level 3 (Assigned & Accepted Responder)**: High-precision GPS coordinates ($\pm 5\text{ m}$) and contact info, encrypted with the responder's public key.
   - **Level 4 (Authorized Medical)**: Sensitive medical notes and triage details, disclosed only under strict role policies.
2. Every tier transition is recorded in the Flight Recorder audit log.

## Consequences
- **Positive:** Protects civilian privacy and physical safety while still enabling rapid mesh discovery.
- **Trade-off:** Requires asymmetric encryption of level 3/4 payloads to specific assigned responder keys.

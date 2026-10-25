# UrSafe Test Strategy & Verification Matrix

## 1. Multi-Tier Testing Philosophy

UrSafe employs rigorous testing across five distinct tiers to guarantee life-safety reliability:

```text
               ▲
              / \     E2E Acceptance Simulation
             /   \    (python scripts/run_acceptance_demo.py)
            /     \
           /       \   Red-Team Adversarial & Fuzz Testing
          /         \  (tests/test_red_team.py, test_crdt_fuzzer.py)
         /           \
        /             \ Integration & API Tests
       /               \ (tests/test_backend_api.py, test_sync.py)
      /                 \
     /═══════════════════\ Unit Tests & Core Invariants
    /                     \ (53 pytest modules, cargo test ursafe-core-rs)
   ─────────────────────────
```

---

## 2. Test Execution Matrix

| Test Suite | Scope | Command | Target / Assertion |
|---|---|---|---|
| **Python Unit Suite** | Crypto, Protocol, DTN, Routing, Trust | `pytest tests/ -v` | 53 tests passing (100% success) |
| **Rust Core Tests** | Vector Clocks, Ed25519, Envelopes | `cargo test` | 3 Rust tests passing |
| **Backend REST & WS** | PBKDF2 Auth, RBAC, Health, Incidents | `pytest tests/test_backend_api.py -v` | Verifies real HTTP API endpoints |
| **Acceptance Demo** | Complete multi-hop LoRa mesh simulation | `python scripts/run_acceptance_demo.py` | 100% operational with zero internet |
| **Red Team Fuzzer** | Packet replay, tampering, Sybil flood | `pytest tests/test_red_team.py -v` | All 8 adversarial attacks rejected |
| **CRDT Fuzzing** | Random network partition state merges | `pytest tests/test_crdt_fuzzer.py -v` | Strict mathematical state convergence |

---

## 3. End-to-End Acceptance Path (Section 62)

The minimum acceptance verification workflow validated by the test suite:

```text
Real User -> Login (PBKDF2) -> Role Resolved -> Android App -> GPS Location
  -> Bluetooth Enabled -> Compatible Radio Discovered -> Radio Connected
  -> Device Identity Verified -> Connection Center Shows Real Radio
  -> Citizen Creates SOS -> SOS Stored Locally in SQLite Outbox
  -> SOS Transmitted via LoRa Mesh -> Responder Receives Alert
  -> Responder Accepts Mission -> Authority Sees Real-time Update
  -> Real Geographic Map Shows Incident + Responder
  -> Responder Arrives On Scene -> Photographic Evidence Uploaded
  -> Structured Rescue Report Submitted -> Authority Verifies SHA-256 Hash
  -> Rescue Receipt Co-Signed -> Immutable Audit Trail Updated
```
All tested and passing with zero central internet connectivity.

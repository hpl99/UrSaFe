# UrSafe Engineering Baseline

## 1. System Environment

- **Operating System**: Windows 11
- **Node.js**: v24.19.0
- **Python**: 3.13.15
- **Rust / Cargo**: 1.99.1
- **Git**: 2.49.0
- **Working Tree**: Clean (`main` branch)

---

## 2. Test Execution Baseline

### 2.1 Python Test Suite (53 Tests)
Command:
```powershell
pytest tests/ -v
```
Result:
```text
tests\test_acceptance.py .                                               [  1%]
tests\test_audit.py ...                                                  [  7%]
tests\test_backend_api.py ....                                           [ 15%]
tests\test_crdt_fuzzer.py .                                              [ 16%]
tests\test_credentials_and_receipts.py ..                                [ 20%]
tests\test_crypto.py .....                                               [ 30%]
tests\test_data_mule.py .                                                [ 32%]
tests\test_domain_and_crdt.py ....                                       [ 39%]
tests\test_hazard_and_dispatch.py ...                                    [ 45%]
tests\test_nlp_and_calibration.py .....                                  [ 54%]
tests\test_protocol.py ....                                              [ 62%]
tests\test_red_team.py ........                                          [ 77%]
tests\test_routing_and_hardware.py .....                                 [ 86%]
tests\test_sync.py ...                                                   [ 92%]
tests\test_trust_and_sybil.py ....                                       [100%]

============================= 53 passed in 0.95s ==============================
```

### 2.2 Rust Protocol & Cryptographic Core Tests
Command:
```powershell
cargo test
```
Result:
```text
running 3 tests
test tests::test_rust_vector_clock_merge ... ok
test tests::test_rust_protocol_envelope ... ok
test tests::test_rust_ed25519_sign_verify ... ok

test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s
```

### 2.3 End-to-End Acceptance Demo
Command:
```powershell
python scripts/run_acceptance_demo.py
```
Result:
```text
======================================================================
 ACCEPTANCE DEMO PASSED: 100% OPERATIONAL WITHOUT INTERNET
======================================================================
```

### 2.4 Backend Health Probe Baseline
Endpoint: `http://localhost:3000/api/v1/health`
Status: `HEALTHY` (Subsystems: `api`, `database`, `authentication`, `websocket`, `sync_service`, `mesh_gateway`).

"""
Automated Integration Tests for UrSafe Multi-Role Backend, Database & RBAC API.
Executes against the real Node.js API and SQLite database engine.
"""

import os
import subprocess
import time
import json
import urllib.request
import urllib.error
import pytest


@pytest.fixture(scope="module")
def api_server():
    """Starts the real backend API server on a dedicated test port."""
    port = 4099
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.Popen(
        ["node", "apps/api/server.js"],
        env=env
    )

    # Wait for server ready
    base_url = f"http://localhost:{port}"
    ready = False
    for _ in range(30):
        try:
            req = urllib.request.urlopen(f"{base_url}/api/v1/health", timeout=1)
            if req.status == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.1)

    if not ready:
        proc.kill()
        raise RuntimeError("Failed to start test API server on port 4099")

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


def make_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, json.loads(err_body) if err_body else {}


def test_health_check(api_server):
    status, data = make_request(f"{api_server}/api/v1/health")
    assert status == 200
    assert data["status"] in ("ok", "HEALTHY")
    assert "stats" in data
    assert data["stats"]["total_incidents"] >= 2


def test_auth_login_success_and_failure(api_server):
    # Valid login
    status, data = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "responder_vikram", "password": "Password123!"}
    )
    assert status == 200
    assert data["session"]["role"] == "RESPONDER"
    token = data["session"]["token"]

    # Invalid password
    bad_status, bad_data = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "responder_vikram", "password": "WrongPassword"}
    )
    assert bad_status == 500 or bad_status == 401
    assert "error" in bad_data

    # Current user /me
    me_status, me_data = make_request(f"{api_server}/api/v1/auth/me", token=token)
    assert me_status == 200
    assert me_data["user"]["full_name"] == "Capt. Vikram Singh"


def test_unauthenticated_protected_route_rejection(api_server):
    status, data = make_request(f"{api_server}/api/v1/auth/me")
    assert status == 401
    assert "error" in data


def test_full_incident_and_rescue_lifecycle(api_server):
    # 1. Login Citizen
    _, cit_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "citizen_priya", "password": "Password123!"}
    )
    cit_token = cit_login["session"]["token"]

    # 2. Citizen creates SOS
    sos_payload = {
        "category": "FLOOD",
        "urgency": "CRITICAL",
        "latitude": 19.0792,
        "longitude": 72.8798,
        "victim_count": 3,
        "description": "Rising floodwaters trapped 3 persons on rooftop",
        "is_simulation": 0
    }
    status, sos_data = make_request(
        f"{api_server}/api/v1/incidents",
        method="POST",
        data=sos_payload,
        token=cit_token
    )
    assert status == 201
    incident_id = sos_data["incident"]["id"]
    assert sos_data["incident"]["status"] == "REPORTED"

    # 3. Login Authority
    _, auth_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "authority_rajesh", "password": "Password123!"}
    )
    auth_token = auth_login["session"]["token"]

    # 4. Authority Dispatches Responder
    status, dispatch_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/assign",
        method="POST",
        data={"responder_id": "usr-responder-01", "notes": "Deploying NDRF watercraft unit"},
        token=auth_token
    )
    assert status == 200
    assert dispatch_data["incident"]["status"] == "DISPATCHED"

    # 5. Login Responder
    _, resp_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "responder_vikram", "password": "Password123!"}
    )
    resp_token = resp_login["session"]["token"]

    # 6. Responder Accepts Assignment
    status, accept_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/accept",
        method="POST",
        token=resp_token
    )
    assert status == 200
    assert accept_data["incident"]["status"] == "ACCEPTED"

    # 7. Responder Updates Status to ON_SCENE
    status, scene_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/status",
        method="POST",
        data={"status": "ON_SCENE", "notes": "On scene with flood boat"},
        token=resp_token
    )
    assert status == 200
    assert scene_data["incident"]["status"] == "ON_SCENE"

    # 8. Responder Uploads Photographic Evidence with SHA-256
    status, evd_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/evidence",
        method="POST",
        data={
            "evidence_type": "PHOTO",
            "file_name": "rooftop_extraction.jpg",
            "file_data_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
            "latitude": 19.0792,
            "longitude": 72.8798
        },
        token=resp_token
    )
    assert status == 201
    assert "sha256_hash" in evd_data["evidence"]

    # 9. Responder Submits Structured Rescue Report
    status, rpt_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/rescue-report",
        method="POST",
        data={
            "outcome": "RESCUED",
            "patients_treated": 3,
            "summary_notes": "All 3 victims safely evacuated to Santacruz relief shelter."
        },
        token=resp_token
    )
    assert status == 201
    assert rpt_data["report"]["verification_status"] == "PENDING"

    # 10a. Security check: Citizen attempting to verify rescue directly must be REJECTED (403 Forbidden)
    unauth_status, unauth_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/verify-rescue",
        method="POST",
        data={"action": "VERIFY", "notes": "Hacker attempt"},
        token=cit_token
    )
    assert unauth_status == 403
    assert "error" in unauth_data

    # 10b. Authority Reviews and Verifies Rescue
    status, verify_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/verify-rescue",
        method="POST",
        data={"action": "VERIFY", "notes": "Photographic evidence matches coordinates"},
        token=auth_token
    )
    assert status == 200
    assert verify_data["incident"]["status"] == "VERIFIED"
    assert verify_data["report"]["verification_status"] == "VERIFIED"

    # 10c. Citizen Co-signs Rescue Receipt (Dual Confirmation)
    cosign_status, cosign_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/confirm-rescue",
        method="POST",
        data={"victim_signature": "sig_ed25519_priya_cosign_ok"},
        token=cit_token
    )
    assert cosign_status == 200
    assert cosign_data["report"]["victim_signature"] == "sig_ed25519_priya_cosign_ok"

    # 11. Flight Recorder Audit Chain Verification
    status, audit_data = make_request(f"{api_server}/api/v1/audit/flight-recorder", token=auth_token)
    assert status == 200
    assert audit_data["status"] == "CHAIN_INTACT"
    assert audit_data["verified"] is True
    assert audit_data["chain_length"] >= 8


def test_state_machine_transition_close_and_reopen(api_server):
    # Authenticate Authority
    _, auth_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "authority_rajesh", "password": "Password123!"}
    )
    auth_token = auth_login["session"]["token"]

    # 1. Create an emergency
    status, sos_data = make_request(
        f"{api_server}/api/v1/emergencies",
        method="POST",
        data={
            "category": "MEDICAL",
            "urgency": "CRITICAL",
            "latitude": 28.6508,
            "longitude": 77.2300,
            "victim_count": 1,
            "description": "Severe heat stroke in crowded bazaar",
            "status": "SOS_CREATED"
        },
        token=auth_token
    )
    assert status == 201
    inc_id = sos_data["incident"]["id"]

    # 2. Transition through state machine
    status, trans_data = make_request(
        f"{api_server}/api/v1/emergencies/{inc_id}/transition",
        method="POST",
        data={
            "new_state": "RESPONDER_ASSIGNED",
            "reason": "Dispatched ALS Medic Unit",
            "device_id": "ble-tablet-01"
        },
        token=auth_token
    )
    assert status == 200
    assert trans_data["incident"]["status"] == "RESPONDER_ASSIGNED"
    assert trans_data["transition_event"]["new_state"] == "RESPONDER_ASSIGNED"

    # 3. Transition to VERIFIED
    status, verif_data = make_request(
        f"{api_server}/api/v1/emergencies/{inc_id}/transition",
        method="POST",
        data={"new_state": "VERIFIED", "reason": "Patient treated and stable"},
        token=auth_token
    )
    assert status == 200
    assert verif_data["incident"]["status"] == "VERIFIED"

    # 4. Close incident
    status, close_data = make_request(
        f"{api_server}/api/v1/emergencies/{inc_id}/close",
        method="POST",
        data={"reason": "Case fully verified and documented"},
        token=auth_token
    )
    assert status == 200
    assert close_data["incident"]["status"] == "CLOSED"

    # 5. Verify Timeline contains all events
    status, timeline = make_request(f"{api_server}/api/v1/emergencies/{inc_id}/timeline", token=auth_token)
    assert status == 200
    assert len(timeline) >= 4
    assert timeline[0]["to_status"] == "SOS_CREATED"
    assert timeline[-1]["to_status"] == "CLOSED"

    # 6. Reopen incident
    status, reopen_data = make_request(
        f"{api_server}/api/v1/emergencies/{inc_id}/reopen",
        method="POST",
        data={"reason": "Patient relapse reported by bystander"},
        token=auth_token
    )
    assert status == 200
    assert reopen_data["incident"]["status"] == "REOPENED"


def test_evidence_validation_and_duplicate_detection(api_server):
    # Authenticate Responder
    _, resp_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "responder_vikram", "password": "Password123!"}
    )
    resp_token = resp_login["session"]["token"]

    inc_id = "inc-2026-001"

    # 1. Invalid MIME type should be rejected
    bad_mime_status, bad_mime_data = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/evidence",
        method="POST",
        data={
            "mime_type": "application/x-executable",
            "file_name": "malicious.exe",
            "file_data_base64": "ZXhlY3V0YWJsZQ=="
        },
        token=resp_token
    )
    assert bad_mime_status == 400
    assert "Invalid file type" in bad_mime_data["error"]

    # 2. Valid image upload
    import base64
    test_image_b64 = base64.b64encode(f"TEST_IMAGE_PAYLOAD_{time.time()}".encode()).decode()
    status, evd_data = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/evidence",
        method="POST",
        data={
            "mime_type": "image/png",
            "file_name": "flood_scene_02.png",
            "file_data_base64": test_image_b64,
            "description": "Water level gauge reading 1.8 meters"
        },
        token=resp_token
    )
    assert status == 201
    assert "sha256_hash" in evd_data["evidence"]

    # 3. Duplicate content upload should be rejected with 409 Conflict
    dup_status, dup_data = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/evidence",
        method="POST",
        data={
            "mime_type": "image/png",
            "file_name": "flood_scene_duplicate.png",
            "file_data_base64": test_image_b64
        },
        token=resp_token
    )
    assert dup_status == 409
    assert "Duplicate evidence detected" in dup_data["error"]


def test_emergency_history_and_active_separation(api_server):
    _, auth_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "authority_rajesh", "password": "Password123!"}
    )
    auth_token = auth_login["session"]["token"]

    # Fetch active emergencies
    status_act, active_cases = make_request(f"{api_server}/api/v1/emergencies?active=true", token=auth_token)
    assert status_act == 200
    for case in active_cases:
        assert case["status"] not in ("VERIFIED", "CLOSED", "CANCELLED")

    # Fetch historical emergencies
    status_hist, history_cases = make_request(f"{api_server}/api/v1/emergencies?history=true", token=auth_token)
    assert status_hist == 200
    for case in history_cases:
        assert case["status"] in ("VERIFIED", "CLOSED", "CANCELLED")


def test_locations_and_device_presence(api_server):
    _, resp_login = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": "responder_vikram", "password": "Password123!"}
    )
    resp_token = resp_login["session"]["token"]

    # 1. Post real location
    status, loc_res = make_request(
        f"{api_server}/api/v1/locations",
        method="POST",
        data={
            "latitude": 19.0782,
            "longitude": 72.8791,
            "accuracy_m": 4.1,
            "speed": 2.5,
            "provider": "GPS_FUSED"
        },
        token=resp_token
    )
    assert status == 201
    assert loc_res["location"]["accuracy_m"] == 4.1

    # 2. Get live locations
    status_get, live_locs = make_request(f"{api_server}/api/v1/locations", token=resp_token)
    assert status_get == 200
    assert "responders" in live_locs
    assert "incidents" in live_locs

    # 3. Connect Bluetooth Device
    status_dev, dev_res = make_request(
        f"{api_server}/api/v1/devices/connect",
        method="POST",
        data={
            "device_id": "ble-ursafe-vikram-01",
            "hardware_model": "UrSafe Mobile BLE Node",
            "role": "RESPONDER"
        },
        token=resp_token
    )
    assert status_dev == 200
    assert dev_res["connection_state"] == "CONNECTED"

    # 4. Heartbeat
    status_hb, hb_res = make_request(
        f"{api_server}/api/v1/devices/heartbeat",
        method="POST",
        data={
            "device_id": "ble-ursafe-vikram-01",
            "battery_level": 84,
            "rssi_dbm": -59
        },
        token=resp_token
    )
    assert status_hb == 200
    assert hb_res["status"] == "HEARTBEAT_ACK"

    # 5. Query categorized devices
    status_devs, devs_data = make_request(f"{api_server}/api/v1/devices")
    assert status_devs == 200
    assert "categorized" in devs_data
    assert "ursafe_devices" in devs_data["categorized"]
    assert "other_devices" in devs_data["categorized"]

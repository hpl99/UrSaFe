"""
End-to-end integration test verifying the three core product verticals:
1. Real exact location & reverse geocoding
2. Complete 18-state lifecycle + evidence SHA-256 hashing + duplicate detection + emergency history + reopening
3. UrSafe Bluetooth device discovery, authenticated connection, heartbeat, and presence.
"""

import os
import subprocess
import time
import json
import hashlib
import urllib.request
import urllib.error
import pytest


@pytest.fixture(scope="module")
def api_server():
    """Starts the real backend API server on a dedicated test port."""
    port = 4098
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.Popen(
        ["node", "apps/api/server.js"],
        env=env
    )

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
        raise RuntimeError("Failed to start test API server on port 4098")

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


def get_auth_token(base_url, username, password="Password123!"):
    status, data = make_request(
        f"{base_url}/api/v1/auth/login",
        method="POST",
        data={"username": username, "password": password}
    )
    assert status == 200, f"Login failed for {username}: {data}"
    return data["session"]["token"]


def test_full_emergency_lifecycle_and_history(api_server):
    # 1. Login as Citizen
    citizen_token = get_auth_token(api_server, "citizen_priya")

    # 2. Reverse Geocode exact location
    status, geo_data = make_request(
        f"{api_server}/api/v1/locations/reverse-geocode",
        method="POST",
        data={"latitude": 28.650805, "longitude": 77.230014},
        token=citizen_token
    )
    assert status == 200
    assert "Chandni Chowk" in geo_data["formatted_address"]

    # 3. Create SOS with real coordinates and reverse-geocoded address
    sos_payload = {
        "category": "MEDICAL",
        "urgency": "CRITICAL",
        "latitude": 28.650805,
        "longitude": 77.230014,
        "accuracy_m": 8.0,
        "location_description": geo_data["formatted_address"],
        "victim_count": 1,
        "description": "Critical trauma victim trapped in collapsed structure."
    }
    status, create_data = make_request(
        f"{api_server}/api/v1/incidents",
        method="POST",
        data=sos_payload,
        token=citizen_token
    )
    assert status == 201
    incident = create_data["incident"]
    inc_id = incident["id"]

    assert incident["status"] in ["SOS_CREATED", "REPORTED"]
    assert incident["latitude"] == 28.650805

    # 4. Authority logs in and assigns responder
    authority_token = get_auth_token(api_server, "authority_rajesh")

    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/dispatch",
        method="POST",
        data={"responder_id": "usr-responder-01"},
        token=authority_token
    )
    assert status == 200

    # 5. Responder logs in and transitions through field lifecycle
    responder_token = get_auth_token(api_server, "responder_vikram")

    # MISSION_ACCEPTED
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "MISSION_ACCEPTED", "reason": "Unit Alpha accepted mission", "actor_role": "RESPONDER"},
        token=responder_token
    )
    assert status == 200

    # EN_ROUTE
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "EN_ROUTE", "reason": "Medic deploying with ALS kit", "actor_role": "RESPONDER"},
        token=responder_token
    )
    assert status == 200

    # ARRIVED_ON_SCENE
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "ARRIVED_ON_SCENE", "reason": "Arrived at Chandni Chowk coordinates", "actor_role": "RESPONDER"},
        token=responder_token
    )
    assert status == 200

    # RESCUE_IN_PROGRESS
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "RESCUE_IN_PROGRESS", "reason": "Extraction in progress", "actor_role": "RESPONDER"},
        token=responder_token
    )
    assert status == 200

    # RESCUE_COMPLETED
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "RESCUE_COMPLETED", "reason": "Victim extracted and stabilized", "actor_role": "RESPONDER"},
        token=responder_token
    )
    assert status == 200

    # 6. Responder uploads on-scene evidence
    evidence_content = f"REAL_FIELD_PHOTO_{time.time()}".encode("utf-8")
    ev_hash = hashlib.sha256(evidence_content).hexdigest()

    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/evidence",
        method="POST",
        data={
            "evidence_type": "PHOTO",
            "file_name": "rescue_scene.jpg",
            "mime_type": "image/jpeg",
            "file_size": len(evidence_content),
            "file_data_base64": "cmVhbF9waG90b19kYXRh",
            "sha256": ev_hash,
            "uploader_role": "RESPONDER",
            "description": "Victim safely removed from collapsed structure",
            "latitude": 28.650805,
            "longitude": 77.230014
        },
        token=responder_token
    )
    assert status == 201

    # Verify duplicate detection (SHA-256 conflict)
    status, dup_data = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/evidence",
        method="POST",
        data={
            "file_name": "duplicate_rescue.jpg",
            "mime_type": "image/jpeg",
            "file_size": len(evidence_content),
            "file_data_base64": "cmVhbF9waG90b19kYXRh",
            "sha256": ev_hash,
            "uploader_role": "RESPONDER",
            "description": "Attempted duplicate upload"
        },
        token=responder_token
    )
    assert status == 409
    assert "Duplicate evidence detected" in dup_data["error"]

    # Transition to EVIDENCE_SUBMITTED & VERIFICATION_PENDING
    make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "EVIDENCE_SUBMITTED", "reason": "Evidence attached with SHA-256 hash", "actor_role": "RESPONDER"},
        token=responder_token
    )
    make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "VERIFICATION_PENDING", "reason": "Awaiting authority verification", "actor_role": "RESPONDER"},
        token=responder_token
    )

    # 7. Authority reviews and approves rescue
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/verify-evidence",
        method="POST",
        data={"action": "APPROVE", "notes": "Photographic evidence matches GPS coordinates."},
        token=authority_token
    )
    assert status == 200

    # 8. Authority closes case
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/close",
        method="POST",
        data={"notes": "Operational objective achieved. Case closed."},
        token=authority_token
    )
    assert status == 200

    # 9. Verify case is NO LONGER in active incidents list
    status, active_incidents = make_request(
        f"{api_server}/api/v1/incidents",
        token=authority_token
    )
    assert status == 200
    assert all(inc["id"] != inc_id for inc in active_incidents)

    # 10. Verify case APPEARS in Emergency History
    status, history_incidents = make_request(
        f"{api_server}/api/v1/incidents?history=true",
        token=authority_token
    )
    assert status == 200
    matched_case = next((inc for inc in history_incidents if inc["id"] == inc_id), None)
    assert matched_case is not None
    assert matched_case["status"] in ["CLOSED", "VERIFIED"]

    # 11. Inspect comprehensive historical case detail
    status, case_detail = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}",
        token=authority_token
    )
    assert status == 200
    assert case_detail["incident"]["id"] == inc_id
    assert len(case_detail["timeline"]) >= 7  # All transitions recorded chronologically
    assert len(case_detail["evidence"]) == 1
    assert case_detail["evidence"][0]["sha256"] == ev_hash

    # 12. Authority reopens case
    status, _ = make_request(
        f"{api_server}/api/v1/incidents/{inc_id}/reopen",
        method="POST",
        data={"reason": "Secondary structural collapse reported nearby requiring follow-up inspection."},
        token=authority_token
    )
    assert status == 200

    # Reopened case should now appear in active list again
    status, active_again = make_request(
        f"{api_server}/api/v1/incidents",
        token=authority_token
    )
    assert status == 200
    assert any(inc["id"] == inc_id and inc["status"] == "REOPENED" for inc in active_again)


@pytest.fixture
def seed_test_ble_device():
    """Seeds test-only BLE node fixture into isolated test database."""
    db_path = os.environ.get("URSAFE_DB_PATH")
    if db_path:
        escaped_path = db_path.replace("\\", "/")
        script = f"""
        const {{ DatabaseSync }} = require('node:sqlite');
        const db = new DatabaseSync('{escaped_path}');
        const now = Date.now();
        db.prepare(`
          INSERT OR REPLACE INTO devices (id, user_id, device_type, hardware_model, mac_address, bluetooth_uuid, battery_level, connection_state, protocol_version, role_advertised, connected_user_id, last_heartbeat)
          VALUES ('ble-ursafe-vikram-01', 'usr-responder-01', 'ANDROID_MOBILE', 'UrSafe Mobile BLE Node', 'AA:BB:CC:DD:EE:FF', '0xFE26', 85.0, 'DISCONNECTED', 'v1', 'RESPONDER', 'usr-responder-01', ?)
        `).run(now);
        """
        subprocess.run(["node", "-e", script], check=True)
    return "ble-ursafe-vikram-01"


def test_bluetooth_device_discovery_and_presence(api_server, seed_test_ble_device):
    responder_token = get_auth_token(api_server, "responder_vikram")

    # 1. Discover devices
    status, devices = make_request(f"{api_server}/api/v1/devices", token=responder_token)
    assert status == 200
    assert "ursafe_devices" in devices
    assert "compatible_radios" in devices
    assert "other_devices" in devices

    ursafe_node = devices["ursafe_devices"][0]
    dev_id = ursafe_node["id"]

    # 2. Connect to UrSafe device
    status, conn_data = make_request(
        f"{api_server}/api/v1/devices/connect",
        method="POST",
        data={"device_id": dev_id},
        token=responder_token
    )
    assert status == 200
    assert conn_data["device"]["status"] == "CONNECTED"
    assert conn_data["device"]["connected_user_id"] == "usr-responder-01"

    # 3. Heartbeat with telemetry
    status, _ = make_request(
        f"{api_server}/api/v1/devices/heartbeat",
        method="POST",
        data={"device_id": dev_id, "rssi_dbm": -59.5, "battery_pct": 82},
        token=responder_token
    )
    assert status == 200

    # 4. Stream location
    status, _ = make_request(
        f"{api_server}/api/v1/locations",
        method="POST",
        data={"latitude": 28.6510, "longitude": 77.2305, "accuracy_m": 6.5, "source": "BLE_DEVICE"},
        token=responder_token
    )
    assert status in [200, 201]

    # 5. Disconnect
    status, disc_data = make_request(
        f"{api_server}/api/v1/devices/disconnect",
        method="POST",
        data={"device_id": dev_id},
        token=responder_token
    )
    assert status == 200
    assert disc_data["device"]["status"] == "DISCONNECTED"

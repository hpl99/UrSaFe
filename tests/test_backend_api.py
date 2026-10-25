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
        "is_simulation": 1
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

    # 10. Authority Reviews and Verifies Rescue
    status, verify_data = make_request(
        f"{api_server}/api/v1/incidents/{incident_id}/verify-rescue",
        method="POST",
        data={"action": "VERIFY", "notes": "Photographic evidence matches coordinates"},
        token=auth_token
    )
    assert status == 200
    assert verify_data["incident"]["status"] == "VERIFIED"
    assert verify_data["report"]["verification_status"] == "VERIFIED"

    # 11. Flight Recorder Audit Chain Verification
    status, audit_data = make_request(f"{api_server}/api/v1/audit/flight-recorder")
    assert status == 200
    assert audit_data["status"] == "CHAIN_INTACT"
    assert audit_data["verified"] is True
    assert audit_data["chain_length"] >= 8

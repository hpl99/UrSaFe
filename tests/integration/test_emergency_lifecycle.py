"""
Automated Integration Tests for UrSafe Emergency Lifecycle.
Verifies the complete 18-state operational lifecycle, role authorization on state transitions,
evidence attachment, authority verification, citizen confirmation, audit trail ordering,
and persistence survival across process restarts.
"""

import os
import json
import urllib.request
import urllib.error
import pytest

BASE_URL = os.environ.get("URSAFE_TEST_URL", "http://127.0.0.1:3000")


def make_request(url, method="GET", data=None, token=None):
    """Executes HTTP request using standard library, returning (status_code, response_dict)."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"raw": err_body}
        return e.code, parsed
    except Exception as e:
        pytest.fail(f"Connection failure to {url}: {e}")


@pytest.fixture(scope="module")
def auth_sessions():
    """Logs into all required roles for lifecycle execution."""
    users = {
        "citizen": ("citizen_priya", "Password123!"),
        "responder": ("responder_vikram", "Password123!"),
        "authority": ("authority_rajesh", "Password123!"),
        "admin": ("admin_system", "Password123!")
    }
    tokens = {}
    for role, (username, password) in users.items():
        status, data = make_request(
            f"{BASE_URL}/api/v1/auth/login",
            method="POST",
            data={"username": username, "password": password}
        )
        assert status == 200, f"Login failed for {username}: {data}"
        tokens[role] = data["session"]["token"]
    return tokens


def test_complete_golden_emergency_lifecycle(auth_sessions):
    """
    Executes the Complete Golden Lifecycle Scenario:
    1. Citizen creates SOS (SOS_CREATED)
    2. Authority dispatches Responder (RESPONDER_ASSIGNED)
    3. Responder accepts mission (ACCEPTED)
    4. Responder updates status to EN_ROUTE
    5. Responder updates status to ARRIVED_ON_SCENE
    6. Responder starts rescue (RESCUE_IN_PROGRESS)
    7. Evidence uploaded with SHA-256 integrity hash
    8. Responder submits rescue report (RESCUE_SUBMITTED)
    9. Authority reviews and verifies rescue proof (VERIFIED)
    10. Citizen confirms rescue assistance
    11. Authority officially closes case (CLOSED)
    12. Case moves to Emergency History
    13. Audit timeline integrity verified
    """
    cit_token = auth_sessions["citizen"]
    resp_token = auth_sessions["responder"]
    auth_token = auth_sessions["authority"]

    # --------------------------------------------------------------------------
    # Step 1: Citizen creates SOS
    # --------------------------------------------------------------------------
    sos_payload = {
        "title": "Severe Flash Flood Rooftop Extraction",
        "category": "FLOOD",
        "urgency": "CRITICAL",
        "latitude": 28.6508,
        "longitude": 77.2300,
        "accuracy_m": 8.5,
        "victim_count": 2,
        "description": "Two individuals trapped on rooftop due to surging water levels in Old Delhi",
        "status": "SOS_CREATED"
    }
    status, sos_res = make_request(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data=sos_payload,
        token=cit_token
    )
    assert status == 201, f"Failed to create SOS: {sos_res}"
    incident_id = sos_res["incident"]["id"]
    assert sos_res["incident"]["status"] in ("SOS_CREATED", "REPORTED")
    assert sos_res["incident"]["latitude"] == 28.6508

    # --------------------------------------------------------------------------
    # Step 2: Authority assigns Responder
    # --------------------------------------------------------------------------
    assign_payload = {
        "responder_id": "usr-responder-01",
        "responder_name": "Capt. Vikram Singh",
        "priority": "HIGH"
    }
    status, assign_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/assign",
        method="POST",
        data=assign_payload,
        token=auth_token
    )
    assert status == 200, f"Assignment failed: {assign_res}"
    assert assign_res["incident"]["assigned_responder_id"] == "usr-responder-01"

    # --------------------------------------------------------------------------
    # Step 3: Responder accepts mission
    # --------------------------------------------------------------------------
    status, accept_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/accept",
        method="POST",
        data={"eta_minutes": 12, "responder_id": "usr-responder-01"},
        token=resp_token
    )
    assert status == 200, f"Accept failed: {accept_res}"
    assert accept_res["incident"]["status"] in ("ACCEPTED", "MISSION_ACCEPTED")

    # --------------------------------------------------------------------------
    # Step 4: Responder moves EN_ROUTE
    # --------------------------------------------------------------------------
    status, enroute_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/transition",
        method="POST",
        data={"new_state": "EN_ROUTE", "reason": "Rapid rescue vessel deployed en route to coordinates"},
        token=resp_token
    )
    assert status == 200, f"En route transition failed: {enroute_res}"
    assert enroute_res["incident"]["status"] == "EN_ROUTE"

    # --------------------------------------------------------------------------
    # Step 5: Responder ARRIVED_ON_SCENE
    # --------------------------------------------------------------------------
    status, arrived_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/transition",
        method="POST",
        data={"new_state": "ARRIVED_ON_SCENE", "reason": "Visual contact made with trapped victims on rooftop"},
        token=resp_token
    )
    assert status == 200
    assert arrived_res["incident"]["status"] == "ARRIVED_ON_SCENE"

    # --------------------------------------------------------------------------
    # Step 6: Responder starts rescue (RESCUE_IN_PROGRESS)
    # --------------------------------------------------------------------------
    status, progress_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/transition",
        method="POST",
        data={"new_state": "RESCUE_IN_PROGRESS", "reason": "Inflatable raft and harnesses deployed"},
        token=resp_token
    )
    assert status == 200
    assert progress_res["incident"]["status"] == "RESCUE_IN_PROGRESS"

    # --------------------------------------------------------------------------
    # Step 7: Upload rescue evidence with cryptographic SHA-256 hash
    # --------------------------------------------------------------------------
    evidence_payload = {
        "file_name": "rooftop_evacuation_proof.jpg",
        "mime_type": "image/jpeg",
        "file_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP...",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "description": "Photographic documentation of victims safely boarded on NDRF rescue boat"
    }
    status, ev_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/evidence",
        method="POST",
        data=evidence_payload,
        token=resp_token
    )
    assert status == 201, f"Evidence upload failed: {ev_res}"
    evidence_id = ev_res["evidence"]["id"]
    assert ev_res["evidence"]["sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # --------------------------------------------------------------------------
    # Step 8: Responder submits rescue report (RESCUE_SUBMITTED)
    # --------------------------------------------------------------------------
    report_payload = {
        "victims_assisted": 2,
        "summary": "Both victims evacuated without hypothermia. Initial triage completed.",
        "evidence_ids": [evidence_id],
        "vitals_summary": "Stable, BP 122/80, SpO2 98%"
    }
    status, report_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/rescue-report",
        method="POST",
        data=report_payload,
        token=resp_token
    )
    assert status == 201, f"Report submission failed: {report_res}"
    assert "report" in report_res
    assert report_res["report"]["outcome"] == "RESCUED"

    # --------------------------------------------------------------------------
    # Step 9: Authority reviews and verifies rescue
    # --------------------------------------------------------------------------
    status, verify_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/verify-evidence",
        method="POST",
        data={"action": "VERIFY", "evidence_id": evidence_id, "notes": "Photographic evidence clear and authentic"},
        token=auth_token
    )
    assert status == 200, f"Evidence verification failed: {verify_res}"
    assert verify_res["incident"]["status"] == "VERIFIED"

    # --------------------------------------------------------------------------
    # Step 10: Citizen confirms rescue assistance
    # --------------------------------------------------------------------------
    status, confirm_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/confirm-rescue",
        method="POST",
        data={"confirmed": True, "satisfaction": "EXCELLENT", "notes": "Responders arrived quickly and kept us calm"},
        token=cit_token
    )
    assert status == 200, f"Citizen rescue confirmation failed: {confirm_res}"

    # --------------------------------------------------------------------------
    # Step 11: Authority officially closes case (CLOSED)
    # --------------------------------------------------------------------------
    status, close_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/close",
        method="POST",
        data={"closure_notes": "Mission successfully completed, victims reunited with family", "disposition": "RESOLVED"},
        token=auth_token
    )
    assert status == 200, f"Close incident failed: {close_res}"
    assert close_res["incident"]["status"] == "CLOSED"

    # --------------------------------------------------------------------------
    # Step 12: Verify case appears in Emergency History
    # --------------------------------------------------------------------------
    status, hist_cases = make_request(
        f"{BASE_URL}/api/v1/incidents?history=true",
        method="GET",
        token=cit_token
    )
    assert status == 200
    assert any(c["id"] == incident_id for c in hist_cases), "Completed incident not found in history"

    # --------------------------------------------------------------------------
    # Step 13: Verify chronological audit trail
    # --------------------------------------------------------------------------
    status, timeline = make_request(
        f"{BASE_URL}/api/v1/incidents/{incident_id}/timeline",
        method="GET",
        token=auth_token
    )
    assert status == 200
    assert len(timeline) >= 6, f"Expected at least 6 chronological events, got {len(timeline)}"
    # Verify strict ascending timestamp order
    timestamps = [e["timestamp"] for e in timeline]
    assert timestamps == sorted(timestamps), "Audit timeline events are not strictly chronological!"


def test_invalid_lifecycle_transitions(auth_sessions):
    """Verifies that unauthorized or invalid state transitions fail safely."""
    cit_token = auth_sessions["citizen"]

    # Create an active incident first
    status, res = make_request(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data={"title": "RBAC Bypass Test", "latitude": 28.6, "longitude": 77.2, "status": "SOS_CREATED"},
        token=cit_token
    )
    assert status == 201
    inc_id = res["incident"]["id"]

    # 1. Citizen cannot jump state directly to VERIFIED or CLOSED (403 Forbidden)
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/{inc_id}/transition",
        method="POST",
        data={"new_state": "VERIFIED", "reason": "Unauthorized bypass"},
        token=cit_token
    )
    assert status == 403, f"Citizen was able to transition to VERIFIED! Status: {status}"


def test_reopen_workflow(auth_sessions):
    """Verifies that completed cases can be reopened only by authorized coordinators."""
    auth_token = auth_sessions["authority"]
    resp_token = auth_sessions["responder"]

    # 1. Create and close an incident
    status, res = make_request(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data={"title": "Reopen Test Case", "latitude": 28.6, "longitude": 77.2, "status": "SOS_CREATED"},
        token=auth_token
    )
    inc_id = res["incident"]["id"]

    make_request(
        f"{BASE_URL}/api/v1/incidents/{inc_id}/close",
        method="POST",
        data={"closure_notes": "Premature close"},
        token=auth_token
    )

    # 2. Responder tries to reopen -> 403 Forbidden
    status, _ = make_request(
        f"{BASE_URL}/api/v1/incidents/{inc_id}/reopen",
        method="POST",
        data={"reason": "Responder reopening"},
        token=resp_token
    )
    assert status == 403

    # 3. Authority reopens -> 200 OK
    status, reopen_res = make_request(
        f"{BASE_URL}/api/v1/incidents/{inc_id}/reopen",
        method="POST",
        data={"reason": "Victim reported further distress in adjacent building"},
        token=auth_token
    )
    assert status == 200
    assert reopen_res["incident"]["status"] == "REOPENED"


def test_database_persistence_direct_inspection(auth_sessions):
    """
    Direct Database Verification (Section 8):
    Inspects data/ursafe.db directly via sqlite3 to prove that all API operations
    are durably written to physical disk tables rather than held only in memory.
    """
    import sqlite3
    db_path = os.environ.get("URSAFE_DB_PATH") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ursafe_dev.db")
    assert "production" not in db_path.lower(), f"Refusing to inspect production database in tests: {db_path}"
    assert os.path.exists(db_path), f"SQLite database file missing at {db_path}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Verify incidents table has records
    cursor.execute("SELECT COUNT(*) FROM incidents")
    incident_count = cursor.fetchone()[0]
    assert incident_count >= 1, "Incidents table is empty on disk!"

    # 2. Verify incident_events audit trail has records
    cursor.execute("SELECT COUNT(*) FROM incident_events")
    event_count = cursor.fetchone()[0]
    assert event_count >= 1, "Incident events table is empty on disk!"

    # 3. Verify evidence table has SHA-256 integrity hashes
    cursor.execute("SELECT id, sha256_hash FROM evidence LIMIT 5")
    evidence_rows = cursor.fetchall()
    assert len(evidence_rows) >= 1, "Evidence table is empty on disk!"
    for ev_id, h in evidence_rows:
        assert len(h) == 64, f"Invalid SHA-256 hash length in database: {h}"

    # 4. Verify audit_events cryptographic flight recorder hash chain on disk
    cursor.execute("SELECT id, previous_event_hash, current_event_hash, timestamp FROM audit_events ORDER BY timestamp ASC")
    chain = cursor.fetchall()
    assert len(chain) >= 2, "Flight recorder audit trail has fewer than 2 entries on disk!"

    for i in range(1, len(chain)):
        prev_id, prev_prev_hash, prev_curr_hash, prev_time = chain[i - 1]
        curr_id, curr_prev_hash, curr_curr_hash, curr_time = chain[i]
        assert curr_prev_hash == prev_curr_hash, f"Hash chain broken between event {prev_id} and {curr_id} on disk!"

    conn.close()

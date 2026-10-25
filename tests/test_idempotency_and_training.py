import json
import urllib.request
import urllib.error
import pytest

def get_auth_token(base_url, username="citizen_priya", password="Password123!"):
    req_body = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/v1/auth/login",
        data=req_body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["session"]["token"]


def test_incident_idempotent_creation_with_client_msg_id(session_api_server):
    """Sub-task 3.7: Repeated POST /api/v1/incidents with same (reporter, client_msg_id) returns existing incident."""
    token = get_auth_token(session_api_server)
    client_msg_id = "test-client-msg-uuid-9999"
    
    payload = {
        "client_msg_id": client_msg_id,
        "category": "FLOOD",
        "urgency": "CRITICAL",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "Idempotent flood test distress signal"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 1. First submission -> Created (HTTP 201)
    req1 = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req1) as resp1:
        assert resp1.status == 201
        res1 = json.loads(resp1.read().decode("utf-8"))
        incident_id_1 = res1["incident"]["id"]
        assert incident_id_1 is not None

    # 2. Second submission with exact same client_msg_id -> Idempotent response (HTTP 200, same id)
    req2 = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req2) as resp2:
        assert resp2.status == 200
        res2 = json.loads(resp2.read().decode("utf-8"))
        assert res2["incident"]["id"] == incident_id_1
        assert res2.get("deduplicated") is True

    # 3. Third submission with same client_msg_id -> Still returns same incident
    req3 = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req3) as resp3:
        assert resp3.status == 200
        res3 = json.loads(resp3.read().decode("utf-8"))
        assert res3["incident"]["id"] == incident_id_1


def test_training_mode_messages_never_forwarded_to_real_transports(session_api_server, isolated_test_database):
    """Sub-task 3.4: SOS messages created with is_simulation/training flag must NEVER be forwarded to real transports."""
    import sqlite3
    token = get_auth_token(session_api_server)
    
    payload = {
        "client_msg_id": "training-drill-msg-001",
        "category": "FIRE",
        "urgency": "HIGH",
        "latitude": 19.0800,
        "longitude": 72.8800,
        "description": "Simulated drill distress - do not forward",
        "is_simulation": 1
    }
    
    req = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        res = json.loads(resp.read().decode("utf-8"))
        inc_id = res["incident"]["id"]
        assert inc_id is not None

    # Wait for asynchronous outbox processing loop
    import time
    conn = sqlite3.connect(isolated_test_database)
    cur = conn.cursor()
    row = None
    for _ in range(20):
        cur.execute("SELECT current_state, last_transport, last_error FROM continuity_messages WHERE incident_id = ?", (inc_id,))
        row = cur.fetchone()
        if row and row[1] is not None:
            break
        time.sleep(0.1)

    assert row is not None, "Message was not enqueued into continuity_messages"
    state, last_tr, last_err = row
    assert last_tr == "SIMULATION_ISOLATED"
    assert "TRAINING" in last_err
    conn.close()

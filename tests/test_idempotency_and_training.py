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
    """Sub-task 3.4 & Step 3.5.3: Messages created with training flag must enter SUPPRESSED_TRAINING and NEVER DELIVERED."""
    import sqlite3
    import time
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
    conn = sqlite3.connect(isolated_test_database)
    cur = conn.cursor()
    row = None
    for _ in range(30):
        cur.execute("SELECT current_state, ack_level, last_transport, last_error FROM continuity_messages WHERE incident_id = ?", (inc_id,))
        row = cur.fetchone()
        if row and row[2] is not None:
            break
        time.sleep(0.1)

    assert row is not None, "Message was not enqueued into continuity_messages"
    state, ack_lvl, last_tr, last_err = row

    # Step 3.5.3 (a): Distinct delivery state SUPPRESSED_TRAINING, never DELIVERED
    assert state == "SUPPRESSED_TRAINING", f"Expected state SUPPRESSED_TRAINING, got: {state}"
    assert state != "DELIVERED", "Training message must NEVER have current_state = DELIVERED"
    assert ack_lvl == "TRAINING_SUPPRESSED", f"Expected ack_level TRAINING_SUPPRESSED, got: {ack_lvl}"
    assert ack_lvl not in ("TRANSPORT_ACK", "NODE_ACK", "APPLICATION_ACK", "HUMAN_ACK")
    assert last_tr == "SIMULATION_ISOLATED"
    assert "TRAINING" in last_err
    conn.close()


def test_is_training_defaults_to_zero_and_permits_author_to_set(session_api_server):
    """Step 3.5.3 (b): is_training defaults to 0 server-side; documented and tested who may set it."""
    token = get_auth_token(session_api_server, "citizen_priya")
    
    # 1. Omitted is_training -> strictly defaults to 0
    req_omitted = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps({
            "client_msg_id": "test-omitted-training-01",
            "category": "MEDICAL",
            "urgency": "HIGH",
            "description": "Real cardiac emergency - training omitted"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    with urllib.request.urlopen(req_omitted) as resp:
        assert resp.status == 201
        res = json.loads(resp.read().decode("utf-8"))
        assert res["incident"]["is_simulation"] == 0

    # 2. Explicitly setting is_training = 1 by authenticated citizen for practice drill -> sets to 1
    req_drill = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps({
            "client_msg_id": "test-explicit-training-01",
            "category": "MEDICAL",
            "urgency": "LOW",
            "description": "Citizen community practice drill",
            "is_simulation": 1
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    with urllib.request.urlopen(req_drill) as resp:
        assert resp.status == 201
        res = json.loads(resp.read().decode("utf-8"))
        assert res["incident"]["is_simulation"] == 1


def test_training_incidents_do_not_appear_in_responder_queues_or_dispatch(session_api_server):
    """Step 3.5.3 (c): Training incidents do not appear in responder queues or dispatch."""
    cit_token = get_auth_token(session_api_server, "citizen_priya")
    resp_token = get_auth_token(session_api_server, "responder_vikram")
    auth_token = get_auth_token(session_api_server, "authority_rajesh")

    # 1. Citizen creates training drill
    req_drill = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps({
            "client_msg_id": "drill-hide-from-responder-01",
            "category": "COLLAPSE",
            "urgency": "CRITICAL",
            "description": "Simulation Drill for NDRF",
            "is_simulation": 1
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cit_token}"},
        method="POST"
    )
    with urllib.request.urlopen(req_drill) as resp:
        drill_data = json.loads(resp.read().decode("utf-8"))
        drill_id = drill_data["incident"]["id"]

    # 2. Responder queries incident queue -> drill must NOT appear
    req_feed = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        headers={"Authorization": f"Bearer {resp_token}"},
        method="GET"
    )
    with urllib.request.urlopen(req_feed) as resp:
        assert resp.status == 200
        feed = json.loads(resp.read().decode("utf-8"))
        drill_matches = [i for i in feed if i["id"] == drill_id]
        assert len(drill_matches) == 0, "Training drill incident MUST NOT appear in operational responder queue"

    # 3. Authority attempts to dispatch real responder to training incident -> rejected with 400 Bad Request
    req_dispatch = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents/{drill_id}/dispatch",
        data=json.dumps({"responder_id": "usr-responder-01"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"},
        method="POST"
    )
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req_dispatch)
    assert exc_info.value.code == 400
    err_body = json.loads(exc_info.value.read().decode("utf-8"))
    assert "Training incidents cannot be dispatched" in err_body["error"]


def test_real_sos_with_training_omitted_is_always_delivered(session_api_server, isolated_test_database):
    """Step 3.5.3 (d): A real SOS with is_training omitted is always delivered."""
    import sqlite3
    import time
    cit_token = get_auth_token(session_api_server, "citizen_priya")
    resp_token = get_auth_token(session_api_server, "responder_vikram")

    req_real = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        data=json.dumps({
            "client_msg_id": "real-life-sos-delivery-01",
            "category": "FLOOD",
            "urgency": "CRITICAL",
            "latitude": 19.0792,
            "longitude": 72.8798,
            "description": "REAL SOS: Family stranded on roof during flash flood"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cit_token}"},
        method="POST"
    )
    with urllib.request.urlopen(req_real) as resp:
        assert resp.status == 201
        real_data = json.loads(resp.read().decode("utf-8"))
        real_id = real_data["incident"]["id"]

    # Responder queue must see it
    req_feed = urllib.request.Request(
        f"{session_api_server}/api/v1/incidents",
        headers={"Authorization": f"Bearer {resp_token}"},
        method="GET"
    )
    with urllib.request.urlopen(req_feed) as resp:
        feed = json.loads(resp.read().decode("utf-8"))
        assert any(i["id"] == real_id for i in feed), "Real incident must appear in responder feed"

    # Outbox message must NOT be SUPPRESSED_TRAINING
    conn = sqlite3.connect(isolated_test_database)
    cur = conn.cursor()
    row = None
    for _ in range(30):
        cur.execute("SELECT current_state, ack_level FROM continuity_messages WHERE incident_id = ?", (real_id,))
        row = cur.fetchone()
        if row and row[0] not in ("QUEUED", "TRANSMITTING"):
            break
        time.sleep(0.1)

    assert row is not None
    state, ack_lvl = row
    assert state != "SUPPRESSED_TRAINING", "Real SOS must never be SUPPRESSED_TRAINING"
    assert ack_lvl != "TRAINING_SUPPRESSED", "Real SOS must never have TRAINING_SUPPRESSED ack level"
    conn.close()


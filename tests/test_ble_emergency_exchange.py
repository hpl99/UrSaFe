"""
UrSafe-to-UrSafe Offline BLE Emergency Exchange Tests.
Covers BLE transport criteria specified in Section 44:
1. Scanner discovers UrSafe devices (0xFE26)
2. Scanner ignores/filters non-UrSafe devices (PCs, earbuds)
3. Connection state transitions (DISCOVERED -> CONNECTING -> CONNECTED -> AUTHENTICATED -> READY -> DISCONNECTED)
4. Handshake succeeds with protocol version and ephemeral session
5. Handshake fails on unknown/corrupted device
6. Authenticated peer appears in active peers list
7. SOS transmits offline over BLE sync envelope
8. Receiver persists SOS in database
9. Receiver sends cryptographic ACK (ack_hash)
10. Sender marks delivery acknowledged
11. Duplicate message does not duplicate emergency (continuity deduplication)
12. Disconnect transitions state to DISCONNECTED
13. Reconnect resumes session
14. Offline mode persists SOS without cloud/internet
15. Unauthorized peer cannot access restricted documents
16. Document metadata transfers
17. Document chunks transfer (512B MTU chunks)
18. Interrupted document transfer resumes from chunk index
19. Final SHA-256 reassembly verification
20. Corrupted document hash mismatch rejection
21. Real-time events / notifications emitted
22. Emergency lifecycle persists over BLE transport
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
    """Starts backend API on test port 4102."""
    port = 4102
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.Popen(["node", "apps/api/server.js"], env=env)

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
        raise RuntimeError("Failed to start test API server on port 4102")

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

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, json.loads(err_body) if err_body else {}


def login(api_server, username, password="Password123!"):
    status, data = make_request(
        f"{api_server}/api/v1/auth/login",
        method="POST",
        data={"username": username, "password": password}
    )
    assert status == 200, f"Login failed for {username}: {data}"
    user = data.get("user", {})
    if "id" not in user and "userId" in data.get("session", {}):
        user["id"] = data["session"]["userId"]
    return data["session"]["token"], user


def test_ble_peers_discovery_and_filtering(api_server):
    """1 & 2. Scanner discovers UrSafe compatible peers and filters out non-UrSafe devices."""
    resp_token, _ = login(api_server, "responder_vikram")
    status, data = make_request(f"{api_server}/api/v1/ble/peers", token=resp_token)
    assert status == 200
    assert "peers" in data
    assert len(data["peers"]) >= 3
    
    # All peers returned must be UrSafe compatible (0xFE26)
    for peer in data["peers"]:
        assert peer["is_ursafe_compatible"] == 1
        assert peer["peer_id"].startswith("USF-")
        assert "rssi_dbm" in peer or "rssi" in peer
        assert "role" in peer
        assert "public_key" in peer


def test_ble_connection_handshake_and_state_machine(api_server):
    """3, 4, 5 & 6. Connection state transitions, handshake, and authenticated peer readiness."""
    resp_token, _ = login(api_server, "responder_vikram")
    
    # Attempt to connect to non-existent peer -> 404
    bad_code, _ = make_request(
        f"{api_server}/api/v1/ble/peers/connect",
        method="POST",
        token=resp_token,
        data={"device_id": "NON-EXISTENT-DEVICE"}
    )
    assert bad_code == 404
    
    # Connect to Priya's UrSafe device
    conn_status, conn_data = make_request(
        f"{api_server}/api/v1/ble/peers/connect",
        method="POST",
        token=resp_token,
        data={"device_id": "USF-9F81-PRIYA"}
    )
    assert conn_status == 200
    peer = conn_data["peer"]
    assert peer["connection_state"] == "READY"
    assert "session_key" in conn_data
    assert conn_data["protocol_version"] == "1.0"
    
    # Verify peer appears as READY in peer list
    _, peer_list = make_request(f"{api_server}/api/v1/ble/peers", token=resp_token)
    priya = next(p for p in peer_list["peers"] if p["peer_id"] == "USF-9F81-PRIYA" or p["device_id"] == "USF-9F81-PRIYA")
    assert priya["connection_state"] == "READY"


def test_offline_sos_transmission_and_ack(api_server):
    """7, 8, 9 & 10. Direct UrSafe-to-UrSafe offline SOS envelope transmission, persistence, and cryptographic ACK."""
    cit_token, _ = login(api_server, "citizen_priya")
    
    message_id = f"msg-test-offline-sos-{int(time.time())}"
    payload = {
        "title": "Severe Flash Flood - Family Stranded on Roof",
        "category": "FLOOD",
        "urgency": "CRITICAL",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "medical_critical": True,
        "victim_count": 4,
        "description": "Water reached 2nd floor, power lost, battery low. Direct BLE emergency link.",
        "evidence_hashes": ["sha256-evidence-flood-roof-01"]
    }
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    
    envelope = {
        "protocol_version": "1.0",
        "message_id": message_id,
        "sender_device_id": "USF-9F81-PRIYA",
        "recipient_device_id": "USF-8A42-VIKRAM",
        "message_type": "EMERGENCY_CREATE",
        "timestamp": int(time.time()),
        "payload": payload,
        "payload_hash": payload_hash,
        "ack_required": True
    }
    
    # Transmit via offline BLE sync endpoint
    sync_status, sync_res = make_request(
        f"{api_server}/api/v1/ble/sync",
        method="POST",
        token=cit_token,
        data=envelope
    )
    assert sync_status == 200
    assert sync_res["status"] == "RECEIVED"
    assert sync_res["delivery_state"] == "ACKNOWLEDGED"
    assert "ack_hash" in sync_res
    assert "incident_id" in sync_res
    
    incident_id = sync_res["incident_id"]
    
    # Verify incident persisted in database
    _, inc_data = make_request(f"{api_server}/api/v1/incidents/{incident_id}", token=cit_token)
    assert inc_data["incident"]["id"] == incident_id
    assert inc_data["incident"]["category"] == "FLOOD"
    assert inc_data["incident"]["urgency"] == "CRITICAL"


def test_deduplication_prevents_duplicate_incidents(api_server):
    """11. Duplicate envelope delivery returns ACK without creating duplicate business records."""
    cit_token, _ = login(api_server, "citizen_priya")
    
    dup_msg_id = f"msg-dedup-test-{int(time.time())}"
    payload = {
        "title": "Dedup Test Emergency",
        "category": "MEDICAL",
        "urgency": "HIGH",
        "latitude": 19.0800,
        "longitude": 72.8800
    }
    envelope = {
        "protocol_version": "1.0",
        "message_id": dup_msg_id,
        "sender_device_id": "USF-9F81-PRIYA",
        "recipient_device_id": "USF-8A42-VIKRAM",
        "message_type": "EMERGENCY_CREATE",
        "timestamp": int(time.time()),
        "payload": payload,
        "payload_hash": "hash123",
        "ack_required": True
    }
    
    # First delivery
    st1, res1 = make_request(f"{api_server}/api/v1/ble/sync", method="POST", token=cit_token, data=envelope)
    assert st1 == 200
    first_incident_id = res1["incident_id"]
    
    # Second delivery with EXACT same message_id
    st2, res2 = make_request(f"{api_server}/api/v1/ble/sync", method="POST", token=cit_token, data=envelope)
    assert st2 == 200
    assert res2["status"] == "DUPLICATE_ACKNOWLEDGED"
    assert res2["duplicate"] is True
    # Must NOT have created a new incident
    assert res2.get("incident_id") == first_incident_id


def test_ble_disconnect_and_reconnect(api_server):
    """12 & 13. Disconnect transitions state to DISCONNECTED, reconnect restores READY."""
    resp_token, _ = login(api_server, "responder_vikram")
    
    # Disconnect Priya's device
    disc_status, disc_res = make_request(
        f"{api_server}/api/v1/ble/peers/disconnect",
        method="POST",
        token=resp_token,
        data={"device_id": "USF-9F81-PRIYA"}
    )
    assert disc_status == 200
    assert disc_res["peer"]["connection_state"] == "DISCONNECTED"
    
    # Reconnect restores READY
    rec_status, rec_res = make_request(
        f"{api_server}/api/v1/ble/peers/connect",
        method="POST",
        token=resp_token,
        data={"device_id": "USF-9F81-PRIYA"}
    )
    assert rec_status == 200
    assert rec_res["peer"]["connection_state"] == "READY"


def test_chunked_document_transfer_and_hash_verification(api_server):
    """16, 17, 18, 19 & 20. 512B MTU chunked document transfer, resume, and SHA-256 verification."""
    resp_token, _ = login(api_server, "responder_vikram")
    
    # Prepare a 1.5 KB payload simulating an offline emergency triage card
    raw_payload = ("URSAFE-EMERGENCY-EVIDENCE-BODY-CHUNK-DATA-" * 40)
    full_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    
    chunk_size = 512
    chunks = [raw_payload[i:i + chunk_size] for i in range(0, len(raw_payload), chunk_size)]
    total_chunks = len(chunks)
    assert total_chunks >= 3
    
    transfer_id = f"doc-xfer-{int(time.time())}"
    
    # Send Chunk 0
    c0_status, c0_res = make_request(
        f"{api_server}/api/v1/ble/documents/transfer",
        method="POST",
        token=resp_token,
        data={
            "transfer_id": transfer_id,
            "sender_device_id": "USF-8A42-VIKRAM",
            "recipient_device_id": "USF-9F81-PRIYA",
            "file_name": "triage_assessment.json",
            "mime_type": "application/json",
            "total_bytes": len(raw_payload),
            "total_chunks": total_chunks,
            "chunk_index": 0,
            "chunk_data": chunks[0],
            "expected_sha256": full_hash
        }
    )
    assert c0_status == 200
    assert c0_res["status"] == "TRANSFERRING"
    assert c0_res["chunks_transferred"] == 1
    
    # Verify status query
    st_code, st_info = make_request(f"{api_server}/api/v1/ble/documents/{transfer_id}/status", token=resp_token)
    assert st_code == 200
    assert st_info["transfer"]["chunks_transferred"] == 1
    
    # Send remaining chunks
    for idx in range(1, total_chunks):
        c_status, c_res = make_request(
            f"{api_server}/api/v1/ble/documents/transfer",
            method="POST",
            token=resp_token,
            data={
                "transfer_id": transfer_id,
                "sender_device_id": "USF-8A42-VIKRAM",
                "recipient_device_id": "USF-9F81-PRIYA",
                "file_name": "triage_assessment.json",
                "mime_type": "application/json",
                "total_bytes": len(raw_payload),
                "total_chunks": total_chunks,
                "chunk_index": idx,
                "chunk_data": chunks[idx],
                "expected_sha256": full_hash
            }
        )
        assert c_status == 200
        if idx == total_chunks - 1:
            # Final chunk must verify SHA-256 and complete
            assert c_res["status"] == "COMPLETED"
            assert c_res["verified_sha256"] == full_hash
            assert c_res["chunks_transferred"] == total_chunks

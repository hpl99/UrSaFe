"""
Comprehensive Security and Role-Based Access Control (RBAC) Test Suite.
Verifies strict cryptographic authentication, authorization walls, role separation,
and anti-tampering guards across Citizen, Responder, Authority, and Admin roles.
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
def tokens():
    """Logs into all 4 distinct test personas and extracts their JWT tokens."""
    roles = {
        "citizen": ("citizen_priya", "Password123!"),
        "responder": ("responder_vikram", "Password123!"),
        "authority": ("authority_rajesh", "Password123!"),
        "admin": ("admin_system", "Password123!")
    }
    sessions = {}
    for role_key, (username, password) in roles.items():
        status, data = make_request(
            f"{BASE_URL}/api/v1/auth/login",
            method="POST",
            data={"username": username, "password": password}
        )
        assert status == 200, f"Login failed for {username}: {data}"
        assert "session" in data
        assert "token" in data["session"]
        sessions[role_key] = data["session"]["token"]
    return sessions


# ==============================================================================
# 1. Unauthenticated and Tampered Token Tests
# ==============================================================================

def test_missing_token_rejection():
    """Unauthenticated calls to protected routes must return 401 Unauthorized."""
    protected_cases = [
        (f"{BASE_URL}/api/v1/auth/me", "GET", None),
        (f"{BASE_URL}/api/v1/incidents", "POST", {"title": "Exploit Attempt", "latitude": 28.0, "longitude": 77.0}),
        (f"{BASE_URL}/api/v1/incidents/inc-test-01/assign", "POST", {"responder_id": "usr-resp-01"}),
        (f"{BASE_URL}/api/v1/users", "GET", None),
        (f"{BASE_URL}/api/v1/credentials/revoke", "POST", {"credential_id": "cred-01", "reason": "Bad"})
    ]
    for url, method, payload in protected_cases:
        status, data = make_request(url, method=method, data=payload)
        assert status == 401, f"Expected 401 for {method} {url}, got {status}: {data}"


def test_tampered_token_rejection(tokens):
    """Tokens with altered payloads or forged signatures must return 401."""
    valid_token = tokens["citizen"]
    # Tamper with the signature bytes
    tampered_token = valid_token[:-6] + "xxxxxx"
    status, data = make_request(f"{BASE_URL}/api/v1/auth/me", token=tampered_token)
    assert status == 401, f"Expected 401 on tampered token, got {status}"


def test_garbage_token_rejection():
    """Garbage strings as bearer tokens must fail safely with 401."""
    status, data = make_request(f"{BASE_URL}/api/v1/auth/me", token="Bearer-Not-A-Valid-Token-12345")
    assert status == 401


# ==============================================================================
# 2. Citizen Privilege Boundary Enforcement
# ==============================================================================

def test_citizen_cannot_dispatch_responder(tokens):
    """A Citizen must NOT be permitted to dispatch or assign responders (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/assign",
        method="POST",
        data={"responder_id": "usr-resp-01", "responder_name": "Vikram"},
        token=tokens["citizen"]
    )
    assert status == 403, f"Citizen was able to dispatch! Status: {status}, Data: {data}"


def test_citizen_cannot_verify_evidence(tokens):
    """A Citizen must NOT be permitted to verify or clear evidence (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/verify-evidence",
        method="POST",
        data={"evidence_id": "ev-01", "status": "CLEARED"},
        token=tokens["citizen"]
    )
    assert status == 403, f"Citizen was able to verify evidence! Status: {status}"


def test_citizen_cannot_close_incident(tokens):
    """A Citizen must NOT be permitted to close an incident administratively (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/close",
        method="POST",
        data={"closure_notes": "Attempted close by citizen"},
        token=tokens["citizen"]
    )
    assert status == 403


def test_citizen_cannot_revoke_credentials(tokens):
    """A Citizen must NOT be permitted to revoke responder credentials (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/credentials/revoke",
        method="POST",
        data={"credential_id": "cred-01", "reason": "Malicious revocation"},
        token=tokens["citizen"]
    )
    assert status == 403


def test_citizen_cannot_list_system_users(tokens):
    """A Citizen must NOT be permitted to list full user databases (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/users",
        method="GET",
        token=tokens["citizen"]
    )
    assert status == 403


# ==============================================================================
# 3. Responder Privilege Boundary Enforcement
# ==============================================================================

def test_responder_cannot_dispatch_others(tokens):
    """A Responder must NOT dispatch incidents to other responders (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/assign",
        method="POST",
        data={"responder_id": "usr-resp-99", "responder_name": "Another Responder"},
        token=tokens["responder"]
    )
    assert status == 403


def test_responder_cannot_reopen_incident(tokens):
    """A Responder must NOT be permitted to reopen completed cases (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/reopen",
        method="POST",
        data={"reason": "Responder unauthorized reopen"},
        token=tokens["responder"]
    )
    assert status == 403


def test_responder_cannot_verify_own_evidence(tokens):
    """A Responder must NOT self-verify their own rescue evidence (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents/inc-test-01/verify-evidence",
        method="POST",
        data={"evidence_id": "ev-01", "status": "CLEARED"},
        token=tokens["responder"]
    )
    assert status == 403


def test_responder_cannot_revoke_credentials(tokens):
    """A Responder cannot revoke other credentials (403 Forbidden)."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/credentials/revoke",
        method="POST",
        data={"credential_id": "cred-01", "reason": "Unauthorized"},
        token=tokens["responder"]
    )
    assert status == 403


# ==============================================================================
# 4. Authority & Admin Capabilities
# ==============================================================================

def test_authority_can_access_dispatch_and_audit(tokens):
    """An Authority Coordinator must be authorized to inspect flight recorder and incident queues."""
    # Flight recorder
    status, data = make_request(
        f"{BASE_URL}/api/v1/audit/flight-recorder",
        method="GET",
        token=tokens["authority"]
    )
    assert status == 200
    assert "audit_trail" in data

    # All incidents
    status, data = make_request(
        f"{BASE_URL}/api/v1/incidents",
        method="GET",
        token=tokens["authority"]
    )
    assert status == 200
    assert isinstance(data, list)
    assert len(data) >= 1


def test_admin_can_manage_users(tokens):
    """The Admin role must be authorized to inspect the system user registry."""
    status, data = make_request(
        f"{BASE_URL}/api/v1/users",
        method="GET",
        token=tokens["admin"]
    )
    assert status == 200
    assert "users" in data
    assert len(data["users"]) >= 4


# ==============================================================================
# 5. Role Verification on /auth/me
# ==============================================================================

@pytest.mark.parametrize("role_key,expected_role", [
    ("citizen", "CITIZEN"),
    ("responder", "RESPONDER"),
    ("authority", "AUTHORITY"),
    ("admin", "ADMIN")
])
def test_identity_and_role_integrity(tokens, role_key, expected_role):
    """Verifies that /auth/me accurately reports each user's authenticated role."""
    status, data = make_request(f"{BASE_URL}/api/v1/auth/me", token=tokens[role_key])
    assert status == 200
    assert data["user"]["role"] == expected_role

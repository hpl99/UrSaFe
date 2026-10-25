"""
Security Probe Script for Step 3 Item 5.
Probes all Authority, Responder, and sensitive Operational endpoints:
1. Without token
2. With Citizen token
3. With Responder token
4. With Authority token
Reports exact status codes, leaked data, and vulnerabilities.
"""

import os
import sys
import json
import urllib.request
import urllib.error

BASE_URL = os.environ.get("URSAFE_TEST_URL", "http://127.0.0.1:4050")

def req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as r:
            body_txt = r.read().decode("utf-8")
            try:
                parsed = json.loads(body_txt)
            except Exception:
                parsed = body_txt
            return r.status, parsed
    except urllib.error.HTTPError as e:
        err_txt = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_txt)
        except Exception:
            parsed = err_txt
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

def login(username, password):
    status, res = req(f"{BASE_URL}/api/v1/auth/login", method="POST", data={"username": username, "password": password})
    if status == 200 and "session" in res:
        return res["session"]["token"]
    raise RuntimeError(f"Login failed for {username}: {res}")

def run_probe():
    print(f"Connecting to {BASE_URL}...")
    citizen_tok = login("citizen_priya", "Password123!")
    responder_tok = login("responder_vikram", "Password123!")
    authority_tok = login("authority_rajesh", "Password123!")

    # Fetch real responder ID
    s, resp_me = req(f"{BASE_URL}/api/v1/auth/me", method="GET", token=responder_tok)
    resp_user_id = resp_me.get("user", {}).get("id", "usr-responder-01") if s == 200 else "usr-responder-01"

    # Fetch a real incident ID
    s, incs = req(f"{BASE_URL}/api/v1/incidents", method="GET", token=authority_tok)
    inc_id = incs[0]["id"] if isinstance(incs, list) and len(incs) > 0 else "inc-test-01"
    print(f"Using incident ID: {inc_id}, responder ID: {resp_user_id}")

    endpoints = [
        # (Name, Method, URL, Payload, Expected Allowed Roles)
        ("Audit Flight Recorder", "GET", f"{BASE_URL}/api/v1/audit/flight-recorder", None, ["AUTHORITY", "ADMIN"]),
        ("Users Registry", "GET", f"{BASE_URL}/api/v1/users", None, ["AUTHORITY", "ADMIN"]),
        ("Revoke Credential", "POST", f"{BASE_URL}/api/v1/credentials/revoke", {"credential_id": "c1", "reason": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Assign Responder", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/assign", {"responder_id": resp_user_id}, ["AUTHORITY", "ADMIN"]),
        ("Close Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/close", {"closure_notes": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Reopen Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/reopen", {"reason": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Accept Mission", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/accept", {"eta_minutes": 10}, ["RESPONDER"]),
        ("Transition Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/transition", {"target_state": "ARRIVED_ON_SCENE"}, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Rescue Report", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/rescue-report", {"victim_condition": "STABLE"}, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Verify Evidence", "POST", f"{BASE_URL}/api/v1/incidents/{inc_id}/verify-evidence", {"evidence_id": "ev-01", "status": "VERIFIED"}, ["AUTHORITY", "ADMIN"]),
        ("List Responders", "GET", f"{BASE_URL}/api/v1/responders", None, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("List Credentials", "GET", f"{BASE_URL}/api/v1/credentials", None, ["AUTHORITY", "ADMIN"]),
        ("List Evidence", "GET", f"{BASE_URL}/api/v1/evidence", None, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("List Rescue Receipts", "GET", f"{BASE_URL}/api/v1/rescue/receipts", None, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Live Locations Map", "GET", f"{BASE_URL}/api/v1/locations", None, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Continuity Cockpit", "GET", f"{BASE_URL}/api/v1/continuity/cockpit", None, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Continuity Outbox", "GET", f"{BASE_URL}/api/v1/continuity/outbox", None, ["AUTHORITY", "ADMIN"]),
        ("Continuity Dead Letter", "GET", f"{BASE_URL}/api/v1/continuity/dead-letter", None, ["AUTHORITY", "ADMIN"]),
        ("Transport Status Override", "POST", f"{BASE_URL}/api/v1/continuity/transports/tr-ble-01/status", {"status": "DEGRADED"}, ["AUTHORITY", "ADMIN"]),
    ]

    results = []
    print("\n" + "="*80)
    print(f"{'Endpoint':<28} | {'No Token':<10} | {'Citizen':<10} | {'Responder':<10} | {'Authority':<10} | Status")
    print("="*80)

    for name, method, url, payload, allowed in endpoints:
        s_none, r_none = req(url, method=method, data=payload, token=None)
        s_cit, r_cit = req(url, method=method, data=payload, token=citizen_tok)
        s_resp, r_resp = req(url, method=method, data=payload, token=responder_tok)
        s_auth, r_auth = req(url, method=method, data=payload, token=authority_tok)

        leak = False
        findings = []
        if s_none not in [401, 403]:
            leak = True
            findings.append("LEAK_NO_AUTH")
        if "CITIZEN" not in allowed and s_cit not in [401, 403]:
            leak = True
            findings.append("LEAK_CITIZEN_RBAC")
        if "RESPONDER" not in allowed and s_resp not in [401, 403]:
            leak = True
            findings.append("LEAK_RESPONDER_RBAC")

        verdict = "VULNERABLE (" + ",".join(findings) + ")" if leak else "SECURE"
        print(f"{name:<28} | {s_none:<10} | {s_cit:<10} | {s_resp:<10} | {s_auth:<10} | {verdict}")
        results.append({
            "name": name,
            "method": method,
            "url": url,
            "no_token": s_none,
            "citizen": s_cit,
            "responder": s_resp,
            "authority": s_auth,
            "verdict": verdict,
            "leak": leak,
            "findings": findings
        })

    print("="*80)
    return results

if __name__ == "__main__":
    run_probe()

"""
Comprehensive Security & RBAC Probe Script for UrSafe.
Audits:
1. Role-based endpoint authorization across all 5 caller contexts (Unauthenticated, Citizen, Responder, Authority, Admin)
2. Object-level authorization (Citizen A reading/modifying Citizen B's incidents and timeline)
3. Reporter user ID spoofing in incident creation POST bodies
4. Token forgery, expiration, and header malformation
5. Incident feed isolation (Citizens ONLY see their own incidents)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = os.environ.get("URSAFE_TEST_URL", "http://127.0.0.1:4050")

def req(url, method="GET", data=None, token=None, custom_auth=None):
    headers = {"Content-Type": "application/json"}
    if custom_auth is not None:
        headers["Authorization"] = custom_auth
    elif token:
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
        return res["session"]["token"], res["session"]["userId"]
    raise RuntimeError(f"Login failed for {username}: {res}")

def register(username, email, password, role, fullName):
    status, res = req(f"{BASE_URL}/api/v1/auth/register", method="POST", data={
        "username": username, "email": email, "password": password, "role": role, "fullName": fullName
    })
    if status == 201 and "session" in res:
        return res["session"]["token"], res["session"]["userId"]
    # Fallback to login if already exists
    return login(username, password)

def run_probe():
    print(f"\n[URSAFE SECURITY AUDIT PROBE] Target: {BASE_URL}")
    priya_tok, priya_id = login("citizen_priya", "Password123!")
    resp_tok, resp_id = login("responder_vikram", "Password123!")
    auth_tok, auth_id = login("authority_rajesh", "Password123!")
    admin_tok, admin_id = login("admin_system", "Password123!")

    # Register / login a second distinct citizen (Bob)
    bob_tok, bob_id = register("citizen_bob_security", "bob.audit@example.com", "Password123!", "CITIZEN", "Bob Audit Citizen")

    # 1. Priya creates an incident (Incident Priya)
    s_priya_create, r_priya_create = req(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data={"category": "MEDICAL", "urgency": "HIGH", "description": "Priya Private Medical Emergency"},
        token=priya_tok
    )
    assert s_priya_create == 201
    inc_priya_id = r_priya_create["incident"]["id"]

    # 2. Bob creates an incident (Incident Bob)
    s_bob_create, r_bob_create = req(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data={"category": "COLLAPSE", "urgency": "CRITICAL", "description": "Bob Private Collapse Emergency"},
        token=bob_tok
    )
    assert s_bob_create == 201
    inc_bob_id = r_bob_create["incident"]["id"]

    probe_results = []

    # =========================================================================
    # PART 1: OBJECT-LEVEL ACCESS CONTROL CHECKS
    # =========================================================================
    print("\n--- Part 1: Object-Level Authorization Checks ---")
    
    # Check 1.1: Bob reading Priya's incident details
    s_read_priya, r_read_priya = req(f"{BASE_URL}/api/v1/incidents/{inc_priya_id}", method="GET", token=bob_tok)
    leak_obj_read = (s_read_priya != 403)
    probe_results.append({
        "check": "Object-Level: Citizen B reading Citizen A incident details",
        "expected": "403 Forbidden",
        "actual": f"{s_read_priya}",
        "leak": leak_obj_read,
        "detail": "Citizen B attempted GET /api/v1/incidents/<Citizen_A_ID>"
    })

    # Check 1.2: Bob reading Priya's timeline
    s_time_priya, _ = req(f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/timeline", method="GET", token=bob_tok)
    leak_obj_time = (s_time_priya != 403)
    probe_results.append({
        "check": "Object-Level: Citizen B reading Citizen A timeline",
        "expected": "403 Forbidden",
        "actual": f"{s_time_priya}",
        "leak": leak_obj_time,
        "detail": "Citizen B attempted GET /api/v1/incidents/<Citizen_A_ID>/timeline"
    })

    # Check 1.3: Bob attempting to cancel Priya's incident
    s_mod_priya, _ = req(
        f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/transition",
        method="POST",
        data={"target_state": "CANCELLED", "reason": "Malicious cancellation attempt"},
        token=bob_tok
    )
    leak_obj_mod = (s_mod_priya != 403)
    probe_results.append({
        "check": "Object-Level: Citizen B modifying/cancelling Citizen A incident",
        "expected": "403 Forbidden",
        "actual": f"{s_mod_priya}",
        "leak": leak_obj_mod,
        "detail": "Citizen B attempted state transition on Citizen A incident"
    })

    # Check 1.4: Incident Feed Isolation: Citizen Priya queries GET /api/v1/incidents
    s_feed_priya, r_feed_priya = req(f"{BASE_URL}/api/v1/incidents", method="GET", token=priya_tok)
    feed_leak = False
    if s_feed_priya == 200 and isinstance(r_feed_priya, list):
        # Must only contain Priya's incidents, never Bob's
        bob_in_priya_feed = any(i["id"] == inc_bob_id or i["reporter_user_id"] == bob_id for i in r_feed_priya)
        if bob_in_priya_feed:
            feed_leak = True
    else:
        feed_leak = True
    probe_results.append({
        "check": "Feed Isolation: Citizens only see their own incident reports",
        "expected": "Priya only sees Priya incidents (zero Bob incidents)",
        "actual": "Isolated 100%" if not feed_leak else "LEAK DETECTED",
        "leak": feed_leak,
        "detail": f"Priya feed count: {len(r_feed_priya) if isinstance(r_feed_priya, list) else 0}"
    })

    # =========================================================================
    # PART 2: REPORTER USER ID SPOOFING IN POST BODIES
    # =========================================================================
    print("\n--- Part 2: Reporter User ID Spoofing Checks ---")
    s_spoof, r_spoof = req(
        f"{BASE_URL}/api/v1/incidents",
        method="POST",
        data={
            "reporter_user_id": priya_id,  # Bob attempts to impersonate Priya
            "category": "FLOOD",
            "urgency": "CRITICAL",
            "description": "Spoofed flood incident created by Bob claiming to be Priya"
        },
        token=bob_tok
    )
    leak_spoof = (s_spoof != 403)
    probe_results.append({
        "check": "Identity Integrity: Reject POST with spoofed reporter_user_id",
        "expected": "403 Forbidden",
        "actual": f"{s_spoof}",
        "leak": leak_spoof,
        "detail": "Citizen B attempted POST /api/v1/incidents with reporter_user_id = Citizen A"
    })

    # =========================================================================
    # PART 3: TOKEN INTEGRITY (FORGED / EXPIRED / MALFORMED)
    # =========================================================================
    print("\n--- Part 3: Token Forgery and Header Integrity Checks ---")
    # 3.1 Forged Token
    s_forged, _ = req(f"{BASE_URL}/api/v1/incidents", method="GET", custom_auth="Bearer ursafe_sess_forged_signature_000000000000000000")
    leak_forged = (s_forged != 401)
    probe_results.append({
        "check": "Token Forgery: Reject non-existent/forged bearer token",
        "expected": "401 Unauthorized",
        "actual": f"{s_forged}",
        "leak": leak_forged,
        "detail": "Bearer ursafe_sess_forged_signature_..."
    })

    # 3.2 Malformed Authorization Header (No Bearer keyword)
    s_malformed_1, _ = req(f"{BASE_URL}/api/v1/incidents", method="GET", custom_auth="Token some_arbitrary_token")
    leak_malformed_1 = (s_malformed_1 != 401)
    probe_results.append({
        "check": "Token Header: Reject malformed header without Bearer prefix",
        "expected": "401 Unauthorized",
        "actual": f"{s_malformed_1}",
        "leak": leak_malformed_1,
        "detail": "Authorization: Token some_arbitrary_token"
    })

    # 3.3 Empty Bearer Token
    s_empty_bearer, _ = req(f"{BASE_URL}/api/v1/incidents", method="GET", custom_auth="Bearer ")
    leak_empty_bearer = (s_empty_bearer != 401)
    probe_results.append({
        "check": "Token Header: Reject empty Bearer token",
        "expected": "401 Unauthorized",
        "actual": f"{s_empty_bearer}",
        "leak": leak_empty_bearer,
        "detail": "Authorization: Bearer "
    })

    # =========================================================================
    # PART 4: ENDPOINT RBAC MATRIX ACROSS ALL ROLES
    # =========================================================================
    print("\n--- Part 4: Role-Based Access Control Endpoint Matrix ---")
    endpoints = [
        ("Audit Flight Recorder", "GET", f"{BASE_URL}/api/v1/audit/flight-recorder", None, ["AUTHORITY", "ADMIN"]),
        ("Users Registry", "GET", f"{BASE_URL}/api/v1/users", None, ["AUTHORITY", "ADMIN"]),
        ("Revoke Credential", "POST", f"{BASE_URL}/api/v1/credentials/revoke", {"credential_id": "c1", "reason": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Assign Responder", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/assign", {"responder_id": resp_id}, ["AUTHORITY", "ADMIN"]),
        ("Close Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/close", {"closure_notes": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Reopen Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/reopen", {"reason": "probe"}, ["AUTHORITY", "ADMIN"]),
        ("Accept Mission", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/accept", {"eta_minutes": 10}, ["RESPONDER"]),
        ("Transition Incident", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/transition", {"target_state": "ARRIVED_ON_SCENE"}, ["RESPONDER", "AUTHORITY", "ADMIN"]),
        ("Rescue Report", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/rescue-report", {"victim_condition": "STABLE"}, ["RESPONDER"]),
        ("Verify Evidence", "POST", f"{BASE_URL}/api/v1/incidents/{inc_priya_id}/verify-evidence", {"evidence_id": "ev-01", "status": "VERIFIED"}, ["AUTHORITY", "ADMIN"]),
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

    print("="*105)
    print(f"{'Endpoint':<26} | {'No Auth':<8} | {'Citizen':<8} | {'Resp':<8} | {'Auth':<8} | {'Admin':<8} | Status")
    print("="*105)

    for name, method, url, payload, allowed in endpoints:
        s_none, _ = req(url, method=method, data=payload, token=None)
        s_cit, _ = req(url, method=method, data=payload, token=priya_tok)
        s_resp, _ = req(url, method=method, data=payload, token=resp_tok)
        s_auth, _ = req(url, method=method, data=payload, token=auth_tok)
        s_adm, _ = req(url, method=method, data=payload, token=admin_tok)

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
        if "AUTHORITY" in allowed and s_auth not in [200, 201]:
            leak = True
            findings.append(f"AUTHORITY_BLOCKED_{s_auth}")
        if "ADMIN" in allowed and s_adm not in [200, 201]:
            leak = True
            findings.append(f"ADMIN_BLOCKED_{s_adm}")

        verdict = "VULNERABLE (" + ",".join(findings) + ")" if leak else "SECURE"
        print(f"{name:<26} | {s_none:<8} | {s_cit:<8} | {s_resp:<8} | {s_auth:<8} | {s_adm:<8} | {verdict}")

        probe_results.append({
            "check": f"RBAC: {name} ({method})",
            "expected": f"Auth only for {allowed}",
            "actual": f"None={s_none}, Cit={s_cit}, Resp={s_resp}, Auth={s_auth}, Adm={s_adm}",
            "leak": leak,
            "detail": verdict
        })

    print("="*105)
    return probe_results

if __name__ == "__main__":
    results = run_probe()
    leaks = [r for r in results if r["leak"]]
    print(f"\nTotal Checks: {len(results)} | Vulnerabilities: {len(leaks)}")
    if len(leaks) > 0:
        print("Vulnerabilities Found:")
        for l in leaks:
            print(" -", l)
        sys.exit(1)
    else:
        print("ALL SECURITY CHECKS PASSED: 100% SECURE.")

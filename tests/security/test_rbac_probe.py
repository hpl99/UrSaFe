"""
Test that runs the comprehensive RBAC probe against all sensitive endpoints.
"""

from scripts.probe_rbac import run_probe

def test_rbac_security_probe(session_api_server):
    results = run_probe()
    assert len(results) > 0
    leaks = [r for r in results if r["leak"]]
    assert len(leaks) == 0, f"Security leak detected: {leaks}"


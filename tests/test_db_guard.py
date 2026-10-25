import subprocess
import os
import sys
import pytest

def test_safety_guard_refuses_production_db_in_test_env():
    """Safety Guard Test: Node backend must refuse to start against any DB path containing 'production' in test environment."""
    env = os.environ.copy()
    env["NODE_ENV"] = "test"
    env["URSAFE_DB_PATH"] = "data/ursafe_production.db"
    
    proc = subprocess.run(
        ["node", "-e", "require('./apps/api/db');"],
        env=env,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    
    assert proc.returncode != 0
    assert "[CRITICAL SAFETY GUARD] Refusing to run tests against production database" in proc.stderr


def test_safety_guard_allows_isolated_temp_db():
    """Safety Guard Test: Node backend starts normally with isolated test database."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        env = os.environ.copy()
        env["NODE_ENV"] = "test"
        env["URSAFE_DB_PATH"] = tmp_path
        
        proc = subprocess.run(
            ["node", "-e", "const { db } = require('./apps/api/db'); console.log('GUARD_PASSED_OK');"],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        assert proc.returncode == 0
        assert "GUARD_PASSED_OK" in proc.stdout
    finally:
        for ext in ["", "-wal", "-shm"]:
            f = tmp_path + ext
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

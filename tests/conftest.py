import os
import sys
import tempfile
import urllib.request
import subprocess
import time
import pytest

# Ensure repo root is on sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Global test environment configuration
os.environ["NODE_ENV"] = "test"
os.environ["TESTING"] = "true"

# Safety Guard: Ensure test runner never points to a production database
if "URSAFE_DB_PATH" in os.environ:
    if "production" in os.environ["URSAFE_DB_PATH"].lower():
        raise RuntimeError(
            f"[CRITICAL SAFETY GUARD] Refusing to start pytest against production database path: {os.environ['URSAFE_DB_PATH']}"
        )
else:
    # Default test database: isolated temporary file
    test_db_fd, test_db_path = tempfile.mkstemp(prefix="ursafe_test_", suffix=".db")
    os.close(test_db_fd)
    os.environ["URSAFE_DB_PATH"] = test_db_path

# Ensure test URL default points to dedicated test server port if not set
TEST_PORT = 4050
if "URSAFE_TEST_URL" not in os.environ:
    os.environ["URSAFE_TEST_URL"] = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database():
    """Session-scoped fixture providing an isolated temporary database for the test run."""
    db_path = os.environ["URSAFE_DB_PATH"]
    assert "production" not in db_path.lower(), f"Safety violation: Test database path contains 'production': {db_path}"
    
    yield db_path

    # Cleanup temp files after test session finishes
    for ext in ["", "-wal", "-shm"]:
        p = db_path + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


@pytest.fixture(scope="session", autouse=True)
def session_api_server(isolated_test_database):
    """Session-scoped test server ensuring integration & security tests have an active server."""
    test_url = os.environ["URSAFE_TEST_URL"]
    
    # Check if a server is already listening
    already_running = False
    try:
        with urllib.request.urlopen(f"{test_url}/api/v1/health", timeout=1) as resp:
            if resp.status == 200:
                already_running = True
    except Exception:
        already_running = False

    if already_running:
        yield test_url
        return

    # Start dedicated test server process
    env = os.environ.copy()
    env["PORT"] = str(TEST_PORT)
    env["NODE_ENV"] = "test"
    env["URSAFE_DB_PATH"] = isolated_test_database
    env.pop("BACKEND_PORT", None)

    proc = subprocess.Popen(
        ["node", "apps/web-console/server.js"],
        env=env,
        cwd=repo_root
    )

    # Wait for server ready
    ready = False
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"{test_url}/api/v1/health", timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.1)

    if not ready:
        proc.kill()
        raise RuntimeError(f"Failed to start session API test server on {test_url}")

    yield test_url

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()

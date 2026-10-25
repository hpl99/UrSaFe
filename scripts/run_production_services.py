"""
UrSafe Production Services Supervisor.
Spawns, monitors, and auto-restarts the UrSafe Coordination Hub & API Gateway on port 3000.
"""

import os
import sys
import time
import signal
import subprocess
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "apps", "web-console", "server.js")
PORT = int(os.environ.get("PORT", "3000"))
HEALTH_URL = f"http://localhost:{PORT}/api/v1/health"

running_process = None

def signal_handler(sig, frame):
    global running_process
    print("\n[Supervisor] Shutting down UrSafe services...")
    if running_process:
        running_process.terminate()
        try:
            running_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            running_process.kill()
    sys.exit(0)

def is_healthy():
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    global running_process
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"============================================================")
    print(f" UrSafe Production Services Supervisor                      ")
    print(f" Target: {SERVER_SCRIPT}")
    print(f" Port:   http://localhost:{PORT}")
    print(f" Health: {HEALTH_URL}")
    print(f"============================================================")

    env = os.environ.copy()
    env["PORT"] = str(PORT)

    while True:
        print(f"[*] Starting UrSafe node service on port {PORT}...")
        running_process = subprocess.Popen(
            ["node", SERVER_SCRIPT],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        # Wait for service to become healthy
        healthy = False
        for _ in range(10):
            time.sleep(0.5)
            if is_healthy():
                healthy = True
                print(f"[✓] UrSafe Coordination Hub is HEALTHY at {HEALTH_URL}")
                break

        if not healthy and running_process.poll() is not None:
            print(f"[!] UrSafe service exited immediately with code {running_process.returncode}. Restarting in 2s...")
            time.sleep(2)
            continue

        # Monitor loop
        while running_process.poll() is None:
            time.sleep(2)
            if not is_healthy():
                print(f"[!] Health check failed at {HEALTH_URL}. Inspecting...")

        print(f"[!] UrSafe service died with exit code {running_process.returncode}. Auto-restarting in 1s...")
        time.sleep(1)

if __name__ == "__main__":
    main()

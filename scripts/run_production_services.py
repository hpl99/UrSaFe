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

    print("============================================================")
    print(" UrSafe Production Services Supervisor                      ")
    print(f" Target: {SERVER_SCRIPT}")
    print(f" Port:   http://localhost:{PORT}")
    print(f" Health: {HEALTH_URL}")
    print("============================================================")

    # Check if an instance is ALREADY running on this port
    if is_healthy():
        print(f"\n[✓] UrSafe Coordination Hub is ALREADY RUNNING and healthy on port {PORT}!")
        print(f"    You can access it directly at: http://localhost:{PORT}")
        print("    If you want to restart it, stop the existing process first.")
        print("\nPress Ctrl+C to exit supervisor.")
        while is_healthy():
            time.sleep(3)
        print("[!] Existing instance stopped. Spawning new instance...")

    env = os.environ.copy()
    env["PORT"] = str(PORT)

    consecutive_crashes = 0

    while True:
        print(f"[*] Starting UrSafe node service on port {PORT}...")
        running_process = subprocess.Popen(
            ["node", SERVER_SCRIPT],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        # Allow time to bind port
        time.sleep(1)

        # Check if it died immediately (e.g. port collision)
        if running_process.poll() is not None:
            consecutive_crashes += 1
            exit_code = running_process.returncode
            if is_healthy():
                print(f"[✓] Port {PORT} is already in use by an active healthy UrSafe server.")
                print(f"    Open your browser at: http://localhost:{PORT}")
                return
            print(f"[!] UrSafe service failed to start (exit code {exit_code}).")
            if consecutive_crashes >= 3:
                print("[!] Multiple startup failures. Port 3000 may be blocked. Exiting.")
                return
            time.sleep(2)
            continue

        consecutive_crashes = 0
        print(f"[✓] UrSafe Coordination Hub is running at http://localhost:{PORT}")

        # Monitor loop
        while running_process.poll() is None:
            time.sleep(3)

        exit_code = running_process.returncode
        print(f"[!] UrSafe service stopped (exit code {exit_code}). Restarting in 2 seconds...")
        time.sleep(2)

if __name__ == "__main__":
    main()

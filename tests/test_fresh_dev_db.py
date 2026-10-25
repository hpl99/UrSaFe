"""
Test verifying that a fresh dev/non-test database boots with zero fake devices,
zero fake mesh nodes, and zero CONNECTED transports.
"""

import os
import tempfile
import subprocess
import json
import pytest


def test_fresh_dev_db_has_no_fake_devices_and_no_connected_transports():
    """Verify that a freshly initialized dev database contains no mock devices and no connected transports."""
    temp_dir = tempfile.mkdtemp()
    fresh_db_path = os.path.join(temp_dir, "ursafe_fresh_dev.db").replace("\\", "/")

    script = f"""
    const path = require('path');
    process.env.URSAFE_DB_PATH = '{fresh_db_path}';
    delete process.env.NODE_ENV;
    delete process.env.PYTEST_CURRENT_TEST;
    delete process.env.TESTING;

    // Boot database interface which executes migrations and seedInitialData
    const {{ db }} = require('./apps/api/db');

    const devices = db.prepare('SELECT * FROM devices').all();
    const meshNodes = db.prepare('SELECT * FROM mesh_nodes').all();
    const transports = db.prepare('SELECT * FROM continuity_transports').all();

    console.log(JSON.stringify({{
      deviceCount: devices.length,
      devices,
      meshNodeCount: meshNodes.length,
      meshNodes,
      transportCount: transports.length,
      connectedTransports: transports.filter(t => t.status === 'CONNECTED' || t.is_connected === 1),
      allTransports: transports.map(t => ({{ id: t.transport_id, status: t.status, is_connected: t.is_connected }}))
    }}));
    """

    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(res.stdout.strip().split("\n")[-1])

    # 1. Zero fake devices
    assert out["deviceCount"] == 0, f"Expected 0 devices in fresh dev DB, found: {out['devices']}"
    assert out["meshNodeCount"] == 0, f"Expected 0 mesh nodes in fresh dev DB, found: {out['meshNodes']}"

    # 2. Zero connected transports
    assert len(out["connectedTransports"]) == 0, f"Expected 0 CONNECTED transports, found: {out['connectedTransports']}"

    # 3. Transports must start DISCONNECTED/UNKNOWN
    assert out["transportCount"] >= 5, "Expected seeded authoritative transport placeholders"
    for t in out["allTransports"]:
        assert t["status"] in ("DISCONNECTED", "UNKNOWN"), f"Transport {t['id']} has invalid initial status: {t['status']}"
        assert t["is_connected"] == 0, f"Transport {t['id']} has is_connected != 0: {t['is_connected']}"

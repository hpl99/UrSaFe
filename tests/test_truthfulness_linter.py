"""
CI Truthfulness Static Linter Test Suite.
Enforces that no known fake metrics, misleading claims, or invalid hardware
literals ever reappear in client-facing applications or production service code.
"""

import os
import re
import pytest

BANNED_PATTERNS = [
    r"14,892",
    r"12,408",
    r"B-77",
    r"94\.2",
    r"99\.4",
    r"\bOPTIMAL\b",
    r"100%\s*OFF-GRID",
    r"\bUS915\b",
    r"0xFFF0\b",
]

TARGET_DIRS = [
    os.path.join("apps", "web-console"),
    os.path.join("apps", "api"),
    os.path.join("apps", "victim-android"),
    os.path.join("apps", "responder-android"),
]

VALID_EXTENSIONS = {".html", ".js", ".css", ".kt", ".kts", ".java", ".json", ".sql"}


def test_no_banned_fake_literals_in_source():
    """Scans all UI and service source code for banned fake literals."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    compiled_patterns = [(p, re.compile(p, re.IGNORECASE)) for p in BANNED_PATTERNS]

    violations = []

    for target_dir in TARGET_DIRS:
        abs_target_dir = os.path.join(repo_root, target_dir)
        if not os.path.exists(abs_target_dir):
            continue

        for root, dirs, files in os.walk(abs_target_dir):
            # Skip build and node_modules
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "build", ".gradle"}]

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in VALID_EXTENSIONS:
                    continue

                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, repo_root)

                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        for pattern_str, regex in compiled_patterns:
                            if regex.search(line):
                                violations.append({
                                    "file": rel_path,
                                    "line": line_idx,
                                    "pattern": pattern_str,
                                    "content": line.strip()
                                })

    assert len(violations) == 0, (
        f"Truthfulness static lint failed: Found {len(violations)} banned fake literal(s):\n"
        + "\n".join([f"  {v['file']}:{v['line']} [{v['pattern']}] -> {v['content']}" for v in violations])
    )

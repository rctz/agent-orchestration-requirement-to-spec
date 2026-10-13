"""Golden tests for the ported v2 men converters (M8 verify item).

Wraps req3/render/men_pkg/tests/run_golden.py — byte-exact fixtures from
the v2 corpus. Exit 0 = green; any drift fails the suite.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT = REPO_ROOT / "req3" / "render" / "men_pkg" / "tests" / "run_golden.py"


def test_men_golden_fixtures():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(REPO_ROOT),
        check=False,
    )
    tail = "\n".join(result.stdout.splitlines()[-8:])
    assert result.returncode == 0, f"golden tests failed:\n{tail}\n{result.stderr}"
    assert "PASS men-spi" in result.stdout
    assert "PASS men-plan" in result.stdout

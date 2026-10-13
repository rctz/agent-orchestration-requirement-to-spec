#!/usr/bin/env python3
"""SR11: run every probe file cited as live evidence in the v12 header; report status."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "13-spec-design-probes.py",
    "20-rev3-order-probes.py",
    "22-rev4-writeorder-probes.py",
    "30b-adv-c6-reaim-probes.py",
    "32-rev8-fdclose-probes.py",
    "36-rev9-ki-argparse-probes.py",
    "41-rev10-adv9-folds-probes.py",
    "47-rev11-adv10-folds-probes.py",
    "48b-adv-c11-probes.py",
    "51-rev12-adv11-folds-probes.py",
]

for f in FILES:
    p = ROOT / "appendix" / f
    try:
        r = subprocess.run(
            [sys.executable, str(p)],
            capture_output=True, text=True, timeout=300, cwd=str(ROOT),
        )
        tail = (r.stdout or r.stderr).strip().splitlines()
        last = tail[-1] if tail else "(no output)"
        status = "RUNS" if r.returncode == 0 else f"exit {r.returncode}"
        print(f"{f:38s} {status:9s} | {last[:100]}")
    except subprocess.TimeoutExpired:
        print(f"{f:38s} TIMEOUT")

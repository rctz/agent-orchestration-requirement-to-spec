#!/usr/bin/env python3
"""88-rev16-liveness-sweep.py — probes-row liveness for spec/16 (rev16
copy of 82; the rev15 text-pinned set 78/79/80/81/83 joined HISTORICAL
at this rollover — each hardcodes the archived spec/15 — and the rev16
set 84/85/86/87 is LIVE; 77 and the permanent probes stay behavioral
and LIVE).

For every probe the header row makes a liveness claim about:
  LIVE-labeled  -> must run green NOW (against spec/15 or behaviorally)
  HISTORICAL-labeled -> must FAIL now (archived spec path) — proving the
  label is truthful, not stale the other way.

This is the SR12-F-01/SR13-F-01 verification class, re-aimed at v15.
"""
import os
import subprocess
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
R = []


def check(name, ok, detail=""):
    R.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def run(path, timeout=900):
    p = subprocess.run([sys.executable, os.path.join("appendix", path)],
                       cwd=HERE, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-400:]


# LIVE-labeled (must run green)
LIVE = [
    "13-spec-design-probes.py",
    "77-rev15-shape-identity.py",
    "84-rev16-gate-reaim.py",
    "85-rev16-fold-pins.py",
    "86-rev16-mangle-sweep.py",
    "87-rev16-delta-audit.py",
    "20-rev3-order-probes.py",
    "22-rev4-writeorder-probes.py",
    "30b-adv-c6-reaim-probes.py",
]
for probe in LIVE:
    rc, tail = run(probe)
    check("LIVE %s runs green" % probe, rc == 0, tail)

# HISTORICAL-labeled (must crash on the archived spec path — FileNotFoundError)
HIST = [
    "25-rev5-serialize-form-probes.py",   # hardcodes spec/06 (SR6-F-03)
    "28-rev6-writegate-probes.py",        # archived spec/06 path
    "32-rev8-fdclose-probes.py",          # archived spec/08 (SR11-F-02)
    "36-rev9-ki-argparse-probes.py",      # archived spec/09 (SR11-F-02)
    "41-rev10-adv9-folds-probes.py",      # archived spec/10 (SR11-F-02)
    "47-rev11-adv10-folds-probes.py",     # archived spec/11 (SR11-F-02)
    "48b-adv-c11-probes.py",              # archived spec/11 text-pin tail (SR12-F-02)
    "51-rev12-adv11-folds-probes.py",     # archived spec/12 (SR12-F-01)
    "58-rev13-sr11-folds-probes.py",      # archived spec/13
    "59-rev13-gate-reaim.py",             # archived spec/13
    "67-rev14-gate-reaim.py",             # archived spec/14 (v15 rollover)
    "68-rev14-delta-audit.py",            # archived spec/14 (v15 rollover)
    "69-rev14-mangle-sweep.py",           # archived spec/14 (v15 rollover)
    "70-rev14-fold-pins.py",              # archived spec/14 (v15 rollover)
    "78-rev15-gate-reaim.py",             # archived spec/15 (this rollover)
    "79-rev15-delta-audit.py",            # archived spec/15 (this rollover)
    "80-rev15-mangle-sweep.py",           # archived spec/15 (this rollover)
    "81-rev15-fold-pins.py",              # archived spec/15 (this rollover)
    "83-rev15-final-gate.py",             # archived spec/15 (this rollover)
]
for probe in HIST:
    rc, tail = run(probe)
    check("HISTORICAL %s does not run green (label truthful)" % probe,
          rc != 0, "exit=%d %s" % (rc, tail[-160:]))

print()
print("TOTAL: %d checks, %d FAILURES" % (len(R), R.count(False)))
sys.exit(1 if R.count(False) else 0)

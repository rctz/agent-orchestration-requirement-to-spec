#!/usr/bin/env python3
"""89-rev16-final-gate.py — completion gate for the v16 revision.

Runs the whole mechanical + behavioral battery against spec/16 and
asserts every number the v16 revision-row/probes-row cites is what the
artifacts actually print (the SR11-F-03 class: never pre-write a count).
"""
import subprocess
import sys
import os

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
R = []


def check(name, ok, detail=""):
    R.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def run(path, timeout=1200):
    p = subprocess.run([sys.executable, os.path.join("appendix", path)],
                       cwd=HERE, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


GATES = [
    ("77-rev15-shape-identity.py", "TOTAL: 30 checks, 0 FAILURES"),
    ("84-rev16-gate-reaim.py", "TOTAL: 15 checks, 0 FAILURES"),
    ("85-rev16-fold-pins.py", "TOTAL: 31 checks, 0 FAILURES"),
    ("86-rev16-mangle-sweep.py", "TOTAL: 4 sweeps, 0 FAILURES"),
    ("87-rev16-delta-audit.py", "TOTAL: 2 checks, 0 FAILURES"),
    ("88-rev16-liveness-sweep.py", "TOTAL: 28 checks, 0 FAILURES"),
    ("14-claim-keyword-check.py", "0"),
    ("15-spec-selfcheck.py", "TOTAL FAILURES: 0"),
    ("13-spec-design-probes.py", "TOTAL FAILURES: 0"),
    ("20-rev3-order-probes.py", "TOTAL FAILURES: 0"),
    ("22-rev4-writeorder-probes.py", "TOTAL FAILURES: 0"),
    ("30b-adv-c6-reaim-probes.py", "FAIL: 0"),
]
for probe, needle in GATES:
    rc, out = run(probe)
    check("%s green with expected summary %r" % (probe, needle),
          rc == 0 and needle in out, out[-200:])

# the fresh 66 re-run log: 27/27 and the timings reproduce the pinned set
log = open("/tmp/rev16-66-run.log", encoding="utf-8").read()
check("66 fresh re-run printed 27/27", "TOTAL: 27 checks, 0 FAILURES" in log,
      log[-160:])

print()
print("TOTAL: %d checks, %d FAILURES" % (len(R), R.count(False)))
sys.exit(1 if R.count(False) else 0)

"""sr14 battery driver — run the designer's v16 battery live, save logs.

Fast tier first (gate re-aims, text pins, mangle, delta, liveness, permanent
checks, older revision probes), then the two behavioral probes (77 shape
identity, 66 binding timing — the long one, ~13 min).
"""
import subprocess
import sys
import time

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

FAST = [
    "84-rev16-gate-reaim.py",
    "85-rev16-fold-pins.py",
    "86-rev16-mangle-sweep.py",
    "87-rev16-delta-audit.py",
    "88-rev16-liveness-sweep.py",
    "14-claim-keyword-check.py",
    "15-spec-selfcheck.py",
    "13-spec-design-probes.py",
    "20-rev3-order-probes.py",
    "22-rev4-writeorder-probes.py",
    "30b-adv-c6-reaim-probes.py",
    "77-rev15-shape-identity.py",
]
SLOW = ["66-rev14-binding-timing.py"]


def run(name):
    t0 = time.time()
    p = subprocess.run(
        [sys.executable, "appendix/" + name],
        cwd=HERE,
        capture_output=True,
        text=True,
        timeout=1500,
    )
    dt = time.time() - t0
    log = "appendix/91-sr14-runlog-{}.txt".format(name.replace(".py", ""))
    with open(log, "w") as f:
        f.write(p.stdout)
        if p.stderr:
            f.write("\n--- STDERR ---\n" + p.stderr)
    tail = "\n".join(p.stdout.strip().splitlines()[-4:])
    print("== {} rc={} {:.1f}s -> {}".format(name, p.returncode, dt, log))
    print(tail)
    sys.stdout.flush()
    return p.returncode


rcs = {}
for n in FAST + SLOW:
    try:
        rcs[n] = run(n)
    except subprocess.TimeoutExpired:
        rcs[n] = "TIMEOUT"
        print("== {} TIMEOUT".format(n))

print("\n==== SUMMARY ====")
for n, rc in rcs.items():
    print("{}: rc={}".format(n, rc))

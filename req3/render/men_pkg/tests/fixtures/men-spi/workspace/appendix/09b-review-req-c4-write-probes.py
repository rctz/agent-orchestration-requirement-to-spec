"""Cycle-4 review probes: output-write phase (F-28 candidate) — live grounding.

Run: python3 appendix/09b-review-req-c4-write-probes.py  (needs /dev/full)
"""
import sys

results = []

# W1: a partial write to /dev/full raises OSError ENOSPC at flush/close time,
# after bytes have "gone out" — i.e. mid-write failure is a real class.
try:
    with open("/dev/full", "w") as f:
        f.write('["ok"' + "x" * 50 + "]")
        f.flush()
    print("W1 mid-write: UNEXPECTED SUCCESS (wrote to /dev/full?!)")
except OSError as e:
    results.append(("W1 mid-write OSError raised at flush",
                    True, f"{type(e).__name__} errno={e.errno} {e.strerror}"))

# W2: text-mode write on a POSIX system: does open(path, "w") translate \n?
# (Demonstrates the default text-mode newline behavior the doc never pins.)
with open("/tmp/c4_probe_out.json", "w") as f:
    f.write('["x\\r\\ny"]\n')
with open("/tmp/c4_probe_out.json", "rb") as f:
    b = f.read()
results.append(("W2 default text-mode keeps CRLF bytes on Linux",
                b == b'["x\\r\\ny"]\n', f"bytes={b!r}"))

for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
sys.exit(0 if all(ok for _, ok, _ in results) else 1)

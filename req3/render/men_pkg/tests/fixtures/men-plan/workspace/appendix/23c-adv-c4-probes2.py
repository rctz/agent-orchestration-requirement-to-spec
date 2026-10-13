# 23c-adv-c4-probes2.py — adversarial-early cycle 4, second probe batch
# QC-1 stderr-print failure mechanics; csv NUL cells (S-13); nothing else.
import csv
import io
import json
import os
import subprocess
import sys

FAILED = []

def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name} — {detail}")
    if not cond:
        FAILED.append(name)

# --- Q1: surrogate escape in an OS-decoded path -> stderr write behavior
r = subprocess.run(
    [sys.executable, "-c", "import sys; sys.stderr.write('p: \\udcff\\n')"],
    capture_output=True)
check("Q1a lone surrogate via sys.stderr.write does NOT raise (errors=backslashreplace)",
      r.returncode == 0,
      f"rc={r.returncode} err={r.stderr[:40]!r}")
r2 = subprocess.run(
    [sys.executable, "-c",
     "import sys\ntry:\n    raise ValueError('x \\udcff')\nexcept ValueError as e:\n    print('csv2json: error:', e, file=sys.stderr)"],
    capture_output=True)
check("Q1b print() of surrogate-bearing message inside except does NOT raise",
      r2.returncode == 0,
      f"rc={r2.returncode} err={r2.stderr[:60]!r}")

# --- Q2: stderr pipe closed at reader end -> EPIPE during error print
code = (
    "import sys\n"
    "try:\n"
    "    raise ValueError('boom')\n"
    "except ValueError:\n"
    "    try:\n"
    "        print('csv2json: error: net', file=sys.stderr)\n"
    "    except BrokenPipeError:\n"
    "        sys.exit(3)\n"
    "    sys.exit(0)\n"
)
rd, wr = os.pipe()
proc = subprocess.Popen([sys.executable, "-c", code],
                        stdout=subprocess.DEVNULL, stderr=wr,
                        pass_fds=(wr,))
os.close(wr)
os.close(rd)  # reader gone
rc = proc.wait()
check("Q2 EPIPE on the error print is catchable as BrokenPipeError (best-effort wrap is implementable)",
      rc in (0, 3),  # rc==3 means the wrap caught it; rc==0 means write went to buffer
      f"rc={rc}")

# --- Q3: does an UNwrapped print to broken stderr escape as traceback?
code2 = (
    "import sys\n"
    "try:\n"
    "    raise ValueError('boom')\n"
    "except ValueError:\n"
    "    print('csv2json: error: net', file=sys.stderr)\n"
    "    sys.exit(0)\n"
)
proc2 = subprocess.Popen([sys.executable, "-c", code2],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
# force small pipe: close read end after short sleep by consuming nothing
proc2_later = None
try:
    proc2.wait(timeout=0.2)
except subprocess.TimeoutExpired:
    proc2.terminate()
    proc2.wait()
rc2 = proc2.returncode
# (pipe buffer usually absorbs the message; rc2==0 here just shows buffering —
#  the catchability result is Q2's job; this run only records it)
check("Q3 record: unwrapped print on normal-pipe stderr exits 0 (buffered)",
      rc2 == 0, f"rc={rc2}")

# --- Q4: csv NUL in an unquoted cell (S-13's 'NUL in cells are data')
try:
    rows = list(csv.reader(io.StringIO('a,b\n1\x002\n', newline="")))
    ok = rows == [["a", "b"], ["1\x002"]]
except Exception as e:
    ok, rows = False, repr(e)
check("Q4a csv.reader keeps NUL in an unquoted cell verbatim", ok, repr(rows))
try:
    s = json.dumps([{"a": "1\x002"}], ensure_ascii=False, separators=(",", ":"))
    check("Q4b json.dumps emits \\u0000 for NUL", s == '[{"a":"1\\u00002"}]', s)
except Exception as e:
    check("Q4b json.dumps emits \\u0000 for NUL", False, repr(e))

print(f"TOTAL FAILURES: {len(FAILED)}")
sys.exit(1 if FAILED else 0)

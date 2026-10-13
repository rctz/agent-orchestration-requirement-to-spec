#!/usr/bin/env python3
"""Spec-review cycle 6 probes — spec/07-spec-v7.md (reviewer's own evidence).

Verifies the candidate findings of appendix/31-review-spec-c6.md live:
  V1  D-48 except-scoped reference shape (spec §4.5 block, verbatim
      semantics): SUCCESS path keeps the file with the right bytes
  V2  same shape, FAILURE path: file removed, exception propagates —
      AND the fd is still OPEN at raise time (never closed on the
      failure path; the "never closed the fd" half of the v6 defect
      charge persists in v7 — POSIX-harmless, Windows-fatal to the
      compensation because os.remove on an open file fails there)
  V3  remove-while-open succeeds on POSIX (control showing V2's defect
      is platform-specific, not universal)
  V4  E-DUP-beats-E-UQ premise: lenient parse of `id,"id` yields the
      duplicate pair ['id','id']; `"id,name` yields one field (no dup)
  V5  S-1 golden bytes: `id,name\n1,x\n2,y\n` -> 46-byte payload ending `]\n`
  V6  manual dispatch on `-h out.json` -> E-READ, exit 1, stdout empty (D-49)
  V7  register-vs-spec disagreement is REAL text: register D-46 row still
      prescribes "finally's remove guarded by whether the open succeeded"
      as the reference shape while spec §4.5 pins the except-scoped shape
  V8  stale-path evidence probes crash after the v7 rollover (25/28/28b
      hardcode spec/06-spec-v6.md)
"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name, detail)


def shape_v7(path, payload, fail=False):
    """The §4.5 'Conforming reference shape (e.g.)' verbatim."""
    fd = None
    try:
        fd = open(path, "wb")            # at-open failure: jumps to except, no remove
        if fail:
            raise OSError(5, "injected EIO")
        fd.write(payload); fd.flush()    # encode already done pre-open (D-43)
        fd.close(); fd = None            # closed: nothing left to compensate
    except BaseException:
        if fd is not None:               # open SUCCEEDED and a later step raised
            try: os.remove(path)         # best-effort (D-33; errors ignored)
            except OSError: pass
        raise


def v1_v2_v3():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "out.json")
    payload = b'[{"id":"1"}]\n'
    # V1 success
    shape_v7(p, payload)
    check("V1 success keeps file, right bytes",
          os.path.exists(p) and open(p, "rb").read() == payload)
    # V2 failure: removed + propagates + fd still open at raise time
    p2 = os.path.join(d, "out2.json")
    open(p2, "wb").write(b'{"prior":"good"}')
    raised = None
    try:
        shape_v7(p2, payload, fail=True)
    except OSError as e:
        raised = e
    fd_still_open = None
    if raised is not None:
        tb = raised.__traceback__
        while tb is not None:
            loc = tb.tb_frame.f_locals
            if "fd" in loc and loc["fd"] is not None:
                fd_still_open = not loc["fd"].closed
            tb = tb.tb_next
    check("V2 failure removes file", raised is not None and not os.path.exists(p2))
    check("V2 fd NEVER closed on failure path (open at raise)", fd_still_open is True)
    # V3 POSIX control: remove-while-open succeeds
    p3 = os.path.join(d, "out3.json")
    f3 = open(p3, "wb")
    f3.write(b"partial")
    try:
        os.remove(p3)
        posix_ok = True
    except OSError:
        posix_ok = False
    finally:
        f3.close()
    check("V3 POSIX remove-while-open succeeds (defect is Windows-specific)",
          posix_ok and not os.path.exists(p3))


def v4():
    rows = list(csv.reader(io.StringIO('id,"id', newline="")))
    check("V4a lenient parse of `id,\"id` -> ['id','id'] (dup wins, S-9b)",
          rows == [["id", "id"]])
    rows2 = list(csv.reader(io.StringIO('"id,name', newline="")))
    check("V4b lenient parse of `\"id,name` -> one field, no dup (E-UQ fires)",
          rows2 == [["id,name"]])


def v5():
    text = "id,name\n1,x\n2,y\n"
    rows = [dict(zip(["id", "name"], r))
            for r in list(csv.reader(io.StringIO(text, newline="")))[1:]]
    doc = json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
    b = doc.encode("utf-8")
    check("V5 S-1 golden: 46 bytes ending ]\\n", len(b) == 46 and b[-2:] == b"]\n",
          f"len={len(b)}")


def v6():
    d = tempfile.mkdtemp()
    tool = os.path.join(d, "m.py")
    open(tool, "w").write(
        "import sys\n"
        "def main(argv):\n"
        "    if len(argv) != 2:\n"
        "        print('csv2json: error: usage: csv2json.py <input.csv> <output.json>',"
        " file=sys.stderr)\n"
        "        return 1\n"
        "    try:\n"
        "        open(argv[0], 'rb').read()\n"
        "    except OSError as e:\n"
        "        print(f'csv2json: error: cannot read {argv[0]}: {e.strerror}',"
        " file=sys.stderr)\n"
        "        return 1\n"
        "    return 0\n"
        "sys.exit(main(sys.argv[1:]))\n")
    r = subprocess.run([sys.executable, tool, "-h", "out.json"],
                       capture_output=True, text=True)
    check("V6 `-h out.json` manual dispatch -> E-READ exit 1 stdout empty",
          r.returncode == 1 and r.stdout == ""
          and r.stderr.startswith("csv2json: error: cannot read -h:"),
          f"rc={r.returncode} out={r.stdout!r}")


def v7():
    reg = open(os.path.join(HERE, "appendix", "03-decision-register.md"),
               encoding="utf-8").read()
    spec = open(os.path.join(HERE, "spec", "07-spec-v7.md"),
                encoding="utf-8").read()
    d46 = reg.split("| D-46 |")[1].split("| D-47 |")[0]
    check("V7a register D-46 still prescribes the superseded finally shape",
          "finally's remove guarded by whether the open succeeded" in d46)
    d43 = reg.split("| D-43 |")[1].split("| D-44 |")[0]
    check("V7b register D-43 still names '(try/finally shape)'",
          "(try/finally shape)" in d43)
    check("V7c spec pins the except-scoped shape (D-48 fold present)",
          "except-scoped" in spec and "failure arm ONLY" in spec)


def v8():
    for f in ("25-rev5-serialize-form-probes.py", "28-rev6-writegate-probes.py",
              "28b-rev6-reviewer-reaim-probes.py"):
        path = os.path.join(HERE, "appendix", f)
        r = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=120)
        crashed = ("FileNotFoundError" in r.stderr
                   or "no live spec revision found" in (r.stdout + r.stderr))
        check(f"V8 {f} stale-path (archived v6 target)", crashed)


if __name__ == "__main__":
    v1_v2_v3()
    v4()
    v5()
    v6()
    v7()
    v8()
    n_fail = sum(1 for _, ok in results if not ok)
    print(f"\nTOTAL CHECKS: {len(results)}  PASS: {len(results)-n_fail}  FAIL: {n_fail}")
    sys.exit(1 if n_fail else 0)

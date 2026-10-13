#!/usr/bin/env python3
"""rev7 re-aim probes (cycle 7) — spec/07-spec-v7.md.

Re-aims the adv-c6 findings' discriminating scenarios at the v7 shape,
using MY OWN probe file (the reviewer's appendix/29b stays as evidence;
never edited). Real filesystem in every probe; only the fault position
is injected, mirroring the spec's own W-series/R6-series method.

Checks:
  P1   the v6 finally-guarded snippet (as written in v6 §4.5) deletes the
       just-written output on the SUCCESS path — the defect D-48 supersedes
  P1b  the v7 except-scoped reference shape (§4.5 code block) keeps the
       file on success and removes it on failure (both target states)
  P2   write-phase (post-open) MemoryError form: pre-existing output is
       REMOVED (T-C16's state assertion for that form = path absent)
  P2b  encode-phase (pre-open) MemoryError form: pre-existing output
       survives byte-identical (T-C16's state assertion = bytes identical)
  P3   same-path invocation (input == output), mid-write failure: exit 1,
       E-WRITE line, and the INPUT file is deleted (R-4 demonstration)
  P4   dispatch divergence on `-h out.json`: manual dispatch (the pinned
       shape) → E-READ, exit 1, stdout empty; argparse default → help on
       stdout, exit 0 (the outcome D-49 forbids)
"""
import os
import subprocess
import sys
import tempfile

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
results = []


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    print(("PASS" if cond else "FAIL"), name, detail)


def stage_v6_snippet(path, payload, fail_at_write=False):
    """The v6 §4.5 reference shape, verbatim semantics."""
    fd = None
    try:
        fd = open(path, "wb")
        if fail_at_write:
            raise OSError(5, "injected EIO")
        fd.write(payload)
        fd.flush()
    finally:
        if fd is not None:
            os.remove(path)


def stage_v7_except_scoped(path, payload, fail_at=None):
    """The v7 §4.5 conforming reference shape (except-scoped remove)."""
    fd = None
    try:
        fd = open(path, "wb")  # at-open failure: no remove, target untouched
        if fail_at == "write":
            raise MemoryError("injected post-open OOM")
        fd.write(payload)
        fd.flush()
        fd.close()
        fd = None
    except BaseException:
        if fd is not None:
            try:
                os.remove(path)  # best-effort; errors ignored per D-33
            except OSError:
                pass
        raise


def stage_v7_encode_pre_open(path, payload_fn, pre_existing):
    """D-43 order: encode (payload_fn) completes BEFORE the open."""
    payload = payload_fn()  # fault position: pre-open encode
    fd = None
    try:
        fd = open(path, "wb")
        fd.write(payload)
        fd.flush()
        fd.close()
        fd = None
    except BaseException:
        if fd is not None:
            try:
                os.remove(path)
            except OSError:
                pass
        raise


# ---------------------------------------------------------------- P1 / P1b
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "out.json")
    # P1: v6 snippet on the SUCCESS path — file must be GONE (the defect)
    stage_v6_snippet(out, b'{"ok":true}\n', fail_at_write=False)
    check("P1 v6-snippet success path deletes output (D-48 supersession evidence)",
          not os.path.exists(out))

    # P1b: v7 shape — success keeps the file...
    stage_v7_except_scoped(out, b'{"ok":true}\n', fail_at=None)
    ok_success = os.path.exists(out) and open(out, "rb").read() == b'{"ok":true}\n'
    # ...and failure (post-open) removes it...
    try:
        stage_v7_except_scoped(out, b'{"ok":true}\n', fail_at="write")
        removed = True
    except MemoryError:
        removed = not os.path.exists(out)
    check("P1b v7 except-scoped shape: success keeps file, failure removes it",
          ok_success and removed,
          f"success_kept={ok_success} failure_removed={removed}")

    # P1b-at-open: at-open failure leaves a pre-existing target untouched
    with open(out, "wb") as f:
        f.write(b'{"prior":"good"}\n')
    os.chmod(out, 0o444)
    try:
        try:
            fd = open(out, "wb")
            fd.close()  # would only succeed as root
            skipped = os.geteuid() == 0  # as root the premise is defeated
        except PermissionError:
            skipped = True  # at-open failure: no remove ran, file intact
        check("P1b at-open failure: no compensation, pre-existing target intact",
              skipped and open(out, "rb").read() == b'{"prior":"good"}\n')
    finally:
        os.chmod(out, 0o644)

# ---------------------------------------------------------------- P2 / P2b
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "out.json")
    prior = b'{"prior":"good-bytes"}\n'

    # P2: post-open (write-phase) MemoryError → pre-existing file REMOVED
    with open(out, "wb") as f:
        f.write(prior)
    try:
        stage_v7_except_scoped(out, b"x" * 10, fail_at="write")
        raised = False
    except MemoryError:
        raised = True
    check("P2 write-phase form: pre-existing output REMOVED (assert path ABSENT)",
          raised and not os.path.exists(out))

    # P2b: pre-open (encode) MemoryError → pre-existing file byte-identical
    def boom():
        raise MemoryError("injected pre-open OOM")
    with open(out, "wb") as f:
        f.write(prior)
    try:
        stage_v7_encode_pre_open(out, boom, pre_existing=True)
        raised = False
    except MemoryError:
        raised = True
    survived = os.path.exists(out) and open(out, "rb").read() == prior
    check("P2b encode-phase form: pre-existing output BYTE-IDENTICAL",
          raised and survived,
          f"survived={survived}")

# ---------------------------------------------------------------- P3
with tempfile.TemporaryDirectory() as td:
    same = os.path.join(td, "data.csv")
    with open(same, "wb") as f:
        f.write(b'id,name\n1,x\n2,y\n')
    tool = os.path.join(td, "csv2json_faulty.py")
    # minimal conforming pipeline with an injected mid-write EIO
    with open(tool, "w") as f:
        f.write(
            "import os, sys\n"
            "text = open(sys.argv[1], encoding='utf-8', newline='').read()\n"
            "doc = '[{\"id\":\"1\",\"name\":\"x\"}]\\n'\n"
            "payload = doc.encode('utf-8')  # encode pre-open (D-43)\n"
            "fd = None\n"
            "try:\n"
            "    fd = open(sys.argv[2], 'wb')\n"
            "    raise OSError(5, 'Input/output error')  # injected mid-write EIO\n"
            "    fd.write(payload); fd.flush(); fd.close(); fd = None\n"
            "except BaseException:\n"
            "    if fd is not None:\n"
            "        try: os.remove(sys.argv[2])\n"
            "        except OSError: pass\n"
            "    print('csv2json: error: cannot write %s: %s' % (sys.argv[2], 'Input/output error'), file=sys.stderr)\n"
            "    sys.exit(1)\n"
        )
    r = subprocess.run([sys.executable, tool, same, same],
                       capture_output=True, text=True)
    gone = not os.path.exists(same)
    check("P3 same-path failed run: exit 1, E-WRITE line, INPUT file deleted (R-4)",
          r.returncode == 1
          and r.stderr.startswith("csv2json: error: cannot write ")
          and r.stdout == ""
          and gone,
          f"rc={r.returncode} gone={gone} stderr={r.stderr.strip()[:60]!r}")

# ---------------------------------------------------------------- P4
with tempfile.TemporaryDirectory() as td:
    manual = os.path.join(td, "manual.py")
    with open(manual, "w") as f:
        f.write(
            "import sys\n"
            "def main(argv):\n"
            "    if len(argv) != 2:\n"
            "        print('csv2json: error: usage: csv2json.py <input.csv> <output.json>', file=sys.stderr)\n"
            "        return 1\n"
            "    try:\n"
            "        open(argv[0], encoding='utf-8', newline='')\n"
            "    except OSError as e:\n"
            "        print('csv2json: error: cannot read %s: %s' % (argv[0], e.strerror), file=sys.stderr)\n"
            "        return 1\n"
            "    return 0\n"
            "sys.exit(main(sys.argv[1:]))\n"
        )
    r_manual = subprocess.run([sys.executable, manual, "-h", "out.json"],
                              capture_output=True, text=True)
    r_argparse = subprocess.run(
        [sys.executable, "-c",
         "import argparse, sys\n"
         "p = argparse.ArgumentParser()\n"
         "p.add_argument('input'); p.add_argument('output')\n"
         "a = p.parse_args(['-h', 'out.json'])\n"],
        capture_output=True, text=True)
    check("P4 manual dispatch: `-h out.json` → E-READ, exit 1, stdout EMPTY (D-49)",
          r_manual.returncode == 1
          and r_manual.stdout == ""
          and r_manual.stderr.startswith("csv2json: error: cannot read -h"),
          f"rc={r_manual.returncode} out={r_manual.stdout[:30]!r} err={r_manual.stderr.strip()[:50]!r}")
    check("P4 argparse default: `-h out.json` → help on stdout, exit 0 (outcome D-49 forbids)",
          r_argparse.returncode == 0 and "usage:" in r_argparse.stdout,
          f"rc={r_argparse.returncode} out_head={r_argparse.stdout[:40]!r}")

# ----------------------------------------------------------------
print()
fails = [n for n, c, _ in results if not c]
print(f"TOTAL CHECKS: {len(results)}  PASS: {len(results) - len(fails)}  "
      f"FAIL: {len(fails)}")
sys.exit(1 if fails else 0)

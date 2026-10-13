#!/usr/bin/env python3
"""33b-adv-c8-probes.py — adversarial-early cycle 8 live probes.

Target spec: spec/08-spec-v8.md (DRAFT, 2026-09-19).
Finds, by live execution, the counterexamples behind the findings of
appendix/33-adv-c8.md:

  P1/P2 (F-01)  KeyboardInterrupt (Ctrl-C) mid-write on the spec's OWN
                §4.5 reference shape: compensation runs, partial removed,
                KI re-raised  <->  an `except Exception` build (entitled by
                §7.1's "kill leaves whatever partial output existed at kill
                time" + §7.3's "KeyboardInterrupt ... NOT caught") leaves
                the partial file.  Two sanctioned readings, opposite
                durable state.
                P2 also measures the unhandled-KI exit code / traceback.
  P3   (F-02)   The sanctioned argparse build (§4.1/D-41/D-49) vs the
                §9 NFR-001 imports audit ("imports only csv, io, json,
                os, sys") — the audit flunks the permitted build; the REQ
                NFR-001 wording (stdlib-only) passes it.  Plus the lone
                `-h` (argc==1) divergence: manual dispatch -> E-USAGE
                exit 1; argparse default -> help on stdout, exit 0.
  P4   (F-04)   POSIX-legal newline-bearing input path interpolated
                verbatim into the E-READ template -> single stderr write
                wrapping across physical lines; §6.3's verbatim-slot
                enumeration does not list the <path> slots.
  P5   (F-03)   §11 line "Decision-coverage check: D-01..D-49 ..." vs the
                decision register's actual maximum id (D-50): stale
                enumeration, mechanically shown.

Run:  python3 appendix/33b-adv-c8-probes.py
"""

import io
import os
import re
import subprocess
import sys
import tempfile

PASS, FAIL = 0, 0


def record(pid, ok, note):
    global PASS, FAIL
    print(("PASS" if ok else "FAIL") + f" {pid}: {note}")
    if ok:
        PASS += 1
    else:
        FAIL += 1


# ---------------------------------------------------------------- P1 (F-01)
SPEC_REFERENCE_SHAPE = '''
import os

def write_output(path, document):
    payload = document.encode("utf-8")          # D-43 encode-before-open
    fd = None
    try:
        fd = open(path, "wb")
        fd.write(payload); fd.flush()
        fd.close(); fd = None
    except BaseException:                        # D-48 shape, verbatim scope
        if fd is not None:
            try: fd.close()                      # D-50 close before remove
            except OSError: pass
            fd = None
            try: os.remove(path)
            except OSError: pass
        raise
'''

EXCEPTION_VARIANT = SPEC_REFERENCE_SHAPE.replace(
    "except BaseException:", "except Exception:")


def _run_shape(src, tmpdir, path, exc_type):
    """Run `src`'s write_output in a child with a write that raises exc_type."""
    prog = src + f'''
import sys
class Fd:
    def __init__(self, real): self._r = real; self.closed = False
    def write(self, b): raise {exc_type.__name__}("injected mid-write")
    def flush(self): pass
    def close(self):
        self.closed = True
        return self._r.close()
_open = open
def open(p, m="r", **k):
    r = _open(p, m, **k)
    return Fd(r) if m == "wb" else r
sys.modules[__name__].open = open
write_output({path!r}, '[{{"a":"b"}}]\\n')
'''
    r = subprocess.run([sys.executable, "-c", prog],
                       capture_output=True, text=True, cwd=tmpdir)
    return r


def probe_p1(tmpdir):
    # prior good output exists; open truncates; write raises KeyboardInterrupt
    doc = "PRIOR-GOOD-OUTPUT-BYTES"
    for label, src, exc in [
            ("reference (except BaseException)", SPEC_REFERENCE_SHAPE,
             KeyboardInterrupt),
            ("variant (except Exception)", EXCEPTION_VARIANT,
             KeyboardInterrupt)]:
        path = os.path.join(tmpdir, f"out_{abs(hash(label)) % 9999}.json")
        with open(path, "w") as f:
            f.write(doc)
        r = _run_shape(src, tmpdir, path, exc)
        exists = os.path.exists(path)
        tb = "KeyboardInterrupt" in r.stderr and "Traceback" in r.stderr
        if label.startswith("reference"):
            # spec's own shape: partial REMOVED, KI re-raised (uncaught)
            ok = (not exists) and tb
            record("P1", ok,
                   f"{label}: Ctrl-C mid-write -> path exists={exists} "
                   f"(spec §7.1 claims 'leaves whatever partial output "
                   f"existed at kill time'), KI re-raised uncaught={tb}")
        else:
            # §7.1/§7.3-entitled build: partial SURVIVES
            ok = exists
            record("P1-control", ok,
                   f"{label}: same Ctrl-C -> partial file SURVIVES={exists} "
                   f"— opposite durable state from the same spec")


def probe_p2():
    r = subprocess.run(
        [sys.executable, "-c", "raise KeyboardInterrupt"],
        capture_output=True, text=True)
    tb = "Traceback" in r.stderr
    record("P2", r.returncode != 0 and tb,
           f"unhandled KeyboardInterrupt: exit={r.returncode}, "
           f"traceback on stderr={tb} — outside the two-valued 0/1 "
           f"catalog + QC-1 no-traceback wording (spec scopes KI out, "
           f"but §7.1's state claim is what F-01 charges)")


# ---------------------------------------------------------------- P3 (F-02)
def probe_p3(tmpdir):
    sanctioned = {"argparse", "csv", "io", "json", "os", "sys"}
    pinned = {"csv", "io", "json", "os", "sys"}          # §9 NFR-001 row
    stdlib = set(sys.stdlib_module_names) | pinned
    audit_pinned = sanctioned <= pinned
    audit_req = sanctioned <= stdlib
    record("P3a", (not audit_pinned) and audit_req,
           f"sanctioned argparse build: §9 pinned-set audit "
           f"{'PASS' if audit_pinned else 'FAIL'} (spec flunks what §4.1 "
           f"permits); REQ NFR-001 stdlib-only audit "
           f"{'PASS' if audit_req else 'FAIL'}")

    # lone `-h` (argc==1): manual dispatch vs argparse default
    manual = ("import sys\n"
              "argv = sys.argv[1:]\n"
              "if len(argv) != 2:\n"
              "    sys.stderr.write('csv2json: error: usage: csv2json.py "
              "<input.csv> <output.json>\\n'); sys.exit(1)\n")
    r1 = subprocess.run([sys.executable, "-c", manual, "-h"],
                        capture_output=True, text=True)
    manual_ok = (r1.returncode == 1 and r1.stdout == ""
                 and r1.stderr.startswith("csv2json: error: usage:"))
    ap = ("import argparse, sys\n"
          "p = argparse.ArgumentParser()\n"
          "p.add_argument('input'); p.add_argument('output')\n"
          "p.parse_args()\n")
    r2 = subprocess.run([sys.executable, "-c", ap, "-h"],
                        capture_output=True, text=True)
    argparse_help = (r2.returncode == 0 and r2.stdout != "")
    record("P3b", manual_ok and argparse_help,
           f"`-h` alone (argc==1): manual -> exit {r1.returncode}, stdout "
           f"{len(r1.stdout)}B, prefixed usage={manual_ok}; argparse default "
           f"-> exit {r2.returncode}, help on stdout={argparse_help} "
           f"(NFR-004 requires stdout empty; §4.1's disable clause says "
           f"'for this two-positional form' — length-1 argv under-scoped)")


# ---------------------------------------------------------------- P4 (F-04)
def probe_p4(tmpdir):
    name = "in\nbad.csv"                       # POSIX-legal newline in name
    path = os.path.join(tmpdir, name)
    with open(path, "w") as f:
        f.write("id\n1\n")
    msg = f"csv2json: error: cannot read {path}: No such file or directory"
    wrapped = "\n" in msg
    record("P4", wrapped and os.path.exists(path),
           "input path with an embedded \\n exists on POSIX; E-READ "
           f"template interpolates <in> verbatim -> message wraps "
           f"({msg.count(chr(10))} data-borne break(s)); §6.3's verbatim-"
           "slot list names <name>/<exception repr>/<strerror> but not the "
           "<path> slots every template interpolates")


# ---------------------------------------------------------------- P5 (F-03)
def probe_p5(root):
    reg = os.path.join(root, "appendix", "03-decision-register.md")
    spec = os.path.join(root, "spec", "08-spec-v8.md")
    with open(reg, encoding="utf-8") as f:
        ids = re.findall(r"^\| (D-\d+[b]?) ", f.read(), re.M)
    with open(spec, encoding="utf-8") as f:
        m = re.search(r"Decision-coverage check: D-\d+\.\.D-(\d+) are all",
                      f.read())
    spec_max = int(m.group(1)) if m else -1
    def num(d):
        return int(re.sub(r"\D", "", d))
    reg_max = max(num(d) for d in ids)
    record("P5", reg_max == 50 and spec_max == 49,
           f"§11 coverage sentence range: D-01..D-{spec_max}; register "
           f"maximum: D-{reg_max} ({len(ids)} DECIDED rows incl. D-11b); "
           f"§1 (line 23) already says D-01..D-50 — stale enumeration, "
           f"same class as SR3-F-02")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory() as tmp:
        probe_p1(tmp)
        probe_p2()
        probe_p3(tmp)
        probe_p4(tmp)
    probe_p5(root)
    print(f"\nTOTAL PASS: {PASS}  TOTAL FAIL: {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

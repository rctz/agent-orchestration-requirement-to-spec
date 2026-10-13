#!/usr/bin/env python3
"""adv-c16 probe 2 — caller-controlled path classes vs the error catalog.

Attack: §6.1 pins 'the output path is used exactly as given — no type check'
and §4.2 maps 'Any OSError' to E-READ. But open() raises NON-OSError classes
for some caller-controlled paths: an embedded NUL raises ValueError, and a
lone-surrogate path raises UnicodeEncodeError (locale-dependent). Those land
in the §7.3 residual net -> E-NET 'internal error: ...' — the catalog class
whose own trigger reads 'unexpected exception (no cataloged class fits)'.
Deterministic, user-triggerable, not an interruption window.

Also: empty-string paths, directory-as-input/output, and the §4.3 parse()
signature consistency pin.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(os.path.dirname(HERE), "spec", "16-spec-v16.md")
PY = sys.executable

FAILURES = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else " | " + str(detail)[:160]))
    if not ok:
        FAILURES.append(name)


# A spec-literal minimal shell: manual dispatch, typed read/decode stage,
# §7.3 net order (MemoryError, ToolError, Exception). Parse/serialize are
# stubbed to success so we exercise the path classes only.
SHELL = r'''
import sys, os

class ToolError(Exception):
    pass

class InputReadError(ToolError):
    pass

class OutputWriteError(ToolError):
    pass

def read_raw(path):
    try:
        with open(path, "rb") as f:      # <- the boundary under test
            return f.read()
    except OSError as e:
        raise InputReadError("csv2json: error: cannot read %s: %s" % (path, e.strerror))

def write_output(path, document):
    payload = document.encode("utf-8")   # D-43: before the open
    fd = None
    try:
        try:
            fd = open(path, "wb")        # <- the boundary under test
        except OSError as e:             # D-46: at-open failure, no compensation
            raise OutputWriteError(
                "csv2json: error: cannot write %s: %s" % (path, e.strerror))
        try:
            fd.write(payload); fd.flush()
            fd.close(); fd = None
        except OSError as e:             # post-open OSError -> E-WRITE after arm
            exc = OutputWriteError(
                "csv2json: error: cannot write %s: %s" % (path, e.strerror))
            if fd is not None:
                try: fd.close()
                except OSError: pass
                fd = None
                try: os.remove(path)
                except OSError: pass
            raise exc from e
    except OutputWriteError:
        raise
    except BaseException:                # non-OSError post-open: arm then re-raise
        if fd is not None:
            try: fd.close()
            except OSError: pass
            fd = None
            try: os.remove(path)
            except OSError: pass
        raise
    return

def main(argv):
    out = argv[1] if len(argv) > 1 else "/dev/null"
    try:
        if len(argv) != 2:
            sys.stderr.write("csv2json: error: usage: csv2json.py <input.csv> <output.json>\n")
            return 1
        data = read_raw(argv[0])
        text = data.decode("utf-8")
        write_output(out, '[{"ok":"1"}]\n')
        return 0
    except MemoryError:
        sys.stderr.write("csv2json: error: out of memory reading %s\n" % argv[0])
        return 1
    except ToolError as e:
        sys.stderr.write(str(e) + "\n")
        return 1
    except Exception as e:              # E-NET
        sys.stderr.write("csv2json: error: %s: internal error: %r\n" % (argv[0], e))
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def run_case(args, cwd):
    p = subprocess.run([PY, "-c", SHELL] + args, capture_output=True, text=True,
                       timeout=60, cwd=cwd)
    return p.returncode, (p.stdout + p.stderr).strip()


def probe_paths():
    d = tempfile.mkdtemp()
    good = os.path.join(d, "in.csv")
    with open(good, "wb") as f:
        f.write(b"id,name\n1,x\n")

    # NOTE: a NUL byte inside an argv element is UNREACHABLE on POSIX —
    # execve builds argv from NUL-terminated strings, so the OS rejects
    # such invocations before the tool starts. Verified as a probe control
    # (run_case_nul below expects the SPAWNER itself to fail); the tool
    # therefore never sees a NUL-bearing path from argv.
    cases = [
        ("empty-string INPUT", ["", os.path.join(d, "out.json")]),
        ("empty-string OUTPUT", [good, ""]),
        ("directory as INPUT", [d, os.path.join(d, "out.json")]),
        ("directory as OUTPUT", [good, d]),
        ("raw-0xff-byte OUTPUT path", [good, os.fsdecode(b"out\xff.json")]),
        ("raw-0xff-byte INPUT path", [os.fsdecode(b"in\xff.csv"), os.path.join(d, "o2.json")]),
        ("control (good run)", [good, os.path.join(d, "ok.json")]),
    ]
    print("P1 — caller-controlled path classes through the spec-literal shell")
    seen = {}
    for label, args in cases:
        rc, msg = run_case(args, d)
        cls = ("E-NET" if "internal error" in msg else
               "E-READ" if "cannot read" in msg else
               "E-WRITE" if "cannot write" in msg else
               "E-USAGE" if "usage" in msg else
               "success" if rc == 0 else "?")
        seen[label] = (rc, cls, msg)
        print("  %-26s rc=%d class=%-7s %s" % (label, rc, cls, msg[:100]))
    # spawner-level control proving NUL argv is rejected by the OS, not us
    try:
        subprocess.run([PY, "-c", SHELL, "in\x00.csv", "x"], capture_output=True,
                       timeout=30)
        nul_rejected = False
    except ValueError:
        nul_rejected = True
    check("P1z OS rejects NUL-bearing argv before exec (surface closed by execve)",
          nul_rejected)
    # what the catalog REQUIRES for each class:
    #  - OSError forms -> E-READ/E-WRITE. Non-OSError (ValueError, Unicode*)
    #    -> E-NET per the net. Record which class each case actually took.
    check("P1a directory-as-INPUT is an OSError (IsADirectory) -> E-READ",
          seen["directory as INPUT"][1] == "E-READ", seen["directory as INPUT"])
    check("P1b directory-as-OUTPUT is an at-open OSError -> E-WRITE",
          seen["directory as OUTPUT"][1] == "E-WRITE", seen["directory as OUTPUT"])
    check("P1c empty-string paths are OSErrors (ENOENT) -> catalog class",
          seen["empty-string INPUT"][1] == "E-READ" and seen["empty-string OUTPUT"][1] == "E-WRITE",
          (seen["empty-string INPUT"], seen["empty-string OUTPUT"]))
    check("P1d raw non-UTF-8 byte path round-trips (surrogateescape) — no crash",
          seen["raw-0xff-byte OUTPUT path"][1] == "success" and
          seen["raw-0xff-byte INPUT path"][1] == "E-READ",
          (seen["raw-0xff-byte OUTPUT path"], seen["raw-0xff-byte INPUT path"]))
    check("P1e control run succeeds silently (rc 0, no output)",
          seen["control (good run)"][0] == 0 and seen["control (good run)"][2] == "")
    # no stray files created by the failed runs (output side clean):
    leftovers = [f for f in os.listdir(d)
                 if f not in ("in.csv", "ok.json") and
                 not f.startswith("out\udcff") and f != "in\udcff.csv"]
    check("P1f failed runs leave no stray catalog-visible files",
          not leftovers, leftovers)
    return seen


def probe_signature():
    with open(SPEC, encoding="utf-8") as f:
        spec = f.read()
    import re
    s43 = re.search(r"^## 4\.3 .*?(?=^## 4\.4 )", spec, re.M | re.S)
    iface = re.search(r"- \*\*Interface\.\*\* `parse\(text: str\) -> "
                      r"list\[dict\[str, str\]\]`", s43.group(0)) if s43 else None
    prose = ("The input path name is passed for message construction "
             "(`parse(text, input_name)`)") if s43 else None
    check("P2a §4.3 Interface line declares parse(text) single-arg",
          iface is not None)
    check("P2b §4.3 prose passes (text, input_name) two-arg — signature "
          "inconsistency between the two declarations",
          prose in s43.group(0) if s43 else False,
          "interface says parse(text: str); prose says parse(text, input_name)")


def main():
    print("adv-c16 probe 2: path classes vs catalog / parse signature pin")
    print("python:", PY, sys.version.split()[0])
    probe_paths()
    print()
    probe_signature()
    print()
    print("TOTAL FAILURES: %d" % len(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

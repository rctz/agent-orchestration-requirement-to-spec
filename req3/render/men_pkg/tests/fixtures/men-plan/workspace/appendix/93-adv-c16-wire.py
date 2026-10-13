#!/usr/bin/env python3
"""adv-c16 probe 3 — argv-borne lone surrogates vs the 'default stderr
preserves UTF-8 verbatim' claims (spec/16-spec-v16.md §6.3 encoding-scope
paragraph, §12 'error catalog' glossary row).

Attack: <path> slots interpolate argv verbatim. On Linux, argv strings are
surrogateescape-decoded, so a filename containing a raw non-UTF-8 byte
reaches the tool as a str with a lone surrogate (e.g. 'in\\udcff.csv').
The E-READ message string then contains that surrogate. The spec's
encoding-scope paragraph anticipates NON-verbatim wire bytes only for
ENVIRONMENT-OVERRIDDEN encodings (PYTHONIOENCODING), and the glossary says
'default CPython stderr preserves UTF-8 verbatim'. But default sys.stderr
uses errors='backslashreplace' — a lone surrogate has NO UTF-8 form, so the
DEFAULT configuration transliterates it (\\udcff) with no override at all,
and no strict-handler raise either. The verbatim STRING contract holds; the
'under default settings the wire is verbatim' gloss is falsifiable for
argv-borne raw-byte paths.
"""
import os
import subprocess
import sys
import tempfile

PY = sys.executable
FAILURES = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else " | " + str(detail)[:200]))
    if not ok:
        FAILURES.append(name)


CHILD = r'''
import sys
# exactly one stderr write, message string built verbatim from argv
msg = "csv2json: error: cannot read %s: No such file or directory\n" % sys.argv[1]
sys.stderr.write(msg)
'''


def main():
    d = tempfile.mkdtemp()
    print("parent stderr encoding/errors:", sys.stderr.encoding, sys.stderr.errors)

    # 1) what does the DEFAULT child stderr put on the wire for the surrogate?
    env = dict(os.environ)            # untouched environment
    p = subprocess.run([PY, "-c", CHILD, "in\udcff.csv"],
                       capture_output=True, env=env, timeout=60)
    wire = p.stderr
    print("rc=%d wire=%r" % (p.returncode, wire))
    check("W1 default-config child emits the surrogate backslash-escaped "
          "(non-verbatim wire bytes, no override, no raise)",
          b"\\udcff" in wire and p.returncode == 0, wire)

    # 2) control: an encodable (Thai) path stays verbatim on the wire
    p2 = subprocess.run([PY, "-c", CHILD, "in\x0e01.csv"],
                        capture_output=True, env=env, timeout=60)
    # (Thai codepoint chosen via escape to keep this file ASCII-ish)
    p2 = subprocess.run([PY, "-c", CHILD, "ประเทศไทย.csv".encode("utf-8").decode("utf-8")],
                        capture_output=True, env=env, timeout=60)
    check("W2 control: Thai path reaches the wire as raw UTF-8 "
          "(glossary sentence TRUE for encodable messages)",
          "ประเทศไทย.csv".encode("utf-8") in p2.stderr, p2.stderr)

    # 3) the message STRING handed to the write is still verbatim (probe the
    #    child's own string directly)
    p3 = subprocess.run(
        [PY, "-c",
         'import sys\n'
         'm = "x %s y" % "in\\udcff.csv"\n'
         'print("SURROGATE-PRESENT" if "\\udcff" in m else "SANITIZED", '
         'file=sys.stdout)\n'],
        capture_output=True, env=env, timeout=60)
    check("W3 message STRING keeps the surrogate verbatim (string-level rule intact)",
          b"SURROGATE-PRESENT" in p3.stdout, p3.stdout)

    # 4) default errors handler really is backslashreplace for stderr
    p4 = subprocess.run(
        [PY, "-c", 'import sys; print(sys.stderr.errors)'],
        capture_output=True, env=env, timeout=60)
    check("W4 default sys.stderr.errors == backslashreplace",
          p4.stdout.strip() == b"backslashreplace", p4.stdout)

    print()
    print("TOTAL FAILURES: %d" % len(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

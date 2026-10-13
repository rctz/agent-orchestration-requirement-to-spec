#!/usr/bin/env python3
"""56b-adv-c12-probes — live probes for adversarial-early cycle 12 (spec/12-spec-v12.md).

F-01 (P1 candidate): the TWO normative E-UTF8 line-number sites in S4.2
  disagree, and both are broken for any input whose valid prefix contains a
  multi-byte UTF-8 character (BOM per REQ-012, Thai per the project's own
  domain):
    - operative formula (S4.2 "Behavior - strict decode"):
        line = line_of_offset(data[:e.start].decode("utf-8"), len(...))
      the second argument is LITERALLY ELIDED in the spec ("len(...)").
    - F-04 note (same section): "The N in the E-UTF8 message is
        line_of_offset(text, e.start)"
      e.start is a BYTE offset into `data`; line_of_offset indexes a str by
      CODE POINT (S4.2 reference shape). For a non-ASCII valid prefix,
      e.start > len(prefix_str) and the pinned reference loop walks off the
      end -> IndexError -> E-NET replaces the pinned E-UTF8 message.

F-02 (P2 candidate): S5.1's closing note ("every path into REPORTING leaves
  the output-side byte-state untouched EXCEPT the recorded at-open residue")
  is contradicted by the contracted post-open compensation: a flush-time
  OSError after a successful open REMOVES a pre-existing target (S-14/S-C8/
  S7.1) - live-demonstrated here by exec'ing the spec's OWN S4.5 reference
  shape with a faulted flush.
"""
import os
import re
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "..", "spec", "12-spec-v12.md")
PY = sys.executable

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else "  [" + detail + "]"))


# ---------------------------------------------------------------------------
# P1 - the two readings of the S4.2 E-UTF8 formula, applied to three inputs
# ---------------------------------------------------------------------------

DECODE_CHILD = r'''
import sys

def line_of_offset(text, offset):
    # S4.2 reference shape, transcribed exactly: '\r' collapses CRLF and
    # consumes 1-2 chars, '\n' consumes 1 char, and ANY break consumed
    # advances line by 1 ("if a break was consumed: line += 1").
    line = 1
    i = 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i+1:i+2] == "\n" else 1
            line += 1
        elif text[i] == "\n":
            i += 1
            line += 1
        else:
            i += 1
    return line

data = open(sys.argv[1], "rb").read()
try:
    data.decode("utf-8")
    print("DECODED-OK")
    raise SystemExit
except UnicodeDecodeError as e:
    prefix = data[:e.start].decode("utf-8")   # always valid (maximal prefix)
    # reading A (operative formula, charitable fill of the elided len(...)):
    #   len of the decoded prefix (the only len that yields the pinned line 4
    #   on the REQ-011 acceptance file)
    try:
        a = line_of_offset(prefix, len(prefix))
    except Exception as ex:
        a = "ERR:" + type(ex).__name__
    # reading B (F-04 note, literal): line_of_offset(text, e.start)
    try:
        b = line_of_offset(prefix, e.start)
    except Exception as ex:
        b = "ERR:" + type(ex).__name__
    print("e.start=%d prefix_chars=%d A=%r B=%r" % (e.start, len(prefix), a, b))
'''


def run_child(code, args=(), timeout=30):
    return subprocess.run([PY, "-c", code, *args], capture_output=True,
                          text=True, timeout=timeout)


def probe_eutf8():
    d = tempfile.mkdtemp()
    cases = [
        # (name, bytes, expected_N, reading_B_expected)
        ("ascii control (REQ-011 AC shape a,b\\rc,d\\rc\\r\\xff)",
         b"a,b\rc,d\rc\r\xff", 4, 4),
        ("BOM + header + bad byte (REQ-012's own feature paired with REQ-011)",
         b"\xef\xbb\xbf" + b"id,name\n1,\xff", 2, "ERR:IndexError"),
        ("Thai prefix + bad byte (the project's motivating domain)",
         "สวัสดี,ทำงาน\nชีวิต,".encode("utf-8") + b"\xff", 2, "ERR:IndexError"),
    ]
    for name, blob, want_n, want_b in cases:
        p = os.path.join(d, "in.csv")
        with open(p, "wb") as f:
            f.write(blob)
        r = run_child(DECODE_CHILD, (p,))
        out = r.stdout.strip()
        m = re.search(r"e\.start=(\d+) prefix_chars=(\d+) A=(\S+) B=(\S+)", out)
        check("P1 [%s] ran and parsed" % name, m is not None,
              "stdout=%r stderr=%r" % (out[:120], r.stderr[-120:]))
        if not m:
            continue
        e_start, pchars, a, b = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        check("P1 [%s] reading A (len(prefix)) == D-28 line %d" % (name, want_n),
              a == str(want_n), "A=%s" % a)
        check("P1 [%s] reading B (F-04 note, e.start as offset) == %r" % (name, want_b),
              b == str(want_b), "B=%s (e.start=%d > prefix_chars=%d)" % (b, e_start, pchars))
    # the elision itself, pinned textually
    spec = open(SPEC, encoding="utf-8").read()
    check("P1 operative formula carries the literal elided len(...)",
          'line_of_offset(data[:e.start].decode("utf-8"), len(...))' in spec,
          "elided-argument sentence not found verbatim")
    check("P1 F-04 note pins line_of_offset(text, e.start)",
          "line_of_offset(text, e.start)" in spec,
          "F-04 note formula not found verbatim")
    # coverage gap: no BOM+invalid or Thai+invalid case anywhere in the spec
    sec83 = spec[spec.find("# 8. Acceptance"):]
    has_nonascii_bad = ("BOM" in sec83 and "0xFF" in sec83 and
                        re.search(r"BOM[^\n]{0,80}(invalid|0x[Ff][Ff])", sec83) is not None)
    check("P1 acceptance layer has NO non-ASCII-prefix invalid-UTF-8 case",
          not has_nonascii_bad, "an unexpected case exists; re-classify")
    import shutil
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# P2 - S5.1's 'untouched' note vs the contracted post-open compensation
# ---------------------------------------------------------------------------
# Exec the spec's OWN S4.5 reference shape (extracted from the fence) with an
# instrumented open() whose flush raises ENOSPC after a successful open.

P2_CHILD = r'''
import os, sys

class FaultedFlush:
    def __init__(self, raw): self.raw = raw; self.closed = False
    def write(self, b): return len(b)
    def flush(self): raise OSError(28, "No space left on device")
    def close(self):
        if not self.closed:
            self.closed = True
            try: self.raw.close()
            except OSError: pass

_open_real = open
def _open(path, mode):
    return FaultedFlush(_open_real(path, mode))

SHAPE = {SHAPE}

def write_output(path, payload):
    ns = {"open": _open, "os": os, "path": path, "payload": payload}
    exec(SHAPE, ns)

def main(argv):
    out = argv[0]
    try:
        document = '[{{"a":"1"}}]\n'
        payload = document.encode("utf-8")
        write_output(out, payload)
    except OSError as e:
        sys.stderr.write("csv2json: error: cannot write %s: %s\n" % (out, e.strerror))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def probe_s51_contradiction():
    spec = open(SPEC, encoding="utf-8").read()
    i = spec.find("Conforming reference shape (e.g.):")
    if i < 0:
        check("P2 spec S4.5 reference shape found", False, "anchor missing")
        return
    j = spec.find("```", i)
    k = spec.find("```", j + 3)
    fence = textwrap.dedent(spec[j + 3:k])
    try:
        compile(fence, "<spec-shape>", "exec")
        compiles = True
    except SyntaxError as ex:
        compiles = False
        check("P2 spec S4.5 fence compiles as Python", False, "SyntaxError: %s" % ex)
    if not compiles:
        return
    check("P2 spec S4.5 fence compiles as Python", True)

    d = tempfile.mkdtemp()
    out = os.path.join(d, "prior.json")
    with open(out, "wb") as f:
        f.write(b'[{"prior":"good"}]\n' * 40)          # 440 bytes
    code = P2_CHILD.replace("{SHAPE}", repr(fence))
    r = subprocess.run([PY, "-c", code, out], capture_output=True, text=True,
                       timeout=30)
    exists_after = os.path.exists(out)
    check("P2 post-open flush ENOSPC (spec's own shape): E-WRITE line, exit 1",
          r.returncode == 1 and "cannot write" in r.stderr and
          "No space left on device" in r.stderr,
          "rc=%r stderr=%r" % (r.returncode, r.stderr.strip()[:100]))
    check("P2 pre-existing target REMOVED by the contracted compensation "
          "(S5.1 note's 'untouched' is false on this REPORTING path)",
          not exists_after, "target still exists")
    # and the S5.1 note textually claims the opposite
    m = re.search(r"every path into REPORTING leaves the\s*\n?output-side byte-state untouched EXCEPT the recorded at-open\s*\n?residue", spec)
    check("P2 S5.1 carries the absolute 'untouched EXCEPT at-open' claim",
          m is not None, "sentence not found (already fixed?)")
    import shutil
    shutil.rmtree(d, ignore_errors=True)


probe_eutf8()
probe_s51_contradiction()

print()
total = len(_results)
fails = _results.count(False)
print("TOTAL: %d checks, %d FAILURES" % (total, fails))
sys.exit(1 if fails else 0)

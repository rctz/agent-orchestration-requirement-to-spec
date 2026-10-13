#!/usr/bin/env python3
"""adv-c16 probe — the E-UTF8 prefix-decode formula vs the catalog (spec/16-spec-v16.md).

Hypothesis: §4.2 pins  line = line_of_offset(data[:e.start].decode("utf-8"), len(...))
and asserts "the valid-UTF-8 prefix is itself decoded". For inputs where the
first invalid byte is a CONTINUATION slot of a multi-byte sequence (lead already
consumed), e.start points INSIDE the sequence, so data[:e.start] ends with a
dangling lead and its decode raises a SECOND UnicodeDecodeError -> the residual
net fires E-NET ('internal error: ...') instead of the catalog's E-UTF8 line,
while §6.3 E-NET's own trigger ("no cataloged class fits") is false for an
invalid-UTF-8 input. Deterministic, input-controlled, not an interruption
window.

Parts:
  A  characterize e.start / reason / prefix-decodability per corpus
  B  E2E through a §4.2-LITERAL decode stage -> which catalog class fires
  C  text pins on spec/16-spec-v16.md (formula + assertion + E-NET trigger +
     T-C3 coverage gap)
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
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else " | " + detail))
    if not ok:
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# A — characterize e.start, reason, prefix decodability
# ---------------------------------------------------------------------------
CORPORA = [
    ("ctrl single-bad b'a\\xff'", b"a\xff"),
    ("P4 acceptance CR-only", b"a,b\rc,d\rc\r\xff"),
    ("bare continuation b'\\x80'", b"\x80"),
    ("2-byte lead+bad-cont b'a\\xe2\\x28'", b"a\xe2\x28"),
    ("4-byte lead+1ok+bad b'\\xf0\\x9f\\x28'", b"\xf0\x9f\x28"),
    ("mid-file, after CRLF rows", b"h1,h2\r\n\xef\xbf\x28"),
    ("thai-valid-then-broken", "h1,h2\nอา\r\n".encode("utf-8") + b"\xf0\x9f\x28"),
    ("truncated-3byte-at-eof b'a\\xe0\\xa0'", b"a\xe0\xa0"),
    ("truncated-4byte-at-eof b'\\xf0\\x9f\\x98'", b"\xf0\x9f\x98"),
    ("overlong b'\\xc0\\xaf'", b"\xc0\xaf"),
]

# ---------------------------------------------------------------------------
# B — a §4.2-literal decode stage, run as a child per corpus
# ---------------------------------------------------------------------------
DECODE_STAGE_LITERAL = r'''
import sys

def line_of_offset(text, offset):
    line = 1
    i = 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i+1:i+2] == "\n" else 1
            line += 1
        else:
            if text[i] == "\n":
                line += 1
            i += 1
    return line

def decode_utf8(data, path):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        # the §4.2 formula, verbatim in shape
        line = line_of_offset(data[:e.start].decode("utf-8"),
                              len(data[:e.start].decode("utf-8")))
        raise SystemExit("csv2json: error: %s line %d: byte 0x%02x is not valid UTF-8"
                         % (path, line, data[e.start]))

def main(argv):
    path = argv[0]
    with open(path, "rb") as f:
        data = f.read()
    try:
        decode_utf8(data, path)
    except SystemExit:
        raise
    except Exception as e:  # §7.3 residual net, E-NET form
        sys.stderr.write("csv2json: error: %s: internal error: %r\n" % (path, e))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def probe_a_b():
    d = tempfile.mkdtemp()
    print("A/B — per-corpus characterization (e.start, prefix decodes?, E2E class)")
    crash_class = []
    for label, raw in CORPORA:
        intro = subprocess.run(
            [PY, "-c",
             "try:\n b=%r.decode('utf-8')\n print('DECODES-OK')\n"
             "except UnicodeDecodeError as e:\n print(e.start, e.end, e.reason)" % raw],
            capture_output=True, text=True, timeout=60)
        sr = intro.stdout.strip()
        if sr == "DECODES-OK":
            print("  %-38s decodes clean (control)" % label)
            continue
        start = int(sr.split()[0])
        bad = raw[start] if start < len(raw) else None
        pref = subprocess.run(
            [PY, "-c",
             "try:\n %r[:%d].decode('utf-8')\n print('PREFIX-OK')\n"
             "except Exception as e2:\n print('PREFIX-RAISES', type(e2).__name__)" % (raw, start)],
            capture_output=True, text=True, timeout=60)
        pstate = pref.stdout.strip()
        pfn = os.path.join(d, "case.bin")
        with open(pfn, "wb") as f:
            f.write(raw)
        p = subprocess.run([PY, "-c", DECODE_STAGE_LITERAL, pfn],
                           capture_output=True, text=True, timeout=60)
        eutf8 = "is not valid UTF-8" in p.stdout + p.stderr
        enet = "internal error" in p.stdout + p.stderr
        line_field = ""
        for tok in (p.stdout + p.stderr).split():
            if tok == "line":
                pass
        print("  %-38s start=%d bad=%s reason=%r prefix=%s | rc=%d E-UTF8=%s E-NET=%s %s"
              % (label, start, ("0x%02x" % bad) if bad is not None else "EOF",
                 sr.split()[-1], pstate, p.returncode, eutf8, enet,
                 (p.stderr or p.stdout).strip()[:90]))
        if pstate == "PREFIX-RAISES":
            crash_class.append(label)
            check("B %s: prefix raises AND catalog class is E-NET (not E-UTF8)" % label,
                  enet and not eutf8,
                  "the §4.2-literal build reports the E-NET net message")
    # controls: the acceptance class must stay E-UTF8
    check("B control (single-bad + P4 corpus): prefix decodes, E-UTF8 fires",
          all("PREFIX-OK" in subprocess.run(
              [PY, "-c",
               "try:\n %r[:%d].decode('utf-8')\n print('PREFIX-OK')\nexcept Exception:\n print('PREFIX-RAISES')"
               % (raw, int(subprocess.run(
                   [PY, "-c",
                    "try:\n b=%r.decode('utf-8')\nexcept UnicodeDecodeError as e:\n print(e.start)" % raw],
                   capture_output=True, text=True, timeout=60).stdout.strip() or 0))],
              capture_output=True, text=True, timeout=60).stdout
              for raw in (b"a\xff", b"a,b\rc,d\rc\r\xff")),
          "acceptance-class prefixes are decodable")
    return crash_class


# ---------------------------------------------------------------------------
# C — text pins on the live spec
# ---------------------------------------------------------------------------
def probe_c():
    with open(SPEC, encoding="utf-8") as f:
        spec = f.read()
    import re
    s42 = re.search(r"^# 4\. .*?(?=^# 5\. )", spec, re.M | re.S)
    s62 = re.search(r"^## 6\.3 .*?(?=^## 6\.4 )", spec, re.M | re.S)
    s83 = re.search(r"^\| T-C3 .*?\|$", spec, re.M)
    check("C1 §4.2 pins the prefix-decode formula (data[:e.start].decode)",
          s42 and "data[:e.start].decode(\"utf-8\")" in s42.group(0))
    check("C2 §4.2 asserts 'the valid-UTF-8 prefix is itself decoded'",
          s42 and "valid-UTF-8 prefix is itself decoded" in s42.group(0))
    check("C3 §4.2 claims multi-byte sequences surface at their first invalid byte",
          s42 and "which `e.start` gives exactly" in s42.group(0))
    check("C4 §6.3 E-NET trigger says 'no cataloged class fits'",
          s62 and "no cataloged class fits" in s62.group(0))
    check("C5 T-C3's corpus set has no mid-sequence-continuation case",
          s83 is not None and "0x28" not in s83.group(0) and "\\xf0" not in s83.group(0),
          "T-C3 = %r" % (s83.group(0)[:120] if s83 else None))


def main():
    print("adv-c16 probe: E-UTF8 prefix-decode formula vs catalog")
    print("python:", PY, sys.version.split()[0])
    crash = probe_a_b()
    print()
    print("corpora whose prefix RAISES:", len(crash))
    for label in crash:
        print("  -", label)
    print()
    probe_c()
    print()
    print("TOTAL FAILURES: %d" % len(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

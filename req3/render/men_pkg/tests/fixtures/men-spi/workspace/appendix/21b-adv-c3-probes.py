#!/usr/bin/env python3
"""adv-c3 verification probes (adversarial-early cycle 3, spec/03-spec-v3.md).

Each probe targets a candidate finding; PASS/FAIL printed per check.
Python on this box: 3.11 (spec pinned probes on 3.13.5; both CPython).
"""
import csv, io, sys

FAILURES = []

def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(name)

# ---------------------------------------------------------------- P1: span/FSM re-verification on 3.11
def records_and_spans(text):
    f = io.StringIO(text, newline="")
    r = csv.reader(f)
    spans, start = [], 0
    while True:
        try:
            rec = next(r)
        except StopIteration:
            break
        end = f.tell()
        spans.append((rec, text[start:end]))
        start = end
    return spans

# R1: S-9b combined header defect — lenient fields of `id,"id` are ['id','id']
s = records_and_spans('id,"id')
check("R1a `id,\"id` single record", len(s) == 1, repr(s))
check("R1b lenient fields = ['id','id'] (duplicate exists)", s[0][0] == ["id", "id"], repr(s[0][0]))

# R2: E-DUP name containing a newline (quoted multi-line header fields)
hdr = '"a\nb","a\nb"\n1,2\n'
s = records_and_spans(hdr)
check("R2a header fields both 'a\\nb'", s[0][0] == ["a\nb", "a\nb"], repr(s[0][0]))
dup = s[0][0][1]
msg = f"csv2json: error: in.csv line 1: duplicate header name '{dup}'"
check("R2b catalog message embeds a raw newline (2 stderr lines)",
      "\n" in msg, repr(msg))

# R3: S-10b CRLF-interior M=3 arithmetic re-verified via D-28 counter
def line_of_offset(text, offset):
    line, i = 1, 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i + 1:i + 2] == "\n" else 1
            line += 1
        elif text[i] == "\n":
            i += 1
            line += 1
        else:
            i += 1
    return line

t = 'h1,h2\n"a\r\nb",c,"d\ne'
s = records_and_spans(t)
check("R3a two records (header + offending)", len(s) == 2, repr([r for r, _ in s]))
start_off = t.index(s[1][1])
N = line_of_offset(t, start_off)
# record-relative opening line of the third field's quote, D-28 basis
rec_text = s[1][1]
line, i, state, opening = 1, 0, "FIELD_START", None
while i < len(rec_text):
    c = rec_text[i]
    if c == '"':
        if state == "FIELD_START":
            state = "QUOTED"
            opening = line
        elif state == "QUOTED":
            state = "CLOSED"
        elif state == "CLOSED":
            state = "QUOTED"
        # UNQUOTED: data
    elif c == ",":
        if state != "QUOTED":
            state = "FIELD_START"
    elif c in "\r\n":
        if state != "QUOTED":
            state = "FIELD_START"
        if c == "\r" and rec_text[i + 1:i + 2] == "\n":
            i += 1
        line += 1
    i += 1
check("R3b FSM ends QUOTED", state == "QUOTED", state)
M = N + opening - 1
check("R3c N=2, M=3 (v3 pinned values)", (N, M) == (2, 3), f"N={N} M={M}")

# ------------------------------------------------- P2: write-stage order per §4.5 (open -> encode)
import os, tempfile
d = tempfile.mkdtemp()
out = os.path.join(d, "output.json")
with open(out, "wb") as f:                # pre-existing good output
    f.write(b'[{"id":"1","name":"x"}]\n')
try:
    fh = open(out, "wb")                  # §4.5: open FIRST (truncates now)
    try:
        raise MemoryError                 # document.encode() tips over here
    finally:
        fh.close()
except MemoryError:
    pass
left = open(out, "rb").read()
check("W1 spec-order S5: MemoryError at encode leaves 0-byte output",
      left == b"", repr(left))
check("W2 MemoryError is not an OSError (OSError-only try misses it)",
      not issubclass(MemoryError, OSError))

# ------------------------------------------------- boundary: 0xFF line citation
data = b"a,b\rc,d\rc\r\xff"
try:
    data.decode("utf-8")
    check("U1 strict decode raises", False)
except UnicodeDecodeError as e:
    prefix = data[:e.start].decode("utf-8")
    check("U1 E-UTF8 line = 4 (D-28, CR-only)", line_of_offset(prefix, len(prefix)) == 4,
          f"start={e.start} line={line_of_offset(prefix, len(prefix))}")

print()
print("TOTAL FAILURES:", len(FAILURES))
sys.exit(1 if FAILURES else 0)

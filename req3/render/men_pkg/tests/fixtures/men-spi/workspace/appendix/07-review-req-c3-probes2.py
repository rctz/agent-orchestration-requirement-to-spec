# Cycle-3 probes batch 2 — F-21/F-22/F-24 evidence + fold spot-checks.

import csv, io, json

def rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))

# F-21: trailing-blank discipline under CR terminators (REQ-009 5th bullet)
print("A", repr(rows("a,b\rc,d\r\r")))       # extra blank CR line after last record
print("B", repr(rows("a,b\rc,d\r")))          # exactly one terminator
print("C", repr(rows("h,k\n\"x\ry\",2\r")))    # REQ-014 third AC input

# F-21: physical-line counting divergence for the decode-error path
text = "a,b\rc,d\r\x85xx"  # not relevant: 0x85 raw is invalid UTF-8 byte here; use decode-level view instead
# The real case: CR-only file, invalid byte on 3rd physical line
raw = b"a,b\rc,d\rc\r\xff"
try:
    raw.decode("utf-8")
except UnicodeDecodeError as e:
    print("D decode error at byte", e.start)
print("E nl-only count before byte:", raw[:8].count(b"\n"))          # -> 0 => 'line 1'
print("F trio count before byte:", raw[:8].count(b"\r"))              # -> 2 => 'line 3'
print("G splitlines count:", len(raw[:8].decode("ascii").splitlines()))  # -> 3 lines => after 2 breaks
# splitlines() class pollution: VT/FF/NEL/LS/PS counted as breaks
print("H splitlines on controls:", len("a\x0bb\xffc\r".splitlines()))

# F-22: quote-parity vs dialect corners
print("I", repr(rows("\"a\"b")))            # quote closed then trailing chars
print("J", repr(rows("x\"y")))              # quote inside unquoted field
print("K", repr(rows("\"a\"\"")))           # escaped quote at EOF, unterminated

# F-24: unterminated non-first field: row start line vs field open line
r = csv.reader(io.StringIO('h1,h2\n"a\nb",c,"d\ne', newline=""))
print("L", [(r.line_num, row) for row in r])

# Fold spot-checks: F-20/D-26 separators, F-19 trailing newline form
print("M", json.dumps([{"id": "1"}], ensure_ascii=False))
print("N", json.dumps([{"id": "1"}], ensure_ascii=False, separators=(",", ":")))

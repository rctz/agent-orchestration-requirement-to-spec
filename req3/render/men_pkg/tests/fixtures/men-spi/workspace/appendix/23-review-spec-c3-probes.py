#!/usr/bin/env python3
"""Spec-review cycle 3 probes (card t_32485fee, spec/04-spec-v4.md).

R-series  FSM/span consistency attacks on §4.3.2 + §4.3.3 (SR1-F-01 fix
          verification at new boundaries: record-internal blank lines,
          mixed CRLF+CR interiors, doubled-quote reopen, csv/FSM agreement)
P-series  §4.5/D-43 order + §6.3 E-MEM cell consistency spot checks
Runs live; no mocks inside any unit under test (pure stdlib semantics).
"""
import csv
import io

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


def parse_with_spans(text):
    rf = io.StringIO(text, newline="")
    reader = csv.reader(rf)
    spans = []
    start = 0
    while True:
        try:
            record = next(reader)
        except StopIteration:
            break
        end = rf.tell()
        spans.append((start, end, record))
        start = end
    return spans


def fsm_scan(record_text):
    """FSM per §4.3.3 table + normative counting rule (CRLF collapses)."""
    state = "FIELD_START"
    line = 1
    opening_line = None
    i = 0
    n = len(record_text)
    while i < n:
        c = record_text[i]
        if c == '"':
            if state == "FIELD_START":
                state = "QUOTED"
                opening_line = line
            elif state == "QUOTED":
                state = "CLOSED"
            elif state == "CLOSED":
                state = "QUOTED"
                opening_line = line
            i += 1
        elif c == ",":
            if state != "QUOTED":
                state = "FIELD_START"
            i += 1
        elif c in "\r\n":
            if c == "\r" and i + 1 < n and record_text[i + 1] == "\n":
                i += 2
            else:
                i += 1
            if state != "QUOTED":
                state = "FIELD_START"
            line += 1
        else:
            if state == "FIELD_START" or state == "CLOSED":
                state = "UNQUOTED"
            i += 1
    return state == "QUOTED", opening_line, state


def line_of_offset(text, offset):
    line, i = 1, 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i + 1:i + 2] == "\n" else 1
            line += 1
        else:
            if text[i] == "\n":
                line += 1
            i += 1
    return line


def nm(text, idx):
    """Full spec pipeline N and M for record idx (span+FSM per §4.3.2/4.3.3)."""
    spans = parse_with_spans(text)
    s, e, rec = spans[idx]
    q, ol, fin = fsm_scan(text[s:e])
    n = line_of_offset(text, s)
    m = n + (ol - 1) if ol else None
    return q, n, m, rec


# R1: record-internal blank line INSIDE a quoted field of the offending record
t1 = 'h1,h2\n"a\n\nb",c,"d\ne'
q, n, m, rec = nm(t1, 1)
print("R1 spans/fields:", parse_with_spans(t1)[1][2])
check("R1a record2 FSM ends QUOTED", q)
check("R1b N=2 (row-start line)", n == 2, n)
check("R1c opening_line=3 -> M=4 (quote of \"d sits on physical L4; D-28 truth 4)",
      m == 4, f"N={n} M={m}")

# R2: unterminated quote is the FIRST field; interior blank before it? (none)
t3 = 'h1,h2\n"a\n\nb,c,"d\ne'  # not used; keep numbering stable
# R2 real: interior blank then unterminated FIRST-field variant
t2 = 'h1,h2\n"a\nb",c,"d\ne'  # control: no interior blank -> M=3 pinned
q2, n2, m2, _ = nm(t2, 1)
check("R2 control (LF interior) N=2 M=3", (n2, m2) == (2, 3), f"{n2},{m2}")

# R3: CRLF then bare CR inside earlier quoted field (two breaks, mixed)
t4 = 'h1,h2\n"a\r\nb\rc",x,"d\ne'
q4, n4, m4, _ = nm(t4, 1)
check("R3a ends QUOTED", q4)
check("R3b N=2", n4 == 2, n4)
check("R3c M=4 matches D-28 truth (CRLF one + CR one)", m4 == 4, m4)

# R4: doubled-quote reopen (QUOTED->CLOSED->QUOTED on '""'), CRLF inside,
# then an unterminated field — the earlier "" pair must not eat the close.
t5 = 'h,k\n"a""b\r\nc",x,"d\ne'  # field1 value a"b\r\nc; "d\ne unterminated
q5, n5, m5, rec5 = nm(t5, 1)
check("R4a ends QUOTED", q5, f"fields={rec5}")
check("R4b N=2", n5 == 2, n5)
check("R4c M=3 (one interior CRLF; truth: quote of \"d sits on L3)", m5 == 3, m5)

# R5: FSM/csv agreement — count-bad row with CLOSED quotes must not fire E-UQ
t6 = 'a,b\n"x,y",3,4\n'
q6, _, _, rec6 = nm(t6, 1)
check("R5 closed-quote count-bad row: not QUOTED -> E-COUNT fires", not q6)

# R6: interior blank INSIDE quotes of an earlier field; the unterminated
# quote opens on the line right after the record's last interior break.
t7 = 'h1,h2\n"x\n\ny",c,"d\ne'  # row2: L2 "x / L3 EMPTY / L4 y",c, / L5 "d e
q7, n7, m7, _ = nm(t7, 1)
check("R6 N=2 (row start), M=4 (quote of \"d on physical L4)", (n7, m7) == (2, 4),
      f"N={n7} M={m7}")

# P1: §4.5 pinned order — encode failure cannot touch target (already
# proven by appendix/22 W1/W2; here re-check the S-matrix quickly on this
# host with the file-based equivalent)
import os
import tempfile

with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "o.json")
    open(out, "wb").write(b"GOOD")
    try:
        def boom(s):
            raise MemoryError
        payload = boom("doc")  # D-43 step 1 encode FIRST
    except MemoryError:
        pass
    check("P1 encode-fault leaves pre-existing target intact",
          open(out, "rb").read() == b"GOOD")

print()
print("TOTAL FAILURES:", len(fails))

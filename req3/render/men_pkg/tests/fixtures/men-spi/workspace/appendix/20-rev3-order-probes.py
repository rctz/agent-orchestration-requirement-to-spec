#!/usr/bin/env python3
"""Revision-cycle-3 probes (card t_cf49c3e9) — verify spec/03-spec-v3.md pins.

R1  CRLF-interior unterminated quote: revised record-relative FSM gives
    M = D-28 truth = 3 for 'h1,h2\\n"a\\r\\nb",c,"d\\ne' (N=2).
R2  Bare-CR interior form: same one-advance rule -> M=3.
R3  Header check order (D-15 slots (5)<(6)): 'id,"id' -> E-DUP 'id';
    '"id,name' (no duplicate) -> E-UQ at line 1.
R4  Byte counts: S-1 output is 46 bytes; '[]\\n' is 3 bytes.
R5  Success path with interior CRLF is byte-exact (D-24): converts with
    \\r\\n preserved in the JSON escape.
R6  FSM regressions: doubled quotes / post-close junk / quote-in-unquoted
    still data (no false positive) under the revised counter.
"""
import io
import csv
import json
import sys

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


def line_of_offset(text, off):
    """D-28 counter (spec §4.2): CRLF one break, bare CR one, LF one."""
    line, i, n = 1, 0, len(text)
    while i < off:
        c = text[i]
        if c == "\r":
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            line += 1
        elif c == "\n":
            i += 1
            line += 1
        else:
            i += 1
    return line


def scan_row(rec_text):
    """Revised per-record FSM (spec §4.3.3 v3): CRLF/CR/LF each ONE advance.

    Returns (unterminated?, record-relative opening line, counter at end).
    """
    line, i, n = 1, 0, len(rec_text)
    FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3
    state, open_line = FIELD_START, 0
    while i < n:
        c = rec_text[i]
        if c == "\r" and i + 1 < n and rec_text[i + 1] == "\n":
            if state in (UNQUOTED, CLOSED):
                state = FIELD_START
            i += 2
            line += 1          # CRLF = ONE advance, in every state
            continue
        if c == "\r" or c == "\n":
            if state in (UNQUOTED, CLOSED):
                state = FIELD_START
            elif state == QUOTED:
                pass           # data inside quotes
            i += 1
            line += 1          # bare CR / LF = ONE advance
            continue
        if state == FIELD_START:
            if c == '"':
                state, open_line = QUOTED, line
            elif c == ",":
                pass
            else:
                state = UNQUOTED
            i += 1
        elif state == UNQUOTED:
            if c == ",":
                state = FIELD_START
            i += 1
        elif state == QUOTED:
            if c == '"':
                state = CLOSED
            i += 1
        else:
            if c == '"':
                state = QUOTED
            elif c == ",":
                state = FIELD_START
            else:
                state = UNQUOTED
            i += 1
    return (state == QUOTED, open_line, line)


def spans_of(text):
    f = io.StringIO(text, newline="")
    reader = csv.reader(f)
    spans = []
    start = 0 if f.tell() == 0 else f.tell()
    start = 0
    while True:
        try:
            rec = next(reader)
        except StopIteration:
            break
        end = f.tell()
        spans.append((rec, start, end, text[start:end]))
        start = end
    return spans


def convert(text):
    """Designed pipeline (spec §4.3.2 v3 order): header rules first."""
    if text.startswith("﻿"):
        text = text[1:]
    f = io.StringIO(text, newline="")
    reader = csv.reader(f)
    header, rows, start, line = None, [], 0, 1
    while True:
        try:
            rec = next(reader)
        except StopIteration:
            break
        end = f.tell()
        rec_text = text[start:end]
        row_start_line = line
        if header is None:
            if len(rec) == 0:
                return "err", "E-HEADER0 line 1"
            seen = set()
            for name in rec:
                if name in seen:
                    return "err", f"E-DUP '{name}' line 1"
                seen.add(name)
        unterm, open_rel, _ = scan_row(rec_text)
        if unterm:
            M = row_start_line + open_rel - 1
            return "err", f"E-UQ line {row_start_line} opened {M}"
        if header is None:
            header = rec
        else:
            if len(rec) != len(header):
                return "err", f"E-COUNT line {row_start_line}"
            rows.append(dict(zip(header, rec)))
        line += line_of_offset(text, end) - line_of_offset(text, start)
        start = end
    if header is None:
        return "err", "E-EMPTY"
    return "ok", rows


# --- R1: CRLF interior -----------------------------------------------------

text = 'h1,h2\n"a\r\nb",c,"d\ne'
spans = spans_of(text)
check("R1 two records", len(spans) == 2, str(len(spans)))
_, s2, e2, rec2 = spans[1]
N = line_of_offset(text, s2)
check("R1 N is 2", N == 2, N)
unterm, open_rel, _ = scan_row(rec2)
check("R1 revised FSM flags unterminated", unterm)
check("R1 opening record-relative line is 2", open_rel == 2, open_rel)
M = N + open_rel - 1
check("R1 M == 3 (D-28 truth)", M == 3, M)
abs_quote = s2 + rec2.index(',"d') + 2
check("R1 M == line_of_offset(opening quote)", M == line_of_offset(text, abs_quote),
      f"{M} vs {line_of_offset(text, abs_quote)}")
k, v = convert(text)
check("R1 pipeline reports line 2 opened at 3",
      (k, v) == ("err", "E-UQ line 2 opened 3"), (k, v))

# --- R2: bare-CR interior --------------------------------------------------

text2 = 'h1,h2\n"a\rb",c,"d\ne'
spans2 = spans_of(text2)
_, s, e, rec2b = spans2[1]
unterm, open_rel, _ = scan_row(rec2b)
check("R2 CR-interior unterminated", unterm)
check("R2 opening record-relative line is 2", open_rel == 2, open_rel)
check("R2 M == 3", spans2 and line_of_offset(text2, s) + open_rel - 1 == 3)

# --- R3: header order ------------------------------------------------------

k, v = convert('id,"id')
check("R3 combined defect -> E-DUP (not E-UQ)", (k, v) == ("err", "E-DUP 'id' line 1"), (k, v))
k, v = convert('"id,name')
check("R3 header quote, no duplicate -> E-UQ line 1 opened 1",
      (k, v) == ("err", "E-UQ line 1 opened 1"), (k, v))
k, v = convert('id,name\n1,x\n')
check("R3 clean header unchanged", k == "ok", (k, v))

# --- R4: byte counts -------------------------------------------------------

out = json.dumps([{"id": "1", "name": "x"}, {"id": "2", "name": "y"}],
                 ensure_ascii=False, separators=(",", ":")) + "\n"
check("R4 S-1 output is 46 bytes", len(out.encode()) == 46, len(out.encode()))
check("R4 '[]\\n' is 3 bytes", len("[]\n".encode()) == 3, len("[]\n".encode()))

# --- R5: success path with interior CRLF (D-24 byte exactness) -------------

k, v = convert('id,name\n"a\r\nb",c\n')
expect = [{"id": "a\r\nb", "name": "c"}]
check("R5 CRLF field converts", (k, v) == ("ok", expect), (k, v))
if k == "ok":
    doc = json.dumps(v, ensure_ascii=False, separators=(",", ":")) + "\n"
    check("R5 \\r\\n preserved in escapes", '\\r\\n' in doc, doc)

# --- R6: FSM regressions ---------------------------------------------------

for name, rowtext, want in [
    ("R6 doubled quotes data", '"a""b",c', False),
    ("R6 post-close junk data", '"a"b,c', False),
    ("R6 quote-in-unquoted data", '5" ruler,2', False),
    ("R6 unterminated still caught", '"abc', True),
]:
    u, rel, _ = scan_row(rowtext)
    check(name, u == want, f"unterm={u}")

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

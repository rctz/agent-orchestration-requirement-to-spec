#!/usr/bin/env python3
"""Spec-review cycle 1 counterexample probes, part 2 (card t_34a2ef7e).

Corrected R1 (slice offset + tuple unpacking fixed) plus extra checks:
  R1b   M for 'h1,h2\\n"a\\r\\nb",c,"d\\ne' — D-28 truth vs P8 FSM vs P3 FSM.
  R7    csv.reader('"a"b') field value (spec §4.3.3 prose claims data
        field "ab"-with-quote).
  R8    len("[]\\n") bytes (spec §6.2.6 claims 2 bytes).
  R9    dialect check: record spans for the R1b input (P1-style).
"""
import io
import csv
import sys

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


def line_of_offset(text, off):
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


# --- R1b: the CRLF-inside-quoted-field M case ------------------------------

text = 'h1,h2\n"a\r\nb",c,"d\ne'

# record spans, P1 style
f = io.StringIO(text, newline="")
reader = csv.reader(f)
spans = []
start = f.tell()
while True:
    try:
        rec = next(reader)
    except StopIteration:
        break
    end = f.tell()
    spans.append((rec, start, end, text[start:end]))
    start = end
print("R1b spans:", [(r, s, e) for r, s, e, _ in spans])
check("R1b two records", len(spans) == 2)
check("R1b record2 lenient fields", spans[1][0] == ["a\r\nb", "c", "d\ne"], spans[1][0])

row2_text = spans[1][3]
N = line_of_offset(text, spans[1][1])
idx = row2_text.index(',"d') + 1  # opening quote of the unterminated field
# absolute offset of that quote:
abs_idx = spans[1][1] + idx
M_truth = line_of_offset(text, abs_idx)
print(f"R1b: N = {N}; D-28 physical line of opening quote (M) = {M_truth}")
check("R1b N is 2", N == 2, N)
check("R1b D-28 M is 3", M_truth == 3, M_truth)


# P8's scan_unterminated (verbatim from appendix/13)
def scan_unterminated(rec_text):
    line, i, n = 1, 0, len(rec_text)
    FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3
    state, open_line = FIELD_START, 0
    while i < n:
        c = rec_text[i]
        if c == "\r" and i + 1 < n and rec_text[i + 1] == "\n" and state != QUOTED:
            state = FIELD_START
            i += 2
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
            elif c == "\n" or c == "\r":
                line += 1
            i += 1
        else:
            if c == '"':
                state = QUOTED
            elif c == ",":
                state = FIELD_START
            else:
                state = UNQUOTED
            i += 1
    return open_line if state == QUOTED else 0


# P3's scan_row (verbatim from appendix/13)
def scan_row(row_text):
    line, i, n = 1, 0, len(row_text)
    FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3
    state = FIELD_START
    open_line = 0
    while i < n:
        c = row_text[i]
        if c == "\r" and i + 1 < n and row_text[i + 1] == "\n":
            if state in (UNQUOTED, CLOSED):
                state = FIELD_START
            i += 2
            line += 1
            continue
        if c == "\r" or c == "\n":
            if state in (UNQUOTED, CLOSED):
                state = FIELD_START
            i += 1
            line += 1
            continue
        if state == FIELD_START:
            if c == '"':
                state = QUOTED
                open_line = line
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
    return (state == QUOTED, open_line if state == QUOTED else 0)


rel8 = scan_unterminated(row2_text)
unterm3, rel3 = scan_row(row2_text)
M_p8 = N + rel8 - 1
M_p3 = N + rel3 - 1
print(f"R1b: P8 FSM rel={rel8} -> M={M_p8}; P3 FSM rel={rel3} -> M={M_p3}")
print("R1b: spec §4.3.3 TABLE applied per-character (QUOTED advances on each of \\r,\\n):")
line, i, n = 1, 0, len(row2_text)
while i < n:
    c = row_text[i]
    if c in "\r\n":
        line += 1  # table: 'advance the record-relative line counter' per char
    i += 1
print(f"      per-character count at the quote (idx {idx}) =",
      1 + sum(1 for ch in row2_text[:idx] if ch in "\r\n"))
check("R1b P8 FSM M != D-28 truth (divergence confirmed)", M_p8 != M_truth,
      f"P8 M={M_p8} truth={M_truth}")
check("R1b P3 FSM M == D-28 truth", M_p3 == M_truth, f"P3 M={M_p3} truth={M_truth}")

# --- R7: '"a"b' dialect value ----------------------------------------------

val = next(csv.reader(io.StringIO('"a"b', newline="")))
print("R7: csv.reader('\"a\"b') ->", val)
check("R7 post-close junk value", val == ["ab"], val)

# --- R8: header-only output bytes ------------------------------------------

print("R8: len(b'[]\\n') =", len("[]\n".encode()), "(spec §6.2.6 claims 2 bytes)")
check("R8 []\\n is 3 bytes", len("[]\n".encode()) == 3)

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

#!/usr/bin/env python3
"""Spec-review cycle 1 counterexample probes (card t_34a2ef7e).

Discriminating checks beyond the designer's own appendix/13 probes:

  R1  M-numbering when a CRLF occurs inside a quoted field of the
      offending record (D-28 ground truth vs the P8 FSM vs the P3 FSM).
  R2  S-1 byte-count claim ("45 bytes") in spec §5.3 S-1.
  R3  Claim-keyword sweep outside §10 of the live spec.
  R4  decode_utf8 line-number formula on a truncated multi-byte prefix
      (spec §4.2: line_of_offset(data[:e.start].decode(...), len(...))).
  R5  Duplicate-header vs unterminated-quote corner: `"id,id`
      (spec §4.3.2 check order: quote check BEFORE header rules).
  R6  0-field header with an unterminated quote: `"a` (single quote,
      file ends) — E-UQ expected per check-1-first order.
"""
import io
import csv
import json
import re
import sys

WS = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# ---- R1: M numbering, CRLF inside quoted field --------------------------

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


text = 'h1,h2\n"a\r\nb",c,"d\ne'  # row 2 starts line 2; 3rd field opens after a CRLF
idx = text.index(',"d') + 1
d28_M = line_of_offset(text, idx)
print("R1: D-28 physical line of opening quote:", d28_M)


def scan_unterminated(rec_text):  # P8 FSM, verbatim from appendix/13
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


def scan_row(row_text):  # P3 FSM, verbatim from appendix/13
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


rec = text[7:]  # record 2 span
N = 2
rel8 = scan_unterminated(rec)
rel3, _ = scan_row(rec)
print("R1: P8-FSM rel open line:", rel8, "-> M =", N + rel8 - 1, "(REQ-013 expects 3)")
print("R1: P3-FSM rel open line:", rel3, "-> M =", N + rel3 - 1, "(REQ-013 expects 3)")
check("R1 P8 FSM matches D-28 M", N + rel8 - 1 == d28_M, f"P8 M={N+rel8-1} D-28 M={d28_M}")
check("R1 P3 FSM matches D-28 M", N + rel3 - 1 == d28_M, f"P3 M={N+rel3-1} D-28 M={d28_M}")

# ---- R2: S-1 byte count ---------------------------------------------------

out = json.dumps(
    [{"id": "1", "name": "x"}, {"id": "2", "name": "y"}],
    ensure_ascii=False,
    separators=(",", ":"),
) + "\n"
print("R2: S-1 output:", repr(out), "=", len(out.encode()), "bytes (spec claims 45)")
check("R2 S-1 byte count is 45", len(out.encode()) == 45, len(out.encode()))

# ---- R3: claim keywords outside §10 ---------------------------------------

spec = open(f"{WS}/spec/02-spec-v2.md", encoding="utf-8").read()
qc_start = spec.index("### QC-1")
sec11 = spec.index("# 11.")
outside = spec[:qc_start] + spec[sec11:]
bad = [
    r"\bidempoten", r"\batomicity\b", r"\batomic\b", r"\bdurab",
    r"\bconcurrency-safe\b", r"\bthread-safe\b", r"\brace-free\b",
    r"\bsecure\b", r"\brecoverable\b", r"\bbackward-compatible\b",
    r"\bperformant\b", r"\bguarantee", r"under concurrent",
]
hits = []
for pat in bad:
    for m in re.finditer(pat, outside, re.I):
        hits.append((m.group(0), outside[: m.start()].count("\n") + 1))
print("R3: claim-keyword hits outside QC:", hits)

# ---- R4: decode line-number formula on truncated multi-byte prefix --------

data = b"h,k\n\xe0\xb8"  # Thai lead bytes at EOF, incomplete sequence
try:
    data.decode("utf-8")
    check("R4 raises", False, "no raise")
except UnicodeDecodeError as e:
    prefix = data[: e.start].decode("utf-8")
    got = line_of_offset(prefix, len(prefix))
    print("R4: e.start =", e.start, "prefix =", repr(prefix), "-> line", got)
    check("R4 formula yields line 2", got == 2, got)

# ---- R5/R6: check-order corners through the designed P8 pipeline ----------


def convert(text):
    """P8's designed pipeline, verbatim logic (input name fixed)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    f = io.StringIO(text, newline="")
    reader = csv.reader(f)
    header = None
    rows = []
    start = 0
    while True:
        try:
            rec = next(reader)
        except StopIteration:
            break
        end = f.tell()
        row_start_line = line_of_offset(text, start)
        rec_text = text[start:end]
        q = scan_unterminated(rec_text)
        if q:
            m_line = row_start_line + q - 1
            return "err", f"input.csv line {row_start_line}: unterminated quoted field (opened at line {m_line})"
        if header is None:
            if len(rec) == 0:
                return "err", f"input.csv line {row_start_line}: invalid header row (found 0 fields)"
            header = rec
            seen = set()
            for name in header:
                if name in seen:
                    return "err", f"input.csv line {row_start_line}: duplicate header name '{name}'"
                seen.add(name)
        else:
            if len(rec) != len(header):
                return "err", f"input.csv line {row_start_line}: expected {len(header)} fields, found {len(rec)}"
            rows.append(dict(zip(header, rec)))
        start = end
    if header is None:
        return "err", "input.csv: file is empty (no header row)"
    return "ok", (json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


k, v = convert('"id,id')
print("R5: '\"id,id' ->", k, repr(v), "(spec table: E-UQ line 1; alt order: E-DUP 'id,name')")
k, v = convert('"a')
print("R6: '\"a' ->", k, repr(v), "(spec table: E-UQ line 1)")

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

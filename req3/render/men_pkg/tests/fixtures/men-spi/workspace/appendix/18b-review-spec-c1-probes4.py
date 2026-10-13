#!/usr/bin/env python3
"""Spec-review cycle 1, part 4: header duplicate-vs-quote ordering corner."""
import io
import csv
import sys

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# lenient parse of the combo input
val = list(csv.reader(io.StringIO('id,"id', newline="")))
print("dialect parse of 'id,\"id':", val)
check("combo parses as duplicate pair", val == [["id", "id"]], val)

val2 = list(csv.reader(io.StringIO('"a"b', newline="")))
print("dialect parse of '\"a\"b':", val2)

# The spec's designed pipeline (P8 order: quote check BEFORE header rules)
def scan_unterminated(rec_text):  # P8 verbatim
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


def convert(text):  # P8 verbatim logic, messages minus prefix
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
        rec_text = text[start:end]
        q = scan_unterminated(rec_text)
        if q:
            return "err", f"E-UQ line 1 (opened at line 1)"
        if header is None:
            if len(rec) == 0:
                return "err", "E-HEADER0"
            header = rec
            seen = set()
            for name in header:
                if name in seen:
                    return "err", f"E-DUP '{name}'"
                seen.add(name)
        else:
            if len(rec) != len(header):
                return "err", "E-COUNT"
            rows.append(dict(zip(header, rec)))
        start = end
    if header is None:
        return "err", "E-EMPTY"
    return "ok", rows


k, v = convert('id,"id')
print("spec-designed behavior for 'id,\"id':", k, "-", v)
check("spec order yields E-UQ (not E-DUP)", (k, v) == ("err", "E-UQ line 1 (opened at line 1)"), (k, v))

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

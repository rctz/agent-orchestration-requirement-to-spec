#!/usr/bin/env python3
"""Spec-design probes for spec/01-spec-v1.md (card t_e56db974).

Verifies, live on this interpreter, the stdlib mechanisms the spec pins:

  P1  csv.reader over a position-tracked io.StringIO(text, newline=""):
      f.tell() after each record equals the record's end offset (no
      read-ahead) -> per-record text slices are exact.
  P2  D-28 offset->line arithmetic: \n, \r\n (ONE break), bare \r break
      lines; VT/FF/NEL/U+2028/U+2029 are data (never break).
  P3  Unterminated-quote scanner FSM: dialect-exact (quote opens only at
      field start; "" escape; " after a closed section is data) on
      REQ-013's acceptance shapes, including the N/M line numbers.
  P4  UnicodeDecodeError.start byte offset -> D-28 line (CR-only case
      must cite line 4 per REQ-011).
  P5  csv.field_size_limit degrade loop terminates (D-27).
  P6  Binary-mode output write ends with exactly b"]\n" (D-35) and the
      escape contract short forms (D-14/D-20) hold on this interpreter.
  P7  csv.reader.line_num agrees with the D-28 line counter at end of
      iteration (D-28's "same basis" claim).
"""
import csv
import io
import json
import sys

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# --- P1: position-tracked row slices -------------------------------------


def row_slices(text):
    f = io.StringIO(text, newline="")
    reader = csv.reader(f)
    out = []
    start = f.tell()
    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        end = f.tell()
        out.append((row, text[start:end]))
        start = end
    return out


s = 'h1,h2\n"a\nb",c,"d\ne'
rows = row_slices(s)
check("P1 count", len(rows) == 2, rows)
check("P1 row1 slice", rows[0][1] == "h1,h2\n", repr(rows[0][1]))
check("P1 row1 fields", rows[0][0] == ["h1", "h2"], rows[0][0])
check("P1 row2 slice", rows[1][1] == '"a\nb",c,"d\ne', repr(rows[1][1]))
check("P1 row2 fields", rows[1][0] == ["a\nb", "c", "d\ne"], rows[1][0])

s2 = "a,b\r\nc,d\r"
rows2 = row_slices(s2)
check(
    "P1 crlf/cr slices",
    rows2[0][1] == "a,b\r\n" and rows2[1][1] == "c,d\r",
    rows2,
)
rows3 = row_slices("a\n\n1\n")
check(
    "P1 blank-line slices",
    [r for r, _ in rows3] == [["a"], [], ["1"]]
    and [t for _, t in rows3] == ["a\n", "\n", "1\n"],
    rows3,
)
rows4 = row_slices('id,name\n"1,2')
check(
    "P1 unterminated-last slice",
    rows4[1][0] == ["1,2"] and rows4[1][1] == '"1,2',
    rows4,
)

# --- P2: D-28 offset -> line ---------------------------------------------


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


cases = [
    ("a,b\rc,d\rc\r", 12, 4),  # REQ-011 CR-only AC: offending byte -> line 4
    ("a\nb\n\nc", 4, 3),  # the \n at off 4 terminates line 3
    ("a\r\nb", 3, 2),  # CRLF = ONE break ('b' would be line 3 if two)
    ("a\x0bb\nc", 4, 2),  # VT is data: 'c' on line 2, NOT line 3
    ("a\x0cb\nc", 4, 2),  # FF is data
    ("a\u0085b\nc", 4, 2),  # NEL is data
    ("a\u2028b\nc", 4, 2),  # U+2028 is data
    ("a", 1, 1),
    ("", 0, 1),
]
for text, off, want in cases:
    if off > len(text):
        off = len(text)  # cite at EOF when the offset runs past the text
    got = line_of_offset(text, off)
    check(f"P2 line_of_offset({text!r}, {off})=={want}", got == want, f"got {got}")

# --- P3: unterminated-quote scanner FSM -----------------------------------


def scan_row(row_text):
    """Walk one record's text with the default-dialect field model.

    Returns (unterminated, open_line) where open_line is the 1-based line,
    counted on the D-28 basis WITHIN the record text, of the opening quote
    of the quoted section still open at end of text (0 if none).
    """
    line, i, n = 1, 0, len(row_text)
    FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3
    state = FIELD_START
    open_line = 0
    while i < n:
        c = row_text[i]
        if c == "\r" and i + 1 < n and row_text[i + 1] == "\n":
            # CRLF is ONE line break, wherever it appears
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
                pass  # stay FIELD_START: next field begins
            else:
                state = UNQUOTED
            i += 1
        elif state == UNQUOTED:
            if c == ",":
                state = FIELD_START
            # '"' inside an unquoted field is DATA (D-30)
            i += 1
        elif state == QUOTED:
            if c == '"':
                state = CLOSED
            # line breaks inside quotes are DATA and count as line breaks
            i += 1
        else:  # CLOSED: a quote just closed the section
            if c == '"':
                state = QUOTED  # doubled quote: re-open
            elif c == ",":
                state = FIELD_START
            else:
                state = UNQUOTED  # post-close junk is data
            i += 1
    unterminated = state == QUOTED
    return (unterminated, open_line if unterminated else 0)


p3_cases = [
    # (row_text, unterminated, rel_open_line)
    ('"1,2', True, 1),
    ('"id,name', True, 1),
    ('"1', True, 1),
    ('"a\nb",c,"d\ne', True, 2),  # rel line 2 -> abs M=3 when row starts at 2
    ('a,b', False, 0),
    ('"a\nb",c', False, 0),
    ('5" ruler,2', False, 0),  # D-30 negative AC: data quote
    ('"a""b"', False, 0),  # doubled quote closes properly
    ('"a"b', False, 0),  # post-close junk is data
    ("", False, 0),
    ("\n", False, 0),
    ('"a\r\nb', True, 1),  # CRLF inside the open quote
]
for row_text, want_unterm, want_line in p3_cases:
    got = scan_row(row_text)
    check(
        f"P3 scan({row_text!r})==({want_unterm},{want_line})",
        got == (want_unterm, want_line),
        f"got {got}",
    )

# End-to-end N/M on REQ-013's multi-field AC: h1,h2\n"a\nb",c,"d\ne
full = 'h1,h2\n"a\nb",c,"d\ne'
rs = row_slices(full)
row2_text = rs[1][1]
row2_start_off = full.index(row2_text)
N = line_of_offset(full, row2_start_off)
unterm, rel_open = scan_row(row2_text)
M = N + rel_open - 1
check(
    "P3 NM multi-field AC -> N=2 M=3",
    unterm and N == 2 and M == 3,
    f"N={N} M={M} unterm={unterm}",
)

# --- P4: UnicodeDecodeError.start -> D-28 line ----------------------------

data = b"a,b\rc,d\rc\r\xff"
try:
    data.decode("utf-8")
    check("P4 raises", False, "decode did not raise")
except UnicodeDecodeError as e:
    prefix = data[: e.start].decode("utf-8")
    got = line_of_offset(prefix, len(prefix))
    check("P4 CR-only byte cites line 4", got == 4, f"got {got} start={e.start}")

data2 = b"a,b\n\xff"
try:
    data2.decode("utf-8")
    check("P4b raises", False, "decode did not raise")
except UnicodeDecodeError as e:
    prefix = data2[: e.start].decode("utf-8")
    got = line_of_offset(prefix, len(prefix))
    check("P4b LF file byte cites line 2", got == 2, f"got {got} start={e.start}")

# --- P5: field-size limit degrade loop ------------------------------------

limit = sys.maxsize
steps = 0
while True:
    steps += 1
    try:
        csv.field_size_limit(limit)
        break
    except OverflowError:
        limit >>= 1
    if steps > 200:
        break
check("P5 degrade loop terminates", steps <= 200 and limit > 0, f"steps={steps} limit={limit}")
check("P5 limit is huge", limit > 131072, f"limit={limit}")

# --- P6: binary write bytes + escape contract -----------------------------

payload = json.dumps(
    [
        {"h": "x\r\ny", "k": "a\fbb\u000bc dd\u007fe ประเทศไท ย"},
    ],
    ensure_ascii=False,
    separators=(",", ":"),
)
blob = (payload + "\n").encode("utf-8")
check("P6 single line + ]\\n", blob.endswith(b']\n') and blob.count(b"\n") == 1, blob)
check(
    "P6 escapes",
    b'"h":"x\\r\\ny"' in blob
    and b"\\f" in blob
    and b"\\u000b" in blob
    and "\\u0000" not in payload
    and "\u007f" in payload
    and "ประเทศไท" in payload,
    blob,
)
nul = json.dumps({"h": "a\x00b"}, ensure_ascii=False, separators=(",", ":"))
check("P6 NUL escape", nul == '{"h":"a\\u0000b"}', nul)
vt = json.dumps({"h": "a\x0bb"}, ensure_ascii=False, separators=(",", ":"))
check("P6 VT escape", vt == '{"h":"a\\u000bb"}', vt)
ls = json.dumps({"h": "a\u2028b"}, ensure_ascii=False, separators=(",", ":"))
check("P6 U+2028 raw", ls == '{"h":"a b"}'.replace(" ", "\u2028"), ls)

# --- P7: reader.line_num lags on CRLF -> the design uses offset arithmetic -

p7_cases = [
    "a\r\nb\r\nc",
    "a\r\nb\rc\nd",
]
for text in p7_cases:
    f = io.StringIO(text, newline="")
    reader = csv.reader(f)
    next(reader)
    end = f.tell()
    want_next_row_start = line_of_offset(text, end)
    check(
        f"P7 reader.line_num lags after CRLF record ({text!r})",
        reader.line_num == 1 and want_next_row_start == 2,
        f"reader={reader.line_num} next-row-start={want_next_row_start}",
    )

# --- P8: the designed per-record pipeline on REQ acceptance cases ---------


def scan_unterminated(rec_text):
    """Dialect-exact FSM over one record's text (which excludes the record's
    own row terminator but INCLUDES newlines inside quoted fields).
    Returns the record-relative 1-based line of the opening quote of the
    quoted section still open at end of text, or 0 if none."""
    line, i, n = 1, 0, len(rec_text)
    FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3
    state, open_line = FIELD_START, 0
    while i < n:
        c = rec_text[i]
        if c == "\r" and i + 1 < n and rec_text[i + 1] == "\n" and state != QUOTED:
            state = FIELD_START  # record-internal terminator: none expected
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
            i += 1  # '"' in an unquoted field is data (D-30)
        elif state == QUOTED:
            if c == '"':
                state = CLOSED
            elif c == "\n" or c == "\r":
                line += 1  # data newline inside the open section
            i += 1
        else:  # CLOSED
            if c == '"':
                state = QUOTED  # doubled quote re-opens
            elif c == ",":
                state = FIELD_START
            else:
                state = UNQUOTED
            i += 1
    return open_line if state == QUOTED else 0


def convert(text):
    """The designed pipeline as a pure function of the decoded text.
    Returns ('ok', output_bytes) or ('err', message). Input path name and
    output path name are fixed ('input.csv' / 'output.json') for the probe."""
    OUT = "output.json"
    if text.startswith("\ufeff"):
        text = text[1:]  # REQ-012/D-16 strip before every other check
    f = io.StringIO(text, newline="")  # REQ-014/D-24 handoff
    reader = csv.reader(f)
    header = None
    rows = []
    start = 0
    while True:
        try:
            rec = next(reader)
        except StopIteration:
            break
        end = f.tell()  # AFTER the record is consumed (P1 order)
        row_start_line = line_of_offset(text, start)
        rec_text = text[start:end]
        q = scan_unterminated(rec_text)  # D-29: per-record, sequential
        if q:
            m_line = row_start_line + q - 1
            return (
                "err",
                f"csv2json: error: input.csv line {row_start_line}: "
                f"unterminated quoted field (opened at line {m_line})",
            )
        if header is None:
            if len(rec) == 0:
                return (
                    "err",
                    f"csv2json: error: input.csv line {row_start_line}: "
                    f"invalid header row (found 0 fields)",
                )
            header = rec
            seen = set()
            for name in header:
                if name in seen:
                    return (
                        "err",
                        f"csv2json: error: input.csv line {row_start_line}: "
                        f"duplicate header name '{name}'",
                    )
                seen.add(name)
        else:
            if len(rec) != len(header):
                return (
                    "err",
                    f"csv2json: error: input.csv line {row_start_line}: "
                    f"expected {len(header)} fields, found {len(rec)}",
                )
            rows.append(dict(zip(header, rec)))
        start = end
    if header is None:
        return "err", "csv2json: error: input.csv: file is empty (no header row)"
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return "ok", (payload + "\n").encode("utf-8")


def p8(name, text, want_kind, want_value):
    kind, val = convert(text)
    if kind != want_kind:
        check(f"P8 {name}", False, f"kind={kind} val={val!r}")
        return
    if want_kind == "ok":
        check(f"P8 {name}", val == want_value, f"got {val!r} want {want_value!r}")
    else:
        check(f"P8 {name}", val == want_value, f"got {val!r} want {want_value!r}")


p8("happy 2 rows", "id,name\n1,x\n2,y\n", "ok", b'[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n')
p8("empty header name (F-33)", "a,,b\n1,2,3\n", "ok", b'[{"a":"1","":"2","b":"3"}]\n')
p8("whitespace-only line (D-36)", "a\n  \n1\n", "ok", b'[{"a":"  "},{"a":"1"}]\n')
p8("CR-only file", "a,b\rc,d\r", "ok", b'[{"a":"c","b":"d"}]\n')
p8("CRLF in quoted field (D-24)", 'h,k\n"x\r\ny",2\n', "ok", b'[{"h":"x\\r\\ny","k":"2"}]\n')
p8("no trailing terminator", "id,name\n1,x", "ok", b'[{"id":"1","name":"x"}]\n')
p8("data quote in unquoted field (D-30)", 'desc,qty\n5" ruler,2\n', "ok", b'[{"desc":"5\\" ruler","qty":"2"}]\n')
p8("BOM stripped (D-16)", "﻿id,name\n1,x\n", "ok", b'[{"id":"1","name":"x"}]\n')
p8(
    "NM multi-field (D-30)",
    'h1,h2\n"a\nb",c,"d\ne',
    "err",
    "csv2json: error: input.csv line 2: unterminated quoted field (opened at line 3)",
)
p8(
    "unterminated data row",
    'id,name\n"1,2',
    "err",
    "csv2json: error: input.csv line 2: unterminated quoted field (opened at line 2)",
)
p8(
    "unterminated header (D-25)",
    '"id,name',
    "err",
    "csv2json: error: input.csv line 1: unterminated quoted field (opened at line 1)",
)
p8(
    "1-col unterminated",
    'a\n"1',
    "err",
    "csv2json: error: input.csv line 2: unterminated quoted field (opened at line 2)",
)
p8(
    "count error wins over later quote (D-29)",
    'id,name\n1\n"2,3',
    "err",
    "csv2json: error: input.csv line 2: expected 2 fields, found 1",
)
p8("blank middle line", "a\n\n1\n", "err", "csv2json: error: input.csv line 2: expected 1 fields, found 0")
p8("trailing blank line", "a,b,c\n1,2,3\n\n", "err", "csv2json: error: input.csv line 3: expected 3 fields, found 0")
p8("only blank lines", "\n\n", "err", "csv2json: error: input.csv line 1: invalid header row (found 0 fields)")
p8("empty file", "", "err", "csv2json: error: input.csv: file is empty (no header row)")
p8("BOM-only file (D-31)", "﻿", "err", "csv2json: error: input.csv: file is empty (no header row)")
p8("duplicate header", "a,a\n1,2\n", "err", "csv2json: error: input.csv line 1: duplicate header name 'a'")
p8("second empty header name", "a,,b,\n1,2,3,4\n", "err", "csv2json: error: input.csv line 1: duplicate header name ''")
p8("too many fields", "a,b\n1,2,3\n", "err", "csv2json: error: input.csv line 2: expected 2 fields, found 3")
p8("mixed terminators", "a\nb\rc\n", "ok", b'[{"a":"b"},{"a":"c"}]\n')

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

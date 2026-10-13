# Cycle-3 verification probes (req-review c3) — Python 3.13.5.
# Re-verifies the cycle-2 fold claims (F-13/F-14/F-15/F-19/F-20 as folded
# into v5) and grounds the new cycle-3 findings (F-21, F-22, F-23).

import csv, io, json, sys

PY = sys.version.split()[0]
print(f"python {PY}")
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f" | {detail}" if detail else ""))


# --- Batch 1: F-13 fold re-verification (newline matrix, REQ-014/D-24) ---
rows = list(csv.reader(io.StringIO("a,b\rc,d\r", newline="")))
check("CR-only file parses to 2 rows under newline=''",
      rows == [["a", "b"], ["c", "d"]], repr(rows))

f = list(csv.reader(io.StringIO('"x\r\ny"', newline="")))
check("CRLF inside quotes preserved byte-exactly", f == [["x\r\ny"]], repr(f))

f = list(csv.reader(io.StringIO('"x\ry"', newline="")))
check("bare CR inside quotes preserved", f == [["x\ry"]], repr(f))

try:
    list(csv.reader(io.StringIO("a,b\rc,d\r")))
    check("plain StringIO crashes on CR-only", False, "no exception raised")
except csv.Error as e:
    check("plain StringIO crashes on CR-only (unclassified)", "new-line" in str(e), str(e))

f = list(csv.reader(io.StringIO('"x\r\ny"', newline=None)))
check("universal newlines TRANSLATE CRLF->LF (forbidden construction)",
      f == [["x\ny"]], repr(f))

# --- Batch 2: F-14 fold re-verification + F-22 evidence (REQ-013/D-25) ---
f = list(csv.reader(io.StringIO('"id,name', newline="")))
check('"id,name" lenient parse = one 1-field header', f == [["id,name"]], repr(f))

f = list(csv.reader(io.StringIO('id,name\n"1,2', newline="")))
check('id,name\\n"1,2 lenient row is COUNT-VALID (unterminated pinned by AC)',
      f == [["id", "name"], ["1,2"]], repr(f))

f = list(csv.reader(io.StringIO('id,name\n"1', newline="")))
check('F-22: id,name\\n"1 lenient row = 1 field != 2 AND quote unterminated from line 2',
      f == [["id", "name"], ["1"]], repr(f))

f = list(csv.reader(io.StringIO('id,name\n1\n"2,3', newline="")))
check('cross-row order: count-bad row line 2 exists BEFORE quote-open line 3',
      f == [["id", "name"], ["1"], ["2,3"]], repr(f))

f = list(csv.reader(io.StringIO('id,id\n"1,2', newline="")))
check('duplicate header + unterminated data quote both present',
      f == [["id", "id"], ["1,2"]], repr(f))

f = list(csv.reader(io.StringIO('"', newline="")))
check("single-quote-byte file, lenient parse", True, repr(f))

f = list(csv.reader(io.StringIO('"\n', newline="")))
check("quote+newline file, lenient parse", True, repr(f))

# --- Batch 3: F-21 evidence (physical-line counting under CR, REQ-007c) ---
r = csv.reader(io.StringIO("a,b\rc,d\rc\rd\r", newline=""))
seen = []
for row in r:
    seen.append((r.line_num, row))
check("reader.line_num under CR-only file (natural implementation)",
      True, repr(seen))

r = csv.reader(io.StringIO("a\n\n1\n", newline=""))
seen = [(r.line_num, row) for row in r]
check("LF control case line_num (REQ-009 AC relies on this)",
      True, repr(seen))

r = csv.reader(io.StringIO('a,b\n"x\ny",2\n1\n', newline=""))
seen = [(r.line_num, row) for row in r]
check("embedded LF in quotes shifts later row line_num",
      True, repr(seen))

r = csv.reader(io.StringIO('a,b\n"x\ry",2\n1\n', newline=""))
seen = [(r.line_num, row) for row in r]
check("embedded bare CR in quotes: does line_num shift?",
      True, repr(seen))

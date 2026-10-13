"""Cycle-4 review probes (reviewer-side): new-corner candidates on Python 3.13.5.

Run: python3 appendix/09-review-req-c4-probes.py
"""
import csv, io, sys

results = []

def check(name, cond, detail):
    results.append((name, bool(cond), detail))

def rows(t):
    return list(csv.reader(io.StringIO(t, newline="")))

# A1: spaces-only line vs blank line (REQ-009 "blank physical line" term)
r = rows("a\n  \n1\n")
check("A1 spaces-line is 1-field data row",
      r == [["a"], ["  "], ["1"]],
      f"rows={r!r} (a spaces-only line is NOT a 0-field row; it is a "
      "1-field row whose value is the spaces)")

# A2: truly blank line -> 0-field row (baseline for A1 contrast)
r = rows("a\n\n1\n")
check("A2 blank-line is 0-field row", r == [["a"], [], ["1"]], f"rows={r!r}")

# A3: quoted section closed + junk quote afterwards = data, never unterminated
r = rows('"a"b"c')
check("A3 close+junk-quote is data", r == [['ab"c']], f"rows={r!r}")

# A4: same-row precedence — row 2 is BOTH count-bad (1 vs 2) and unterminated
r = rows('id,name\n"1,2')
check("A4 same-row count-vs-quote",
      r == [["id", "name"], ["1,2"]],
      f"rows={r!r} -> row 2 lenient-valid 1-field row, count 1 != 2, AND the "
      "field's quote never closes; v6 pins neither which error wins nor the "
      "message if the quote error wins")

# A5: header duplicate + unterminated quote in one header line
r = rows('id,"id')
check("A5 header dup+quote lenient fields", r == [["id", "id"]],
      f"rows={r!r} -> lenient header is ['id','id']: slot (5) duplicate "
      "fires before slot (6) quote per D-15 — outcome pinned only by "
      "inference, no AC")

# A6: trailing bare CR after the last record
r1 = rows("a\n1\n\r")
r2 = rows("a\n1\r\r")
check("A6 trailing-CR yields extra 0-field row",
      r1 == [["a"], ["1"], []] and r2 == [["a"], ["1"], []],
      f"LF-file+CR={r1!r} CR-file+CR={r2!r} (either way a 3rd, 0-field row "
      "-> REQ-006 error at line 3 per the trailing-newline discipline)")

# A7: usage-error exit code — argparse (the natural argv parser) exits 2
import argparse
code = None
try:
    p = argparse.ArgumentParser(prog="csv2json.py")
    p.add_argument("input"); p.add_argument("output")
    p.parse_args(["only-one"])
except SystemExit as e:
    code = e.code
check("A7 argparse usage exit code is 2 (not 1)",
      code == 2, f"SystemExit code={code!r} (REQ-001 pins only 'non-zero'; "
      "every other error class in v6 exits exactly 1)")

# A8: empty header field name — usable verbatim as a JSON key (F-33 evidence)
r = rows("a,,b\n1,2,3\n")
import json
out = json.dumps([dict(zip(r[0], r[1]))], ensure_ascii=False,
                 separators=(",", ":"))
check("A8 empty header name becomes an empty-string JSON key",
      r == [["a", "", "b"], ["1", "2", "3"]]
      and out == '[{"a":"1","":"2","b":"3"}]',
      f"rows={r!r} out={out} (valid compact JSON; v6 never says whether "
      "empty header names are permitted keys)")

for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
failed = [x for x in results if not x[1]]
print(f"\n{len(results)-len(failed)}/{len(results)} probes done (Python {sys.version.split()[0]})")
sys.exit(1 if failed else 0)

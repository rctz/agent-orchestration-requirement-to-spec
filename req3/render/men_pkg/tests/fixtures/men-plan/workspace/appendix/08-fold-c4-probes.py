"""Fold-verification probes for requirements v6 (cycle-4 folds D-28..D-31).

Re-runs live (Python 3.13.5) the stdlib-behavior claims the v6 folds pin.
Each probe asserts one normative claim; the script exits 0 iff all pass.
Run: python3 appendix/08-fold-c4-probes.py
"""
import csv, io, json, re, sys

results = []

def check(name, cond, detail):
    results.append((name, bool(cond), detail))

def d28_line_count(text):
    """D-28 basis: CRLF=one break, then bare CR, then LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n").count("\n")

# --- D-28: CRLF is ONE break (csv.reader.line_num agrees) ---
r = csv.reader(io.StringIO("a,b\r\nc,d\r\ne,f\r\n", newline=""))
rows = list(r)
check("D-28 CRLF-as-one (line_num)", len(rows) == 3 and r.line_num == 3,
      f"rows={rows} line_num={r.line_num}")

# --- D-28: CR-only file: 3 terminators -> next content is line 4 ---
cr_only = "a,b\rc,d\rc\r"
check("D-28 CR-only count", d28_line_count(cr_only) == 3,
      f"breaks={d28_line_count(cr_only)} -> offending byte at line 4")

# --- D-28: VT 0x0B is DATA (csv.reader keeps it in-field; line_num=2) ---
r = csv.reader(io.StringIO("a,b\nc\x0bd,e\n", newline=""))
rows = list(r)
check("D-28 VT is data (reader)", rows == [["a", "b"], ["c\x0bd", "e"]]
      and r.line_num == 2, f"rows={rows} line_num={r.line_num}")

# --- D-28: str.splitlines() is a NON-conforming counter (breaks on VT) ---
split_demo = "a\nb\x0bc\n".splitlines()
check("D-28 splitlines non-conforming", split_demo == ["a", "b", "c"],
      f"splitlines={split_demo!r} (3 breaks vs D-28's 2)")

# --- D-29: lenient parse of the F-22 counterexample (facts behind the AC) ---
text = 'id,name\n1\n"2,3'
rows = list(csv.reader(io.StringIO(text, newline="")))
check("D-29 F-22 counterexample parse",
      rows == [["id", "name"], ["1"], ["2,3"]],
      f"rows={rows} -> count-bad row 2 precedes quote row 3; "
      "sequential fail-fast cites line 2")

# --- D-30: N/M for a non-first unterminated field (facts behind the AC) ---
text = 'h1,h2\n"a\nb",c,"d\ne'
rows = list(csv.reader(io.StringIO(text, newline="")))
check("D-30 F-23 N/M parse", rows == [["h1", "h2"], ["a\nb", "c", "d\ne"]],
      f"rows={rows}")
check("D-30 F-23 lines", d28_line_count(text) == 3
      and text.replace("\r\n", "\n").replace("\r", "\n").split("\n")[2].startswith('b",c,"d'),
      "row starts line 2; third field's opening quote sits on line 3 "
      "-> 'line 2 ... (opened at line 3)'")

# --- D-30: quote in UNQUOTED field is data (F-24 negative AC) ---
rows = list(csv.reader(io.StringIO('desc,qty\n5" ruler,2\n', newline="")))
obj = [{"desc": rows[1][0], "qty": rows[1][1]}]
out = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
check("D-30 F-24 data-quote", rows == [["desc", "qty"], ['5" ruler', "2"]]
      and out == '[{"desc":"5\\" ruler","qty":"2"}]', f"rows={rows} out={out}")

# --- D-31: BOM-only file decodes, strips to empty, parses to ZERO rows ---
bom_only = b"\xef\xbb\xbf".decode("utf-8")
stripped = bom_only.lstrip("\ufeff")
rows = list(csv.reader(io.StringIO(stripped, newline="")))
check("D-31 BOM-only", bom_only == "\ufeff" and stripped == "" and rows == [],
      f"decoded={bom_only!r} stripped={stripped!r} rows={rows} "
      "-> REQ-009 empty-file class, not invalid-header")

failed = [x for x in results if not x[1]]
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
print(f"\n{len(results) - len(failed)}/{len(results)} probes passed "
      f"(Python {sys.version.split()[0]})")
sys.exit(1 if failed else 0)

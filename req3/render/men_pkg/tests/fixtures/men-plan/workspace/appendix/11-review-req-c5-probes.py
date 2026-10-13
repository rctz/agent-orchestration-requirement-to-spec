# Cycle-5 review probes (independent, req-review cycle 5): corners this
# review exercises against v7 claims. Run: python3 appendix/11-review-req-c5-probes.py
import csv, io, sys

fails = []
def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, detail)
    if not cond:
        fails.append(name)

def rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))

# P1: duplicate-header + unterminated-quote co-present in the header row
# (`id,"id` -> lenient parse ['id','id']). D-15 fixed order: slot (5)
# duplicate precedes slot (6) quote detection -> duplicate error wins.
r = rows('id,"id')
check("c5.header-dup-plus-unterminated", r == [["id", "id"]], repr(r))

# P2: the REQ-013 AC that forces within-row quote-before-count precedence:
# `id,name\n"1,2` -> row 2 is ONE field (count-bad) AND unterminated; the AC
# pins the QUOTE message, so quote check precedes count check per row.
r = rows('id,name\n"1,2')
check("c5.quote-vs-count-same-row", r == [["id", "name"], ["1,2"]], repr(r))

# P3: whitespace-only line with a TAB is a 1-field data row (D-36).
r = rows("a\n\t\n1\n")
check("c5.tab-only-line-1field", r == [["a"], ["\t"], ["1"]], repr(r))

# P4: whitespace-only line terminated by CRLF is still 1 field (D-28/D-36).
r = rows("a\n \r\n1\r\n")
check("c5.space-crlf-line-1field", r == [["a"], [" "], ["1"]], repr(r))

# P5: N/M recomputation for the pinned AC shape (N=2, M=3).
rd = csv.reader(io.StringIO('h1,h2\n"a\nb",c,"d\ne', newline=""))
out = list(rd)
ln = rd.line_num
check("c5.nm-shape", out == [["h1", "h2"], ["a\nb", "c", "d\ne"]] and ln == 4,
      f"rows={out!r} line_num={ln}")

# P6: header-only + trailing newline -> [] (REQ-009 case 1).
r = rows("a,b\n")
check("c5.header-only", r == [["a", "b"]], repr(r))

print(f"\n{len(fails)} failure(s)" if fails else "\nALL PASS")
sys.exit(1 if fails else 0)

# Cycle-5 review probes, batch 2: pure dialect corners.
# Run: python3 appendix/11b-review-req-c5-probes2.py
import csv, io, sys

def rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))

for name, text in [
    ("junk-after-close", 'a,"b"c,d\n1,2,3\n'),
    ("single-quote-file", '"'),
    ("header-dup-unterminated", 'id,"id'),
    ("space-then-quote", 'a, "x\n1,2\n'),
]:
    print(name, "->", repr(rows(text)))

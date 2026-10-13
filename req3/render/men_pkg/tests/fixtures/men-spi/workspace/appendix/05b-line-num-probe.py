"""Cycle-2 micro-probe: reader.line_num counting semantics (CR vs LF)."""
import csv, io

for label, text in [("LF file", "a\n1\n2\n"), ("CR file", "a\r1\r2\r"),
                    ("CRLF file", "a\r\n1\r\n2\r\n")]:
    r = csv.reader(io.StringIO(text, newline=""))
    rows = []
    nums = []
    for row in r:
        rows.append(row)
        nums.append(r.line_num)
    print(f"{label}: rows={rows} line_num_after_each={nums}")

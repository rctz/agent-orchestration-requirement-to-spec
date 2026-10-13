# Cycle-3 probes batch 4 — realistic counterexamples for F-21/F-22/F-27.

import csv, io, json

def rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))

# F-22 realistic case: inch marks in data (odd quote count, no quoted field)
print("1", repr(rows('desc,qty\n5" ruler,2\n')))   # valid file, 1 quote total

# F-22: quote-parity vs state machine on the SAME file
total_quotes = 'desc,qty\n5" ruler,2\n'.count('"')
print("2 total quotes in file:", total_quotes, "-> parity scanner says:",
      "UNTERMINATED (odd)" if total_quotes % 2 else "ok")

# F-21: VT is data (D-14) but splitlines counts it as a break
prefix = "a\nb\x0bc\n"
print("3 LF-count of prefix:", prefix.count("\n"))            # -> 2 (byte on line 3)
print("4 splitlines of prefix:", prefix.splitlines())           # -> ['a','b','c'] (byte on line 4)
print("5 parser row model:", rows("a\nb\x0bc\n1\n"))            # VT stays in field data

# F-21: CR-only file, count error in 2nd row — which line does REQ-007(c) print?
print("6 rows:", rows("a\rb\rc,d"))                             # 1-col header, rows b and c,d(2 fields)
r = csv.reader(io.StringIO("a\rb\rc,d", newline=""))
print("7 line_num per row:", [(r.line_num, row) for row in r])

# F-27: BOM-only file
raw = b"\xef\xbb\xbf"
text = raw.decode("utf-8")
print("8 decoded:", repr(text), "| stripped starts with BOM:",
      text.startswith("\ufeff"))
print("9 reader on stripped text:", list(csv.reader(io.StringIO(text[1:], newline=""))))
print("10 reader on unstripped text:", list(csv.reader(io.StringIO(text, newline=""))))

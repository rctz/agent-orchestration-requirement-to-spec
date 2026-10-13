# Cycle-3 probes batch 3 — line counting + quote-state corners.

import csv, io

def rows(text):
    return list(csv.reader(io.StringIO(text, newline="")))

def lnums(text):
    r = csv.reader(io.StringIO(text, newline=""))
    return [(r.line_num, row) for row in r]

# 1. CRLF: does reader.line_num count \r\n as ONE line break?
print("1 CRLF lnums:", lnums("a,b\r\nc,d\r\ne,f\r\n"))

# 2. VT (0x0B) inside a quoted field: data per D-14 — does line_num skip it?
print("2 VT-in-quotes lnums:", lnums('a,b\n"x\x0by",2\n1\n'))

# 3. FF (0x0C) inside a quoted field:
print("3 FF-in-quotes lnums:", lnums('a,b\n"x\x0cy",2\n1\n'))

# 4. splitlines boundary set vs terminator trio (clean re-run)
print("4a splitlines VT:", "a\x0bb".splitlines())
print("4b splitlines FF:", "a\x0cb".splitlines())
print("4c splitlines NEL:", "a\x85b".splitlines())
print("4d splitlines CR:", "a\rb".splitlines())

# 5. REQ-013 parity gloss corners (state machine vs 'odd number of quotes')
print("5a \"a\"b\"c :", repr(rows('"a"b"c')))     # odd total quotes; state machine: closed?
print("5b \"a\"\"   :", repr(rows('"a""')))        # open,a,escaped-quote,EOF -> unterminated?
print("5c say \"hi\":", repr(rows('say "hi"')))    # quotes in UNQUOTED field
print("5d h,k\\nsay \"hi\",2:", repr(rows('h,k\nsay "hi",2')))

# 6. full-file shape for the F-21 counterexample (CR-only + invalid byte)
raw = b"a,b\rc,d\rc\r\xff"
try:
    raw.decode("utf-8")
    print("6 decoded?!")
except UnicodeDecodeError as e:
    print("6 bad byte offset:", e.start)
    prefix = raw[: e.start]
    print("6 LF-count:", prefix.count(b"\n"), "| CR-count:", prefix.count(b"\r"))

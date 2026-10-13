#!/usr/bin/env python3
"""62d-adv-c13-globals — test the hypothesis: 48c's 24-27 s vs 55h's 15 s
gap for the 'same' two-quantity walk is MODULE-LEVEL GLOBALS vs FUNCTION
LOCALS (CPython name-binding cost inside the per-character loop).

Runs the 48c-verbatim loop twice: once at module level (all names global),
once inside a function (all names fast locals). Same payload, same process.
"""
import csv as _csv
import io as _io
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"
text = "h1,h2\n" + "".join(ROW for _ in range(n))


def count_line_breaks(s, a, b):
    c = 0
    j = a
    while j < b:
        if s[j] == "\r":
            j += 2 if s[j + 1:j + 2] == "\n" else 1
            c += 1
        elif s[j] == "\n":
            j += 1
            c += 1
        else:
            j += 1
    return c


def walk_function(text):
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    start = 0
    line = 1
    nrec = 0
    while True:
        try:
            record = next(reader)
        except StopIteration:
            break
        end = buf.tell()
        record_text = text[start:end]
        st = 0
        i = 0
        L = len(record_text)
        while i < L:
            c = record_text[i]
            if c == '"':
                st = {0: 2, 2: 3, 3: 2}.get(st, st)
                i += 1
            elif c == ",":
                if st in (1, 3):
                    st = 0
                i += 1
            elif c in "\r\n":
                if c == "\r" and i + 1 < L and record_text[i + 1] == "\n":
                    i += 2
                else:
                    i += 1
                st = 2 if st == 2 else 0
                if st == 2:
                    pass
            else:
                if st == 0:
                    st = 1
                elif st == 3:
                    st = 1
                i += 1
        line += count_line_breaks(text, start, end)
        start = end
        nrec += 1
    return nrec, line


# ---- module-level (globals) form: the 48c measurement style ----
t0 = time.perf_counter()
buf = _io.StringIO(text, newline="")
reader = _csv.reader(buf)
start = 0
line = 1
nrec = 0
while True:
    try:
        record = next(reader)
    except StopIteration:
        break
    end = buf.tell()
    record_text = text[start:end]
    st = 0
    i = 0
    L = len(record_text)
    while i < L:
        c = record_text[i]
        if c == '"':
            st = {0: 2, 2: 3, 3: 2}.get(st, st)
            i += 1
        elif c == ",":
            if st in (1, 3):
                st = 0
            i += 1
        elif c in "\r\n":
            if c == "\r" and i + 1 < L and record_text[i + 1] == "\n":
                i += 2
            else:
                i += 1
            st = 2 if st == 2 else 0
            if st == 2:
                pass
        else:
            if st == 0:
                st = 1
            elif st == 3:
                st = 1
            i += 1
    line += count_line_breaks(text, start, end)
    start = end
    nrec += 1
t_module = time.perf_counter() - t0

# ---- function (locals) form: the 55h measurement style ----
t0 = time.perf_counter()
r = walk_function(text)
t_func = time.perf_counter() - t0

print(f"module-level (48c style): {t_module:.1f}s  records={nrec} line={line}")
print(f"function    (55h style): {t_func:.1f}s  {r}")
print(f"ratio: {t_module/max(t_func,0.001):.2f}x")

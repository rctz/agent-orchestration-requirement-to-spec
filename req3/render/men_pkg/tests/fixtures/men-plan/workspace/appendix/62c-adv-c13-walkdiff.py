#!/usr/bin/env python3
"""62c-adv-c13-walkdiff — why does 48c's walk measure 26.3 s while 55h's
nominally-identical '48c shape' walk measures 15.0 s on the same host?

Extract both walk functions verbatim from the two artifacts, run them
interleaved (A,B,A,B) on the same payload, and diff their sources.
"""
import csv as _csv
import io as _io
import re
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


def walk_48c(text):
    """Verbatim 48c inner shape (FSM without open_line/rel + count_line_breaks)."""
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


def walk_55h(text):
    """Verbatim 55h two_quantity_walk shape (FSM WITH open_line/rel + count_line_breaks)."""
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
        open_line = None
        rel = 0
        while i < L:
            c = record_text[i]
            if c == '"':
                if st == 0 and open_line is None:
                    open_line = rel + 1
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
                rel += 1
                st = 0 if st != 2 else 2
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


for name, fn in (("48c-shape", walk_48c), ("55h-shape", walk_55h)):
    t0 = time.perf_counter()
    r = fn(text)
    print(f"{name}: {time.perf_counter()-t0:.1f}s {r}")
for name, fn in (("48c-shape", walk_48c), ("55h-shape", walk_55h)):
    t0 = time.perf_counter()
    r = fn(text)
    print(f"{name}: {time.perf_counter()-t0:.1f}s {r}")

#!/usr/bin/env python3
"""55h-sr11-fused-timing — LIVE measurement for the T-C9 fused-walk claim.

spec/12-spec-v12.md §8.3 T-C9 claims: 'fused D-58 single-pass walk and
reader-only baseline ~0.8-1 s (appendix/48c, appendix/51 B3)'.

48c measures NO fused form and appendix/51 B3 has no timing at all.
This probe measures BOTH forms on the SAME payload as 48c (~50 MB, 250k
rows): the two-quantity walk (48c's shape) and the D-58 fused single pass
(one scan doing FSM transitions + break counting together)."""

import csv as _csv
import io as _io
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"  # same as 48c
t0 = time.perf_counter()
text = "h1,h2\n" + "".join(ROW for _ in range(n))
print(f"payload: {len(text)/1e6:.1f} MB, {n} rows, built in {time.perf_counter()-t0:.1f}s")


def two_quantity_walk(text):
    """48c's spec-shape walk: FSM scan with own counter + count_line_breaks."""
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

    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    start = 0
    line = 1
    nrec = 0
    uq = []
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
                    open_line = rel + 1  # record-relative opening line
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
        if st == 2:
            uq.append((line, line + (open_line or 1) - 1))
        line += count_line_breaks(text, start, end)
        start = end
        nrec += 1
    return nrec, line, uq


def fused_walk(text):
    """D-58 fused single pass: ONE scan per record doing FSM transitions AND
    break counting (the counter advances exactly where the D-28 rule does)."""
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    start = 0
    line = 1
    nrec = 0
    uq = []
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
                rel += 1  # fused: the SAME pass advances the break counter
                st = 0 if st != 2 else 2
            else:
                if st == 0:
                    st = 1
                elif st == 3:
                    st = 1
                i += 1
        if st == 2:
            uq.append((line, line + (open_line or 1) - 1))
        line += rel  # fused: no second scan of the span
        start = end
        nrec += 1
    return nrec, line, uq


# outcome identity first
r1 = two_quantity_walk("h1,h2\n\"a\r\nb\",c,\"d\ne")
r2 = fused_walk("h1,h2\n\"a\r\nb\",c,\"d\ne")
print("outcome identity on CRLF corpus:", r1 == r2, r1, r2)

t0 = time.perf_counter()
a = two_quantity_walk(text)
t_two = time.perf_counter() - t0
print(f"TWO-QUANTITY (48c shape): {t_two:.1f}s  records={a[0]} final_line={a[1]}")

t0 = time.perf_counter()
b = fused_walk(text)
t_fused = time.perf_counter() - t0
print(f"FUSED (D-58 shape):        {t_fused:.1f}s  records={b[0]} final_line={b[1]}")

print(f"agreement: {a == b}")
print(f"T-C9 claim was: fused ~0.8-1 s like the reader-only baseline")
print(f"measured: fused={t_fused:.1f}s two-quantity={t_two:.1f}s ratio={t_two/max(t_fused,0.001):.1f}x")

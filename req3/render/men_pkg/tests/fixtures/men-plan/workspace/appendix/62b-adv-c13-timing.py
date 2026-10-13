#!/usr/bin/env python3
"""62b-adv-c13-timing — adversarial-early cycle-13 live timing probes.

Spec v13 (SR11-F-01 fix) states in T-C9 / QC-5 / D-58 register row:
  - two-quantity walk ~25-27 s, fused walk ~9.1 s (walk-only numbers)
  - margin arithmetic: fused leaves "~20 s" of the 30 s envelope for
    decode+dict+serialize+write ("still inside 30 s"); two-quantity
    "leaves only ~3-5 s".

The cited artifacts (48c, 55h) measure WALK-ONLY and stage pieces, never
the end-to-end pipeline. This probe measures, on ONE payload (~52 MB,
250k rows, the 48c/55h shape):
  P1: end-to-end TWO-QUANTITY pipeline (decode + full spec walk + dict + serialize + write)
  P2: end-to-end FUSED pipeline (D-58 shape)
  P3: walk-only numbers for direct comparison with 48c/55h claims
"""
import csv as _csv
import io as _io
import json as _json
import os as _os
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"  # same as 48c/55h
t0 = time.perf_counter()
text = "h1,h2\n" + "".join(ROW for _ in range(n))
print(f"payload: {len(text)/1e6:.1f} MB, {n} rows, built in {time.perf_counter()-t0:.1f}s")

OUT = "/tmp/adv62b_out.json"


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


def walk(text, fused):
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
        rel = 0
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
                rel += 1
                st = 0 if st != 2 else 2
            else:
                if st == 0:
                    st = 1
                elif st == 3:
                    st = 1
                i += 1
        if fused:
            line += rel
        else:
            line += count_line_breaks(text, start, end)
        start = end
        nrec += 1
    return nrec, line


def pipeline(fused, label):
    t0 = time.perf_counter()
    # stage S1+S2: bytes->str (decode) — 48c/55h skip this; the spec counts it
    data = text.encode("utf-8")
    t_enc = time.perf_counter() - t0
    t0 = time.perf_counter()
    decoded = data.decode("utf-8")
    t_dec = time.perf_counter() - t0
    t0 = time.perf_counter()
    nrec, finalline = walk(decoded, fused)
    t_walk = time.perf_counter() - t0
    t0 = time.perf_counter()
    buf = _io.StringIO(decoded, newline="")
    rows = [dict(zip(("h1", "h2"), r)) for r in _csv.reader(buf)]
    t_dict = time.perf_counter() - t0
    t0 = time.perf_counter()
    doc = _json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
    payload = doc.encode("utf-8")
    t_ser = time.perf_counter() - t0
    t0 = time.perf_counter()
    fd = open(OUT, "wb")
    fd.write(payload)
    fd.flush()
    fd.close()
    t_write = time.perf_counter() - t0
    total = t_enc + t_dec + t_walk + t_dict + t_ser + t_write
    print(f"{label}: total={total:.1f}s  decode={t_dec:.1f}s (encode-for-input {t_enc:.1f}s excluded from total)"
          f"  walk={t_walk:.1f}s  dict={t_dict:.1f}s  serialize={t_ser:.1f}s  write={t_write:.1f}s"
          f"  records={nrec}")
    return total, t_walk


# order: fused first (fresher thermal state is the OPTIMISTIC one for the
# two-quantity form we want to stress; if two-quantity STILL busts 30 s when
# measured second, the claim is dead regardless of ordering bias)
tot_fused, walk_fused = pipeline(True, "P2 END-TO-END FUSED (D-58)      ")
tot_two, walk_two = pipeline(False, "P1 END-TO-END TWO-QUANTITY (spec) ")

print()
print(f"P3 walk-only: two-quantity={walk_two:.1f}s fused={walk_fused:.1f}s")
print(f"spec v13 claims to check (T-C9/QC-5/D-58 row):")
print(f"  fused walk ~9.1 s (55h): measured {walk_fused:.1f}s")
print(f"  two-quantity walk ~25-27 s (48c): measured {walk_two:.1f}s")
print(f"  'fused ... still inside 30 s': measured end-to-end fused total = {tot_fused:.1f}s")
print(f"  'two-quantity ... leaves only ~3-5 s': measured end-to-end two-quantity total = {tot_two:.1f}s")
if _os.path.exists(OUT):
    _os.remove(OUT)

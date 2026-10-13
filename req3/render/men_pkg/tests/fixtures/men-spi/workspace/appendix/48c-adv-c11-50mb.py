#!/usr/bin/env python3
"""48c-adv-c11-50mb — one-shot timing: the §4.3.2/§4.3.3 spec-shape record
walk (slice + FSM-with-counter + count_line_breaks) over a ~50 MB /
250k-row input, plus the reader-only and full-pipeline baselines, on this
host. Evidence for the adv-c11 perf note (QC-5/T-C9 envelope margin)."""
import csv as _csv
import io as _io
import json as _json
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"  # ~209 B/row
t0 = time.perf_counter()
text = "h1,h2\n" + "".join(ROW for _ in range(n))
t_gen = time.perf_counter() - t0
mb = len(text) / 1e6


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


# spec-shape walk
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
dt_walk = time.perf_counter() - t0

# reader-only baseline
t0 = time.perf_counter()
rows_raw = list(_csv.reader(_io.StringIO(text, newline="")))
dt_plain = time.perf_counter() - t0

# full pipeline baseline (parse->dicts->serialize)
t0 = time.perf_counter()
rows = [dict(zip(("h1", "h2"), r)) for r in rows_raw]
doc = _json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
dt_rest = time.perf_counter() - t0

print(f"input={mb:.1f} MB rows={n} records={nrec} final_line={line}")
print(f"gen={t_gen:.1f}s  spec-shape-walk={dt_walk:.1f}s  reader-only={dt_plain:.1f}s  dict+serialize={dt_rest:.1f}s")
print(f"spec-shape walk ratio vs reader-only: {dt_walk/dt_plain:.1f}x")
print(f"doc bytes={len(doc)/1e6:.1f} MB")

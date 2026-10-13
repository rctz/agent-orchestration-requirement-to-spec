#!/usr/bin/env python3
"""62g-adv-c13-rss — sanity-check T-C9/QC-5's '< 1 GB RSS' envelope claim on
the reference-class host, end-to-end fused pipeline (the envelope's own
assertion is < 30 s AND < 1 GB RSS; timing was measured by 62b — this
probe adds the RSS dimension). Also re-times with the REAL 10-column dict
build (48c/55h/62b all simplified dicts to 2 columns, which under-measures
the dict+serialize stage).
"""
import csv as _csv
import io as _io
import json as _json
import resource
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"
HDR = [f"f{j}" for j in range(10)]
text = "h1" + ",".join(HDR[1:]) + "\n" + "".join(ROW for _ in range(n))

t0 = time.perf_counter()
buf = _io.StringIO(text, newline="")
reader = _csv.reader(buf)
rows = []
hdr = None
start = 0
line = 1
while True:
    try:
        record = next(reader)
    except StopIteration:
        break
    end = buf.tell()
    span = text[start:end]
    # fused walk (D-58)
    st = 0
    i = 0
    L = len(span)
    rel = 0
    while i < L:
        c = span[i]
        if c == '"':
            st = {0: 2, 2: 3, 3: 2}.get(st, st)
            i += 1
        elif c == ",":
            if st in (1, 3):
                st = 0
            i += 1
        elif c in "\r\n":
            if c == "\r" and i + 1 < L and span[i + 1] == "\n":
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
    line += rel
    start = end
    if hdr is None:
        hdr = record
    else:
        rows.append(dict(zip(hdr, record)))
t_walkdict = time.perf_counter() - t0

t0 = time.perf_counter()
doc = _json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
payload = doc.encode("utf-8")
t_ser = time.perf_counter() - t0

peak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(f"fused walk + REAL 10-col dict build: {t_walkdict:.1f}s")
print(f"serialize(10-col, {len(payload)/1e6:.0f} MB doc) + encode: {t_ser:.1f}s")
print(f"NOTE: decode stage excluded here (text built in-memory); see 62b for stage split")
print(f"peak RSS: {peak_kb/1e6:.2f} GB (claim: < 1 GB)")

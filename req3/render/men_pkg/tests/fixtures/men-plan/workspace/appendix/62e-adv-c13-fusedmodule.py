#!/usr/bin/env python3
"""62e-adv-c13-fusedmodule — the fused walk at MODULE level (48c's binding
style), to test whether the D-58 '27.3 s vs 9.1 s' ranking survives a
change of binding. 62d showed the two-quantity walk: module 26.0 s vs
function 15.0 s (1.73x). If the fused walk degrades similarly, the fused
module-level cost (~15-16 s) EQUALS the two-quantity function cost — the
two effects are the same size and the margin narrative is binding-bound.
"""
import csv as _csv
import io as _io
import time

n = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"
text = "h1,h2\n" + "".join(ROW for _ in range(n))

# ---- module-level (globals) FUSED walk: the 55h loop body hoisted to
# module scope, exactly like 48c's layout ----
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
    line += rel
    start = end
    nrec += 1
t_module_fused = time.perf_counter() - t0
print(f"module-level FUSED walk: {t_module_fused:.1f}s  records={nrec} line={line}")
print("compare: function fused 9.1s (55h/62b), function two-quantity 15.0s, module two-quantity 26.0s (62d)")

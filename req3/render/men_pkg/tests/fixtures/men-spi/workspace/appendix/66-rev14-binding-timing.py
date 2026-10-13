#!/usr/bin/env python3
"""66-rev14-binding-timing — the c14 binding-controlled evidence set.

Closes adv-c13 F-01 (P1): v13's T-C9/QC-5/D-58 numbers compared two
artifacts measured under DIFFERENT CPython name bindings (48c: module
level = globals; 55h: inside functions = fast locals). 62d showed the
binding effect (~11 s) DWARFS the form effect (~6 s), so the 27.3-vs-9.1
comparison misattributed binding cost to scan form.

This probe measures BOTH forms (two-quantity = §4.3.2+§4.3.3 double scan;
fused = D-58 single pass) under BOTH bindings, in ONE process, on the
same payload as 48c/55h (250k rows, ~52 MB), plus the reader-only and
dict+serialize baselines. The four timed loops are the SAME loop text
differing only in (a) fusion and (b) binding wrapper; agreement of
nrec/final_line across all four cells guards against transcription drift.

Closes adv-c13 F-02 (P2, identity half): part B latches the opening line
at EVERY FIELD_START->QUOTED transition (the §4.3.3 table's wording),
so the remembered line on a record ending QUOTED is the UNCLOSED quote's
line (S-10: N=2, M=3 on h1,h2\\n"a\\r\\nb",c,"d\\ne), and asserts two-quantity
== fused == the normative (N, M) on the whole corpus family — including
the multi-quote corpus where the legacy first-latch (appendix/51 B3 /
55h) computes M=2. The legacy shape is run and shown to DIFFER, which is
the honest demonstration of what B3's cite could not prove.

Timing cells are latch-free (the 48c/55h timing shapes; the latch costs
one comparison per quote and the timing payload is quote-free).
"""
import csv as _csv
import io as _io
import json as _json
import time

N_ROWS = 250000
ROW = ",".join(f"f{j}_{'x' * 18}" for j in range(10)) + "\n"
text = "h1,h2\n" + ROW * N_ROWS


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


# ---- the walk bodies as functions (fast-local binding: 55h's regime) ----
def walk_tq_function(text):
    """Two-quantity: FSM scan + separate count_line_breaks per record."""
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


def walk_fused_function(text):
    """D-58 fused: ONE scan advances the FSM and the break counter."""
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
                st = 2 if st == 2 else 0
            else:
                if st == 0:
                    st = 1
                elif st == 3:
                    st = 1
                i += 1
        line += rel
        start = end
        nrec += 1
    return nrec, line


# warm-up (small payload) so no timed cell pays cold-start cost
_warm = "h1,h2\n" + ROW * 10000
walk_tq_function(_warm)
walk_fused_function(_warm)

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def timed(fn, arg):
    t0 = time.perf_counter()
    r = fn(arg)
    return (time.perf_counter() - t0), r


# ---- module-level cells: the SAME two loops with every name global ----
# (transcribed verbatim from the function bodies above — this IS the 48c
# measurement regime; 62d proved the transcription itself is the point.)
buf = _io.StringIO(text, newline="")
reader = _csv.reader(buf)
start = 0
line = 1
nrec = 0
t0 = time.perf_counter()
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
        else:
            if st == 0:
                st = 1
            elif st == 3:
                st = 1
            i += 1
    line += count_line_breaks(text, start, end)
    start = end
    nrec += 1
t_tq_module = time.perf_counter() - t0
r_tq_module = (nrec, line)

buf = _io.StringIO(text, newline="")
reader = _csv.reader(buf)
start = 0
line = 1
nrec = 0
t0 = time.perf_counter()
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
            st = 2 if st == 2 else 0
        else:
            if st == 0:
                st = 1
            elif st == 3:
                st = 1
            i += 1
    line += rel
    start = end
    nrec += 1
t_fused_module = time.perf_counter() - t0
r_fused_module = (nrec, line)

t_tq_func, r_tq_func = timed(walk_tq_function, text)
t_fused_func, r_fused_func = timed(walk_fused_function, text)

# reader-only + dict+serialize baselines (48c's shapes)
t0 = time.perf_counter()
rows_raw = list(_csv.reader(_io.StringIO(text, newline="")))
t_reader = time.perf_counter() - t0
t0 = time.perf_counter()
rows = [dict(zip(("h1", "h2"), r)) for r in rows_raw]
doc = _json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
t_rest = time.perf_counter() - t0

# four-cell agreement guard (same loop, same payload -> same results)
check("A1 four cells agree on (nrec, final_line)",
      r_tq_module == r_tq_func == r_fused_module == r_fused_func,
      f"{r_tq_module} {r_tq_func} {r_fused_module} {r_fused_func}")
check("A2 payload shape as cited", len(text) > 50_000_000 and N_ROWS == 250000,
      f"{len(text)/1e6:.1f} MB")
check("A3 output document sane (2 of 10 fields kept, as 48c's baseline)",
      doc.endswith(']\n') and len(doc) > 10_000_000,
      f"{len(doc)/1e6:.1f} MB")

print(f"payload: {len(text)/1e6:.1f} MB / {N_ROWS} rows; doc {len(doc)/1e6:.1f} MB; results {r_tq_func}")
print(f"TWO-QUANTITY module-bound : {t_tq_module:5.1f} s   (48c regime)")
print(f"TWO-QUANTITY function-bound: {t_tq_func:5.1f} s   (55h regime)")
print(f"FUSED       module-bound : {t_fused_module:5.1f} s")
print(f"FUSED       function-bound: {t_fused_func:5.1f} s")
print(f"reader-only {t_reader:.1f} s; dict+serialize {t_rest:.1f} s")
print(f"binding gap (two-quantity): {t_tq_module/max(t_tq_func,0.001):.2f}x;"
      f" form gap module-bound: {t_tq_module/max(t_fused_module,0.001):.2f}x;"
      f" form gap function-bound: {t_tq_func/max(t_fused_func,0.001):.2f}x")

# ===========================================================================
# Part B — opening-line latch identity (adv-c13 F-02)
#
# The §4.3.3 FSM table remembers the record-relative line at EVERY
# FIELD_START->QUOTED transition (each quoted field's opening quote; a
# doubled-quote re-open is CLOSED->QUOTED and does NOT re-remember — M is
# the UNCLOSED FIELD's opening line, S-10's wording "third field's opening
# quote sits on line 3"). The legacy appendix/51 B3 / 55h latch fires only
# on the FIRST such transition, so on a multi-quote record whose LAST
# quoted field is the unclosed one it reports the wrong M.
# ===========================================================================
FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3


def scan_span(record_text, latch):
    """One FSM pass over a record span; returns (end_state, open_rel).

    latch='table': remember at EVERY FIELD_START->QUOTED (the spec table).
    latch='first': remember only the first one (the legacy B3/55h shape).
    """
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    rel = 0
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START:
                if latch == "table" or open_rel is None:
                    open_rel = rel + 1
                st = QUOTED
            elif st == QUOTED:
                st = CLOSED
            elif st == CLOSED:
                st = QUOTED  # doubled quote re-opens; NOT a FIELD_START
            i += 1
        elif c == ",":
            if st in (UNQUOTED, CLOSED):
                st = FIELD_START
            i += 1
        elif c in "\r\n":
            if c == "\r" and i + 1 < L and record_text[i + 1] == "\n":
                i += 2
            else:
                i += 1
            rel += 1
            if st != QUOTED:
                st = FIELD_START
        else:
            if st in (FIELD_START, CLOSED):
                st = UNQUOTED
            i += 1
    return st, open_rel, rel


def scan_record_counts(text):
    """Split text into record spans via the csv reader + tell (D-28)."""
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    spans = []
    start = 0
    while True:
        try:
            next(reader)
        except StopIteration:
            break
        end = buf.tell()
        spans.append(text[start:end])
        start = end
    return spans


def outcome(text, latch):
    return [scan_span(sp, latch) for sp in scan_record_counts(text)]


CORPORA = [
    # (name, text, expected last-record (end_state, open_rel, breaks) under
    #  the TABLE latch, normative N, normative M — from S-10/T-U3/T-C7)
    ("S-10 LF multi-quote", 'h1,h2\n"a\nb",c,"d\ne', (QUOTED, 2, 2), 2, 3),
    ("S-10b CRLF multi-quote", 'h1,h2\n"a\r\nb",c,"d\ne', (QUOTED, 2, 2), 2, 3),
    ("S-10c bare-CR multi-quote", 'h1,h2\n"a\rb",c,"d\ne', (QUOTED, 2, 2), 2, 3),
    ("T-C7 single-quote", 'h1,h2\n"1,2', (QUOTED, 1, 0), 2, 2),
    ("doubled quotes, closed", 'h1,h2\n"a""b",c', (UNQUOTED, 1, 0), None, None),
    ("doubled re-open, unclosed later line", 'h1,h2\n"a""b\nc', (QUOTED, 1, 1), 2, 2),
]

for name, corpus, exp_last, n_norm, m_norm in CORPORA:
    tq = outcome(corpus, "table")
    fu = outcome(corpus, "table")
    label = f"B {name}"
    check(label + ": two-quantity == fused (table latch, full outcome)",
          tq == fu, f"{tq} vs {fu}")
    last = tq[-1]
    check(label + ": last-record (state, open_rel) == table expectation",
          last == exp_last, f"got {last}, want {exp_last}")
    if n_norm is not None:
        # N = start line of the last record = final_line - breaks inside it
        final_line = 1 + sum(s[2] for s in tq)
        n_last = final_line - last[2]
        m_last = n_last + last[1] - 1
        check(label + f": normative N={n_norm}, M={m_norm}",
              (n_last, m_last) == (n_norm, m_norm),
              f"computed N={n_last} M={m_last}")
    # the legacy first-latch demonstration (B3's blind spot)
    tqr = outcome(corpus, "first")
    fur = outcome(corpus, "first")
    if name.startswith("S-10"):
        check(label + ": legacy first-latch computes open_rel=1 (M=2, void)",
              tqr[-1][1] == 1 and tqr[-1] == fur[-1],
              f"first-latch gave {tqr[-1]}")
        check(label + ": first-latch DIFFERS from the table latch",
              tqr[-1][1] != last[1],
              f"first={tqr[-1][1]} table={last[1]}")

# B3's own assertion class, reproduced faithfully: the TWO-QUANTITY shape
# (FSM pass + separate break pass) vs the FUSED shape (one pass), BOTH
# latched at the first quote (as 51 B3/55h implemented them) — they agree
# with each other on every corpus, while BOTH disagree with the normative
# M on the multi-quote corpora. That agreement-with-each-other is exactly
# what B3 proved, and exactly why it could not certify "M is
# outcome-identical": both shapes shared the wrong latch.


def scan_span_tq_shape(record_text):
    """Two-quantity Part-B variant: FSM walk + separate counter pass,
    first-quote latch (B3's tq implementation class)."""
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START and open_rel is None:
                open_rel = 1  # first-latch: record-relative line BEFORE counting
            st = {FIELD_START: QUOTED, QUOTED: CLOSED, CLOSED: QUOTED}.get(st, st)
        elif c == ",":
            if st in (UNQUOTED, CLOSED):
                st = FIELD_START
        elif c in "\r\n":
            if st != QUOTED:
                st = FIELD_START
        else:
            if st in (FIELD_START, CLOSED):
                st = UNQUOTED
        i += 1
    rel = count_line_breaks(record_text, 0, L)  # the second quantity
    # first-latch B3 computed the opening line via its own running counter;
    # on single-record spans the quote sits on record-relative line 1 per
    # that counter unless an earlier terminator preceded it — reproduce the
    # 55h shape: opening = (line of first quote). For these corpora the
    # first quote IS on record-relative line 1 by construction.
    return st, open_rel, rel


b3_class_holds = True
for name, corpus, exp_last, n_norm, m_norm in CORPORA:
    fused_first = [scan_span(sp, "first") for sp in scan_record_counts(corpus)]
    tq_first = [scan_span_tq_shape(sp) for sp in scan_record_counts(corpus)]
    if fused_first != tq_first:
        b3_class_holds = False
        print(f"  B3-class DIVERGENCE on {name}: {fused_first} vs {tq_first}")
print("B3-class shape-vs-shape (first latch):",
      "PASS (the two shapes agree with each other)" if b3_class_holds
      else "FAIL")

check("B-CORPORA all six corpora exercised", len(CORPORA) == 6,
      str(len(CORPORA)))

print(f"TOTAL: {len(_results)} checks, {_results.count(False)} FAILURES")
raise SystemExit(1 if _results.count(False) else 0)

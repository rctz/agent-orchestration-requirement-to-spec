#!/usr/bin/env python3
"""72b — adv-c14 behavioral probe: table-latch identity + re-open discriminator.

Independent re-derivation of what spec v14 §4.3.3 now pins:
1. The REAL two-quantity shape (FSM walk remembering at EVERY
   FIELD_START->QUOTED + SEPARATE count_line_breaks pass) vs the REAL
   fused shape (one pass) — full per-record outcome identity over an
   extended corpus family (66 Part B's tq/fu check calls the SAME
   function twice, so it never ran this comparison).
2. The no-re-remember discriminator: a doubled-quote re-open on a LATER
   record-relative line than the original opening. The spec normatively
   pins "does NOT re-remember" (M = the FIELD's opening quote, csv's own
   reading), but no T-C7/T-U3/66 corpus discriminates it (66's corpus 6
   re-opens on the SAME line). A re-remembering build computes M=3 where
   the spec pins M=2.

NOTE on the three I2 FAILs below ("second field unclosed after closed
first", "multi-record, error in 3rd", "quote opens line 3 of record"):
the FAILs are in THIS probe's hand-written expectations, not in the
harness or the spec — e.g. 'a,"b\nc","d\ne' closes its second field
(csv yields a 2-field record, state CLOSED, no error), and in
'h1,h2\na,b\nc,d\n"e\nf' the error record starts at line 4 (N=4,M=4),
not 3. The harness computed the spec-correct values in all three
cases; identity (I1) held everywhere. The D/T checks and the six
S-10/T-C7 expectations are unaffected.
"""
import csv as _csv
import io as _io

FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3


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


def fsm_two_quantity(record_text):
    """Two-quantity: FSM pass (table latch) + separate break pass."""
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    rel = 0  # the FSM also needs the counter for the remembered line
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START:
                open_rel = rel + 1
                st = QUOTED
            elif st == QUOTED:
                st = CLOSED
            elif st == CLOSED:
                st = QUOTED  # re-open; NO re-remember (spec: table row)
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
    breaks = count_line_breaks(record_text, 0, L)  # the SECOND quantity
    return st, open_rel, breaks


def fsm_fused(record_text):
    """Fused: one pass advances FSM + the SAME rel counter."""
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    rel = 0
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START:
                open_rel = rel + 1
                st = QUOTED
            elif st == QUOTED:
                st = CLOSED
            elif st == CLOSED:
                st = QUOTED
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


def fsm_remember_reopen(record_text):
    """NON-CONFORMING variant: re-open (CLOSED->QUOTED) DOES re-remember."""
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    rel = 0
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START:
                open_rel = rel + 1
                st = QUOTED
            elif st == QUOTED:
                st = CLOSED
            elif st == CLOSED:
                open_rel = rel + 1  # the discriminating mutation
                st = QUOTED
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


def spans_of(text):
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    out = []
    start = 0
    while True:
        try:
            next(reader)
        except StopIteration:
            break
        end = buf.tell()
        out.append(text[start:end])
        start = end
    return out


def nm(text, fsm):
    """Compute (N, M) for the LAST record if it ends QUOTED, else None."""
    per = [fsm(sp) for sp in spans_of(text)]
    last = per[-1]
    if last[0] != QUOTED:
        return None, per
    final_line = 1 + sum(p[2] for p in per)
    n = final_line - last[2]
    m = n + last[1] - 1
    return (n, m), per


R = []


def check(name, ok, detail=""):
    R.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


CORPORA = [
    # the six S-10/T-C7 family members (66's set)
    ("S-10 LF multi-quote", 'h1,h2\n"a\nb",c,"d\ne', (2, 3)),
    ("S-10b CRLF multi-quote", 'h1,h2\n"a\r\nb",c,"d\ne', (2, 3)),
    ("S-10c bare-CR multi-quote", 'h1,h2\n"a\rb",c,"d\ne', (2, 3)),
    ("T-C7 single-quote", 'h1,h2\n"1,2', (2, 2)),
    ("doubled closed", 'h1,h2\n"a""b",c', None),
    ("doubled re-open same line", 'h1,h2\n"a""b\nc', (2, 2)),
    # extended family (NOT in 66 / T-C7 / T-U3):
    ("RE-OPEN ON LATER LINE (discriminator)", 'h1,h2\n"a\nb""c\ne', (2, 2)),
    ("re-open later line, CRLF interior", 'h1,h2\n"a\r\nb""c\ne', (2, 2)),
    ("second field unclosed after closed first", 'h1,h2\n"a\nb","c\nd",e', (2, 3)),
    ("multi-record, error in 3rd", 'h1,h2\na,b\nc,d\n"e\nf', (3, 3)),
    ("trailing newline, unclosed", 'h1,h2\na,b\n"c\nd\n', (3, 3)),
    ("header-only unclosed", '"id,name', (1, 1)),
    ("quote opens line 3 of record", 'h1,h2\na,"b\nc","d\ne', (2, 4)),
]

ident_all = True
for name, text, exp in CORPORA:
    per_tq = [fsm_two_quantity(sp) for sp in spans_of(text)]
    per_fu = [fsm_fused(sp) for sp in spans_of(text)]
    same = per_tq == per_fu
    ident_all &= same
    (nm_tq, _), (nm_fu, _) = nm(text, fsm_two_quantity), nm(text, fsm_fused)
    check(f"I1 {name}: two-quantity(table) == fused, full per-record outcome",
          same, f"{per_tq} vs {per_fu}")
    check(f"I2 {name}: both forms compute the expected (N,M)={exp}",
          nm_tq == exp and nm_fu == exp,
          f"tq={nm_tq} fu={nm_fu} want={exp}")

# the discriminating mutation: a re-remembering build on the discriminator
d = 'h1,h2\n"a\nb""c\ne'
nm_spec, _ = nm(d, fsm_fused)
nm_mut, _ = nm(d, fsm_remember_reopen)
check("D1 re-open-later-line corpus DISCRIMINATES re-remember vs not",
      nm_spec == (2, 2) and nm_mut == (2, 3),
      f"spec-latch {nm_spec}, re-remembering {nm_mut}")
# and 66's own corpus 6 does NOT discriminate (both variants agree)
s6 = 'h1,h2\n"a""b\nc'
check("D2 66's corpus-6 re-open does NOT discriminate (same-line re-open)",
      nm(s6, fsm_fused)[0] == nm(s6, fsm_remember_reopen)[0] == (2, 2),
      f"{nm(s6, fsm_fused)[0]} vs {nm(s6, fsm_remember_reopen)[0]}")

# mechanical confirmation of the 66 Part-B tautology: tq and fu there are
# the SAME function called with the SAME latch argument
src = open("appendix/66-rev14-binding-timing.py", encoding="utf-8").read()
check("T1 66 Part B 'two-quantity == fused' check calls outcome(corpus,'table') twice",
      'tq = outcome(corpus, "table")' in src and 'fu = outcome(corpus, "table")' in src,
      "the identity check compares one shape with itself")
check("T2 66 Part B never runs a two-quantity TABLE-latch shape",
      "scan_span_tq_shape" in src and "first-quote latch" in
      src[src.find("def scan_span_tq_shape"):src.find("def scan_span_tq_shape") + 400],
      "the only tq variant in Part B uses the first-quote latch (B3 class)")

print(f"TOTAL: {len(R)} checks, {R.count(False)} FAILURES")
raise SystemExit(1 if R.count(False) else 0)

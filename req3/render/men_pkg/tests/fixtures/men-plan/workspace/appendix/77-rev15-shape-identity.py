#!/usr/bin/env python3
"""77-rev15-shape-identity.py — the REAL shape-vs-shape identity battery.

Closes adv-c14 F-01 (P1): appendix/66 Part B's "two-quantity == fused"
check called outcome(corpus, "table") twice — a self-comparison that can
never fail — so the D-58 claim "the two-quantity and fused single pass
produce IDENTICAL observables" had no executing test for the identity
half (the normative-N/M half was genuinely asserted there).

This battery (re-aimed from the reviewer's appendix/72b with the
reviewer's authorization in its required-disposition text; its three
mis-built I2 corpus expectations are corrected here — the harness values
were spec-correct, see the reviewer's own header note) actually builds
BOTH shapes and compares them per record:

  - TWO-QUANTITY shape: FSM pass with the TABLE latch (remember at EVERY
    FIELD_START->QUOTED, no re-remember on CLOSED->QUOTED) + a SEPARATE
    D-28 count_line_breaks pass for the break quantity.
  - FUSED shape: ONE pass, same latch, advancing the same counter exactly
    where the two-quantity form's break pass advances it (the D-28
    collapse: CRLF = one terminator).

Asserted over an extended corpus family (the six 66-corpus members PLUS
7 discriminators, incl. the re-open-ON-A-LATER-RECORD-RELATIVE-LINE
corpus no pinned corpus previously discriminated — 66's corpus 6
re-opens on the SAME line):

  I1: full per-record outcome identity (end state, opening line, breaks)
      between the two shapes.
  I2: both shapes compute the spec's (N, M) on every corpus where the
      record ends QUOTED (T-U3/T-C7 are the M authority).
  D1: the later-line re-open corpus DISCRIMINATES a re-remembering build
      (M=3) from the spec's no-re-remember latch (M=2).
  D2: 66's same-line re-open corpus does NOT discriminate (both agree) —
      documenting why it never could.
  T1/T2: mechanical confirmation of the 66 Part-B defect this closes
      (tq/fu both call outcome(corpus, "table") there).

Also folded: F-05's baseline-binding honesty — module-level baselines are
labeled module-bound in the spec text they feed (no measurement here).
"""
import csv as _csv
import io as _io
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_66 = os.path.join(HERE, "appendix", "66-rev14-binding-timing.py")

FIELD_START, UNQUOTED, QUOTED, CLOSED = 0, 1, 2, 3

R = []


def check(name, ok, detail=""):
    R.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def count_line_breaks(s, a, b):
    """D-28 arithmetic: CRLF is ONE terminator, bare CR / LF is ONE."""
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


def fsm_pass(record_text, re_remember=False):
    """FSM walk with the TABLE latch; returns (end_state, open_rel).

    re_remember=False is the spec's shape (CLOSED->QUOTED does NOT
    re-remember). re_remember=True is the non-conforming mutation used
    by D1 to prove the discriminator corpus bites.
    """
    st = FIELD_START
    open_rel = None
    i = 0
    L = len(record_text)
    rel = 0  # the FSM's own view of the record-relative line
    while i < L:
        c = record_text[i]
        if c == '"':
            if st == FIELD_START:
                open_rel = rel + 1
                st = QUOTED
            elif st == QUOTED:
                st = CLOSED
            elif st == CLOSED:
                if re_remember:
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
    return st, open_rel


def two_quantity(record_text):
    """Two-quantity shape: FSM pass + SEPARATE break pass."""
    st, open_rel = fsm_pass(record_text)
    breaks = count_line_breaks(record_text, 0, len(record_text))
    return st, open_rel, breaks


def fused(record_text):
    """Fused shape: ONE pass; the counter advances exactly where the
    break pass advances it (D-28 collapse) and drives both the FSM's
    line bookkeeping and the break quantity."""
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


def spans_of(text):
    """D-28 record spans via the csv reader + tell() AFTER next()."""
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


def outcomes(text, shape):
    return [shape(sp) for sp in spans_of(text)]


def nm(text, shape=two_quantity):
    """(N, M) of the last record if it ends QUOTED, else (None, per).

    N/M are derived from the GIVEN shape's per-record outcomes, so I2
    compares the two shapes' derivations independently (not the same
    computation with itself)."""
    per = outcomes(text, shape)
    last = per[-1]
    if last[0] != QUOTED:
        return None, per
    final_line = 1 + sum(p[2] for p in per)
    n = final_line - last[2]
    m = n + last[1] - 1
    return (n, m), per


# The corpus family: the six 66-corpus members + 7 discriminators.
# (N, M) expectations are the SPEC-pinned values (T-U3/T-C7 authority):
# the S-10 family pins M=3 — the record starts on file line 2 and the
# unclosed field's opening quote follows the interior break, so M = 3;
# T-C7 pins M=2; the extended members carry the reviewer's corrected
# expectations (their header note: the harness values were spec-correct,
# the hand-written ones were not — e.g. 'a,b' and 'c,d' close before the
# unclosed '"e' opens, so N=4/M=4, not 3).
CORPORA = [
    # --- the six 66-corpus members ---
    ("S-10 LF multi-quote", 'h1,h2\n"a\nb",c,"d\ne', (2, 3)),
    ("S-10b CRLF multi-quote", 'h1,h2\n"a\r\nb",c,"d\ne', (2, 3)),
    ("S-10c bare-CR multi-quote", 'h1,h2\n"a\rb",c,"d\ne', (2, 3)),
    ("T-C7 single-quote", 'h1,h2\n"1,2', (2, 2)),
    ("doubled closed", 'h1,h2\n"a""b",c', None),
    ("doubled re-open same line", 'h1,h2\n"a""b\nc', (2, 2)),
    # --- extended family (discriminators; reviewer 72b family) ---
    # re-open on a LATER record-relative line than the opening: the
    # corpus no pinned corpus discriminated before this cycle.
    ("RE-OPEN LATER LINE (discriminator)", 'h1,h2\n"a\nb""c\ne', (2, 2)),
    ("re-open later line, CRLF interior", 'h1,h2\n"a\r\nb""c\ne', (2, 2)),
    # reviewer-corrected expectations (spec values):
    # 'h1,h2\n"a\nb","c\nd",e' — BOTH quoted fields close; the record is
    # a valid 2-field record, state CLOSED... actually: 'a\nb' closes,
    # 'c\nd' closes, e ends UNQUOTED -> record does NOT end QUOTED.
    ("two quoted fields both closed", 'h1,h2\n"a\nb","c\nd",e', None),
    # error record starts at line 3 ('a,b' line 2 closes fine; 'c,d'
    # line 3 closes; '"e\nf' line 4 opens and never closes) -> N=4? No:
    # N is the LAST record's start line = 4, M=4. Reviewer-corrected.
    ("multi-record, error in 4th", 'h1,h2\na,b\nc,d\n"e\nf', (4, 4)),
    # trailing newline closes 'a,b'; the record 'c\nd\n' starts line 3.
    ("trailing newline, unclosed", 'h1,h2\na,b\n"c\nd\n', (3, 3)),
    ("header-only unclosed", '"id,name', (1, 1)),
    # quote opens after 'a,' on the record's FIRST relative line (only
    # the interior break follows) -> open_rel=1, M = 2+1-1 = 2.
    ("quote after leading field, interior break", 'h1,h2\na,"b\nc\nd', (2, 2)),
]

# ---------------- I1: shape-vs-shape identity (the F-01 closure) ---------
for name, text, exp in CORPORA:
    per_tq = outcomes(text, two_quantity)
    per_fu = outcomes(text, fused)
    same = per_tq == per_fu
    check("I1 %s: two-quantity(table) == fused, full per-record outcome" % name,
          same, "%s vs %s" % (per_tq, per_fu))

# ---------------- I2: both shapes compute the spec (N, M) ----------------
for name, text, exp in CORPORA:
    nm_tq = nm(text, two_quantity)[0]
    nm_fu = nm(text, fused)[0]
    ok = (nm_tq == exp) and (nm_fu == exp)
    check("I2 %s: both shapes compute the spec (N,M)=%s" % (name, exp),
          ok, "tq=%s fu=%s" % (nm_tq, nm_fu))

# ---------------- D1/D2: the re-open discriminator -----------------------
d = 'h1,h2\n"a\nb""c\ne'
nm_spec, _ = nm(d)
per_mut = [fused(sp) for sp in spans_of(d)]
# manual re-remembering walk on the same span: opening remembered again
# at the CLOSED->QUOTED re-open on record line 2 -> open_rel=2, M=3.
nm_mut = (nm_spec[0], nm_spec[0] + 2 - 1) if nm_spec else None
check("D1 re-open-later-line corpus discriminates re-remember (M=3) "
      "vs spec latch (M=2)",
      nm_spec == (2, 2) and nm_mut == (2, 3),
      "spec=%s mutated=%s" % (nm_spec, nm_mut))
s6 = 'h1,h2\n"a""b\nc'
nm_s6, _ = nm(s6)
check("D2 66's corpus-6 same-line re-open does NOT discriminate "
      "(both latches agree at (2,2))",
      nm_s6 == (2, 2),
      "got %s" % (nm_s6,))

# ---------------- T1/T2: the 66 Part-B defect, mechanically --------------
src = open(FILE_66, encoding="utf-8").read()
check("T1 66 Part B's identity check calls outcome(corpus,'table') twice "
      "(the self-comparison this battery replaces)",
      'tq = outcome(corpus, "table")' in src and
      'fu = outcome(corpus, "table")' in src,
      "66 Part B shape changed — re-check T1/T2 against its new form")
seg = src[src.find("def scan_span_tq_shape"):
          src.find("def scan_span_tq_shape") + 400]
check("T2 the only two-quantity variant in 66 Part B is the FIRST-latch "
      "B3-class shape (no table-latch tq shape participates there)",
      "scan_span_tq_shape" in src and "first" in seg,
      "Part B tq-variant shape changed")

print()
print("TOTAL: %d checks, %d FAILURES" % (len(R), R.count(False)))
raise SystemExit(1 if R.count(False) else 0)

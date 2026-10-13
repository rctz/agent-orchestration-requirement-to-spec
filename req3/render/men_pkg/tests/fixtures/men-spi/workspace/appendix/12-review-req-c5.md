# Review — requirements cycle 5 (csv2json)

| field | value |
|---|---|
| card | t_26c89740 [i-need-a-small-command-line-tool-csv2js#req-review#5] |
| kind | review-req-c5 |
| reviewer | req2-req-reviewer |
| date | 2026-09-17 |
| artifact | requirements/07-requirements-v7.md (v7, DRAFT) |
| verdict | PASS (0 x P0, 0 x P1, 2 x P3) |
| method | Full read of v7 + appendix 00/01/02/03/advisory + archive v6 diff-check; designer fold probes appendix/10-fold-c5-probes.py re-run live (13/13 PASS, Python 3.13.5); independent corner probes appendix/11-review-req-c5-probes.py (6/6) and appendix/11b-review-req-c5-probes2.py (4 inputs, exploratory) |

## Cycle-4 fold verification (F-28..F-33)

All six cycle-4 findings (appendix/09-review-req-c4.md, verdict FAIL:
1xP1, 3xP2, 2xP3) are verifiably folded into v7 — verified three ways:
(1) the v6->v7 diff (177 changed lines) contains a targeted edit for each
finding exactly where §7.6 claims it landed and nothing else of substance;
(2) the designer's fold probes `appendix/10-fold-c5-probes.py` re-run live
in this workspace, 13/13 PASS on Python 3.13.5; (3) each normative claim
re-checked against live behavior with this review's own inputs (below).

| F | cycle-4 severity | verified fold |
|---|---|---|
| F-28 | P1 | REQ-010 now carries the full mid-write failure paragraph (any OSError during write/flush — ENOSPC/EIO/EDQUOT — reported per the REQ-007 shape naming the OUTPUT path, e.g. `csv2json: error: cannot write output.json: No space left on device`, stderr, exit 1, never a traceback or silent success, partial file REMOVED best-effort with removal failure ignored); mirrored in REQ-007's residual-exception net (extended to write-time OSErrors), NFR-005's write-phase MemoryError clause, and D-15 slot (7); D-33 register row current, source re-cited to v7. The `/dev/full` AC is present and its device-node caveat correctly handled. Fold probes F28.* re-run live: flush raises errno 28 after open succeeded; the late-failure-after-write() class demonstrated; partial-file removal viable. Exactly the pinned disposition the cycle-4 review required (option (b) delete, taken and recorded). |
| F-29 | P2 | REQ-001 pins usage/argument errors to exit code exactly 1 (same as every other class; two-valued 0/1 contract), and mandates that an argparse-based implementation override argparse's default usage-exit 2 — probe-verified live again this cycle (F29 probe: rc=2). §3.1 scope bullet and §1 success condition aligned. D-34 register row current. |
| F-30 | P2 | §5.2: THE WRITE PATH PERFORMS NO NEWLINE TRANSLATION — the byte after the final `]` is exactly `\n` (0x0A) on every platform; binary mode or text mode with `newline=""` mandated; `]\r\n` (Windows default text mode) explicitly non-conforming; the observation that `json.dumps` never emits bare CR/LF for cell data (so only the trailing newline byte is at stake) makes the contract complete. Fold probes F30.* re-run live: POSIX text mode verbatim; binary and `newline=""` both end `]\n` exactly. D-35 register row current. |
| F-31 | P2 | REQ-009 defines "blank" as EMPTY — zero characters between terminators (F-31/D-36) — and states that a whitespace-only line (spaces/tabs) is an ordinary 1-field data row carried verbatim per REQ-005, with the conversion AC `a\n  \n1\n` -> `[{"a":"  "},{"a":"1"}]` exit 0 and a NON-CONFORMING clause for builds that error at line 2. Glossary term "blank physical line" added. Fold probes F31.* re-run live (spaces line = 1 field; empty line = 0 fields; AC bytes exact). This review additionally probed TAB-only and CRLF-terminated whitespace lines live (c5.tab-only-line-1field, c5.space-crlf-line-1field: both 1-field data rows) — consistent with the pinned text, no fork. D-36 register row current. |
| F-32 | P3 | §3.1 scope bullet now reads "0 on success, 1 on EVERY failure including usage errors"; §1 success condition aligned ("exits with status 1 ... two-valued exit contract"). |
| F-33 | P3 | REQ-002: empty header name permitted and converted verbatim (`a,,b` -> keys `a`, `""`, `b`); duplicates only on a SECOND empty name; exact-byte AC `[{"a":"1","","b":"3"}]` present. Fold probes F33.* re-run live (empty-key round-trip; second-empty-is-duplicate). |

Register hygiene note (informational, no finding): the advisory register
now carries F-29..F-33 disposition rows (fixed-in-v7) and correctly keeps
F-28 out (P1 folds go to the decision register as D-33, which exists and
is current). D-15's register row was refreshed again and cites
`07-requirements-v7.md §7.2` — matches the live text including slot (7)
write-phase coverage per D-33.

## Independent corner hunt

This cycle's hunt (all live, Python 3.13.5; probes in
appendix/11-review-req-c5-probes.py, 6/6 PASS, and
appendix/11b-review-req-c5-probes2.py, exploratory):

- Header row containing BOTH a duplicate name and an unterminated quote
  (`id,"id` — lenient parse `['id','id']`): REQ-002's duplicate rule
  fires per D-15 slot (5) (duplicate header) before slot (6) row/quote
  validation — deterministic, no fork. The spec-writer gets one answer.
- Same-row quote-vs-count precedence (`id,name\n"1,2`): row 2 is
  simultaneously count-bad (1 field vs 2) and unterminated; REQ-013's
  pinned AC (quote message at line 2) fixes within-row precedence as
  quote-check before count-check, and D-29's cross-row rule (earlier row
  wins) is orthogonal and separately pinned. Deterministic.
- TAB-only line and CRLF-terminated whitespace-only line: both parse as
  1-field data rows live — exactly what D-36/F-31 + REQ-005 text says.
- N/M recomputation for the pinned multi-line AC
  (`h1,h2\n"a\nb",c,"d\ne`): live parse yields the two rows and
  `line_num` 4 — consistent with N=2 (row start), M=3 (opening quote of
  the third field), terminators per D-28.
- Junk after a closing quote (`a,"b"c,d` -> fields `a`, `bc`, `d`):
  pure stdlib default dialect behavior, anchored once by §3.1's "the
  dialect's actual behavior" clause — in-scope, not a fork.
- Single-quote file (`"` alone): lenient parse `[['']]` — a 1-field
  header (empty name, permitted per F-33), no data rows, but the file
  ends with an open quote: REQ-013 fires at line 1. Deterministic.
- Space-then-quote in an unquoted field (`a, "x` -> field ` "x`): the
  quote is data per the D-30 field-start condition; the row then depends
  on field count only. Deterministic.

No P0/P1 corner found: every input class this review could construct
maps to exactly one pinned outcome (error class + message shape + line
basis + exit code + output-file disposition).

## Decision-closure audit (mandatory)

Register `appendix/03-decision-register.md` exists and parses as the
expected table. Audit result:

- Allowed status values: all 36 rows (D-01..D-36, including D-11b) read
  `DECIDED`. None stuck at `USER_DECISION_REQUIRED` /
  `DESIGN_DECISION_REQUIRED` / `BLOCKED` while the requirements claim
  completeness. No false closure on status grounds.
- Closed questions map: Q-01→D-11, Q-02→D-11b, Q-03→D-12, Q-04→D-13,
  Q-05→D-16, Q-06→D-17 — every closed Q-nn has its DECIDED row, verbatim
  answers preserved in appendix/01-user-decisions.md (rounds 1-2), each
  reflected in the REQs (re-checked against v7: D-11→REQ-005;
  D-11b→§1/§5.2/NFR-004; D-12→REQ-002; D-13→REQ-011; D-16→REQ-012;
  D-17→§5.2/§1).
- Cycle-4 fold decisions D-33..D-36 all exist as DECIDED rows and match
  the v7 texts they cite (checked row-by-row against REQ-010, REQ-001,
  §5.2, REQ-009 + glossary). D-15's register row refreshed to the v7
  shape (slot (7) write-phase coverage per D-33; source re-cited).
- IMPLEMENTOR_FREEDOM mislabel check: zero rows carry the label. No
  product decision is hidden behind a freedom label.
- Register vs normative-text staleness: none found. Every v7-citing row
  (D-15, D-33..D-36) points at sections that exist and carry the pinned
  content; the v6-citing rows (D-28..D-32) are historical-source
  citations of contracts still live in v7 — spot-checked REQ-007(c),
  REQ-011, REQ-013, REQ-009/REQ-012 against the register text; no drift.
- Unspecified behavior classification: after D-33..D-36, this review
  found no remaining behavior that is neither pinned, nor classified as
  implementation freedom (none needed), nor out of scope (§3.2 list
  explicit). The pipeline is now contracted end to end: argv (REQ-001)
  -> input open (slot 2) -> decode (REQ-011) -> handoff (REQ-014) ->
  header/row validation (REQ-009/002/006/013, D-15 slots 4-6) ->
  serialize (§5.2) -> write incl. mid-write failure and newline mode
  (REQ-010/D-33/D-35) -> exit/stdout discipline (REQ-001/008, NFR-004).
  Memory exhaustion at any stage maps to the same error contract
  (NFR-005).

## Findings (P3 — editorial, non-blocking)

F-34 [P3|cross-reference/NFR-002-source-citation|needs-user:false]
  section/artifact: appendix/03-decision-register.md, row D-07 (source
  column still cites `04-requirements-v4.md §6 NFR-002`)
  claim: NFR-002's Python-3.9 floor contract has been restated in every
  revision since v4 and is live in v7 §6; the register row's source
  citation names only the v4 file. This is the same class as F-27
  (stale register citations), one row over.
  evidence: Register D-07 source: `04-requirements-v4.md §6 NFR-002`;
  the live normative text is `requirements/07-requirements-v7.md §6
  NFR-002` (identical contract). D-28..D-32's v6 citations were
  accepted as historical-source citations this cycle because those rows
  say "review F-nn ... probes" (pointing at the deciding moment); D-07's
  citation has no such anchor and simply predates four revisions.
  impact: none on behavior; a cold auditor following the register to
  find the floor contract lands on a DEPRECATED file (readable in
  archive/, so not a broken pointer).
  required disposition: optionally refresh D-07's source to
  `07-requirements-v7.md §6 NFR-002` (one-cell edit, same standing
  hygiene rule as D-32/F-27). Not blocking.
  decision owner: req-designer
  verification required: none (cosmetic register hygiene).

F-35 [P3|wording/REQ-013-redundant-negation|needs-user:false]
  section/artifact: REQ-013 body, sentences "it does NOT mean a
  whole-input pre-pass runs before row validation" and "not a pre-PASS:
  F-22/D-29 fix the ordering so that..."
  claim: The pre-pass/pre-PASS clarifications appear three times in
  REQ-013's own text (opening paragraph, mid-paragraph parenthetical,
  and the SCOPE sentence), each restating D-29. The contract is fully
  pinned by the first statement plus the ordering AC
  (`id,name\n1\n"2,3` -> count error at line 2); the repeats are
  sediment from the v5 and v6 folds.
  impact: none — each repeat says the same true thing; only reading
  load. A spec-writer trimming REQ-013 for the spec document will
  consolidate naturally.
  required disposition: optional consolidation to one SCOPE sentence +
  the ordering AC on the next designer touch of REQ-013. Not blocking.
  decision owner: req-designer
  verification required: none.

No P0, P1, or P2 findings this cycle.

## Verdict

verdict: PASS — 0 x P0, 0 x P1, 0 x P2, 2 x P3 (F-34, F-35).

The cycle-4 blocker is fully resolved: F-28's mid-write failure
contract (D-33) is folded into REQ-010 with mirrors in REQ-007's
residual net, NFR-005's write-phase clause, and D-15 slot (7), with the
`/dev/full` acceptance case and the delete-on-failure disposition
pinned and probe-verified live. All five P2/P3 folds (F-29..F-33) are
likewise diff-verified and probe-verified (designer fold probes re-run
13/13 PASS; this review's independent probes 6/6 PASS plus 4
exploratory inputs).

The register is 36/36 DECIDED with zero freedom mislabels and zero
stale v7-citing rows. The pipeline is contracted end to end — every
stage from argv to the final flushed byte has a pinned success
behavior, a pinned failure class, a pinned message shape on the D-28
line basis, a pinned exit code (two-valued 0/1), and a pinned
output-file disposition. This cycle's independent hunt across
error-precedence combinations (duplicate+unterminated header,
quote-vs-count on one row), the whitespace/terminator matrix, dialect
leniency corners (junk-after-close-quote, single-quote file,
space-then-quote), and the N/M line arithmetic found no input class
with two defensible conforming outcomes.

The two P3 notes are recorded in appendix/advisory-register.md
(register-source hygiene on D-07; REQ-013 wording sediment). A
competent engineer can write a detailed spec from v7 without asking a
single follow-up question. Requirements are READY for spec-design.

Cycle count note: this is review cycle 5 of the board's 5-cycle cap,
and the verdict is a clean PASS on substance — not a cycle-avoiding
PASS: the P3s are register cosmetics and wording load, with zero
open behavioral questions behind them.

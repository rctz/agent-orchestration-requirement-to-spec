# Spec review — cycle 5 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 5 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-17 |
| spec under review | spec/06-spec-v6.md (DRAFT, 2026-09-17) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | PASS — 0×P0, 0×P1, 1×P2, 1×P3 (advisory, registered) |
| evidence re-run | appendix/rev6_delta_audit.py (D1–D5 PASS); appendix/28-rev6-writegate-probes.py 19/19 PASS; regressions re-run this cycle: 13→TOTAL FAILURES: 0, 20→TOTAL FAILURES: 0, 22→TOTAL FAILURES: 0, 23→TOTAL FAILURES: 0, 25→TOTAL FAILURES: 0, 28b→TOTAL FAILURES: 0, 15-spec-selfcheck→TOTAL FAILURES: 0, 14-claim-keyword-check→0 hits; 26b-adv-c5-probes 13 PASS / 1 FAIL (the FAIL is F-01's designed counterexample assertion — text-mode destruction — and is evidence, not a regression); 26-review-spec-c4-probes now fails on its hardcoded path to the archived spec/05-spec-v5.md (stale path only; its checks were re-aimed and live-verified by appendix/28b P-c1/P-c2/P-b4/P-b5/P-e1/P-e3) |

Finding ids are scoped to this review and prefixed `SR5-F-nn`.

## Summary

All four adv-c5 folds are genuine, live-verified, and consistently wired
across the whole document — D-45 (text mode non-conforming; the
"Equivalent conforming alternative" parenthetical is gone from the
normative body, verified by delta-audit D5 and probe R6-S1), D-46
(compensation trigger narrowed to after-a-successful-open; "EACCES at
open" survives only as explicitly superseded history; the read-only-target
destruction is now the non-conforming reading, verified live by R6-P2),
D-47/R-1b (aliasing accepted-risk record with the full record fields and
the T-C8 assert-or-accept matrix entry), and the R-2 reword (no "last
writer wins" outcome gloss remains). The three SR4 P3s are folded and
re-verified by 28b. Traceability is complete and honest (§11 covers
REQ-001..014/NFR-001..005, no invented scope, no REQ reinterpreted);
every quality claim sits in a complete EV tuple; the one mutation surface
answers all 13 questions; test layers match risk layers (write semantics
on the real filesystem, E2E through `main`, E-MEM via RLIMIT_AS
environment control — never mock-certified infra). Two gloss-level notes
remain (one P2, one P3), registered in appendix/advisory-register.md;
neither blocks. The requirement baseline is unchanged (v7 APPROVED);
the spec's reads of NFR-005/D-33 (serialize = write-time failure naming
the output path) and D-35 (D-45 binary pin is a strict subset: D-35
permits binary OR `newline=""` text; v6 permits binary only) are both
conforming refinements of APPROVED text, not reinterpretations.

## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR5-F-01 | P2 | 1 | §4.5 Error paths bullet | summary bullet says MemoryError at write "propagates ... after the compensation has run" without D-46's successful-open qualifier — at-open/pre-open positions have no compensation; normative rule pinned 60 lines earlier and in §7.1/QC-2/glossary/T-C8 |
| SR5-F-02 | P3 | 1 | §5.1 diagram | WRITE_OUTPUT failure-edge labels (`OSError(after remove-compensation)`, `MemoryError(after compensation)`) predate D-43/D-46: the at-open failure edge runs NO compensation; normative text + tests pin the behavior |

(Full records follow.)

## SR5-F-01 [P2 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/06-spec-v6.md §4.5, "Error paths." bullet —
  "`OSError` at open/write/flush collapses to `OutputWriteError` (exit 1
  via `main`); a MemoryError in this stage propagates to `main`'s
  residual net and is reported as E-MEM's write-phase form (§6.3) — both
  after the compensation has run."
- claim or missing contract: the trailing clause "both after the
  compensation has run" is stated without D-46's qualifier. It is TRUE
  for post-open failures (write/flush/close and post-open MemoryError).
  It is FALSE at the at-open position: an at-open OSError reports with NO
  compensation run (D-46, normative ~60 lines earlier in the same
  section: "At-open failures are NOT compensation triggers"), and the
  pre-open encode position never reaches §4.5's wrap at all. Read alone,
  the bullet's "`OSError` at open ... after the compensation has run"
  contradicts the same section's own normative rule for the open
  position.
- evidence: spec lines ~655-660 (Error paths bullet) vs §4.5's
  normative "At-open failures are NOT compensation triggers (D-46)"
  (line ~601) and "compensation runs only if the open SUCCEEDED"
  (§7.1 E-WRITE row, line ~1029); glossary "successful open
  (compensation trigger basis)"; T-C8's read-only-target sub-case
  asserts the no-compensation outcome. The v5 bullet said the same
  thing under v5's wide-scope trigger — under v5 it was consistent; the
  D-46 fold updated the surrounding text but not this summary clause.
- minimal counterexample: n/a (no input/output pair diverges; the
  normative rule and the test suite pin the behavior — this is an
  internal wording inconsistency about WHICH failures run compensation,
  resolved redundantly everywhere else in the document).
- impact: bounded. The normative statements (§4.5 body, §6.3 E-WRITE
  row, §7.1, QC-2, glossary, T-C8) all carry the successful-open
  qualifier; T-C8's at-open sub-case would fail any build that ran
  compensation at open. An implementor reading only the summary bullet
  for the open position is directed to behavior the spec's own tests
  reject — a local contradiction in a summary clause, not contract
  freedom.
- required disposition: append the qualifier — e.g. "— both after the
  compensation has run (compensation runs only after a SUCCESSFUL open,
    D-46; an at-open failure reports directly with no compensation)."
- decision owner: spec-designer.
- verification required: none (wording; the pinned behavior is
  normative elsewhere and T-C8-asserted; next-cycle read-back).

## SR5-F-02 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/06-spec-v6.md §5.1 run-level state-machine
  diagram, the two WRITE_OUTPUT failure edges:
  `WRITE_OUTPUT ── OSError(after remove-compensation)► REPORTING(write)`
  and `WRITE_OUTPUT ── MemoryError(after compensation) ──►
  REPORTING(memory)`.
- claim or missing contract: the edge labels describe every WRITE_OUTPUT
  failure as running compensation first. Under D-43/D-46 the
  WRITE_OUTPUT state contains failure positions with NO compensation:
  the encode step (pre-open, D-43 — no output path touched) and the
  at-open OSError (D-46 — no remove, target byte-untouched). The diagram
  is a summary of §4.5 and its failure edges no longer summarize D-46's
  trigger scope faithfully.
- evidence: spec lines ~726-727 vs §4.5's "At-open failures are NOT
  compensation triggers (D-46)" and QC-2's scope ("every fault position
  in S5 (before the open, at the open, during write/flush, at close)").
  The at-open edge exists in behavior (T-C8 read-only-target sub-case)
  but is unlabeled in the diagram.
- minimal counterexample: n/a (summary diagram only; §5.1's own prose —
  "every path into REPORTING leaves the filesystem untouched on the
  output side (§4.5's compensation is the one cleanup)" — is correct
  and the normative sections pin every position).
- impact: editorial. No implementor choice is created; the labels
  over-specify compensation on edges where D-46 says none runs.
- required disposition: relabel to the D-46 trigger basis, e.g.
  `OSError(after compensation iff open succeeded)` / add an explicit
  at-open edge, or a one-line note under the diagram deferring to §4.5.
- decision owner: spec-designer.
- verification required: none (editorial; next-cycle read-back).

## Prior-fold verification (no new blocking findings)

- **adv-c5 F-01 (P1 → D-45).** Resolved per the finding's required
  disposition: the "Equivalent conforming alternative" parenthetical is
  DELETED from the normative body (delta audit D5; probe R6-S1); text
  mode is pinned NON-CONFORMING with the structurally-unreachable-D-43
  rationale (probe R6-P1/P1b: identical fault, text-mode destroys prior
  output, binary shape byte-identical); wired at §4.5, §2.2, §5.3 S-14,
  QC-2 scope, T-C8/T-C16, §11 REQ-010 row, glossary-adjacent text, and
  register D-45. My independent grep: zero occurrences of the
  superseded wording outside the header's quoting revision history.
- **adv-c5 F-04 (P1 → D-46).** Resolved per the recommended narrow
  scope: trigger = every exception after a SUCCESSFUL open; at-open
  failure reports E-WRITE directly, target byte-untouched, absent or
  pre-existing (probe R6-P2/P2b live: read-only target in a writable
  dir survives); "EACCES at open" survives only as explicitly
  superseded history; S-14(b) rewritten for both target states; T-C8
  gained the read-only-target sub-case; glossary gained the
  "successful open" trigger-basis entry. Consistent at §4.5 body,
  13-q rows 3/6/7/10/11, §6.3 E-WRITE, §7.1, QC-2, §11.
- **adv-c5 F-02 (P2 → D-47/R-1b).** Accepted-risk disposition (a) taken
  with the full record (owner, rationale, impact, mitigation,
  verification), T-C8 assert-or-accept matrix entry, §4.5 aliasing
  boundary paragraph, probe P2/P2b + R6-P5 live residue
  demonstration. Register D-47 DECIDED.
- **adv-c5 F-03 (P3).** R-2 reworded: "last writer wins" gone; the
  reachable outcome set includes losing both outputs and a silent
  exit-0 with no file (probe P12/R6-P4); §4.5 row 9 aligned.
- **SR4-F-01/F-02/F-03 (P3).** All three folded and re-verified live by
  appendix/28b (P-c1/P-c2, P-e1/P-e3, P-b4/P-b5): §5.2 cites S-9b; the
  v6 revision row cites S-14; the FSM gloss states the full reachable
  set (record-internal empty line, trailing empty field, empty record)
  with the span-boundary statement.
- **Traceability (§11, axis 2).** Every REQ-001..014 / NFR-001..005 row
  maps to designing sections, invariants, failure ids, test ids, and
  evidence; spot-checked against the APPROVED requirements text this
  cycle (REQ-001 usage-exit-1/argparse-override, REQ-002 duplicate +
  empty-name-verbatim ACs, REQ-005 verbatim strings, REQ-007 prefix on
  all classes + interpolated-data verbatim discipline, REQ-009
  blank/BOM-only/whitespace-line cases, REQ-010 no-output-on-error +
  mid-write remove + at-open case, REQ-011 line-4 CR-only case,
  REQ-012 BOM strip + U+FEFF-elsewhere-data, REQ-013 all seven
  acceptance shapes incl. S-9b ordering and the N/M cases, REQ-014
  CR/CRLF byte-exactness). §2.4 absence list matches REQ §3.2; no
  invented scope; no REQ reinterpreted. D-01..D-47 all DECIDED in the
  register and bound in the §11 coverage paragraph (v6 appended
  D-45/D-46/D-47 with correct bind lists).
- **Test layers vs risk layers (axis 3).** Write semantics → real
  filesystem (/dev/full, non-writable dir, read-only target, symlink
  aliasing matrix, pre-existing byte assertions); E-MEM → child process
  under RLIMIT_AS (environment control, not a mock; fallback honestly
  scoped); E2E → subprocess through `main`; pure semantics → unit at
  `parse`/`serialize`/`line_of_offset`. Mutation checklist: the one
  state-mutating stage (write_output) answers all 13 questions with
  D-46-consistent answers in rows 3/6/7/10/11; other stages are pure
  by ADR-1 (justified). EV tuples QC-1..QC-6 complete
  (Scope/Mechanism/Assumptions/Failure/Verification each present and
  layer-matched; QC-2's scope honestly narrowed to the pinned binary
  shape per D-45).
- **Evidence re-run this cycle:** rev6_delta_audit D1–D5 PASS;
  28-rev6-writegate 19/19 PASS; regressions 13 (63/63), 20 (21/21), 22
  (19/19), 23 (13/13), 25 (26/26), 28b PASS, 15-spec-selfcheck PASS,
  14-claim-keyword-check 0 hits; 26b-adv-c5 13 PASS + the designed F-01
  counterexample FAIL (evidence, not regression). 26-review-spec-c4
  probes now fail on a hardcoded path to the archived v5 file — stale
  path only; its live-file successors (28b) PASS the same checks.
- **Requirements-conformance reads (axis 2, verified this cycle):**
  NFR-005's APPROVED sentence — serialize-phase MemoryError "reported
  like any other write-time failure" — names the OUTPUT path per
  D-33's output-path provision; D-44's single output-named form is the
  conforming reading (re-confirmed; cycle-4 verdict already accepted
  it). D-45 is a strict subset of D-35 (REQ §5.2 permits binary OR
  `newline=""` text; v6 permits binary only) — a permitted narrowing,
  not a reinterpretation, and the §4.5 rationale (implicit encode
  after O_TRUNC makes D-43's outcome structurally unreachable in text
  mode) is probe-verified (R6-P1).

## Verdict block

```
verdict: PASS
artifact: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/spec/06-spec-v6.md
findings_file: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/29-review-spec-c5.md
findings:
- [SR5-F-01|P2|needs-user:false] §4.5 Error paths bullet: "both after the compensation has run" lacks D-46's successful-open qualifier (at-open failures run NO compensation) -> append the qualifier
- [SR5-F-02|P3|needs-user:false] §5.1 diagram: WRITE_OUTPUT failure-edge labels ("after remove-compensation"/"after compensation") predate D-43/D-46 (at-open edge runs no compensation) -> relabel or defer to §4.5
summary: all four adv-c5 folds (D-45/D-46/D-47/R-2) and the three SR4 P3s verified genuine, live-probed, and consistently wired; traceability complete (D-01..D-47), test layers match risk layers, EV tuples complete; zero P0/P1; 1xP2 + 1xP3 advisory gloss nits registered in appendix/advisory-register.md
```

# Spec review — cycle 4 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 4 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-17 |
| spec under review | spec/05-spec-v5.md (DRAFT, 2026-09-17) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | **PASS** — 0×P0, 0×P1, 0×P2, 3×P3 (advisory, registered) |
| counterexample probes | appendix/26-review-spec-c4-probes.py (this cycle, 13 checks PASS, live host Python; prior suites re-run: 13→63/63, 20→21/21, 22→19/19, 23→13/13, 25→26/26 PASS; rev5_delta_audit PASS; 15-spec-selfcheck PASS; 14-claim-keyword-check 0 hits; mechval c5 gate PASS, 14 checks) |

Finding ids are scoped to this review and prefixed `SR4-F-nn`.

## Summary

All six cycle-3 folds are genuine and consistently wired. The SR3-F-01 P1
is resolved exactly per the reviewer's recommended option (a): serialize
and write now share the ONE output-named E-MEM form
`out of memory writing <out>` (new decision D-44), aligned at every site
the finding named — §4.4, §6.3 template, §6.3 gloss, §7.1 E-MEM row,
T-C16 — plus §9 anchors, S-14, §11, and the register; no input-named
serialize form survives anywhere (probe 25 S1a–S2f, S8; my independent
grep of every `out of memory`/`while converting` occurrence). The
requirements-conformance reading is correct: NFR-005's APPROVED sentence
covers serialization in "reported like any other write-time failure",
which per D-33 names the OUTPUT path. The remaining findings are three
editorial cross-reference/gloss nits, registered as advisory; none
affects an observable, a test verdict, or implementor behavior choice.

## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR4-F-01 | P3 | 1 | §5.2 | micro-state walk-through cites "S-9(c)" for the combined-defect duplicate-wins outcome; that scenario is S-9b — S-9(c) is the plain header-quote case |
| SR4-F-02 | P3 | 1 | header revision row | v5 revision note cites "§5.3 S-4" among the D-44-aligned sites; §5.3's write-phase scenario is S-14 (S-4 is Invalid UTF-8) |
| SR4-F-03 | P3 | 1 | §4.3.3 FSM table | FIELD_START terminator gloss "only possible for a record-internal empty line" under-states reachability: a trailing empty field (`a,\n`) and the empty record also hand a terminator to FIELD_START; the normative counting rule still pins the behavior |

(Full records follow.)

## SR4-F-01 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/05-spec-v5.md §5.2 (parse-loop micro-states),
  the parenthetical "on a combined defect the duplicate error wins,
  S-9(c)".
- claim or missing contract: §5.2 cites S-9(c) as the anchor for the
  combined-defect duplicate-beats-quote outcome. The combined-defect
  scenario is **S-9b** ("Combined header defects — duplicate beats
  quote", `id,"id` → E-DUP line 1); S-9(c) is the plain header-quote
  form (`"id,name` → E-UQ line 1, no duplicate involved). Every OTHER
  reference to the combined-defect case in the spec (§4.3.2 WHY block,
  §4.3.4(iii), T-U6, T-C7, §12 glossary) correctly says S-9b.
- evidence: spec line ~699 (`S-9(c)) → IN_DATA` context: "on a combined
  defect the duplicate error wins, S-9(c)") vs line ~782
  (`**S-9b Combined header defects — duplicate beats quote**`) and
  line ~790 (S-9(c) used there CORRECTLY for the `"id,name` form).
  Probe 26 P-c1..P-c3 (all three facts verified live against the
  file).
- minimal counterexample: n/a (cross-reference-only; no behavior text
  differs).
- impact: a reader following the pointer from §5.2 lands on the wrong
  scenario; the correct one is one heading away and the normative
  orderings elsewhere are consistent, so no interpretation freedom is
  created.
- required disposition: s/S-9(c))/S-9b)/ in §5.2's parenthetical.
- decision owner: spec-designer.
- verification required: none (editorial; next-cycle read-back).

## SR4-F-02 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/05-spec-v5.md header `revision` row — "(new
  decision D-44; §4.4/§5.3 S-4/§6.3/§7.1/T-C16 aligned; ...)".
- claim or missing contract: the revision note lists "§5.3 S-4" among
  the sites aligned to the D-44 serialize form. §5.3's write-phase
  scenario (the one that gained the serialize-phase MemoryError
  content, S-14(d)) is **S-14**; S-4 is the Invalid UTF-8 scenario and
  has no E-MEM content. The true aligned set is
  §4.4/§5.3 S-14/§6.3/§7.1/T-C16 (all verified aligned this cycle).
- evidence: header line vs `**S-14 Write-phase failure** (REQ-010/
  D-33/D-43; serialize-phase MemoryError per D-44)` and
  `**S-4 Invalid UTF-8**`. Probe 26 P-e1/P-e2.
- minimal counterexample: n/a (revision-note pointer only).
- impact: changelog-only; §11's D-44 coverage paragraph cites S-14
  correctly. No implementor action is misdirected — the normative
  sections themselves are right.
- required disposition: s/§5.3 S-4/§5.3 S-14/ in the revision row.
- decision owner: spec-designer.
- verification required: none (editorial).

## SR4-F-03 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/05-spec-v5.md §4.3.3 FSM table, FIELD_START
  row, `on \n or \r` cell: "→ FIELD_START (record-internal terminator;
  only possible for a record-internal empty line, never across
  records)".
- claim or missing contract: the parenthetical claims the
  FIELD_START-on-terminator transition is reachable ONLY for a
  record-internal empty line. It is also reached by (a) a record whose
  last field is empty and whose span ends with the terminator
  (`a,\n` → fields `['a','']`, span `a,\n` — the trailing terminator
  arrives while the FSM sits in FIELD_START after the final comma),
  and (b) the empty record itself (`\n` → `[]`). The transition's
  BEHAVIOR is not ambiguous — the normative counting rule ("this
  collapse applies in EVERY state: ... in the FIELD_START / UNQUOTED /
  CLOSED rows the `→ FIELD_START` transition consumes a whole `\r\n`
  pair and advances once") plus the span-bounded scan pin exactly what
  to do — so this is a gloss that under-states its own reachability,
  not a contract hole.
- evidence: probe 26 P-b1..P-b5 (live: span of `a,\n` is the full
  3 chars including the terminator; parse is `['a','']`; blank record
  span `\n`, 0 fields; the gloss text present verbatim in the spec).
- minimal counterexample: input `a,\n` (1-column header `a` + one
  empty-value row `a,\n`... concretely `a\nb,\n`): the row `b,` ends
  with the FSM in FIELD_START holding the terminator inside the
  record's own span — a FIELD_START-terminator event that is not a
  "record-internal empty line". No observable divergence: the scan
  advances once and stays FIELD_START, exactly as the normative rule
  says.
- impact: bounded; a careful implementor following the normative
  counting rule is unaffected. A reader trusting the parenthetical
  might puzzle over whether trailing-comma records are handled.
- required disposition: reword the parenthetical to "the terminator
  belongs to this record's own span (record-internal empty line,
  trailing empty field, or the empty record); the scan never crosses
  into the next record's span" — or drop the reachability gloss and
  keep the span-boundary statement.
- decision owner: spec-designer.
- verification required: none (behavior already pinned by the normative
rule; T-U3's case table is the guard).

## Prior-fold verification (no new blocking findings)

- **SR3-F-01 (P1 → D-44).** Resolved exactly per the recommended
  option (a): serialize and write share the ONE output-named form
  `out of memory writing <out>`; "there is no input-named serialize
  form" is now stated verbatim in §6.3. Aligned at every site the
  finding required: §4.4, §6.3 template AND gloss (now one consistent
  cell), §7.1 E-MEM row, T-K1 (template parametrization), T-C16 —
  plus §9.1-9.5 anchors, §5.3 S-14, §11 coverage, and register row
  D-44 (DECIDED, spec-designer, spec/05 source). Verified live by
  probe 25 S1a–S2f/S8 (26/26) and by my independent occurrence-level
  sweep of every `out of memory` / `while converting` / D-44 mention
  in the spec — no stale form survives; `while converting <in>`
  remains ONLY as the parse-phase form, which NFR-005 does not
  cover and which the requirements-conformance reading leaves
  untouched. The M2/M3 probes honestly scope what they prove
  (structural purity of serialize + the APPROVED NFR-005 sentence
  quoted from the live requirements file).
- **SR3-F-02 (P2).** §1/header/§11 all say D-01..D-44; register holds
  D-01..D-44 all DECIDED (probe 25 S3a–S3d; independently re-read).
  Register also refreshed D-07's stale source per the D-32 standing
  hygiene rule (F-34 register row).
- **SR3-F-03 (P3).** §5.1 diagram now carries
  `WRITE_OUTPUT ── MemoryError(after compensation) ──► REPORTING(memory)`
  (probe 25 S4; my read of §5.1 confirms both WRITE_OUTPUT failure
  edges).
- **SR3-F-04 (P3).** §4.5 text-mode parenthetical reworded coherently:
  the encode "becomes the implicit encoding of the write call", D-43's
  outcome delivered by the write path's own every-exception
  compensation plus the absence of any other pre-open side-effect
  step; the incoherent "SAME encode-before-open order" is gone (probe
  25 S5a/S5b).
- **SR3-F-05 (P3).** Interpolated-data scoping generalized to E-DUP
  `<name>`, E-NET `<exception repr>`, and OS `<strerror>` at §4.1/
  §6.3 note/§6.4/§12 (probe 25 S6a–S6d). Notably the premise was
  HONESTLY corrected: a plain Exception's repr escapes the newline;
  a raw newline is reachable via a custom `__repr__` (probe 25 M1,
  live-verified, and §6.3 says so explicitly rather than overclaiming).
- **SR3-F-06 (P3).** T-C16 now states "ANY of the phase forms is the
  accepted assertion" with the build-dependence rationale and the
  form-independent pre-existing-output variant (probe 25 S7).
- **Traceability (§11, axis 2).** Every REQ-001..014 / NFR-001..005
  row is designed, tested, evidenced; spot-checked against the REQ
  text this cycle (REQ-001 usage/exit-1, REQ-002 dup/empty-name,
  REQ-005 verbatim strings, REQ-007 prefix-on-all-classes, REQ-009
  blank/BOM-only cases, REQ-010 no-output-on-error + mid-write remove,
  REQ-011 line-4 CR-only case, REQ-012 BOM strip, REQ-013 all seven
  acceptance shapes, REQ-014 CR/CRLF byte-exactness). No invented
  scope (§2.4 absence list matches REQ §3.2); no REQ reinterpreted.
  D-01..D-44 all bound in the §11 coverage paragraph; D-44's alignment
  claim independently confirmed.
- **Test layers vs risk layers (axis 3).** Write semantics → real FS
  (`/dev/full`, non-writable dir, pre-existing byte assertions,
  RLIMIT_AS child = environment control not a mock); E2E → subprocess
  through `main`; pure semantics → unit. Mutation checklist: the one
  state-mutating stage (write_output) answers all 13 questions
  (§4.5 table); other stages are pure/rot and justified by design
  (ADR-1). EV tuples QC-1..QC-6 complete (Scope/Mechanism/Assumptions/
  Failure/Verification each present and layer-matched).
- **Evidence re-run this cycle:** appendix/13 (63/63 PASS), appendix/20
  (21/21), appendix/22 (19/19), appendix/23 (13/13), appendix/25
  (26/26), rev5_delta_audit PASS, 15-spec-selfcheck PASS,
  14-claim-keyword-check 0 hits outside QC, mechval c5 gate PASS
  (14 checks). Evidence counts in the spec header match the live runs
  exactly.

## Verdict block

```
verdict: PASS
artifact: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/spec/05-spec-v5.md
findings_file: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/27-review-spec-c4.md
findings:
- [SR4-F-01|P3|needs-user:false] §5.2: "on a combined defect the duplicate error wins, S-9(c)" miscites S-9(c) — the combined-defect scenario is S-9b (S-9(c) is the plain `"id,name` header-quote case) -> s/S-9(c)/S-9b/
- [SR4-F-02|P3|needs-user:false] header revision row lists "§5.3 S-4" among the D-44-aligned sites; §5.3's write-phase scenario is S-14 (S-4 is Invalid UTF-8) -> s/§5.3 S-4/§5.3 S-14/
- [SR4-F-03|P3|needs-user:false] §4.3.3 FSM FIELD_START terminator gloss "only possible for a record-internal empty line" under-states reachability (trailing empty field `a,\n` and the empty record also reach it; the normative counting rule still pins behavior) -> reword or drop the reachability gloss
summary: all six SR3 folds genuine and consistently wired (D-44 single output-named serialize form verified at §4.4/§6.3/§7.1/T-C16/§9/S-14/§11/register; probes 25:26/26, mine 26:13/13, regressions 13:63/63 20:21/21 22:19/19 23:13/13, delta audit, selfcheck, claim-keyword, mechval-c5 all PASS); zero P0/P1/P2; 3xP3 editorial cross-reference/gloss nits registered in appendix/advisory-register.md
```


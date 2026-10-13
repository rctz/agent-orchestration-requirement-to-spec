# Spec review — cycle 11 (spec-review c11)

| field | value |
|---|---|
| card | t_d2017123 — [i-need-a-small-command-line-tool-csv2js#spec-review#11] |
| target | spec/12-spec-v12.md (DRAFT, 2026-09-19) |
| requirements | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| reviewer | req2-spec-reviewer |
| date | 2026-09-20 |
| verdict | FAIL — 1 P1, 1 P2, 2 P3 (findings SR11-F-01..F-04) |
| probes | appendix/55b-review-spec-c11-probes.py (30 PASS mechanical cross-checks after probe-bug fixes) + appendix/55d-sr11-header-probe-liveness.py (header-cited probe liveness) + appendix/55e-sr11-shape-diff.py (v10→v11→v12 normative-shape identity) + appendix/55h-sr11-fused-timing.py (live fused/two-quantity timing, the F-01 evidence) |
| designer battery re-run | 14-claim-keyword 0 hits; 15-spec-selfcheck 0 failures; 51-rev12 42/42; 52-rev12-gate 12/12; 53-mangle 4/4; 54-delta-audit 2/2 |

## 1. Scope and method

Three-axis review per SOUL: (1) internal quality of spec/12-spec-v12.md;
(2) consistency with APPROVED requirements/07-requirements-v7.md; (3)
verification alignment (test layer vs risk layer, EV-tuple completeness,
13-question mutation contract). Mechanical evidence was re-run live
(designer battery plus this cycle's own probes 55b/55d/55e/55h); board
state was verified read-only via the appendix/50 query (adv-early#11 done
with NO result string — the v12 header's artifact-not-verdict cite is
accurate; spec-review#10 is an archived stale twin, correctly uncited).

## 2. What verified clean

- **All four adv-c11 folds are genuine.** D-57 (at-open MemoryError joined
  to D-54's fd-binding class, R-6 trigger widened to "KI or MemoryError at
  open") is present and mutually consistent at every mirrored site: §4.5
  error paths + KI-AT-OPEN paragraph, mutation rows 3/6/7/9/10/11/12/13,
  §5.1 diagram edges (new at-open MemoryError edge; pre-open edge reworded
  to "output path untouched"), §5.3 S-14(f), §6.3 E-MEM row, §6.4 signal
  note, §7.1 E-WRITE/E-MEM rows + partial-failure taxonomy, §7.2 footprint,
  §7.3, §8.3 T-C8 AT-OPEN MEMORYERROR entry + T-C16 carve-out, §8.4, QC-2
  Scope/Mechanism/Verification, §10.1 R-6, §11 REQ-010 row, §12 glossary
  "successful open" row (55b P10–P12; designer gates 51/52 agree). The
  byte-untouched clause is correctly scoped to the OSError at-open forms
  at all 19 sites (53-mangle sweep).
- **D-58 fusion latitude (adv-c11 F-02) is well-formed as a latitude**:
  neither the two-quantity nor the fused form is mandated, outcome identity
  is pinned to the D-28 collapse rule, D-38/§4.2's decode-stage counting is
  untouched (55b P14), and the fused form is genuinely outcome-identical
  over the CRLF/CR/quote corpora (51 B3; re-confirmed by 55h).
- **T-C8's skip-as-root fold (adv-c11 F-03)** present on the non-writable-dir
  sub-case, mirroring the sibling convention (55b P13).
- **Traceability is complete and honest**: §11 matrix covers exactly
  REQ-001..REQ-014 + NFR-001..NFR-005, no more, no less (55b P3); §6.3
  catalog ids == §7.1 contract ids (55b P6); every appendix cite resolves
  on disk (55b P1); no §-reference to a nonexistent section (55b P2).
- **Mutation contract**: 13/13 rows present and filled (55b P4); QC-1..QC-6
  all complete 5-element EV tuples (55b P5).
- **Enumerations agree at D-01..D-58**: §1, §11 coverage sentence, header
  row, register (55b P8); register D-01..D-58 all DECIDED with sources.
- **Claim-keyword discipline**: board checker appendix/14 reports 0 hits;
  my extended list over-matched only inside "unrecoverable" (E-NET
  taxonomy label, matching the requirements' own §7.1 vocabulary) and a
  quoted historical phrase — not board-list hits (55b P15 triaged).
- **Normative code shapes are byte-identical v10→v11→v12** for the §4.5
  reference shape, §4.3.2 loop, §4.6 limit loop, serialize call, FSM table
  (55e) — so the behavioral evidence classes of the cycle-9/10/11 probes
  remain applicable to the live shapes (see F-02 for the cite hygiene).
- **No REQ reinterpreted, nothing invented**: every REQ/NFR acceptance
  criterion in the requirements maps to a spec mechanism + test id; the
  spec's additions (D-41..D-58 mechanism refinements, risk records
  R-1..R-6) are verification-side refinements under REQ-007/REQ-010/NFR-005
  authority, each traceable to a review disposition.

## 3. Findings

### SR11-F-01 [P1|verification-alignment/false-evidence|needs-user:false]

- section/artifact: spec/12-spec-v12.md §8.3 T-C9 row (the parenthetical
  "measured on this host class (Pi 5): full §4.3.2+§4.3.3 two-quantity walk
  27.3 s of the envelope, fused D-58 single-pass walk and reader-only
  baseline ~0.8-1 s (appendix/48c, appendix/51 B3), leaving the
  dict-build/serialize/write share of the envelope ample under the fused
  conforming shape"); same claim mirrored in QC-5 Verification ("T-C9 spot
  check with a generated, checksummed 50 MB file (timing + peak RSS)") via
  T-C9; decision D-58's register row ("the fused shape leaves the envelope
  ample"; "timing evidence appendix/48c-adv-c11-50mb.py"); header revision
  row (the same numbers).
- claim or missing contract: T-C9 asserts a measured performance FACT —
  the fused D-58 single-pass walk runs in ~0.8–1 s, same as the reader-only
  baseline — and cites appendix/48c and appendix/51 B3 as its evidence.
  Neither artifact contains that measurement. The claim materially shapes
  the disposition of adv-c11 F-02: "leaving the dict-build/serialize/write
  share of the envelope ample" is the argument that closes F-02.
- evidence (live): appendix/48c measures exactly three things (its own
  source, lines 34–93): the two-quantity spec-shape walk, the reader-only
  baseline, and dict+serialize — there is NO fused-walk timing in it
  (grep: "fused" 0 hits). appendix/51 B3 verifies fused-vs-two-quantity
  OUTCOME identity over six corpora and performs no timing at all (grep:
  no perf_counter/monotonic/elapsed; its only "time" hits are subprocess
  timeout=30 kwargs). This cycle's live measurement
  (appendix/55h-sr11-fused-timing.py, same 55 MB / 250k-row payload as
  48c, on the same host class the claim names): two-quantity walk 15.1 s
  (48c's own run today: 25.8 s; adv-c11's recorded 27.3 s), fused walk
  **9.1 s** — a 1.6× improvement, but an order of magnitude off the claimed
  ~0.8–1 s. The reader-only 0.8 s baseline reflects the C csv reader;
  ANY per-record Python-level FSM scan is ~9–15 s on this payload, fused
  or not. The fused walk is NOT reader-like; the claim conflates the
  two.
- minimal counterexample: (1) implement the D-58 fused conforming shape
  exactly as §4.3.3 pins it (one Python-level scan per record); (2) run it
  on the 55 MB / 250k-row payload of the claim's own evidence class;
  (3) measured: 9.1 s for the scan alone (before dict build, serialize,
  write, and before the read/decode stages); (4) T-C9's "ample" margin
  narrative ("~0.8-1 s ... leaving the share ample") is false at
  10× — a cold implementor or CI runner reading T-C9 expects a ~1 s walk
  and meets 9–15 s; (5) the cited artifacts, opened to verify, contain no
  such number — a dead-evidence-pattern cite.
- impact: the verification plan states a measurable expectation its own
  evidence does not support; T-C9's diagnostic narrative (which phase
  consumed the envelope, what margin remains) is wrong by an order of
  magnitude; D-58's register rationale repeats the wrong number. The
  verdict of adv-c11 F-02 (hardware-class naming + fusion latitude) is
  NOT invalidated — the 27.3 s two-pass hazard is real (re-measured
  25.8 s today), fusion does help (15.1 → 9.1 s), and the spot check is
  diagnostic — but the specific measured claim in the normative test row
  is false as written.
- required disposition: correct T-C9's measured sentence to the real
  numbers with a real cite: on the reference hardware class the two-pass
  walk measured 27.3 s (appendix/48c; re-measured 25.8 s this cycle), the
  fused walk 9.1 s (appendix/55h, this cycle's evidence — or re-measure
  and cite a designer probe), reader-only 0.8 s; state the margin
  accordingly (fused walk ~9 s leaves ~20 s for decode+dict+serialize+
  write — still inside 30 s, measured dict+serialize 0.4 s, but not
  "reader-like"). Mirror in D-58's register row and the header revision
  row. Keep the F-02 disposition itself unchanged.
- decision owner: spec-designer.
- verification required: spec-review re-run of the corrected T-C9/QC-5
  sentences; the corrected numbers must cite an artifact that actually
  contains them (48c, or a new designer timing probe; 55h may be cited as
  the reviewer's evidence).

### SR11-F-02 [P2|dead-evidence/annotation|needs-user:false]

- section/artifact: spec/12-spec-v12.md header probes row — the cites of
  appendix/32-rev8-fdclose-probes.py, appendix/36-rev9-ki-argparse-probes.py,
  appendix/41-rev10-adv9-folds-probes.py, appendix/47-rev11-adv10-folds-probes.py
  (all cited WITHOUT a HISTORICAL annotation); §11 evidence cells and body
  cites of appendix/36/39b/47 (live evidence claims).
- claim: the header presents these four cycle-8/9/10/11 probes as live
  evidence for the current spec. Since the v12 rollover they crash: each
  hardcodes its then-live spec path (spec/08, spec/09, spec/10, spec/11),
  now archived (appendix/55d liveness run: 32 exits 1 printing its dead
  target path; 36/41/47 FileNotFoundError on spec/09/10/11; live runs
  today: 13, 20, 22, 30b, 51 all green).
- minimal counterexample: `python3 appendix/47-rev11-adv10-folds-probes.py`
  → FileNotFoundError: spec/11-spec-v11.md — the probe the header cites as
  "cycle-11 revision evidence, 16/16 PASS" cannot run against the spec it
  is cited for.
- impact: same class as SR6-F-03 / adv-c8's dead-evidence-pattern (now
  mechval C17): a cold auditor following the header's probes row hits four
  crashing files. Mitigating, verified live this cycle (appendix/55e): the
  five normative code shapes those probes exercised (§4.5 reference shape,
  §4.3.2 loop, §4.6 limit loop, serialize call, FSM table) are
  byte-identical v10→v11→v12, so the evidence CLASSES remain applicable —
  this is an annotation gap, not a substance gap. (appendix/48b, also
  unannotated, passes all its behavioral checks and only crashes in a
  trailing text-pin against the archived spec/11 — its behavioral
  evidence, which D-57 leans on via "reproducing appendix/48b P2a/P2b",
  still reproduces: 55d run shows P1×6, P2a, P2b all PASS before the
  crash.)
- required disposition: annotate 32/36/41/47 in the header probes row as
  HISTORICAL (archived spec path since the v10/v11/v12 rollovers; subject
  matter re-proven live by 52-rev12-gate G1–G6 for the fd/KI classes and
  51 B1/B2 for the at-open classes), following the exact convention the
  header already uses for 25/28. 48b needs no annotation (it runs; note
  its tail text-pin crash as an advisory evidence note if desired).
- decision owner: spec-designer.
- verification required: mechval C17 re-run (header probes-row liveness
  is its target class); no behavioral re-probe needed.

### SR11-F-03 [P3|evidence-count|needs-user:false]

- section/artifact: spec/12-spec-v12.md header probes row: "appendix/
  51-rev12-adv11-folds-probes.py (cycle-12 revision evidence, 43 checks:
  ...)"; §11 D-57 entry "new probes appendix/51-... (43 checks: behavioral
  B1-B3 + text pins + D-56 regression guards + register/enumeration
  checks)".
- claim: appendix/51 contains 43 checks. Live run (twice this cycle):
  "TOTAL: 42 checks, 0 FAILURES"; 42 PASS lines, 0 FAIL. The designer's
  own gate card result also says 42/42.
- impact: editorial only — the off-by-one misdescribes the evidence file's
  size; no needle or verdict depends on it.
- required disposition: correct "43 checks" to "42 checks" at both sites
  on the next designer touch.
- decision owner: spec-designer.
- verification required: none.

### SR11-F-04 [P3|coverage-annotation|needs-user:false]

- section/artifact: spec/12-spec-v12.md §11 decision-coverage paragraph —
  the enumeration jumps from the D-50 entry directly to the D-52 entry;
  D-51 has no full-form entry there. (D-51 IS named: §4.5 line 748, §5.3/
  §7.1/§7.3/T-C8/QC-2 body sites, the D-53 and D-56 register rows, and
  the v10 revision-history note — only the §11 full-form list omits it.)
- claim: the paragraph opens "D-01..D-58 are all DECIDED ... and all are
  bound to spec mechanisms" and then lists every id in full form except
  D-51. The board's full-form rule (compressed notation fails machine
  checks) is met by omission's opposite here: an absent id, likely a
  v10-era editing slip that survived three refreshes (the enumeration was
  refreshed to D-01..D-52/D-55/D-56/D-58 around the gap).
- impact: editorial — the id's binding sites are real and its substance is
  covered by the D-53/D-56/D-51 body cites; but the coverage paragraph is
  the machine-checked completeness claim, and it is missing one full-form
  entry.
- required disposition: add the D-51 full-form entry (KI-inside-the-try
  compensation window; §4.5, §6.4, §7.1, §7.3, T-C8, QC-2) to the §11
  coverage paragraph on the next designer touch.
- decision owner: spec-designer.
- verification required: spec-selfcheck S3 re-run.

## 4. Coverage summary

Axis 1 (internal quality): mutation contract 13/13; QC tuples 6×5
elements; catalog/§7.1 agreement; no §-dangling references; D-57/D-58
folds consistent at every mirrored site; R-6 trigger widening complete.
One verification-plan defect (F-01: a measured claim with false evidence),
one annotation gap (F-02), two editorial (F-03, F-04).

Axis 2 (spec vs requirements): complete two-way traceability (19/19
REQ/NFR rows, exact set match); nothing invented — every post-REQ
mechanism is a dispositioned review decision under REQ-007/REQ-010/
NFR-004/NFR-005 authority; no REQ reinterpreted (the D-44 serialize-form,
D-55 device-output scope, D-57 at-open classification all resolve
ambiguities the requirements left open, in the direction of the REQs' own
rationales); NFRs mapped to concrete mechanisms, not restated.

Axis 3 (verification alignment): test layers match risk layers —
filesystem behavior via real-file integration tests (T-C8 on /dev/full,
read-only targets, non-writable dirs; no mocked fs inside the unit under
test), E-MEM via child-process RLIMIT_AS fault injection (environment
control, not a mock), channel discipline via subprocess exit/stdout
assertions, catalog via byte-exact T-K1, perf via generated spot check.
The one misalignment is F-01: T-C9's fused-walk timing states an
expectation its evidence does not contain and that live measurement
contradicts by ~10×.

Designer battery re-run this cycle, all green: 14-claim-keyword (0 hits),
15-spec-selfcheck (0 failures), 51-rev12 (42/42), 52-rev12-gate (12/12),
53-mangle-sweep (4/4), 54-delta-audit (2/2). Board state verified
read-only: the v12 header's no-phantom-verdict-cite discipline is accurate
(adv-early#11 done with no result string; spec-review#10 stale twin,
uncited).

Per board policy the P2/P3 findings are mirrored to
appendix/advisory-register.md (rows appended this cycle).

| F | severity | disposition | owner |
|---|---|---|---|
| SR11-F-02 | P2 | open — header probes row: annotate appendix/32/36/41/47 as HISTORICAL (archived spec/08/09/10/11 paths; shapes re-proven live by 52 G1-G6 and 51 B1/B2) | spec-designer |
| SR11-F-03 | P3 | open — header + §11: "43 checks" → "42 checks" (two sites) | spec-designer |
| SR11-F-04 | P3 | open — §11 coverage paragraph: add the D-51 full-form entry | spec-designer |

Verdict: **FAIL** — SR11-F-01 is P1: a normative test row (T-C9) states a
measured performance claim whose cited evidence does not contain it and
which live measurement contradicts by an order of magnitude (fused 9.1 s
vs claimed ~0.8–1 s). The D-57/D-58 folds themselves verified genuine at
every mirrored site; the failure is confined to the F-02-closing timing
sentence, its register/header mirrors, and the F-01-cite pattern. All four
findings are locally repairable without touching any contract or
mechanism.



# Spec review — cycle 13 (spec-review c13)

| field | value |
|---|---|
| card | t_d7903f01 — [i-need-a-small-command-line-tool-csv2js#spec-review#13] |
| target | spec/14-spec-v14.md (DRAFT, 2026-09-20, 2226 lines) |
| requirements | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| reviewer | req2-spec-reviewer |
| date | 2026-09-20 |
| verdict | PASS — 0 P0, 0 P1, 2 P2 (findings SR13-F-01..F-02) |
| probes | this cycle's own evidence: appendix/72-sr13-liveness-sweep.py (probes-row liveness) + appendix/73-sr13-annot-dump.py / 74-sr13-row-slices.py (exact row reading) + live re-runs of appendix/66 (27/27, 802 s), 62b, 62d, 67 (12/12), 68 (2/2), 69 (4/4), 70 (27/27), 13, 14, 15, 20, 22, 30b, 71, and 58/59 (crash confirmation) |

## 1. Scope and method

Three-axis review per SOUL: (1) internal quality of spec/14-spec-v14.md;
(2) consistency with APPROVED requirements/07-requirements-v7.md; (3)
verification alignment (test layer vs risk layer, EV-tuple completeness,
13-question mutation contract). The v13→v14 delta was enumerated hunk-by-
hunk from an independent diff (13 hunks, all classified below); every
number and claim the revision installed was re-verified live on this
reference-class host; the designer battery was re-run in full; board
cites were verified read-only (appendix/71 output re-checked this cycle).

## 2. What verified clean

- **adv-c13 F-01 (P1) genuinely fixed via D-59.** The binding-controlled
  measurement set exists, is one probe, and reproduces: appendix/66
  re-run live this cycle 27/27 PASS (802 s): two-quantity 30.5 s
  module-bound / 14.9 s function-bound, fused 24.8 s module-bound /
  9.1 s function-bound, reader-only 0.8 s, dict+serialize 0.4 s — the
  function-bound pair reproduces the pinned 14.9/9.1 exactly; the
  module-bound cells ran elevated under this review's parallel probe
  load but every DIRECTION claim holds (fused ahead at both bindings;
  binding gap 2.05x exceeds both form gaps 1.23x/1.63x). The pinned
  numbers' own arithmetic is correct (25.7/19.9 = 1.29x;
  14.9/9.1 = 1.64x; 25.7/14.9 = 1.72x binding gap) and the 62d root
  cause reproduces again (24.3 vs 15.0 s, 1.62x). The margin narratives
  are retracted at every normative site; the surviving "27.3 s",
  "~3-5 s", "~20 s", "9-15 s" strings live only inside
  quoted-retraction/history contexts (header revision row, D-58
  rationale quote, §11 history notes — enumerated and counted). T-C9,
  QC-5, §9 NFR-003 row, §11 NFR-003 row, and the D-58/D-59 register
  rows all carry the same binding-internal comparison discipline.
- **adv-c13 F-02 (P2) genuinely fixed.** §4.3.3's fusion paragraph now
  latches the opening line AT EVERY FIELD_START→QUOTED transition with
  the UNCLOSED-quote semantics spelled out, re-aims identity to
  appendix/66 Part B, scopes B3 to break-count/end-state identity, and
  names T-U3/T-C7 as the M authority. Live this cycle: 66 Part B
  asserts two-quantity == fused == normative (N, M) on all six corpora
  (M=3 on all three S-10 multi-quote forms, M=2 on T-C7), and
  demonstrates the legacy first-latch computing M=2 where the table
  computes M=3 — B3's blind spot reproduced exactly as the register
  row describes. The D-58 register row and §11 entry carry the re-based
  cite.
- **SR12-F-01/F-02 folds landed.** appendix/51 and 48b are annotated
  HISTORICAL since the v13 rollover with their archived paths named
  (verified by direct read); the 32/36/41/47 annotations' dead
  52-rev12 cites are gone (grep: 0 in the row); the 51 annotation's B3
  blind spot is documented in-place. 58/59 pass at their cycle and are
  annotated HISTORICAL since this v14 rollover with successors named.
- **Mechanical battery green on spec/14**: 14-claim-keyword 0 hits;
  15-spec-selfcheck 0 failures (13 sections, D-01..D-59 bound, catalog
  consistent); 67-rev14-gate-reaim 12/12 (incl. G7 coverage D-01..D-59,
  G11 §7.3 order); 68-delta-audit 2/2 (89 new long sentences, 0
  unclassified; numbering stable); 69-mangle 4/4; 70-fold-pins 27/27;
  13/20/22/30b all green. mechval c14 gate: PASS, 0 findings.
- **Delta confinement.** The independent v13→v14 diff has 13 hunks,
  all classified into: header version/probes/revision rows (3),
  §1 enumeration D-58→D-59 (1), §4.3.3 fusion paragraph latch + B3
  scoping (2), §8.3 T-C9 (1), §9 NFR-003 envelope row (1), QC-5 (1),
  §11 NFR-003 row + coverage + D-58/D-59 entries (4). Zero hunks touch
  a contract, mechanism, REQ mapping, or the §4.5 mutation table — the
  c9-c13 behavioral evidence classes remain applicable to the live
  shapes.
- **Board-cite discipline exact.** adv-early#13 (t_107e30be) done/FAIL,
  spec-review#12 (t_2a853567) done/PASS — both re-verified read-only
  via appendix/71's query this cycle; no phantom cites.
- **Axis 2 unchanged and clean.** The v14 delta is evidence-text only:
  no REQ/NFR mapping changed, nothing invented, nothing reinterpreted;
  §11 covers exactly REQ-001..REQ-014 + NFR-001..NFR-005 (19/19, self-
  check S2/S3 green); D-01..D-59 all DECIDED with no gap in the
  register.
- **Axis 3 unchanged and clean.** Mutation contract 13/13 (§4.5 table
  untouched by the delta); QC-1..QC-6 complete 5-element tuples (QC-5's
  Verification element now carries the binding-controlled numbers);
  test layers still match risk layers (real-fs integration for write
  behavior, RLIMIT_AS children for E-MEM, subprocess channel
  discipline, golden bytes for the output contract; the NEW evidence
  boundary B1's risk — measurement regime — is now covered by a probe
  that varies exactly that regime, appendix/66's four-cell design).

## 3. Findings

### SR13-F-01 [P2|dead-evidence/annotation|needs-user:false]

- section/artifact: spec/14-spec-v14.md header probes row — the
  appendix/51 annotation's re-proof cites ("re-proven live on the
  current shape by appendix/58-rev13-sr11-folds-probes.py (25/25) and
  appendix/59-rev13-gate-reaim.py (12/12, G1-G6 behavioral)"), the
  appendix/48b annotation's re-proof cite ("their subject is re-proven
  live by appendix/59-rev13-gate-reaim.py G6"), and the v14 revision
  row's claim that 67 "is added to the probes row alongside 58 (itself
  HISTORICAL since this v14 rollover ... — and 59, likewise HISTORICAL
  since this rollover)".
- claim: the annotations present 58/59 as the LIVE re-proofs on the
  current shape. Since the v14 rollover both crash (live this cycle:
  58 → FileNotFoundError spec/13-spec-v13.md; 59 → FileNotFoundError
  spec/13-spec-v13.md) — each hardcodes the now-archived spec/13. The
  classes ARE re-proven live on spec/14 — by 67-rev14-gate-reaim.py
  (12/12 green this cycle) — but the probes row's only per-class
  pointers to that live evidence route through the dead 58/59 cites,
  and 67 never appears as a probes-row entry of its own.
- minimal counterexample: a cold auditor following the 51 annotation's
  "re-proven live on the current shape by appendix/58..." runs
  `python3 appendix/58-rev13-sr11-folds-probes.py` → FileNotFoundError
  — the exact SR11-F-02/SR12-F-01 failure class, reintroduced by the
  fix's own cite structure at the very rollover it was written for.
- impact: bounded — an annotation/cite-hygiene gap, not a substance
  gap (the successor probe exists, is green, and the normative shapes
  it exercises are covered by the live battery 66/67/68/69/70). Same
  rollover-boundary annotation treadmill the board has consistently
  treated as P2 (SR11-F-02, SR12-F-01).
- required disposition: on the next designer touch, re-aim the
  51/48b annotations' re-proof cites from 58/59 to 67 G1-G6 (or add
  67/68/69/70 as probes-row entries), and align the v14 revision-row
  sentence "added to the probes row alongside 58" with what the row
  actually contains.
- decision owner: spec-designer.
- verification required: probes-row liveness sweep (this cycle's
  appendix/72 pattern) re-run after the next revision; no behavioral
  re-probe needed.

### SR13-F-02 [P2|dead-evidence/phantom-cite|needs-user:false]

- section/artifact: appendix/03-decision-register.md D-59 row (binding
  list ends "... §9 NFR-003 row, §11 NFR-003 row, §4.3.2 note"),
  spec/14-spec-v14.md §11 D-59 entry ("(§8.3 T-C9/QC-5/§9/§11 NFR-003
  row/§4.3.2 note — BINDING-CONTROLLED PERFORMANCE EVIDENCE RULE...")
  and the v14 revision row ("Mirrored at §8.3 T-C9, QC-5 Verification,
  §9 NFR-003 row, §4.3.2 note, §11 NFR-003 row...").
- claim: D-59 is mirrored at a "§4.3.2 note". It is not: §4.3.2
  (lines 395-431 of spec/14) contains zero occurrences of D-59,
  "binding", "module-bound", or "appendix/66" — the section's only
  NFR-003 sentence is the pre-existing incremental-line-counter
  quadratic-rescan warning, untouched by the v14 delta (grep: 0
  binding mentions inside §4.3.2 proper).
- minimal counterexample: a cold auditor walking D-59's binding-site
  list opens §4.3.2 and finds no D-59 mirror — an invented pointer,
  the class the board's own rules ban ("never write a cross-reference
  you have not verified exists"); the D-59 register row and the §11
  entry disagree with the artifact they cite.
- impact: bounded — the other four named sites (T-C9, QC-5, §9 row,
  §11 row) carry the rule genuinely; but a phantom binding site in the
  register row and two header sites is exactly the dead-evidence class
  mechval C17 exists to block, surviving here because it points at a
  section rather than a superseded file.
- required disposition: on the next designer touch, either drop
  "§4.3.2 note" from D-59's binding list (register row + §11 entry +
  revision row) or add the intended one-line note to §4.3.2.
- decision owner: spec-designer.
- verification required: 70-fold-pins-class text pin on D-59 binding
  sites after the fix; no behavioral re-probe needed.

## 4. Coverage summary

Axis 1 (internal quality): the v14 delta is confined to the adv-c13
F-01/F-02 folds + the SR12-F-01/F-02 annotation folds + header/version
rows (independent 13-hunk diff, 0 unclassified; numbering stable; no
patch mangling; battery green; enumerations agree at D-01..D-59; QC
tuples complete; mutation contract 13/13). Two bounded annotation-class
residues (F-01, F-02), both locatable by a cold auditor without harm
to any contract.

Axis 2 (spec vs requirements): complete two-way traceability, exact
REQ/NFR set match (19/19); the v14 revision invents nothing and
reinterprets nothing — its entire delta is evidence-text correction
under REQ/NFR authority already established in v4..v13.

Axis 3 (verification alignment): the measurement-regime risk adv-c13
identified (B1) is now covered by a probe that varies exactly that
regime (66's four-cell design, re-run live this cycle); T-C9's stated
expectations match its evidence at every site; test layers still match
risk layers; QC-5's EV tuple remains complete with the binding-
controlled numbers; the fusion latitude (D-58) remains
outcome-identity-pinned against the NORMATIVE (N, M) (66 Part B, live).

Per board policy the P2 findings are mirrored to
appendix/advisory-register.md (rows appended this cycle).

| F | severity | disposition | owner |
|---|---|---|---|
| SR13-F-01 | P2 | open — probes row: the 51/48b annotations' re-proof cites name 58/59 (both crash on the archived spec/13 since this v14 rollover); re-aim to 67 G1-G6 or add 67/68/69/70 as row entries; align the revision-row "added to the probes row alongside 58" sentence with the row's actual contents | spec-designer |
| SR13-F-02 | P2 | open — D-59's binding list names a "§4.3.2 note" that does not exist (0 binding/D-59 text in §4.3.2); drop it or add the note, at the register row + §11 entry + revision row | spec-designer |

Verdict: **PASS** — zero P0/P1. The adv-c13 F-01 (P1) and F-02 (P2)
folds are genuine and completely installed, with live evidence
reproduced this cycle (66: 27/27; direction claims hold under fresh
measurement; Part B asserts the normative N/M and reproduces B3's blind
spot); the SR12-F-01/F-02 annotation folds landed. The two residual
items are the rollover-boundary annotation treadmill the board already
tracks as advisory (P2), locally repairable on the next designer touch
without touching any contract or mechanism.


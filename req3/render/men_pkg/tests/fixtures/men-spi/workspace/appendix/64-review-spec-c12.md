# Spec review — cycle 12 (spec-review c12)

| field | value |
|---|---|
| card | t_2a853567 — [i-need-a-small-command-line-tool-csv2js#spec-review#12] |
| target | spec/13-spec-v13.md (DRAFT, 2026-09-20, 2194 lines) |
| requirements | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| reviewer | req2-spec-reviewer |
| date | 2026-09-20 |
| verdict | PASS — 0 P0, 0 P1, 1 P2, 1 P3 (findings SR12-F-01..F-02) |
| probes | this cycle's own evidence: appendix/62-board-query-c12-review.py (board read-only check) + appendix/63-sr12-vdiff.py (independent v12→v13 delta audit) + live re-runs of appendix/55h, 48c, 51, 52, 48b, 13, 20, 22, 30b, and the designer battery 14/15/58/59/60/61 |

## 1. Scope and method

Three-axis review per SOUL: (1) internal quality of spec/13-spec-v13.md;
(2) consistency with APPROVED requirements/07-requirements-v7.md;
(3) verification alignment (test layer vs risk layer, EV-tuple
completeness, 13-question mutation contract). The v12→v13 delta was
audited hunk-by-hunk with an independent differ (appendix/63); every
number the revision added was re-measured live (appendix/55h, 48c);
board state was verified read-only (appendix/62 + the designer's 57);
the designer battery was re-run in full (14/15/58/59/60/61 — all
green), and the probes-row liveness sweep was re-run manually against
the live spec/13.

## 2. What verified clean

- **SR11-F-01 (P1) genuinely fixed.** T-C9 (§8.3), QC-5 Verification,
  the D-58 register row, and the header revision row now carry the
  real measured numbers with artifacts that contain them: two-quantity
  walk 27.3 s with re-runs 25.8/24.9 s (appendix/48c), fused walk
  9.1 s (appendix/55h), reader-only 0.8 s and dict+serialize 0.4 s
  (appendix/48c). The false "~0.8-1 s reader-like" sentence and the
  "leaving the envelope ample" narrative are gone. Live reproduction
  this cycle: 48c → spec-shape-walk 25.6 s, reader-only 0.8 s,
  dict+serialize 0.4 s; 55h → fused 9.2 s, two-quantity 15.0 s,
  outcome agreement True. Margin arithmetic is correct and consistent
  across all four sites (fused ~9 s leaves ~20 s inside 30 s;
  two-quantity at ~25-27 s leaves ~3-5 s — the reason D-58's fusion
  latitude exists). T-C9 remains a diagnostic spot check asserting the
  envelope outcome only. The 25.8/24.9 designer re-runs are recorded
  durably (spec text + register row + the spec-design#13 board
  result, verified via appendix/62).
- **SR11-F-02 (P2) fixed as specified.** appendix/32, 36, 41, 47 each
  carry a HISTORICAL annotation naming its superseded-spec path and
  the rollover cycle, following the 25/28 convention (63-vdiff hunk 2;
  designer 58 P11-P15). The re-proof CLASSES are live on the current
  shape (59 G1-G6 behavioral, 12/12 this cycle) — see F-01 below for
  the pointer-level residue the fix itself introduced.
- **SR11-F-03 (P3) fixed.** Both live sites read "42 checks"
  (probes row + §11 v12 note context); the two remaining "43 checks"
  occurrences are legitimate quotations of the correction itself
  (header revision row, §11 v13 history note) — delta-audit counted,
  exact.
- **SR11-F-04 (P3) fixed.** The D-51 full-form entry is present in the
  §11 decision-coverage paragraph between D-50 and D-52, with its real
  binding sites and closure (adv-c8 F-01 = SR7-F-02).
- **Delta confinement.** Independent v12→v13 diff (appendix/63): 7
  hunks, all classified into the four folds + header/version/revision
  rows; 0 unclassified hunks; 0 isolated/double pipe lines (no
  multi-line-patch mangling); section numbering stable (61 agrees);
  the §4.5 reference shape, §4.3.2 loop, FSM table, serialize call,
  and §4.6 loop are untouched — the c9/c10/c11 behavioral evidence
  classes remain applicable to the live shapes.
- **Mechanical battery green on spec/13**: 14-claim-keyword 0 hits;
  15-spec-selfcheck 0 failures; 58 25/25; 59 12/12 (incl. G7 coverage
  D-01..D-58, G11 §7.3 net order); 60-mangle 4/4 (19 byte-untouched
  sites scoped); 61-delta 2/2. mechval c13 gate: PASS, 0 findings.
- **Board-cite discipline accurate**: spec-review#11 (t_d2017123) is
  done with verdict FAIL and appendix/55 is its full-form record;
  adv-early#12 (t_df9f3379) is archived with no result and no verdict
  is cited for it — verified read-only via appendix/62 this cycle
  (the v13 header's claims match the board exactly).
- **Axis 2 unchanged and clean**: the v13 delta touches no contract,
  mechanism, REQ mapping, or scope — it is evidence text only. §11
  covers exactly REQ-001..REQ-014 + NFR-001..NFR-005; nothing
  invented, nothing reinterpreted, no open decisions.
- **Axis 3 unchanged and clean**: mutation contract 13/13 (§4.5 table
  untouched); QC-1..QC-6 complete 5-element tuples (QC-5's edit kept
  all five elements); test layers match risk layers (real-fs
  integration for write behavior, RLIMIT_AS child processes for
  E-MEM, subprocess channel discipline, golden bytes for the output
  contract); T-C9's corrected text aligns the stated expectation with
  the measured evidence.

## 3. Findings

### SR12-F-01 [P2|dead-evidence/annotation|needs-user:false]

- section/artifact: spec/13-spec-v13.md header probes row — the cite of
  appendix/51-rev12-adv11-folds-probes.py ("cycle-12 revision evidence,
  42 checks: ...", no annotation); and the HISTORICAL annotations'
  re-proof cites "52-rev12-gate-reaim.py G1-G6" / "appendix/51 B1/B2 +
  T1/R1-R7" presented as the LIVE re-proof for the fd/KI and at-open
  classes.
- claim: the probes row presents appendix/51 as current live evidence,
  and the four new annotations direct the cold auditor to 51/52 as the
  live re-proofs. Since the v13 rollover both crash: each hardcodes
  spec/12-spec-v12.md, now archived (live run this cycle: 51 →
  FileNotFoundError spec/12-spec-v12.md before any check; 52 →
  FileNotFoundError spec/12-spec-v12.md). The classes ARE re-proven on
  the live shape — by 59-rev13-gate-reaim.py G1-G6 (12/12 green this
  cycle) and 58-rev13 (25/25) — but neither 58 nor 59 appears in the
  header probes row at all (grep: 0 cites), so the row's only pointers
  to the D-50/D-51/D-54/D-57 live evidence are dead.
- minimal counterexample: a cold auditor following the v13 header's
  probes row runs `python3 appendix/52-rev12-gate-reaim.py` as the
  annotation's "live re-proof" instructs → FileNotFoundError — the
  exact SR11-F-02 failure class, reintroduced by the fix's own cite
  update on the next rollover.
- impact: bounded — an annotation/cite-hygiene gap, not a substance
  gap (the successor probes exist, are green, and the normative shapes
  they exercise are byte-identical v12→v13 per appendix/63 hunk
  audit). Same class as SR11-F-02, which the board has consistently
  treated as P2 (annotation treadmill at the rollover boundary).
- required disposition: on the next designer touch, (a) annotate
  appendix/51 in the probes row as HISTORICAL since the v13 rollover
  (archived spec/12 path; subject matter re-proven live by
  58-rev13/59-rev13), and (b) re-aim the annotations' re-proof cites
  to the live successors (59 G1-G6 for the fd/KI write-shape classes;
  58 P11-P15 for the annotation/count checks) or add 58/59 to the
  probes row — the same re-aim discipline the board already applies
  at every rollover (30→30b, 32→52→59).
- decision owner: spec-designer.
- verification required: mechval C17/probes-row liveness re-run after
  the next revision; no behavioral re-probe needed.

### SR12-F-02 [P3|evidence-note|needs-user:false]

- section/artifact: spec/13-spec-v13.md header probes row — the cite of
  appendix/48b-adv-c11-probes.py ("adversarial-early cycle-11
  evidence, reviewer file, cited as evidence only").
- claim: 48b is cited without qualification. Since the v13 rollover it
  crashes at its trailing text pin against the archived spec/11 (live
  run this cycle: FileNotFoundError spec/11-spec-v11.md), while its
  behavioral checks (P1×6, P2a, P2b — the at-open MemoryError
  reproductions D-57's "reproducing appendix/48b P2a/P2b" leans on)
  passed when last runnable and are re-proven live by 59 G6 and the
  51-successor chain.
- impact: editorial — the "cited as evidence only" label already
  signals it is a reviewer artifact; but its post-rollover crash
  state is worth one clause so the cold auditor is not surprised.
  (SR11-F-02 explicitly declined to annotate 48b while it still ran;
  the v13 rollover changed that fact.)
- required disposition: on the next designer touch, extend the 48b
  parenthetical with "HISTORICAL since the v13 rollover (archived
  spec/11 text-pin tail; behavioral subject re-proven live by 59 G6)"
  or the equivalent.
- decision owner: spec-designer.
- verification required: none (advisory note only).

## 4. Coverage summary

Axis 1 (internal quality): the v13 delta is confined to the four SR11
folds (independent 7-hunk audit, 0 unclassified); numbering stable; no
patch mangling; battery green; enumerations agree at D-01..D-58; QC
tuples complete; mutation contract 13/13. One annotation residue
(F-01) and one evidence note (F-02), both bounded.

Axis 2 (spec vs requirements): complete two-way traceability, exact
REQ/NFR set match (19/19); the v13 revision invents nothing and
reinterprets nothing — its entire delta is evidence-text correction
under REQ/NFR authority already established in v4..v12.

Axis 3 (verification alignment): T-C9's stated expectations now match
its measured evidence at every site (re-measured live this cycle);
test layers still match risk layers; QC-5's EV tuple remains complete
with the corrected numbers; the fusion latitude (D-58) remains
outcome-identity-pinned (55h agreement True on the CRLF corpus).

Per board policy the P2/P3 findings are mirrored to
appendix/advisory-register.md (rows appended this cycle).

| F | severity | disposition | owner |
|---|---|---|---|
| SR12-F-01 | P2 | open — probes row: annotate appendix/51 (HISTORICAL since v13 rollover) and re-aim the annotations' live re-proof cites to 58/59 (or add 58/59 to the row); both 51 and 52 crash on the archived spec/12 path | spec-designer |
| SR12-F-02 | P3 | open — 48b cite: add the post-v13-rollover HISTORICAL note (tail text-pin crashes on archived spec/11; behavioral subject live via 59 G6) | spec-designer |

Verdict: **PASS** — zero P0/P1. All four spec-review cycle-11 findings
are genuinely and completely fixed, with live evidence reproduced this
cycle; the two residual items are the rollover-boundary annotation
treadmill the board already tracks as advisory (P2/P3), locally
repairable on the next designer touch without touching any contract
or mechanism.


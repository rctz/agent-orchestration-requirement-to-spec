# Spec review — cycle 14 (spec-review c14)

| field | value |
|---|---|
| card | t_b7379694 — [i-need-a-small-command-line-tool-csv2js#spec-review#14] |
| target | spec/16-spec-v16.md (DRAFT, 2026-09-20, 2275 lines) |
| requirements | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| reviewer | req2-spec-reviewer |
| date | 2026-09-20 |
| verdict | PASS — 0 P0, 0 P1, 0 P2, 0 P3 |
| probes | this cycle's own evidence: appendix/91-sr14-battery-driver.py + per-probe runlogs appendix/91-sr14-runlog-*.txt (13 probes re-run live, all rc=0) + appendix/92-sr14-board-query.py (read-only board verification) + an independent hunk-by-hunk v15→v16 diff |

## 1. Scope and method

Three-axis review per SOUL: (1) internal quality of spec/16-spec-v16.md;
(2) consistency with APPROVED requirements/07-requirements-v7.md; (3)
verification alignment (test layer vs risk layer, EV-tuple completeness,
13-question mutation contract). The v15→v16 delta was enumerated
hunk-by-hunk from an independent diff (5 changed regions + 1 pure
insertion, all classified below); the cycle's driving finding
(mechval-c15 F-01, P1, C17 probe-path-stale) was re-checked by direct
grep against every superseded-spec cite in the live text; the designer
battery was re-run in full on this reference-class host; board cites
were verified read-only via appendix/92-sr14-board-query.py.

## 2. Delta classification (independent v15→v16 diff)

The revision row claims "mechanical-validation fix only". Verified by
diffing archive/spec/15-spec-v15.md against spec/16-spec-v16.md — 5
changed regions + 1 pure insertion, every one classified:

| # | region | change | class |
|---|---|---|---|
| 1 | header version/status | v15/DEPRECATED → v16/DRAFT | rollover hygiene |
| 2 | header probes row (line 14) | the 67-entry's spec/14 cite gains "(HISTORICAL since the v15 rollover …)" with successor 84 named in the same sentence; 78/79/80/81/83 annotated HISTORICAL since the v16 rollover; 84/85/86/87/88 added as cycle-16 LIVE entries; the four "re-proven live by 78" cites re-aimed to 84 (32/36/48b/51); the now-false "HISTORICAL itself since the v15" parentheticals removed | mechval-c15 F-01 fix (C17) + rollover hygiene |
| 3 | header revision row (line 15) | v16 entry prepended describing the cycle-16 fix | revision history |
| 4 | §11 coverage paragraph | v16 history note appended (12 lines: the F-01 closure + rollover hygiene, no decision added) | revision history |
| 5 | §11 v11 note | the appendix/47 parenthetical gains its HISTORICAL-since-v12 annotation (the same C17 class, folded in the same pass) | rollover hygiene |
| 6 | (none other) | — | zero hunks touch any contract, mechanism, REQ mapping, mutation-table row, QC tuple, or test inventory |

The claim is truthful: the delta is annotation text only, confined to
header rows and §11 history. Section numbering unchanged; §1/§11
enumerations unchanged at D-01..D-59 (verified by direct read); no
decision added (register stays D-01..D-59, 60 DECIDED rows incl. D-11b).

## 3. What verified clean

- **mechval-c15 F-01 (P1) genuinely fixed.** The C17 probe-path-stale
  charge was: the spec cited superseded spec/14-spec-v14.md with no
  HISTORICAL annotation. Live verification this cycle: the 67-entry's
  spec/14 cite (probes row, line 14) now carries "(HISTORICAL since the
  v15 rollover — its 12 checks passed at cycle 14 and the classes are
  re-proven live on the current shape by appendix/84-rev16-gate-reaim.py;
  the missing annotation on this cite is mechval-c15 F-01, closed at
  v16)" — annotation present, successor named in the same sentence, and
  the successor is real and green (84 ran 15/15 this cycle). The residual
  greps that could indicate an incomplete fix all resolve to legitimate
  quoted-history: the 2 surviving "re-proven live by 78" strings sit at
  line 15 (the v16 revision row describing what it re-aimed) and §11:2138
  (the v16 history note) — quotation, not annotation; the 1 surviving
  "HISTORICAL itself since the v15" string is the v16 row's own quote of
  the parenthetical it removed; the probes row's only 78 mention is the
  correctly-labeled HISTORICAL entry. mechval c16 re-ran PASS (0
  findings) after the fix.
- **Rollover hygiene genuine and complete.** All five rev15 text-pinned
  probes (78/79/80/81/83) carry HISTORICAL-since-v16 labels with their
  archived spec/15 paths named; their classes are carried live by the
  rev16 re-aims, all of which ran green this cycle (84: 15/15 incl. the
  new G12a/G12b arm-abort observables and G13 device class; 85: 31/31;
  86: 4 sweeps; 87: 2/2; 88: 28/28 — 88 verifies the annotation truth in
  both directions: LIVE-labeled probes run green, HISTORICAL-labeled
  probes fail on their archived paths, so a false label cannot survive
  it).
- **Battery green on spec/16** (appendix/91-sr14-battery-driver.py, all
  13 probes rc=0, logs in appendix/91-sr14-runlog-*.txt): 13 (63 checks)
  / 14-claim-keyword (0 hits, ours and sibling) / 15-selfcheck (0
  failures, sections 1..12 in order, D-01..D-59 bound) / 20 (21) / 22 /
  30b (8/8) / 77 (30/30 — the real shape-vs-shape identity battery) /
  66 (27/27 — the binding-controlled timing set; the function-bound pair
  reproduces the pinned numbers exactly at 14.9/9.1 s; module-bound cells
  ran 28.0/22.3 s elevated under this review's own concurrent load, with
  every DIRECTION claim holding: fused ahead at both bindings, binding
  gap 1.88x exceeds both form gaps 1.25x/1.63x — the pinned numbers'
  arithmetic and comparison discipline are unaffected) / 84 (15/15) / 85
  (31/31) / 86 / 87 / 88 (28/28).
- **Evidence descriptions match artifacts.** 66 Part B's vacuous
  self-comparison (tq/fu both `outcome(corpus, "table")`, source lines
  377-378) is documented in the spec as superseded by battery 77, and
  77's T1/T2 pins it mechanically; 66's B3-class block genuinely builds
  two different shapes. The spec never cites 66 Part B for shape-vs-
  shape identity — only for the normative N/M assertions and the
  first-latch demonstration, which the live run confirms.
- **Board-cite discipline exact** (appendix/92 output): spec-review#13
  (t_d7903f01) done/PASS, adv-early#14 (t_e2856728) done/FAIL,
  spec-design#16 (t_15693023) done/DONE — every verdict the v16 revision
  row cites exists on the board; no phantom cites. The parallel
  adv-early#16 twin (t_e9d477b9) is running and is cited by nothing in
  the spec (correctly — no verdict exists yet).
- **Axis 1 (internal quality): unchanged from the c13 PASS baseline and
  clean.** The v16 delta touches no contract; re-read of the full
  2,275-line text this cycle found the §4.5 mutation contract complete
  (13/13 rows, failure/retry/duplicate/concurrency/residue semantics all
  answered), QC-1..QC-6 complete 5-element tuples, §6.3 catalog closed
  with the verbatim-slot enumeration intact, D-15/D-29 ordering pinned
  with the S-9b combined-defect case, and the D-43..D-59 decision chain
  consistently mirrored across §2.2/§4.5/§5.1/§5.3/§6/§7/§8/§10.1/§11.
- **Axis 2 (spec vs requirements): unchanged and clean.** §1.2 maps and
  §11 covers exactly REQ-001..REQ-014 + NFR-001..NFR-005 (19/19,
  selfcheck S2/S3 green); nothing invented, nothing reinterpreted; the
  v16 delta is annotation-only under authority established in v4..v15.
  Register and §11 agree at D-01..D-59 (60 DECIDED rows; the D-58/D-59
  rows' source column still cites spec/15 §-sites, which is the
  register's own last-touched-version convention — the sites themselves
  are version-stable section numbers, and the spec's own coverage
  paragraph is the binding enumeration).
- **Axis 3 (verification alignment): unchanged and clean.** Test layers
  still match risk layers (real-fs integration for write behavior,
  RLIMIT_AS child processes for E-MEM, subprocess channel discipline,
  golden bytes for the output contract, exec'd-shape probes for the
  reference write shape); every quality claim sits in a complete EV
  tuple; the measurement-regime risk (adv-c13's B1) remains covered by
  66's four-cell design, re-run live this cycle.

## 4. Findings

None. Zero P0/P1/P2/P3.

The two residual observations collected during verification, both
resolving to legitimate structure (recorded here so the next reviewer
does not re-chase them):

- The strings "re-proven live by 78" (2 sites) and "HISTORICAL itself
  since the v15" (1 site) survive in the file — all three are the v16
  revision row's / §11 history note's own quotations of the wording the
  fix removed (grep line numbers 15 and 2138; delta-audit class:
  changelog quotation, the board's sanctioned history form).
- appendix/03-decision-register.md's newest rows (D-58/D-59) still cite
  "spec/15-spec-v15.md §..." in their source column. This is the
  register's per-cycle convention (every row cites the version whose
  cycle wrote it — older rows cite spec/06..spec/12 likewise) and the
  cited sections are version-stable; the normative enumeration lives in
  the spec's own §11 coverage paragraph, which is current at D-01..D-59.
  Not a defect under C17 (the register cites sections of record, not
  probe paths, and the cited section numbers exist unchanged in the live
  spec).

## 5. Coverage summary

Axis 1: delta confined to annotation/history text (independent diff, 5+1
regions, 0 unclassified); battery green; enumerations agree; mutation
contract 13/13; QC tuples complete. Axis 2: exact REQ/NFR set match
(19/19), nothing invented or reinterpreted. Axis 3: layers match risks;
EV tuples complete; the binding-controlled evidence rule (D-59) is
honored at every stage-cost sentence, re-verified live.

Verdict: **PASS** — zero P0/P1 (and zero P2/P3). The mechval-c15 F-01
fold is genuine and completely installed; the prophylactic rollover
hygiene is truthful in both directions (liveness sweep 28/28); the spec
remains at the quality bar the c13 review PASSed, with no contract
touched by this cycle. No advisory-register rows appended (nothing to
register).



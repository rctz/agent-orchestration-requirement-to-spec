# Spec review — cycle 7 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 7 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-19 |
| spec under review | spec/08-spec-v8.md (DRAFT, 2026-09-19) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | FAIL — 2×P1, 2×P2 (advisory P2 registered) |
| probes (this cycle) | re-run of the designer battery + live board-record queries (appendix/33-board-query-c7.py, read-only) |

Finding ids are scoped to this review and prefixed `SR7-F-nn`.

## Summary

Cycle 8 of the spec closed all seven spec-review cycle-6 findings
(SR6-F-01..F-07, appendix/31-review-spec-c6.md). Every one of the seven
folds is genuine and live-verified this cycle: the new D-50
close-before-remove failure arm is real (probe 32 re-run 6/6 — the
failure arm's fd is closed AND cleared before the remove, the
KeyboardInterrupt path still removes, the v7 control still removes with
the handle open); the register rows D-43/D-46/D-48 carry the live
except-scoped + D-50 shape with a v8 refresh paragraph; the header
probes row annotates 25/28 as HISTORICAL; T-C16's "(or byte-identical)"
slack is deleted; §4.5 op-order (3), §5.1's edge label, and R-4's
rationale are reworded as charged. The designer's delta audit (19/19)
and the full evidence battery re-ran green under my own shell (13:
63/63; 20: 21/21; 22: 19/19; 30 re-aimed at v8: 24/24; 30b: 8/8;
15-selfcheck: PASS; 14-claim-keyword: 0 hits).

Two P1s remain, one process and one technical:

1. **The v8 header claims a gate verdict that does not exist.** The
   revision row asserts "adversarial-early cycle-7 verdict PASS". The
   board record shows adv-early#7 (card t_aaaa036c) was manually
   reclaimed mid-run at 2026-09-19 07:56 UTC (20 min of heartbeats, then
   `reclaimed: manual, termination_attempted, terminated`) and archived
   with NO result, NO comments, and NO findings artifact — no
   `*adv-c7*.md` exists anywhere in the workspace. The probe battery
   that gate wrote before being killed (appendix/31b-adv-c7-probes.py,
   all 8 observations PASS) frames five candidate-finding families in
   its own docstring; none of them is cited or adjudicated anywhere in
   v8. A spec that cites a phantom PASS as its revision provenance, and
   leaves a written-but-never-adjudicated adversarial battery in the
   appendix tree, has an evidence-integrity hole exactly where the
   board's whole method is evidence discipline. One of the five
   unadjudicated families is itself a live P1 (SR7-F-02).
2. **KI-mid-write leaves two sections contracting opposite durable
   states.** §4.5's normative reference shape wraps `except
   BaseException` and its state contract says the target "is removed,
   whatever exception class the failure raised" — KeyboardInterrupt
   included (probe 32 P4 proves the arm removes on KI). §7.1's
   timeout-cancellation gloss says a kill "leaves whatever partial
   output existed at kill time"; §7.3 says KI is "NOT caught". Both
   readings are sanctioned by the text; they produce opposite on-disk
   outcomes for the same event (probe 31b P1 vs P1c), and no test in
   §8 pins the KI window.

P2s: SR6-F-03's historical-probes fix covered only the header row's
25/28 — the BODY still cites appendix/29b (4 sites) and appendix/25
M1, both of which exit non-zero today; and the D-50 binding-site lists
in the header/§11/register name "§11 REQ-010 row" and "T-C16" as
carrying D-50, but neither row's text contains it.

Axis 3 otherwise: test layers match risk layers everywhere they did in
cycle 6, plus the D-50 ordering is now pinned with the Windows-mode
rationale in T-C8. The KI window (SR7-F-02) is the one place a
contracted state has no test at any layer.


## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR7-F-01 | P1 | 2 | header `revision` row | "adversarial-early cycle-7 verdict PASS" cites a gate that was manually reclaimed mid-run and archived with no verdict, no comments, and no findings artifact; its probe battery's five candidate-finding families were never adjudicated |
| SR7-F-02 | P1 | 1 | §4.5 vs §7.1/§7.3 | KI mid-write: the normative `except BaseException` reference shape removes the target (probe 32 P4) while §7.1's kill gloss says the partial output is "left" and §7.3 says KI is NOT caught — two sanctioned readings, opposite durable states, no test pins the window |
| SR7-F-03 | P2 | 3 | §4.1, §5.3 S-14(e), §8.3 T-C16, §6.3 note, §10 QC-2 | SR6-F-03 fixed only the header row: body cites appendix/29b (4 sites) and appendix/25 M1 — both files exit non-zero today on the archived spec/06 path |
| SR7-F-04 | P2 | 2 | header revision row, §11 coverage paragraph, register D-50 row | D-50 binding-site lists name "§11 REQ-010 row" and "T-C16" as carrying D-50; neither row's text contains it (only T-C8 does) |

## Prior-fold verification

All seven cycle-6 findings verified FIXED in v8 (evidence re-run live
this cycle under my own shell):

- **SR6-F-01 (P1 → D-50).** FIXED. §4.5's reference shape failure arm
  now closes the fd (best-effort, `fd = None`) BEFORE the remove; QC-2
  Scope carries the platform-scope sentence ("holds on every platform
  in the conformance domain — POSIX and Windows alike — because the
  failure arm closes the fd BEFORE the remove"); T-C8 carries the
  Windows-mode rationale; register D-50 row exists and says QC-2 stays
  UNSCOPED. Probe 32 re-run: 6/6 PASS (P2: close event strictly before
  remove event, fd cleared; P3: v7 control removes with the handle
  open; P4: KI still removes). The recommended option (b) was adopted.
- **SR6-F-02 (P1 → register refresh).** FIXED. Register D-46's
  reference-shape clause now reads "EXCEPT-SCOPED per D-48 — ... the
  arm closing the fd before the remove (D-50) and re-raising"; D-43's
  clause reads "except-scoped shape per D-48"; D-48's row carries the
  v8 REFRESH paragraph. Delta-audit D5d green; verified by direct read
  of the register rows.
- **SR6-F-03 (P2 → historical annotation).** PARTIALLY FIXED — the
  header row annotates 25/28 as HISTORICAL (28b is no longer cited
  anywhere). Residual: the BODY still cites appendix/29b (4 sites) and
  appendix/25 M1, both non-running today → SR7-F-03.
- **SR6-F-04 (P2 → T-C16 slack).** FIXED. The "(or byte-identical)"
  parenthetical is gone from T-C16's assertion; the string survives
  only inside the SR6-F-04 deletion note itself (delta-audit D2b
  accounts for exactly those 2 citation sites).
- **SR6-F-05 (P3 → op-order wording).** FIXED. §4.5 op-order (3) now
  describes the manual close of the reference shape, with the
  with-block as a semantics-preserving equivalent conditioned on D-48 +
  D-50 semantics.
- **SR6-F-06 (P3 → §5.1 edge label).** FIXED. The edge reads
  "MemoryError(pre-open encode: nothing open — filesystem untouched)".
- **SR6-F-07 (P3 → R-4 rationale).** FIXED. The tautology is demoted
  to a supporting note; the closed-catalog and
  legitimate-in-place-conversion reasons carry the rationale.

Evidence battery re-run this cycle (all green): 13-spec-design-probes
63/63; 20-rev3-order 21/21; 22-rev4-writeorder 19/19; 30-rev7 (re-aimed
at v8) 24/24; 30b-adv-c6-reaim 8/8; 32-rev8-fdclose 6/6;
15-spec-selfcheck PASS (D-01..D-50 coverage); 14-claim-keyword 0 hits;
rev8_delta_audit 19/19. Axis-2 traceability re-checked: §11 covers
REQ-001..014 + NFR-001..005 with the same invariants as cycle 6 (plus
D-49/D-50 wording); §2.4 absence list matches REQ §3.2; no invented
scope; no REQ reinterpreted. Stale-probe census: 25 (refuses to run),
28 (annotated historical in the header), 28b (uncited), 29b (crashes
after P1..P4 pass, cited 4× in the body — SR7-F-03), 31b-review-spec-c6
(crashes after V1..V6 pass, uncited — same class, one line in the
findings file), 26b (13/14 — its P1 FAIL is the by-design text-mode
control arm, not a defect).


## SR7-F-01 [P1 | axis 2: spec vs authoritative artifacts | needs-user:false]

- section/artifact: spec/08-spec-v8.md header `revision` row, first
  sentence: "fixed all seven spec-review cycle-6 findings
  (appendix/31-review-spec-c6.md; adversarial-early cycle-7 verdict
  PASS)".
- claim or missing contract: the revision row cites an
  adversarial-early cycle-7 gate verdict as provenance for v8. No such
  verdict exists. The board record (queried read-only,
  appendix/33-board-query-c7.py) shows adv-early#7 (card t_aaaa036c,
  "EARLY-MODE twin of adv-review, running in PARALLEL with spec-review
  on the SAME draft spec/07-spec-v7.md") was claimed at 2026-09-19
  07:37 UTC, heartbeated for ~19 minutes, then at 07:56 UTC was
  MANUALLY RECLAIMED (`"manual": true, termination_attempted: true,
  terminated: true`) and archived — status `archived`, result empty,
  ZERO comments, run outcome `reclaimed`. No `*adv-c7*.md` findings
  artifact exists anywhere in the workspace (every prior FAILed adv
  cycle has one: 21-adv-c3.md, 26-adv-c5.md, 29-adv-c6.md). The gate's
  probe battery DOES exist (appendix/31b-adv-c7-probes.py, all 8
  observations PASS when run) and its own docstring frames five
  candidate-finding families — (P1/P1c) §4.5 vs §7.1 contracting
  opposite KI-mid-write states, (P2) `/dev/stdout`//`/dev/stderr` as
  output paths falsifying §6.1/§6.4's "stdout/stderr empty on
  success", (P3) C-locale stderr mangling the verbatim E-DUP name that
  §6.3 declares NON-CONFORMING to escape, (P4) the concurrency residue
  behind §6.3's unqualified at-open "byte-untouched" note, (P5) a
  passing E-UTF8 precedence sanity check. None of the four
  candidate-defect families is cited, dispositioned, or risk-recorded
  anywhere in v8; grep for `31b|adv-c7` in spec/08-spec-v8.md returns
  nothing. The designer's spec-design#8 completion comment says only
  "adversarial-early c7 premise re-checked (all nine PASS probes'
  premises intact)" — an internal re-check of probe premises is not an
  adjudication, and the claim in the header is a VERDICT.
- evidence: board events for t_aaaa036c (created 1789803421, reclaimed
  1789804594 `manual: true`, archived 1789804595; run 552 outcome
  `reclaimed`; zero task_comments rows); `grep -rn "adv-c7"
  <workspace>` matches only the probe file itself; live run of
  appendix/31b-adv-c7-probes.py this cycle: P1 PASS (BaseException
  shape removes), P1c PASS (Exception shape leaves), P2/P2b PASS
  (`/dev/stdout` → rc 0 with the JSON on stdout; `/dev/stderr` → rc 0
  with the JSON on stderr), P3/P3b PASS (LC_ALL=C: Thai name arrives
  as `\u0e1b...` backslash-escaped, verbatim bytes unreachable, no
  crash), P4 PASS (concurrent at-open EACCES while a writer holds a
  0-byte truncation), P5 PASS.
- minimal counterexample: a cold auditor reads the v8 header, looks for
  the adv-c7 verdict artifact to verify the PASS claim, and finds an
  archived card with no verdict plus an unadjudicated probe battery
  whose own labels describe spec-contract violations. The provenance
  chain the header asserts cannot be walked.
- impact: the spec's revision provenance contains an unverifiable
  verdict claim; four live adversarial observations against §4.5/§6.1/
  §6.3/§6.4/§7.1 sit in the appendix tree with no disposition, so the
  next cycle (or an implementor) inherits neither their resolution nor
  even their existence. This is the board's own SR6-F-02 artifact-class
  (authoritative artifacts disagree / a cited authority does not say
  what the spec claims), now on the spec's own evidence trail.
- required disposition: (a) delete the "adversarial-early cycle-7
  verdict PASS" clause (the honest statement is that the gate was
  cancelled mid-run), or back it with a real verdict artifact; AND (b)
  adjudicate the 31b-adv-c7 observation families in the next designer
  cycle — fix in the spec, record as accepted risk, or refute, each
  with a finding/disposition row (the KI family is SR7-F-02 below and
  is P1 on its own merits; the `/dev/stdout` and C-locale families are
  at minimum P2-class and need explicit dispositions; the P4
  concurrency residue is likely closable by pointing at R-2/§4.5 row 9
  from §6.3's at-open note).
- decision owner: spec-designer (with req2-orchestrator for the
  cancelled-gate provenance).
- verification required: next-cycle re-read of the header row; grep
  that every adversarial observation family has a disposition; board
  state of t_aaaa036c unchanged (it is the evidence).

## SR7-F-02 [P1 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/08-spec-v8.md §4.5 (reference shape `except
  BaseException:` + the normative state sentence "the target is
  removed, whatever exception class the failure raised") vs §7.1's
  timeout-cancellation taxonomy note ("cancellation is the user killing
  the process, which leaves whatever partial output existed at kill
  time — outside the tool's contract, recorded as an accepted scope
  boundary") and §7.3's last sentence ("`SystemExit`/`KeyboardInterrupt`
  are NOT caught (process-level signals pass through ...)").
- claim or missing contract: KeyboardInterrupt striking mid-write (the
  one window where the user's Ctrl-C and the tool's mutation overlap)
  has TWO sanctioned readings with OPPOSITE durable-state outcomes.
  Reading A (§4.5 taken literally): KI is a BaseException, the failure
  arm runs — close the fd, remove the target, re-raise — so a
  KI-interrupted run leaves NO output file (live: probe 32 P4, events
  `open, write, close, closed, remove`, "KI propagated (D-48
  every-exception scope intact)"; probe 31b P1, `removed=True`).
  Reading B (§7.1 + §7.3 taken literally): the kill "leaves whatever
  partial output existed at kill time" and KI is "NOT caught" — the
  narrow `except Exception` wrap that §7.3's sentence sanctions leaves
  the partial file on disk (live: probe 31b P1c, `removed=False`).
  Both builds conform to the spec as written, and they differ in
  exactly the property QC-2 exists to protect (no plausible-complete
  partial output survives). §7.1's "outside the tool's contract" gloss
  cannot reconcile them, because §4.5's reference shape — the block an
  implementor copies — makes the KI outcome a contracted, deterministic
  consequence of the pinned code, not an OS race.
- evidence: probe appendix/32-rev8-fdclose-probes.py P4 (re-run this
  cycle, PASS: the spec's own shape removes on KI); probe
  appendix/31b-adv-c7-probes.py P1 vs P1c (re-run this cycle, both
  PASS as labeled: BaseException wrap removes, Exception wrap leaves);
  §4.5 "Compensation trigger is every exception raised after a
  successful open" + the shape's `except BaseException:`; §7.3 "are NOT
  caught"; §7.1 taxonomy "leaves whatever partial output existed at
  kill time".
- minimal counterexample: FIFO or slow device as output; the write
  blocks; the user presses Ctrl-C. Build A (copies §4.5's block):
  partial file removed, KI traceback-visible exit. Build B (follows
  §7.3's not-caught sentence with `except Exception`): partial file
  SURVIVES as a plausible-complete JSON document after a
  user-interrupted run — the QC-2 outcome the spec's own compensation
  exists to prevent, on a conforming build, with no test in §8 that
  could tell the two apart (T-C8/T-C16 inject OSError/MemoryError,
  never a signal).
- impact: observable behavior ambiguous for a real, common event
  (Ctrl-C during a large write); a core no-partial-output property is
  build-dependent; the verification plan has no probe at the layer
  where the divergence lives (signal delivery during the write).
- required disposition: pick one contract and align all three sites.
  Recommended: keep §4.5's BaseException arm (the D-48/D-50 state
  contract then holds for signals too — the strictly safer outcome),
  and (i) fix §7.1's taxonomy note to say the §4.5 arm removes the
  partial file for KeyboardInterrupt (SIGINT-delivered) kills — the
  "leaves whatever partial output existed" residue applies only to
  uncatchable kills (SIGKILL/SIGTERM-default), and (ii) qualify
  §7.3's "NOT caught" to "not caught by main's handler chain" (the
  write-stage arm still compensates before re-raising — exactly what
  probe 32 P4 demonstrates). Add a KI sub-case to T-C8's matrix
  (SIGINT to a blocked write, assert target absent + no traceback
  beyond the KI exit).
- decision owner: spec-designer.
- verification required: next-cycle re-read of §4.5/§7.1/§7.3
  alignment; a probe asserting the KI-window state (31b P1's method:
  FIFO-blocked write + SIGINT) pinned in T-C8's matrix.

## SR7-F-03 [P2 | axis 3: verification alignment | needs-user:false]

- section/artifact: spec/08-spec-v8.md body evidence citations — §4.1
  (line ~247, "probe appendix/29b P4"), §5.3 S-14(e) (line ~967-968,
  "probe appendix/29b P2"/"appendix/29b P2b"), §8.3 T-C16 row (line
  ~1210, "probes appendix/29b P2/P2b"), §10 QC-2 Verification (line
  ~1332, "probes appendix/29b P2/P2b"), §6.3 E-DUP note (line ~1059,
  "appendix/25 M1"); also the uncited-but-present
  appendix/31b-review-spec-c6-probes.py (crashes after V6).
- claim or missing contract: SR6-F-03 charged the v7 header with
  citing stale probes; the v8 fold annotated ONLY the header's probes
  row (25 and 28 marked HISTORICAL, 28b dropped). The body's own
  citations were left pointing at files that no longer run:
  appendix/29b-adv-c6-probes.py hardcodes spec/06-spec-v6.md and exits
  non-zero today (P1..P4 print PASS, then FileNotFoundError in p5 on
  the archived path — verified live this cycle), yet the spec body
  cites it four times as live evidence for v8 claims; likewise §6.3's
  E-DUP note cites appendix/25 M1 and 25 refuses to run ("no live spec
  revision found (06/05 missing)" — verified live). The same class
  also now covers the cycle-6 reviewer's own probe file
  (31b-review-spec-c6-probes.py, crashes after V6 on the archived v7
  path) — noted for the record; it is not cited by the spec.
- evidence: live runs this cycle: `python3 appendix/29b-adv-c6-probes.py`
  → P1/P1b/P2/P2b/P3/P4 PASS then `FileNotFoundError:
  .../spec/06-spec-v6.md`, exit non-zero; `python3
  appendix/25-rev5-serialize-form-probes.py` → "no live spec revision
  found", exit non-zero; `grep -n "appendix/29b" spec/08-spec-v8.md` →
  4 body hits (§4.1, S-14(e) ×2, T-C16, QC-2 — five mentions across
  four sites); `grep -n "appendix/25" spec/08-spec-v8.md` → line 1059
  body hit + header row.
- minimal counterexample: n/a (evidence-infrastructure staleness; no
  runtime behavior of the tool diverges).
- impact: bounded — the cited behaviors are re-proven by 30/30b/32 and
  the claims stand; but a cold auditor walking the body's evidence
  citations hits two crashing files, the same audit-trail weakness
  SR6-F-03 charged, now in the body instead of the header.
- required disposition: on the next designer touch, either re-aim
  29b at the live spec revision (the 28-series re-aim method) or
  annotate each body cite "(historical; re-proven by 30/30b)" — and
  do the same for the §6.3 appendix/25 M1 cite (its subject matter is
  re-proven by 30b/25's own recorded cycle-5 run).
- decision owner: spec-designer.
- verification required: re-run of the re-aimed files (or read-back of
  the annotations) next cycle.

## SR7-F-04 [P2 | axis 2: spec vs authoritative artifacts | needs-user:false]

- section/artifact: spec/08-spec-v8.md header revision row ("D-50 is
  bound in the reference shape, the compensation bullet, mutation table
  rows 10/11, T-C8 (with the Windows-mode rationale), QC-2
  Scope/Mechanism, and §11 REQ-010"), §11 coverage paragraph ("bound
  also in ... §8.3 T-C8/T-C16, QC-2, §11 REQ-010 row, register D-48 v8
  refresh"), and register D-50 row (source cell lists "§4.5 table rows
  10/11, §8.3 T-C8 note, QC-2, §11 REQ-010 row").
- claim or missing contract: three authoritative artifacts enumerate
  D-50's binding sites, and the enumerated sites "§11 REQ-010 row" and
  "T-C16" do not contain D-50. Verified: the §11 REQ-010 row (line
  ~1502) names D-43/D-45/D-46/D-47/D-48/R-4/R-1b — no D-50; the T-C16
  row (line ~1210) names D-43/D-44/D-46 — no D-50; `grep -c "D-50"`
  on those lines returns 0 for both. T-C8 and QC-2 DO carry it. The
  inaccuracy is a factor-two overcount on two of the three lists (the
  register row and §11 both name the REQ-010 row; §11 and the header
  both name T-C16).
- evidence: `sed -n '1502p' spec/08-spec-v8.md | grep -c "D-50"` → 0;
  `sed -n '1210p' spec/08-spec-v8.md | grep -c "D-50"` → 0; register
  D-50 row's source cell text (appendix/03-decision-register.md line
  57) ends "...§8.3 T-C8 note, QC-2, §11 REQ-010 row"; header row 15
  lists "...T-C8 (with the Windows-mode rationale), QC-2
  Scope/Mechanism, and §11 REQ-010".
- minimal counterexample: n/a (mechanical cross-reference check).
- impact: bounded — D-50's normative content is fully bound at its
  real sites (§4.5 shape + bullet + rows 10/11/13, T-C8, QC-2); but
  the binding-site lists are what mechval and cold auditors walk, and
  two of three lists name sites that do not exist. Given the board's
  D-32 hygiene rule and SR6-F-02's precedent (register/spec
  disagreement is P1 when normative shape text diverges), this is a
  P2: the divergence is in enumerations of binding sites, not in any
  normative contract, and the implementor following any single site is
  unaffected.
- required disposition: either add the D-50 mention to the §11 REQ-010
  row and the T-C16 row (recommended — the ordering IS what makes the
  T-C16 write-phase "path-absent" assertion hold on Windows, so the
  cite is substantively earned), or correct the three binding-site
  lists to the actual sites.
- decision owner: spec-designer.
- verification required: next-cycle grep of lines ~1210/~1502 for
  "D-50" (or the corrected lists).

## Verdict block

(pending)

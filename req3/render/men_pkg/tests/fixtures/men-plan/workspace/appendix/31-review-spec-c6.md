# Spec review — cycle 6 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 6 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-19 |
| spec under review | spec/07-spec-v7.md (DRAFT, 2026-09-17) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | FAIL — 2×P1, 2×P2, 3×P3 (advisory P2/P3 registered) |
| probes (this cycle) | appendix/31b-review-spec-c6-probes.py — 14/14 PASS (V1..V8) |

Finding ids are scoped to this review and prefixed `SR6-F-nn`.

## Summary

Cycle 7 of the spec rewrote §4.5's compensation reference shape per D-48
(except-scoped; the v6 try/finally snippet deleted every successful
run's output) and closed adv-c6 F-01..F-05 plus both SR5 advisories.
All seven folds are genuine, live-verified, and consistently wired
inside spec/07-spec-v7.md — verified this cycle by re-running the
designer's evidence battery (13: 63/63, 20: 21/21, 22: 19/19, 30:
24/24, 30b: 8/8, 15-selfcheck, 14-claim-keyword 0 hits) and by my own
V-probes (V4a/V4b confirm the S-9b E-DUP-beats-E-UQ premise; V5 the
S-1 46-byte golden; V6 the D-49 `-h out.json` → E-READ outcome).

Two P1s remain, both downstream of the D-48 fold:

1. **The fold is incomplete against its own defect charge.** D-48
   (spec §4.5, register D-48) supersedes the v6 shape partly because it
   "never closed the fd". The v7 reference shape STILL never closes the
   fd on the failure path (probe V2: the fd is open at raise time). On
   POSIX this is harmless (V3: remove-while-open succeeds); on Windows
   `os.remove` on the open handle raises PermissionError — swallowed by
   the best-effort clause — so the partial file SURVIVES: exactly the
   D-33/QC-2 outcome the compensation exists to prevent, deterministically,
   on a platform the requirements assess conformance on (D-35's own
   `]\r\n`-on-Windows rationale). The state contract is met on Linux CI
   and silently fails on Windows with no EV tuple, no risk row, no
   platform scope anywhere.
2. **The machine-parsed register contradicts the spec.** Register rows
   D-46 and D-43 still prescribe the try/finally shape as THE reference
   shape ("finally's remove guarded by whether the open succeeded";
   "(try/finally shape)") — the exact v6 form D-48 superseded because
   its finally runs on the success path, deleting every successful
   run's output (probe V7a/V7b vs V7c). D-32's standing hygiene rule
   (register rows cite the live shape, not stale snapshots) applies to
   D-46/D-43 exactly as it applied to D-15 in cycle 3.

P2/P3: three evidence probes (25/28/28b) cited in the v7 header now
crash on the archived spec/06-spec-v6.md path (V8) — the v6 rollover
left them stale, same class as the 26-c4-probes staleness recorded in
cycle 5; T-C16's "(or byte-identical)" slack; R-4's rationale carries a
known tautology ("no REQ promises same-path semantics" is trivially
true of a REQ set that never considered the case — it is the reason the
record exists, not a defense of the recorded behavior); and two
cross-reference nits (§4.5 op-order "(3)" cites a with-block the
reference shape no longer uses; §5.1 labels the pre-open encode
MemoryError "no compensation" where the correct statement is "no
compensation REQUIRED" — nothing is open yet).

Axis 2 (spec vs APPROVED requirements): clean. Traceability complete
and honest (§11 covers REQ-001..014, NFR-001..005; spot-checked
against the APPROVED text: REQ-001 D-49 pin, REQ-002 duplicate +
empty-name ACs, REQ-005 verbatim strings, REQ-007 prefix-on-all +
verbatim interpolation, REQ-009 blank/BOM/whitespace cases, REQ-010
no-output-on-error + mid-write remove + at-open case, REQ-011 CR-only
line-4 case, REQ-013 all seven AC shapes incl. S-9b and N/M,
REQ-014 byte-exactness). No invented scope (§2.4 absence list matches
REQ §3.2); no REQ reinterpreted. R-4 and D-49 are new decisions inside
spec freedom, not requirement rewrites.

Axis 3 (verification alignment): layers match risk layers everywhere
except the Windows-fd gap (F-01's core): write semantics on the real
filesystem, E2E through main, E-MEM via RLIMIT_AS environment control,
pure semantics at unit seams. The 13-question mutation table answers
all 13 with D-46-consistent values; QC-1..QC-6 complete; QC-2's
platform scope is the one incomplete tuple (F-01).

## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR6-F-01 | P1 | 1 | §4.5 reference shape + QC-2 scope | except-scoped shape still never closes the fd on the failure path — on Windows the swallowed PermissionError from os.remove leaves the partial file (deterministic QC-2 violation, unrecorded) |
| SR6-F-02 | P1 | 2 | appendix/03-decision-register.md D-46, D-43 rows | machine-parsed register still prescribes the superseded try/finally reference shape — the exact form D-48 superseded (deletes every successful run's output); D-32 hygiene breach |
| SR6-F-03 | P2 | 3 | header probes row; §4.5/§4.4 evidence cites | evidence probes 25/28/28b crash on the archived spec/06-spec-v6.md path — cycle-5's known staleness class, now tripled |
| SR6-F-04 | P2 | 1 | §8.3 T-C16 | "(or byte-identical)" slack in the write-phase-form assertion lets a non-removing build pass the phase-form gate |
| SR6-F-05 | P3 | 1 | §4.5 op order (3) | "(3) write, flush, then close (the with block closes...)" cites a with-block the reference shape replaced with manual close |
| SR6-F-06 | P3 | 1 | §5.1 diagram | "MemoryError(pre-open encode: no compensation)" — accurate outcome, wrong mechanism wording (nothing is open; no compensation REQUIRED, none POSSIBLE) |
| SR6-F-07 | P3 | 2 | §10.1 R-4 rationale | "no REQ promises same-path semantics" is evidence FOR recording, not a rationale against guarding; the substantive rationale (new error class outside closed catalog; legitimate in-place conversion) is present and sufficient |

## SR6-F-01 [P1 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/07-spec-v7.md §4.5, "Conforming reference shape
  (e.g.)" code block (lines ~633-644) + QC-2 Scope/Mechanism (§10) + §7.1
  E-WRITE row; register D-48.
- claim or missing contract: the D-48 disposition charged the v6 shape
  with two defects — (i) its finally ran the remove on the SUCCESS path
  (deleting every successful run's output) and (ii) it "never closed
  the fd". The v7 fold fixes (i) only. The new except-scoped reference
  shape still never closes the fd on the FAILURE path: the except arm
  runs `os.remove` while the handle is open, then re-raises. On POSIX
  this is harmless (unlink-while-open is allowed). On Windows — a
  platform the requirements assess conformance on (REQ §5.2/D-35's
  entire rationale is the Windows `]\r\n` text-mode failure; NFR-002's
  floor is interpreter-wide, not OS-wide) — `os.remove` on an open
  handle raises PermissionError, which the shape's best-effort clause
  swallows: the partial file SURVIVES a failed post-open run. That is
  exactly the outcome D-33/QC-2 exist to prevent ("a partially written
  file must never survive as a plausible complete JSON document"), now
  reachable deterministically on a supported platform, with no EV-tuple
  platform scope, no risk row, and no close-before-remove ordering
  pinned anywhere in the spec.
- evidence: probe appendix/31b V2 — the §4.5 shape verbatim, fault
  injected at write: exception propagates, file removed (POSIX), and
  the fd is STILL OPEN at raise time (walked the traceback frames);
  V3 — control: POSIX `os.remove` on an open fd succeeds, so the defect
  is invisible on the Linux CI that runs T-C8/T-C16. Windows
  remove-while-open → PermissionError is documented platform behavior
  (CPython `os.remove` = Win32 DeleteFile on a handle the OS keeps
  open via the CRT fd). Spec text: the except arm's only close-path is
  `fd.close(); fd = None` in the TRY block; the EXCEPT arm has no
  close. QC-2's Scope says "every supported platform (NFR-002 floor
  3.9+)" for QC-1 but QC-2's own scope line names no platform bound
  for the compensation; §4.5's normative state sentence ("the target is
  removed, whatever exception class the failure raised") carries no
  platform qualifier while the mechanism that delivers it fails on
  Windows.
- minimal counterexample (Windows, any conforming-as-written build):
  1. `out.json` exists or not; input valid; disk full or EIO at write.
  2. §4.5 shape: open succeeds → write/flush raises OSError.
  3. except arm: `fd is not None` → `os.remove(path)` →
     PermissionError (file still open) → swallowed by `except OSError:
     pass`.
  4. re-raise → E-WRITE message, exit 1 — and the PARTIAL `out.json`
     survives on disk. QC-2's contracted outcome ("the target is
     removed") is violated by the spec's own reference shape.
- impact: a data-integrity property (no plausible-complete partial
  output survives a failed run) fails deterministically on a platform
  in the spec's conformance domain, and the verification plan cannot
  detect it (T-C8/T-C16 run on POSIX where remove-while-open succeeds).
  The implementor following the reference shape literally ships the
  defect; the implementor closing the fd in the except arm before the
  remove departs from the pinned shape with no textual warrant (D-48's
  "reference shape" language is normative-for-outcomes but the block is
  what an implementor copies).
- required disposition: pin the ordering "close the fd (best-effort)
  BEFORE the remove, inside the failure arm" in the reference shape and
  in D-48's register row — e.g. the except arm becomes
  `if fd is not None: try: fd.close() except OSError: pass; try:
  os.remove(path) except OSError: pass` — and either (a) scope QC-2's
  compensation clause to POSIX with a recorded Windows risk row
  (owner/rationale/impact/mitigation/verification) if close-before-
  remove is adopted, or (b) keep QC-2 unscoped and adopt (a)'s close
  ordering (then the Windows residue disappears and no risk row is
  needed). Option (b) is the recommended minimal fix.
- decision owner: spec-designer.
- verification required: next-cycle re-read of §4.5 + register D-48
  row; a new probe asserting the except arm closes before removing
  (fd.closed True at remove time) on POSIX; note in T-C8 that the
  Windows remove-while-open failure mode is the reason the close
  ordering is pinned.

## SR6-F-02 [P1 | axis 2: spec vs authoritative artifacts | needs-user:false]

- section/artifact: appendix/03-decision-register.md rows D-46 and
  D-43 vs spec/07-spec-v7.md §4.5 (D-48 fold).
- claim or missing contract: the register is the machine-parsed
  authoritative decision record (D-32's standing hygiene rule: a row
  cites the live revision's shape, not a stale snapshot — the exact
  rule applied to D-15 in cycle 3 as F-27/D-32). After the v7 D-48
  fold, register D-46's row still prescribes "reference shape: open
  INSIDE the try, finally's remove guarded by whether the open
  succeeded" as THE reference shape, and D-43's row still names
  "(b) ... (try/finally shape)". Both describe the v6 form D-48
  superseded BECAUSE its finally runs on the success path — deleting
  every successful run's just-written output. Any consumer following
  the register (the mechanical validator, the mechval gates, a future
  designer refreshing a fold) reads the register as authoritative and
  finds two rows prescribing a shape the spec's own revision history
  calls non-conforming-since-v7. This is the same artifact-disagreement
  class as cycle-3's SR3-F-02 (P2, stale enumeration) but with
  normative shape text, not just an id list.
- evidence: probe appendix/31b V7a — register D-46 row contains
  "finally's remove guarded by whether the open succeeded"; V7b —
  D-43 row contains "(try/finally shape)"; V7c — spec §4.5 pins the
  except-scoped shape ("except-scoped", "failure arm ONLY") and the
  header revision row declares the v6 snippet superseded (register
  D-48: "the v6 try/finally snippet ... is superseded"). The
  disagreement is live in the same workspace state this review ran on.
- minimal counterexample: n/a (no runtime behavior diverges inside the
  spec itself; the divergence is between two authoritative artifacts —
  the spec's normative shape and the register's machine-parsed rows).
- impact: the register and the spec disagree on the compensation
  reference shape; downstream mechanical checks (mechval C15 final
  mode reads the register) and any future fold that cites D-46/D-43 as
  its shape source reintroduces the success-path deletion defect the
  cycle-7 review just removed. Authoritative-artifact disagreement is
  P1 by the board's severity policy.
- required disposition: refresh register rows D-46 and D-43 to the
  v7 shape (per D-32's standing rule): D-46's "reference shape"
  clause → "reference shape: except-scoped per D-48 — open inside the
  try; the best-effort remove lives in the failure arm only, guarded
  by `fd is not None`" (plus the F-01 close ordering once decided);
  D-43's "(try/finally shape)" → "(except-scoped shape per D-48)".
  Cite spec/07-spec-v7.md §4.5 as the source cell.
- decision owner: spec-designer.
- verification required: next-cycle re-read of the register rows
  (mechval gate re-runs); no runtime probe applies.

## SR6-F-03 [P2 | axis 3: verification alignment | needs-user:false]

- section/artifact: spec/07-spec-v7.md header `probes` row (cites
  appendix/25, appendix/28, appendix/30b) and §4.4/§4.5/§8.3 evidence
  cites naming appendix/28 (R6-P1/R6-P2) and the 25/22/28 series.
- claim or missing contract: three probe files cited as live evidence
  for v7 claims hardcode `spec/06-spec-v6.md` and now crash
  (FileNotFoundError / "no live spec revision found") after the
  rollover archived v6: appendix/25-rev5-serialize-form-probes.py,
  appendix/28-rev6-writegate-probes.py,
  appendix/28b-rev6-reviewer-reaim-probes.py. The BEHAVIORS they
  proved are unchanged by v7 and were re-proven by appendix/30 and
  30b, but a cold auditor following the header's evidence trail hits
  three crashes before reaching the working re-aims. This is the same
  staleness class cycle 5 already recorded for
  26-review-spec-c4-probes (noted in appendix/29's evidence line) —
  the rollover keeps multiplying it.
- evidence: probe appendix/31b V8 — all three files exit non-zero on
  the archived path; 30-rev7-writegate-probes.py PASSes the same
  subject matter (TOTAL FAILURES: 0), and 30b PASSes 8/8.
- minimal counterexample: n/a (evidence-infrastructure staleness, not
  spec behavior).
- impact: bounded — the claims remain probe-backed via 30/30b; the
  header's evidence row names files that no longer run, weakening the
  audit trail the mechval gates and cold auditors walk.
- required disposition: on the next designer touch, either re-aim the
  three files at spec/07-spec-v7.md (the 28-series method already used
  for 26-c4 → 28b) or annotate the header's probes row that 25/28/28b
  are historical (pre-v7) evidence superseded by 30/30b.
- decision owner: spec-designer.
- verification required: re-run of the re-aimed files (or the
  annotation read-back) next cycle.

## SR6-F-04 [P2 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/07-spec-v7.md §8.3 T-C16 — "so the correct
  assertion is that the path is ABSENT (or byte-identical) — never
  still present with foreign bytes."
- claim or missing contract: for the write-phase (post-open) E-MEM
  form, the contracted state (D-33/D-46 compensation removes the
  truncated target) is "path absent". The parenthetical "(or
  byte-identical)" admits a second outcome with no mechanism that
  could produce it on a conforming build: after a successful open the
  every-exception compensation removes the target, and a remove
  failure on a regular file is R-1's pathological-only residue (not
  reachable under RLIMIT_AS fault injection). The slack lets a build
  whose compensation silently never runs (the exact F-01-class defect)
  pass T-C16's phase-form gate on the byte-identical branch.
- evidence: §4.5 normative state sentence ("the target is removed,
  whatever exception class the failure raised"); R-1's likelihood
  "pathological"; T-C16's own preceding sentence pins the write-form
  outcome as "REMOVES the target" before the parenthetical loosens the
  assertion.
- minimal counterexample: n/a (test-assertion slack; no input pair
  diverges — the point is that the assertion cannot fail a
  compensation-less build on the byte-identical branch when the
  pre-existing bytes happen to be what the truncated-then-failed run
  leaves... concretely: RLIMIT_AS run whose OOM strikes after open on
  a build with a broken except arm that never removes → path still
  present, bytes = prior content → T-C16 accepts "(byte-identical)":
  PASS despite a QC-2 violation).
- impact: bounded — the primary assertion (absent) is correct and the
  slack only weakens one sub-case; but the adv-c6 F-01 fix's whole
  point was making T-C16's state assertion form-exact, and the
  parenthetical re-opens a (narrower) hole in the same gate.
- required disposition: delete "(or byte-identical)" from the
  write-phase-form assertion, or justify it with the mechanism that
  can produce it (none exists on a conforming build under this fault
  injection).
- decision owner: spec-designer.
- verification required: next-cycle read-back; no runtime change.

## SR6-F-05 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/07-spec-v7.md §4.5 operation order —
  "(3) `write(payload)`, then `flush()`, then close (the `with` block
  closes; flush failures surface inside the `with` before close
  accounting)".
- claim or missing contract: the sentence describes a `with`-block
  close, but the D-48 reference shape below it uses manual
  `fd.close(); fd = None` inside the try. The two descriptions of the
  same stage diverge syntactically; an implementor coding the op-order
  sentence with `with` and then reconciling it against the reference
  shape must reconcile an apparent mismatch (a with-block's __exit__
  close is NOT visible as fd=None to the except arm — the shapes
  compose differently).
- evidence: §4.5 lines ~563-565 (with-block wording) vs the reference
  shape block lines ~633-644 (manual close).
- minimal counterexample: n/a (editorial cross-reference).
- impact: editorial; the normative state contract is identical either
  way.
- required disposition: reword (3) to "then close (manually in the
  reference shape below; a `with` block is an acceptable equivalent
  only if the D-48 failure-arm semantics are preserved)".
- decision owner: spec-designer.
- verification required: none (next-cycle read-back).

## SR6-F-06 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/07-spec-v7.md §5.1 diagram edge —
  "WRITE_OUTPUT ── MemoryError(pre-open encode: no compensation) ──►
  REPORTING(memory)".
- claim or missing contract: "no compensation" reads as though the
  compensation trigger was evaluated and not fired; at the pre-open
  encode position no compensation is POSSIBLE (nothing is open — the
  D-43/D-44 basis). Same gloss class as SR5-F-02, one edge over.
- evidence: §4.4 ("nothing has been opened yet at this stage, so no
  compensation applies — the serialize phase simply leaves the
  filesystem untouched"); D-44 register row.
- minimal counterexample: n/a (diagram wording).
- impact: editorial.
- required disposition: relabel "no compensation" → "nothing open —
  filesystem untouched" (or equivalent).
- decision owner: spec-designer.
- verification required: none (next-cycle read-back).

## SR6-F-07 [P3 | axis 2: spec vs requirements | needs-user:false]

- section/artifact: spec/07-spec-v7.md §10.1 R-4 rationale — "no REQ
  promises same-path semantics, so the risk is recorded, not
  engineered away."
- claim or missing contract: the absence of a REQ promise is the
  reason the case needed a record, not a defense of the recorded
  behavior; as written the clause is a near-tautology (the REQ set
  never considered same-path invocation). The SUBSTANTIVE rationale —
  a refusal guard needs a new error class outside the closed §6.3
  catalog (D-42) and would forbid a legitimate in-place conversion —
  is present in the same paragraph and carries the argument alone.
- evidence: §10.1 R-4 text; §6.3 closed-catalog statement; R-1b's
  rationale paragraph (which argues from mechanism trade-offs, the
  stronger form).
- minimal counterexample: n/a (rationale wording).
- impact: editorial; the disposition itself (accepted-risk record) is
  sound and live-demonstrated (appendix/30b P3).
- required disposition: drop or demote the "no REQ promises" clause to
  a supporting note; keep the catalog-closure and legitimate-use
  reasons as the rationale.
- decision owner: spec-designer.
- verification required: none (next-cycle read-back).

## Prior-fold verification (no other blocking findings)

- **adv-c6 F-01 (P1 → T-C16 phase-form).** Resolved: T-C16's
  pre-existing-output assertion is phase-form-dependent (byte-identical
  pre-open / absent write-phase), the §7.1 taxonomy sentence and QC-2
  Verification inherit the correction, and the v6 "form-independent"
  wording survives only as quoted history. Verified by 30b P2/P2b and
  my read of §8.3/§7.1/QC-2. (Residual slack: SR6-F-04.)
- **adv-c6 F-02 (P1 → D-48).** Resolved in outcome (success keeps the
  file, failure removes it — 30b P1/P1b re-run PASS); the fold's own
  second defect charge (fd never closed) is only half-fixed: SR6-F-01.
- **adv-c6 F-03 (P2 → R-4).** Resolved: full accepted-risk record
  (owner user+implementor, rationale, impact, mitigation,
  live-demonstrated verification via 30b P3), mirrored in §4.5 row 10
  and S-1's same-path note. (Rationale wording: SR6-F-07.)
- **adv-c6 F-04 (P3).** Resolved: T-C8's read-only sub-case carries
  "SKIP AS ROOT" with the DAC_OVERRIDE rationale (§8.3, §4.5 row 13).
- **adv-c6 F-05 (P2 → D-49).** Resolved: manual dispatch outcome
  normative for ALL length-2 argv; `-h`/`--help` are path strings;
  argparse builds must disable the builtin help action; T-C1 sub-case
  present; re-verified live (31b V6; 30b P4).
- **SR5-F-01 (P2).** Folded: §4.5 Error paths bullet now carries the
  D-46 successful-open qualifier ("WHICH MEANS after a SUCCESSFUL open
  only (D-46)").
- **SR5-F-02 (P3).** Folded: §5.1 WRITE_OUTPUT edges relabeled per
  D-43/D-46 with the pointer note to §4.5. (One edge's wording:
  SR6-F-06.)
- **Traceability (§11, axis 2).** REQ-001..014 / NFR-001..005 all
  mapped with invariants, failure ids, test layers, evidence; the
  D-01..D-49 coverage paragraph binds every register row; spot-checks
  against the APPROVED text passed (REQ-001 usage-exit-1 + D-49
  argv-of-length-2; REQ-002 duplicate/empty-name; REQ-005 verbatim;
  REQ-007 prefix-all + verbatim interpolation; REQ-009
  blank/BOM-only/whitespace; REQ-010 no-output-on-error + mid-write
  remove + at-open survival; REQ-011 line-4 CR-only; REQ-013 all seven
  AC shapes incl. S-9b; REQ-014 CR/CRLF byte-exactness). §2.4 matches
  REQ §3.2; nothing invented; nothing reinterpreted. The register-row
  staleness (SR6-F-02) is the one axis-2 breach.
- **Test layers vs risk layers (axis 3).** Write semantics on the real
  filesystem (/dev/full, non-writable dir, read-only target,
  assert-or-accept aliasing matrix); E2E through the one external seam;
  E-MEM via RLIMIT_AS environment control with an honest fallback;
  pure semantics at unit seams; the one mutation surface answers all
  13 questions with D-46-consistent answers. QC-1..QC-6 EV tuples
  complete in form; QC-2's compensation clause is the one tuple whose
  mechanism does not deliver its scope everywhere (SR6-F-01).
- **Evidence re-run this cycle:** designer battery 13 (63/63), 20
  (21/21), 22 (19/19), 30 (TOTAL FAILURES: 0), 30b (8/8), 15-selfcheck
  (PASS), 14-claim-keyword (0 hits); reviewer probes 31b (14/14);
  25/28/28b crash stale (SR6-F-03).

## Verdict block

```
verdict: FAIL
artifact: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/spec/07-spec-v7.md
findings_file: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/31-review-spec-c6.md
findings:
- [SR6-F-01|P1|needs-user:false] §4.5 reference shape + QC-2: the except-scoped shape never closes the fd on the failure path — on Windows os.remove on the open handle raises PermissionError (swallowed), the partial file SURVIVES, and no EV tuple/risk row/platform scope records it -> pin close-before-remove in the failure arm (and in register D-48), keeping QC-2 unscoped (recommended), or scope QC-2 to POSIX with a Windows risk row
- [SR6-F-02|P1|needs-user:false] register rows D-46/D-43 still prescribe the try/finally reference shape D-48 superseded (its finally deletes every successful run's output) — machine-parsed register contradicts the spec, D-32 hygiene breach -> refresh both rows to the except-scoped v7 shape citing spec/07 §4.5
- [SR6-F-03|P2|needs-user:false] header probes row cites appendix/25/28/28b which now crash on the archived spec/06 path (rollover staleness, 3rd occurrence of the class) -> re-aim at v7 or annotate as historical evidence superseded by 30/30b
- [SR6-F-04|P2|needs-user:false] T-C16 write-phase-form assertion "(or byte-identical)" slack admits a compensation-less build on the byte-identical branch -> delete the parenthetical or name a mechanism that can produce it
- [SR6-F-05|P3|needs-user:false] §4.5 op-order (3) describes a with-block close; the D-48 reference shape uses manual close -> reword to cite the reference shape's manual close (with-block only as a semantics-preserving equivalent)
- [SR6-F-06|P3|needs-user:false] §5.1 edge "MemoryError(pre-open encode: no compensation)" — nothing is open there, so no compensation is POSSIBLE, not merely not fired -> relabel "filesystem untouched (nothing open)"
- [SR6-F-07|P3|needs-user:false] §10.1 R-4 rationale leans on the tautology "no REQ promises same-path semantics" -> drop/demote it; the closed-catalog and legitimate-in-place-conversion reasons carry the rationale
summary: all seven v7 folds (adv-c6 F-01..F-05, SR5-F-01/F-02) verified genuine, live-probed, wired; traceability and test layers clean; 2xP1 — the D-48 fold half-fixed its own fd-close defect charge (Windows partial-file survival, unrecorded) and the machine-parsed register still prescribes the superseded try/finally shape in D-46/D-43; evidence: appendix/31b probes 14/14 PASS, designer battery re-run all green
```


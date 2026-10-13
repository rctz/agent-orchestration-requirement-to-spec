# Final report — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js (tool name: `csv2json`) |
| kind | final-report (DERIVED artifact — generated from the authoritative files, never a second source of truth) |
| date | 2026-09-20 |
| author | req2-orchestrator |
| verdict | **READY** — all gates passed; the bundle can be handed to a code implementor |
| project root | /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/ |

If this report and the bundle disagree, the bundle wins.

## 1. What was produced

From the one-paragraph intake (appendix/00-intake.md, 2026-09-16 17:26) the
lab produced a fully-reviewed requirements set and a buildable implementation
spec for `csv2json` — a single-file, stdlib-only Python 3.9+ CLI that converts
a UTF-8 CSV file with a header row into a compact single-line JSON array of
flat objects (all values verbatim strings, raw non-ASCII, `ensure_ascii=False`),
with a two-valued exit contract (0/1), an 11-message error catalog with
D-28-based physical line numbers, strict UTF-8 decode, BOM strip, per-record
structural validation (field count, duplicate headers, unterminated quotes
with N/M line reporting), and a fail-safe binary write stage
(encode-before-open, delete-on-failure compensation, KI windows contracted).

- Requirements: 19 REQ/NFR ids (REQ-001..014 + NFR-001..005), 7 versions,
  approved at v7 after 5 review cycles.
- Spec: 12 sections + traceability matrix (every REQ covered, nothing
  invented), 16 versions, approved at v16 after 14 spec-review dispatches,
  16 adversarial cycles, and 17 mechanical-validation runs.
- Decision register D-01..D-59 (all DECIDED), seeded by 6 verbatim user
  answers (Q-01..Q-06) in 2 question rounds.

## 2. Approvals trail (every gate, with dates and file links)

Paths below are relative to the project root
`/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/`.

| # | gate | verdict | date | evidence |
|---|---|---|---|---|
| 1 | req-review cycle 5 (final) | **PASS** — 0 P0, 0 P1, 0 P2, 2 P3 advisory | 2026-09-17 | appendix/12-review-req-c5.md (cycles 1-4 FAIL: appendix/04, 06, 07, 09) |
| 2 | USER APPROVAL (`req2 approve`) | **APPROVED** | 2026-09-17 09:14 | appendix/01-user-decisions.md ("User gate decision — APPROVED"); STATE.json `user_approval` (req_review_cycle 5, requirements/07-requirements-v7.md); header flipped to `status: APPROVED` |
| 3 | spec-review cycle 14 (final, on spec v16) | **PASS** — 0 P0, 0 P1, 0 P2, 0 P3 | 2026-09-20 | appendix/93-review-spec-c14.md (13 probes re-run live, all rc=0) |
| 4 | mechval re-check after spec-review PASS | **PASS** — 0 findings | 2026-09-20 04:45 +0700 | appendix/31-mechval-c16.md (run id spec-design#16, mode gate) |
| 5 | adversarial review cycle 16 (early twin, merged with spec-review#14) | **PASS** — 0 P0, 0 P1, 2 P2 + 1 P3 registered advisory | 2026-09-20 | appendix/94-adv-c16.md (probes 91/92/93 run live) |
| 6 | mechval final (C13 adversarial coverage + C14 APPROVED checks) | **PASS** — 0 findings | 2026-09-20 05:16 +0700 | appendix/32-mechval-c16.md (run id parallel-merge#16, mode final) |
| 7 | spec APPROVED | `status: APPROVED` flipped in header | 2026-09-20 | spec/16-spec-v16.md line 8 |
| 8 | cold-audit cycle 1 | **READY** (board mapping: PASS) — zero blocking questions; 6 non-blocking assumptions (A-1..A-6), 3 evidence-status notes | 2026-09-20 | appendix/95-coldaudit-c1.md; board card t_ef3d0126 done, completion comment `verdict: PASS` |

History note (why 16 spec cycles ≠ 15 failures): intermediate spec-review
PASSes at cycles 4, 5, 12, 13 each later fell at adversarial review
(appendix/29-adv-c6.md, 65-adv-c13.md, 72-adv-c14.md) or mechval
(appendix/30-mechval-c15.md, probe-path-stale) and re-entered spec-design —
the verdict trail above lists only the gates that stand for v16. Verdict
counts here are extracted from the review artifacts, not from cycle numbers.

## 3. Handoff bundle (what to give the code implementor)

| file | role |
|---|---|
| requirements/07-requirements-v7.md | Requirements, status APPROVED (19 REQ/NFR ids, acceptance criteria, user-decision provenance) |
| spec/16-spec-v16.md | Implementation spec, status APPROVED (§4 module design, §5 state machines, §6 interface contracts incl. §6.3 error catalog, §8 verification plan, §9 NFR mapping, §11 traceability matrix) |
| appendix/03-decision-register.md | Decision register D-01..D-59, all DECIDED, each with rationale |
| appendix/01-user-decisions.md | Verbatim user answers Q-01..Q-06 + the user gate approval |
| spec/16-spec-v16.md §6.3 | Error contract: closed 11-message catalog with verbatim interpolation rules |
| spec/16-spec-v16.md §11 | Traceability: every REQ/NFR → spec section → test id |
| spec/16-spec-v16.md §8 | Verification plan (unit / contract / E2E layers, T-U*/T-K*/T-C* ids) |
| spec/16-spec-v16.md §2.3-§2.4, D-58/D-59 | Explicit implementation freedoms (two-quantity vs fused parse form both conforming; argparse non-conforming — manual dispatch is the ONE shape) |
| appendix/advisory-register.md | Deferrals: P2/P3 advisory rows with owners (see §4) |
| spec/16-spec-v16.md §10.1 | Risk register R-1, R-1b, R-2..R-6 (claims that are NOT guarantees, with owners) |
| appendix/95-coldaudit-c1.md | Cold-audit: implementor simulation, 28-contract inventory, assumptions A-1..A-6 |

## 4. Open P2/P3 notes (owner + disposition)

Currently open, named by the cold audit (appendix/95 §9), owner spec-designer,
all wording/gate-coverage class with zero behavior change — non-blocking per
board policy:

| id | severity | subject | disposition |
|---|---|---|---|
| adv-c16 F-01 | P2 | §6.3/§12 "default CPython stderr preserves UTF-8 verbatim" over-broad for argv-borne surrogate paths (wire form is environment-controlled; message-STRING rule honored) | open, registered (advisory-register rows 226-228) |
| adv-c16 F-02 | P2 | §4.3 Interface line `parse(text)` vs prose `parse(text, input_name)` arity wording | open; cold-audit A-1/A-2 resolve it per the reviewer's own preference (two-arg form) — cannot change an observable byte |
| adv-c16 F-03 | P3 | header claims probes 66/77 + 13/14/15 LIVE; gate 88's LIVE list omits 66/14/15 (all verified green manually in cycle 16) | open, evidence-hygiene only |

The advisory register additionally carries 10 legacy `open` P2/P3 rows
(adv-c6-F-03/F-04/F-05, SR6-F-03..F-07, SR13-F-01/F-02 — opened against
superseded revisions; several substantively addressed by later rollover
folds but their rows were never closed) and 3 `deferred` rows (F-35,
SR5-F-01/F-02) — every row names an owner (spec-designer); none is
behavioral, and the cold audit confirmed none blocks implementation.
Full list: appendix/advisory-register.md (13 open + 3 deferred).

## 5. Readiness metrics snapshot

- P0/P1 at the final gates: **0** (spec-review c14: 0 findings; adv-c16:
  0 P0/P1; mechval final: 0 findings; cold-audit: 0 blocking questions).
- mechval: 17 runs total (15 PASS / 2 FAIL, each FAIL exactly 1 × P1:
  appendix/10-mechval-c1.md claim-without-evidence, appendix/30-mechval-c15.md
  probe-path-stale; both fixed and re-run PASS). N/A count: 0 in every run.
- Adversarial classes N/A (justified, with approving reviewer disposition):
  stale-read/lost-update (no cross-run state — §7.1 taxonomy note),
  corrupt/version-incompatible persisted data (no schema persisted),
  invalid/caller-controlled authorization context (no auth layer, REQ §2),
  duplicate/out-of-order events (no event fabric — batch converter).
- ASK_USER rounds: 2 (2026-09-16 17:38 Q-01..Q-04; 17:53 Q-05..Q-06),
  plus 1 user gate decision (approve, 2026-09-17 09:14).
- Wall-clock intake → READY: 2026-09-16 17:26 → 2026-09-20 05:21 (+07) =
  3.5 days (~84 h).
- Trend metrics: appendix/06-metrics.md.

## 6. Next step

Hand the §3 bundle to a code implementor. The cold audit's own build plan
(appendix/95-coldaudit-c1.md §2: single file `csv2json.py`, pinned imports
`csv, io, json, os, sys`, build order 1→2→5→3→4→7→8→9→6) is a validated
starting point. Post-handoff defect feedback:
`req2 defect i-need-a-small-command-line-tool-csv2js <area> "<note>"`.

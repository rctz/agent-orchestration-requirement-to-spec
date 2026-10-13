# Adversarial-early review — cycle 8 (appendix/33-adv-c8.md)

| field | value |
|---|---|
| card | t_cd6dc833 — [i-need-a-small-command-line-tool-csv2js#adv-early#8] |
| target | spec/08-spec-v8.md (status DRAFT, 2026-09-19, 1630 lines) |
| reviewer | req2-adv-reviewer (early-mode twin, parallel with spec-review cycle 7) |
| probes | appendix/33b-adv-c8-probes.py — 7/7 PASS, 2026-09-19 (P5 ran against register + §11 mechanically) |
| verdict | FAIL — 1 P1 (F-01), 2 P2 (F-02, F-03), 1 P3 (F-04) |
| scope note | EARLY MODE: this verdict feeds the router's merge with spec-review cycle 7; the spec is not expected to change from this card alone |

Method: inventory the mutation surfaces and external boundaries from the
spec itself, then attack each with the 13 scenario classes; every finding
carries a minimal counterexample, executed live where the platform allows
(probe ids P1..P5). Sections 1–4 below.

## 1. Mutation-surface & boundary inventory (status: COMPLETE)

Derived from the spec's own mechanisms (§2.1 pipeline, §4 stage designs,
§5.1 state machine). The tool is a single linear process with exactly one
state-mutating stage (S5 write) plus process-visible boundaries at argv,
stdio, and the two filesystem paths.

| # | surface / boundary | kind | spec anchor | notes for scenario derivation |
|---|---|---|---|---|
| M1 | argv dispatch (`len(argv) != 2` branch) | caller input boundary | §4.1, D-34/D-41/D-49 | option-looking positionals are path strings (D-49); argparse builds conditionally sanctioned (D-41 register row) |
| M2 | input read (`read_raw`) + strict UTF-8 decode + BOM strip | read boundary (external dep: filesystem, encoding) | §4.2, REQ-011/012, D-13/D-16/D-23/D-28/D-31 | E-READ/E-UTF8; line number of offending byte via prefix decode |
| M3 | parse loop (csv.reader over StringIO newline="") | pure computation, no mutation | §4.3, D-15/D-24/D-25/D-29/D-30/D-36 | header rules → per-record quote scan → count check, sequential |
| M4 | serialize (json.dumps) | pure computation | §4.4, D-17/D-26/D-44 | no side effect; MemoryError → E-MEM write-phase form |
| M5 | write stage: encode → open(path,"wb") → write → flush → close | THE mutation surface (output file create/truncate/write/remove) | §4.5, D-43/D-45/D-46/D-47/D-48/D-50, D-33 compensation | trigger = every exception after a successful open; except-scoped reference shape; close-before-remove |
| M6 | compensation `os.remove(path)` | mutation (unlink) | §4.5, D-33/D-46/D-50 | best-effort, name-scoped (R-1b aliasing), same-path (R-4) |
| M7 | stderr print (single message, one write) + exit code | output boundary | §4.1, §6.3, §6.4, QC-1, R-3 | closed-stderr failure degrades (QC-1 Failure clause) |
| M8 | startup limit raise (`csv.field_size_limit`) | process-global state at import | §4.6, D-21/D-27 | cannot fail (halving loop) |
| M9 | signals: SystemExit/KeyboardInterrupt pass-through (not caught) | process boundary | §7.3 last sentence | interacts with M5's BaseException-scoped arm — F-01 |
| M10 | main's residual net order: MemoryError → ToolError → Exception | control boundary | §7.3, D-42 | E-NET repr may carry data-borne newline |
| M11 | concurrent runs on one target | out-of-scope boundary (recorded) | §4.5 row 9, R-2 | accepted scope boundary |
| M12 | input path == output path | aliasing boundary (recorded) | R-4, S-1 note | failed run deletes the input |
| M13 | output path is symlink/hardlink | aliasing boundary (recorded) | D-47, R-1b | name removed, aliased inode may hold partial |

Inventory status: COMPLETE — 13 surfaces/boundaries, all attacked or
 dispositioned in §2.

## 2. Scenario table per class (status: COMPLETE)

Legend: ✔ = spec's contract survives the attack (with spec anchor); ✘ = the
attack breaks or bifurcates the contract (finding); ✔-boundary = attack
outside the contracted scope, recorded as accepted risk/scope boundary with
an anchor. Every ✘ cites its finding; every ✔ carried forward from earlier
cycles is anchored so this table is self-contained.

| class | surface(s) | injection point / starting state | injected failure or action | expected observable result (per spec) | invariant that must hold | durable state after | rollback/ compensation | error contract | retry behavior | test layer | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| duplicate/double-submission | M5 | valid CSV; fresh output path | run the tool twice back-to-back | second run truncates+rewrites the target; both exit 0 | last successful run's bytes define the file (§4.5 row 8) | target = run-2 bytes | none needed (replace semantics) | none | clean (§4.5 row 7) | E2E T-C2 byte-exact case | ✔ (§4.5 rows 7/8) |
| retry-after-partial-success | M5 | valid CSV; prior good output exists; mid-write ENOSPC | failed run then rerun after freeing space | failed run removes partial (D-33/D-46); rerun replaces cleanly | no plausible-complete partial survives a failed run | absent after failure; rewritten after retry | D-33 best-effort remove, every exception post-open | E-WRITE (§6.3) | clean (§4.5 row 7) | E2E T-C8 /dev/full | ✔ (D-43/D-46/D-50) |
| concurrent execution | M11 | two processes, one target | interleave writes / compensation unlinks concurrent winner | no promised outcome; exit-0 run can end with NO file | none promised (out of REQ §2 scope) | any of the recorded outcome set | none (no lock designed in) | per-run classes unchanged | not promised | documented probe class (appendix/26b P12) | ✔-boundary (R-2) |
| stale-read/lost-update | M2/M5 | — | read-modify-write race on one file | N/A — the tool holds no cross-run state; every run re-opens both paths (§7.1 taxonomy note) | — | — | — | E-READ/E-WRITE on vanished paths | fresh state per run | N/A per §7.1 | N/A (no cross-run state exists) |
| partial failure at each async boundary | M5/M6 | valid CSV; prior output exists | fault at encode / at open / mid-write / at flush / at close | encode: bytes survive (D-43); open: bytes survive (D-46); post-open: partial removed (D-33/D-46/D-50) | QC-2: no created-or-truncated target on any failed run | phase-dependent (S-14(d)/(e)) | D-33 (post-open only) | E-WRITE / E-MEM write-phase | clean (row 7) | E2E T-C8, T-C16 | ✔ (boundaries individually pinned) |
| timeout/cancellation — SIGKILL | M5 | mid-write, any build | SIGKILL the process | partial file remains (no handler can run) | none promised (accepted scope boundary) | partial file possible | none possible | none (process dead) | user-driven | outside contract | ✔-boundary (§7.1 kill note, R-2 class) |
| timeout/cancellation — SIGINT (Ctrl-C) | M5+M9 | prior output exists; spec's §4.5 reference shape reaches mid-write | SIGINT arrives; `fd.write` raises KeyboardInterrupt | reference shape's BaseException arm removes the partial (P1); an `except Exception` build (sanctioned by §7.3's KI-not-caught) leaves it (P1-control) | QC-2 (§7.1 taxonomy claims this class N/A with "leaves whatever partial output existed at kill time") | REMOVED vs SURVIVES — opposite states under the same spec | reference: remove runs; variant: none | reference: KI re-raised → exit 130 + traceback (P2), outside 0/1 + QC-1 wording | n/a (user abort) | T-C8 class (fault injection) | ✘ → **F-01 (P1)** |
| refresh/restart/crash mid-operation | M5 | mid-write | process crashes (power loss, SIGKILL) | partial file remains; accepted boundary | none promised | partial possible | none possible (dead process) | none | user-driven | outside contract | ✔-boundary (same §7.1 note, kill form) |
| unavailable dependency | M2/M5 | disk full; perms; /dev/full | ENOSPC/EACCES at read or write boundaries | E-READ / E-WRITE shapes; at-open failure leaves target untouched (D-46) | REQ-010 absent-or-unchanged for pre-open/at-open faults | phase-dependent | D-33 post-open only | §6.3 E-READ/E-WRITE | clean | E2E T-C2/T-C8 | ✔ |
| unavailable dependency — stderr closed | M7 | error path with closed fd 2 | print raises | QC-1 Failure clause: nonzero exit, never 0/traceback | degraded-failure visible | n/a | best-effort print wrap | degraded (documented) | n/a | not asserted (assumption-class) | ✔-boundary (R-3) |
| corrupt/version-incompatible persisted data | M2 | invalid UTF-8; multi-byte invalid sequences; BOM positions | strict decode failure | E-UTF8 at offending byte's own D-28 line (§4.2 F-04 note) | QC-4 line-number basis | no output written | n/a (nothing opened) | §6.3 E-UTF8 | deterministic-fail | E2E T-C3 | ✔ |
| duplicate/out-of-order events | M3 | — | N/A — batch converter, no event queue, no timers | — | — | — | — | — | — | — | N/A (no event fabric exists) |
| invalid/caller-controlled authorization context | M1/M5 | — | N/A — single-user CLI, no auth layer (REQ §2; §4.5 row 1: whoever can execute and write) | — | — | — | — | — | — | — | N/A (design has no auth surface) |
| boundary/oversized inputs — content | M2/M3/M4 | 10 MB field; NUL/VT/FF; <script> | huge/corrupt cells | limit raised (§4.6); values inert strings; escapes per D-14/D-20 | QC-6 inertness | output valid JSON | n/a | E-MEM if OOM | bounded by NFR-003 envelope | T-C13/T-U8 | ✔ |
| boundary/oversized inputs — argv/paths | M1/M2/M7 | argc 0/1/3; `-h` as positional; POSIX-legal newline-bearing path | option-looking or control-character path strings | E-USAGE / E-READ exit 1 (D-49); path interpolated verbatim → single stderr write wraps (P4) | NFR-004 stdout empty; §6.3 "exact message template" per class | no file created | n/a | E-USAGE/E-READ | clean | E2E T-C1/T-C2 | ✔ behavior; ✘ catalog scope → **F-04 (P3)** |
| initialization/recovery failure | M8 | import time | OverflowError loop | halving loop terminates (P5 probe of cycle-1) | huge fields never hit 131072 cap | n/a | n/a | none | n/a | T-U8 | ✔ |
| build-shape freedom bifurcation | M1+M5 (sanctioned alternative builds) | implementor picks §4.1's argparse branch or an `except Exception` variant | two conforming-reading builds on the same inputs | both sanctioned → observable divergence on `-h` alone (P3b), stdin/stderr channels, Ctrl-C state (P1) | NFR-004 (stdout empty), QC-2 (state after failed post-open run) | divergent states allowed by text | variant-dependent | divergent outcomes | n/a | T-C1 sub-case / T-C8 class | ✘ → **F-02 (P2)** (argv channel), folded into **F-01** (Ctrl-C state) |
| spec-internal consistency (machine-checked) | §11 vs register | D-50 appended in v8 | mechanical range check | §11 says "D-01..D-49 are all DECIDED" while D-50 exists DECIDED | §11's own "Nothing uncovered; nothing invented" | n/a | n/a | n/a | n/a | probe P5 | ✘ → **F-03 (P2)** |

Scenario table status: COMPLETE — 13 classes covered: 9 ✔ (anchored), 3
✔-boundary (anchored to accepted-risk/scope records), 4 ✘ rows mapping to
4 findings (F-01..F-04); 3 classes N/A with justification (stale-read,
duplicate events, authorization — no cross-run state, no event fabric, no
auth surface).

## 3. Findings (status: COMPLETE)

Summary table (full records below):

| F | severity | sections | one-line |
|---|---|---|---|
| F-01 | P1 | §7.1 taxonomy note; §7.3 last sentence; vs §4.5 reference shape (D-48/D-50) | Ctrl-C (SIGINT) mid-write: the spec's own reference shape contradicts §7.1's kill-state claim — two sanctioned readings leave opposite durable states |
| F-02 | P2 | §4.1 + register D-41 vs §9 NFR-001 row; §4.1 disable-help scope | sanctioned argparse build flunks the spec's own NFR-001 imports audit and diverges on argv length ≠ 2 with help on stdout |
| F-03 | P2 | §11 decision-coverage sentence | "D-01..D-49" stale after D-50 was appended — same class as SR3-F-02 |
| F-04 | P3 | §6.3 verbatim-slot enumeration | the `<path>` interpolation slots are missing from the verbatim/wrap-allowed slot list, leaving the "exact message template" phrase over-broad |

### F-01 [P1 | axis: cancellation semantics vs compensation trigger | needs-user:false]

- **section/artifact:** spec/08-spec-v8.md §7.1 taxonomy coverage note (timeout-cancellation clause, lines 1119–1122); §7.3 last sentence (lines 1153–1155); §4.5 reference shape (lines 639–653) and D-48/D-50 register rows; QC-2 Scope (lines 1284–1292).
- **claim:** §7.1's taxonomy note asserts that cancellation ("the user killing the process") "leaves whatever partial output existed at kill time — outside the tool's contract, recorded as an accepted scope boundary", and §7.3 asserts `SystemExit`/`KeyboardInterrupt` are "NOT caught (process-level signals pass through)". D-48 pins the compensation arm's scope as **BaseException**, and D-50/QC-2 pin the state contract ("the target is removed ... whatever exception class the failure raised, ON EVERY PLATFORM") with no exception for KeyboardInterrupt.
- **evidence (live, probe P1/P1-control/P2):**
  1. Spec's own §4.5 reference shape, KI raised at `fd.write`, prior output present: **file REMOVED**, KI re-raised uncaught → exit 130 with a traceback. So the reference build's observable behavior is the exact opposite of "leaves whatever partial output existed at kill time".
  2. A build that wraps the write stage in `except Exception:` (entitled by §7.3's "KeyboardInterrupt NOT caught" + E-NET's `except Exception` net in §7.3) on the identical Ctrl-C: **partial file SURVIVES**, matching §7.1's kill-note — but then QC-2's mechanism (compensation on EVERY exception class post-open) does not hold for the KeyboardInterrupt class in that build.
  3. Uncaught KI exits 130 (or −2 in subprocess terms) with a traceback on stderr — outside §6.4's two-valued matrix and QC-1's no-traceback wording.
- **minimal counterexample:** user runs `python csv2json.py in.csv out.json` where out.json already holds the user's prior good data; mid-write the user presses Ctrl-C. Build A (spec reference shape, BaseException arm): out.json is gone; exit 130; traceback. Build B (`except Exception`): out.json holds a truncated/partial document; exit 130. The spec simultaneously asserts (§7.1) that the partial survives, (QC-2) that the compensation triggers on every exception class post-open, and (§7.3) that KI is not caught — all three cannot hold at once across the sanctioned build set; two conforming-reading builds leave opposite durable states, and neither state contract is testable as pinned (T-C8's fault-injection classes never include a KI injection).
- **impact:** the implementor must choose material behavior for Ctrl-C mid-write (remove vs keep partial; catch-and-report vs re-raise) with no normative anchor; the cold auditor cannot derive the expected post-Ctrl-C state from the document; QC-2's "every exception class" wording is falsified by the build the spec itself prints in §4.5 when that build is read with §7.3's KI clause, and §7.1's kill-state claim is falsified by that same build.
- **required disposition:** pin one coherent story for KeyboardInterrupt/SIGINT: either (a) KI remains outside the contract — then §4.5's arm scope must be `except Exception` (with the D-50 close-before-remove retained inside), the v8 probe P4 KI evidence re-aimed, and QC-2's "every exception class" + D-48's BaseException wording qualified ("every exception class the residual net sees; KeyboardInterrupt/SystemExit deliberately not compensated"); or (b) KI is compensated — then §7.1's "leaves whatever partial output existed" is deleted/qualified to SIGKILL-only kills, and the exit-code/traceback consequence (exit 130, traceback, outside 0/1) is recorded (risk record or §6.4 note). Spec-designer decides; T-C8 gains an explicit KI-injection sub-case under the chosen story.
- **decision owner:** spec-designer (behavior choice); user only if the product wants Ctrl-C to be a first-class "clean cancel" UX.
- **verification required:** mechval re-run (final-mode C15 will block on any unregistered P2/P3 — see F-02/F-03/F-04 rows below); spec-review cycle 8 convergence on the merged fix list.

### F-02 [P2 | axis: sanctioned build bifurcation / verification alignment | needs-user:false]

- **section/artifact:** §4.1 (argparse acceptability clause, lines 236–247) + register D-41 vs §9 NFR-001 row (line 1244) + §4.1's disable-help scope ("for this two-positional form") + §6.4 matrix; probes P3a/P3b.
- **claim:** §4.1 sanctions an argparse build "ONLY if it overrides both the exit code (1) and the message shape ... on every error path" and disables/overrides "argparse's builtin help action **for this two-positional form**". §9's NFR-001 row pins the audit as "imports only `csv, io, json, os, sys`" and NFR-001's verification anchor says "T-C-suite imports audit (the test asserts the module's import set)".
- **evidence (live, probes P3a/P3b):**
  1. The sanctioned argparse build imports `argparse` — the §9-pinned imports audit fails it (set `{argparse, csv, io, json, os, sys}` ⊄ `{csv, io, json, os, sys}`), while the REQ's own NFR-001 wording (stdlib-only) passes it. The spec's audit spec must choose which build set it certifies.
  2. `-h` alone (argc==1, not the two-positional form): manual dispatch → prefixed usage, exit 1, stdout empty; argparse default → help text on **stdout**, exit 0. §4.1's disable-help clause scopes itself to "this two-positional form" (length-2 argv), so a conforming argparse build may keep default help for length-1/3 argv — an outcome class NFR-004 (stdout empty on every path) forbids and §6.4 has no row for. D-49's "NORMATIVE for ALL argv of length 2" wording deliberately scoped to length 2 leaves ≠2 lengths as an argparse freedom that contradicts NFR-004.
- **minimal counterexample:** implementor A ships manual dispatch, passes the imports audit. Implementor B follows §4.1's argparse branch (overrides error paths and two-positional help per D-49); B's tool runs `csv2json.py -h` → help on stdout, exit 0 — NFR-004 violation in a sanctioned build; and B cannot pass the §9 imports audit at all.
- **impact:** a sanctioned build cannot pass the spec's own NFR-001 audit; observable stdout/exit divergence on argc≠2 between sanctioned builds; T-C1's `-h` sub-case only pins the length-2 form.
- **required disposition:** pick one: (a) drop the argparse alternative entirely (simplest, matches §2.2/§9 import list and ADR-ish minimalism — the manual dispatch is already normative); or (b) keep it but rewrite §9's NFR-001 row as "csv, io, json, os, sys **plus argparse if the §4.1 argparse branch is used**", and widen D-49/§4.1's help-override scope from "this two-positional form" to ALL argv lengths (help must never reach stdout, exit must be 0/1 only). Either resolves both half-defects.
- **decision owner:** spec-designer.
- **verification required:** mechval re-run; T-C1 sub-case extension if (b).

### F-03 [P2 | axis: spec-internal consistency | needs-user:false]

- **section/artifact:** §11 decision-coverage sentence (line 1516: "Decision-coverage check: D-01..D-49 are all DECIDED") vs appendix/03-decision-register.md (51 DECIDED rows, maximum id D-50) and §1 line 23 ("D-01..D-50 ... are all DECIDED").
- **claim:** §11 claims complete decision coverage with range D-01..D-49; the register and §1 say D-01..D-50.
- **evidence:** mechanical (probe P5): register max id = 50 (D-50 DECIDED, bound in §4.5/QC-2/§11 REQ-010 row); §11 sentence reads D-01..D-49; the very next paragraph (§11 v8 note) documents the D-50 append.
- **minimal counterexample:** a coverage checker trusting §11's sentence reports D-50 unbound (covered only by the later REQ-010 row's prose binding) and flags a phantom gap D-50 for every reader of the sentence alone; an implementor reading only §11's coverage claim is told the decision set ends at D-49.
- **impact:** minor editorial drift; but same class as SR3-F-02 (cycle 3, P2, stale enumeration) — the board has treated stale enumerations as P2 habitually.
- **required disposition:** one-word fix: "D-01..D-50". Register hygiene per D-32.
- **decision owner:** spec-designer.
- **verification required:** mechval re-run (C15 will block on an unregistered P2 — register row appended, see §4).

### F-04 [P3 | axis: error-message catalog completeness | needs-user:false]

- **section/artifact:** §6.3 catalog verbatim-slot enumeration (E-DUP note, lines 1053–1067): "this verbatim discipline applies to EVERY interpolated-data slot in the catalog: E-DUP's `<name>`, E-NET's `<exception repr>` ..., and the OS `<strerror>` in E-READ/E-WRITE."
- **claim:** the enumeration names three slot kinds; but every template's `<path>` slot (E-READ `<in>`, E-UTF8 `<in>`, E-EMPTY `<in>`, E-HEADER0 `<in>`, E-DUP `<in>`, E-COUNT/E-UQ `<in> line N`, E-WRITE `<out>`, E-MEM `<in>`/`<out>`) also interpolates caller-controlled data (the path string from argv) verbatim.
- **evidence (live, probe P4):** a POSIX-legal input path containing a raw newline (`touch 'in\nbad.csv'`) exists; the E-READ template `csv2json: error: cannot read <in>: <strerror>` with `<in>` = that path produces a single stderr write that physically wraps across lines — behavior identical in kind to the E-DUP newline-name case the note documents, but the `<path>` slots are absent from the enumeration.
- **minimal counterexample:** an implementor reading the note's "EVERY interpolated-data slot" list concludes paths are exempt (or sanitized), sanitizes the path in E-READ, and a T-K1 parametrization over path forms has no row for it — a build whose stderr differs on a legal path from the reference build's, with no clause deciding which is conforming.
- **impact:** local wording gap; T-K1's parametrized forms ("plain, empty, and a newline-bearing name") cover only E-DUP name forms.
- **required disposition:** add the `<path>` slots to the verbatim-slot enumeration (one clause), and optionally a T-K1 parametrization note for a newline-bearing path form.
- **decision owner:** spec-designer.
- **verification required:** mechval re-run; advisory-register row (auto, P3).

## 4. Coverage summary (status: COMPLETE)

| metric | value |
|---|---|
| mutation surfaces / boundaries inventoried | 13 (M1–M13, §1) |
| scenario classes attempted | 13/13 — none skipped |
| classes with ✘ verdicts | 4 rows → 4 findings: F-01 (P1), F-02 (P2), F-03 (P2), F-04 (P3) |
| classes ✔ or ✔-boundary | 9 ✔ anchored + 3 ✔-boundary (R-2 concurrency, R-3 closed-stderr, §7.1 kill-form) |
| classes N/A (justified) | 3: stale-read/lost-update (no cross-run state exists — §7.1 taxonomy note), duplicate/out-of-order events (no event fabric, batch converter), invalid/caller-controlled authorization context (no auth layer, REQ §2 / §4.5 row 1) |
| live probes | appendix/33b-adv-c8-probes.py — 7/7 PASS 2026-09-19 (P1, P1-control, P2, P3a, P3b, P4, P5) |
| P0 | 0 |
| P1 | 1 (F-01) |
| P2 | 2 (F-02, F-03) |
| P3 | 1 (F-04) |
| verdict | **FAIL** — any P0/P1 → FAIL per board policy |

### N/A approver note

The three N/A classes carry no risk of hidden exposure: each names a
structural absence in the design (no cross-run state, no event fabric, no
auth surface), each anchored to a spec clause that says so. Approver for
the N/A set: req2-adv-reviewer (this card), as in prior cycles.

### Advisory-register mirror (P2/P3 rule)

Per the card protocol's P2/P3 mirror rule, rows appended to
appendix/advisory-register.md (disposition: open — this verdict feeds the
router's merge; disposition becomes fixed-in-v9 once the merge lands):

| F | severity | disposition | owner |
|---|---|---|---|
| F-02 | P2 | open (adv-c8: argparse build vs §9 imports audit + `-h`-alone divergence; see appendix/33-adv-c8.md) | spec-designer |
| F-03 | P2 | open (adv-c8: §11 "D-01..D-49" stale, register max is D-50; probe P5) | spec-designer |
| F-04 | P3 | open (adv-c8: `<path>` slots missing from §6.3 verbatim-slot enumeration; probe P4) | spec-designer |

Registration note: the register's own header says dispositions are one of
fixed-in-vN / accepted-risk / deferred — `open (...)` is not in that set; I
use it to keep the rows live for the merge (same convention as an
unlanded fixed-in-v9). If the router's merged fix list closes them in v9,
the disposition flips to `fixed-in-v9` in the next cycle's pass.

Report complete — t_cd6dc833, 2026-09-19.

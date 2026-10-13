# Adversarial-early review — cycle 6 (adv-c6)

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | adversarial-early (parallel gate, twin of adv-review) |
| target | spec/06-spec-v6.md (status DRAFT, 2026-09-17) |
| reviewer | req2-adv-reviewer |
| date | 2026-09-17 |
| method | mutation-surface + boundary inventory derived from the spec itself; per-class scenario derivation; MINIMAL COUNTEREXAMPLE per finding; live probes where the scenario is executable (appendix/29b-adv-c6-probes.py, 13 checks PASS, Python 3.13.5, this workspace; filesystem REAL in every probe — only the fault position is injected, mirroring the spec's own W-series/R6-series evidence method) |
| verdict | FAIL — 2 P1 (F-01, F-02) + 2 P2 (F-03, F-05) + 1 P3 (F-04); P2/P3 mirrored to advisory-register.md |

# 1. Mutation-surface & boundary inventory

Carried from adv-c5 §1 (unchanged surfaces re-audited against v6's
reworked §4.5; new-in-v6 surfaces marked ★):

| # | surface / boundary | spec site | class of attack |
|---|---|---|---|
| M1 | argv dispatch (`len(argv) != 2`) | §4.1, D-41 | boundary input, duplicate call, option-looking args ★ |
| M2 | input read (open/read whole file, bytes) | §4.2 `read_raw`, D-15(2) | unavailable dep (EACCES/ENOENT), oversized input, corrupt data |
| M3 | strict UTF-8 decode + BOM strip | §4.2, REQ-011/012 | corrupt data, boundary offsets |
| M4 | D-28 line arithmetic | §4.2 `line_of_offset`, §4.3.2 incremental | terminator mixes, stale basis |
| M5 | csv parse loop (records, spans via tell()) | §4.3.1/4.3.2 | terminator mixes, oversized fields, check order |
| M6 | header rules | §4.3.4 | empty/unicode names, name with raw newline |
| M7 | unterminated-quote FSM | §4.3.3 | CRLF-in-record counter, M arithmetic, header scope/order |
| M8 | count validation + row build | §4.3.5 | blank/whitespace rows, trailing terminators |
| M9 | serialize (json.dumps compact) | §4.4 | control chars, huge payload (E-MEM serialize, D-44) |
| M10 | output write (the ONLY mutation): D-43 encode → open("wb") → write → flush + every-post-open-exception delete-on-failure (D-46 trigger; D-47 aliasing boundary) | §4.5 | fault position (encode/at-open/write/flush/close), compensation shape ★, target aliasing, device paths, input==output coincidence ★, concurrent writers |
| M11 ★ | the §4.5 "reference shape" code snippet introduced by the D-46 rework (`fd = None; try: fd = open(...); ... finally: if fd is not None: remove(path)`) | §4.5 (compensation-scope block) | does the pinned shape itself implement the pinned state contract? |
| B1 | process boundary: exit codes 0/1, stderr single write | §4.1, §6.4, QC-1 | residual exceptions, stderr closed (R-3), E-MEM/E-NET handler order |
| B2 | filesystem (input side, read-only) | §4.2 | unreadable, mid-run deletion |
| B3 | filesystem (output side, mutating) | §4.5 | pre-existing/absent target, non-regular targets, unwritable dir, read-only target, aliased target, SAME path as input ★ |
| B4 | memory (whole-file in-memory pipeline) | NFR-003/005, E-MEM | OOM at each phase; which E-MEM form T-C16 may observe ★ |
| B5 | interpreter startup (limit raise) | §4.6 | OverflowError degrade loop |

No network, no timers, no queues, no persisted state, no auth layer —
those classes stay structurally N/A (§4).


# 2. Scenario table (per class)

Columns: injection point / starting state / injected failure or action /
expected observable result (per spec) / invariant that must hold / durable
state after / rollback-compensation / error contract / retry behavior /
test layer. "✔" = spec contract complete and internally consistent for the
row; "✘" = gap (finding); "N/A" justified inline. Fault positions and
target states follow adv-c5 §2 with the v6 shapes.

| class | surface | scenario | outcome |
|---|---|---|---|
| duplicate/double-submission | M10 | re-run after success | ✔ §4.5 rows 7/8: no session; successful rerun replaces target wholesale; last successful run's bytes define the file. |
| retry-after-partial-success | M10 | run failed mid-write (E-WRITE), user reruns | ✔ §7.1 E-WRITE "rerun is clean": post-open compensation removed the partial; pre-open/at-open failures left the target untouched (D-43/D-46). |
| concurrent execution | M10 | two runs, same target, overlapping | ✔-boundary §4.5 row 9 + R-2 (v6 reword): NO promised outcome; reachable outcomes include losing both outputs and a silent exit-0 with no file (probe R6-P4 verifies reachability). No property promised — boundary properly recorded (adv-c5 F-03 folded). |
| stale-read/lost-update | B2/B3 | input deleted mid-run; output dir vanishes before write | ✔ §7.1 taxonomy: input re-opened per run (E-READ); output writability discovered by open() (E-WRITE). No cross-run references. |
| partial failure — pre-open (encode) | M10 step (1) | valid input, pre-existing GOOD output, MemoryError at encode | ✔ D-43 encode-before-open → prior bytes byte-identical (W-series, R6-P1). This is the ONE form for which T-C16's byte-identity assertion is true — see F-01 for the other forms. |
| partial failure — at open | M10 step (2) | EACCES on read-only target (writable dir); EACCES absent target; EISDIR; /dev/full | ✔ v6 pinned cleanly: D-46 — open never succeeded → NO compensation runs → target byte-identical whether absent or pre-existing (R6-P2/R6-P3 at-open case). Adv-c5 F-04 folded. |
| partial failure — mid-write/flush | M10 step (3) | ENOSPC/EIO at write or flush; MemoryError mid-write | ✔ every-post-open-exception compensation (D-46 trigger): partial removed, then E-WRITE or E-MEM write-phase form (W-series, /dev/full probe F28). BUT the durable state for a PRE-EXISTING target is "removed", which T-C16 also asserts "byte-identical ... form-independent" → F-01. ✘ the compensation shape's own reference snippet is wrong → F-02. ✘ input==output coincidence unrecorded → F-03. |
| partial failure — at close | M10 with-block exit | OSError at close | ✔ §4.5: flush failures surface inside the `with` before close accounting; close errors are OSErrors → same compensation + E-WRITE. |
| timeout/cancellation | B1 | user kills process mid-write | ✔-boundary §7.1 timeout-cancellation N/A row + no-fsync note: kill/crash leaves whatever partial existed; accepted scope boundary. |
| refresh/restart/crash mid-operation | B1/B3 | process dies between open and write/flush | ✔-boundary same row; OS-level crash outside contract; no fsync pinned (§4.5 error-paths). |
| unavailable dependency — storage full | M10 | ENOSPC at write/flush (/dev/full) | ✔ T-C8, live-verified (F28: open ok → flush errno 28 → compensation EINVAL ignored → E-WRITE shape, no regular-file leftover). |
| unavailable dependency — permission AT open | M10 step (2) | read-only target in writable dir; absent target in unwritable dir | ✔ D-46: no compensation, target byte-untouched, E-WRITE shape (R6-P2). Fold of adv-c5 F-04 verified consistent across §4.5/S-14(b)/§7.1/T-C8/QC-2/§11. |
| corrupt/version-incompatible persisted data | M2/M3 | invalid UTF-8; BOM positions; multi-byte invalid sequences | ✔ E-UTF8 at the offending byte's own D-28 line (§4.2 F-04-of-c3 note); first-invalid byte via e.start; BOM only at start; nothing persisted (§7.1 N/A). |
| duplicate/out-of-order events | n/a | no event sources (single-shot CLI) | N/A — no queues/timers/signals in the design. |
| invalid/caller-controlled authorization context | n/a | no auth layer (REQ §2) | N/A — whoever can execute the script and write the target (§4.5 row 1). |
| boundary/oversized inputs — argv | M1 | 0/1/3 args; 2 args where arg 1 is `-h` | ✔ for argc≠2 (E-USAGE, T-C1). ✘ for option-looking positional args the two sanctioned dispatch shapes diverge observably (`-h out.json`: manual → E-READ exit 1; argparse default → help + exit 0) and the §4.1 override clause only covers argparse's *error* paths, not its `-h` success path → F-05 (P2). |
| boundary/oversized inputs — field size | M5/B4 | 10 MB single field / row | ✔ §4.6 limit raise (T-U8); memory the only bound; E-MEM if exhausted. |
| boundary/oversized inputs — interpolated data | M6/B1 | header name with raw newline in E-DUP; strerror platform text | ✔ §6.3 E-DUP note + §4.1 F-03 scoping, verbatim, one stderr write. |
| boundary inputs — name/line edges | M4/M7 | CRLF-in-record M arithmetic; header-scope order; combined defects | ✔ S-9b/S-10(b)(c), T-U3/T-U6/T-C7 pinned with probe evidence (appendix/20 R1/R2, appendix/28b P-c*). |
| initialization/recovery failure | B5 | §4.6 limit-raise loop | ✔ loop terminates by construction (≥1; 64 halvings suffice for any C ssize_t). |
| memory exhaustion — which forms T-C16 may observe | B4 | conforming chunked-write build; E-MEM strikes post-open (write phase) vs pre-open (encode/serialize) | ✘ T-C16 accepts ANY phase form ("a chunked write may OOM at write") yet asserts the pre-existing output is "byte-identical after the failed run ... form-independent" — the write-phase (post-open) form's pinned mechanism (D-46 compensation) REMOVES the pre-existing target. Probe P2/P2b: post-open form → file gone; encode form → bytes survive. The claim is form-DEPENDENT → F-01 (P1). |
| mutation-shape fidelity | M11 | implement the §4.5 "reference shape" snippet as written | ✘ the snippet (`fd = None; try: fd = open(...); ... finally: if fd is not None: remove(path)`) runs its finally on the SUCCESS path too — fd is not None after a successful open — so the remove fires on every successful run and deletes the just-written output; it also never closes the fd. Live probe P1: file absent after a successful stage execution; the intended except-scoped shape passes both paths (P1b) → F-02 (P1). |
| target-path coincidence | B3 | input path == output path; mid-write failure | ✘ unrecorded anywhere in the spec: the pinned mechanism (open O_TRUNC + D-46 compensation) deletes the file, which is the user's INPUT data. Probe P3. S-1's success path also silently replaces the input; the destructive FAILED-run case is a data-loss outcome the risk register never names → F-03 (P2). |
| memory-exhaustion at reporting time | B1/B4 | MemoryError while formatting/printing the E-MEM line | ✔-boundary QC-1 assumptions + R-3: degrades to nonzero exit, never exit 0 / traceback. |
| test-infrastructure reachability | §8.3 | run T-C8's new read-only-target sub-case as root | ✘ `chmod 444` does not block `open(path,"wb")` for root — the sub-case's premise (at-open EACCES) never materializes and the test misjudges (asserting byte-identity of a file the run actually overwrote... or worse, silently passing on a truncated write). T-C2 has the "(skip as root)" guard; T-C8's sibling case lacks it → F-04 (P3). |


# 3. Findings

F-01 [P1|verification-claim/fault-form-dependence|needs-user:false]
  section/artifact: §8.3 T-C16 last sentence ("variant with a
  pre-existing output file: its prior bytes are byte-identical after the
  failed run (D-43 — no truncation at any phase boundary; this
  pre-existing-output variant is form-independent)") vs §8.3 T-C16's own
  form-acceptance sentence ("ANY of the phase forms is the accepted
  assertion, because which phase trips under RLIMIT_AS is build-dependent
  (a chunked write may OOM at write, ...)"), §4.5/S-14(e)/§7.1 E-MEM row
  (post-open MemoryError → D-33/D-46 compensation REMOVES the target),
  §7.1 taxonomy note ("no failure at a phase boundary can truncate or
  delete a pre-existing target"), QC-2 Verification ("RLIMIT_AS variant
  with a pre-existing output asserted byte-identical").
  claim: T-C16 asserts that for EVERY accepted phase form the
  pre-existing output's prior bytes survive byte-identical, and calls
  this "form-independent".
  evidence: the write-phase form T-C16 itself accepts ("a chunked write
  may OOM at write") is a POST-OPEN MemoryError; its pinned mechanism
  (§4.5 D-46 trigger, S-14(e): "the partial file is removed", §7.1 E-MEM
  row: "post-open (mid-write) — the D-33 compensation removes the partial
  file") first truncates (O_TRUNC at open) then REMOVES the pre-existing
  target. Live probe P2: conforming chunked-write stage, fault at the
  second chunk, pre-existing `{"prior":"good-bytes"}` → exit 1, accepted
  message form `csv2json: error: out of memory writing <out>`, and the
  file is GONE. Probe P2b: identical scenario with the fault at the
  encode step (pre-open) → bytes survive. The outcome is form-DEPENDENT
  by the spec's own mechanism table.
  minimal counterexample: (1) out.json exists with a good prior document;
  (2) a conforming chunked-write build runs a valid input large enough
  that the second write chunk OOMs (RLIMIT_AS) — the exact build class
  T-C16's parenthetical names; (3) open() has already O_TRUNC'd out.json;
  (4) the D-46 compensation removes it; (5) stderr matches the accepted
  write-phase E-MEM form, exit 1, no partial — every T-C16 assertion
  PASSES except "prior bytes are byte-identical", which is false: the
  file is absent. A test suite cannot be green against both T-C16
  sentences for this build; whichever way the implementor resolves it,
  one pinned assertion fails. (The §7.1 taxonomy sentence "no failure at
  a phase boundary can truncate or delete a pre-existing target" is
  false for the same case — the post-open mid-write boundary CAN delete
  a pre-existing target, by design.)
  impact: T-C16 as written is self-contradictory for a sanctioned build
  class; the verification plan cannot prove QC-2's byte-identity claim
  for the E-MEM path (P1: "the verification plan cannot prove a claimed
  property").
  required disposition: scope the byte-identity assertion to the forms
  where it is true: the encode/serialize (pre-open) forms — or weaken it
  to "absent or byte-identical" for the post-open write form. Fix the
  §7.1 taxonomy sentence the same way (post-open mid-write failures DO
  delete a pre-existing target by design). QC-2's verification line
  inherits the fix.
  decision owner: spec-designer
  verification required: spec-review re-run on §8.3 T-C16 + §7.1; the
  probe P2/P2b pair is the discriminating evidence.

F-02 [P1|reference-shape/pinned-code-defect|needs-user:false]
  section/artifact: §4.5 compensation-scope block, the D-46 "reference
  shape" sentence: "A `try/finally` whose finally runs the best-effort
  remove is the reference shape — with the open INSIDE the try and the
  finally's remove guarded by whether the open succeeded (e.g.
  `fd = None; try: fd = open(...); ... write/flush ... finally:
  if fd is not None: remove(path)`)".
  claim: the given snippet is "the reference shape" for the compensation.
  evidence: a try/FINALLY runs on success as well as on failure. After a
  successful open `fd` is not None, so on the SUCCESS path the finally's
  guard is TRUE and `remove(path)` fires — deleting the just-written
  output of every successful run. The snippet also never closes the fd,
  contradicting §4.5 step (3) ("then close (the `with` block closes)") —
  a bare try/finally has no with-block. Live probe P1: the snippet
  executed verbatim on a success run leaves the output path ABSENT;
  probe P1b: the obviously-intended except-scoped shape (compensation in
  an `except BaseException` arm, or a with-block whose exception path
  removes) keeps the file on success and removes it on failure — i.e.
  the spec's own normative state contract ("the normative contract is
  the state outcome") is met by everything EXCEPT the snippet offered as
  its reference.
  minimal counterexample: (1) implementer copies the reference shape
  from §4.5 (the spec says the normative contract is the state outcome,
  "not the syntactic form" — but the snippet is the only concrete shape
  given); (2) happy-path run `csv2json.py in.csv out.json`; (3) write
  and flush succeed; (4) the finally runs `remove(out.json)`; (5) the
  process exits 0 SILENTLY (success contract) with NO output file —
  violating S-1, §6.2, QC-3's "every successful run" scope, and the
  REQ §1 success condition ("the output file contains a valid ...
  array"), the tool's core definition. Two builds — snippet-as-written
  and intended-shape — are both defensible readings of §4.5 and produce
  opposite success-path outcomes.
  impact: the one concrete code shape the spec pins for its only
  state-mutating operation is wrong; an implementor following it ships a
  tool that silently discards every successful conversion. (Severity is
  carried by the success-path destruction, not by any failed-run
  contract: the failure path happens to behave correctly in the
  snippet.)
  required disposition: fix the snippet to an except-scoped compensation
  (or a with-block whose exception arm runs the guarded remove), e.g.
  `fd = None; try: fd = open(...); fd.write(payload); fd.flush();
  fd.close(); fd = None
  except BaseException: ...` with the remove inside the except arm
  guarded by `fd is not None` — or keep try/finally but make the
  finally's remove conditional on failure (`error` flag), and close the
  fd. Any shape that cannot run the remove on the success path.
  decision owner: spec-designer
  verification required: spec-review re-run (§4.5); probe P1/P1b is the
  discriminating evidence; the R6-P3 probe's own stage() already used
  the except-scoped shape (the correct one) — the spec text diverged
  from its own evidence.

F-03 [P2|unrecorded-data-loss/input==output|needs-user:false]
  section/artifact: §4.5 (mutation contract, all 13 rows), §10.1 risk
  register, §2.4, §5.3 — absence of any statement about input path ==
  output path.
  claim or missing contract: nothing in the spec addresses the caller
  passing the SAME path as both arguments. The pinned mechanism's
  behavior in that case is derivable but destructive and unrecorded.
  evidence: probe P3 — `csv2json.py data.csv data.csv` (valid input),
  fault at mid-write: S1 read the whole input into memory first
  (whole-file pipeline, §2.2), so parse succeeds; S5 open(data.csv,"wb")
  O_TRUNCs the input file; the mid-write EIO triggers the D-46
  compensation; `os.remove(data.csv)` DELETES the user's input. Exit 1,
  correct E-WRITE line. On the success path the input is likewise
  replaced wholesale by the JSON (S-1's replace semantics), which is at
  least the user's evident intent — but the FAILED-run deletion of the
  SOURCE DATA is a data-loss outcome the risk register never names.
  minimal counterexample: (1) user runs `csv2json.py data.csv data.csv`
  (in-place conversion intent); (2) disk fills mid-write (ENOSPC);
  (3) exit 1 with `csv2json: error: cannot write data.csv: No space
  left on device`; (4) data.csv — the INPUT — no longer exists. No
  spec row promises, forbids, or records this.
  impact: bounded to the same-path invocation (user-induced), but the
  destroyed file is the user's SOURCE, not a derived output — a
  materially different loss class than R-1's "partial output a user
  might mistake for a complete document".
  required disposition: either record an accepted-risk row (R-4:
  same-path invocation; failed runs can delete the input; success
  replaces it) or add a guard (refuse identical paths with a usage-class
  error). Spec-designer's choice; recording suffices at P2.
  decision owner: spec-designer
  verification required: whichever disposition, mirror it in §4.5
  row 10 (state remaining after mid-op failure) so the 13-question
  table stays complete.

F-04 [P3|test-infrastructure/root-guard|needs-user:false]
  section/artifact: §8.3 T-C8's new sub-case ("pre-existing READ-ONLY
  target (mode 444) in a writable dir → E-WRITE and the target's prior
  bytes BYTE-IDENTICAL afterward") vs sibling T-C2 ("chmod 000 file
  (skip as root)").
  claim: T-C8's sub-case as written is runnable as intended in any
  environment.
  evidence: `chmod 444` does not stop root from opening the file for
  writing — DAC_OVERRIDE. As root the at-open EACCES never happens:
  open succeeds, the run truncates and rewrites the target, and on a
  mid-write-free run exits 0 with new bytes. The test's premise fails
  silently; depending on assertion order it either false-passes
  (byte-identity vs the NEW bytes it just read) or false-fails. T-C2
  already established the board's convention for this: "(skip as root)".
  minimal counterexample: CI container runs as uid 0; T-C8 sub-case
  executes: chmod 444 out.json; run tool with valid input → open
  SUCCEEDS (root), writes, flushes, exits 0 — the asserted "E-WRITE and
  byte-identical" outcome is unreachable; the suite reports a failure
  whose cause is the environment, not the build.
  impact: test-infrastructure only; bounded to root-run environments.
  required disposition: add the same "(skip as root)" guard to T-C8's
  read-only-target sub-case (matching T-C2's convention).
  decision owner: spec-designer
  verification required: none beyond the spec-review re-run of §8.3.

F-05 [P2|dispatch-shape-divergence/option-looking-args|needs-user:false]
  section/artifact: §4.1 ("Manual dispatch (an `if`) is specified
  ... An argparse-based implementation is acceptable ONLY if it
  overrides both the exit code (1) and the message shape (prefix +
  usage text) on every error path, including unknown-option errors")
  + §6.1 flags row ("`-h`/`--help` are out of scope ... an
  argparse-based build must still route any unknown-option error
  through the prefixed usage message with exit 1").
  claim or missing contract: the two sanctioned dispatch shapes are
  observably equivalent for every argv. They are not: for argv where
  the FIRST positional is option-looking (`-h`, `--help`), argparse's
  builtin help action is not an "error path" — it prints help to STDOUT
  and exits 0 — so the §4.1 override clause (which binds only error
  paths) never fires. The manual shape treats `-h` as a filename:
  E-READ, exit 1. Live probe P4: manual → `csv2json: error: cannot
  read -h: No such file or directory` exit 1; argparse default on the
  identical argv → help text, exit 0.
  minimal counterexample: (1) build A uses the pinned manual dispatch;
  build B uses argparse, overriding exit code and message on every
  ERROR path exactly as §4.1 requires; (2) user runs
  `csv2json.py -h out.json`; (3) build A: E-READ, exit 1, nothing on
  stdout; build B: help on stdout, exit 0, no file touched. Both builds
  satisfy every sentence of §4.1/§6.1 (build B hits no error path), yet
  they diverge in exit code AND channel AND output-file effect. NFR-004
  ("stdout empty on every path" — §6.4 success row) is violated by
  build B under the reading that `-h out.json` is a failed run, or the
  §6.4 matrix is violated under the reading that it is a success.
  impact: bounded to option-looking argument values (the requirements
  declare no flags, so a user typing `-h` is off the happy path); the
  divergence is between two builds the spec simultaneously sanctions —
  an implementor choosing argparse per §4.1's allowance ships a tool
  whose exit contract differs from the pinned manual shape on this
  argv class.
  required disposition: one line: either (a) declare the manual
  dispatch's outcome normative for ALL argv of length 2 (an argparse
  build must disable/override its help action for the two-positional
  form), or (b) record the divergence as accepted (both outcomes
  conforming for option-looking argv). (a) is the smaller change and
  keeps NFR-004/§6.4 intact.
  decision owner: spec-designer
  verification required: spec-review re-run (§4.1); optionally a T-C1
  sub-case pinning the chosen outcome for `-h out.json`.


# 4. Coverage summary

Cycle-5 findings' v6 dispositions were re-audited first and all verified
folded: adv-c5 F-01 → D-45 (text-mode parenthetical gone; single binary
shape), F-04 → D-46 (at-open failures excluded from the compensation
trigger; consistent across §4.5/S-14(b)/§7.1/T-C8/QC-2/§11), F-02 →
D-47/R-1b (aliasing accepted-risk record + T-C8 assert-or-accept
matrix), F-03 → R-2 reword (reachable-outcome-set language). No stale
v5 wording survives outside explicit supersession mentions (grep: the
phrases "EACCES at open", "harmless no-op", "last writer wins" appear
only as superseded-wording citations). The four cycle-6 findings are all
in text that is NEW or REWORKED in v6 — the D-46 rework itself
introduced F-02's defective snippet, the D-44 fold left T-C16's
byte-identity sentence over-broad (F-01), and the D-46 test fold missed
the root guard (F-04).

Scenario classes attempted, each with an injection point from the §1
inventory:

- covered with counterexample or live probe: duplicate/double-submission,
  retry-after-partial-success, partial failure at every S5 sub-boundary
  (encode / at-open / write / flush / close, pre- and post-open fault
  positions), concurrent execution (R6-P4; R-2 reword verified),
  stale-read/lost-update (taxonomy row), unavailable dependency (EACCES
  at open and mid-write, ENOSPC via /dev/full — all previously
  live-verified), corrupt input data (E-UTF8 arithmetic, carried from
  c2..c5 probes), boundary/oversized inputs (argv incl. option-looking
  args — F-05; field size; interpolated message data; name/line edges),
  resource exhaustion at each phase incl. the T-C16 form-dependence gap
  (F-01, probes P2/P2b), mutation-shape fidelity of the spec's own
  reference code (F-02, probe P1), target-path coincidence input==
  output (F-03, probe P3), test-infrastructure reachability as root
  (F-04), reporting-time memory exhaustion (QC-1 boundary), and
  initialization failure (§4.6 loop).
- N/A with justification (approver: this reviewer, per the spec's own
  §7.1 taxonomy and REQ §2 scope): duplicate/out-of-order events (no
  event sources — single-shot CLI, no queues/timers/signals);
  authorization context (no auth layer exists); restart/recovery/
  migration (no persistent state — process lifetime only; OS-crash
  mid-write is outside any REQ and recorded as boundary);
  schema-version mismatch (nothing persisted). These N/As are the
  spec's own, cross-checked and found justified.

Findings: F-01 (P1), F-02 (P1), F-03 (P2), F-05 (P2), F-04 (P3).
P2/P3 mirrored to appendix/advisory-register.md per the board's mirror
rule.

Probe evidence: appendix/29b-adv-c6-probes.py — 13 checks PASS, 0 FAIL
(Python 3.13.5, this workspace, real filesystem in every probe; only the
fault position was injected, mirroring the spec's own W-series/R6-series
evidence method).

Verdict: FAIL — two P1 findings (F-01, F-02). Both are localized: F-01
is a two-sentence fix in §8.3 T-C16 (+ the §7.1 taxonomy sentence and
QC-2's verification line); F-02 is a one-snippet fix in §4.5's D-46
block. The pinned MECHANISMS (binary single-shape write, D-43 order,
D-46 trigger scope, D-47 aliasing boundary) were re-attacked and held —
the failures are in v6's own new test assertions and its new reference
code, not in the state contracts themselves.

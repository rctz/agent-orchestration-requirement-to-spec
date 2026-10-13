# Adversarial-early review — cycle 5 (adv-c5)

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | adversarial-early (parallel gate, twin of adv-review) |
| target | spec/05-spec-v5.md (status DRAFT, 2026-09-17) |
| reviewer | req2-adv-reviewer |
| date | 2026-09-17 |
| method | mutation-surface + boundary inventory derived from the spec itself; per-class scenario derivation; MINIMAL COUNTEREXAMPLE per finding; live probes where the scenario is executable (appendix/26b-adv-c5-probes.py, Python 3.13.5, this workspace; filesystem REAL in every probe — only the fault position is injected, mirroring the spec's own W-series evidence method) |
| verdict | FAIL — 2 P1 (F-01, F-04) + 1 P2 (F-02) + 1 P3 (F-03); P2/P3 mirrored to advisory-register.md |

# 1. Mutation-surface & boundary inventory

The tool is a five-stage single-shot pipeline (§2.1) with exactly ONE
state-mutating operation (§4.5's own 13-question table) and a handful of
external boundaries. Inventory taken from the spec:

| # | surface / boundary | spec site | class of attack |
|---|---|---|---|
| M1 | argv dispatch (`len(argv) != 2`) | §4.1, D-41 | boundary input, duplicate call |
| M2 | input read (open/read whole file, bytes) | §4.2 `read_raw`, D-15(2) | unavailable dep (EACCES/ENOENT), oversized input (E-MEM read), corrupt data |
| M3 | strict UTF-8 decode + BOM strip | §4.2, REQ-011/012 | corrupt data (invalid bytes, multi-byte, BOM positions), boundary offsets |
| M4 | D-28 line arithmetic (pure) | §4.2 `line_of_offset`, §4.3.2 incremental | boundary offsets (CRLF/CR/VT/FF/NEL/U+2028/9), stale basis |
| M5 | csv parse loop (records, spans via tell()) | §4.3.1/4.3.2, D-24/D-29 | terminator mixes, oversized fields (§4.6 limit), interleaved check order |
| M6 | header rules (0-field, duplicates) | §4.3.4, D-15(4)/(5) | empty name, unicode/duplicate names, name with raw newline (E-DUP slot) |
| M7 | unterminated-quote FSM (per record) | §4.3.3, D-30/D-39 | CRLF-in-record counter, M arithmetic, header scope/order |
| M8 | count validation + row build | §4.3.5, REQ-006 | blank/whitespace rows, trailing terminators |
| M9 | serialize (`json.dumps` compact) | §4.4, D-14/17/20/26 | control chars, huge payload (E-MEM serialize, D-44) |
| M10 | **output write (the ONLY mutation)**: encode→open("wb")→write→flush + every-post-open-exception delete-on-failure | §4.5, D-33/D-43 | partial failure at each sub-step, fault position (pre-/post-open), compensation scope, target aliasing (symlink/hardlink), device paths, concurrent writers, retry |
| B1 | process boundary: exit codes 0/1, stderr single write | §4.1, §6.4, QC-1 | residual exceptions, stderr closed (R-3), E-MEM/E-NET order (§7.3) |
| B2 | filesystem (input side, read-only) | §4.2 | concurrent modification during read (out of scope, no shared state), unreadable |
| B3 | filesystem (output side, mutating) | §4.5 | pre-existing target (truncate), absent target, non-regular targets, unwritable dir |
| B4 | memory (whole-file in-memory pipeline) | NFR-003/005, E-MEM | OOM at each phase; message formatting under OOM |
| B5 | interpreter startup (limit raise) | §4.6 | OverflowError degrade loop |

No network, no timers, no queues, no persisted state, no auth layer —
those scenario classes are structurally N/A (justified in §4 below).

# 2. Scenario table (per class)

Columns: injection point / starting state / injected failure or action /
expected observable result (per spec) / invariant that must hold / durable
state after / rollback-compensation / error contract / retry behavior /
test layer. "✔" = the spec's contract is complete and internally consistent
for that row; "✘" = gap (finding); "N/A" justified inline.

| class | surface | scenario | outcome |
|---|---|---|---|
| duplicate/double-submission | M10, B1 | user re-runs the same command after success | ✔ §4.5 rows 7/8: no session; successful rerun replaces target wholesale (REQ §5.1); exit 0 silent. Last successful run's bytes define the file. |
| retry-after-partial-success | M10 | run failed mid-write (E-WRITE), user reruns | ✔ §7.1 E-WRITE "rerun is clean": compensation removed the partial; pre-open failure positions cannot have touched the target (D-43). Retry semantics fully pinned per class (§7.1 retryable? column). |
| concurrent execution | M10 | two runs, same target, overlapping in time | ✔-boundary §4.5 row 9 + R-2: out of scope by REQ §2, recorded as accepted scope boundary, not a promised property. See F-03 (P3): the pinned mechanism makes "last writer wins" (R-2's gloss) inaccurate in one interleaving, but the boundary is properly recorded. |
| stale-read/lost-update | B2/B3 | input deleted mid-run; output dir vanishes between validate and write | ✔ §7.1 taxonomy: input re-opened per run (E-READ); output writability discovered by open() itself (E-WRITE). No cross-run references exist. |
| partial failure at async boundary — pre-open (encode) | M10 step (1) | valid input, pre-existing GOOD output, MemoryError at encode | ✔ pinned shape: D-43 encode-before-open → prior bytes byte-identical (T-C8/T-C16, W-series probes). ✘ for the §4.5 "equivalent conforming alternative" — F-01 (P1). |
| partial failure — at open | M10 step (2) | EACCES/EROFS at open; /dev/full open succeeds | ✔ S-14(b), T-C8: same E-WRITE shape; compensation harmless no-op (ENOENT ignored); /dev/full verified live (probe P3). |
| partial failure — mid-write/flush | M10 step (3) | ENOSPC/EIO at write or flush; MemoryError mid-write | ✔ every-post-open-exception compensation (D-33 widened, F-01-of-c3 disposition): partial removed, then E-WRITE or E-MEM write-phase form. Device-path removal failure ignored. ✘ aliasing targets: F-02 (P2). |
| partial failure — at close | M10 with-block exit | OSError at close accounting | ✔ §4.5: "flush failures surface inside the `with` before close accounting"; close errors are OSErrors → same every-exception compensation + E-WRITE. |
| timeout/cancellation | B1 | user kills the process mid-write (SIGKILL/SIGINT) | ✔-boundary §7.1 timeout-cancellation row: N/A — no timeouts exist; kill leaves whatever partial output existed at kill time; explicitly recorded as accepted scope boundary (same class as R-3). KeyboardInterrupt not caught (§7.3). |
| refresh/restart/crash mid-operation | B1/B3 | process dies between open and write/flush | ✔-boundary same row as above: OS-level crash is outside the contract; the delete-on-failure compensation is a tool-level mechanism only. A crash CAN leave a partial file (no fsync — §4.5 "no fsync requirement"); no REQ pins crash-resilience. |
| unavailable dependency — storage full | M10 | ENOSPC at write/flush (/dev/full) | ✔ T-C8, live-verified (probe P3: open ok → write/flush raises errno 28 → compensation EINVAL ignored → E-WRITE shape). |
| unavailable dependency — storage/permission failure AT open | M10 step (2) | EACCES/EROFS at open (absent target, unwritable dir); EACCES at open (pre-existing read-only target, writable dir); /dev/full | ✔ absent-target + unwritable-dir: S-14(b), T-C8, compensation harmless (remove ENOENT/EACCES ignored). ✘ pre-existing read-only target + writable dir: the §4.5 wide trigger list deletes the user's prior file; §11/D-43(b) narrow scope preserves it — two normative readings, divergent durable state, no test distinguishes → F-04 (P1). |
| corrupt/version-incompatible persisted data | M2/M3 | invalid UTF-8; BOM positions; multi-byte invalid sequences | ✔ E-UTF8 at the offending byte's own D-28 line (§4.2 F-04 note); first-invalid-byte for multi-byte (e.start); BOM strip only at start (D-16/D-31); no persisted schema (§7.1 N/A). |
| duplicate/out-of-order events | n/a | no event sources exist (single-shot CLI) | N/A — no queues/timers/signals in the design. |
| invalid/caller-controlled authorization context | n/a | no auth layer (REQ §2) | N/A — whoever can execute the script and write the target (§4.5 row 1). |
| boundary/oversized inputs — argv | M1 | 0/1/3 args; unknown options (`-h`) | ✔ E-USAGE inline, exit 1 (T-C1); unknown options fall to argc≠2 manual dispatch (D-41) — an argparse build must route them through the prefixed usage (§6.1). |
| boundary/oversized inputs — field size | M5/B4 | 10 MB single field; 10 MB row | ✔ §4.6 limit raise (T-U8); memory the only bound; E-MEM if exhausted. |
| boundary/oversized inputs — interpolated data in messages | M6/B1 | header name with raw newline in E-DUP; strerror with platform text | ✔ §6.3 E-DUP note + §4.1 F-03 scoping (verbatim, one stderr write, physical wrap allowed) — SR3-F-05 fold verified consistent across §4.1/§6.3/§6.4/§12. |
| boundary inputs — name/line edges | M4/M7 | CRLF-in-record M arithmetic; header-scope order; combined defects | ✔ S-9b/S-10(b)(c), T-U3/T-U6/T-C7 pinned with live probe evidence (appendix/20 R1/R2, my P4/P5 re-derivation agrees: `a,"b\n1` → one record, N=1, M=1, QUOTED at end). |
| initialization/recovery failure | B5 | §4.6 limit-raise loop; interpreter absence | ✔ loop terminates by construction (≥1, 64 halvings); §7.1 init-failure N/A justified. |
| memory-exhaustion at reporting time | B1/B4 | MemoryError while formatting/printing the E-MEM line | ✔-boundary QC-1 assumptions + R-3: closed stderr / print failure degrades to nonzero exit, never exit 0 / traceback; the deeper double-OOM (message formatting itself re-faults) is not separately contracted but the last-resort nonzero-exit behavior covers the observable (probe P6 shows a re-raise is possible; QC-1's failure clause covers it). |

# 3. Findings

F-01 [P1|failure-contract/alternative-shape|needs-user:false]
  section/artifact: §4.5 operation-order parenthetical ("Equivalent
  conforming alternative: text mode `open(path, "w", newline="",
  encoding="utf-8")` ...") vs QC-2 scope, T-C8/T-C16, S-14(d), REQ-010/REQ-008
  (APPROVED), D-43.
  claim: the parenthetical asserts the text-mode shape is an "Equivalent
  conforming alternative" delivering "the D-43 outcome ... so a failure
  before the write still touches no output path".
  evidence: in the text-mode shape there is no pre-open encode step — the
  parenthetical itself says "text mode performs the encode implicitly inside
  the write call". The open (with its O_TRUNC) therefore necessarily precedes
  the encode. A MemoryError at the implicit encode is a failure DURING the
  write call, not "before the write", and it strikes AFTER the target has
  been truncated. Live probe P1 (appendix/26b-adv-c5-probes.py): pre-existing
  good output `{"prior":"good-bytes"}` + fault-injected MemoryError at the
  implicit encode → text-mode shape leaves the target ABSENT (0-truncated by
  open, then removed by compensation); the pinned binary shape on the
  identical fault leaves the prior bytes byte-identical (P1b). This is the
  exact destruction adv-c3 F-01 (P0, fixed by D-43) was created to prevent —
  re-opened by a shape §4.5 labels conforming.
  minimal counterexample: (1) out.json exists containing a good prior
  document; (2) user runs the tool on a valid large input with the text-mode
  build; (3) the implicit encode inside write() raises MemoryError; (4) the
  build conforms to §4.5's parenthetical, yet out.json is truncated/deleted —
  violating QC-2 ("no output file is created or truncated on any failed
  run", scope "every fault position in S5 (before the open, ...)"), S-14(d),
  T-C16's pre-existing-output assertion, REQ-010 ("must NOT create or
  truncate") and REQ-008 ("absent or unchanged"). The spec's own acceptance
  suite T-C8 (encode-fault case) fails for this "conforming" build: two
  builds both called conforming produce different observable outcomes on the
  same input and fault.
  impact: an implementor taking the sanctioned alternative ships a build
  that destroys pre-existing outputs on encode-phase OOM and fails the
  spec's own T-C8/T-C16 assertions; reviewers cannot tell which behavior is
  normative.
  required disposition: delete the parenthetical, or reclassify text mode as
  NON-CONFORMING (consistent with the neighboring sentence "The spec pins
  binary mode as the single implemented shape"), or condition conformance on
  delivering the D-43 outcome observably (pre-open-encode or equivalent
  no-side-effect ordering) — which text mode cannot.
  decision owner: spec-designer
  verification required: spec-review re-run (§4.5); T-C8/T-C16 unchanged
  (they already pin the correct outcome).

F-02 [P2|compensation-scope/aliasing|needs-user:false]
  section/artifact: §4.5 compensation (D-33 "best-effort os.remove of the
  exact path this stage opened") vs QC-2 scope ("pre-existing output
  targets"), REQ-010 ("A partial output file is never left behind as a
  plausible complete JSON document"), R-1.
  claim or missing contract: the compensation's unit of mutation is the
  opened NAME; the write's unit of mutation is the targeted INODE. Under
  aliasing the two diverge and the pinned compensation cannot undo the
  mutation it is scoped to.
  evidence: probe P2 — out-path is a symlink to real.json (good prior
  bytes); mid-write EIO fault → open wrote THROUGH the link into real.json;
  compensation removes the link name; real.json survives holding a 34-byte
  partial JSON document `[{"id":"1","name":"aaaaaaaaaaaaaaa` — a plausible
  complete document prefix. Probe P2b (hardlink): the twin name keeps the
  partial bytes after the opened name is removed.
  minimal counterexample: `ln -s real.json out.json`; run with a valid input
  and a mid-write EIO/ENOSPC; tool exits 1 with the correct E-WRITE line and
  "cleans up" out.json — while real.json now contains the truncated payload.
  REQ-010's "never left behind as a plausible complete JSON document" fails
  observably, and R-1 does not cover it (R-1 is about os.remove FAILING on a
  regular file; here remove SUCCEEDS and the partial survives anyway).
  impact: bounded to aliasing targets (symlink/hardlink output paths); error
  message and exit code are unaffected; a user-induced-or-not alias leaves
  corrupted data the contract claims cannot exist.
  required disposition: either (a) record as an explicit accepted-risk
  extension of R-1 (name-vs-inode aliasing: compensation removes the opened
  name only), or (b) tighten the mechanism (e.g., remove only if the tool
  created the entry, or unlink-by-fd semantics) — spec-designer's choice.
  decision owner: spec-designer
  verification required: whichever disposition, add the aliasing case to
  T-C8's documented matrix (assert-or-accept) so the cold auditor sees it.

F-03 [P3|risk-record-accuracy/concurrency|needs-user:false]
  section/artifact: §10.1 R-2 gloss ("two simultaneous runs to the same
  target race at the OS level and the last writer wins"), §4.5 row 9.
  claim: R-2's outcome description.
  evidence: probe P12 (deterministic interleaving): run A opens out.json,
  faults post-open, its compensation removes the NAME; run B — already
  holding an fd to the now-unlinked inode — writes, flushes, closes
  successfully and exits 0 silently. Final state: out.json does not exist.
  "Last writer wins" is false: NO writer's output survives and one SILENT
  SUCCESS (exit 0, empty stdout) produced no file — the REQ glossary's
  success condition ("exits 0 and the output file contains the complete
  converted array") breaks for B.
  minimal counterexample: as above; the recorded boundary's stated outcome
  does not match the pinned mechanism's reachable outcome.
  impact: none on any promised behavior (concurrency is out of scope by
  REQ §2 and no property is promised); the inaccuracy is in the risk
  register's descriptive gloss only — but it understates what can happen
  (silent success with no file), which is the kind of note a future
  maintainer relies on.
  required disposition: reword R-2 (e.g., "interleaved runs can lose BOTH
  outputs; a failed run's compensation can unlink a concurrent success's
  file; no property is promised").
  decision owner: spec-designer
  verification required: none (risk-record wording).

F-04 [P1|compensation-trigger/at-open-failure|needs-user:false]
  section/artifact: §4.5 compensation scope ("ANY exception raised after the
  open — OSError (ENOSPC, EIO, EDQUOT, EACCES at open, ...) — first runs the
  compensation") + S-14(b) ("nothing was created so compensation is a
  harmless no-op (ENOENT ignored)") vs D-43(b) register text ("triggers on
  EVERY exception raised AFTER the open") and the compensation's own
  rationale.
  claim or missing contract: the AT-open failure case (open itself raised,
  nothing was ever written) sits under TWO normative scopes in the spec:
  §4.5's wrap explicitly lists "EACCES at open" among the compensation
  triggers (wide: remove runs even though nothing was opened), while D-43(b)
  — the normative register decision the mechanism implements — scopes the
  compensation to "EVERY exception raised AFTER the open" (narrow: open
  failed, no open ever succeeded, no compensation). S-14(b) predicts the
  at-open compensation is "a harmless no-op" — true only for an ABSENT path.
  evidence: the §4.5 trigger list explicitly includes "EACCES at open"
  (wide scope); D-43(b) says "after the open" (narrow scope); S-14(b)
  describes the at-open compensation as a "harmless no-op" — which is true
  only for an ABSENT path (remove → ENOENT → ignored). Probe P10: pre-existing
  read-only target (mode 444) in a WRITABLE directory; open(path,"wb") fails
  EACCES (the tool never opens the file); the wide-scope compensation's
  os.remove(path) SUCCEEDS (directory is writable) and DELETES the user's
  prior good output. A failed run that never held an fd to the file destroys
  it.
  minimal counterexample: `chmod 444 out.json` (dir writable), run the tool
  with a valid input → exit 1, correct E-WRITE line, and out.json — the
  user's prior good data — is gone. Under the narrow (D-43(b)) reading the
  file survives byte-identical: the two readings give observably different
  durable state on the same scenario, and the spec contains both readings.
  impact: REQ-008's AC ("absent or unchanged") is literally satisfied either
  way (deleted = absent), so no acceptance test distinguishes the readings —
  but user data destruction by a run that never opened the file contradicts
  the compensation's stated rationale ("a partially written file must never
  survive" — nothing was partially written here) and S-14(b)'s own
  prediction. Local, bounded to at-open-failure + pre-existing-target.
  required disposition: pin ONE scope. Recommended: compensation fires only
  after a SUCCESSFUL open (nothing can be partial if open failed; matches
  D-43(b), the rationale, and leaves S-14(b) correct for absent paths) —
  then delete "EACCES at open" from the §4.5 trigger list; or keep the wide
  scope and rewrite S-14(b) to own the deletion of pre-existing read-only
  targets.
  decision owner: spec-designer
  verification required: spec-review re-run (§4.5, S-14(b)); a T-C8 sub-case
  (pre-existing read-only target + writable dir) pinning the chosen outcome.

# 4. Coverage summary

Scenario classes attempted, each with an injection point from the §1
inventory:

- covered with counterexample or live probe: duplicate/double-submission,
  retry-after-partial-success, partial failure at every S5 sub-boundary
  (encode / open / write / flush / close, both fault positions pre- and
  post-open, F-01/F-04), concurrent execution (P12, F-03),
  stale-read/lost-update (taxonomy row), unavailable dependency (EACCES,
  ENOSPC via /dev/full — live P3; read-only target — live P10), corrupt
  input data (E-UTF8 edge arithmetic re-derived, P4/P5), boundary/oversized
  inputs (argv, field size via §4.6, interpolated message data, name/line
  edges), resource exhaustion at each phase incl. reporting-time (P6, P9),
  initialization failure (§4.6 loop).
- N/A with justification (approver: this reviewer, per the spec's own §7.1
  taxonomy and REQ §2 scope): duplicate/out-of-order events (no event
  sources — single-shot CLI, no queues/timers/signals); authorization
  context (no auth layer exists); restart/recovery/migration (no persistent
  state — process lifetime only; OS-crash mid-write is outside any REQ and
  recorded as boundary); schema-version mismatch (nothing persisted).
  These N/As are the spec's own, cross-checked and found justified.

Findings: F-01 (P1), F-04 (P1), F-02 (P2), F-03 (P3).
P2/P3 mirrored to appendix/advisory-register.md per the board's mirror rule.

Probe evidence: appendix/26b-adv-c5-probes.py — 13 PASS, 1 FAIL (the FAIL
line is F-01's counterexample assertion: the text-mode alternative destroys
the prior output exactly as the finding claims; the pinned binary shape
passes the identical fault). All probes ran on Python 3.13.5 in this
workspace against a REAL filesystem (only the fault position was injected,
mirroring the spec's own W-series evidence method); /dev/full exercised
live.

Verdict: FAIL — two P1 findings (F-01, F-04). Both are localized to §4.5's
write-stage wording (the text-mode "equivalent alternative" parenthetical
and the compensation-trigger scope); no P0 (the pinned binary shape itself
is coherent, live-verified, and satisfies REQ/QC-2/T-C8/T-C16 on every
probed fault position — the failures are in what the spec ADDITIONALLY
permits or leaves two-normative-reading ambiguous, not in the mechanism it
pins).


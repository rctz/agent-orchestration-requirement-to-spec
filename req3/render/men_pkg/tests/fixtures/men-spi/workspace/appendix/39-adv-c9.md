# Adversarial-early review — cycle 9 (adv-c9)

| field | value |
|---|---|
| subject | spec/09-spec-v9.md (status DRAFT, 2026-09-19) |
| reviewer | req2-adv-reviewer (adversarial-early, parallel gate) |
| card | t_45f87418 |
| probes | appendix/39b-adv-c9-probes.py (13 PASS + 1 intentional-FAIL marker, 2026-09-19) + designer battery re-run appendix/36 (7/7 PASS) |
| verdict | FAIL — 3 P1 (F-01, F-02, F-03) + 1 P2 (F-04) + 1 P3 (F-05) |

## 1. Mutation-surface & boundary inventory

Derived from the spec's own text, not a generic checklist. The tool has one
mutable external state (the output path's file) and four boundaries (argv,
input fs, output fs, signals/interpreter).

| # | surface / boundary | spec site | notes |
|---|---|---|---|
| M1 | output-path file create/truncate/write (open O_TRUNC, write, flush, close) | §4.5, D-43/D-45 | the only state mutation in the tool |
| M2 | D-33 compensation: arm-local `fd.close()` + `os.remove(path)` | §4.5, D-46/D-48/D-50/D-51 | runs for every exception after a successful open, KI included |
| M3 | argv (caller-controlled paths) | §4.1, D-34/D-49/D-52 | paths are data; no validation beyond open() |
| M4 | input filesystem read (whole file as bytes) | §4.2 read_raw | OSError → E-READ |
| M5 | stderr/stdout channels (encoding, writability) | §4.1, §6.4, NFR-004 | verbatim-interpolation contract depends on stream encoding |
| M6 | signal delivery (SIGINT → KeyboardInterrupt) | §6.4 signal note, §7.1, D-51 | KI is raisable at any bytecode boundary incl. inside open() and inside the compensation arm |
| M7 | interpreter state: import set, csv field limit | §4, §4.6 | NFR-001 audit pinned to `csv, io, json, os, sys` |
| M8 | clock/environment (locale, PYTHONIOENCODING) | §6.1 env row | locale-independent claim — decode/encode only |

## 2. Scenario table (class coverage)

Per SOUL method. "cov" = covered this cycle (probe id or textual
counterexample); N/A rows carry a one-line justification.

| class | surface | cov | result |
|---|---|---|---|
| duplicate/double-submission | M3 (rerun), M1 | prior cycles + §4.5 rows 7/8 | clean — rerun re-executes from scratch; last success defines bytes; no session |
| retry-after-partial-success | M1/M2 | §4.5 row 7, S-14 | clean — post-open failure removes partial; at-open leaves prior byte-identical |
| concurrent execution | M1/M2 | §4.5 row 9, R-2 | accepted scope boundary (out of REQ §2) — no finding |
| stale-read/lost-update | M1 | N/A — whole input read before S5; no read-modify-write of any file | |
| partial failure at async boundary | M1/M2 | covered — F-01 (KI inside the compensation arm), F-02 (KI at open) | broken absolute claims |
| timeout/cancellation | M6 | covered — F-01/F-02; SIGKILL/SIGTERM-default residue is explicitly scoped out (§7.1) | |
| refresh/restart/crash mid-operation | M1 | N/A — no persistent state; SIGKILL window contracted as out-of-scope | |
| unavailable dependency | M4 (input), M1 (ENOSPC) | covered in prior cycles (E-READ, /dev/full T-C8) + this cycle F-03 (device output path) | |
| corrupt/version-incompatible persisted data | — | N/A — the tool persists nothing; input corruption is a parse-stage data case (E-UTF8/E-UQ/...) | |
| duplicate/out-of-order events | — | N/A — no event queue; signals are the only async input and are handled under M6 | |
| invalid/caller-controlled authorization context | M3 | N/A — no auth layer (REQ §2); OS permissions surface as E-READ/E-WRITE | |
| boundary/oversized inputs | M3, M5 | covered — F-03 (`/dev/stdout` output), F-04 (stderr encoding); huge fields covered prior cycles (§4.6, S-16) | |
| initialization/recovery failure | M7 | covered prior cycles (§4.6 loop cannot exhaust); imports audit NFR-001 re-verified P5b | |

## 3. Findings

### F-01 [P1 | timeout-cancellation / partial-failure | needs-user:false]

- section/artifact: §4.5 compensation bullet + reference shape (D-51),
  §4.5 mutation row 9, §6.4 signal note, §7.1 timeout-cancellation note,
  QC-2 Mechanism.
- claim or missing contract: "a KeyboardInterrupt raised inside the §4.5 try
  has already run the failure arm — fd closed per D-50, partial removed
  best-effort — before the KI propagates past `main`, so an interrupted run
  leaves no partial target" (§7.3, repeated at §6.4 "an interrupted run
  never leaves a plausible-complete partial document on disk", §4.5 row 9,
  QC-2 "so an interrupted mid-write run also leaves no partial target").
- evidence: the guarantee is stated as an ABSOLUTE over the SIGINT class,
  but the reference shape's failure arm catches only `OSError` around its
  own `fd.close()`. A second SIGINT landing inside the compensation arm —
  the ordinary double-Ctrl-C every interactive user can produce — raises KI
  from the arm's `fd.close()` itself; the arm's `except OSError` does not
  catch it, so `os.remove` never executes.
- minimal counterexample (probe 39b P1, live, PASS): target
  `out.json` pre-exists with `PRIOR-GOOD`; run with a 50-row input; user
  presses Ctrl-C once (KI inside `fd.write` — the D-51 window, half the
  JSON lands) and presses Ctrl-C again within the milliseconds the arm
  spends in `fd.close()`. Observed: KI propagates, exit is the signal
  exit, and `out.json` SURVIVES containing exactly the first 1546 of
  3092 JSON bytes — a partial document of exactly the
  "plausible-complete" class QC-2 exists to prevent. Control P1c: single
  Ctrl-C → target removed (D-51's own mechanism works when the arm
  completes).
- impact: every site that states the D-51 outcome as an unconditional
  invariant ("never leaves", row 9's "an interrupted run leaves no partial
  target", QC-2's same claim) is falsified by a two-keystroke user action
  on every conforming build; T-C8's KI sub-case asserts the single-KI
  outcome and cannot catch the divergence.
- required disposition: scope the D-51 guarantee to "a single
  KeyboardInterrupt, and only if the failure arm runs to completion" —
  i.e. add to §4.5/§6.4/§7.1/QC-2 that a SECOND KI (or any exception from
  the arm's own close) escaping mid-compensation leaves the partial file
  in place, recorded as the accepted residue of best-effort cleanup
  (R-1's class), OR specify a KI-resistant arm (e.g. block/defer SIGINT
  around the compensation) — note the `signal` import needed for the
  latter conflicts with the NFR-001 pinned import set, so the
  record-as-residue reading is likely the only conforming fix.
- decision owner: spec-designer.
- verification required: adv-c10 (or the fold's fold-gate) re-runs probe
  39b P1; T-C8's KI sub-case gains the double-SIGINT form only if the
  residue is asserted rather than accepted.

### F-02 [P1 | timeout-cancellation / partial-failure | needs-user:false]

- section/artifact: §4.5 operation order + D-46 ("An open that itself
  raised never held the file, so no remove runs and the target survives
  byte-identical"; glossary "successful open (compensation trigger
  basis)"), §7.1 taxonomy note ("a pre-existing target survives a failed
  run IFF the failure struck before the open"), QC-2.
- claim or missing contract: the at-open story assumes open() either
  returns or raises OSError. For the KI class the intermediate state
  "kernel completed the open (O_TRUNC already applied), signal raised
  before the call returned / before `fd` was bound" is reachable, and in
  it the spec's two contracts (KI compensated per D-51 vs at-open
  failures uncompensated per D-46) point at opposite durable states with
  no rule to choose.
- evidence: probe 39b P2a (live): SIGINT delivered to a process blocked
  IN `open()` (FIFO, no reader) makes `open()` itself raise
  KeyboardInterrupt ("KI-FROM-OPEN") — the raising site is open(), not a
  post-open step. Probe P2b (mechanism, live): when the signal lands
  after the kernel applied O_CREAT|O_TRUNC but before `fd` is bound, the
  reference shape sees `fd is None`, runs NO compensation, and the
  pre-existing prior-good target is left at 0 bytes.
- minimal counterexample: `out.json` holds the user's prior good 20-byte
  document; output path is a FIFO-blocked or merely slow target (NFS,
  cold FUSE); user presses Ctrl-C during the open syscall. Build A
  (spec-literal: KI reaching the §4.5 try's except arm with fd None) →
  no remove → 0-byte `out.json` survives — "target survives
  byte-identical" (D-46/glossary) is false and QC-2's "no output file is
  created or truncated on any failed run" is false for a claim QC-2
  itself asserts for the KI class. Reading B (treat KI-from-open as
  D-51's post-open window because truncation already happened) → remove
  runs → target gone — contradicting D-46's at-open rule and §7.1's
  "survives IFF the failure struck before the open". Both readings are
  sanctioned; they prescribe opposite filesystem outcomes.
- impact: an uncontracted durable state (0-byte prior-good target) for a
  user-reachable signal timing; the glossary's operational definition of
  "successful open" (the state in which open() has RETURNED) classifies
  this case as at-open while its physical effect is post-open truncation.
- required disposition: pin the KI-at-open rule explicitly: either (a)
  declare the interrupted open uncompensated (fd never bound) and record
  the 0-byte-residue as accepted-risk (R-1 class, with the honest note
  that QC-2's absolute wording gains a KI-at-open exception), or (b)
  widen the trigger to "whenever the kernel may have applied O_TRUNC"
  (unobservable from Python without extra syscalls/imports) — (a) is the
  implementable reading; state it in §4.5 D-46/D-51 interaction, glossary
  "successful open", and QC-2.
- decision owner: spec-designer.
- verification required: adv-c10 re-runs 39b P2a/P2b; the folded T-C8
  matrix documents the KI-at-open outcome per the chosen reading.

### F-03 [P1 | boundary-input / unavailable-dependency | needs-user:false]

- section/artifact: §6.1 invocation contract (form row: "exactly two
  positional args"), §6.4 success row, NFR-004 (§6.1 stdout row "empty on
  success; empty on failure", §9 NFR-004 row, T-K3).
- claim or missing contract: no spec site addresses an output path that is
  a CHARACTER DEVICE or other non-regular file. `/dev/stdout`,
  `/dev/stderr`, `/dev/null`, `/dev/fd/N`, character devices, sockets
  passed by descriptor, and named pipes as output are all legal argv[1]
  values that a conforming build opens, writes, flushes, closes, and
  exits 0 — the success contract has no row for them.
- evidence: probe 39b P3 (live, on a build implementing §4.5's exact
  reference shape): `csv2json.py in.csv /dev/stdout` → exit 0 with the
  JSON document ON STDOUT (`[{"id":"1","name":"x"}]\n`); `/dev/stderr` →
  exit 0 with the document on stderr.
- minimal counterexample: user runs `csv2json.py in.csv /dev/stdout`
  (or `/dev/stderr`) on any conforming build. NFR-004's letter — "stdout
  empty on every path" (§6.1) and the §6.4 success row "stdout: empty /
  stderr: empty" — is violated on a SUCCESS run: the success channel
  discipline is argv-controllable, which is precisely the class of leak
  NFR-004 exists to close (the D-52 retraction used an equivalent
  stdout-leak argument to ban argparse). The success contract is
  arg-dependent with no rule stated: nothing says the document-on-stdout
  outcome is sanctioned, and nothing forbids it.
- impact: an acceptance ambiguity on a fully legal invocation: T-K3
  ("stdout empty on every path" per §6.4) versus the tool's own success
  behavior on `/dev/stdout` cannot both hold; a conformance suite that
  runs T-K3 parametrically over output paths fails every conforming
  build, and a user piping the "output file" to stdout gets silent
  success with un-contracted channel contents.
- required disposition: pin the outcome for non-regular output paths:
  either (a) record that the stdout/stderr channel rows of §6.4/NFR-004
  scope to regular-file output paths (the document-on-/dev/stdout
  outcome is then the documented consequence of the caller's own
  redirection — arguably the POSIX-idiomatic result the user asked
  for), or (b) forbid non-regular output targets — which needs a new
  error class outside the closed §6.3 catalog (D-42) plus stat
  machinery; (a) is the minimal conforming fix (a scope note on §6.4's
  rows + NFR-004).
- decision owner: spec-designer.
- verification required: adv-c10 re-runs 39b P3; T-K3's parametrization
  scope statement reflects the chosen reading.

### F-04 [P2 | boundary-input | needs-user:false]

- section/artifact: §6.3 E-DUP note and verbatim-slot enumeration
  (adv-c8 F-04 fold), §4.1 F-03 note, §6.4 stderr column, §12 glossary
  "error catalog" row.
- claim or missing contract: "interpolated VERBATIM — no escaping, no
  sanitization ... escaping or sanitizing the path in any catalog
  message is NON-CONFORMING" is asserted as an unconditional byte-level
  property of the emitted stderr, but the emission goes through
  `sys.stderr` whose ENCODING is environment-controlled
  (PYTHONIOENCODING / locale), not tool-controlled; the spec pins no
  stderr encoding or error handler anywhere (§4/§6.3 never say how the
  message is written).
- evidence: probe 39b P4 (live): with
  `PYTHONIOENCODING=ascii:backslashreplace`, a conforming single-print
  of the Thai-name E-DUP message emits `'\u0e1b\u0e23...` backslash
  escapes — the name is NOT verbatim on the wire; the tool did nothing
  wrong at the formatting layer (the mangling happens inside the print
  call). Default CPython stderr (errors=backslashreplace) preserves
  verbatim UTF-8 under C locale and UTF-8 locale alike (P4 controls).
  A strict handler (`PYTHONIOENCODING=ascii`) additionally makes the
  print itself raise inside `main`'s handler — the QC-1 residual path
  (nonzero exit, no catalog line) — live-verified.
- minimal counterexample: header `"a\nb","a\nb"` under
  `PYTHONIOENCODING=ascii:backslashreplace`: the spec-conforming build
  performs its single stderr write of the verbatim message; the observed
  stderr bytes contain `\u0e1b`-class escapes, so "the message text
  itself may contain a line break ... verbatim" is not deliverable as a
  byte-level guarantee on that environment; a tester asserting T-K1's
  verbatim-name form under that env fails a conforming build.
- impact: bounded — the tool's own formatting is unaffected; the
  divergence lives in the stream layer the spec never mentions. The
  verbatim-slot enumeration (this cycle's adv-c8 F-04 fold) reads as a
  byte guarantee it cannot universally deliver.
- required disposition: one scope sentence in §6.3 (and mirrored in the
  §6.4 stderr cell / glossary): the verbatim guarantee binds the
  MESSAGE STRING the tool hands to the single stderr write; the bytes
  observed on the wire additionally depend on the interpreter's
  stderr encoding (default UTF-8-verbatim on supported CPython;
  environment-overridden encodings may transliterate — outside the
  tool's control, same class as R-3's closed-stream boundary).
- decision owner: spec-designer.
- verification required: none blocking (P2); fold-check cites 39b P4.

### F-05 [P3 | editorial | needs-user:false]

- section/artifact: §6.3 catalog table, E-NET row.
- claim or missing contract: E-NET's template
  `csv2json: error: <in>: internal error: <exception repr>` is the only
  catalog row whose (b)-provision names the INPUT path; the
  verbatim-slot enumeration added by the adv-c8 F-04 fold ("E-READ/
  E-UTF8/E-EMPTY/E-HEADER0/E-DUP `<in>`, E-COUNT/E-UQ `<in>`, E-WRITE/
  E-MEM `<out>`) lists every template's path slot EXCEPT E-NET's
  `<in>` — the enumeration that closes adv-c8 F-04 says "EVERY
  template's `<path>` slot" and then omits one.
- evidence: grep of spec/09-spec-v9.md — the enumeration appears at
  §6.3 (E-DUP note) and in the header revision row; neither mentions
  E-NET's slot.
- minimal counterexample: an E-NET message with a newline-bearing INPUT
  path (e.g. `in\ncsv`) wraps across physical lines exactly like the
  enumerated cases; a reader applying the enumeration as exhaustive
  concludes the verbatim rule does not apply to E-NET's `<in>`, while
  the note's own rule ("EVERY interpolated-data slot in the catalog")
  says it does — the two statements disagree on one template.
- impact: editorial only; the note's general rule already covers E-NET.
- required disposition: add E-NET `<in>` to the enumeration (one clause).
- decision owner: spec-designer.
- verification required: none (P3); fold-check grep.

## 4. Coverage summary

Scenario classes covered with live probes or textual counterexamples this
cycle: partial-failure at async boundary (F-01, F-02 — both live),
timeout/cancellation (F-01/F-02; SIGKILL/SIGTERM-default residue is
explicitly contracted out at §7.1 — no finding), boundary/oversized input
(F-03 device-path output, live; F-04 stderr encoding, live; huge fields
were covered in earlier cycles and are pinned by §4.6/S-16/T-U8),
duplicate/double-submission and retry-after-partial-success (§4.5 rows
7/8 — clean; the rerun story is coherent), concurrent execution
(§4.5 row 9 / R-2 — accepted scope boundary, out of REQ §2, no finding),
initialization/recovery (§4.6 loop proven terminating in prior cycles;
imports audit re-verified by probe P5b).

N/A classes with justification: stale-read/lost-update (whole input is
read to memory before any mutation; no read-modify-write of any file),
refresh/restart/crash mid-operation (no persistent state; the SIGKILL
window is contracted as out-of-scope at §7.1), corrupt or
version-incompatible persisted data (the tool persists nothing; input
corruption is a parse-stage data case with its own catalog ids),
duplicate/out-of-order events (no event queue exists; signals are the
only async input and are handled under F-01/F-02), authorization
context (no auth layer exists — REQ §2; OS permissions surface as
E-READ/E-WRITE, probe-pinned in earlier cycles).

Approver note: N/A dispositions follow the spec's own scope statements
(REQ §2 single-user single-invocation; §7.1 taxonomy N/A rows); none
required a product decision. All five findings' decision owners are
spec-designer; none is needs-user.

## 5. Probe transcript (appendix/39b)

`python3 appendix/39b-adv-c9-probes.py` — 2026-09-19, CPython 3.11.16,
Linux 6.18 (rpi). 13 PASS + 1 marker-FAIL:

```
PASS P1c single-KI: partial target REMOVED (D-51 holds)
PASS P1a double-SIGINT: KI propagates from the arm
PASS P1b double-SIGINT: os.remove NEVER ran; partial file SURVIVES
     with half the JSON bytes (QC-2/§6.4 'never leaves a partial
     target' falsified) | surviving bytes=1546 of 3092
PASS P2a live: SIGINT while blocked in open() makes open() itself
     raise KeyboardInterrupt (fd never bound) | KI-FROM-OPEN
PASS P2b interrupted-open-after-truncate: KI propagates, fd is None
PASS P2b prior good target DESTROYED to 0 bytes, no remove ran
PASS P3a output=/dev/stdout: exit 0
PASS P3a output=/dev/stdout: the JSON DOCUMENT is on stdout —
     NFR-004 letter 'stdout empty on every path' / §6.4 success row /
     T-K3 falsified on a legal argv | b'[{"id":"1","name":"x"}]\n'
PASS P3b output=/dev/stderr: exit 0 with document on stderr —
     §6.4 'success | stderr empty' falsified
PASS P4[utf8-locale] stderr carries the Thai name verbatim (UTF-8)
PASS P4[c-locale-nocoerce] stderr carries the Thai name verbatim (UTF-8)
FAIL P4[pyioencoding-ascii] stderr carries the Thai name verbatim
     (UTF-8) | MANGLED: b"me '\\u0e1b\\u0e23\\u0e30\\u0e40\\u0e17\\u0e28..."
     (this FAIL line IS the F-04 evidence — the probe asserts the
     spec's verbatim claim and the environment breaks it)
PASS P5a §11 coverage sentence names D-01..D-52
PASS P5b argparse control: bare '-h' prints help to STDOUT and exits 0
     (D-52 retraction premise reproduced) | rc=0 stdout=80B
```

Supplementary strict-handler check (F-04 impact note):
`PYTHONIOENCODING=ascii` (strict) makes the single stderr write itself
raise inside main's handler → process exits nonzero with NO catalog line
on stderr and no traceback — the QC-1 Assumptions/Failure residual path,
now demonstrated live for the encoding-induced variant (the closed-
stderr variant R-3 remains untested-by-design).

Designer battery re-run (regression check): appendix/36-rev9-ki-
argparse-probes.py 7/7 PASS on this workspace — v9's own folds (D-51
single-KI window, D-52 retraction, §11 enumeration) hold; the findings
above are the residual gaps not covered by that battery.

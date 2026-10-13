# Adversarial early review — cycle 3 (adv-c3)

| field | value |
|---|---|
| spec | spec/03-spec-v3.md (DRAFT, 2026-09-17) |
| reviewer | req2-adv-reviewer (EARLY-MODE, parallel to spec-review c2) |
| method | mutation-surface + boundary inventory -> 13 scenario classes -> minimal counterexample per finding; live probes appendix/21b-adv-c3-probes.py (10 checks PASS on Python 3.11.16, 2026-09-17) |
| verdict | FAIL — 1 P0 + 1 P1 (+ 1 P2 + 2 P3, registered) |
| inputs cross-checked | requirements/07-requirements-v7.md (APPROVED), appendix/03-decision-register.md (D-01..D-42), appendix/20-rev3-order-probes.py evidence as cited by the spec |

Status: DRAFT-COMPLETE (all sections filled)

## A. Mutation-surface & boundary inventory

| # | surface / boundary | kind | spec anchor | attack notes |
|---|---|---|---|---|
| M1 | `main(argv)` dispatch | state (process entry) | §4.1 | argc≠2 branch; no mutation; injection = malformed argv |
| M2 | `read_raw(path)` input read | external fs boundary (read) | §4.2 | OSError mapping; TOCTOU on source file; unbounded size |
| M3 | `decode_utf8` strict decode | pure transform | §4.2 | invalid byte position arithmetic; BOM strip |
| M4 | `parse(text)` per-record loop | in-memory state machine | §4.3 | header rules vs quote-scan order; spans via tell(); FSM |
| M5 | `serialize(rows)` | pure transform | §4.4 | memory blow-up (E-MEM serialize phase) |
| M6 | `write_output(path, doc)` | THE ONLY state mutation (fs write) | §4.5 | open("wb") truncates at open; compensation scope; encode placement |
| M7 | startup `csv.field_size_limit` raise | process-global init | §4.6 | halving loop termination |
| M8 | stderr print of the one error line | external channel boundary | §6.1/§6.4/§7.3 | message content vs "exactly one line" |
| M9 | OS process environment | external dependency | §6.1 env row | argv encoding, stderr encoding, RLIMIT_AS (T-C16) |

## B. Scenario table (13 classes)

Columns per protocol: injection point / starting state / injected failure or action / expected observable result / invariant that must hold / durable state after / rollback-compensation / error contract / retry behavior / test layer. "OK" = the spec's contracts fully determine the outcome; deviations are escalated to §C.

| class | injection / start / action | expected observable | invariant | durable state / rollback | error & retry | test layer |
|---|---|---|---|---|---|---|
| duplicate/double-submission | M6: user re-runs tool; target already holds last run's bytes | identical bytes re-written; exit 0 | §4.5 rows 7-8: rerun re-executes from scratch, successful run REPLACES the file | target replaced wholesale; no rollback needed (delete-on-failure only) | none; clean retry | E2E (implicit in T-C-suite) |
| retry-after-partial-success | M6: S5 raises mid-write after open("wb") truncated a pre-existing good file | per D-33: partial removed, `cannot write <out>: <strerror>`, exit 1 | QC-2: "no output file is created OR TRUNCATED on any failed run" | OK for OSError (compensation removes) | retry clean | T-C8 |
| retry-after-partial-success | M6: MemoryError at `document.encode()` after open("wb") truncated the target — probe W1 | F-01: 0-byte output survives; E-MEM write-phase message despite no write attempted | REQ-010 "must NOT ... truncate the output file" — VIOLATED | 0-byte file survives (compensation is OSError-scoped) — F-01 | retry clean but data lost | none — F-01 |
| concurrent execution | two processes, same target | last writer wins at OS level | out of scope by REQ §2; recorded R-2 | OS-level race | n/a (accepted boundary) | N/A (justified by §4.5 row 9, R-2) |
| stale-read/lost-update | n/a — no read-modify-write across calls; the file is a projection of one serialize() output | — | — | — | — | N/A (single-phase write, §4.5 row 5) |
| partial failure at each async boundary | n/a — no async boundaries; the pipeline is a synchronous five-stage linear flow (§5.1), no timers/queues/network | — | — | — | — | N/A (§5.1: "the process is linear") |
| timeout/cancellation | M9: SIGKILL mid-S5 | whatever partial bytes the OS had | out of contract — §7.1 timeout-cancellation row | partial file possible; recorded as accepted scope boundary | n/a | N/A (justified §7.1) |
| refresh/restart/crash mid-operation | same as kill/crash: no persistent tool state; a fresh run re-reads and re-writes | exit 0/1 per input validity | §7.1 corrupt-persisted-state N/A row | only the output file; wholesale replaced on success | clean | N/A (no daemon/restart state) |
| unavailable dependency | M2/M6: input unreadable (E-READ); output EACCES/ENOSPC/EIO/EDQUOT (E-WRITE) | one catalog line, exit 1 | closed catalog §6.3 | none / compensation | retryable per §7.1 | T-C2/T-C8 |
| unavailable dependency | M9: MemoryError per phase (read/parse-serialize/write) | E-MEM phase form, exit 1 | §6.3 E-MEM row | partial removed IF S5 AND OSError-shaped — see F-01 for the MemoryError-at-encode hole | more RAM / smaller input | T-C16 |
| corrupt/version-incompatible persisted data | n/a — tool persists no schema; input is user data validated per run | — | — | — | — | N/A (§7.1 schema-version N/A row) |
| duplicate/out-of-order events | n/a — no event stream; records are consumed sequentially from one decoded text | — | D-29 ordering pinned by S-11/T-U6/T-C7 | — | — | N/A (no event source exists) |
| invalid/caller-controlled authorization context | n/a — no auth layer; OS permissions surface as E-READ/E-WRITE | — | §4.5 row 1 | — | — | N/A (REQ §2 single-user CLI) |
| boundary/oversized inputs | M3/M4: 0-byte, BOM-only, blank-lines-only, whitespace-only, terminator mixes, embedded NUL/VT/FF, U+FEFF mid-cell, `5" ruler`, `"a"b`, `"a""b` | fully pinned by S-4..S-16, T-C3..T-C13 | catalog closed | no output on any failure | deterministic (not retryable) | T-C3..T-C13 |
| boundary/oversized inputs | M4: header name containing a raw newline (quoted multi-line header field) — probe R2 | F-03 (P2): E-DUP message embeds the newline -> "exactly one line to stderr" (§4.1) becomes two physical lines | §6.4 "exactly one line per failed run" — wording-level tension, bounded | no output | deterministic | none today — F-03 |
| boundary/oversized inputs | M4: duplicate header name containing `'` — message `'a'b'` remains parseable prefix+shape | minor, same shape | (a) prefix intact | no output | deterministic | note only (no finding) |
| initialization/recovery failure | M7: limit-raise loop; M9: interpreter absence | loop terminates (≥1 by construction); interpreter absence out of scope | §4.6 "cannot exhaust" | none | n/a | T-U8 |

## C. Findings

### F-01 [P0|data-integrity/recovery-contract|needs-user:false]
- section/artifact: §4.5 write stage (order of open/encode/write + compensation trigger), against QC-2 (§10) and §6.3 E-MEM row.
- claim: "Wrap open/write/flush in one try; on `OSError` ... first run the compensation" — the D-33 delete-on-failure compensation is scoped to OSError only, while the write stage's own declared inputs include the str->bytes encode step, and E-MEM's write-phase form proves a MemoryError is contractually expected inside S5.
- evidence: probe W1 (appendix/21b, this cycle): with the spec's operation order — `open(path, "wb")` first, then `document.encode("utf-8")` — a MemoryError raised at encode leaves a 0-byte output file behind; probe W2: `MemoryError` is not an `OSError` subclass, so the OSError-scoped try/compensation never fires.
- minimal counterexample: (1) user has a good `out.json` from an earlier run; (2) valid `in.csv` parses; (3) S5 opens `out.json` "wb" — the good file is truncated to 0 bytes NOW (POSIX O_TRUNC at open, before any write call); (4) `document.encode("utf-8")` raises MemoryError (a ~180 MB document on a capped-RLIMIT_AS box, exactly T-C16's fault-injection environment); (5) E-MEM's compensation claim "partial file removed (if raised in S5)" (§7.1) does not fire — the D-33 compensation catches OSError, and MemoryError is not one; (6) user's prior good output is destroyed and left as a 0-byte file; exit 1. REQ-010: "On any error ... the tool must NOT create or truncate the output file"; QC-2: "no output file is created or truncated on any failed run". Both fail.
- impact: silent destruction of a pre-existing user file on a failed run — the exact property REQ-010 exists to guarantee; also makes §7.1's E-MEM side-effects cell ("partial file removed (if raised in S5)") false as specified.
- required disposition: encode-before-open (reorder S5 to `payload = document.encode("utf-8")` THEN `open(path, "wb")`), or widen the S5 compensation to `except BaseException`-style cleanup (try/finally around everything after open), and pin the chosen order in §4.5's behavior text so T-C8/T-C16 assertions can target it.
- decision owner: spec-designer
- verification required: spec-review cycle on §4.5/QC-2/§6.3 E-MEM consistency; T-C8 gains a pre-existing-output + MemoryError-at-encode case (fault-injected per §8.4), asserting prior bytes survive.

### F-02 [P1|recovery/partial-failure semantics|needs-user:false]
- section/artifact: §4.5 (S5 interface `write_output(path, document: str)` and operation order), §7.1 E-MEM row, QC-2.
- claim or missing contract: WHERE in S5 the MemoryError strikes is left undefined by the spec's own text: §4.5's body specifies open/encode/write/flush with the compensation keyed to OSError, but never states whether `document.encode("utf-8")` happens before or after `open(path, "wb")`. The two orders have materially different observable outcomes (truncate-then-fail vs fail-without-touching).
- evidence: §4.5 "Behavior — no newline translation (D-35)": "Open with `open(path, "wb")` ... Encode once: `document.encode("utf-8")`" — that sentence orders open BEFORE encode; §6.3 E-MEM write-phase form and §7.1 E-MEM row prove a MemoryError inside S5 is an expected, cataloged event; probe W1 shows the open-before-encode order truncates a pre-existing target before encode can fail.
- minimal counterexample: implementor A follows §4.5's sentence order literally (open, then encode): the F-01 destruction scenario fires. Implementor B encodes first: the same MemoryError leaves the pre-existing output byte-untouched and no file created. Same spec, same input, same fault — two observably different durable outcomes (0-byte destroyed file vs untouched file). §7.1's E-MEM "side effects" cell cannot be evaluated against either build without the implementor guessing.
- impact: an acceptance test for E-MEM-write-phase cleanup (T-C16's "no partial output file left" under RLIMIT_AS) gives different verdicts on conforming-per-spec builds; the data-destruction variant of F-01 is reachable exactly through this ambiguity.
- required disposition: pin the encode-vs-open order normatively in §4.5 (encode-before-open is the fix that also closes F-01), and make §7.1 E-MEM's side-effects cell state the pinned order's outcome.
- decision owner: spec-designer
- verification required: re-run of the §4.5/QC-2 contract tests with the pinned order; this file's F-01 verification.



### F-03 [P2|boundary-input/error-contract-shape|needs-user:false]
- section/artifact: §6.3 E-DUP template `duplicate header name '<name>'`; §4.1 "exactly one line to stderr"; §6.4 "exactly one line per failed run"; §4.3.4(ii).
- claim or missing contract: the duplicate-header name is interpolated into the message verbatim (D-12: message cites the name; F-33: empty name cites `''`). A quoted header field may legally contain a raw newline (REQ-004/S-8c: quoted fields span physical lines). Nothing in the catalog sanitizes or escapes `<name>`.
- evidence: probe R2 (appendix/21b): header `"a\nb","a\nb"` parses to fields `['a\nb','a\nb']`; the catalog-conformant message is `csv2json: error: in.csv line 1: duplicate header name 'a\nb'` — which prints as TWO physical stderr lines. A name containing a `\r` similarly emits a bare CR mid-line.
- minimal counterexample: in.csv = `"a\nb","a\nb"\n1,2\n` → conforming build must print `... duplicate header name 'a\nb'` (the only catalog form) → stderr carries 2 physical lines → §6.4's "exactly one line" cell is unmeetable for this input; any escape the implementor invents (e.g. `\n` literal) leaves the closed-catalog rule (§6.3: "a build emitting a message outside this catalog is non-conforming") with no defined form to emit.
- impact: bounded (grep-style prefix tests still pass; exit code and channel unaffected) but the one-line channel invariant is worded absolutely and this input class is legal per the dialect. An AC cannot yield a clear verdict for a "one line" assertion on this input.
- required disposition: spec-designer picks one: (a) scope "exactly one line" to "no trailing newline is added by the tool" (content-borne line breaks are data), or (b) define the escaped form of `<name>` in the catalog (e.g. `\n`→`\\n` per D-14-style escaping). Either is a one-line spec fix.
- decision owner: spec-designer
- verification required: T-K1 parametrized over a newline-bearing duplicate name once the form is pinned.

### F-04 [P3|editorial|needs-user:false]
- section/artifact: §4.2 E-UTF8 message construction; QC-4 scope row.
- claim or missing contract: E-UTF8's N is the offending byte's own line (`line_of_offset` over the decoded prefix — probe U1 re-verified `a,b\rc,d\rc\r\xff` → line 4 on 3.11.16), not REQ-007(c)'s row-start convention (meaningless pre-parse). The spec never says so in one place; §4.2's formula settles it operationally.
- minimal counterexample: n/a (mechanical wording note; no behavior divergence — `0xFF` as byte 0 yields `line 1`, the only sensible value).
- impact: none on behavior.
- required disposition: optional one-clause note in §4.2 that E-UTF8 N is the byte's line, not a row-start line.
- decision owner: spec-designer
- verification required: none.

### N-01 (covered class, NON-finding — no counterexample constructible)
- BOM position vs line arithmetic (§4.2): the strip runs after decode, so E-UTF8 line numbers are computed on BOM-bearing text; but U+FEFF is not in the D-28 break set and never forms a terminator pair, so no input exists where strip-before-vs-after moves any N. Inputs tried: `EF BB BF 0xFF` (line 1 both ways), `EF BB BF 61 0D 0A FF` (line 2 both ways). Recorded so the next cycle does not re-derive it.

### F-05 [P3|process/protocol-hygiene|needs-user:false]
- section/artifact: §10.1 R-1 (and R-2/R-3) risk-register entries.
- claim or missing contract: R-1 records the partial-file-survives-failed-remove residual as an accepted risk, but carries no disposition/owner/rationale/impact/mitigation/verification structure — the board's severity policy requires an accepted risk to close as "an explicit constraint/risk record with owner, rationale, impact, mitigation, verification — never as a bare 'accepted'". R-1 has a mitigation cell ("implementor to preserve the compensation order") and an implicit owner, but no verification hook (no test can exercise a failing os.remove on a regular file; the T-C suite never asserts it).
- minimal counterexample: n/a (mechanical/protocol check; the spec's own policy document is the evidence).
- impact: none on tool behavior; cold-audit/mechval friction on final gating.
- required disposition: one-line tightening of R-1 (verification cell: "untestable pathologically; owner: implementor; reviewed at code review") or fold into an explicit constraint record.
- decision owner: spec-designer
- verification required: none (register hygiene).




## D. Coverage summary

Classes covered with a live counterexample or pinned outcome: duplicate/double-submission (§4.5 rows 7-8); retry-after-partial-success (OSError path pinned by D-33/T-C8; MemoryError-at-encode path broken -> F-01); boundary/oversized inputs (all REQ-identified shapes pinned by S-4..S-16/T-C3..T-C13, plus the newline-bearing header name -> F-03 and the E-UTF8 line-1 byte -> F-04); initialization (M7 termination argued + T-U8); unavailable dependency (E-READ/E-WRITE/E-MEM catalog rows, with F-01/F-02 on the E-MEM write-phase cleanup).

Classes N/A (with justification, approver = this reviewer per EARLY-MODE card):
- concurrent execution — out of scope by REQ §2; recorded as R-2 with owner (spec §10.1).
- stale-read/lost-update — no read-modify-write exists; single-phase projection write (§4.5 row 5).
- partial failure at async boundaries — no async boundaries; §5.1 linear pipeline.
- timeout/cancellation — no timeouts; kill-mid-S5 recorded as accepted boundary in §7.1.
- refresh/restart/crash mid-operation — no persistent tool state; folded into the timeout/crash boundary above.
- corrupt/version-incompatible persisted data — tool persists no schema (§7.1 N/A row).
- duplicate/out-of-order events — no event stream; sequential record consumption only.
- invalid/caller-controlled authorization context — no auth layer (REQ §2, §4.5 row 1).

Class coverage count: 5 covered, 8 N/A-justified, 0 skipped.

## E. Probe evidence

appendix/21b-adv-c3-probes.py, run 2026-09-17 on Python 3.11.16 (host interpreter; the spec's own probes ran on 3.13.5 — both CPython, csv/json/StringIO semantics identical for the pinned behaviors):

```
[PASS] R1a `id,"id` single record — [(['id', 'id'], 'id,"id')]
[PASS] R1b lenient fields = ['id','id'] (duplicate exists) — ['id', 'id']
[PASS] R2a header fields both 'a\nb' — ['a\nb', 'a\nb']
[PASS] R2b catalog message embeds a raw newline (2 stderr lines) — "csv2json: error: in.csv line 1: duplicate header name 'a\nb'"
[PASS] R3a two records (header + offending) — [['h1', 'h2'], ['a\r\nb', 'c', 'd\ne']]
[PASS] R3b FSM ends QUOTED — QUOTED
[PASS] R3c N=2, M=3 (v3 pinned values) — N=2 M=3
[PASS] W1 spec-order S5: MemoryError at encode leaves 0-byte output — b''
[PASS] W2 MemoryError is not an OSError (OSError-only try misses it) — True
[PASS] U1 E-UTF8 line = 4 (D-28, CR-only) — start=10 line=4
TOTAL FAILURES: 0
```

Interpretation: R1/R3/U1 re-verify the spec's own pinned semantics (span arithmetic, S-9b combined defect, S-10b M=3, CR-only UTF-8 line 4) on the local interpreter — no regression found in v3's cycle-3 fixes. W1/W2 are adversarial evidence FOR F-01/F-02. R2 is adversarial evidence for F-03.

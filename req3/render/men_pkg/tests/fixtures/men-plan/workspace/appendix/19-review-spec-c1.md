# Spec review — cycle 1 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 1 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-17 |
| spec under review | spec/02-spec-v2.md (DRAFT, 2026-09-17) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | **FAIL** — 2×P1, 3×P2, 5×P3 |
| counterexample probes | appendix/16-, 17-, 18-, 18b-review-spec-c1-probes*.py (this cycle, live on Python 3.13.5) |

Finding ids are scoped to this review and prefixed `SR1-F-nn` (the shared
advisory register already carries req-review ids F-01..F-35; the prefix
keeps the register unambiguous).

## Summary

The spec is strong: genuine probe evidence (appendix/13 re-run this cycle,
63/63 PASS on Python 3.13.5), complete EV tuples QC-1..QC-6, a complete
13-question mutation contract for the one state-mutating stage, a full
REQ-001..014/NFR-001..005 traceability matrix, a closed message catalog
that matches the requirements' pinned examples verbatim, and test layers
that match risk layers (real filesystem for write semantics, subprocess
for E2E, pure-unit for parse). Two P1 findings block READY:

- SR1-F-01: the §4.3.3 FSM table contradicts the section's own prose, the
  spec's own P3 probe, and REQ-013/D-28/D-30 on the M line number when a
  CRLF (or CR) occurs inside a quoted field of the offending record —
  the spec's end-to-end probe P8 computes M one too high.
- SR1-F-02: the spec's per-record check order (quote check before header
  duplicate check) contradicts the APPROVED D-15 slot order ((5) duplicate
  header before (6) unterminated quote) on combined header defects —
  different stderr message for the same input.

## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR1-F-01 | P1 | 1+2 | §4.3.3, probe P8 vs P3 | FSM counts CRLF as two breaks inside QUOTED → M off by one; contradicts own prose, own P3 probe, REQ-013/D-28 |
| SR1-F-02 | P1 | 2 | §4.3.2, §5.2 vs REQ D-15 | quote-check-before-duplicate-check on the header record inverts D-15 slot (5)<(6); `id,"id` → spec E-UQ, REQ E-DUP |
| SR1-F-03 | P2 | 2 | header, §1, §11 | decision-coverage claim stale: D-01..D-36 cited, live register holds D-01..D-42 |
| SR1-F-04 | P2 | 3 | §7.1 E-MEM row, §8.4 | E-MEM's proving test has no T-id; §7.1 cites T-C9 (perf spot-check) which does not assert E-MEM |
| SR1-F-05 | P2 | 2 | §6.3 E-MEM | write-phase MemoryError message names the INPUT path; NFR-005 says "reported like any other write-time failure" (output path) |
| SR1-F-06 | P3 | 1 | §4.1 error-paths table | MemoryError classified as ToolError there, but §7.3 catches it as its own class before ToolError |
| SR1-F-07 | P3 | 1 | header probes row | "70/70 PASS" — the suite has 63 check() calls (all pass) |
| SR1-F-08 | P3 | 1 | §5.3 S-1 | "writes 45 bytes" — the pinned output is 46 bytes |
| SR1-F-09 | P3 | 1 | §6.2 item 6 | "`[]\n` (2 bytes)" — `[]\n` is 3 bytes |
| SR1-F-10 | P3 | 3 | §8.4 macOS note | `ulimit -f` fallback kills the child via SIGXFSZ (signal death, not an OSError) — cannot exercise the E-WRITE contract as written |

(Full records follow.)

## SR1-F-01 [P1 | axis 1+2: internal contradiction + REQ-013/D-28/D-30 consistency | needs-user:false]

- section/artifact: spec/02-spec-v2.md §4.3.3 (FSM state table + following
  prose), §5.3 S-10, glossary §12; appendix/13-spec-design-probes.py
  P8 (scan_unterminated) vs P3 (scan_row).
- claim or missing contract: the spec pins M ("opened at" line of REQ-013)
  to the D-28 physical line of the opening quote — CRLF is ONE break
  everywhere in the counting basis. But the normative FSM table in §4.3.3
  (`QUOTED` row, `\n` or `\r` column: "advance the record-relative line
  counter") counts CRLF as TWO advances, and the spec's end-to-end probe
  P8 implements exactly that, while §4.3.3's own closing prose ("CRLF
  inside a record's text ... is one line break for the record-relative
  counter") and the spec's own P3 scanner count it as one.
- evidence: appendix/13 lines 311 vs 135-147 — two scanners in the SAME
  evidence file disagree; live re-run this cycle (appendix/17): input
  `h1,h2\n"a\r\nb",c,"d\ne` gives N=2 and D-28 truth M=3; the §4.3.3
  table semantics and P8 yield M=4; P3 yields M=3.
- minimal counterexample: `h1,h2\n"a\r\nb",c,"d\ne` — row 2 starts at line
  2; the opening quote of the unterminated third field sits after one
  CRLF, i.e. on physical line 3; D-28 basis: 2 + 1 = 3. A build following
  the §4.3.3 table emits `line 2: unterminated quoted field (opened at
  line 4)` — a line number that does not exist in the file (the file has
  3 physical lines).
- impact: any input whose offending record carries a CRLF (or CR) inside
  an earlier quoted field gets M off by exactly the number of CRLF/CR
  pairs inside quoted sections; every REQ-013 acceptance case uses LF
  only, so the implemented ACs stay green while the normative table is
  wrong — the defect ships silently.
- required disposition: one arithmetic, everywhere. Fix the QUOTED-row
  newline advance to count `\r\n` (and bare `\r`) as one break (probe P3
  semantics — P3 already implements the D-28-exact arithmetic and passes),
  align P8's scan_unterminated to it, and add the CRLF-interior acceptance
  case (`h1,h2\n"a\r\nb",c,"d\ne` → `line 2 ... (opened at line 3)`) to
  REQ-013's AC set in the spec's test outline (T-U3/T-C7) so the
  divergence becomes test-caught.
- decision owner: spec-designer.
- verification required: spec-review cycle 2 re-runs appendix/17 probes
  and checks the §4.3.3 table's QUOTED row wording.

## SR1-F-02 [P1 | axis 2: spec vs requirements consistency | needs-user:false]

- section/artifact: spec/02-spec-v2.md §4.3.2 (check order), §5.2
  (micro-states), §5.3 S-9(c) vs requirements/07-requirements-v7.md §7.2
  D-15 (slots (5) and (6)) and REQ-013.
- claim or missing contract: the spec orders the per-record checks as
  quote-check → header-rules → count-check. On the header record this
  means the unterminated-quote check runs BEFORE the duplicate-header
  check. The APPROVED D-15 pins the validation order as (5) duplicate
  header (REQ-002, line 1) BEFORE (6) unterminated-quote detection during
  the sequential pass. On an input that is both duplicate-headered AND
  quote-unterminated (e.g. `id,"id` — one physical line, quote opened at
  field 2 never closed), the two orders produce different stderr lines:
  spec → `csv2json: error: input.csv line 1: unterminated quoted field
  (opened at line 1)`; requirements → duplicate error citing 'id' at
  line 1.
- evidence: spec §4.3.2 "The three checks run in exactly this order PER
  RECORD"; D-15 slot list in REQ §7.2 ((5) duplicate, (6) quote); live
  probe appendix/18b: the designed pipeline (quote check first) yields
  E-UQ on `id,"id`, the D-15 order yields E-DUP.
- minimal counterexample: `python csv2json.py in.csv out.json` with
  in.csv = `id,"id` (no trailing newline): spec-conforming build prints
  the quote error; requirements-conforming build prints the duplicate
  error — same exit 1, different observable message, tests pinned to one
  or the other fail.
- impact: an implementor following the spec ships an error-precedence
  observable that contradicts the approved D-15 ordering; contract tests
  written from the requirements will fail against a spec-built tool.
- required disposition: spec must defer the quote check on the header
  record: run header rules (0-field → duplicate) first, and the quote
  check after them within slot (6) scope — OR the requirements must be
  shown to license the spec's order. Cleanest disposition consistent with
  D-15/D-25 (detection scope includes the header) is: per record, quote
  check first for DATA records; for the header record, duplicate check
  (slot 5) precedes quote detection (slot 6). The spec text in §4.3.2/
  §5.2/S-9(c) and the probe P8 must be aligned to whichever order is
  pinned, and the combined-defect AC (`id,"id` → E-DUP at line 1) added.
- decision owner: spec-designer (with req-designer ack if any doubt on
  D-15's intent; none observed — D-15 is unambiguous).
- verification required: spec-review cycle 2 re-runs appendix/18b probe
  against the revised check order; the combined-defect case must be
  pinned as an AC in the revised spec.

## SR1-F-03 [P2 | axis 2: authoritative-artifact agreement | needs-user:false]

- section/artifact: spec/02-spec-v2.md header block, §1, §11
  (decision-coverage check); appendix/03-decision-register.md.
- claim or missing contract: the spec claims three times (header "D-01..D-36,
  all DECIDED"; §1 "D-01..D-36 ... are all DECIDED"; §11 "D-01..D-36 are all
  DECIDED in appendix/03-decision-register.md and all are bound") — but the
  live register (machine-parsed by mechval) now holds D-01..D-42: the
  spec-designer added D-37..D-42 when designing spec-v1 and never refreshed
  the spec's coverage claims. The spec's §11 paragraph does bind D-37's
  ADR-1/ADR-4 content (§2.3 rows) but never mentions D-38 (offset-based
  line numbers / `line_num` never used) in the D-enumeration, nor D-39,
  D-40, D-41, D-42.
- evidence: register rows D-37..D-42 cite "spec/01-spec-v1.md §2.1/§2.3/
  §4.1/§4.3.3/§4.5/§6.3" — their content IS in the spec body; only the
  enumeration claims are stale.
- minimal counterexample: n/a (mechanical cross-check).
- impact: the mechval decision-coverage check reads the register and the
  spec's claim; a reviewer or downstream auditor trusting "D-01..D-36"
  misses six register decisions; if mechval's coverage rule tightens, the
  spec fails the gate on a hygiene miss.
- required disposition: refresh the three claim sites to D-01..D-42 and add
  the missing D-38..D-42 bindings in §11 (or fold the enumeration into a
  pointer to the register to stop the staleness class).
- decision owner: spec-designer.
- verification required: mechval re-run; spec-review cycle 2 spot check.

## SR1-F-04 [P2 | axis 3: verification alignment | needs-user:false]

- section/artifact: spec/02-spec-v2.md §7.1 (E-MEM row, "verification"
  column), §8.3/§8.4 (test ids), §9 anchors.
- claim or missing contract: E-MEM is a cataloged error class with a pinned
  proving standard — "T-C9 (constructed via limit, fault-injection note in
  §8.4)" — but T-C9 is the NFR-003 performance spot-check; §8.4 says E-MEM
  is exercised "by fault injection ... child process with low RLIMIT_AS",
  yet no test id owns that fault-injection case. No §8 table row asserts
  the E-MEM message, exit code, or no-partial-file property.
- evidence: §8.3 T-C9 = "performance envelope ... (spot check, not a hard
  gate)"; §8.4 bullet 2 names the E-MEM fault-injection method but no
  T-id; the E-MEM proving tuple element therefore dangles.
- minimal counterexample: n/a.
- impact: the one catalog class whose proof depends on deliberate
  environment-level fault injection has no owner test; an implementor can
  skip it and no pinned test fails, so the E-MEM half of NFR-005/REQ-007
  coverage is unproven (the exact layer-mismatch this board polices).
- required disposition: give the E-MEM fault-injection case its own id
  (e.g. T-C16: child under RLIMIT_AS → E-MEM line, exit 1, no partial
  output) in §8.3, and point §7.1's E-MEM row and QC's E-MEM references
  at it.
- decision owner: spec-designer.
- verification required: spec-review cycle 2 checks the id exists and is
  wired (§7.1 row, §8.3 row, §9 anchors).

## SR1-F-05 [P2 | axis 2: spec vs requirements consistency | needs-user:false]

- section/artifact: spec/02-spec-v2.md §6.3 (E-MEM template) and §7.1 E-MEM
  row vs requirements/07-requirements-v7.md NFR-005 (write-phase
  MemoryError clause).
- claim or missing contract: REQ NFR-005 pins: "If exhaustion strikes
  during the output write or serialization, the run fails per the same
  contract ... and a MemoryError there is caught and reported like any
  other write-time failure". "Like any other write-time failure" (per
  REQ-007/D-33) means naming the OUTPUT path. The spec's E-MEM template
  instead hardcodes two INPUT-path forms: `csv2json: error: out of memory
  reading <in>` and `... while converting <in>` — there is no write-phase
  form naming the output path.
- evidence: spec §6.3 E-MEM row: "any phase, MemoryError |
  `csv2json: error: out of memory reading <in>` (parse/serialize/write
  phase: `... while converting <in>`)". REQ-010's write-failure clause and
  D-33 pin output-path naming for write-time failures.
- minimal counterexample: MemoryError raised during the output write on a
  valid 50 MB input: requirements-conforming build prints an error naming
  the output path; spec-conforming build prints `... while converting
  input.csv` — different observable stderr.
- impact: message-shape divergence between spec and requirements on a
  contracted failure class; contract tests written from either document
  disagree.
- required disposition: add the write-phase E-MEM form
  (`csv2json: error: cannot write <out>: ...`-family or an explicit
  `out of memory writing <out>` variant) and reconcile with REQ-007(b)'s
  output-path provision; or, if the single message family is kept, note
  the deviation from NFR-005's "like any other write-time failure" and
  get req-designer sign-off recorded.
- decision owner: spec-designer (req-designer ack if deviating).
- verification required: spec-review cycle 2 checks §6.3/§7.1 align with
  NFR-005's write-phase clause.

## SR1-F-06 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/02-spec-v2.md §4.1 error-paths table ("MemoryError
  anywhere | `ToolError` (generic contract message)") vs §7.3 (handler
  order: `except MemoryError` BEFORE `except ToolError`).
- claim or missing contract: the table says MemoryError maps to ToolError;
  §7.3 says MemoryError is caught as its own class ahead of the ToolError
  handler so the catalog distinction (E-MEM vs E-NET) survives. The table
  is a stale simplification of the pinned handler order.
- evidence: §4.1 table row 6 vs §7.3 first sentence.
- minimal counterexample: n/a.
- impact: an implementor skimming the table models MemoryError as ToolError
  and merges E-MEM into the generic net, erasing the catalog distinction
  §7.3 exists to protect; SR1-F-04 compounds this (no test would catch
  it).
- required disposition: reword the §4.1 row to "own handler before the
  typed net (§7.3)".
- decision owner: spec-designer.
- verification required: none beyond cycle-2 read-back.

## SR1-F-07 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/02-spec-v2.md header block, probes row:
  "appendix/13-spec-design-probes.py (70/70 PASS, 2026-09-17)".
- claim or missing contract: the file prints 63 PASS lines (63 check()
  calls), all passing — re-run live this cycle. The count is wrong (v1's
  header said 70; v2 kept it).
- evidence: `python3 appendix/13-spec-design-probes.py | grep -c '^PASS'`
  → 63, TOTAL FAILURES: 0.
- minimal counterexample: n/a (mechanical).
- impact: minor trust erosion on evidence claims; a cold auditor recounting
  finds a mismatch.
- required disposition: correct the count (or drop the number and cite the
  zero-failures line).
- decision owner: spec-designer.
- verification required: none.

## SR1-F-08 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/02-spec-v2.md §5.3 S-1: "S5 writes 45 bytes".
- claim or missing contract: the pinned output for
  `id,name\n1,x\n2,y\n` is
  `[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n` = 46 bytes (live
  check, appendix/16 R2).
- evidence: len() of the exact pinned bytes = 46.
- minimal counterexample: n/a (mechanical).
- impact: editorial; a byte-count assertion copied from S-1 would fail.
- required disposition: 45 → 46 (or drop the count).
- decision owner: spec-designer.
- verification required: none.

## SR1-F-09 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/02-spec-v2.md §6.2 item 6: "Header-only input
  produces exactly `[]\n` (2 bytes)".
- claim or missing contract: `[]\n` is 3 bytes (`]`, `[`, `\n`).
- evidence: len(b"[]\n") == 3 (live, appendix/17 R8).
- minimal counterexample: n/a (mechanical).
- impact: editorial; wrong byte budget in a byte-level contract section.
- required disposition: "2 bytes" → "3 bytes".
- decision owner: spec-designer.
- verification required: none.

## SR1-F-10 [P3 | axis 3: verification alignment | needs-user:false]

- section/artifact: spec/02-spec-v2.md §8.4 first bullet (macOS fallback
  for the ENOSPC case: "use `ulimit -f`").
- claim or missing contract: on macOS, a write past RLIMIT_FSIZE kills the
  process with SIGXFSZ rather than raising a catchable OSError, so the
  child dies by signal and the E-WRITE contract (message, exit 1, partial
  removal) is never exercised — the fallback as written cannot produce the
  pinned observable.
- evidence: POSIX RLIMIT_FSIZE semantics (SIGXFSZ on exceed; Python does
  not convert it to OSError).
- minimal counterexample: run the tool as a child with `ulimit -f` below
  the payload size on macOS: child exits by signal (returncode < 0), no
  E-WRITE line — T-C8's assertions fail for the wrong reason.
- impact: the documented portability path for a P1-grade contract test is
  unexecutable as written; CI on macOS would see spurious failures or the
  case gets skipped, losing the D-33 proof there.
- required disposition: reword to a working fallback (read-only mount
  directory; or tmpfs-size-capped mount; or mark the ENOSPC shape
  Linux-only and keep message-shape coverage via the non-writable-dir
  case) — and note SIGXFSZ explicitly so the implementor does not "fix"
  the test by catching the signal.
- decision owner: spec-designer.
- verification required: none (test-outline note).

## Verdict block

```
verdict: FAIL
artifact: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/spec/02-spec-v2.md
findings_file: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/19-review-spec-c1.md
findings:
- [SR1-F-01|P1|needs-user:false] §4.3.3+P8 vs §4.3.3 prose+P3+REQ-013/D-28: QUOTED-state newline advance counts CRLF as two breaks -> M off by one on CRLF-interior inputs (`h1,h2\n"a\r\nb",c,"d\ne` -> spec table/P8 M=4, D-28 truth 3); unify arithmetic (P3's), align P8, add CRLF-interior AC to T-U3/T-C7
- [SR1-F-02|P1|needs-user:false] §4.3.2/§5.2/S-9(c) vs REQ D-15 slot (5)<(6): quote check before duplicate check on the header record -> `id,"id` yields E-UQ (spec) vs E-DUP (requirements); reorder to D-15 or get the order pinned, add combined-defect AC
- [SR1-F-03|P2|needs-user:false] header/§1/§11: "D-01..D-36" stale — live register holds D-01..D-42; refresh enumeration and bind D-38..D-42 in §11
- [SR1-F-04|P2|needs-user:false] §7.1 E-MEM row cites T-C9 (perf spot-check) as its proving test; the RLIMIT_AS fault-injection case has no T-id -> give it one and wire it
- [SR1-F-05|P2|needs-user:false] §6.3 E-MEM write-phase message names the INPUT path; NFR-005/D-33 require write-time failures to name the OUTPUT path -> add the write-phase form or record an approved deviation
- [SR1-F-06|P3|needs-user:false] §4.1 table maps MemoryError to ToolError; §7.3 pins a dedicated earlier handler -> reword row
- [SR1-F-07|P3|needs-user:false] header: probes are 63/63 PASS, not 70/70
- [SR1-F-08|P3|needs-user:false] §5.3 S-1: output is 46 bytes, not 45
- [SR1-F-09|P3|needs-user:false] §6.2.6: `[]\n` is 3 bytes, not 2
- [SR1-F-10|P3|needs-user:false] §8.4 macOS `ulimit -f` fallback dies by SIGXFSZ, not OSError -> replace with a working fallback or mark ENOSPC Linux-only
summary: 2xP1 (FSM CRLF line-count arithmetic contradicts REQ-013/D-28 and the spec's own prose/probe P3; header check order contradicts approved D-15 slot order) + 3xP2 + 5xP3; probes genuine, matrix honest otherwise
```


# Spec — csv2json

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | spec |
| version | v11 |
| status | DEPRECATED |
| date | 2026-09-19 |
| author | req2-spec-designer |
| requirements | requirements/07-requirements-v7.md (status: APPROVED, 2026-09-17) |
| user decisions | appendix/01-user-decisions.md (Q-01..Q-06 answered) |
| decision register | appendix/03-decision-register.md (D-01..D-56, all DECIDED) |
| probes | appendix/13-spec-design-probes.py (63 checks PASS, TOTAL FAILURES: 0, 2026-09-17) + appendix/20-rev3-order-probes.py (21 checks PASS, cycle-3 revision evidence: CRLF-interior M, header check order, byte counts) + appendix/22-rev4-writeorder-probes.py (rev4 re-aim evidence: encode-before-open ordering, compensation scope, S5-failure state matrix, E-DUP name-form matrix) + appendix/25-rev5-serialize-form-probes.py (HISTORICAL since the v6 rollover — hardcodes the archived spec/06-spec-v6.md and no longer runs (SR6-F-03); its 26 checks passed at cycle 5 and the subject matter was re-proven live by 30/30b, cycle-5 revision evidence: D-44 single output-named serialize observable, NFR-005 clause coverage, D-01..D-44 enumeration consistency, WRITE_OUTPUT memory edge, generalized interpolated-data scoping incl. the custom-`__repr__` newline premise, T-C16 permissive phase form, register D-44 row) + appendix/28-rev6-writegate-probes.py (HISTORICAL since the v6 rollover — archived spec/06 path, superseded by appendix/30/30b (SR6-F-03); cycle-6 revision evidence at its cycle: single implemented write shape — text-mode parenthetical gone; compensation trigger AFTER a successful open only, at-open failure leaves a pre-existing read-only target byte-identical; aliasing accepted-risk record present; R-2 wording) + appendix/30b-adv-c6-reaim-probes.py (cycle-7 revision evidence: except-scoped reference shape — file kept on success, removed on failure; T-C16 phase-form-dependent state assertion — encode-form bytes survive, write-form file gone; same-path failed-run input deletion (R-4); `-h out.json` dispatch outcome pinned) + appendix/32-rev8-fdclose-probes.py (cycle-8 revision evidence, 6/6 PASS 2026-09-19: D-50 close-before-remove ordering — the failure arm's fd is closed+cleared at remove time, never a live open handle; the superseded v7 arm control removes with the handle OPEN; KeyboardInterrupt through the BaseException arm still removes; delta P5 pins the v8-vs-v7 arm difference) + appendix/36-rev9-ki-argparse-probes.py (cycle-9 revision evidence, 7/7 PASS 2026-09-19: D-51 KI window — KeyboardInterrupt raised inside the §4.5 try REMOVES the partial target, re-raises, exit outside 0/1; the §7.3 except-Exception control leaves the partial and KI reaches the top level; D-52 — argc==1 `-h` → usage line on stderr, exit 1, stdout empty; argc==2 with `-h` positional → E-READ, exit 1, stdout empty; §11 coverage sentence names D-01..D-52; §9 NFR-001 row carries no argparse alternative) + appendix/41-rev10-adv9-folds-probes.py (cycle-10 revision evidence: re-run of the v9 folds on spec/10-spec-v10.md — D-51 single-KI window intact, D-52 dispatch outcomes intact, §11 coverage sentence names D-01..D-55; D-53 double-KI residue reproduced live on the v10 reference shape — second SIGINT inside the failure arm leaves the partial target; D-54 KI-at-open classified at-open, fd None, no remove; D-55 `/dev/stdout` output → exit 0, document on stdout, no tool stdout write) + appendix/47-rev11-adv10-folds-probes.py (cycle-11 revision evidence, 16/16 PASS 2026-09-19: adv-c10's six checks re-run against spec/11-spec-v11.md — D-56(a) MemoryError cascade reproduced live on the v11 reference shape: MemoryError at `fd.write` + second MemoryError at the arm's `fd.close()` leaves the 1546-of-3092-byte partial PRESENT at the E-MEM write-phase stderr line (P1a), control single-MemoryError removes it (P1b), pure-RLIMIT_AS honest negative (P1c); `/dev/stderr` and `/dev/stdout` device outcomes re-verified live (P2a/P2b); §1 and §11 enumerations agree at D-01..D-56 (P3a); the five absolute write-phase-removal sites carry the D-53/R-5 arm-abort qualifier (fold-checks F1-F6); R-6's create-flavor wording present at every mirrored site and the pre-existing-only bound gone from every normative site (P4/F7); §6.1 stderr row + §12 silent-success row carry D-55's regular-file scope (F9)) |
| revision | v11 — cycle-11: fixed all four adversarial-early cycle-10 findings (appendix/45-adv-c10.md, probes appendix/45b; the spec-review#9 gate card is an ARCHIVED STALE TWIN with no board result and no findings artifact, so this revision cites no spec-review verdict — the SR7-F-01 phantom-cite rule, board-verified via appendix/46-board-query-c10.py; adv-early#10's FAIL verdict and findings file ARE board-verified and cited). adv-c10 F-01 (P1): new decision D-56(a) — D-53's arm-abort class is ANY non-OSError (R-5's own wording: "(or any non-OSError)"), so a SECOND MemoryError inside the failure arm aborts the compensation exactly like a second KI (live probe appendix/47 P1a: partial file PRESENT at the E-MEM write-phase stderr line; control P1b: single MemoryError removes it; P1c honest-negative: a pure RLIMIT_AS sweep does not reproduce the cascade — the sanctioned-interruption-point evidence class carries the fold, as the board accepted for D-53/R-5); the five absolute write-phase-removal claims — §5.3 S-14(e), §6.3 E-MEM row, §7.2 footprint sentence, §8.3 T-C16, QC-2 Verification — each gain the "unless the compensation itself is aborted per D-53/R-5 (second KI or second MemoryError)" qualifier, and §7.1's partial-failure taxonomy sentence gains the same clause. adv-c10 F-04 (P2): D-56(b) — R-6's residue bound widened from "bounded to pre-existing targets" to BOTH flavors of the same KI-at-open window: a PRE-EXISTING target may be left truncated to 0 bytes OR an ABSENT target may be left CREATED at 0 bytes (the kernel applies O_CREAT|O_TRUNC before the signal strikes, `fd` never binds, no compensation runs); §10.1 R-6 (body + Impact), QC-2 Scope's exception enumeration, §4.5's KI-AT-OPEN paragraph, §7.2's footprint sentence and the §11 D-54 index entry carry the create flavor. adv-c10 F-02 (P2): D-55's regular-file scope note added to the two stderr-side statements it missed — §6.1's stderr row and §12's "silent success" glossary row, mirroring the stdout row's parenthetical (probe appendix/47 P2a/P2b re-verifies both device outcomes live). adv-c10 F-03 (P3): §1's enumeration refreshed to D-01..D-56 (the v10 revision row had claimed that refresh but left §1 at D-01..D-52 — the same staleness class as adv-c8 F-03). New probes: appendix/47-rev11-adv10-folds-probes.py (45b's six checks re-run against spec/11-spec-v11.md, all PASS, plus the five-site fold-check greps and the R-6 create-flavor textual check). Section numbering unchanged from v10. v10 — cycle-10: fixed all five adversarial-early cycle-9 findings (appendix/39-adv-c9.md, probes appendix/39b; the spec-review#8 gate card was archived with NO board result and no findings artifact, so this revision cites no spec-review verdict — SR7-F-01's phantom-cite rule). adv-c9 F-01 (P1): new decision D-53 — D-51's compensation outcome is re-scoped to a SINGLE-KeyboardInterrupt contract conditional on the failure arm running to completion: a SECOND KI landing inside the arm interrupts the compensation itself (KI is raisable inside `fd.close()`; the arm's `except OSError` clauses do not catch it), so `os.remove` may never run and the partial file survives — recorded as accepted-risk R-5 (§10.1), the accepted residue of best-effort cleanup; a KI-resistant arm is rejected (the `signal` import conflicts with NFR-001's pinned set, D-52's precedent); §4.5 compensation bullet + reference-shape note, §4.5 mutation row 9, §6.4 signal note, §7.1 timeout-cancellation clause, §7.3, T-C8's KI sub-case and QC-2 Scope/Mechanism/Verification re-scoped accordingly (probe appendix/39b P1a/P1b live: double-SIGINT leaves a 1546-of-3092-byte partial; control P1c single-KI removes it). adv-c9 F-02 (P1): new decision D-54 — a KeyboardInterrupt raised BY `open()` itself (fd never bound, including the kernel-applied-O_TRUNC-already state) is classified as an AT-OPEN failure: the arm runs NO compensation and the truncated-to-0-bytes prior target is the recorded residue R-6 (§10.1); the opposite reading (compensate because truncation already happened) is rejected as unimplementable — O_TRUNC application is unobservable from Python; glossary "successful open (compensation trigger basis)", §4.5/D-46's at-open story, §7.1's "survives IFF ... before the open" sentence and QC-2 carry the R-5/R-6 exceptions (probe appendix/39b P2a live: KI-FROM-OPEN on a FIFO-blocked open; P2b: fd None, no remove, prior-good target at 0 bytes). adv-c9 F-03 (P1): new decision D-55 — the §6.4 success row and NFR-004's stdout/stderr rows scope to REGULAR-FILE output paths; a character-device output (`/dev/stdout`, `/dev/stderr`, `/dev/null`, `/dev/fd/N`) is written and exited 0 by every conforming build, recorded as the documented consequence of the caller's own redirection (forbidding it was rejected: new error class outside the CLOSED catalog (D-42) plus stat machinery no REQ mandates); §6.1 form row, §6.4 success row, §9 NFR-004 row, T-K3 and the §11 NFR-004 row carry the scope note (probe appendix/39b P3a/P3b live). adv-c9 F-04 (P2): §6.3's verbatim rule re-scoped to the MESSAGE STRING the tool hands to its single stderr write — the wire bytes additionally depend on the interpreter's stderr encoding (default CPython stderr preserves UTF-8 verbatim; `PYTHONIOENCODING`-overridden encodings may transliterate or make the write raise — the latter is QC-1's residual path, the closed-stderr class R-3); mirrored in §6.4's stderr cell and the §12 glossary "error catalog" row. adv-c9 F-05 (P3): the §6.3 verbatim-slot enumeration now names E-NET's `<in>` explicitly. New probes: appendix/41-rev10-adv9-folds-probes.py (v9 folds re-verified on the v10 text + the D-53/D-54/D-55 mechanisms reproduced live). Section numbering unchanged from v9. v9 — cycle-9: fixed all four adversarial-early cycle-8 findings (appendix/33-adv-c8.md, probes appendix/33b) and, from the spec-review cycle-7 run (card reclaimed mid-cycle before a verdict block was posted; its full-form findings file appendix/34-review-spec-c7.md is the record), the three non-duplicate findings SR7-F-01/F-03/F-04. adv-c8 F-01 (P1, = SR7-F-02): new decision D-51 — KeyboardInterrupt/SIGINT is INSIDE the D-48/D-50 compensation story: the §4.5 BaseException failure arm runs for the KI class too (close per D-50, best-effort remove, re-raise), so an interrupted mid-write run leaves NO partial target; §7.1's timeout-cancellation note now scopes "leaves whatever partial output existed at kill time" to UNCATALOGED kills (SIGKILL, SIGTERM-default) and carves the SIGINT window out to D-51; §7.3's pass-through sentence is qualified (not caught by main's handler chain — the §4.5 arm still compensates before re-raising); §6.4 notes the signal exit (outside the two-valued matrix, traceback wording out of REQ-007's scope); §4.5 table row 9 and QC-2 gain the KI-window sentences; T-C8 gains the SIGINT-fault sub-case (probe appendix/36 P1/P2). adv-c8 F-02 (P2): new decision D-52 — the §4.1 argparse alternative is RETRACTED; the manual `len(argv) != 2` dispatch is the ONE conforming dispatch shape (the sanctioned argparse build could not pass §9 NFR-001's pinned import-set audit, and its default `-h` outcome on argc==1 — help on stdout, exit 0 — violated NFR-004 with no §6.4 row); D-41/D-49 rows narrowed to their live content; §6.1 flags row, §8.3 T-C1, §9 NFR-001 row, §11 REQ-001 row and the coverage-paragraph D-41/D-49 clauses re-aligned; probe appendix/36 P3/P4. adv-c8 F-03 (P2): §11's decision-coverage sentence refreshed to D-01..D-52 (was stale at D-01..D-49 after D-50; probe appendix/33b P5). adv-c8 F-04 (P3): §6.3's verbatim-slot enumeration now names EVERY template's `<path>` slot (E-READ/E-UTF8/E-EMPTY/E-HEADER0/E-DUP `<in>`, E-COUNT/E-UQ `<in> line <N>`, E-WRITE/E-MEM `<out>`), and T-K1's parametrization covers a newline-bearing path form. SR7-F-01 (P1): the v8 header's "adversarial-early cycle-7 verdict PASS" clause is RETRACTED — the board record shows the adv-early#7 gate was reclaimed mid-run and archived with no verdict, no comments, and no findings artifact; this row cites only existing verdict artifacts (appendix/33-adv-c8.md is adv-early#8's FAIL report). SR7-F-03 (P2): the four body cites of appendix/29b (refuses to run on the archived spec/06 path) are re-aimed — §4.1 → appendix/30b P4, S-14(e) → appendix/30b P2/P2b, T-C16 → appendix/30b P2/P2b (29b retained as a historical-annotation parenthetical), QC-2 → appendix/30b P2/P2b — and §6.3's appendix/25 M1 cite is annotated historical (subject matter live in appendix/22's E-DUP name-form matrix and appendix/30b P4). SR7-F-04 (P2): D-50's binding-site lists now name only sites whose text carries D-50 — T-C16 and the §11 REQ-010 row gained the D-50 mention. New probes: appendix/36-rev9-ki-argparse-probes.py (7/7 PASS). Section numbering unchanged from v8. |

# 1. Overview & goals

This document is the implementation spec for `csv2json`, a small,
dependency-free command-line tool that converts a CSV file with a header row
into a JSON array of flat objects. It is derived from
requirements/07-requirements-v7.md (status APPROVED, 2026-09-17). It adds no
requirements, reinterprets none, and leaves none unresolved: D-01..D-56 in
appendix/03-decision-register.md are all DECIDED, all six user answers
(Q-01..Q-06) are folded, and appendix/02-open-questions.md records zero open
questions. The spec is written so an implementor can build the tool from this
document alone, without the requirements conversation.

## 1.1 Goal and success condition

**Goal.** A single-file Python 3 script `csv2json.py` (stdlib only) that
converts a UTF-8 CSV file with a header row into a COMPACT single-line JSON
array of flat objects, all values carried as JSON strings, losslessly, with
silent success and a two-valued exit contract (0 or 1) with the fixed
`csv2json: error:` message shape.

**Success condition** (REQ §1). A user runs `python csv2json.py input.csv
output.json`; the output file contains a valid, compact, single-line JSON
array in which each element maps header names to that row's field values as
JSON strings; `"42"` stays `"42"`, an empty cell becomes `""` (never null);
non-ASCII text appears as raw UTF-8 characters, never `\uXXXX` escapes;
rows with a field count different from the header produce a clear error
naming the line number and the tool exits 1; a successful run prints nothing
to stdout; no third-party packages are required.

## 1.2 Requirement map (traceability entry point)

| REQ/NFR | title (one line) | where designed |
|---|---|---|
| REQ-001 | CLI invocation form, two positional args, usage errors exit 1 | §4.1 CLI, §6.1 |
| REQ-002 | header row defines keys; duplicates error; empty name verbatim | §4.3, §6.2 |
| REQ-003 | one object per data row, in input row order | §4.3, §4.4 |
| REQ-004 | quoted fields (embedded commas/quotes/newlines) per the dialect | §4.3 |
| REQ-005 | values are strings only, lossless; empty cell = "" | §4.3, §4.4 |
| REQ-006 | field-count validation of every data row | §4.3, §6.2 |
| REQ-007 | error message shape `csv2json: error:` + file + line + counts | §6, §7 |
| REQ-008 | fail-fast: first invalid row only; no output on error | §4.3, §5.3 |
| REQ-009 | empty file / invalid header / blank-line / trailing-terminator rules | §4.3, §6.2 |
| REQ-010 | output file safety; write-phase failure → remove partial, report | §4.5, §7.2 |
| REQ-011 | strict UTF-8 decode with D-28 line numbers | §4.2 |
| REQ-012 | UTF-8 BOM stripped from file start; U+FEFF elsewhere is data | §4.2 |
| REQ-013 | unterminated quoted field at end of input is an error (N and M) | §4.3.2 |
| REQ-014 | decode→parse handoff with newline='' semantics | §4.3.1 |
| NFR-001 | zero dependencies (stdlib only) | §9.1 |
| NFR-002 | Python 3.9+ floor is a contract | §9.2 |
| NFR-003 | 50 MB / 250k rows under 30 s / 1 GB envelope | §9.3 |
| NFR-004 | error channel discipline (stderr only; silent success) | §6, §9.4 |
| NFR-005 | no execution of input; field-size limit raised; memory contract | §4.2, §9.5 |

Every mechanism section cites the REQ ids it implements; §11 is the full
traceability matrix (nothing uncovered, nothing invented) and §10 holds the
quality-claim evidence tuples.

## 1.3 Design principles

- **Single external seam.** The tool is a pipeline with ONE external seam —
  the `main(argv)` interface — and the acceptance layer tests through it.
  Internal stages are internal seams used by unit tests only where the
  external seam cannot reach (decode-level line arithmetic).
- **Deep modules.** `main(argv)` is the deep interface: five-line contract
  in, whole-tool behavior out. Stage functions are deep for their stage.
- **Pure-function core, thin process shell.** The core is a pure function of
  the decoded input text; the shell does process plumbing (argv, stdio,
  filesystem, exit codes). This is what makes the tool testable at the
  external seam without mocking infrastructure inside the unit under test.
- **Evidence discipline.** Every stdlib-behavior pin in this spec was
  verified live on Python 3.13.5 in this workspace before being pinned
  (appendix/13-spec-design-probes.py, 63 checks PASS / TOTAL FAILURES: 0); where the requirements
  already probe-verified a behavior, the spec cites that probe too.

# 2. Architecture

The tool is a five-stage linear pipeline with a process shell around it. The
stages exist because the requirements fix a strict error-precedence order
(D-15) and because each stage's failure mode is a different error class.

## 2.1 Component diagram (text form)

```
                 csv2json.py  (single file, stdlib only)
┌────────────────────────────────────────────────────────────────┐
│ shell: main(argv)                                              │
│   argv dispatch · exit codes · stderr/stdout · filesystem      │
└──────────┬─────────────────────────────────────────────────────┘
           │  (input_path, output_path) | UsageError
┌──────────▼─────────────────────────────────────────────────────┐
│ stage 1  read_raw(path) -> bytes          [filesystem in]      │
│ stage 2  decode_utf8(bytes) -> text      REQ-011/012, D-28    │
│ stage 3  parse(text) -> rows | FieldError REQ-014/002/013,    │
│            (per-record, sequential)        REQ-006/009, D-29  │
│ stage 4  serialize(rows) -> str          §5.2, D-14/D-17/26   │
│ stage 5  write_output(path, str)         REQ-010, D-33/D-35  │
└────────────────────────────────────────────────────────────────┘
```

## 2.2 Component responsibilities

| component | responsibility | REQ anchors |
|---|---|---|
| `main(argv)` | dispatch exactly-two-positional-args; run the pipeline; catch the typed error hierarchy; print one REQ-007 message to stderr; exit 0/1 | REQ-001, REQ-007, REQ-008, D-34, NFR-004 |
| `read_raw` | read the whole input file as bytes; map OS errors to the error contract | D-15 (2), REQ-007 |
| `decode_utf8` | strict UTF-8 decode of the whole byte string; strip one leading BOM; locate an invalid byte at a D-28 line | REQ-011, REQ-012, D-13/D-16/D-23/D-28 |
| `parse` | hand the text to `csv.reader` with `newline=''` semantics; iterate record by record; header rules first on record 1 (0-field, duplicates — D-15 slots (4)/(5)), then the per-record unterminated-quote scan (slot (6), header scope included), then per-row count validation; build the list of dicts | REQ-014, REQ-002/003/004/006/009/013, D-15/D-24/D-25/D-29/D-30/D-31/D-36 |
| `serialize` | `json.dumps(rows, ensure_ascii=False, separators=(",", ":"))` + one trailing `\n` | §5.2, D-11b/D-14/D-17/D-20/D-26 |
| `write_output` | encode the document to UTF-8 bytes FIRST (D-43 — before the path is touched); open the output path for binary write; write the payload; flush; on ANY exception raised after a SUCCESSFUL open (OSError or otherwise, D-46) remove the partial file best-effort, then report — OSError per the REQ-007 shape naming the output path, MemoryError per E-MEM's write-phase form | REQ-010, D-33/D-35/D-43/D-46 |

## 2.3 ADR-style decisions (each: decision → rationale)

- **ADR-1 — Pure-function core `parse(text)` over the decoded text; process
  shell owns all I/O.** Rationale: every REQ-identified behavior except
  file-read/write is a pure function of the decoded text, so the riskiest
  logic (D-15 precedence, D-29 ordering, N/M line numbers) is testable at a
  single seam with zero filesystem mocks. The filesystem boundary stays in
  the shell where it is exercised by real-file integration tests.
  (codebase-design: deep module, small interface, one external seam.)
- **ADR-2 — Line numbers come from the tool's own offset arithmetic, not
  from `csv.reader.line_num`.** Probe evidence (13-spec-design-probes.py
  P7): after consuming the record `a\r\n`, `reader.line_num` reports 1 while
  the next row's start line is 2 — it lags one row on CRLF/CR terminators,
  so building messages on it would misreport exactly the CRLF files
  REQ-014/D-24 legitimize. The tool instead records each record's byte span
  via the reader-file's `tell()` (P1: exact, no read-ahead) and computes
  lines from offsets with the D-28 arithmetic (P2/P4). This is a pure
  implementation detail; D-28's normative claim ("same counting basis as
  `csv.reader.line_num`") remains true — both count the same breaks — and
  is corroborated by P7's basis-agreement semantics.
- **ADR-3 — Unterminated-quote detection is a per-record FSM scan of each
  record's own text slice, not a whole-input pre-pass.** Rationale: D-29
  fixes sequential fail-fast (a count-bad earlier row wins), which is exactly
  the behavior of checking each record when it is reached; and P1 proves the
  reader exposes exact per-record slices, so the FSM (P3/P8: dialect-exact on
  all REQ-013 acceptance shapes) sees precisely the text the dialect parsed.
  A pre-pass would duplicate the whole input scan and risk reordering
  against D-15 slot (6).
- **ADR-4 — Single-phase write: validate everything, then one
  open/write/flush with delete-on-failure.** Rationale: REQ-010 forbids
  creating/truncating the output before the input is fully validated, which
  the phase split makes structural (the output path is not even opened until
  `parse` has returned successfully); D-33's delete-on-failure disposition
  (option (b)) is then a two-line compensation in the shell's only write
  site — no temp-file + rename machinery is needed to meet any pinned
  requirement, and the extra moving parts would add failure modes REQ-007
  would then have to cover.
- **ADR-5 — Errors are a typed exception hierarchy internal to the file;
  `main` is the single printer.** Rationale: one formatting site per
  REQ-007(c) element means the message shape cannot drift between error
  classes; typed classes keep D-15's precedence explicit in `parse`'s
  control flow instead of scattered string checks.

## 2.4 What is deliberately absent

No config files, no options/flags beyond the two positional args, no stdin/
stdout I/O, no dialect sniffing, no streaming for oversized files, no type
inference, no logging (silent success is the contract), no Windows-specific
code paths beyond avoiding newline translation (D-35 is platform-neutral).
Out-of-scope per REQ §3.2; the implementor adds none of these.

# 3. Domain model & data dictionary

The tool's domain is small; its subtlety lives in a handful of terms that the
requirements pinned precisely. This section restates the domain in
implementation-facing terms; the glossary (§12) is normative for wording.

## 3.1 Entities

| entity | type in the implementation | constraints / invariants |
|---|---|---|
| Input CSV | bytes on disk → `bytes` → `str` (decoded) | must be strict UTF-8 (REQ-011); one optional leading BOM (REQ-012); first parsed record is the header (REQ-002) |
| Header row | `list[str]` (parsed once) | length ≥ 1 (REQ-009); names unique (REQ-002/D-12); empty name allowed once (REQ-002/F-33); used verbatim, no trimming/case-folding |
| Data row | `list[str]` (parsed) | `len(row) == len(header)` exactly (REQ-006); `len >= 1` always true for parsed non-header rows (a blank line parses to 0 fields and errors per REQ-009) |
| Field value | `str` | data only, no semantics assigned (D-05/NFR-005); carried verbatim into JSON (REQ-005/D-11); control characters are data (D-14) |
| Output JSON | `str` (one `json.dumps` call) → bytes UTF-8 written binary | compact single line; ends `]\n` byte-exact on every platform (D-26/D-35); array of flat objects in input row order (REQ-003/D-06) |
| Physical line | derived: count of D-28 breaks before an offset, + 1 | breaks are exactly `\n`, `\r\n` (ONE), bare `\r`; VT/FF/NEL/U+2028/U+2029 are data (D-28) |
| Record span | `(start_offset, end_offset)` per parsed record, in decoded-text code points | obtained from the reader file's `tell()` around `next()`; exact, no read-ahead (probe P1); basis for all row-start line numbers |

## 3.2 Ubiquitous language (deltas and bindings for the implementor)

- "record" = what `csv.reader` yields per iteration (a logical row; may span
  several physical lines). "physical line" = D-28 line of the decoded text.
  Never conflate the two in code identifiers: use `record*` for parsed rows
  and `line*` for D-28 line numbers.
- "blank physical line" means EMPTY (zero characters between terminators) —
  it parses as a 0-field record; a whitespace-only line is an ordinary
  1-field data row (D-36). Identifier hint: `is_blank_record` never tests
  `strip()`; emptiness is decided by the dialect's 0-field parse, not by
  character inspection.
- "unterminated quoted field" is a property of a RECORD's text (its quoted
  section never closed by end-of-input), detected by the FSM of §4.3.2; the
  term never applies to a `"` inside an unquoted field (that is data, D-30).
- "row-start line" (REQ-007(c)) = the physical line of the record's FIRST
  character = `line_of_offset(text, record_start_offset)`.
- "opened-at line" (REQ-013 M) = row-start line + (record-relative line of
  the opening quote) − 1.

# 4. Module-by-module design

One file, `csv2json.py`, laid out in this order: module docstring, imports
(`argparse`-free — see §4.1; `csv`, `io`, `json`, `os`, `sys`), limit-raising
call, exception types, pure helpers, stage functions, `main`, entry-point
guard. Interface sizes are deliberately small; all behavior sits behind
them.

## 4.1 CLI shell — `main(argv)`

- **Purpose.** Own everything process-shaped: argument dispatch, the error
  printer, exit codes, and the call order of the five stages.
- **Interface.** `main(argv: list[str]) -> int` plus a module entry guard
  `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`.
  Callers/tests need only this one function.
- **Behavior — argument dispatch (REQ-001, D-34).** If `len(argv) != 2`,
  print `csv2json: error: usage: csv2json.py <input.csv> <output.json>` to
  stderr and return 1. Manual dispatch (an `if`) is specified instead of
  `argparse` because argparse's default usage-exit is 2 and its default
  error text does not carry the `csv2json: error:` prefix; both deviations
  would have to be overridden (probe-verified exit 2, appendix/10-fold-c5
  F29 probe) — the simpler construction is to not create the deviation.
  **No argparse alternative exists (D-52, closes adv-c8 F-02).** Earlier
  revisions sanctioned a hypothetical argparse build under override
  conditions; that branch is RETRACTED in v9 — an argparse build is
  NON-CONFORMING in this tool, for two observed reasons: (a) importing
  argparse flunks §9 NFR-001's pinned import-set audit
  (`csv, io, json, os, sys` — an extra top-level import has no conforming
  reading there); (b) argparse's builtin help action fires on `csv2json.py
  -h` (argc==1, outside D-49's length-2 scope) printing help to STDOUT and
  exiting 0 — an outcome NFR-004 (stdout empty on every path) and the §6.4
  matrix (no help row, no exit 0 outside success) forbid, and §4.1's old
  help-override clause scoped itself to "this two-positional form" so it
  never reached the argc==1/3 classes (live: adv-c8 probes P3a/P3b,
  appendix/33-adv-c8.md; the dispatch outcomes on BOTH argv classes are
  pinned by appendix/36-rev9-ki-argparse-probes.py P3/P4). The manual
  `if len(argv) != 2` branch is the ONE dispatch shape this spec permits:
  §6.1's flags row, §8.3 T-C1, §9 NFR-001, §11 REQ-001, and D-41/D-49 are
  aligned to that single shape.
- **Behavior — pipeline order (D-15).** With two arguments, run in order:
  (2) `read_raw(input_path)`; (3) `decode_utf8`; (3b) the parse-time
  construction inside `parse` (its `io.StringIO(text, newline="")` IS the
  REQ-014 handoff); (4)–(6) inside `parse` (header/row validation
  sequential, first error wins); (7) `serialize` then `write_output`.
  Any typed error (§7) propagates to `main`'s single handler.
- **Behavior — success (NFR-004, D-11b).** On success return 0; print
  NOTHING to stdout (no summary line, no filename echo).
- **Behavior — failure (REQ-007/008, NFR-004).** Print exactly one line to
  stderr: the message carried by the typed error, already fully formatted
  per the REQ-007 shape; return 1. "Exactly one line" is the TOOL's
  print discipline (F-03, option (a)): the tool performs exactly one
  stderr write and adds no newline of its own beyond the message's
  terminating one; it never emits a second message. A line break borne
  by DATA interpolated into ANY message slot — a header name containing
  a raw newline (quoted legally per REQ-004) in E-DUP's `<name>`, an
  exception repr carrying one in E-NET's `<exception repr>`, or an OS
  strerror carrying one (platform-dependent) in E-READ/E-WRITE — may wrap
  that single message across physical lines — the tool does not escape
  or sanitize interpolated data (the catalog form is verbatim; §6.3
  E-DUP note).
  Never print a traceback (any residual unexpected exception is also
  caught and reported per the REQ-007 net — see §7.3), never write a
  partial output on a failed run.
- **Error paths.** Table:

| condition | error type raised/caught | message emitted by | exit |
|---|---|---|---|
| `len(argv) != 2` | (none — handled inline) | inline usage line, prefixed | 1 |
| input unreadable (OS) | `InputReadError` | `main` via formatter | 1 |
| invalid UTF-8 byte | `InvalidUtf8Error` | `main` via formatter | 1 |
| empty file / 0-field first row / count error / duplicate header / unterminated quote | `FieldError` (with class-specific text) | `main` via formatter | 1 |
| output open/write/flush OSError | `OutputWriteError` | `main` via formatter | 1 |
| MemoryError anywhere | own `MemoryError` handler ahead of the typed net (§7.3 handler order) — E-MEM per its phase form | `main` via formatter | 1 |
| any other residual exception | caught in `main` | REQ-007 net message | 1 |

## 4.2 Decode stage — `read_raw`, `decode_utf8`, line arithmetic helpers

- **Purpose.** Own the bytes→text boundary and the D-28 line basis: nothing
  else in the file knows about encodings or line counting.
- **Interfaces.**
  - `read_raw(path: str) -> bytes` — opens binary, reads whole file, closes.
  - `decode_utf8(data: bytes) -> str` — strict decode, BOM strip, raising
    `InvalidUtf8Error` with a computed line number.
  - `line_of_offset(text: str, offset: int) -> int` — pure D-28 counter.
- **Behavior — read (D-15 slot 2).** Any `OSError` opening/reading the input
  becomes `InputReadError` carrying the OS strerror; message:
  `csv2json: error: cannot read <path>: <strerror>` (REQ-007(b), prefix per
  (a); no line number exists for this class).
- **Behavior — strict decode (REQ-011, D-13).** `data.decode("utf-8")` with
  no error parameter. On `UnicodeDecodeError`: compute
  `line = line_of_offset(data[:e.start].decode("utf-8"), len(...))` — the
  valid-UTF-8 prefix is itself decoded and the offending byte's position
  mapped on the D-28 basis (probe P4: the CR-only REQ-011 acceptance file
  `a,b\rc,d\rc\r\xff` yields exactly line 4). Message:
  `csv2json: error: <path> line <N>: byte 0x?? is not valid UTF-8` where
  `0x??` is the offending byte in two-digit lowercase hex (REQ-011's
  "stating the byte sequence is not valid UTF-8"; the single-byte form
  covers the acceptance cases; multi-byte sequences surface at their first
  invalid byte, which `e.start` gives exactly).
- **Behavior — BOM strip (REQ-012, D-16, D-31).** After successful decode,
  if `text` starts with U+FEFF, remove exactly that one character. A U+FEFF
  anywhere else is data (later stages never inspect it). The strip happens
  BEFORE the empty check, so a BOM-only file becomes the empty string and
  routes to REQ-009's empty-file error (D-31; probe P8 "BOM-only file").
- **E-UTF8 line-number basis (F-04 note).** The N in the E-UTF8 message is
  `line_of_offset(text, e.start)` — the D-28 physical line of the
  OFFENDING BYTE ITSELF (which may sit mid-row, far past its row's start
  line), not REQ-007(c)'s row-start convention (which is meaningless
  pre-parse; §4.2's formula settles the value operationally).
- **Behavior — `line_of_offset` (D-28).** Pure function; counts breaks by
  scanning `text[0:offset]`: `\r\n` advances one line and consumes two
  characters; a bare `\r` (next char exists and is not `\n`) or a `\n`
  advances one line and consumes one; VT 0x0B, FF 0x0C, NEL U+0085,
  U+2028, U+2029 advance nothing. `line_of_offset(anything, 0) == 1`.
  THIS ONE-BREAK-PER-TERMINATOR BASIS IS TOOL-WIDE: CRLF is one break
  everywhere, including inside a quoted section of a record — every line
  number the tool prints (E-UTF8 N, E-COUNT N, E-UQ N and M) is derived
  from this same counter (or the incremental per-span accumulation of
  §4.3.2, which shares this exact definition via `count_line_breaks`), so
  no stage may count a terminator pair as two breaks. The record-relative
  FSM counter of §4.3.3 is the same arithmetic restricted to the record's
  own span (SR1-F-01 fix: the QUOTED row of that FSM's table previously
  advanced once per `\r` and once per `\n`, splitting CRLF; it now
  collapses CRLF and counts bare CR as one, exactly as here).
  A `str.splitlines()`-based counter is NON-CONFORMING (it breaks on VT/FF/
  NEL/U+2028/U+2029 — probe P2 shows the divergence). Reference shape
  (verified by probes P2/P4, appendix/13-spec-design-probes.py):

```
line = 1
i = 0
while i < offset:
    if text[i] == "\r":
        i += 2 if text[i+1:i+2] == "\n" else 1
    else:
        i += 1          # covers "\n" and every non-break character
    if a break was consumed: line += 1
```

- **Error paths.** `InputReadError` (above); `InvalidUtf8Error` (above);
  `MemoryError` on a huge file is NOT specially caught here — it propagates
  to `main`'s residual net (§7.3), which reports it per the generic
  contract (`out of memory reading <path>` — the E-MEM read-phase form,
  §6.3).

## 4.3 Parse stage — `parse(text)` (the deep core)

- **Purpose.** The whole tool's decision logic: dialect-exact record
  iteration, unterminated-quote detection, header rules, per-row count
  rules, in D-15/D-29 order. Pure: text in, list-of-dicts out, typed errors.
- **Interface.** `parse(text: str) -> list[dict[str, str]]`, raising
  `FieldError` (message fully pre-formatted) — one method, five behavior
  clauses below. The input path name is passed for message construction
  (`parse(text, input_name)`); nothing else is configurable.
- **Behavior — 4.3.1 construction, the REQ-014 handoff (D-24).** The FIRST
  statement builds `reader = csv.reader(io.StringIO(text, newline=""))`.
  `newline=""` is the contract: it disables newline translation at the
  StringIO so CR/CRLF/LF reach the dialect intact (probe P8 CR-only and
  CRLF-in-quoted-field cases; the requirements verified the same
  constructions live, appendix/05-review-req-c2-probes.py batch 2).
  FORBIDDEN anywhere in the pipeline: `io.StringIO(text)` without
  `newline=""` (crashes on CR-only files), universal-newline file reading,
  `str.splitlines()` reconstruction (rewrites quoted-field CRLF/CR to LF —
  a lossy mangle). Before iterating, the startup limit-raise of §4.6 has
  already run (it is process-global, not per-parse).
- **Behavior — 4.3.2 per-record loop (D-15 slot 6, D-29).** Iterate records;
  for each, first determine its text span:

```
start = 0
line = 1                      # running row-start line (incremental, NFR-003)
while True:
    try:
        record = next(reader)
    except StopIteration:
        break
    end = reader_file.tell()          # AFTER next() — probe P1 order
    record_text = text[start:end]
    row_start_line = line             # == line_of_offset(text, start)
    # --- record 1 only: header rules FIRST (D-15 slots (4)/(5)) ---
    #     check 1: 0-field header row (REQ-009, §4.3.4 i)
    #     check 2: duplicate header names (REQ-002, §4.3.4 ii)
    # --- every record, AFTER the header rules above ---
    #     check 3: unterminated quote (REQ-013, D-30 FSM below)
    #     check 4: field-count rule for data rows
    line += count_line_breaks(text, start, end)   # D-28 basis, O(end-start)
    start = end
```

  The checks run in exactly this order PER RECORD: on the FIRST record
  the two header rules (D-15 slots (4)/(5)) run BEFORE the quote scan
  (slot (6)); on EVERY record the quote scan runs BEFORE the count check.
  The loop returns or raises at the first failing check of the first
  failing record — this IS the D-29 sequential fail-fast (no whole-input
  pre-pass; a count-bad earlier row raises before a later
  unterminated-quote row is ever examined; probe P8 "count error wins
  over later quote").
  WHY the header record defers its quote scan (SR1-F-02 fix, mandatory):
  the APPROVED D-15 orders slot (5) duplicate-header BEFORE slot (6)
  unterminated-quote, and REQ-013/D-25 give the quote check SCOPE over the
  whole input INCLUDING the header. Scope says the header's quote defect
  IS detected (never the lenient `[]` outcome); order says it is detected
  only after the header's higher-precedence checks pass. On a
  combined-defect header (`id,"id` — duplicate names AND an unclosed quote
  on one physical line) the tool therefore reports E-DUP
  (`duplicate header name 'id'` at line 1), never E-UQ; that acceptance
  case is pinned in §8.1 T-U6 and §8.3 T-C7. A header with NO duplicate
  still trips the quote scan (`"id,name` → E-UQ line 1, D-25, unchanged).
  Data records are unchanged: quote check first, then count.
  The line counter advances INCREMENTALLY (count breaks of the record's
  span and add them): calling `line_of_offset(text, start)` from offset 0
  per record would rescan the whole prefix each time — quadratic across
  many records and a violation of the NFR-003 envelope (fixed here so the
  implementor does not reintroduce it). `line_of_offset` itself remains
  the decode-stage counter (called once per run, §4.2); the incremental
  form shares its D-28 break definition via the same `count_line_breaks`
  helper, so the two can never diverge.
- **Behavior — 4.3.3 unterminated-quote FSM (REQ-013, D-30).** A per-record
  scanner over `record_text` with states FIELD_START / UNQUOTED / QUOTED /
  CLOSED:

| state | on `"` | on `,` | on `\n` or `\r` | on other |
|---|---|---|---|---|
| FIELD_START | → QUOTED, remember current record-relative line as the opening line | stay FIELD_START | → FIELD_START (record-internal terminator; the terminator belongs to this record's own span — reachable for a record-internal empty line, a trailing empty field such as `a,\n`, or the empty record itself; the scan never crosses into the next record's span) | → UNQUOTED |
| UNQUOTED | stay UNQUOTED (data — D-30) | → FIELD_START | → FIELD_START | stay UNQUOTED |
| QUOTED | → CLOSED | stay QUOTED (data) | stay QUOTED (data); the record-relative counter advances by ONE per terminator, where a consecutive `\r\n` pair is ONE terminator (the D-28 basis of §4.2 — never one advance per character) | stay QUOTED |
| CLOSED | → QUOTED (doubled quote re-opens) | → FIELD_START | → FIELD_START | → UNQUOTED |

  NORMATIVE counting rule for the record-relative counter (SR1-F-01 fix,
  binding for every row of the table): the counter obeys the §4.2 D-28
  arithmetic restricted to the record's span. Scanning `record_text`, a
  `\r` immediately followed by `\n` advances the counter by ONE and
  consumes both characters; a `\r` at end of `record_text` (or a `\r`
  whose next character is not `\n`) or a `\n` advances by ONE and consumes
  one character. This collapse applies in EVERY state: in the QUOTED row
  it advances the counter with no state change; in the FIELD_START /
  UNQUOTED / CLOSED rows the `→ FIELD_START` transition consumes a whole
  `\r\n` pair and advances once. The opening line remembered at a
  `"`-transition is the counter value AFTER all such collapses upstream of
  that quote. Result: a CRLF or bare CR inside a quoted section of the
  offending record adds exactly ONE to M, matching `line_of_offset`/D-28
  and probe P3 (the former per-character advance split CRLF into two
  advances and put M one too high per interior CRLF/CR — see T-U3's
  CRLF-interior case, which now pins the correct value).

  If, at end of `record_text`, the state is QUOTED, the record has an
  unterminated quoted field: raise `FieldError` with N = `row_start_line`
  and M = `row_start_line + opening_line - 1` (M = the D-28 physical line
  of the opening quote — by the counting rule above, a CRLF or bare CR
  inside an earlier quoted field of the same record adds exactly ONE to M,
  never two). Worked CRLF-interior case (probe-verified, appendix/20):
  `h1,h2\n"a\r\nb",c,"d\ne` — row 2 starts at line 2 (N = 2); scanning the
  record's span, the `\r\n` inside the first field advances the
  record-relative counter once, so the third field's opening quote sits on
  record-relative line 2 and M = 2 + 2 - 1 = 3:
  `csv2json: error: in.csv line 2: unterminated quoted field (opened at
  line 3)` — note 3, the file's real physical line of that quote (the
  pre-fix per-character count produced the nonexistent "line 4").
  `csv2json: error: <path> line N: unterminated quoted field (opened at
  line M)`. Probe P3 exercises all REQ-013 acceptance shapes (including
  `5" ruler` as data, doubled quotes, post-close junk) and P8 pins the
  end-to-end N/M outcomes (line 2/opened at line 3 for the multi-field AC;
  line 1 for `"id,name`).
  FSM details that make it dialect-exact (all probe-verified): the FSM
  never runs past the record's own span; CRLF inside a record's text
  (possible only inside a quoted section) is one line break for the
  record-relative counter; a `"` in UNQUOTED is data; post-CLOSE `"` is a
  doubled quote (re-open) but post-CLOSE other-character returns to
  UNQUOTED (so `"a"b` is the data field `ab`-with-quote, never an error).
- **Behavior — 4.3.4 header rules (first record only; REQ-002/009).** In
  order: (i) if `len(record) == 0` (the file's first parsed record is
  0-field — e.g. only blank physical lines), raise
  `csv2json: error: <path> line 1: invalid header row (found 0 fields)`
  (probe P8 "only blank lines": `\n\n` → this message at line 1; the
  no-records-at-all case is end-of-iteration, below, not this clause).
  (ii) duplicate scan left-to-right with a set: on the first name already
  seen, raise
  `csv2json: error: <path> line 1: duplicate header name '<name>'`
  (D-12; the empty name participates normally — a SECOND empty name
  duplicates and the message cites `''`, probe P8). (iii) otherwise the
  header is accepted verbatim (no trimming/case-folding; empty name
  allowed, F-33) — and THEN, per the §4.3.2 order, the record's
  unterminated-quote scan runs (so `"id,name` → E-UQ at line 1, while the
  combined defect `id,"id` already raised E-DUP at step (ii), S-9b).
- **Behavior — 4.3.5 data-row rules (subsequent records; REQ-006/009).**
  `len(record) != len(header)` raises
  `csv2json: error: <path> line <row_start_line>: expected <len(header)>
  fields, found <len(record)>` — this covers blank-line 0-field records
  (`found 0`) at their own line, including a trailing blank line (probe
  P8: `a,b,c\n1,2,3\n\n` fails at line 3), and whitespace-only lines are
  ordinary 1-field rows (never an error here, D-36). Field-count-matching
  rows become `dict(zip(header, record))` appended in input order
  (REQ-003; dict preserves insertion order on all supported Pythons —
  NFR-002 floor 3.9: ordered dicts are a language promise there).
- **Behavior — end of iteration (REQ-009/D-31).** If the reader yielded no
  record at all (empty string after BOM strip), raise
  `csv2json: error: <path>: file is empty (no header row)` — no line
  number in this class (probe P8 "empty file" and "BOM-only file").
  Note the empty-file check is expressed as "no first record", which is
  exactly equivalent to the empty-text condition and immune to ordering
  disputes.
- **Error paths.** All errors leave `parse` as `FieldError` with the final
  message text; `parse` performs no printing and no I/O. A residual
  `_csv.Error` (none remains possible after §4.3.1's pins, but defensively)
  or any unexpected exception propagates to `main`'s net (§7.3).

## 4.4 Serialize stage — `serialize(rows)`

- **Purpose.** Turn the row list into the exact output document bytes
  contract (§5.2 of the REQ): compact, raw UTF-8, escape forms, one
  trailing newline. Deep for its size: every byte-level decision of §5.2
  lives behind this one call.
- **Interface.** `serialize(rows: list[dict[str, str]]) -> str` returning
  the full document INCLUDING the trailing newline; the write stage then
  encodes (before touching the path, D-43) and writes. (Keeping the
  newline here — not in the write stage — makes the byte contract a
  pure-function test.)
- **Behavior.** Exactly:
  `payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))`,
  then `return payload + "\n"`.
  - `separators=(",", ":")` is MANDATORY (D-26): json.dumps' defaults are
    `", "`/`": "` (space after every comma) — non-compact (probe
    05c-separators, REQ §5.2; probe P6 in this workspace).
  - `ensure_ascii=False` is MANDATORY (D-17): non-ASCII becomes raw UTF-8
    characters in the encoded bytes (probe P6 Thai case).
  - Escape forms are whatever this construction emits (D-14/D-20): short
    forms `\f \b \n \r \t \" \\`; `\u00xx` lowercase for control chars
    without short forms (NUL → `\u0000`, VT → `\u000b`); DEL 0x7F and
    U+2028/U+2029 raw (all probe P6). The implementor must NOT post-process
    or customize the escaping.
  - The trailing `"\n"` makes the document end `]\n` (D-26/F-19).
- **Error paths.** `MemoryError` on a gigantic payload propagates to the
  residual net (§7.3) — reported per the OUTPUT-named E-MEM form
  (`out of memory writing <out>`, §6.3, D-44), exit 1, no output file
  (REQ-010: nothing has been opened yet at this stage, so no compensation
  applies — the serialize phase simply leaves the filesystem untouched).
  NFR-005's clause covers serialization in its "reported like any other
  write-time failure" sentence, which names the OUTPUT path (D-33's
  output-path provision); D-44 pins that single observable for both the
  serialize and write phases. json.dumps on `list[dict[str, str]]` cannot
  otherwise fail.

## 4.5 Write stage — `write_output(path, document)`

- **Purpose.** The only place that touches the output filesystem: one
  open/write/flush, with D-33's delete-on-failure compensation.
- **Interface.** `write_output(path: str, document: str) -> None`, raising
  `OutputWriteError` on any failure (message pre-formatted with the OUTPUT
  path; `main` prints it).
- **Behavior — operation order (D-43, normative: encode BEFORE open).**
  The stage executes in exactly this order:
  (1) `payload = document.encode("utf-8")` — UTF-8, no BOM (D-09) —
  COMPLETES FIRST, while the output path is still untouched;
  (2) `open(path, "wb")` (binary);
  (3) `write(payload)`, then `flush()`, then close — closed MANUALLY in
  the reference shape below (`fd.close(); fd = None` inside the try, so
  the failure arm can test `fd is not None` and run its own
  close-before-remove per D-50); a `with` block is an acceptable
  equivalent only if the D-48 failure-arm semantics (remove in the
  failure arm only, guarded by whether the open succeeded) AND the D-50
  close-before-remove ordering are preserved. Flush failures surface
  before close accounting either way.
  Rationale (F-01/F-02 disposition): `open(..., "wb")` truncates an
  existing target AT OPEN (POSIX O_TRUNC), before any write call; an
  encode placed after open would let a MemoryError at encode destroy a
  pre-existing good output while the OSError-scoped compensation never
  fires (MemoryError is not an OSError — appendix/21b probes W1/W2).
  Encoding first makes the encode phase a no-side-effect transformation:
  a failure there leaves every output target byte-identical, created or
  pre-existing (probe appendix/22-rev4-writeorder-probes.py, W-series:
  MemoryError at encode → pre-existing bytes intact, no file created).
  Binary mode makes the `]\n` ending byte-exact on every platform; a
  text-mode open without `newline=""` would emit `]\r\n` on Windows and
  is NON-CONFORMING (D-35).
  **Single implemented shape — text mode NON-CONFORMING for this stage
  (D-45, closes adv-c5 F-01).** Binary `open(path, "wb")` is the ONE
  write shape this spec permits; there is NO conforming text-mode
  alternative. In a text-mode build (`open(path, "w", newline="",
  encoding="utf-8")`, writing `document` itself) the encode happens
  implicitly INSIDE the write call — necessarily AFTER the open has
  already applied O_TRUNC — so a MemoryError at that implicit encode is
  a failure after the truncation point: it is exactly the D-43 outcome
  class (pre-existing output destroyed by an encode-phase OOM) that
  D-43 was created to prevent, and the pre-open no-side-effect phase
  that delivers QC-2's "before the open" coverage cannot exist in that
  shape (probe appendix/28-rev6-writegate-probes.py R6-P1: fault at the
  implicit encode truncates/removes the prior good file in the text-mode
  shape while the pinned binary shape leaves it byte-identical on the
  identical fault). Byte-exactness alone (D-35) could be repaired with
  `newline=""`, but the ordering defect cannot; text mode is therefore
  non-conforming for the write stage as a whole, and T-C8/T-C16 apply
  only to the binary shape.
- **Behavior — write then flush; compensation scope (D-33 as widened
  here, per F-01; trigger narrowed per D-46, closes adv-c5 F-04).**
  `write(...)`, then `flush()` BEFORE close accounting: D-33
  names flush-time failures (ENOSPC on some filesystems surfaces at
  flush/close) as covered. Steps after the open — the write, the flush,
  the close (manual in the reference shape below; the wrap is over the
  whole try body), and equally a MemoryError surfacing inside the
  write (per §6.3's E-MEM write-phase form) — are wrapped so that ANY
  exception raised AFTER A SUCCESSFUL OPEN first runs the compensation
  (below), then propagates: `OSError` → `OutputWriteError` with message
  `csv2json: error: cannot write <path>: <strerror>` (REQ-007 shape with
  (b)'s output-path provision); MemoryError → the residual net (§7.3),
  reported as E-MEM's write-phase form
  `csv2json: error: out of memory writing <path>`.
  **At-open failures are NOT compensation triggers (D-46).** If `open`
  itself raises — EACCES/EPERM on a pre-existing read-only target or
  unwritable directory, EISDIR, any open-time OSError — the open never
  succeeded, so no partial write exists and there is nothing to clean
  up: the stage reports the E-WRITE message directly and the output
  path is left EXACTLY as it was, absent or pre-existing (probe
  appendix/28-rev6-writegate-probes.py R6-P2: pre-existing read-only
  target in a writable directory survives a failed run byte-identical).
  **KI-AT-OPEN classification (D-54, closes adv-c9 F-02).** `open()`
  itself can raise KeyboardInterrupt: SIGINT delivered while the process
  is blocked inside the open syscall (a FIFO with no reader, a slow
  NFS/FUSE target) makes `open()` raise KI — including the state where
  the kernel has ALREADY applied O_CREAT|O_TRUNC but the signal struck
  before `open()` returned and `fd` was bound. That case is classified
  as an AT-OPEN failure, NOT a D-51 post-open failure: the reference
  shape observes `fd is None`, the arm runs NO compensation, and the KI
  propagates — so a PRE-EXISTING target may be left truncated to 0
  bytes by the kernel's O_TRUNC even though this stage wrote nothing,
  AND an ABSENT target may be left CREATED at 0 bytes by the kernel's
  O_CREAT — the same window's two flavors (adv-c10 F-04, decision
  D-56(b)); in the create flavor the run leaves behind a 0-byte file
  that DID NOT EXIST before.
  That 0-byte residue is accepted-risk R-6 (§10.1), the same
  record-don't-contract disposition as R-5; the fd-binding point is the
  only observable boundary the reference shape has (whether the kernel
  applied O_TRUNC is unobservable from Python without extra syscalls or
  imports, so compensating "whenever O_TRUNC may have applied" has no
  conforming mechanism). T-C8's matrix documents the KI-at-open
  outcome per this reading.
  Earlier revisions worded the trigger as "EACCES at open" inside the
  compensation scope; that wording is superseded (register D-46) —
  running the remove after a failed open would delete a pre-existing
  target the run never opened (the adv-c5 P10 destruction), contradict
  the compensation's own rationale (a partially written file must never
  survive — nothing was partially written here), and break the REQ-008
  intent that a failed run leaves the user's file "absent or unchanged"
  in its unchanged sense. The compensation's REFERENCE SHAPE is an
  except-scoped block — the remove lives inside the failure arm ONLY, so
  it can never run on the success path (a bare `try/finally` runs its
  finally on success too and would delete the just-written output; a
  finally-based shape is conforming ONLY with an explicit failure flag
  such as `error = True` set at the top of the try and cleared after the
  close, the finally removing only while the flag still reads True).
  Conforming reference shape (e.g.):

  ```
  fd = None
  try:
      fd = open(path, "wb")            # at-open failure: jumps to except, no remove
      fd.write(payload); fd.flush()    # encode already done pre-open (D-43)
      fd.close(); fd = None            # closed: nothing left to compensate
  except BaseException:
      if fd is not None:               # open SUCCEEDED and a later step raised
          try: fd.close()              # D-50: close BEFORE the remove (Windows: os.remove on an open handle raises)
          except OSError: pass         #   close errors are ignored too (best-effort)
          fd = None
          try: os.remove(path)         # best-effort (D-33; errors ignored) — fd now CLOSED on every platform
          except OSError: pass
      raise
  ```

  The except arm re-raises after the compensation, so §4.5's propagation
  rules are unchanged. The arm itself carries two contracted failure
  windows (D-53/D-54): a SECOND KeyboardInterrupt (or any non-OSError)
  raised INSIDE the arm — at its `fd.close()` or `os.remove` — is not
  caught by the arm's `except OSError` clauses, aborts the compensation
  mid-flight, and leaves the partial file in place (accepted residue
  R-5, §10.1 — the arm is best-effort, not KI-proof); and a KI raised by
  the `open()` call itself leaves `fd is None` with NO remove run — the
  D-54 at-open classification, whose kernel-level O_TRUNC residue is
  R-6 (§10.1). The failure arm's close-before-remove ordering is
  decision D-50: the OS keeps the target's handle open until `fd.close()`
  runs, and on Windows `os.remove` on an open handle raises
  `PermissionError` — which the best-effort clause would swallow, leaving
  the partial file in place (a deterministic QC-2 violation on a platform
  in the conformance domain). Closing first (errors ignored) makes the
  remove a real best-effort step on every platform; a shape that removes
  while the fd is open is NON-CONFORMING. The normative contract is the
  state outcome, not the syntactic form: after a failed write attempt
  on a regular-file path — where "failed write attempt" means the open
  SUCCEEDED and a later step raised — the target is removed, whatever
  exception class the failure raised, ON EVERY PLATFORM IN THE
  CONFORMANCE DOMAIN — ALWAYS within the D-53 arm-abort scope: the arm
  must run to completion; a second KI or a second MemoryError (any
  non-OSError) landing INSIDE the arm aborts the compensation and the
  partial file survives as the recorded residue R-5 (D-56(a),
  adv-c10 F-01) (the mechanism above delivers the outcome on POSIX
  and Windows alike; probe appendix/32-rev8-fdclose-probes.py P2/P3:
  fd.closed is True at remove time, remove-after-close in the failure
  arm, and the pre-close shape leaves the fd open at raise):
  10-fold-c5 F28: `/dev/full` accepts open, fails flush with errno 28 —
  the run must exit 1 with the E-WRITE message shape and no leftover
  partial file; probe 22-rev4 W-series: MemoryError at
  write/encode-in-S5 → partial removed, pre-existing file NOT silently
  kept as partial; probe appendix/30b-adv-c6-reaim-probes.py P1: the
  except-scoped shape keeps the file on success and removes it on
  failure — the v6 finally-guarded snippet deleted the just-written
  output of every successful run and is superseded, register D-48).
- **Behavior — compensation (D-33, delete-on-failure; trigger scope
  D-46; close ordering D-50; aliasing boundary D-47; single-KI scope
  D-53).** On ANY exception
  raised after a
  SUCCESSFUL open — including KeyboardInterrupt (D-51: the arm is
  BaseException-scoped precisely so the signal class is compensated; the
  fd close + best-effort remove run BEFORE the KI re-raises) — the
  failure arm has first closed the fd (D-50,
  errors ignored), so the remove acts on the PATH, not on an open
  handle:
  best-effort
  `os.remove(path)` of
  the exact path this stage opened; IGNORE any exception from the remove
  (including ENOENT when the path was already gone, and EINVAL/EPERM
  when the path is a device node such as `/dev/full` — REQ-010's AC
  states the removal attempt on a device path fails harmlessly). The
  reported error is the run's outcome; the removal is silent cleanup.
  **Single-KI scope (D-53, closes adv-c9 F-01).** The compensated-KI
  outcome is conditional on the failure arm running to completion: a
  SECOND KeyboardInterrupt landing INSIDE the arm — the ordinary
  double-Ctrl-C — interrupts the compensation itself (KI is raisable at
  any bytecode boundary, including inside the arm's `fd.close()` and
  `os.remove`; the arm's `except OSError` clauses catch only OSError),
  so the remove may never run and the partial file SURVIVES the
  interrupted run. That survival is the accepted residue of best-effort
  cleanup — recorded as R-5 (§10.1), the same class as R-1's
  remove-failure residue — NOT an invariant; no site of this spec may
  state the interrupted-run outcome without the single-KI condition. A
  KI-resistant arm (blocking/deferring SIGINT around the compensation)
  is NON-CONFORMING here because the required `signal` import conflicts
  with §9 NFR-001's pinned import set (§4.1/D-52's precedent: an extra
  top-level import has no conforming reading).
  Rationale: a partially written file must never survive as a plausible
  complete JSON document; delete-on-failure is D-33's pinned
  disposition, and the compensation trigger is every exception raised
  after a successful open (see the operation order above; v3's
  OSError-only scoping was the F-01 hole; the "EACCES at open" wording
  is superseded by D-46 — an at-open failure never held the file, so
  the remove does not run and the target survives).
  **Aliasing boundary (D-47, accepted risk R-1b):** the compensation's
  unit of mutation is the opened NAME; the write's unit of mutation is
  the targeted INODE. When the output path is a symlink or hardlink
  alias, open() writes THROUGH the link and the remove unlinks only the
  name — the aliased real/twin file can retain a partial payload while
  the opened name is gone (probe appendix/26b-adv-c5-probes.py P2/P2b).
  This is recorded as accepted-risk R-1b (§10.1), not a contracted
  removal; T-C8's matrix documents the case (assert-or-accept, §8.3).
- **Error paths.** `OSError` at open/write/flush collapses to
  `OutputWriteError` (exit 1 via `main`); a MemoryError in this stage
  propagates to `main`'s residual net and is reported as E-MEM's
  write-phase form (§6.3) — both after the compensation has run, WHICH
  MEANS after a SUCCESSFUL open only (D-46): an at-open failure reports
  directly with NO compensation (target byte-untouched), and a pre-open
  encode failure (D-43) never reaches this stage's wrap at all. There
  is no retry loop, no temp-file rename, no fsync requirement (none is
  pinned by any REQ; flush covers the D-33 surface).
- **Mutation contract (the 13 questions) for this stage** — the only
  state-mutating operation in the tool:

| # | question | answer |
|---|---|---|
| 1 | who may call it | whoever can execute the script and write to the target path (single-user CLI; REQ §2 — no auth layer exists) |
| 2 | input & validation contract | `path: str`, `document: str` ending `]\n`; no path validation beyond what `open()` enforces |
| 3 | where preconditions are enforced | output path is only touched AFTER `parse` returned successfully (REQ-010 phase split, D-15 slot 7); since D-43 the encode step also runs BEFORE the open, so even a MemoryError during encode cannot touch any output path; writability is discovered by `open()` itself; an at-open failure ends the stage with the target untouched (D-46 — no compensation runs because nothing was opened) |
| 4 | where mutation occurs | this stage exclusively: one encode (no side effect), then one `open(path, "wb")`, one write, one flush — the first filesystem-touching call is the open |
| 5 | source of truth | the in-memory `document` string produced by `serialize`; the file is a projection of it |
| 6 | all-or-nothing boundary | one file; the encode-before-open order (D-43) means every pre-open failure — including at-open failures (D-46) — leaves the target byte-untouched; after a successful open, best-effort in-place write with the every-exception delete-on-failure compensation — no cross-file all-or-nothing property is required or provided (single invocation, no concurrent readers in scope) |
| 7 | on retry | re-running the tool re-executes from scratch; a successful rerun overwrites/truncates the target; a failed run left no file — or, on an at-open failure (D-46), left the prior target byte-identical — so retry is clean |
| 8 | on duplicate call | same as retry — the tool has no session; "duplicate" means the user ran it again; last successful run's bytes define the file (REQ §5.1: successful run REPLACES the file entirely) |
| 9 | when two runs overlap in time | out of scope by REQ §2 (single-user, single-invocation); no locking is provided; interleaved runs can lose BOTH outputs — a failed run's compensation can unlink the file name a concurrent successful run wrote, leaving a silent exit-0 run with no file at all — and no ordering property is promised; recorded as an accepted scope boundary, not a promised property (see §10.1 R-2). WITHIN one run, signal-delivered KeyboardInterrupt during the post-open window is IN scope (D-51) with the SINGLE-KI scope of D-53: one KI strikes and the BaseException failure arm runs to completion (close per D-50, remove) before the KI re-raises — an interrupted run leaves no partial target; a SECOND KI landing INSIDE the arm interrupts the compensation and the partial target SURVIVES as accepted residue R-5 (§10.1); a KI raised BY `open()` itself is the D-54 at-open class — no compensation, 0-byte residue R-6 possible (§10.1). The out-of-scope kill forms (SIGKILL, SIGTERM-default) remain ones no handler can observe |
| 10 | state remaining after mid-op failure | pre-open failures (encode MemoryError per D-43; at-open OSError per D-46): target byte-untouched whether absent or pre-existing. Post-open failures: the partial file is removed best-effort for EVERY exception class — on EVERY PLATFORM in the conformance domain, because the failure arm closes the fd before the remove (D-50; without that ordering Windows raises PermissionError on the open handle and a best-effort clause would leave the partial file); if removal itself fails (rare), the error already reported stands and exit is 1 (REQ-010 wording); under an aliased target the R-1b residue (§10.1) is possible. KI-WINDOW states (D-53/D-54): a SECOND KI inside the failure arm aborts the compensation mid-flight — the partial file SURVIVES (accepted residue R-5, §10.1); a KI raised by `open()` itself (fd never bound, D-54) runs no compensation — a pre-existing target may be left 0-BYTE by the kernel's O_TRUNC (accepted residue R-6, §10.1); both are recorded accepted residues of an unprotectable window, not contract failures. SAME-PATH invocation (output path == input path): the post-open compensation's remove can delete the caller's INPUT file (open truncated it, the failed run removes it) — accepted-risk R-4 (§10.1); a successful same-path run replaces the input with the output by S-1's replace semantics |
| 11 | rollback/compensation | exactly D-33's mechanism (best-effort `os.remove`, failures ignored), triggered by every exception raised after a SUCCESSFUL open (F-01 disposition — not OSError-only; at-open failures excluded per D-46); the failure arm's ordering is close-the-fd (best-effort) THEN remove (D-50 — without it the remove fails on Windows while the handle is open and the partial file survives); the compensation is itself best-effort and KI-interruptible (D-53: a second KI inside the arm aborts it mid-flight, leaving R-5's partial-file residue; the KI-at-open class of D-54 never reaches the arm — fd None, no remove, R-6's 0-byte residue possible) |
| 12 | caller/user learning of failure | one `csv2json: error: cannot write <path>: <strerror>` line on stderr for OSError failures (via `main`); MemoryError per §6.3's E-MEM write-phase form `out of memory writing <path>`; exit 1 either way; nothing on stdout (NFR-004) |
| 13 | proving test | §8 contract tests: `/dev/full` write-failure case (open succeeds, flush raises), non-writable-dir case AND pre-existing read-only target case (both at-open failures: E-WRITE, target byte-untouched — D-46; the read-only sub-case skips as root, where DAC_OVERRIDE defeats mode 444 — T-C2's convention), invalid-input/no-file-created case, byte-exact success case, pre-existing-output cases (T-C8: prior bytes survive an encode-phase MemoryError; T-C16: RLIMIT_AS fault injection, no partial output; the `/dev/full` and mid-write cases pin the D-50 close-before-remove failure-arm ordering — a shape that removes while the fd is open is non-conforming (the ordering is why the Windows remove-while-open failure mode cannot occur)); the aliasing case (symlink target) is documented assert-or-accept in T-C8's matrix (R-1b), as are the double-KI residue (R-5) and the KI-at-open 0-byte residue (R-6) — real filesystem, no mocks (infra behavior is never certified mock-only) |

## 4.6 Startup limit raise (NFR-005/D-21/D-27)

- **Purpose.** Make memory, not the csv module's 131072-byte default field
  limit, the binding constraint on field size (probe-verified default;
  REQ NFR-005).
- **Interface.** Module-level statement executed at import, before `main`
  is reached (process-global setting):

```
limit = sys.maxsize
while True:
    try:
        csv.field_size_limit(limit)
        break
    except OverflowError:
        limit >>= 1              # degrade: C-ssize_t binding (D-27)
```

- **Behavior.** Terminates: the limit halves until it fits the
  interpreter's C-integer binding (probe P5: terminates with a limit far
  above 131072). The chosen value is never user-visible; the only
  observable requirement is that huge fields do not trip the default limit.
- **Error paths.** The loop cannot exhaust (limit reaches ≥1 by
  construction; 64 halvings suffice for any C ssize_t). No other failure
  mode exists at this call.

# 5. State & flow

## 5.1 Run-level state machine (states of one process invocation)

States are ordered by the D-15 validation sequence; every failure jump goes
to the single REPORTING state, then exits 1. There is no retry, no
interactive state, no daemon state: the process is linear.

```
START
  │ argv length != 2 ──────────────────────────────► REPORTING(usage) ─► exit 1
  ▼ ARGV_OK
READ_INPUT ── OSError ────────────────────────────► REPORTING(read) ───► exit 1
  ▼ INPUT_READ
DECODE ── UnicodeDecodeError ─────────────────────► REPORTING(utf8) ───► exit 1
  ▼ DECODED (BOM stripped)
PARSE ══ per-record loop (5.2) ═══════════════════► REPORTING(field) ──► exit 1
  ▼ PARSED (all records valid; rows built)
SERIALIZE ── MemoryError ─────────────────────────► REPORTING(memory) ─► exit 1
  ▼ SERIALIZED
WRITE_OUTPUT ── OSError(after compensation iff open succeeded)► REPORTING(write) ──► exit 1
WRITE_OUTPUT ── MemoryError(pre-open encode: nothing open — filesystem untouched) ──► REPORTING(memory) ─► exit 1
WRITE_OUTPUT ── MemoryError(post-open: after compensation) ──► REPORTING(memory) ─► exit 1
  (at-open OSError edge: NO compensation — reports directly, D-46; the
  failure-position contract lives in §4.5, which this diagram summarizes)
  ▼ WRITTEN
exit 0  (stdout silent)
```

REPORTING prints exactly one stderr line and nothing else. The output file
can exist only after WRITTEN; every path into REPORTING leaves the
filesystem untouched on the output side (§4.5's compensation is the one
cleanup).

## 5.2 Parse-loop micro-states (inside PARSE)

`AWAITING_HEADER` → on first record: header rules FIRST (0-field check →
duplicate check — D-15 slots (4)/(5), §4.3.2's pinned order) →
`HEADER_VALIDATED` → then the record's FSM quote scan (slot (6), scope
covers the header per D-25; on a combined defect the duplicate error wins,
S-9b) → `IN_DATA` → per record: FSM scan → count check → row appended.
`IN_DATA` until StopIteration → `PARSE_OK`.
Any check failure raises straight out of PARSE (REPORTING(field)).
The FSM's own four states (FIELD_START/UNQUOTED/QUOTED/CLOSED, §4.3.3) are
re-created per record and never leak across records.

## 5.3 Scenario walk-throughs (every REQ-identified scenario, with failure paths)

Steps cite stages (S1 read_raw, S2 decode_utf8, S3 parse, S4 serialize,
S5 write_output); "→msg" gives the exact stderr line; "exit" gives the code.

**S-1 Happy path** (REQ-001/002/003/005; REQ §1 success condition).
`python csv2json.py in.csv out.json`, in.csv = `id,name\n1,x\n2,y\n`:
argv ok → S1 reads bytes → S2 decodes (no BOM) → S3: record 1
`id,name` — header rules run first (no 0-field, no duplicates; the
quote scan then finds no unterminated quote); records 2–3
pass FSM, counts match, rows built → S4 emits
`[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n` → S5 writes 46 bytes →
exit 0, stdout empty, out.json created/replaced. (Same-path note: with
`csv2json.py data.csv data.json` replaced by `csv2json.py data.csv
data.csv`, the success semantics are identical — the input is replaced
by the output; the FAILED-run same-path case is accepted-risk R-4, §10.1.)

**S-2 Usage error** (REQ-001/D-34). zero/one/three args: →msg
`csv2json: error: usage: csv2json.py <input.csv> <output.json>`, exit 1,
no file touched (S1 never runs).

**S-3 Input unreadable** (D-15 slot 2). in.csv missing / no permission:
S1 raises OSError → `csv2json: error: cannot read in.csv: No such file or
directory` (strerror verbatim), exit 1, no output file.

**S-4 Invalid UTF-8** (REQ-011/D-13/D-23/D-28). in.csv = `a,b\rc,d\rc\r\xff`:
S2 raises at byte offset 10 (the 0xFF) → prefix decodes `a,b\rc,d\rc\r` →
D-28 count → 4 → msg `csv2json: error: in.csv line 4: byte 0xff is not
valid UTF-8`, exit 1, no output file. (CR-only counting per D-28: each
`\r` ends a physical line; an LF-only counter would wrongly say line 1.)
Failure path note: output path is never opened — REQ-010's no-output-on-
error holds structurally.

**S-5 BOM handling** (REQ-012/D-16/D-31). (a) BOM + `id,name\n1,x\n`: S2
strips U+FEFF after decode; flow continues as S-1; output byte-identical
to the no-BOM file. (b) BOM only (3 bytes): decode succeeds, strip leaves
`""` → S3 yields no record → `csv2json: error: in.csv: file is empty (no
header row)`, exit 1, no output file (empty-file class, NOT the line-1
invalid-header class).

**S-6 Empty / header-less inputs** (REQ-009). (a) zero-byte file: as S-5(b)
minus the strip — same empty-file message, exit 1. (b) file of only blank
lines `\n\n`: S3 first record is `[]` (0-field) →
`csv2json: error: in.csv line 1: invalid header row (found 0 fields)`,
exit 1. (c) blank line before data in a 1-column file `a\n\n1\n`: first
record `['a']` is the header; record 2 `[]` → count error →
`csv2json: error: in.csv line 2: expected 1 fields, found 0`, exit 1.
(d) trailing blank line `a,b,c\n1,2,3\n\n`: fails at line 3
(`expected 3 fields, found 0`) — exactly ONE trailing terminator would
have been fine; the second is a 0-field row. (e) whitespace-only middle
line `a\n  \n1\n`: NOT blank (D-36) → 1-field data rows convert →
`[{"a":"  "},{"a":"1"}]`, exit 0.

**S-7 Duplicate header names** (REQ-002/D-12). (a) `id,name,id\n...`:
first record's duplicate scan trips on the third field →
`csv2json: error: in.csv line 1: duplicate header name 'id'`, exit 1, no
output file. (b) empty-name duplicate `a,,b,\n...`: message cites `''`
(the second empty name). (c) single empty name `a,,b\n1,2,3\n`: converts
verbatim → `[{"a":"1","":"2","b":"3"}]`, exit 0 (F-33).

**S-8 Quoted fields** (REQ-004, §3.1 dialect). (a) `"a,b",c` → fields
`a,b`,`c`. (b) `"say ""hi"""` → `say "hi"`. (c) quoted field spanning two
physical lines parses as one field of one record. (d) `"x\r\ny"` → value
`x\r\ny` byte-exact (CRLF NOT rewritten to LF — the universal-newline
rewrite is a non-conforming implementation); `"x\ry"` keeps its bare CR
(D-24 handoff; probe P8 CRLF-in-quoted-field case reproduces the exact
output bytes `[{"h":"x\r\ny","k":"2"}]` for `h,k\n"x\r\ny",2\n`).

**S-9 Unterminated quote — data row** (REQ-013/D-19/D-25/D-30). (a)
`id,name\n"1,2` (file ends with the section open): record 2's FSM scan
ends in QUOTED → `csv2json: error: in.csv line 2: unterminated quoted
field (opened at line 2)`, exit 1, no output file. (b) 1-column
`a\n"1`: lenient parse would give a count-valid row — must still error
with the same message shape at line 2. (c) header-line form `"id,name`
(single line, file ends): header rules run FIRST (§4.3.2 order) and
pass (one field, no duplicate) — then the FIRST record's FSM scan
trips → `... line 1: unterminated quoted field (opened at line 1)` —
never the `[]`/exit-0 lenient outcome (D-25; scope covers the header,
order defers the scan to after the header rules).

**S-9b Combined header defects — duplicate beats quote** (SR1-F-02 AC,
D-15 slots (5)<(6)). `id,"id` (one physical line, no trailing newline):
the header record carries BOTH a duplicate name pair (`id`,`id` — the
lenient dialect closes the record with fields `id`,`id`) AND an
unclosed quote opened at field 2. Per the pinned order, the duplicate
scan (slot 5) runs before the quote scan (slot 6) →
`csv2json: error: in.csv line 1: duplicate header name 'id'`, exit 1,
no output file — never the quote error. The quote defect is not lost:
any header WITHOUT the duplicate (`"id,name`, S-9(c)) still reports
E-UQ at line 1.

**S-10 Unterminated quote — N ≠ M** (REQ-013/D-30; LF interior form).
`h1,h2\n"a\nb",c,"d\ne`
(one record starting at physical line 2, whose third field's opening
quote sits on line 3 and never closes): record 2's FSM scan ends QUOTED
with record-relative opening line 2 → N=2, M=3 →
`csv2json: error: in.csv line 2: unterminated quoted field (opened at
line 3)`, exit 1, no output file. (b) CRLF-interior form
`h1,h2\n"a\r\nb",c,"d\ne` — identical structure, but the record's
interior terminator is CRLF: per the §4.3.3 counting rule CRLF is ONE
advance (never two), so the opening quote is again on record-relative
line 2 → N=2, M=3, exact same message, exit 1. (The pre-fix per-char
count produced M=4 — a physical line the 3-line file does not even
have; T-U3's CRLF-interior case and T-C7's E2E case pin the M=3
outcome.) (c) bare-CR interior form `h1,h2\n"a\rb",c,"d\ne` — one CR
inside the first quoted field: also ONE advance → N=2, M=3.

**S-11 Error ordering within PARSE** (D-29/D-15; REQ-013 scope-not-prepass).
`id,name\n1\n"2,3`: record 2 is count-bad (`found 1`) and record 3
contains the unterminated quote; the sequential loop reaches record 2
first → `csv2json: error: in.csv line 2: expected 2 fields, found 1` —
the count error at the earlier row wins; the quote error never fires.
The unterminated-quote check is per-record scope covering the whole
input (header included), never a separate whole-input pre-pass.

**S-12 Quote in an unquoted field is data** (D-30 negative AC).
`desc,qty\n5" ruler,2\n`: record 2's FSM: `"` arrives in UNQUOTED →
data; no error → `[{"desc":"5\" ruler","qty":"2"}]`, exit 0. A build
that rejects it as "unterminated" is NON-CONFORMING. Likewise `"a"b`
(post-close junk → data) and `"a""b"` (doubled-quote escape) never
false-positive the FSM (probe P3).

**S-13 Lossless values** (REQ-005/D-11/Q-01). `42,3.14,true,` →
`"42"`,`"3.14"`,`"true"`,`""` (never null); `007,` → `"007"`,`""`;
leading zeros, numeric-looking and boolean-looking text keep their
string type; `<script>`-style content is inert data (NFR-005); NUL/FF/VT
in cells are data, escaped per D-14/D-20 (`\u0000`, `\f`, `\u000b`).

**S-14 Write-phase failure** (REQ-010/D-33/D-43; serialize-phase MemoryError per D-44). Valid input; output
target `/dev/full` (or a file on a full disk): S5's encode completes
first (untouched), open succeeds, write/flush raises OSError(ENOSPC) →
compensation runs first (best-effort os.remove; on a device path it
fails harmlessly and is ignored) →
`csv2json: error: cannot write /dev/full: No space left on device` on
stderr, exit 1 — never a traceback, never a silent success, no leftover
partial file on a REGULAR filesystem. (b) open() itself raises (EACCES):
two target states, ONE outcome shape — same message form (with that
strerror), exit 1, and the target is left byte-identical in both
(D-46: the compensation never runs because no open ever succeeded):
(b1) absent target in a non-writable directory → nothing was created,
no file exists afterward (the v5 "harmless no-op" description, which
was accurate only for this absent-path form, is superseded by D-46's
no-remove rule); (b2) pre-existing READ-ONLY target in a WRITABLE
directory (probe appendix/28-rev6-writegate-probes.py R6-P2) → the
user's prior good output SURVIVES byte-identical — the v5 wide-scope
wording, under which the compensation's os.remove deleted that file
(adv-c5 probe P10 destruction), is non-conforming since v6. (c) output
path is an existing file: a successful run replaces
it entirely (REQ §5.1); an error before S5 leaves it byte-untouched
(REQ-008/010: "absent or unchanged"). (d) pre-existing output + MemoryError
at S5's encode (fault-injected per §8.4; appendix/22 W-series): the
encode raises BEFORE the open (D-43) → the prior good file survives
byte-identical, no file is created, stderr carries E-MEM's
`out of memory writing <out>` form, exit 1. (e) MemoryError striking
AFTER the open (mid-write): the compensation is NOT scoped to OSError —
the partial file is removed, then E-MEM's write-phase form is reported,
exit 1 (this sentence states the arm-runs-to-completion form; the
D-53/R-5 arm-abort class — second KI or second MemoryError inside the
arm — leaves the partial file in place, as spelled out below); under (e) a PRE-EXISTING output does not survive as such: the
open truncated it and the D-33 compensation then removed it — the file
is GONE after the failed run (by design, D-46's trigger; UNLESS the
compensation itself is aborted mid-flight per D-53/R-5 — a second KI
or a second MemoryError landing inside the failure arm — in which case
the partial file SURVIVES as the recorded residue, decision D-56(a),
adv-c10 F-01; live probe
appendix/30b-adv-c6-reaim-probes.py P2, re-aimed per SR7-F-03; historical:
appendix/29b P2), whereas under (d) it survives byte-identical (probe
appendix/30b P2b; historical: appendix/29b P2b) — the T-C16 assertions
follow the observed phase form
(§8.3); in both (d) and (e) a pre-existing output is never left
truncated (probe W1/W2 evidence class, appendix/21b + 22); if the
output path is an ALIAS (symlink/hardlink), the R-1b residue (§10.1)
applies — the opened name is removed but the aliased file may retain
the partial bytes; if input path == output path, R-4 (§10.1) applies —
a failed post-open run can delete the caller's input.

**S-15 CR-only and mixed terminators** (REQ-014/§3.1). (a) `a,b\rc,d\r`
→ two records → `[{"a":"c","b":"d"}]`, exit 0 (the plain-StringIO
construction would instead crash with an unclassified `_csv.Error` —
the reason D-24 exists). (b) `a\nb\rc\n` → mixed LF/CR/LF: three
records, exit 0. (c) `h,k\n"x\ry",2\r` → `h` = `x\ry`, exit 0.

**S-16 Pathological sizes** (NFR-005/D-21/D-27). A 10 MB single field,
or a 10 MB row spread across fields: startup limit-raise makes memory
the only bound → converts (within the NFR-003 envelope) or fails per
the generic memory contract; the 131072-byte default limit never trips.
`",,,,"`-style oddities behave per the dialect; nothing executes or
interpolates input content.

# 6. Interface contracts

The tool has no network/API surface: the contracts are the CLI invocation,
the output document, and the error messages. All three are pinned here in
full; §8 maps each to its verification.

## 6.1 CLI invocation contract (REQ-001/D-34)

| aspect | contract |
|---|---|
| form | `python csv2json.py <input.csv> <output.json>` — exactly two positional args, input first, output second; the output path is used exactly as given — no type check is performed (D-55: a character-device or other non-regular openable target such as `/dev/stdout` is opened, written, flushed, closed like any other path, and the document appears on that device) |
| arg count ≠ 2 | stderr `csv2json: error: usage: csv2json.py <input.csv> <output.json>`; exit 1; no file created |
| exit codes | 0 on success; 1 on EVERY failure (usage, read, decode, parse, write, memory, residual) — two-valued, no exit 2 anywhere |
| stdout | empty on success; empty on failure (errors go to stderr) — the success row scopes to REGULAR-FILE output paths (D-55: with output `/dev/stdout` the DOCUMENT is written to that device by the caller's own redirection choice, exit 0; the tool itself performs no stdout write on any path) |
| stderr | empty on success — FOR REGULAR-FILE output paths; with a character-device output (`/dev/stderr` etc.) the DOCUMENT itself lands on that device at exit 0 (D-55, the caller's own redirection — the success-side statements in §6.4/§9/T-K3 carry the same scope); on a regular-file run it is exactly one error message per failed run — the tool adds no newline beyond the message's terminating one and emits no second message; data-borne breaks inside ANY interpolated slot (E-DUP `<name>`, E-NET `<exception repr>`, OS `<strerror>`) may wrap it across physical lines (§4.1 F-03 note, §6.3) |
| flags/options | NONE accepted. `-h`/`--help` are out of scope (REQ §3.2: no named options); as positionals they are ORDINARY PATH STRINGS — the manual dispatch's outcome is normative for ALL argv of length 2: E-READ on `-h out.json`, exit 1, nothing on stdout (D-49). On argc ≠ 2 (e.g. `csv2json.py -h` alone) the usage branch reports the prefixed usage line on stderr with exit 1 — help text NEVER reaches stdout on any argv (NFR-004; the manual dispatch is the ONE conforming shape, D-52 — an argparse build's default help action prints help to stdout and exits 0, which is non-conforming on this argv class too; adv-c6 F-05, adv-c8 F-02) |
| environment | no env vars read; locale-independent (decode/encode are explicit UTF-8; no `open()` default-encoding dependency anywhere) |

## 6.2 Output document contract (§5.2 REQ, D-11b/D-17/D-20/D-26/D-35)

Byte-level, machine-checkable:

1. One line: `json.dumps(rows, ensure_ascii=False, separators=(",", ":"))`
   followed by exactly one `\n`.
2. The file's last two bytes are `]` `0x0A` on every platform (binary-mode
   write; `]\r\n` is non-conforming).
3. UTF-8, no BOM. Non-ASCII data appears as raw UTF-8 (Thai
   `ประเทศไทย` is those characters' UTF-8 bytes, not `\u0e1b...` escapes).
4. Escape forms: `\f \b \n \r \t \" \\` short forms; `\u00xx` lowercase
   for control characters without short forms (NUL `\u0000`, VT
   `\u000b`); DEL 0x7F, U+2028, U+2029 raw.
5. Structure: one JSON array; one flat object per data row in input row
   order; keys = header names verbatim in header order; every value is a
   JSON string (never number/bool/null; empty cell → `""`).
6. Header-only input produces exactly `[]\n` (3 bytes).

## 6.3 Error message contract (REQ-007/D-22; message catalog)

Shape: (a) prefix `csv2json: error:` on ALL classes without exception;
(b) input file named / output path named per class; (c) 1-based D-28
physical line where the row starts; (d) expected vs actual counts where
meaningful. Catalog (the complete set — a build emitting a message outside
this catalog is non-conforming):

| id | trigger (D-15 slot) | exact message template | (b)(c)(d) |
|---|---|---|---|
| E-USAGE | (1) argc ≠ 2 | `csv2json: error: usage: csv2json.py <input.csv> <output.json>` | (b)-(d) N/A |
| E-READ | (2) input OSError | `csv2json: error: cannot read <in>: <strerror>` | (b) input; (c)(d) N/A |
| E-UTF8 | (3) invalid byte | `csv2json: error: <in> line <N>: byte 0x<hh> is not valid UTF-8` | (b)(c); (d) N/A |
| E-EMPTY | (4) no records after BOM strip | `csv2json: error: <in>: file is empty (no header row)` | (b) input; (c)(d) N/A |
| E-HEADER0 | (4) first record 0 fields | `csv2json: error: <in> line 1: invalid header row (found 0 fields)` | (b)(c); (d) found=0, expected N/A |
| E-DUP | (5) duplicate header name | `csv2json: error: <in> line 1: duplicate header name '<name>'` | (b)(c); counts N/A |
| E-COUNT | (6) data row count ≠ header | `csv2json: error: <in> line <N>: expected <H> fields, found <F>` | (b)(c)(d) |
| E-UQ | (6) unterminated quoted field | `csv2json: error: <in> line <N>: unterminated quoted field (opened at line <M>)` | (b)(c) two line numbers |
| E-WRITE | (7) output OSError | `csv2json: error: cannot write <out>: <strerror>` (at-open failures report the same shape; per D-46 no compensation runs at open — the target is left byte-untouched) | (b) output path; (c)(d) N/A |
| E-MEM | any phase, MemoryError | read phase: `csv2json: error: out of memory reading <in>`; parse phase: `csv2json: error: out of memory while converting <in>`; serialize/write phases: `csv2json: error: out of memory writing <out>` (NFR-005: a MemoryError during the output write/serialize is reported like any other write-time failure — the OUTPUT path named, D-33/D-44: serialize and write therefore share the ONE output-named form; there is no input-named serialize form. Write-phase placement per D-43: the encode runs BEFORE the open, so a MemoryError at encode touches no output path; a MemoryError after the open first triggers the D-33 compensation, so no partial file survives — §4.5 — UNLESS the compensation itself is aborted per D-53/R-5: a second MemoryError (or second KI) landing inside the failure arm aborts the best-effort remove mid-flight and the partial file PRESENT is the recorded residue (decision D-56(a), adv-c10 F-01; probe appendix/47 P1a — partial PRESENT with this phase form on stderr; control P1b — single MemoryError, file removed). Serialize phase per D-44: nothing is open yet, so the filesystem is simply untouched — no compensation applies) | (b) per-phase; (c)(d) N/A |
| E-NET | residual unexpected exception | `csv2json: error: <in>: internal error: <exception repr>` | (b); (c)(d) N/A |

E-NET is the catch-all net for genuinely unforeseen exceptions; it
deliberately does NOT swallow or disguise any cataloged class (each has its
own id above — retry/recovery distinctions are per-class, never erased by
the net). `strerror` is the OS's message text verbatim (e.g. `No space
left on device`), satisfying REQ-010's example shape.

E-DUP `<name>` note (F-03, generalized per SR3-F-05): the duplicate name
is interpolated VERBATIM per D-12 — no escaping, no sanitization (an
empty name yields `''`, per F-33); this verbatim discipline applies to
EVERY interpolated-data slot in the catalog: E-DUP's `<name>`, E-NET's
`<exception repr>` (an exception repr may legally contain a raw newline —
live-verified as reachable via a custom `__repr__` override; a plain
Exception's repr escapes the newline — appendix/25 M1, the original
cycle-5 demonstration, is HISTORICAL: it refuses to run on the archived
spec/06 path since the rollover (SR7-F-03 annotation); the subject matter
is re-proven live by appendix/22's E-DUP name-form matrix and
appendix/30b P4),
and the OS `<strerror>` in E-READ/E-WRITE — AND every template's `<path>`
slot (closes adv-c8 F-04): E-READ/E-UTF8/E-EMPTY/E-HEADER0/E-DUP
interpolate `<in>` verbatim, E-COUNT/E-UQ interpolate `<in>` (inside
`... <in> line <N>`), E-WRITE and E-MEM's write-phase form interpolate
`<out>` — the path string comes from argv (caller-controlled data) and
may legally contain a raw newline (POSIX forbids only the NUL byte and
the path separator), so a template whose `<path>` is such a name wraps
across physical lines exactly like the E-DUP newline-name case below;
escaping or sanitizing the path in any catalog message is NON-CONFORMING.
E-NET's `<in>` slot is covered by the same rule (closes adv-c9 F-05):
the template `csv2json: error: <in>: internal error: <exception repr>`
interpolates `<in>` verbatim like every other `<in>` slot, so an
E-NET message with a newline-bearing INPUT path wraps across physical
lines exactly like the enumerated cases.
**Encoding scope of the verbatim rule (closes adv-c9 F-04).** The
verbatim discipline above binds the MESSAGE STRING the tool hands to
its single stderr write — the tool's formatting layer never escapes or
sanitizes any slot. The BYTES observed on the wire additionally depend
on the interpreter's stderr encoding, which is environment-controlled
(`PYTHONIOENCODING`, locale), not tool-controlled: on default CPython
stderr the Thai-name E-DUP message reaches the wire as verbatim UTF-8
under C and UTF-8 locales alike (probe appendix/39b P4 UTF-8 and
C-locale controls), but an overridden encoding such as
`PYTHONIOENCODING=ascii:backslashreplace` transliterates the message
inside the print call itself (probe appendix/39b P4
pyioencoding-ascii FAIL is this F-04's evidence), and a strict handler
(`PYTHONIOENCODING=ascii`) makes the write itself raise inside
`main`'s handler — that failure path is QC-1's residual
nonzero-exit-with-no-catalog-line path (R-3's closed-stream class).
The tool pins no stderr encoding and adds no reconfiguration; a
tester asserting the verbatim byte form under a non-default stderr
encoding is testing the environment, not the tool.
A header field may legally
contain a raw newline (quoted
multi-line field, REQ-004), so the message text itself may contain a
line break: `csv2json: error: in.csv line 1: duplicate header name
'a\nb'` is the conforming output for input `"a\nb","a\nb"` — one
message, one stderr write, physically wrapping across two lines (see
the §4.1 one-line scoping). A build that escapes the name (e.g. `\n`
→ `\\n`) or that suppresses the message is NON-CONFORMING.

## 6.4 Exit-code and channel matrix

| class | exit | stdout | stderr |
|---|---|---|---|
| success | 0 | empty — scope: REGULAR-FILE output paths (D-55: with a character-device output such as `/dev/stdout` the DOCUMENT is written to that device by the caller's own redirection choice; the tool still performs no stdout/stderr write of its own) | empty — same regular-file scope (D-55) |
| E-USAGE/E-READ/E-UTF8/E-EMPTY/E-HEADER0/E-DUP/E-COUNT/E-UQ | 1 | empty | one catalog message (one stderr write; data-borne breaks inside `<name>` may wrap it physically — §6.3 E-DUP note; the verbatim rule binds the MESSAGE STRING handed to that write — wire bytes additionally depend on the interpreter's stderr encoding, §6.3 E-DUP note's encoding scope) |
| E-WRITE (incl. mid-write) | 1 | empty | one catalog message (output path named) |
| E-MEM / E-NET | 1 | empty | one catalog message |

Signal-delivered interrupts (KeyboardInterrupt from SIGINT) are OUTSIDE
this matrix's two-valued contract: they are not tool-reported errors, and
a run interrupted that way exits with the shell's signal convention (130;
subprocess-observed as a negative returncode) with whatever stderr state
the interrupting moment left — REQ-007's "no unhandled traceback" wording
governs the tool's OWN reporting paths, not the interpreter's
Ctrl-C behavior. What IS contracted is the on-disk OUTPUT state of such a
run, under the single-KI scope of D-53: ONE KeyboardInterrupt striking
after a successful open runs the §4.5 failure arm before re-raising
(D-51; probe appendix/36 P1), so a single-Ctrl-C interrupted run never
leaves a plausible-complete partial document on disk. Beyond that single
KI the outcome is recorded residue, not contract: a SECOND Ctrl-C landing
inside the failure arm aborts the compensation mid-flight and the partial
file SURVIVES (accepted residue R-5, §10.1), and a Ctrl-C striking DURING
the `open()` call itself is the D-54 at-open class — no compensation
runs, and a pre-existing target may be left truncated to 0 bytes
(accepted residue R-6, §10.1).

# 7. Error & recovery contract

## 7.1 Per-class contract (all cataloged errors)

"Layer" is the stage that raises (S1..S5 per §2.1); "propagation" names the
typed path to `main`'s single handler; "side effects" is the state the run
leaves behind (the output file is the only mutable state in the tool).
Every row's "verification" cites the §8 test id.

| id | layer | trigger | propagation | side effects | retryable? | recovery action | caller-visible | user-visible | verification |
|---|---|---|---|---|---|---|---|---|---|
| E-USAGE | shell (§4.1) | argc ≠ 2 | none — inline branch | none (no file touched) | yes — rerun with 2 args | user supplies exactly two args | exit 1 + stderr line | same line | T-C1 |
| E-READ | S1 | OSError on open/read of input | `InputReadError` → main | none | yes once the file is readable | fix path/permissions; no cleanup needed | exit 1 + stderr line | same line | T-C2 |
| E-UTF8 | S2 | `UnicodeDecodeError` on strict decode | `InvalidUtf8Error` → main | none | no (deterministic on this input) | user converts/fixes the file's encoding | exit 1 + stderr line (file+line cited) | same line | T-C3 |
| E-EMPTY | S3 | no record after BOM strip | `FieldError` → main | none | no (input property) | supply a file with a header row | exit 1 + stderr line | same line | T-C4 |
| E-HEADER0 | S3 | first record 0-field | `FieldError` → main | none | no | file must start with a real header | exit 1 + stderr line | same line | T-C4 |
| E-DUP | S3 | duplicate header name (2nd occurrence, incl. empty name) | `FieldError` → main | none | no | de-duplicate the header | exit 1 + stderr line | same line | T-C5 |
| E-COUNT | S3 | data row count ≠ header (incl. blank-line 0-field rows) | `FieldError` → main | none | no (fail-fast, first row only) | fix the row at the cited line | exit 1 + stderr line | same line | T-C6 |
| E-UQ | S3 | record's quoted section unclosed at end of input (header row included) | `FieldError` → main | none | no | close the quote / repair truncation at the cited lines | exit 1 + stderr line (N and M) | same line | T-C7 |
| E-WRITE | S5 | OSError at open/write/flush of output (EACCES/ENOSPC/EIO/EDQUOT) | compensation runs only if the open SUCCEEDED (D-46), then `OutputWriteError` → main; an at-open failure reports directly, no compensation | post-open failures: partial file removed best-effort (device-path removal failure ignored); at-open failures: no compensation, every output target byte-untouched (D-46); pre-open encode failures (D-43) likewise leave every output target byte-untouched | yes — after freeing space/fixing permissions; rerun is clean | user fixes the target (space, permissions, path); the tool's own compensation (delete partial) is automatic for post-open failures | exit 1 + stderr line (output path named) | same line | T-C8 |
| E-MEM | S1–S5 | MemoryError (file/payload genuinely too large for available RAM) | residual net → main | read/parse phases: none. Serialize phase: none (nothing open yet — D-44, filesystem untouched). Write phase: pre-open (encode, D-43) — every output target byte-untouched; post-open (mid-write) — the D-33 compensation removes the partial file (compensation trigger is every exception raised after a SUCCESSFUL open, §4.5/D-46), removal failure ignored; the D-53 arm-abort scope applies — a second MemoryError (or second KI) landing inside the failure arm aborts the remove mid-flight and the partial file SURVIVES as the recorded residue R-5 (§10.1; decision D-56(a), adv-c10 F-01) | only with more RAM/smaller input | reduce input size; tool reports per contract | exit 1 + stderr line (phase form: reading/while converting/writing — serialize and write share the output-named form, D-44; §6.3) | same line | T-C16 (child process under a low RLIMIT_AS → E-MEM line, exit 1, no partial output outside the D-53/R-5 arm-abort residue — a second MemoryError inside the failure arm leaves it, D-56(a); pre-existing-output case asserts per the OBSERVED phase form: bytes survive for a pre-open form, path absent for the write-phase form — §8.3/D-46; fault-injection method per §8.4) |
| E-NET | any | unexpected exception (no cataloged class fits) | residual net → main | none before S5; a post-open S5 hit (open succeeded) runs the D-33 compensation first (§4.5/D-46), then reports | n/a — signals a bug | file a defect; the tool still honors exit+prefix+no-traceback | exit 1 + stderr line | same line | T-C10 (fault-injection) |

Taxonomy coverage: validation (E-COUNT, E-DUP, E-HEADER0, E-EMPTY, E-UQ —
all input-shape validation), stale reference (N/A — the tool holds no
references across calls; every run re-opens both paths, so a deleted input
surfaces as E-READ and a vanished output directory as E-WRITE), invalid
state or transition (N/A — the process state machine §5.1 is linear with
no re-entry), permission (E-READ/E-WRITE EACCES forms), dependency
unavailable (N/A — stdlib-only, no external services; the OS is the only
dependency and its absence is not a runtime state), read-write failure
(E-READ, E-WRITE), partial failure (E-WRITE's mid-write form with the
delete-on-failure compensation, and the write-phase E-MEM forms which
share that compensation — after D-43 the encode runs pre-open, and per
D-46 an at-open failure never triggers the compensation, so the
boundaries BEFORE the open cannot truncate or delete a pre-existing
target; a failure AFTER a successful open (mid-write, at flush, or a
post-open MemoryError) both truncates (the open's O_TRUNC) and then
REMOVES a pre-existing target by design — the D-33 compensation — so a
pre-existing target survives a failed run IFF the failure struck before
the open, with the two recorded signal-window exceptions (adv-c6 F-01
correction of the v6 over-broad sentence; D-53/D-54 scope it further):
a SECOND KI — or a second MemoryError, any non-OSError — inside the
failure arm leaves the partial file (R-5; the arm-abort class is not
KI-specific, D-56(a)/adv-c10 F-01), and a
KI striking the `open()` call itself can leave a pre-existing target
truncated to 0 bytes (R-6; the same window also has a create flavor —
an absent target left CREATED at 0 bytes, D-56(b)/adv-c10 F-04) — both accepted residues (§10.1), the only
conforming-build states outside the before-open rule,
timeout-cancellation (no timeouts
exist in the tool; the contract splits by kill form, D-51 with the
single-KI scope of D-53: a SIGINT-delivered KeyboardInterrupt (the
user's Ctrl-C) striking AFTER a successful open runs the §4.5
BaseException failure arm first — close per D-50, best-effort remove,
re-raise — so a single-Ctrl-C interrupted mid-write run leaves NO
partial output file, then exits outside the §6.4 matrix (signal exit
130, outside REQ-007's own-reporting scope — the §6.4 signal note);
this window is contracted, tested as T-C8's KI sub-case, NOT an
accepted boundary, but ONLY for the single-KI form: a SECOND Ctrl-C
inside the failure arm aborts the compensation mid-flight and leaves
the partial file (accepted residue R-5, §10.1), and a Ctrl-C striking
the `open()` call itself is the D-54 at-open class — no compensation,
a pre-existing target may be left 0-byte (accepted residue R-6,
§10.1). Only UNCATALOGED kills — SIGKILL, or SIGTERM under its default
disposition — leave whatever partial output existed at kill time; that
residue is outside the tool's contract (no handler can run) and is
recorded as an accepted scope boundary), resource exhaustion (E-MEM; disk-exhaustion
is E-WRITE/ENOSPC), schema-version mismatch (N/A — no persisted schema
anywhere: input/output formats are version-free by design), corrupt
persisted state (N/A — the tool persists nothing; it reads user data and
replaces the output wholesale on success), init failure (N/A — §4.6's
startup raise cannot fail; Python-interpreter absence is not a tool
state), unrecoverable (E-NET residual bug form — reported, never
silent, exit 1).

## 7.2 Fail-fast and first-error-wins invariants

- Exactly one error is ever reported per run: the first in D-15 slot order
  (§5.1), and within slot (6), the first failing check of the earliest
  failing record (D-29). Probe P8 "count error wins over later quote" pins
  the ordering case the requirements call out.
- A failed run's output-side footprint: no file (error before S5), or the
  target removed (error in S5) — UNLESS the compensation itself is aborted
  mid-flight per D-53/R-5 (a second KI or a second MemoryError inside the
  failure arm), in which case the partial target survives as the recorded
  residue — or the target harmlessly untouched
  (device/permission cases where removal is impossible — the error message
  is then the run's entire effect). One more recorded exception to "no
  file": a KI striking the `open()` call itself on an ABSENT target can
  leave a CREATED 0-byte file (the kernel applied O_CREAT before the signal
  struck; the arm sees `fd is None` and runs no compensation) — the
  create flavor of R-6 (§10.1, decision D-56(b), adv-c10 F-04).
- REQ-008's "output file absent or unchanged" is enforced structurally:
  S5 is unreachable until S3 has accepted every record.

## 7.3 Residual-exception net

`main`'s handler is `except MemoryError` (E-MEM) first, then
`except ToolError` (the typed hierarchy), then a final `except Exception`
(E-NET). Order matters: MemoryError derives from Exception, so a bare net
ahead of it would swallow the memory class into E-NET and erase the
catalog distinction. The net formats E-NET with the exception repr so
a defect is diagnosable from the stderr line alone; it never re-raises,
never prints a traceback (REQ-007: no exception ever escapes as an
unhandled traceback), and always returns 1. `SystemExit`/`KeyboardInterrupt`
are NOT caught by `main`'s handler chain (process-level signals pass
through it to the interpreter). This main-level pass-through does NOT
suspend the write stage's own compensation (D-51): a KeyboardInterrupt
raised inside the §4.5 try has already run the failure arm — fd closed per
D-50, partial removed best-effort — before the KI propagates past `main`,
so an interrupted run leaves no partial target — ALWAYS under the
single-KI scope of D-53: that outcome holds for ONE KI whose failure arm
runs to completion (probe appendix/36 P1; the except-Exception variant is
NON-CONFORMING, probe appendix/36 P2). A SECOND KI landing inside the arm
interrupts the compensation mid-flight and the partial file survives
(accepted residue R-5, §10.1), and a KI raised by the `open()` call
itself never reaches the arm at all — fd None, no compensation, the
D-54 at-open class with R-6's possible 0-byte residue (§10.1).

# 8. Acceptance-test outline

Layer rule (SOUL): pure domain rule → unit test at `parse`/`serialize`/
`line_of_offset`; interface/schema compat → contract test on the output
bytes and message catalog; persistence/transaction → adapter integration
test against the real filesystem (never mock the filesystem inside the
unit under test; infra behavior is never certified with the infrastructure
mocked out); concurrent clients → N/A (single-invocation CLI, §4.5 row 9);
restart/recovery/migration → N/A (no persistent state — process lifetime
only); authorization boundary → N/A (no auth layer, REQ §2); critical
journey → E2E through `main(sys.argv)` (the one external seam). Every REQ
AC cited in the requirements is enumerated in §10 with its T-id.

## 8.1 Unit layer (pure functions; no I/O)

| T-id | verifies | input → expected | REQ/D |
|---|---|---|---|
| T-U1 | `line_of_offset` D-28 basis | the P2 case table (terminator trio; VT/FF/NEL/U+2028/U+2029 data; CRLF one break) | D-28 |
| T-U2 | per-record span extraction | P1 case table (slices exact incl. unterminated-last record) | §4.3.2 |
| T-U3 | unterminated-quote FSM | P3 case table (all REQ-013 shapes; `5" ruler` data; doubled quotes; post-close junk); PLUS the CRLF-interior case `h1,h2\n"a\r\nb",c,"d\ne` → unterminated, record-relative opening line 2 (CRLF = one advance, appendix/20 R2) and the bare-CR interior form → same, opening line 2 | REQ-013/D-30/D-28 |
| T-U4 | parse: header rules | header-only → `[]`; 0-field first row → E-HEADER0 text; duplicates incl. empty-name → E-DUP text | REQ-002/009 |
| T-U5 | parse: count rules | blank middle line → E-COUNT at line 2; trailing blank → line 3; whitespace-only line converts | REQ-006/009/D-36 |
| T-U6 | parse: D-29 ordering + header check order | `id,name\n1\n"2,3` → E-COUNT at line 2 (quote never reached); `id,"id` → E-DUP 'id' at line 1, NOT E-UQ (D-15 slot (5) before (6), §4.3.2 order, S-9b); `"id,name` → E-UQ at line 1 (no duplicate, so the deferred scan fires, S-9c) | D-29/D-15/D-25 |
| T-U7 | serialize byte form | compact separators, raw UTF-8, escape forms, `]\n` ending — P6 case table | D-14/17/20/26 |
| T-U8 | limit raise | after import, `csv.field_size_limit()` > 131072 | D-21/D-27 |

## 8.2 Contract layer (message catalog + output bytes, still I/O-free)

| T-id | verifies | method |
|---|---|---|
| T-K1 | every E-* template | run the pure stages on each trigger input; assert the exact catalog string from §6.3 (parametrized over strerror where OS-dependent; over name forms for E-DUP — plain, empty, and a newline-bearing name asserted verbatim per the §6.3 E-DUP note; and over PATH forms for the `<path>` slots per the §6.3 verbatim-slot enumeration — including a newline-bearing path asserted verbatim, one stderr write, no escaping — closes adv-c8 F-04) |
| T-K2 | output document byte form | golden bytes for: happy path, Thai text, control chars, header-only `[]\n`, CRLF-in-field (S-1, S-8d, S-13, §6.2.6) |
| T-K3 | exit/channel discipline | `main()` return values 0/1 per §6.4; stdout capture empty on every path — parametrized over REGULAR-FILE output paths (D-55: a `/dev/stdout`-style device output legitimately carries the document on that device at exit 0; the T-K3 assertion is that the TOOL performs no stdout write of its own, verified by running with a regular-file output and by the appendix/41 D-55 probe for the device form) |

## 8.3 Integration / E2E layer (real filesystem, real process)

| T-id | verifies | method | REQ |
|---|---|---|---|
| T-C1 | usage errors | subprocess: 0/1/3 args → exact usage line, exit 1, no file created; sub-case: 2 args with the first option-looking (`-h out.json`) → E-READ on `-h`, exit 1, stdout EMPTY (no help text — the manual dispatch's outcome is normative for all length-2 argv, D-49; skip-with-warning on platforms where `-h` resolves to an existing file); sub-case argc==1 with `-h` as the only arg → the SAME usage line on stderr, exit 1, stdout EMPTY — help text NEVER reaches stdout on any argv (NFR-004; D-52: the manual branch is the one conforming shape, an argparse build's default help action would print help to stdout and exit 0 here; probe appendix/36-rev9-ki-argparse-probes.py P3) | REQ-001/D-34/D-49/D-52 |
| T-C2 | unreadable input | missing path; chmod 000 file (skip as root) → E-READ, exit 1 | D-15(2) |
| T-C3 | UTF-8 errors | `0xFF` file; CR-only file `a,b\rc,d\rc\r\xff` → line 4 cited | REQ-011 |
| T-C4 | empty/BOM-only/blank-lines | zero-byte → E-EMPTY; EF BB BF only → E-EMPTY; `\n\n` → E-HEADER0 line 1 | REQ-009/012/D-31 |
| T-C5 | duplicate header | `id,name,id` → E-DUP 'id'; `a,,b,` → E-DUP ''; `a,,b` converts | REQ-002/F-33 |
| T-C6 | count errors | short row at line 4 → exact E-COUNT (physical-line numbering); trailing blank; whitespace-line converts | REQ-006/007/009 |
| T-C7 | unterminated quotes | `id,name\n"1,2`; `a\n"1`; `"id,name`; N≠M case `h1,h2\n"a\nb",c,"d\ne`; CRLF-interior case `h1,h2\n"a\r\nb",c,"d\ne` → `... line 2: unterminated quoted field (opened at line 3)` (appendix/20 R1); bare-CR interior → same N/M; combined header defect `id,"id` → E-DUP line 1 (not E-UQ, S-9b); negative `5" ruler` converts | REQ-013/D-28/D-15 |
| T-C8 | write-phase failures | `/dev/full` → E-WRITE with output path, exit 1, no regular-file leftover; non-writable dir → E-WRITE, no file created; pre-existing READ-ONLY target (mode 444) in a writable dir → E-WRITE and the target's prior bytes BYTE-IDENTICAL afterward (at-open failure, D-46 — the v5 wide-scope behavior that deleted it is non-conforming; SKIP AS ROOT — DAC_OVERRIDE defeats mode 444 and the premise never materializes, T-C2's convention, adv-c6 F-04); pre-existing output file survives an input-error run byte-unchanged; pre-existing output + fault-injected MemoryError at S5's encode → prior bytes byte-identical, no 0-byte file (§8.4 method); the mid-write cases pin the D-50 failure-arm ordering — on Windows an `os.remove` on the still-open handle raises PermissionError which a best-effort clause swallows and the partial file would SURVIVE, which is exactly why close-before-remove is pinned (the POSIX CI cannot observe that mode — remove-while-open succeeds there — so the pinned ordering itself, not the CI environment, is what rules the Windows mode out; probe appendix/32-rev8-fdclose-probes.py asserts fd.closed at remove time); documented assert-or-accept matrix entry for an ALIASED target (symlink to a regular file) with a mid-write failure: the opened name is removed and the aliased file's partial residue is R-1b (§10.1) — accepted, not asserted ; KeyboardInterrupt sub-case (D-51, closes adv-c8 F-01 = SR7-F-02; probe appendix/36-rev9-ki-argparse-probes.py P1/P2): a KeyboardInterrupt raised inside the write stage (the live probe faults `fd.write` after a successful open on a pre-existing target; in CI, inject the exception class — the FIFO-blocked-write + SIGINT form is the same window) runs the D-48/D-50 failure arm — the partial target is REMOVED, the close-before-remove ordering applies to the KI class like any other — and the KI then propagates: the process exits OUTSIDE the 0/1 matrix (shell-observed 130 on SIGINT; see the §6.4 signal note), stdout empty; the except-Exception build that would leave the partial file is NON-CONFORMING (probe P2 demonstrates the forbidden divergence the D-51 choice closes); SINGLE-KI SCOPE (D-53, closes adv-c9 F-01; probe appendix/39b P1a/P1b live, control P1c): the removal assertion above holds for the SINGLE-KI form only — a SECOND SIGINT delivered INSIDE the failure arm (at its `fd.close()`/`os.remove`) aborts the compensation mid-flight, KI propagates, and the partial target SURVIVES: the documented assert-or-accept matrix entry is that this residue is R-5 (§10.1) — accepted, not asserted (T-C8 asserts the single-KI outcome and documents the double-KI residue); KI-AT-OPEN entry (D-54, closes adv-c9 F-02; probe appendix/39b P2a/P2b live): a SIGINT delivered while `open()` is blocked (FIFO, no reader) makes `open()` itself raise KI with `fd` never bound — NO remove runs and a pre-existing target may be left 0-byte; that outcome is the D-54 at-open classification and its residue is R-6 (§10.1) — documented, not asserted as a target-state contract | REQ-010/D-33/D-43/D-46/D-50/D-51/D-53/D-54/R-1b/R-5/R-6 |
| T-C9 | performance envelope | generated ~50 MB / ~250k-row CSV converts < 30 s, < 1 GB RSS (spot check, not a hard gate) | NFR-003 |
| T-C10 | no-traceback net | fault-injected stage raising a bare `RuntimeError` → E-NET line, exit 1, no traceback substring on stderr | REQ-007 |
| T-C11 | quoted-field byte exactness | `"x\r\ny"` and `"x\ry"` fields → output contains the `\r\n`/`\r` JSON escapes, NOT rewritten `\n` | REQ-004/014/D-24 |
| T-C12 | CR-only + mixed terminators E2E | `a,b\rc,d\r` → converts; `a\nb\rc\n` → converts | REQ-014/§3.1 |
| T-C13 | lossless + inertness E2E | `42,3.14,true,` / `007,` / `<script>` / NUL-FF-VT cells → string-only output, valid JSON | REQ-005/NFR-005/D-14 |
| T-C14 | Python floor | the suite runs on the oldest supported interpreter available in CI (3.9 target; skip-with-warning if unavailable) | NFR-002 |
| T-C15 | BOM E2E | BOM+header → clean keys; byte-identical to no-BOM run; U+FEFF mid-cell preserved | REQ-012 |
| T-C16 | E-MEM fault form | child process run under a low `RLIMIT_AS` (resource limit set before exec — an environment control, not a mock) on a valid input too large for the capped address space → stderr matches an E-MEM phase form (`out of memory reading/while converting/writing ...`); ANY of the phase forms is the accepted assertion, because which phase trips under RLIMIT_AS is build-dependent (a chunked write may OOM at write, a bulk read at read, the row-list build at parse) — the test must not force a specific one; exit 1, stdout empty, no partial output file left (outside the recorded D-53/R-5 arm-abort residue — a second KI or second MemoryError inside the failure arm — per D-56(a)); variant with a pre-existing output file: the state assertion DEPENDS ON THE OBSERVED PHASE FORM of that run — if the form is a PRE-OPEN phase (reading / while converting), the prior bytes must be byte-identical after the failed run (D-43: no truncation has happened at those boundaries); if the form is the WRITE phase (post-open, `out of memory writing <out>`), the pinned D-33/D-46 compensation REMOVES the target (open already truncated it), so the correct assertion is that the path is ABSENT — unless the compensation itself is aborted mid-flight per D-53/R-5 (a SECOND KI, or a second MemoryError — any non-OSError — landing inside the failure arm), in which case the partial file is PRESENT and that outcome is the recorded residue, not a contract violation (adv-c10 F-01, decision D-56(a); live probe appendix/47 P1a — partial PRESENT at this exact phase-form stderr line, control P1b single-MemoryError removal, P1c pure-RLIMIT_AS honest negative) — no conforming mechanism can otherwise leave it present: after a successful open the every-exception compensation removes the target, and a remove failure on a regular file is R-1's pathological-only residue, unreachable under RLIMIT_AS fault injection (SR6-F-04: the former "(or byte-identical)" slack is deleted — it admitted a compensation-less build on the byte-identical branch) — never still present with foreign bytes OUTSIDE the D-53 arm-abort residue. The test must read the phase from the stderr form and assert the matching state; asserting byte-identity unconditionally (v6 wording, "form-independent") is non-conforming — a chunked-write build that OOMs at write deletes the pre-existing file BY DESIGN (adv-c6 F-01; live probes appendix/30b-adv-c6-reaim-probes.py P2/P2b, re-aimed per SR7-F-03; historical: appendix/29b P2/P2b) | REQ-007/NFR-005/E-MEM/D-43/D-44/D-46/D-50 |

## 8.4 Test-infrastructure notes

- `/dev/full` exists on Linux CI; on macOS the E-WRITE/ENOSPC case is
  replaced by writing the output into a directory on a read-only mount
  (or any directory made non-writable), which fails `open()` itself with
  EACCES/EROFS — the T-C8 assertion is on the message/exit/cleanup
  contract, not on the ENOSPC errno itself. Do NOT use `ulimit -f`
  (RLIMIT_FSIZE) as the macOS fallback: exceeding RLIMIT_FSIZE kills the
  process with SIGXFSZ (signal death, not a catchable OSError), so the
  child can never print the E-WRITE line and the T-C8 assertions would
  fail for the wrong reason (returncode < 0). The ENOSPC-open-succeeds
  shape (T-C8's flush-failure form) is therefore Linux-CI-only; macOS
  keeps message-shape/exit/cleanup coverage via the non-writable-dir form.
- E-MEM (T-C16) is exercised by fault injection: monkeypatching
  is NOT used inside the unit under test; instead the test runs a child
  process with a low `RLIMIT_AS` so a genuine MemoryError surfaces in
  `main`'s net. (RLIMIT_AS injection is an environment control, not a
  mock.) Where RLIMIT_AS is unavailable (some CI sandboxes), the fallback
  is a genuinely huge generated input under the normal rlimit — the
  asserted contract (E-MEM line, exit 1, no partial file) is identical.
  For the pre-existing-output variant the state assertion follows the
  OBSERVED phase form (§8.3 T-C16, adv-c6 F-01): byte-identical for a
  pre-open form, path-absent for the write-phase form (the D-33/D-46
  compensation removes the truncated target by design).
- The 50 MB NFR-003 case is generated, checksummed, and reused so the
  spot check is reproducible; it is marked `slow` and may be excluded from
  the default run.

# 9. Non-functional requirement mapping

| NFR | design decision that delivers it | where |
|---|---|---|
| NFR-001 zero deps | single file; imports only `csv, io, json, os, sys` (§4.1: manual dispatch is the ONE conforming shape — D-52 retracts the former argparse alternative, whose import would break this pinned set) | §4.1, §2.2 |
| NFR-002 3.9+ floor | no 3.10+ syntax (no match, no `\|` unions in annotations used at runtime); dict ordering relied on only as a documented 3.7+ language property; f-strings and `encoding=` forms are 3.9-safe | §4.3.5 |
| NFR-003 envelope | whole-file in-memory pipeline (documented as acceptable below the envelope; larger files out of scope per REQ §3.2); line numbering advances INCREMENTALLY per record span (§4.3.2) so the whole pipeline is O(input length) — no quadratic prefix rescans; the FSM is O(record length), records sum to the input length | §2, §4.2, §4.3.2 |
| NFR-004 channel discipline | single printer in `main`; success path contains no print statements at all; the stdout/stderr rows of §6.4 and T-K3 scope to REGULAR-FILE output paths — a character-device output (`/dev/stdout`, `/dev/stderr`, `/dev/null`, `/dev/fd/N`) receives the document on that device at exit 0 by the caller's own redirection choice (D-55); the tool performs no stdout/stderr write of its own on any path | §4.1, §6.1, §6.4 |
| NFR-005 robustness | input only ever parsed (csv) and serialized (json) — never executed/interpolated; startup limit-raise (§4.6) removes the 131072-byte field cap; MemoryError handled per E-MEM | §4.6, §7.1 |

## 9.1-9.5 Verification anchors

NFR-001: T-C-suite imports audit (the test asserts the module's import
set). NFR-002: T-C14. NFR-003: T-C9. NFR-004: T-K3 + every E2E asserting
empty stdout. NFR-005: T-C13 + T-U8 + T-C10 + T-C16 (E-MEM fault form;
NFR-005's write-phase MemoryError clause is asserted by T-C16's phase-form
match and T-K1's write-phase template assertion — under D-44 the
serialize phase asserts the SAME output-named template).

# 10. Quality-claim evidence tuples

This section is the ONLY home of the mechanical validator's claim
vocabulary in this document. Every word on that keyword list used anywhere
in the spec appears inside one of the tuples below; outside §10 the spec is
worded in mechanism and trigger terms. Claims that have no complete tuple
are assumptions, proposals, or risks — stated as such where they occur.

### QC-1 <all error classes exit exactly 1 with one prefixed stderr line>
- Scope: every failure path E-USAGE..E-NET (§6.3) on every supported
  platform (NFR-002 floor 3.9+).
- Mechanism: single handler in `main` (§7.3) prints the pre-formatted
  message carried by the typed error and returns 1; no other code path
  prints or returns nonzero; the argv branch returns 1 inline; argparse's
  exit-2 default is avoided by manual dispatch (§4.1, D-34 probe).
- Assumptions: stderr is writable (a closed stderr would make the print
  itself raise — the net's print is wrapped best-effort; a process whose
  stderr is closed is outside the tool's contract, same accepted boundary
  as timeout-cancellation in §7.1).
- Failure: if the mechanism itself fails (print raises), the last-resort
  behavior is process exit with a nonzero code — the two-valued contract
  degrades to nonzero-visible-failure, never to exit 0 or a traceback.
- Verification: T-C1..T-C10, T-C16, T-K1, T-K3 assert message text and
  exit code for every catalog class on a real subprocess.

### QC-2 <no output file is created or truncated on any failed run>
- Scope: every error class; both "absent" and "pre-existing" output
  targets; every fault position in S5 (before the open, at the open,
  during write/flush, at close); the pinned binary write shape only
  (D-45 — no text-mode build is conforming, so no claim is made for one);
  PLATFORM SCOPE: the compensation clause holds on every platform in the
  conformance domain — POSIX and Windows alike — because the failure arm
  closes the fd BEFORE the remove (D-50); the state contract holds on
  every platform by mechanism, not by scoping. SIGNAL-WINDOW EXCEPTIONS
  (D-53/D-54, closing adv-c9 F-01/F-02): the claim is scoped to runs
  where AT MOST ONE KeyboardInterrupt strikes and the failure arm runs
  to completion — the two recorded residues OUTSIDE the claim are the
  double-KI form (a second KI inside the failure arm aborts the
  compensation mid-flight; the partial file survives — R-5, §10.1) and
  the KI-at-open form (a KI raised by `open()` itself, fd never bound,
  runs no compensation; a PRE-EXISTING target may be left 0-byte, and
  an ABSENT target may be left CREATED at 0 bytes by the kernel's
  O_CREAT — both flavors of the same window are R-6, §10.1, decision
  D-56(b) per adv-c10 F-04),
  plus the UNCATALOGED kills already outside §7.1's
  scope (SIGKILL, SIGTERM-default).
- Mechanism: phase split (D-15 slot 7, §4.5 row 3) — S5 is structurally
  unreachable until S3 accepted every record; within S5 the pinned
  operation order D-43 runs the encode to completion BEFORE the open, so
  a failure before the open cannot touch any output path (probe
  appendix/22 W-series: a MemoryError at encode leaves pre-existing
  bytes byte-identical); at-open failures leave the target byte-untouched
  because the compensation is triggered only by exceptions raised after
  a SUCCESSFUL open (D-46 — no remove runs, absent or pre-existing
  target survives; probe appendix/28 R6-P2); after a successful open,
  the D-33 delete-on-failure
  compensation triggers on EVERY exception class (except-scoped
  reference shape, §4.5 — the remove runs in the failure arm only, never
  on the success path, D-48) — not OSError only — so a MemoryError
  mid-write also removes the
  partial file; the failure arm CLOSES the fd before the remove (D-50:
  on Windows `os.remove` on an open handle raises PermissionError, which
  a best-effort clause swallows — close-before-remove is what makes the
  remove a real step on every platform; probe appendix/32-rev8-fdclose-probes.py
  P2/P3); the SAME clause covers the signal-delivered KeyboardInterrupt
  class (D-51) — a KI raised inside the try (AFTER a successful open)
  runs the identical arm (close, remove, re-raise), so a single-KI
  interrupted mid-write run also leaves no partial target (probe
  appendix/36 P1; the except-Exception control
  leaves it and is NON-CONFORMING, probe appendix/36 P2; SINGLE-KI SCOPE
  per D-53: the outcome requires the arm to run to completion — a second
  KI inside the arm aborts it mid-flight and the partial file survives,
  R-5, probe appendix/39b P1a/P1b with control P1c; a KI raised BY
  `open()` itself never reaches the arm — the D-54 at-open class, fd
  None, no remove, R-6, probe appendix/39b P2a/P2b); before S5 even
  starts, the serialize phase holds the same
  no-side-effect property (D-44: nothing is open, the filesystem is
  untouched).
- Assumptions: the compensation's `os.remove` can fail on device/permission
  paths — REQ-010 explicitly accepts and ignores that (harmless attempt);
  under an aliased target (symlink/hardlink output path) the removal
  covers the opened NAME only — the R-1b residue (§10.1) is an accepted
  risk, not part of this claim's scope.
- Failure: if removal fails on a REGULAR file (pathological: e.g. parent
  dir made unwritable between write and remove), a partial file may
  survive — the error is still reported and exit is 1; recorded as an
  accepted residual risk (R-1, §10.1), not silently folded.
- Verification: T-C1 (no file created), T-C8 (write-failure forms
  incl. `/dev/full`, the pre-existing-output + MemoryError-at-encode
  case, and the pre-existing read-only-target at-open case), T-C8
  pre-existing-file-unchanged assertion, T-C8's KeyboardInterrupt
  sub-case (D-51: KI inside the try removes the partial target, then
  propagates — probe appendix/36 P1; the except-Exception control that
  leaves it is non-conforming, probe appendix/36 P2; SINGLE-KI SCOPE per
  D-53 — the removal assertion covers the one-KI form; the double-KI
  residue R-5 and the KI-at-open 0-byte residue R-6 are documented
  assert-or-accept matrix entries, live-probed by appendix/39b
  P1a/P1b/P1c and P2a/P2b), T-C16 (RLIMIT_AS
  variant with a pre-existing output: the state assertion follows the
  OBSERVED phase form — byte-identical for a pre-open-phase form
  (reading/while converting), path-absent for the write-phase form
  (the D-33/D-46 compensation removes it by design — with the same
  D-53/R-5 arm-abort scope: a second KI or second MemoryError inside
  the failure arm leaves the partial file, the recorded residue per
  D-56(a), probe appendix/47 P1a/P1b/P1c); asserting
  byte-identity unconditionally is non-conforming — adv-c6 F-01,
  live probes appendix/30b-adv-c6-reaim-probes.py P2/P2b (re-aimed per
  SR7-F-03; historical: appendix/29b P2/P2b)).

### QC-3 <the output document bytes are exactly the §6.2 contract on every platform>
- Scope: every successful run, all values, all supported Pythons 3.9+.
- Mechanism: `serialize` pins `json.dumps(rows, ensure_ascii=False,
  separators=(",", ":"))` + `"\n"` (§4.4, D-17/D-26); the write path is
  binary mode so no OS newline translation can alter the trailing byte
  (D-35).
- Assumptions: json.dumps escape behavior is stable across 3.9..3.13 for
  the pinned forms (probe P6 on 3.13.5; the REQ's own probes verified the
  short-form set on the same interpreter family).
- Failure: a future Python changing escape forms would be a schema-version
  mismatch of the platform — detected by T-U7/T-K2 golden bytes, which pin
  the exact byte forms in CI.
- Verification: T-K2 golden bytes; T-C11 (quoted-field CR/CRLF
  byte-exactness E2E); T-C15 (BOM byte-identity).

### QC-4 <row-start line numbers are the D-28 physical lines, on every terminator mix>
- Scope: E-COUNT/E-UQ/E-UTF8/E-HEADER0 line citations; REQ-007(c),
  REQ-011, REQ-013 N and M.
- Mechanism: the tool's own offset-based counting (ADR-2): record spans
  from `tell()` (P1), incremental break counting per span (§4.3.2),
  `line_of_offset` with the D-28 break set (P2/P4) — `reader.line_num` is
  NOT used for messages (P7: it provably lags one row after CRLF records).
- Assumptions: `StringIO.tell()` advances exactly with consumption for
  `csv.reader` (P1 verified incl. quoted multi-line records).
- Failure: a reader implementation change breaking the tell() invariant
  would surface as misnumbered lines — caught by T-U2's exact-slice table
  and T-C3/T-C6/T-C7's pinned line numbers.
- Verification: T-U1 (D-28 counter table), T-U2 (spans), T-C3 (`a,b\rc,d\rc\r\xff`
  → line 4), T-C6 (physical-line numbering), T-C7 (N and M cases).

### QC-5 <the pipeline is linear-time in the input size>
- Scope: NFR-003 envelope (50 MB / ~250k rows < 30 s, < 1 GB RAM).
- Mechanism: each stage touches the data a constant number of times:
  one decode; per record one tell/slice + one O(record) FSM scan +
  one O(record) break count added incrementally (§4.3.2 — the
  quadratic-prefix-rescan trap is explicitly designed out); one
  serialization; one write. Whole-file in-memory is documented as
  acceptable under the envelope (REQ §3.2).
- Assumptions: interpreter-level costs (csv/json C accelerators) are
  linear on 3.9+; the RSS envelope holds for the pinned 50 MB input.
- Failure: pathological memory pressure fails per E-MEM (reported, exit 1)
  rather than silently degrading.
- Verification: T-C9 spot check with a generated, checksummed 50 MB file
  (timing + peak RSS); marked slow, reproducible.

### QC-6 <input content never executes, interpolates, or escapes the data channel>
- Scope: NFR-005; all input bytes.
- Mechanism: the only consumers of input text are `csv.reader` (parse) and
  `json.dumps` (serialize); no eval/exec/format/interpolation of input
  content anywhere in the design; output escaping is json.dumps' grammar
  (D-14/D-20), so output is always valid JSON.
- Assumptions: stdlib csv/json contain no relevant CVE-class injection
  vector for this data flow (stdlib-supported versions per NFR-002).
- Failure: a stdlib-level parsing bug would be an interpreter defect
  outside the tool's control; the tool's surface adds no second path.
- Verification: T-C13 (hostile cells `<script>`, control chars → inert
  valid JSON); T-U7 escape table; imports audit (no exec/eval imports).

## 10.1 Risk register (claims that are NOT guarantees)

- R-1: a partial output file can in principle survive a failed S5 if
  `os.remove` itself fails on a regular file (QC-2 Failure).
  Likelihood: pathological. Owner: implementor (preserve the
  compensation order: remove BEFORE raising, for every exception class
  raised after a successful open — D-46). Rationale: no REQ mandates surviving this case;
  REQ-010's own AC accepts a harmless removal failure on device paths.
  Impact: bounded — the error message and exit 1 are unaffected; the
  residue is a partial file a user might mistake for a complete
  document. Mitigation: delete-on-failure compensation runs first
  (before the raise) on every failure after a successful open;
  pre-open and at-open failures (D-43/D-46)
  cannot create this residue at all. Verification: not
  exercisable by test on a regular file (a failing `os.remove` on a
  regular file is not reachable without mocking the very call under
  test); enforced by the compensation-order invariant in §4.5 and
  reviewed at code review; the /dev/full form (removal fails on a
  DEVICE path) is covered by T-C8.
  (v4, F-05: restructured into the full accepted-risk record — owner,
  rationale, impact, mitigation, verification.)
- R-1b: under an ALIASED output target (symlink or hardlink), a failed
  post-open S5 run can leave the partial payload in the aliased
  real/twin file while the opened NAME is removed: open() writes
  THROUGH the link (the write mutates the targeted INODE) and the
  D-33 compensation unlinks only the opened name (the compensation's
  unit of mutation — probe appendix/26b-adv-c5-probes.py P2/P2b;
  accepted per D-47, closing adv-c5 F-02 as accepted-risk disposition
  (a)). Likelihood: user-induced aliasing of the output path (e.g.
  `ln -s real.json out.json`); bounded to that setup — regular-file
  targets are unaffected. Owner: implementor (preserve the
  name-scoped remove: `os.remove(path)` of the opened path, never an
  inode-directed truncation) and user (avoid aliased output paths; no
  REQ promises aliasing semantics). Rationale: the alternatives were
  (i) name-scoped compensation with a recorded risk and (ii) tightened
  mechanics (create-then-rename or fd-based unlink); (ii) adds
  temp-file machinery ADR-4 explicitly designed out and no REQ covers
  aliased targets, so (i) was taken. Impact: bounded — the error
  message, exit code, and regular-file behavior are unaffected; under
  an alias the residue is a partial document in the aliased file a
  user might mistake for a complete one (REQ-010's "plausible complete
  JSON document" wording is met for the opened name, not the alias
  target). Mitigation: T-C8's documented assert-or-accept matrix entry
  (§8.3) makes the case visible to the implementor and auditor; the
  §4.5 aliasing boundary paragraph names it normatively. Verification:
  not asserted (an accepted-risk record is not a test claim); the
  probe P2/P2b evidence class in appendix/26b demonstrates the
  residue; the cold auditor reads this record plus the T-C8 matrix
  entry.
- R-2: two concurrent processes writing one target interleave at the
  OS level with NO promised outcome (§4.5 row 9). Out of scope per REQ
  §2; no lock is provided. The reachable outcomes include: both runs
  fail; one succeeds and is then overwritten; or a failed run's
  compensation unlinks the file name a concurrent successful run
  already wrote — leaving a silent exit-0 run with NO file at all
  (deterministic probe: appendix/26b-adv-c5-probes.py P12). Not a
  guarantee — an accepted scope boundary (v6 rewording, adv-c5 F-03:
  the earlier "last writer wins" gloss did not describe the reachable
  outcome set).
- R-3: a closed/broken stderr makes error reporting itself fail (QC-1
  Assumptions). Outside the tool's contract; same class as the user
  closing the terminal.
- R-4: SAME-PATH invocation (`csv2json.py data.csv data.csv`, closing
  adv-c6 F-03). The whole-file pipeline (§2.2) reads the input into
  memory BEFORE S5 opens the output, so the run can succeed — replacing
  the input file with the JSON (S-1's wholesale replace semantics; the
  evident in-place intent) — but a FAILED post-open S5 run (mid-write
  ENOSPC/EIO, post-open MemoryError) truncates the input at the open and
  then the D-33 compensation's remove DELETES it: the destroyed file is
  the user's SOURCE data, not a derived output — a materially different
  loss class than R-1's residue (a partial output mistaken for a
  complete document). Likelihood: user-induced (the caller passed the
  same path twice); bounded to that invocation. Owner: user (do not
  pass the same path as both arguments; keep the source elsewhere or
  rely on a backup) and implementor (no special-casing: behavior is
  exactly the ordinary single-target contract on that path). Rationale
  for recording rather than guarding: a same-path refusal would need a
  new error class outside the CLOSED catalog (§6.3, D-42), and it would
  forbid a legitimate in-place conversion the requirements never
  prohibit — those two reasons carry the rationale (v8, SR6-F-07: the
  earlier "no REQ promises same-path semantics" clause is demoted to a
  supporting note; it described the absence of a REQ promise, which is
  why the case needed a record, not a defense of the recorded
  behavior). Impact: on a failed same-path run the
  input no longer exists after exit 1; the message/exit/cleanup contract
  is otherwise exactly E-WRITE's. Mitigation: this record plus §4.5 row
  10's same-path sentence; the §11 REQ-010 row cites it. Verification:
  probe appendix/30b-adv-c6-reaim-probes.py P3 demonstrates the failed
  same-path deletion live (real filesystem); not asserted as a test
  claim (an accepted-risk record is not a test claim), the cold auditor
  reads this record.
- R-5: a SECOND KeyboardInterrupt (or any non-OSError) landing INSIDE the
  §4.5 failure arm interrupts the compensation mid-flight (KI is raisable
  at any bytecode boundary, including inside the arm's `fd.close()` and
  `os.remove`; the arm's `except OSError` clauses do not catch it), so
  the best-effort `os.remove` may never run and the PARTIAL file
  survives the interrupted run — a document of exactly the
  "plausible-complete" class the compensation exists to prevent
  (live-probed: appendix/39b-adv-c9-probes.py P1a/P1b — 1546 of 3092
  bytes survived a double-SIGINT run; control P1c: the single-KI
  outcome holds, D-51's mechanism intact when the arm completes).
  Likelihood: user-induced (the ordinary double-Ctrl-C within the
  arm's millisecond-scale window); bounded to the post-open
  compensation window. Owner: user (one Ctrl-C is the contracted
  interrupt; a second strike during cleanup has no conforming
  protection) and implementor (no special-casing: the arm stays
  best-effort). Rationale for recording rather than guarding: a
  KI-resistant arm (signal blocking/deferral around the compensation)
  needs the `signal` import, which conflicts with NFR-001's pinned
  import set (D-52's precedent — an extra top-level import has no
  conforming reading); recording the residue is the only conforming
  disposition (decision D-53, closing adv-c9 F-01). Impact: bounded —
  the single-KI contract, all cataloged-error outcomes, exit codes,
  and messages are unaffected; the residue is a partial file a user
  might mistake for a complete document, same loss class as R-1.
  Mitigation: every site that states the interrupted-run outcome does
  so under the single-KI condition (§4.5, §6.4 signal note, §7.1,
  §7.3, QC-2, T-C8); T-C8 documents the double-KI residue as an
  assert-or-accept matrix entry. Verification: the residue is
  demonstrated live by appendix/39b P1a/P1b (not asserted as a test
  claim — an accepted-risk record is not a test claim); the cold
  auditor reads this record plus the T-C8 matrix entry.
- R-6: a KeyboardInterrupt raised BY the `open()` call itself —
  including the state where the kernel has already applied
  O_CREAT|O_TRUNC but the signal struck before `open()` returned and
  `fd` was bound — is classified as an AT-OPEN failure (D-54): the
  reference shape observes `fd is None`, runs NO compensation, and the
  KI propagates, so a PRE-EXISTING target may be left truncated to
  0 bytes by the kernel's O_TRUNC even though the tool wrote nothing
  (live-probed: appendix/39b-adv-c9-probes.py P2a — SIGINT while
  blocked in `open()` on a FIFO makes `open()` itself raise KI,
  "KI-FROM-OPEN"; P2b — fd None, no remove, prior-good target at
  0 bytes). Likelihood: low (requires the interrupt to land inside the
  open syscall — a blocking FIFO, slow NFS/FUSE target — or in the
  narrow post-syscall pre-bind window); bounded to the KI-at-open
  window itself — BOTH flavors: a PRE-EXISTING target truncated to
  0 bytes, or an ABSENT target CREATED at 0 bytes by the kernel's
  O_CREAT (adv-c10 F-04; decision D-56(b)). Owner: user (avoid
  interrupting runs against slow/blocking
  output targets; keep the prior output backed up) and implementor
  (no special-casing: fd-binding is the trigger basis). Rationale for
  recording rather than compensating: whether the kernel applied
  O_TRUNC is unobservable from Python without extra syscalls or
  imports, so "compensate whenever O_TRUNC may have applied" has no
  conforming mechanism; the fd-binding point is the only observable
  boundary, and classifying by it is the implementable reading
  (decision D-54, closing adv-c9 F-02; the opposite reading —
  compensate because truncation already happened — would contradict
  D-46's at-open rule with no way to detect the case). Impact:
  bounded — the pre-open/at-open story (D-43/D-46), all cataloged
  outcomes, and the single-KI contract are unaffected; the residue is
  a 0-byte file — where the user's prior output stood (truncation
  flavor) or at a path that did not exist before (create flavor,
  D-56(b)) — discoverable at
  the next read. Mitigation: §4.5's KI-at-open classification names
  the case normatively (both flavors); §7.1's before-open survival rule and QC-2's
  Scope carry the R-6 exception; T-C8's matrix documents the
  KI-at-open outcome. Verification: demonstrated live by appendix/39b
  P2a/P2b (not asserted as a test claim — an accepted-risk record is
  not a test claim); the cold auditor reads this record plus the T-C8
  matrix entry.

# 11. Traceability matrix

Every REQ/NFR → designing section → key invariant → failure behavior
(§6.3 id) → test layer + id → evidence. "Impl detail" rows are marked as
implementation details (not REQ-derived). Nothing uncovered; nothing
invented.

| REQ/NFR | designed in | invariant | failure id | test layer / id | evidence |
|---|---|---|---|---|---|
| REQ-001 | §4.1, §6.1 | argc==2 else prefixed usage; input-then-output; manual-dispatch outcome normative for ALL length-2 argv incl. option-looking positionals (D-49); argc≠2 (e.g. `-h` alone) → usage line on stderr, exit 1 — the manual branch is the ONE conforming dispatch shape (D-52; argparse non-conforming: import-set + stdout-help) | E-USAGE | E2E T-C1 (incl. `-h out.json` sub-case and the argc==1 `-h` sub-case) | REQ AC; 10-fold-c5 F29 (argparse exit 2); appendix/30b P4; appendix/36 P3/P4 |
| REQ-002 | §4.3.4, §3.1 | header verbatim; ≥1 field; dup error; empty name once | E-HEADER0/E-DUP | unit T-U4; E2E T-C5 | REQ ACs; P8 |
| REQ-003 | §4.3.5, §6.2.5 | one object/row, input order | — (success path) | unit T-U5; E2E T-C13 | P8 happy path |
| REQ-004 | §4.3.1, §4.3.3 | dialect-exact quoted fields; byte-exact in-quote newlines | E-UQ (only if unclosed) | unit T-U3; E2E T-C11 | P8 CRLF-in-field; REQ 05-batch-2 probes |
| REQ-005 | §4.4, §6.2.5 | all values JSON strings; "" not null; verbatim | — | unit T-U7; E2E T-C13 | P6; REQ ACs |
| REQ-006 | §4.3.5 | len(row)==len(header) per data row | E-COUNT | unit T-U5; E2E T-C6 | P8 count cases |
| REQ-007 | §6.3 catalog, §7.1 | prefix on ALL classes; (b)-(d) per class | all | contract T-K1 | catalog vs REQ examples |
| REQ-008 | §7.2, §5.1 | first error only; S5 unreachable on failure | all | E2E T-C8 (unchanged file), T-U6 | P8 ordering |
| REQ-009 | §4.3.4/§4.3.5/§4.3-end | 0-field model; blank=EMPTY; whitespace=data; one-trailer rule | E-EMPTY/E-HEADER0/E-COUNT | unit T-U4/T-U5; E2E T-C4/T-C6 | P8; 10-fold-c5 F31 |
| REQ-010 | §4.5, §7.1, QC-2 | encode-before-open (D-43); single binary write shape (D-45); validate-then-write; compensation on every exception after a successful open (D-46) via the EXCEPT-SCOPED reference shape (D-48); name-scoped remove with R-1b aliasing boundary (D-47); same-path invocation accepted-risk R-4; compensation best-effort and KI-scoped — single-KI outcome per D-53 (double-KI residue R-5) and KI-at-open classification per D-54 (0-byte residue R-6); output-path naming | E-WRITE | E2E T-C8 (incl. pre-existing + MemoryError-at-encode, the read-only-target at-open case skip-as-root, the KI sub-case with the D-53 single-KI scope, and the D-54 KI-at-open matrix entry) | 10-fold-c5 F28 (/dev/full); appendix/22 W-series; appendix/28 R6-P1/R6-P2; appendix/30b P1/P1b/P2/P2b/P3; appendix/39b P1a/P1b/P1c/P2a/P2b |
| REQ-011 | §4.2, §7.1 | strict decode; byte cited at D-28 line | E-UTF8 | E2E T-C3 | P4 (line 4 case) |
| REQ-012 | §4.2 | one leading BOM stripped; U+FEFF elsewhere data | E-EMPTY (BOM-only) | E2E T-C15 | P8 BOM cases; D-31 |
| REQ-013 | §4.3.3, §5.3 S-9..S-11 | FSM per record; N=row start, M=open line; header included; no pre-pass | E-UQ | unit T-U3/T-U6; E2E T-C7 | P3/P8 all AC shapes |
| REQ-014 | §4.3.1 | newline='' handoff; no universal newlines anywhere | E-COUNT (CR crash shape gone) | E2E T-C11/T-C12 | P8 CR-only; REQ batch-2 |
| NFR-001 | §2.2, §9 | stdlib-only import set | — | imports audit (T-C suite) | §9 |
| NFR-002 | §9 | 3.9-safe syntax; behavior identical across floor | — | T-C14 | §9 |
| NFR-003 | §4.3.2, §9, QC-5 | O(input) pipeline; incremental line counting | E-MEM | T-C9 | §4.3.2 note |
| NFR-004 | §4.1, §6.4 | stdout empty on every path — scoped to REGULAR-FILE output paths (D-55: a character-device output such as `/dev/stdout` receives the document by the caller's own redirection; the tool itself performs no stdout write); one stderr line on failure | — | contract T-K3 | §6.4 |
| NFR-005 | §4.6, §7.1, QC-6 | limit raised; content inert; MemoryError contracted | E-MEM/E-NET | T-U8/T-C13/T-C10 | P5; REQ ACs |
| Impl detail | ADR-2 (§2.3) | offset-based line numbers (line_num lags) | — | T-U2 | P7 lag evidence |
| Impl detail | ADR-4 (§2.3) | no temp-file+rename (single-phase write suffices) | — | — | §2.3 rationale |
| Impl detail | §4.6 degrade loop | halving on OverflowError | — | T-U8 | P5 |

Decision-coverage check: D-01..D-56 are all DECIDED in
appendix/03-decision-register.md and all are bound to spec mechanisms —
D-01 (§4.1), D-02 (§4.1, §6.1), D-03 (§4.3.4), D-04 (§4.3.1), D-05
(§4.3.5), D-06 (§4.3.5, §4.4), D-07 (§9), D-08 (§2.4), D-09 (§4.5), D-10
(§7.2), D-11 (§4.4), D-11b (§4.1, §4.4), D-12 (§4.3.4), D-13 (§4.2), D-14
(§4.4), D-15 (§4.3.2, §5.1), D-16 (§4.2), D-17 (§4.4), D-18 (§4.3.5), D-19
(§4.3.3), D-20 (§4.4), D-21 (§4.6), D-22 (§6.3), D-23 (§4.2), D-24
(§4.3.1), D-25 (§4.3.2, §4.3.3), D-26 (§4.4), D-27 (§4.6), D-28 (§4.2,
§4.3.3 counting rule), D-29 (§4.3.2), D-30 (§4.3.3), D-31 (§4.2), D-32
(register hygiene, not a spec mechanism), D-33 (§4.5), D-34 (§4.1), D-35
(§4.5), D-36 (§4.3.5), D-37 (§2.1, §2.3 ADR-1/ADR-4 — pure-function core,
five linear stages, one external seam `main`, no temp-file machinery),
D-38 (§4.3.2 tell()-span arithmetic, §4.2 incremental counting — offset-
based line numbers everywhere, `reader.line_num` never used for messages),
D-39 (§4.3.3 — the per-record 4-state FSM itself), D-40 (§4.5 single-phase
binary write with the D-33 delete-on-failure compensation; residual risks
R-1/R-2/R-3 in §10.1), D-41 (§4.1 manual argc dispatch), D-42 (§6.3 closed
catalog + §7.3 net order; §7.1 taxonomy N/A rows), D-43 (§4.5 — S5's
normative operation order: encode completes before the open, and the
delete-on-failure compensation triggers on every exception raised
after a successful open (trigger scope narrowed at the D-46 refinement,
same mechanism); bound also in §2.2, §5.3 S-14, §6.3 E-MEM, §7.1
E-WRITE/E-MEM
rows, §8.3 T-C8/T-C16, QC-2), D-44 (§4.4/§6.3 — the E-MEM serialize
phase reports the SAME output-named form as the write phase
(`out of memory writing <out>`), per NFR-005's APPROVED sentence covering
write/serialize as write-time failures naming the output path; no
compensation at serialize since nothing is open; bound also in §4.4,
§7.1 E-MEM, §8.3 T-C16), D-45 (§4.5 — the write stage has ONE
implemented shape, binary `open(path, "wb")` with the D-43
encode-before-open order; a text-mode build is NON-CONFORMING because
its encode runs implicitly inside the write call, after the open's
O_TRUNC, so the D-43 pre-open no-side-effect outcome is structurally
unreachable there — closes adv-c5 F-01; bound also in §2.2, §5.3 S-14,
QC-2 scope, §8.3 T-C8/T-C16, §11 REQ-010 row), D-46 (§4.5 — the D-33
compensation trigger is every exception raised AFTER A SUCCESSFUL
open; an at-open failure reports E-WRITE directly and leaves the
output target byte-untouched whether absent or pre-existing (read-only
target in a writable dir survives — probe appendix/28 R6-P2),
superseding the v5 wording ("EACCES at open" as a trigger) and
S-14(b)'s
"harmless no-op" description — closes adv-c5 F-04; bound also in
§2.2, §4.5 table rows 3/6/7/10/11, §5.3 S-14(b), §7.1 E-WRITE/E-MEM/
E-NET rows and the partial-failure taxonomy note, §8.3 T-C8, QC-2,
§11 REQ-010 row), D-47 (§4.5 aliasing boundary — the compensation
removes the opened NAME while the write mutates the targeted INODE;
under a symlink/hardlink output path the aliased file can retain a
partial payload; disposition accepted-risk (a) per adv-c5 F-02,
recorded as R-1b in §10.1 and documented assert-or-accept in T-C8's
matrix; bound also in §4.5 table row 10, §5.3 S-14(e), §11 REQ-010
row), D-48 (§4.5 — the compensation's REFERENCE SHAPE is except-scoped:
the best-effort remove lives in the failure arm ONLY, guarded by
`fd is not None`, and the arm re-raises, so it can never run on the
success path; a finally-based shape conforms only with an explicit
failure flag; the v6 try/finally-with-guarded-remove snippet — which
deleted every successful run's output — is superseded, closes adv-c6
F-02; bound also in §4.5, QC-2 Mechanism, §11 REQ-010 row), D-49 (§4.1
— the manual dispatch's outcome is NORMATIVE for ALL argv of length 2:
`-h`/`--help` in a positional slot are ordinary path strings (E-READ,
exit 1, stdout empty); argparse is non-conforming outright per D-52
(v9 retraction), whose builtin help action's stdout-help+exit-0 outcome
has no §6.4 matrix row on any argv class (closes adv-c6 F-05, tightened
by adv-c8 F-02); bound also in §6.1 flags row,
§8.3 T-C1, §11 REQ-001 row), D-50 (§4.5 — the D-48 failure arm CLOSES
the fd (best-effort, errors ignored) BEFORE the best-effort remove: the
OS holds the target's handle open until close, and on Windows
`os.remove` on an open handle raises PermissionError which a
best-effort clause swallows, so a remove-while-open shape leaves the
partial file — a deterministic QC-2 violation on a supported platform;
close-before-remove delivers the state contract on POSIX and Windows
alike and QC-2 stays UNSCOPED, closing SR6-F-01; a shape that removes
while the fd is open is NON-CONFORMING; bound also in §4.5 reference
shape + compensation bullet, §4.5 table rows 10/11, §8.3 T-C8/T-C16,
QC-2 Scope/Mechanism, §11 REQ-010 row, register D-48 v8 refresh),
D-52 (§4.1 — the dispatch has ONE conforming shape: the manual
`len(argv) != 2` branch; the former hypothetical argparse alternative
(sanctioned under override conditions in earlier revisions) is
RETRACTED — an argparse import flunks §9 NFR-001's pinned import-set
audit, and its builtin help action puts help text on STDOUT with exit 0
on the argc==1 class, violating NFR-004 with no §6.4 matrix row;
D-41 (manual argc dispatch) and D-49 (length-2 normative outcome) keep
their substance; closes adv-c8 F-02; bound also in §4.1, §6.1 flags
row, §8.3 T-C1, §9 NFR-001 row, §11 REQ-001 row), D-53 (§4.5/§6.4/§7.1/
§7.3/QC-2 — the D-51 compensation outcome is a SINGLE-KeyboardInterrupt
contract conditional on the failure arm running to completion: one KI
raised after a successful open runs the D-48/D-50 arm (close, remove,
re-raise) and leaves no partial target, but a SECOND KI landing inside
the arm aborts the compensation mid-flight and the partial file
survives — the accepted residue R-5 (§10.1); the KI-resistant-arm
alternative is rejected because the `signal` import conflicts with
NFR-001's pinned import set (D-52's precedent); closes adv-c9 F-01;
bound also in §4.5 compensation bullet + reference-shape note +
mutation rows 9/10/11/13, §6.4 signal note, §7.1 timeout-cancellation
clause, §7.3, §8.3 T-C8, QC-2 Scope/Mechanism/Verification, §10.1 R-5,
§11 REQ-010 row; v11 fold: the arm-abort class is ANY non-OSError —
explicitly including a second MemoryError — so the five absolute
write-phase-removal claims (§5.3 S-14(e), §6.3 E-MEM, §7.2 footprint,
§8.3 T-C16, QC-2 Verification) now carry this qualifier (adv-c10 F-01)),
D-54 (§4.5 KI-AT-OPEN classification — a
KeyboardInterrupt raised BY the `open()` call itself, fd never bound,
is an AT-OPEN failure: no compensation runs; the kernel's O_TRUNC may
already have left a pre-existing target at 0 bytes, the accepted
residue R-6 (§10.1); the fd-binding point is the only observable
trigger boundary — whether O_TRUNC was applied is unobservable from
Python without extra syscalls/imports; closes adv-c9 F-02; bound also
in §4.5, §7.1 partial-failure sentence, §7.2 footprint sentence, §8.3
T-C8, QC-2 Scope, §10.1
R-6, §12 glossary "successful open"; v11: R-6's residue bound widened
to BOTH flavors of the same window — a pre-existing target truncated
to 0 bytes, an absent target CREATED empty (adv-c10 F-04)), D-55 (§6.4/§9 — the success row
and NFR-004's stdout/stderr rows scope to REGULAR-FILE output paths: a
character-device output (`/dev/stdout`, `/dev/stderr`, `/dev/null`,
`/dev/fd/N`) is opened/written/flushed/closed at exit 0 with the
document on that device — the documented consequence of the caller's
own redirection; forbidding non-regular targets was rejected: new
error class outside the CLOSED catalog (D-42) plus stat machinery no
REQ mandates; closes adv-c9 F-03; bound also in §6.1 form + stdout
rows, §9 NFR-004 row, §8.2 T-K3, §11 NFR-004 row), D-56 (§4.5/§10.1 —
two residue-bound folds, one mechanism each already recorded: (a) the
D-53 arm-abort class — its non-OSError form, explicitly a SECOND
MemoryError inside the failure arm, interrupting the compensation the
same way a second KI does (live-probed: appendix/47 P1a — partial file
PRESENT at the E-MEM write-phase stderr line; control P1b single
MemoryError removes it, P1c honest-negative RLIMIT_AS sweep) — is
folded into every absolute write-phase-removal claim: §5.3 S-14(e),
§6.3 E-MEM row, §7.2 footprint sentence, §8.3 T-C16, QC-2
Verification; closes adv-c10 F-01; (b) R-6's residue bound is widened
from pre-existing-truncated to BOTH flavors of the same KI-at-open
window: a PRE-EXISTING target may be left truncated to 0 bytes AND an
ABSENT target may be left CREATED at 0 bytes (the kernel applies
O_CREAT|O_TRUNC, the signal strikes before `fd` binds, the arm sees
`fd is None` and runs no compensation — §4.5 KI-AT-OPEN paragraph,
QC-2 Scope, §7.2 footprint sentence carry the create flavor); closes
adv-c10 F-04; no new mechanism, no new residue — the recorded windows
are unchanged, only the five absolute claims and the one mis-scoped
bound are corrected). No
decision is unbound;
none is reinterpreted. (v11: fixed all four adversarial-early cycle-10
findings (appendix/45-adv-c10.md, probes appendix/45b; the
spec-review#9 gate card is an ARCHIVED STALE TWIN with no board result
and no findings artifact, so this revision cites no spec-review
verdict — the SR7-F-01 phantom-cite rule, board-verified via
appendix/46-board-query-c10.py; adv-early#10's FAIL verdict and
findings file ARE board-verified and cited). New decision D-56 folds
adv-c10 F-01 (P1) and F-04 (P2): F-01 — D-53's arm-abort class is ANY
non-OSError, so a SECOND MemoryError inside the failure arm aborts the
compensation exactly like a second KI (R-5's own wording already
covers it: "(or any non-OSError)"); the five absolute
write-phase-removal claims — §5.3 S-14(e) "the file is GONE", §6.3
E-MEM "so no partial file survives", §7.2 "the target removed", §8.3
T-C16 "no conforming mechanism can leave it present", QC-2
Verification's write-phase path-absent assertion — each gain the
explicit "unless the compensation itself is aborted per D-53/R-5
(second KI or second MemoryError)" qualifier; §7.1's taxonomy
partial-failure sentence gains the same clause. F-04 — R-6's residue
bound is widened from "bounded to pre-existing targets" to BOTH
flavors of the KI-at-open window: a pre-existing target truncated to
0 bytes OR an absent target CREATED at 0 bytes (§10.1 R-6 body and
Impact, QC-2 Scope's exception enumeration, §4.5's KI-AT-OPEN
paragraph, §7.2's footprint sentence, and the §11 D-54 index entry
carry the create flavor). adv-c10 F-02 (P2): D-55's regular-file
scope note is added to the two stderr-side statements it missed —
§6.1's stderr row and §12's "silent success" glossary row (mirroring
the stdout row's parenthetical; live probe appendix/47 P2a/P2b
re-verifies the /dev/stderr and /dev/stdout outcomes). adv-c10 F-03
(P3): §1's enumeration refreshed to D-01..D-56 (the v10 header had
claimed the §1 refresh but left it at D-01..D-52). New probes:
appendix/47-rev11-adv10-folds-probes.py (re-run of 45b's six checks
against spec/11-spec-v11.md, all PASS, plus the five-site fold-check
greps and the R-6 create-flavor textual check). Section numbering
unchanged from v10. v10: D-53 appended for the adv-c9 F-01
disposition — the D-51 compensation outcome re-scoped to a
SINGLE-KeyboardInterrupt contract conditional on the failure arm
running to completion, the double-KI residue recorded as R-5, the
KI-resistant-arm alternative rejected on NFR-001's pinned import set;
D-54 appended for the adv-c9 F-02 disposition — a KI raised by
`open()` itself classified as an AT-OPEN failure with the 0-byte
residue recorded as R-6, the O_TRUNC-observability rationale stated;
D-55 appended for the adv-c9 F-03 disposition — §6.4/NFR-004's
stdout/stderr rows scoped to regular-file output paths, the
character-device outcome documented as the caller's own redirection;
§4.5 compensation bullet + reference-shape note + mutation rows
9/10/11/13, §6.4 signal note + success row + stderr cell, §7.1
partial-failure and timeout-cancellation clauses, §7.3, §8.2 T-K3,
§8.3 T-C8, QC-2 Scope/Mechanism/Verification, §11 REQ-010 and
NFR-004 rows, §10.1 R-5/R-6, and the §12 glossary rows aligned;
F-04's encoding-scope note added to §6.3/§6.4/§12; F-05's E-NET
`<in>` clause added to the §6.3 enumeration; §1 enumeration refreshed
to D-01..D-55. v9: D-51 appended for the adv-c8 F-01
disposition — the KeyboardInterrupt window is inside the D-48/D-50
compensation contract; §7.1's kill-note scoped to uncataloged kills
(SIGKILL/SIGTERM-default), §7.3's pass-through qualified to main's
handler chain, a signal note added to §6.4, and the §4.5 compensation
bullet, mutation row 9, QC-2 Scope/Mechanism/Verification and T-C8
extended to the KI class; D-52 appended for adv-c8 F-02 — the §4.1
argparse alternative retracted, §6.1 flags row, §9 NFR-001 row, §11
REQ-001 row and the D-49 coverage clause aligned; the §11 coverage
sentence refreshed to D-01..D-52 per adv-c8 F-03; the §6.3 verbatim-slot
enumeration gained the `<path>` slots and T-K1 a path-form
parametrization (adv-c8 F-04); the body's appendix/29b cites re-aimed
to appendix/30b with historical annotations and appendix/25 M1
annotated historical (SR7-F-03); the D-50 binding-site lists corrected —
T-C16 and the §11 REQ-010 row now carry D-50 (SR7-F-04); the v8
header's phantom adversarial-early-cycle-7 PASS clause retracted per
SR7-F-01 — the gate was reclaimed mid-run with no verdict artifact;
§1 enumeration refreshed to D-01..D-52. v8: D-50 appended for the SR6-F-01 disposition —
the failure-arm close-before-remove ordering; register rows D-43/D-46/D-48
refreshed to the live shape per D-32's hygiene rule (SR6-F-02); T-C16's
"(or byte-identical)" slack deleted (SR6-F-04); header probes row annotates
25/28 as historical since the rollover (SR6-F-03); §4.5 op-order (3) reworded
to the manual close (SR6-F-05); §5.1 pre-open-encode edge relabeled "nothing
open — filesystem untouched" (SR6-F-06); R-4 rationale tautology demoted
(SR6-F-07); §1 enumeration refreshed to D-01..D-50; section numbering
unchanged from v7. v7: D-48/D-49 appended for the adv-c6
F-02/F-05 dispositions; R-4 appended to §10.1 for adv-c6 F-03;
§1 enumeration refreshed to D-01..D-49. v6: D-45/D-46/D-47 appended for the adv-c5
F-01/F-04/F-02 dispositions; §1 enumeration refreshed to D-01..D-47.
v5: D-44 appended for the SR3-F-01 disposition;
§1 enumeration refreshed to D-01..D-44 per SR3-F-02.
v4: D-43 appended for the F-01/F-02 disposition;
v3, SR1-F-03: enumeration refreshed from the
stale D-01..D-36 and D-38..D-42 now bound explicitly; cite-the-register
rule unchanged.)

# 12. Glossary

Consistent with the requirements glossary (REQ §8); terms are restated
with their implementation binding. Wording here is normative for the code.

| term | definition (implementation binding) |
|---|---|
| stdlib default dialect | Python `csv` module defaults: delimiter `,`, quote `"`, doubled-quote escape; blank line → 0-field record; lenient unclosed quote (tightened to E-UQ by REQ-013). Operative definition for `parse`. |
| record / logical row | One iteration of `csv.reader`; may span several physical lines. Identifier prefix `record*`. |
| physical line | 1-based line of the decoded text; breaks are exactly `\n`, `\r\n` (one), bare `\r`; VT/FF/NEL/U+2028/U+2029 are data. Same basis as D-28. Computed by the tool's offset arithmetic, never `reader.line_num` (ADR-2). |
| blank physical line | Zero characters between terminators → 0-field record → E-COUNT `found 0` (after header). Never tested via `strip()`. |
| whitespace-only line | One-or-more space/tab characters → ordinary 1-field data row, value verbatim (D-36). |
| field value | One parsed cell (`str`), data only; verbatim into the output object (REQ-005). |
| output object | `dict` mapping header names (verbatim, insertion-ordered) to field values. |
| compact JSON | `json.dumps(..., ensure_ascii=False, separators=(",", ":"))` + one trailing `\n` — the §6.2 byte contract. |
| newline='' semantics | The `io.StringIO(text, newline="")` construction of §4.3.1 — no newline translation between decode and parse (REQ-014/D-24). |
| unterminated quoted field | A record whose text ends while the FSM is in QUOTED (§4.3.3) — the E-UQ error with N (row-start line) and M (opening-quote line). Scope covers the whole input INCLUDING the header (D-25); on the header record the scan runs after the header rules (§4.3.2 order, S-9b). A `"` in an unquoted field is never this (data, D-30). |
| row-start line / opened-at line | N = `line` at the record's start offset; M = N + record-relative opening line − 1, where the record-relative counter uses the D-28 basis (a `\r\n` pair or a bare `\r` or a `\n` each advance it by ONE, §4.3.3 counting rule) — so M is the physical line of the opening quote even when CRLF sits inside an earlier quoted field (S-10b). |
| lossless | Every input cell's exact text appears unchanged in the JSON output: no coercion, trimming, newline rewriting, or replacement (Q-01/D-11). |
| error catalog | The closed E-* message set of §6.3; every failure prints exactly one catalog message (one stderr write, no tool-added extra newline; a data-borne break inside ANY interpolated slot — E-DUP `<name>`, E-NET `<exception repr>`, OS `<strerror>` — may wrap it physically — §6.3 E-DUP note). The verbatim rule binds the MESSAGE STRING the tool hands to that single stderr write; the BYTES observed on the wire additionally depend on the interpreter's stderr encoding — default CPython stderr preserves UTF-8 verbatim, while environment-overridden encodings (`PYTHONIOENCODING`) may transliterate or make the write itself raise (outside the tool's control, same class as R-3's closed-stream boundary). |
| silent success | Exit 0 with empty stdout and the output file written — for REGULAR-FILE output paths (Q-02/D-11b); with a character-device output the document is written to that device at exit 0 and no file appears (D-55 — the caller's own redirection choice). |
| successful open (compensation trigger basis) | The state in which `open(path, "wb")` has RETURNED a file object — only exceptions raised from that point on trigger the D-33 remove (D-46). An open that itself raised never held the file, so no remove runs; this includes a KeyboardInterrupt raised BY the open call (D-54): the KI-at-open class is an at-open failure even when the kernel has already applied O_TRUNC before the signal struck — the fd-binding point is the trigger basis, and the 0-byte residue that state can leave is accepted-risk R-6 (§10.1), not a compensated outcome. |

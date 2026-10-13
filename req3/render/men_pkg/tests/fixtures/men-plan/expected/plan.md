# Implementation Plan: I need a small command-line tool: csv2json.

**Branch**: `i-need-a-small-command-line-tool-csv2js` | **Date**: 2026-09-20 | **Spec**: req-lab spec v16 (APPROVED)

**Input**: Feature specification `spec.md` (spec_version 7, CSV2JS-1)

## Summary

**Goal.** Provide a small, dependency-free command-line tool `csv2json` that
converts a CSV file with a header row into a JSON array of objects, one object
per data row, keyed by the header names. All field values are carried through
losslessly as JSON strings, in compact JSON, with silent success.

**Success condition.** A user runs
`python csv2json.py input.csv output.json`;
`output.json` contains a valid, COMPACT (single-line, no indentation) JSON
array in which each element maps header names to that row's field values as
JSON strings — `"42"` stays `"42"`, an empty cell becomes `""` (never `null`);
non-ASCII text appears as raw UTF-8 characters, never `\uXXXX` escapes
(Q-06 → D-17); rows with a field count different from the header produce a
clear error naming
the line number, and the tool exits with status 1 (the two-valued exit
contract, §3.1/REQ-001); a successful run
prints nothing to stdout; no third-party packages are required.

**Source requirement (verbatim, from appendix/00-intake.md):**

> I need a small command-line tool: csv2json. It reads a CSV file (with a header row), converts each data row into a JSON object keyed by the header names, and writes the result as a JSON array to an output file. Must handle quoted fields containing commas, and report a clear error (with line number) when a row has a different number of fields than the header. Single-file Python script, stdlib only, run as: python csv2json.py input.csv output.json

## Technical Context

**Language/Version**: NFR-002 — target runtime: Python 3.9 or newer. The floor is a CONTRACT, not a freedom (F-07: v3's "exact floor is implementor freedom" clause is deleted — it contradicted the acceptance criterion below; register D-07 updated accordingly): observable behavior must be identical on every supported version. *Acceptance:* the script imports and runs on Python 3.9.
**Primary Dependencies**: NFR-001 — zero dependencies: The tool runs with the Python standard library only. No pip installs, no third-party imports, no build step. *Acceptance:* `grep` of the script shows imports only from the stdlib; the tool runs on a bare Python installation.
**Testing**: test suites recorded in the req-lab spec traceability matrix: T-C-series, T-U-series (tests are specified, not run, at this stage)
**Storage**: not pinned as a distinct field; data entities and formats are specified verbatim in spec.md (Key Entities, Data Formats)
**Target Platform**: not pinned as a distinct field in the req-lab artifacts
**Project Type**: not pinned as a distinct field in the req-lab artifacts; see Summary for the deliverable shape
**Performance Goals**: NFR-003 — performance envelope: A 50 MB CSV (~250k rows) converts in under 30 seconds and under 1 GB RAM on a typical laptop. In-memory processing is acceptable below this envelope; larger files are out of scope (§3.2). *Acceptance:* documented test with a generated 50 MB file completes within the limits (spot check, not a hard gate).
**Constraints**: out-of-scope commitments are listed verbatim in requirement.json `out_of_scope` (9 items) and spec.md's Out of Scope section
**Scale/Scope**: 14 functional (REQ-001..REQ-014); 5 non-functional (NFR-001..NFR-005) — the full list is in spec.md's Requirements section

## Project Structure

The req-lab spec does not prescribe a repository layout; its structural design is carried by the architecture Design Elements: DE-1 (spec §2.1), DE-2 (spec §2.2), DE-3 (spec §2.3), DE-4 (spec §2.4).

## Design Elements

- **DE-1 — Component diagram (text form)** (spec §2.1)

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

  Backs: AC-6, AC-10, AC-11, AC-14

- **DE-2 — Component responsibilities** (spec §2.2)

  | component | responsibility | REQ anchors |
|---|---|---|
| `main(argv)` | dispatch exactly-two-positional-args; run the pipeline; catch the typed error hierarchy; print one REQ-007 message to stderr; exit 0/1 | REQ-001, REQ-007, REQ-008, D-34, NFR-004 |
| `read_raw` | read the whole input file as bytes; map OS errors to the error contract | D-15 (2), REQ-007 |
| `decode_utf8` | strict UTF-8 decode of the whole byte string; strip one leading BOM; locate an invalid byte at a D-28 line | REQ-011, REQ-012, D-13/D-16/D-23/D-28 |
| `parse` | hand the text to `csv.reader` with `newline=''` semantics; iterate record by record; header rules first on record 1 (0-field, duplicates — D-15 slots (4)/(5)), then the per-record unterminated-quote scan (slot (6), header scope included), then per-row count validation; build the list of dicts | REQ-014, REQ-002/003/004/006/009/013, D-15/D-24/D-25/D-29/D-30/D-31/D-36 |
| `serialize` | `json.dumps(rows, ensure_ascii=False, separators=(",", ":"))` + one trailing `\n` | §5.2, D-11b/D-14/D-17/D-20/D-26 |
| `write_output` | encode the document to UTF-8 bytes FIRST (D-43 — before the path is touched); open the output path for binary write; write the payload; flush; on ANY exception raised after a SUCCESSFUL open (OSError or otherwise, D-46) remove the partial file best-effort, then report — OSError per the REQ-007 shape naming the output path, MemoryError per E-MEM's write-phase form | REQ-010, D-33/D-35/D-43/D-46 |

  Backs: AC-15

- **DE-3 — ADR-style decisions (each: decision → rationale)** (spec §2.3)

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

  Backs: AC-7, AC-10, AC-13, AC-14

- **DE-4 — What is deliberately absent** (spec §2.4)

  No config files, no options/flags beyond the two positional args, no stdin/
stdout I/O, no dialect sniffing, no streaming for oversized files, no type
inference, no logging (silent success is the contract), no Windows-specific
code paths beyond avoiding newline translation (D-35 is platform-neutral).
Out-of-scope per REQ §3.2; the implementor adds none of these.

  Backs: —

- **DE-5 — Entities** (spec §3.1)

  | entity | type in the implementation | constraints / invariants |
|---|---|---|
| Input CSV | bytes on disk → `bytes` → `str` (decoded) | must be strict UTF-8 (REQ-011); one optional leading BOM (REQ-012); first parsed record is the header (REQ-002) |
| Header row | `list[str]` (parsed once) | length ≥ 1 (REQ-009); names unique (REQ-002/D-12); empty name allowed once (REQ-002/F-33); used verbatim, no trimming/case-folding |
| Data row | `list[str]` (parsed) | `len(row) == len(header)` exactly (REQ-006); `len >= 1` always true for parsed non-header rows (a blank line parses to 0 fields and errors per REQ-009) |
| Field value | `str` | data only, no semantics assigned (D-05/NFR-005); carried verbatim into JSON (REQ-005/D-11); control characters are data (D-14) |
| Output JSON | `str` (one `json.dumps` call) → bytes UTF-8 written binary | compact single line; ends `]\n` byte-exact on every platform (D-26/D-35); array of flat objects in input row order (REQ-003/D-06) |
| Physical line | derived: count of D-28 breaks before an offset, + 1 | breaks are exactly `\n`, `\r\n` (ONE), bare `\r`; VT/FF/NEL/U+2028/U+2029 are data (D-28) |
| Record span | `(start_offset, end_offset)` per parsed record, in decoded-text code points | obtained from the reader file's `tell()` around `next()`; exact, no read-ahead (probe P1); basis for all row-start line numbers |

  Backs: AC-2

- **DE-6 — Ubiquitous language (deltas and bindings for the implementor)** (spec §3.2)

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

  Backs: AC-7, AC-13

- **DE-7 — CLI shell — `main(argv)`** (spec §4.1)

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

  Backs: AC-1, AC-18

- **DE-8 — Decode stage — `read_raw`, `decode_utf8`, line arithmetic helpers** (spec §4.2)

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
  §4.3.2, which shares this exact definition via `count_line_breaks`),
  so no stage may count a terminator pair as two breaks. The
  record-relative
  FSM counter of §4.3.3 is the same arithmetic restricted to the record's
  own span (SR1-F-01 fix: the QUOTED row of that FSM's table previously
  advanced once per `\r` and once per `\n`, splitting CRLF; it now
  collapses CRLF and counts bare CR as one, exactly as here).
  Binding note (D-59 mirror — the site adv-c14 F-04 found promised but
  missing): the per-record walk inside the parse stage is the stage-cost
  measurement D-59 binding-controls — any stage-cost number the spec
  cites for it names its CPython name binding per D-59 (see §8.3 T-C9).
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

  Backs: AC-11, AC-12, AC-19

- **DE-9 — Parse stage — `parse(text)` (the deep core)** (spec §4.3)

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
  CONFORMING FUSION (D-58, closes adv-c11 F-02): the FSM and the break
  count may be computed in ONE fused pass — a single scan of
  `record_text` that advances the counter exactly where the normative
  rule above advances it (the D-28 collapse), transitions the FSM
  exactly where the table transitions it, and remembers the opening
  line from that same counter AT EVERY FIELD_START→QUOTED transition
  (the table's row — so the remembered line on a record ending QUOTED
  is the UNCLOSED field's opening quote, exactly what S-10/T-U3/T-C7
  pin as M; a doubled-quote re-open is CLOSED→QUOTED and does NOT
  re-remember). The two-quantity wording above and the
  fused single pass produce IDENTICAL observables (state at end of
  span, opening line M, per-record break count) — the outcome-identity
  WITH THE NORMATIVE (N, M) is asserted live over an extended
  13-corpus family (the six S-10/T-C7 members plus seven
  discriminators, including a re-open-ON-A-LATER-RECORD-RELATIVE-LINE
  corpus no earlier corpus discriminated) by
  appendix/77-rev15-shape-identity.py, which builds BOTH shapes for
  real — a two-quantity form (table-latch FSM pass + separate D-28
  break pass) and a fused single pass — and compares their per-record
  outcomes (adv-c14 F-01's closure: it supersedes the vacuous
  self-comparison that appendix/66-rev14-binding-timing.py Part B
  executed under the same claim, where `tq` and `fu` were the same
  call; battery 77's T1/T2 pins that defect mechanically; 66 Part B's
  NORMATIVE-N/M assertions and its first-latch demonstration remain
  valid and cited) (M=3 on all
  three S-10 multi-quote forms, M=2 on T-C7's single-quote form; the
  same probe demonstrates that the LEGACY first-quote latch shared by
  appendix/51 B3 and appendix/55h computes M=2 where the table computes
  M=3, which is why B3's shape-vs-shape agreement could not certify the
  M observable — B3 remains cited for what it proves: per-record break
  count and end-state identity between the two shapes; T-U3/T-C7 are
  the M authority); neither form is
  required, either is conforming, and this is purely an
  implementation-shape latitude with NO behavior change (a build may
  still keep `count_line_breaks` as a separate helper for the
  decode-stage counter — D-38/§4.2 are unchanged; the latitude is
  scoped to the per-record scan of §4.3.2/§4.3.3).

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

  Backs: AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, AC-9, AC-13, AC-14, AC-17

- **DE-10 — Serialize stage — `serialize(rows)`** (spec §4.4)

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

  Backs: AC-3, AC-5

- **DE-11 — Write stage — `write_output(path, document)`** (spec §4.5)

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
  **At-open MemoryError joins this class (D-57, closes adv-c11 F-01).**
  A MemoryError raised by the open call itself (fd never bound) is
  classified by the SAME observable as the KI-at-open form: the arm
  runs NO compensation, the run reports E-MEM's write-phase form via
  the residual net (§6.3), and the kernel-applied O_CREAT|O_TRUNC can
  leave the same two 0-byte flavors — so R-6's trigger reads "KI or
  MemoryError at open" from this revision on. The D-54 rationale is
  verbatim D-57's: fd-binding is the only observable boundary, and a
  "compensate whenever the kernel may have mutated the inode" rule has
  no conforming detection mechanism.
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
  MEANS after a SUCCESSFUL open only (D-46): an at-open failure — the
  open itself raising, whether OSError or MemoryError (D-57) — reports
  directly with NO compensation, and a pre-open
  encode failure (D-43) never reaches this stage's wrap at all. There
  is no retry loop, no temp-file rename, no fsync requirement (none is
  pinned by any REQ; flush covers the D-33 surface).
  AT-OPEN MEMORYERROR STATE (D-57, closes adv-c11 F-01): unlike the
  OSError at-open forms, a MemoryError raised by the open call itself
  can strike AFTER the kernel has already applied O_CREAT|O_TRUNC — the
  raw fd exists for a moment, CPython's cleanup closes it, and the
  wrapper raises before `fd` binds — so an ABSENT target may be left
  CREATED at 0 bytes and a PRE-EXISTING target truncated to 0 bytes,
  exactly the two flavors of the KI-at-open window (live:
  appendix/51-rev12-adv11-folds-probes.py B1/B2, reproducing the
  reviewer's appendix/48b P2a/P2b on the identical fault). The run's
  observable outcome is unchanged — E-MEM's write-phase form, exit 1 —
  and the state residue is the SAME accepted-risk record R-6 (§10.1,
  trigger widened to "KI or MemoryError at open" by D-57); the
  byte-untouched phrasing of the preceding sentence holds for the
  OSError at-open forms, and for MemoryError is superseded by this
  paragraph at exactly this boundary.
- **Mutation contract (the 13 questions) for this stage** — the only
  state-mutating operation in the tool:

| # | question | answer |
|---|---|---|
| 1 | who may call it | whoever can execute the script and write to the target path (single-user CLI; REQ §2 — no auth layer exists) |
| 2 | input & validation contract | `path: str`, `document: str` ending `]\n`; no path validation beyond what `open()` enforces |
| 3 | where preconditions are enforced | output path is only touched AFTER `parse` returned successfully (REQ-010 phase split, D-15 slot 7); since D-43 the encode step also runs BEFORE the open, so even a MemoryError during encode cannot touch any output path; writability is discovered by `open()` itself; an at-open failure ends the stage with the target untouched for the OSError forms (D-46 — no compensation runs because nothing was opened); an at-open MEMORYERROR (D-57) is the recorded exception to "untouched" — the kernel may already have applied O_CREAT|O_TRUNC before `fd` bound, leaving the R-6 0-byte residue (§10.1) |
| 4 | where mutation occurs | this stage exclusively: one encode (no side effect), then one `open(path, "wb")`, one write, one flush — the first filesystem-touching call is the open |
| 5 | source of truth | the in-memory `document` string produced by `serialize`; the file is a projection of it |
| 6 | all-or-nothing boundary | one file; the encode-before-open order (D-43) means every pre-open failure leaves the target byte-untouched, and at-open failures (D-46) leave it byte-untouched for the OSError forms — the at-open MemoryError (D-57) is the recorded R-6 exception (kernel O_CREAT|O_TRUNC, 0-byte residue, §10.1); after a successful open, best-effort in-place write with the every-exception delete-on-failure compensation — no cross-file all-or-nothing property is required or provided (single invocation, no concurrent readers in scope) |
| 7 | on retry | re-running the tool re-executes from scratch; a successful rerun overwrites/truncates the target; a failed run left no file — or, on an at-open failure (D-46), left the prior target byte-identical — so retry is clean (an at-open MemoryError's R-6 0-byte residue, D-57, is also cleaned by a successful rerun) |
| 8 | on duplicate call | same as retry — the tool has no session; "duplicate" means the user ran it again; last successful run's bytes define the file (REQ §5.1: successful run REPLACES the file entirely) |
| 9 | when two runs overlap in time | out of scope by REQ §2 (single-user, single-invocation); no locking is provided; interleaved runs can lose BOTH outputs — a failed run's compensation can unlink the file name a concurrent successful run wrote, leaving a silent exit-0 run with no file at all — and no ordering property is promised; recorded as an accepted scope boundary, not a promised property (see §10.1 R-2). WITHIN one run, signal-delivered KeyboardInterrupt during the post-open window is IN scope (D-51) with the SINGLE-KI scope of D-53: one KI strikes and the BaseException failure arm runs to completion (close per D-50, remove) before the KI re-raises — an interrupted run leaves no partial target; a SECOND KI landing INSIDE the arm interrupts the compensation and the partial target SURVIVES as accepted residue R-5 (§10.1); a KI raised BY `open()` itself is the D-54 at-open class — no compensation, 0-byte residue R-6 possible (§10.1; per D-57 a MemoryError raised by the open call itself lands in the SAME at-open class with the same R-6 residue). The out-of-scope kill forms (SIGKILL, SIGTERM-default) remain ones no handler can observe |
| 10 | state remaining after mid-op failure | pre-open failures (encode MemoryError per D-43; at-open OSError per D-46): target byte-untouched whether absent or pre-existing. AT-OPEN MEMORYERROR (D-57): the one at-open state that is NOT byte-untouched — the kernel may already have applied O_CREAT|O_TRUNC before `fd` bound, so an absent target may be left CREATED 0-byte or a pre-existing target TRUNCATED 0-byte (accepted residue R-6, §10.1). Post-open failures: the partial file is removed best-effort for EVERY exception class — on EVERY PLATFORM in the conformance domain, because the failure arm closes the fd before the remove (D-50; without that ordering Windows raises PermissionError on the open handle and a best-effort clause would leave the partial file); if removal itself fails (rare), the error already reported stands and exit is 1 (REQ-010 wording); under an aliased target the R-1b residue (§10.1) is possible. KI-WINDOW states (D-53/D-54/D-57): a SECOND KI inside the failure arm aborts the compensation mid-flight — the partial file SURVIVES (accepted residue R-5, §10.1); a KI raised by `open()` itself (fd never bound, D-54) runs no compensation — a pre-existing target may be left 0-BYTE by the kernel's O_TRUNC, and an absent target left CREATED 0-byte (accepted residue R-6, §10.1, both flavors; D-57 adds the MemoryError trigger to the same window); all are recorded accepted residues of an unprotectable window, not contract failures. SAME-PATH invocation (output path == input path): the post-open compensation's remove can delete the caller's INPUT file (open truncated it, the failed run removes it) — accepted-risk R-4 (§10.1); a successful same-path run replaces the input with the output by S-1's replace semantics |
| 11 | rollback/compensation | exactly D-33's mechanism (best-effort `os.remove`, failures ignored), triggered by every exception raised after a SUCCESSFUL open (F-01 disposition — not OSError-only; at-open failures excluded per D-46, including the at-open MemoryError per D-57 — fd never bound, the arm never runs); the failure arm's ordering is close-the-fd (best-effort) THEN remove (D-50 — without it the remove fails on Windows while the handle is open and the partial file survives); the compensation is itself best-effort and KI-interruptible (D-53: a second KI inside the arm aborts it mid-flight, leaving R-5's partial-file residue; the D-54/D-57 at-open class never reaches the arm — fd None, no remove, R-6's 0-byte residue possible) |
| 12 | caller/user learning of failure | one `csv2json: error: cannot write <path>: <strerror>` line on stderr for OSError failures (via `main`); MemoryError per §6.3's E-MEM write-phase form `out of memory writing <path>` — including the at-open MemoryError, whose phase form is the same write-phase form while no compensation ran (D-57, §6.3); exit 1 either way; nothing on stdout (NFR-004) |
| 13 | proving test | §8 contract tests: `/dev/full` write-failure case (open succeeds, flush raises), non-writable-dir case AND pre-existing read-only target case (both at-open failures: E-WRITE, target byte-untouched — D-46; the non-writable-dir sub-case and the read-only sub-case skip as root, where DAC_OVERRIDE defeats mode 0555 dirs and mode 444 files alike — T-C2's convention, adv-c11 F-03), invalid-input/no-file-created case, byte-exact success case, pre-existing-output cases (T-C8: prior bytes survive an encode-phase MemoryError; T-C16: RLIMIT_AS fault injection, no partial output; the `/dev/full` and mid-write cases pin the D-50 close-before-remove failure-arm ordering — a shape that removes while the fd is open is non-conforming (the ordering is why the Windows remove-while-open failure mode cannot occur)); the aliasing case (symlink target) is documented assert-or-accept in T-C8's matrix (R-1b), as are the double-KI residue (R-5) and the at-open 0-byte residue for KI or MemoryError (R-6, D-54/D-57) — real filesystem, no mocks (infra behavior is never certified mock-only) |

  Backs: AC-10

- **DE-12 — Startup limit raise (NFR-005/D-21/D-27)** (spec §4.6)

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

  Backs: AC-19

- **DE-13 — Run-level state machine (states of one process invocation)** (spec §5.1)

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
WRITE_OUTPUT ── MemoryError(pre-open encode: nothing open — output path untouched) ──► REPORTING(memory) ─► exit 1
WRITE_OUTPUT ── MemoryError(at-open: fd never bound — NO compensation, D-57; 0-byte residue R-6 possible, both flavors) ──► REPORTING(memory) ─► exit 1
WRITE_OUTPUT ── MemoryError(post-open: after compensation) ──► REPORTING(memory) ─► exit 1
  (at-open OSError edge: NO compensation — reports directly, D-46, target
  byte-untouched; the at-open MemoryError edge above shares the no-compensation
  classification but NOT the byte-untouched clause — the kernel's O_CREAT|O_TRUNC
  may already have mutated the target before fd bound, D-57/R-6; the
  failure-position contract lives in §4.5, which this diagram summarizes)
  ▼ WRITTEN
exit 0  (stdout silent)
```

REPORTING prints exactly one stderr line and nothing else. The output file
can exist only after WRITTEN; every path into REPORTING leaves the
output-side byte-state untouched EXCEPT the recorded at-open residue
(R-6, D-54/D-57: the kernel may already have applied O_CREAT|O_TRUNC
before `fd` bound) — §4.5's compensation remains the one cleanup, and the
at-open exception is record-don't-contract, not a compensation path.

  Backs: AC-8

- **DE-14 — Parse-loop micro-states (inside PARSE)** (spec §5.2)

  `AWAITING_HEADER` → on first record: header rules FIRST (0-field check →
duplicate check — D-15 slots (4)/(5), §4.3.2's pinned order) →
`HEADER_VALIDATED` → then the record's FSM quote scan (slot (6), scope
covers the header per D-25; on a combined defect the duplicate error wins,
S-9b) → `IN_DATA` → per record: FSM scan → count check → row appended.
`IN_DATA` until StopIteration → `PARSE_OK`.
Any check failure raises straight out of PARSE (REPORTING(field)).
The FSM's own four states (FIELD_START/UNQUOTED/QUOTED/CLOSED, §4.3.3) are
re-created per record and never leak across records.

  Backs: —

- **DE-15 — Scenario walk-throughs (every REQ-identified scenario, with failure paths)** (spec §5.3)

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
truncated (probe W1/W2 evidence class, appendix/21b + 22); (f) a
MemoryError striking the open call itself (fd never bound, D-57,
closes adv-c11 F-01): the arm runs NO compensation and the E-MEM
write-phase form is reported, exit 1 — but the kernel may already have
applied O_CREAT|O_TRUNC before the wrapper raised, so an ABSENT target
may be left CREATED at 0 bytes or a PRE-EXISTING target truncated to
0 bytes; that residue is R-6 (§10.1, trigger "KI or MemoryError at
open" per D-57) — the same window and record as the KI-at-open class,
live-probed at appendix/51-rev12-adv11-folds-probes.py B1/B2; if the
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

  Backs: AC-8, AC-13

- **DE-16 — CLI invocation contract (REQ-001/D-34)** (spec §6.1)

  | aspect | contract |
|---|---|
| form | `python csv2json.py <input.csv> <output.json>` — exactly two positional args, input first, output second; the output path is used exactly as given — no type check is performed (D-55: a character-device or other non-regular openable target such as `/dev/stdout` is opened, written, flushed, closed like any other path, and the document appears on that device) |
| arg count ≠ 2 | stderr `csv2json: error: usage: csv2json.py <input.csv> <output.json>`; exit 1; no file created |
| exit codes | 0 on success; 1 on EVERY failure (usage, read, decode, parse, write, memory, residual) — two-valued, no exit 2 anywhere |
| stdout | empty on success; empty on failure (errors go to stderr) — the success row scopes to REGULAR-FILE output paths (D-55: with output `/dev/stdout` the DOCUMENT is written to that device by the caller's own redirection choice, exit 0; the tool itself performs no stdout write on any path) |
| stderr | empty on success — FOR REGULAR-FILE output paths; with a character-device output (`/dev/stderr` etc.) the DOCUMENT itself lands on that device at exit 0 (D-55, the caller's own redirection — the success-side statements in §6.4/§9/T-K3 carry the same scope); on a regular-file run it is exactly one error message per failed run — the tool adds no newline beyond the message's terminating one and emits no second message; data-borne breaks inside ANY interpolated slot (E-DUP `<name>`, E-NET `<exception repr>`, OS `<strerror>`) may wrap it across physical lines (§4.1 F-03 note, §6.3) |
| flags/options | NONE accepted. `-h`/`--help` are out of scope (REQ §3.2: no named options); as positionals they are ORDINARY PATH STRINGS — the manual dispatch's outcome is normative for ALL argv of length 2: E-READ on `-h out.json`, exit 1, nothing on stdout (D-49). On argc ≠ 2 (e.g. `csv2json.py -h` alone) the usage branch reports the prefixed usage line on stderr with exit 1 — help text NEVER reaches stdout on any argv (NFR-004; the manual dispatch is the ONE conforming shape, D-52 — an argparse build's default help action prints help to stdout and exits 0, which is non-conforming on this argv class too; adv-c6 F-05, adv-c8 F-02) |
| environment | no env vars read; locale-independent (decode/encode are explicit UTF-8; no `open()` default-encoding dependency anywhere) |

  Backs: AC-1

- **DE-17 — Output document contract (§5.2 REQ, D-11b/D-17/D-20/D-26/D-35)** (spec §6.2)

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

  Backs: AC-2, AC-3, AC-5, AC-6, AC-9

- **DE-18 — Error message contract (REQ-007/D-22; message catalog)** (spec §6.3)

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
| E-MEM | any phase, MemoryError | read phase: `csv2json: error: out of memory reading <in>`; parse phase: `csv2json: error: out of memory while converting <in>`; serialize/write phases: `csv2json: error: out of memory writing <out>` (NFR-005: a MemoryError during the output write/serialize is reported like any other write-time failure — the OUTPUT path named, D-33/D-44: serialize and write therefore share the ONE output-named form; there is no input-named serialize form. Write-phase placement per D-43: the encode runs BEFORE the open, so a MemoryError at encode touches no output path; a MemoryError after the open first triggers the D-33 compensation, so no partial file survives — §4.5 — UNLESS the compensation itself is aborted per D-53/R-5: a second MemoryError (or second KI) landing inside the failure arm aborts the best-effort remove mid-flight and the partial file PRESENT is the recorded residue (decision D-56(a), adv-c10 F-01; probe appendix/47 P1a — partial PRESENT with this phase form on stderr; control P1b — single MemoryError, file removed). Serialize phase per D-44: nothing is open yet, so the filesystem is simply untouched — no compensation applies. One further placement for this form: an at-open MemoryError (D-57) reports this write-phase form while the compensation has NOT run — the open itself raised after the kernel applied O_CREAT|O_TRUNC, so the 0-byte target residue (created or truncated flavor) is the recorded R-6 class (§10.1), not the compensated-then-aborted D-53/R-5 class) | (b) per-phase; (c)(d) N/A |
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

  Backs: AC-7

- **DE-19 — Exit-code and channel matrix** (spec §6.4)

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
file SURVIVES (accepted residue R-5, §10.1), and a trigger striking DURING
the `open()` call itself is the D-54/D-57 at-open class — no compensation
runs, and a pre-existing target may be left truncated to 0 bytes
(accepted residue R-6, §10.1; the at-open trigger class is KI or
MemoryError per D-57).

  Backs: AC-18

- **DE-20 — Per-class contract (all cataloged errors)** (spec §7.1)

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
| E-WRITE | S5 | OSError at open/write/flush of output (EACCES/ENOSPC/EIO/EDQUOT) | compensation runs only if the open SUCCEEDED (D-46), then `OutputWriteError` → main; an at-open failure reports directly, no compensation | post-open failures: partial file removed best-effort (device-path removal failure ignored); at-open failures: no compensation, every output target byte-untouched (D-46); pre-open encode failures (D-43) likewise leave every output target byte-untouched. (The at-open MEMORYERROR class of E-MEM, D-57, is the recorded exception to the byte-untouched at-open rule — R-6's 0-byte residue; it reports under E-MEM, not here) | yes — after freeing space/fixing permissions; rerun is clean | user fixes the target (space, permissions, path); the tool's own compensation (delete partial) is automatic for post-open failures | exit 1 + stderr line (output path named) | same line | T-C8 |
| E-MEM | S1–S5 | MemoryError (file/payload genuinely too large for available RAM) | residual net → main | read/parse phases: none. Serialize phase: none (nothing open yet — D-44, filesystem untouched). Write phase: pre-open (encode, D-43) — every output target byte-untouched; post-open (mid-write) — the D-33 compensation removes the partial file (compensation trigger is every exception raised after a SUCCESSFUL open, §4.5/D-46), removal failure ignored; the D-53 arm-abort scope applies — a second MemoryError (or second KI) landing inside the failure arm aborts the remove mid-flight and the partial file SURVIVES as the recorded residue R-5 (§10.1; decision D-56(a), adv-c10 F-01). AT-OPEN (D-57): a MemoryError raised by the open call itself runs NO compensation (fd never bound) and can leave the R-6 0-byte residue (created or truncated flavor, §10.1) while still reporting this write-phase form | only with more RAM/smaller input | reduce input size; tool reports per contract | exit 1 + stderr line (phase form: reading/while converting/writing — serialize and write share the output-named form, D-44; §6.3) | same line | T-C16 (child process under a low RLIMIT_AS → E-MEM line, exit 1, no partial output outside the D-53/R-5 arm-abort residue — a second MemoryError inside the failure arm leaves it, D-56(a), and outside the D-57 at-open residue — an at-open MemoryError leaves the R-6 0-byte target; pre-existing-output case asserts per the OBSERVED phase form: bytes survive for a pre-open form, path absent for the write-phase form, 0-byte for the D-57 at-open form — §8.3/D-46/D-57; fault-injection method per §8.4) |
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
the open, with the recorded at-open exceptions (R-6: a KI — or a
MemoryError, D-57 — striking the open call itself can leave it 0-byte,
truncated or created flavor, §10.1) and the two recorded signal-window
exceptions beyond that (adv-c6 F-01
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

  Backs: AC-7, AC-10, AC-11, AC-19

- **DE-21 — Fail-fast and first-error-wins invariants** (spec §7.2)

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
  file": a KI — or a MemoryError (D-57) — striking the open call itself
  can leave the target 0-byte: a PRE-EXISTING target truncated (the
  kernel's O_TRUNC), or an ABSENT target left a CREATED 0-byte file (the
  kernel applied O_CREAT before the trigger struck; the arm sees
  `fd is None` and runs no compensation) — both flavors of R-6 (§10.1,
  decisions D-54/D-57, adv-c10 F-04 / adv-c11 F-01).
- REQ-008's "output file absent or unchanged" is enforced structurally:
  S5 is unreachable until S3 has accepted every record.

  Backs: AC-8, AC-10

- **DE-22 — Residual-exception net** (spec §7.3)

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
D-54 at-open class with R-6's possible 0-byte residue (§10.1); per
D-57 the same at-open classification covers a MemoryError raised by
the open call itself (reported as E-MEM's write-phase form, same R-6
residue).

  Backs: AC-7

- **DE-23 — Non-functional requirement mapping** (spec §9)

  | NFR | design decision that delivers it | where |
|---|---|---|
| NFR-001 zero deps | single file; imports only `csv, io, json, os, sys` (§4.1: manual dispatch is the ONE conforming shape — D-52 retracts the former argparse alternative, whose import would break this pinned set) | §4.1, §2.2 |
| NFR-002 3.9+ floor | no 3.10+ syntax (no match, no `\|` unions in annotations used at runtime); dict ordering relied on only as a documented 3.7+ language property; f-strings and `encoding=` forms are 3.9-safe | §4.3.5 |
| NFR-003 envelope | whole-file in-memory pipeline (documented as acceptable below the envelope; larger files out of scope per REQ §3.2); line numbering advances INCREMENTALLY per record span (§4.3.2) so the whole pipeline is O(input length) — no quadratic prefix rescans; the per-record scan may fuse the FSM walk and the break count into ONE pass (D-58's conforming fusion) or keep the two-quantity form — both O(record); the envelope's 30 s figure is stated on the reference hardware class T-C9 names; all stage-cost evidence is BINDING-CONTROLLED per D-59 (appendix/66-rev14-binding-timing.py: every cited number names its CPython name binding, form comparisons are binding-internal — cross-binding comparison is void; reader-only 0.8 s and dict+serialize 0.4 s are module-bound baselines, labeled per D-59 at §8.3 T-C9) | §2, §4.2, §4.3.2, §8.3 T-C9 |
| NFR-004 channel discipline | single printer in `main`; success path contains no print statements at all; the stdout/stderr rows of §6.4 and T-K3 scope to REGULAR-FILE output paths — a character-device output (`/dev/stdout`, `/dev/stderr`, `/dev/null`, `/dev/fd/N`) receives the document on that device at exit 0 by the caller's own redirection choice (D-55); the tool performs no stdout/stderr write of its own on any path | §4.1, §6.1, §6.4 |
| NFR-005 robustness | input only ever parsed (csv) and serialized (json) — never executed/interpolated; startup limit-raise (§4.6) removes the 131072-byte field cap; MemoryError handled per E-MEM | §4.6, §7.1 |

  Backs: AC-13, AC-15, AC-16, AC-17, AC-18, AC-19

## Notes on Spec Clarifications

- D-01: Language: Python, single-file script, stdlib only
- D-02: Invocation form: `python csv2json.py input.csv output.json` (two positional args, input then output)
- D-03: CSV first row is always a header row; header fields become output object keys, in order
- D-04: Quoted fields with embedded commas/quotes/newlines must parse correctly (RFC-4180 via stdlib csv)
- D-05: Row with field count ≠ header count is an error reported with the line number
- D-06: Output is a JSON array of flat objects written to the given output file, rows in input order
- D-11: Value typing: ALL values as strings, lossless; empty cell = empty string, never null (user answer Q-01 (a), 2026-09-16 17:38)
- D-12: Duplicate header names are an error, citing line 1 and the duplicate name; no silent overwrite (user answer Q-03 (a), 2026-09-16 17:38)
- D-13: Non-UTF-8 input fails with a clear error; lossy conversion is forbidden (user answer Q-04 (a), 2026-09-16 17:38)
- D-16: UTF-8 BOM on input: STRIPPED from the first header field; keys come out clean (`id`, not `\ufeffid`); U+FEFF elsewhere is data (user answer Q-05 (a), 2026-09-16 17:53)
- D-17: Non-ASCII output escaping: RAW UTF-8, `ensure_ascii=False`; real Thai characters in the JSON file (user answer Q-06 (a), 2026-09-16 17:53)

## Review & Validation Trail (req-lab)

This plan is a deterministic re-layout of the APPROVED req-lab spec; the authoritative design record is the spec bundle.
- user gate: APPROVED 2026-09-17 09:14
- mechval final: PASS (cycle 16)
- cold-audit: READY

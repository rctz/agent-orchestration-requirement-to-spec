# Spec — csv2json

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | spec |
| version | v2 |
| status | DEPRECATED |
| date | 2026-09-17 |
| author | req2-spec-designer |
| requirements | requirements/07-requirements-v7.md (status: APPROVED, 2026-09-17) |
| user decisions | appendix/01-user-decisions.md (Q-01..Q-06 answered) |
| decision register | appendix/03-decision-register.md (D-01..D-36, all DECIDED) |
| probes | appendix/13-spec-design-probes.py (70/70 PASS, 2026-09-17) |
| revision | v2 — cycle-2: fixed mechval F-01 by rephrasing the §4.5 row-9 label without the claim term and adding the §10.1 R-2 pointer; no other section changed |

# 1. Overview & goals

This document is the implementation spec for `csv2json`, a small,
dependency-free command-line tool that converts a CSV file with a header row
into a JSON array of flat objects. It is derived from
requirements/07-requirements-v7.md (status APPROVED, 2026-09-17). It adds no
requirements, reinterprets none, and leaves none unresolved: D-01..D-36 in
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
  (appendix/13-spec-design-probes.py, 70/70 PASS); where the requirements
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
| `parse` | hand the text to `csv.reader` with `newline=''` semantics; iterate record by record; per-record unterminated-quote scan; header checks; per-row count validation; build the list of dicts | REQ-014, REQ-002/003/004/006/009/013, D-24/D-25/D-29/D-30/D-31/D-36 |
| `serialize` | `json.dumps(rows, ensure_ascii=False, separators=(",", ":"))` + one trailing `\n` | §5.2, D-11b/D-14/D-17/D-20/D-26 |
| `write_output` | open the output path for binary write; write the encoded payload; flush; on any OSError remove the partial file best-effort and report per the REQ-007 shape naming the output path | REQ-010, D-33/D-35 |

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
  An argparse-based implementation is acceptable ONLY if it overrides both
  the exit code (1) and the message shape (prefix + usage text) on every
  error path, including unknown-option errors.
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
  per the REQ-007 shape; return 1. Never print a traceback (any residual
  unexpected exception is also caught and reported per the REQ-007 net —
  see §7.3), never write a partial output on a failed run.
- **Error paths.** Table:

| condition | error type raised/caught | message emitted by | exit |
|---|---|---|---|
| `len(argv) != 2` | (none — handled inline) | inline usage line, prefixed | 1 |
| input unreadable (OS) | `InputReadError` | `main` via formatter | 1 |
| invalid UTF-8 byte | `InvalidUtf8Error` | `main` via formatter | 1 |
| empty file / 0-field first row / count error / duplicate header / unterminated quote | `FieldError` (with class-specific text) | `main` via formatter | 1 |
| output open/write/flush OSError | `OutputWriteError` | `main` via formatter | 1 |
| MemoryError anywhere | `ToolError` (generic contract message) | `main` via formatter | 1 |
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
- **Behavior — `line_of_offset` (D-28).** Pure function; counts breaks by
  scanning `text[0:offset]`: `\r\n` advances one line and consumes two
  characters; a bare `\r` (next char exists and is not `\n`) or a `\n`
  advances one line and consumes one; VT 0x0B, FF 0x0C, NEL U+0085,
  U+2028, U+2029 advance nothing. `line_of_offset(anything, 0) == 1`.
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
  contract (`csv2json: error: out of memory reading <path>` shape).

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
    # --- check 1: unterminated quote (REQ-013, D-30 FSM below) ---
    # --- check 2: header rules when this is the first record ---
    # --- check 3: field-count rule for data rows ---
    line += count_line_breaks(text, start, end)   # D-28 basis, O(end-start)
    start = end
```

  The three checks run in exactly this order PER RECORD; the loop returns
  or raises at the first failing check of the first failing record — this
  IS the D-29 sequential fail-fast (no whole-input pre-pass; a count-bad
  earlier row raises before a later unterminated-quote row is ever
  examined; probe P8 "count error wins over later quote").
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
| FIELD_START | → QUOTED, remember current record-relative line as the opening line | stay FIELD_START | → FIELD_START (record-internal terminator; only possible for a record-internal empty line, never across records) | → UNQUOTED |
| UNQUOTED | stay UNQUOTED (data — D-30) | → FIELD_START | → FIELD_START | stay UNQUOTED |
| QUOTED | → CLOSED | stay QUOTED (data) | stay QUOTED (data), advance the record-relative line counter | stay QUOTED |
| CLOSED | → QUOTED (doubled quote re-opens) | → FIELD_START | → FIELD_START | → UNQUOTED |

  If, at end of `record_text`, the state is QUOTED, the record has an
  unterminated quoted field: raise `FieldError` with N = `row_start_line`
  and M = `row_start_line + opening_line - 1`:
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
  allowed, F-33).
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
  the full document INCLUDING the trailing newline; the write stage only
  encodes and writes. (Keeping the newline here — not in the write stage —
  makes the byte contract a pure-function test.)
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
  residual net (§7.3) — reported per the generic contract, exit 1, no
  output file (REQ-010: nothing has been opened yet at this stage).
  json.dumps on `list[dict[str, str]]` cannot otherwise fail.

## 4.5 Write stage — `write_output(path, document)`

- **Purpose.** The only place that touches the output filesystem: one
  open/write/flush, with D-33's delete-on-failure compensation.
- **Interface.** `write_output(path: str, document: str) -> None`, raising
  `OutputWriteError` on any failure (message pre-formatted with the OUTPUT
  path; `main` prints it).
- **Behavior — no newline translation (D-35).** Open with
  `open(path, "wb")` (binary). Encode once: `document.encode("utf-8")` —
  UTF-8, no BOM (D-09). Binary mode makes the `]\n` ending byte-exact on
  every platform; a text-mode open without `newline=""` would emit `]\r\n`
  on Windows and is NON-CONFORMING (D-35). (Equivalent conforming
  alternative: text mode `open(path, "w", newline="", encoding="utf-8")`;
  the spec pins binary mode as the single implemented shape.)
- **Behavior — write then flush.** `write(...)`, then `flush()` BEFORE
  close accounting: D-33 names flush-time failures (ENOSPC on some
  filesystems surfaces at flush/close) as covered. Wrap open/write/flush in
  one try; on `OSError` (ENOSPC, EIO, EDQUOT, EACCES at open, ...): first
  run the compensation (below), then raise
  `OutputWriteError` with message
  `csv2json: error: cannot write <path>: <strerror>` (REQ-007 shape with
  (b)'s output-path provision; probe 10-fold-c5 F28: `/dev/full` accepts
  open, fails flush with errno 28 — the run must exit 1 with this message
  shape and no leftover partial file).
- **Behavior — compensation (D-33, delete-on-failure).** On ANY failure
  after the file was (possibly) created: best-effort `os.remove(path)` of
  the exact path this stage opened; IGNORE any exception from the remove
  (including ENOENT when open itself failed, and EINVAL/EPERM when the
  path is a device node such as `/dev/full` — REQ-010's AC states the
  removal attempt on a device path fails harmlessly). The reported error
  is the run's outcome; the removal is silent cleanup. Rationale: a
  partially written file must never survive as a plausible complete JSON
  document; delete-on-failure is D-33's pinned disposition.
- **Error paths.** Every failure collapses to `OutputWriteError` (exit 1
  via `main`); there is no retry loop, no temp-file rename, no fsync
  requirement (none is pinned by any REQ; flush covers the D-33 surface).
- **Mutation contract (the 13 questions) for this stage** — the only
  state-mutating operation in the tool:

| # | question | answer |
|---|---|---|
| 1 | who may call it | whoever can execute the script and write to the target path (single-user CLI; REQ §2 — no auth layer exists) |
| 2 | input & validation contract | `path: str`, `document: str` ending `]\n`; no path validation beyond what `open()` enforces |
| 3 | where preconditions are enforced | output path is only touched AFTER `parse` returned successfully (REQ-010 phase split, D-15 slot 7); writability is discovered by `open()` itself |
| 4 | where mutation occurs | this stage exclusively: one `open(path, "wb")`, one write, one flush |
| 5 | source of truth | the in-memory `document` string produced by `serialize`; the file is a projection of it |
| 6 | all-or-nothing boundary | one file; best-effort in-place write with delete-on-failure compensation — no cross-file all-or-nothing property is required or provided (single invocation, no concurrent readers in scope) |
| 7 | on retry | re-running the tool re-executes from scratch; a successful rerun overwrites/truncates the target; a failed run left no file (or a harmless device path) so retry is clean |
| 8 | on duplicate call | same as retry — the tool has no session; "duplicate" means the user ran it again; last successful run's bytes define the file (REQ §5.1: successful run REPLACES the file entirely) |
| 9 | when two runs overlap in time | out of scope by REQ §2 (single-user, single-invocation); no locking is provided; two simultaneous runs to the same target race at the OS level and the last writer wins — recorded as an accepted scope boundary, not a promised property (see §10.1 R-2) |
| 10 | state remaining after mid-op failure | none intended: the partial file is removed best-effort; if removal itself fails (rare), the error already reported stands and exit is 1 (REQ-010 wording) |
| 11 | rollback/compensation | exactly D-33's: best-effort `os.remove`, failures ignored |
| 12 | caller/user learning of failure | one `csv2json: error: cannot write <path>: <strerror>` line on stderr (via `main`), exit 1; nothing on stdout (NFR-004) |
| 13 | proving test | §8 contract tests: `/dev/full` write-failure case (open succeeds, flush raises), non-writable-directory case, invalid-input/no-file-created case, byte-exact success case — real filesystem, no mocks (infra behavior is never certified mock-only) |

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
WRITE_OUTPUT ── OSError(after remove-compensation)► REPORTING(write) ──► exit 1
  ▼ WRITTEN
exit 0  (stdout silent)
```

REPORTING prints exactly one stderr line and nothing else. The output file
can exist only after WRITTEN; every path into REPORTING leaves the
filesystem untouched on the output side (§4.5's compensation is the one
cleanup).

## 5.2 Parse-loop micro-states (inside PARSE)

`AWAITING_HEADER` → on first record: `HEADER_VALIDATED` (after FSM scan →
0-field check → duplicate check) → `IN_DATA` → per record: FSM scan → count
check → row appended. `IN_DATA` until StopIteration → `PARSE_OK`.
Any check failure raises straight out of PARSE (REPORTING(field)).
The FSM's own four states (FIELD_START/UNQUOTED/QUOTED/CLOSED, §4.3.3) are
re-created per record and never leak across records.

## 5.3 Scenario walk-throughs (every REQ-identified scenario, with failure paths)

Steps cite stages (S1 read_raw, S2 decode_utf8, S3 parse, S4 serialize,
S5 write_output); "→msg" gives the exact stderr line; "exit" gives the code.

**S-1 Happy path** (REQ-001/002/003/005; REQ §1 success condition).
`python csv2json.py in.csv out.json`, in.csv = `id,name\n1,x\n2,y\n`:
argv ok → S1 reads bytes → S2 decodes (no BOM) → S3: record 1 `id,name`
passes FSM (no quote), header validated (2 unique names); records 2–3
pass FSM, counts match, rows built → S4 emits
`[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n` → S5 writes 45 bytes →
exit 0, stdout empty, out.json created/replaced.

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
(single line, file ends): the FIRST record's FSM scan trips →
`... line 1: unterminated quoted field (opened at line 1)` — never the
`[]`/exit-0 lenient outcome (D-25).

**S-10 Unterminated quote — N ≠ M** (REQ-013/D-30). `h1,h2\n"a\nb",c,"d\ne`
(one record starting at physical line 2, whose third field's opening
quote sits on line 3 and never closes): record 2's FSM scan ends QUOTED
with record-relative opening line 2 → N=2, M=3 →
`csv2json: error: in.csv line 2: unterminated quoted field (opened at
line 3)`, exit 1, no output file.

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

**S-14 Write-phase failure** (REQ-010/D-33). Valid input; output target
`/dev/full` (or a file on a full disk): S5's open succeeds, write/flush
raises OSError(ENOSPC) → compensation runs first (best-effort
os.remove; on a device path it fails harmlessly and is ignored) →
`csv2json: error: cannot write /dev/full: No space left on device` on
stderr, exit 1 — never a traceback, never a silent success, no leftover
partial file on a REGULAR filesystem. (b) non-writable directory:
open() itself raises (EACCES) → same message shape (with that strerror),
exit 1; nothing was created so compensation is a harmless no-op (ENOENT
ignored). (c) output path is an existing file: a successful run replaces
it entirely (REQ §5.1); an error before S5 leaves it byte-untouched
(REQ-008/010: "absent or unchanged").

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
| form | `python csv2json.py <input.csv> <output.json>` — exactly two positional args, input first, output second |
| arg count ≠ 2 | stderr `csv2json: error: usage: csv2json.py <input.csv> <output.json>`; exit 1; no file created |
| exit codes | 0 on success; 1 on EVERY failure (usage, read, decode, parse, write, memory, residual) — two-valued, no exit 2 anywhere |
| stdout | empty on success; empty on failure (errors go to stderr) |
| stderr | empty on success; exactly one line per failed run |
| flags/options | NONE accepted. `-h`/`--help` are out of scope (REQ §3.2: no named options); an argparse-based build must still route any unknown-option error through the prefixed usage message with exit 1 |
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
6. Header-only input produces exactly `[]\n` (2 bytes).

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
| E-WRITE | (7) output OSError | `csv2json: error: cannot write <out>: <strerror>` | (b) output path; (c)(d) N/A |
| E-MEM | any phase, MemoryError | `csv2json: error: out of memory reading <in>` (parse/serialize/write phase: `... while converting <in>`) | (b); (c)(d) N/A |
| E-NET | residual unexpected exception | `csv2json: error: <in>: internal error: <exception repr>` | (b); (c)(d) N/A |

E-NET is the catch-all net for genuinely unforeseen exceptions; it
deliberately does NOT swallow or disguise any cataloged class (each has its
own id above — retry/recovery distinctions are per-class, never erased by
the net). `strerror` is the OS's message text verbatim (e.g. `No space
left on device`), satisfying REQ-010's example shape.

## 6.4 Exit-code and channel matrix

| class | exit | stdout | stderr |
|---|---|---|---|
| success | 0 | empty | empty |
| E-USAGE/E-READ/E-UTF8/E-EMPTY/E-HEADER0/E-DUP/E-COUNT/E-UQ | 1 | empty | one catalog line |
| E-WRITE (incl. mid-write) | 1 | empty | one catalog line (output path named) |
| E-MEM / E-NET | 1 | empty | one catalog line |

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
| E-WRITE | S5 | OSError at open/write/flush of output (EACCES/ENOSPC/EIO/EDQUOT) | compensation runs, then `OutputWriteError` → main | partial file removed best-effort (device-path removal failure ignored) | yes — after freeing space/fixing permissions; rerun is clean | user fixes the target (space, permissions, path); the tool's own compensation (delete partial) is automatic | exit 1 + stderr line (output path named) | same line | T-C8 |
| E-MEM | S1–S5 | MemoryError (file/payload genuinely too large for available RAM) | residual net → main | partial file removed (if raised in S5) | only with more RAM/smaller input | reduce input size; tool reports per contract | exit 1 + stderr line | same line | T-C9 (constructed via limit, fault-injection note in §8.4) |
| E-NET | any | unexpected exception (no cataloged class fits) | residual net → main | partial file removed (if raised in S5) | n/a — signals a bug | file a defect; the tool still honors exit+prefix+no-traceback | exit 1 + stderr line | same line | T-C10 (fault-injection) |

Taxonomy coverage: validation (E-COUNT, E-DUP, E-HEADER0, E-EMPTY, E-UQ —
all input-shape validation), stale reference (N/A — the tool holds no
references across calls; every run re-opens both paths, so a deleted input
surfaces as E-READ and a vanished output directory as E-WRITE), invalid
state or transition (N/A — the process state machine §5.1 is linear with
no re-entry), permission (E-READ/E-WRITE EACCES forms), dependency
unavailable (N/A — stdlib-only, no external services; the OS is the only
dependency and its absence is not a runtime state), read-write failure
(E-READ, E-WRITE), partial failure (E-WRITE's mid-write form with the
delete-on-failure compensation), timeout-cancellation (N/A — no timeouts
exist; cancellation is the user killing the process, which leaves whatever
partial output existed at kill time — outside the tool's contract, recorded
as an accepted scope boundary), resource exhaustion (E-MEM; disk-exhaustion
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
  target removed (error in S5), or the target harmlessly untouched
  (device/permission cases where removal is impossible — the error message
  is then the run's entire effect).
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
are NOT caught (process-level signals pass through; see §7.1
timeout-cancellation N/A note).

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
| T-U3 | unterminated-quote FSM | P3 case table (all REQ-013 shapes; `5" ruler` data; doubled quotes; post-close junk) | REQ-013/D-30 |
| T-U4 | parse: header rules | header-only → `[]`; 0-field first row → E-HEADER0 text; duplicates incl. empty-name → E-DUP text | REQ-002/009 |
| T-U5 | parse: count rules | blank middle line → E-COUNT at line 2; trailing blank → line 3; whitespace-only line converts | REQ-006/009/D-36 |
| T-U6 | parse: D-29 ordering | `id,name\n1\n"2,3` → E-COUNT at line 2 (quote never reached) | D-29 |
| T-U7 | serialize byte form | compact separators, raw UTF-8, escape forms, `]\n` ending — P6 case table | D-14/17/20/26 |
| T-U8 | limit raise | after import, `csv.field_size_limit()` > 131072 | D-21/D-27 |

## 8.2 Contract layer (message catalog + output bytes, still I/O-free)

| T-id | verifies | method |
|---|---|---|
| T-K1 | every E-* template | run the pure stages on each trigger input; assert the exact catalog string from §6.3 (parametrized over strerror where OS-dependent) |
| T-K2 | output document byte form | golden bytes for: happy path, Thai text, control chars, header-only `[]\n`, CRLF-in-field (S-1, S-8d, S-13, §6.2.6) |
| T-K3 | exit/channel discipline | `main()` return values 0/1 per §6.4; stdout capture empty on every path |

## 8.3 Integration / E2E layer (real filesystem, real process)

| T-id | verifies | method | REQ |
|---|---|---|---|
| T-C1 | usage errors | subprocess: 0/1/3 args → exact usage line, exit 1, no file created | REQ-001/D-34 |
| T-C2 | unreadable input | missing path; chmod 000 file (skip as root) → E-READ, exit 1 | D-15(2) |
| T-C3 | UTF-8 errors | `0xFF` file; CR-only file `a,b\rc,d\rc\r\xff` → line 4 cited | REQ-011 |
| T-C4 | empty/BOM-only/blank-lines | zero-byte → E-EMPTY; EF BB BF only → E-EMPTY; `\n\n` → E-HEADER0 line 1 | REQ-009/012/D-31 |
| T-C5 | duplicate header | `id,name,id` → E-DUP 'id'; `a,,b,` → E-DUP ''; `a,,b` converts | REQ-002/F-33 |
| T-C6 | count errors | short row at line 4 → exact E-COUNT (physical-line numbering); trailing blank; whitespace-line converts | REQ-006/007/009 |
| T-C7 | unterminated quotes | `id,name\n"1,2`; `a\n"1`; `"id,name`; N≠M case `h1,h2\n"a\nb",c,"d\ne`; negative `5" ruler` converts | REQ-013 |
| T-C8 | write-phase failures | `/dev/full` → E-WRITE with output path, exit 1, no regular-file leftover; non-writable dir → E-WRITE; pre-existing output file survives an input-error run byte-unchanged | REQ-010/D-33 |
| T-C9 | performance envelope | generated ~50 MB / ~250k-row CSV converts < 30 s, < 1 GB RSS (spot check, not a hard gate) | NFR-003 |
| T-C10 | no-traceback net | fault-injected stage raising a bare `RuntimeError` → E-NET line, exit 1, no traceback substring on stderr | REQ-007 |
| T-C11 | quoted-field byte exactness | `"x\r\ny"` and `"x\ry"` fields → output contains the `\r\n`/`\r` JSON escapes, NOT rewritten `\n` | REQ-004/014/D-24 |
| T-C12 | CR-only + mixed terminators E2E | `a,b\rc,d\r` → converts; `a\nb\rc\n` → converts | REQ-014/§3.1 |
| T-C13 | lossless + inertness E2E | `42,3.14,true,` / `007,` / `<script>` / NUL-FF-VT cells → string-only output, valid JSON | REQ-005/NFR-005/D-14 |
| T-C14 | Python floor | the suite runs on the oldest supported interpreter available in CI (3.9 target; skip-with-warning if unavailable) | NFR-002 |
| T-C15 | BOM E2E | BOM+header → clean keys; byte-identical to no-BOM run; U+FEFF mid-cell preserved | REQ-012 |

## 8.4 Test-infrastructure notes

- `/dev/full` exists on Linux CI; on macOS the E-WRITE/ENOSPC case is
  replaced by a small FUSE-free trick: write to a file on a read-only
  mount or use `ulimit -f` (file-size rlimit) — the T-C8 assertion is on
  the message/exit/cleanup contract, not on the ENOSPC errno itself.
- E-MEM (T-C9's fault form) is exercised by fault injection: monkeypatching
  is NOT used inside the unit under test; instead the test runs a child
  process with a low `RLIMIT_AS` so a genuine MemoryError surfaces in
  `main`'s net. (RLIMIT_AS injection is an environment control, not a
  mock.)
- The 50 MB NFR-003 case is generated, checksummed, and reused so the
  spot check is reproducible; it is marked `slow` and may be excluded from
  the default run.

# 9. Non-functional requirement mapping

| NFR | design decision that delivers it | where |
|---|---|---|
| NFR-001 zero deps | single file; imports only `csv, io, json, os, sys` (no argparse needed — §4.1) | §4.1, §2.2 |
| NFR-002 3.9+ floor | no 3.10+ syntax (no match, no `\|` unions in annotations used at runtime); dict ordering relied on only as a documented 3.7+ language property; f-strings and `encoding=` forms are 3.9-safe | §4.3.5 |
| NFR-003 envelope | whole-file in-memory pipeline (documented as acceptable below the envelope; larger files out of scope per REQ §3.2); line numbering advances INCREMENTALLY per record span (§4.3.2) so the whole pipeline is O(input length) — no quadratic prefix rescans; the FSM is O(record length), records sum to the input length | §2, §4.2, §4.3.2 |
| NFR-004 channel discipline | single printer in `main`; success path contains no print statements at all | §4.1 |
| NFR-005 robustness | input only ever parsed (csv) and serialized (json) — never executed/interpolated; startup limit-raise (§4.6) removes the 131072-byte field cap; MemoryError handled per E-MEM | §4.6, §7.1 |

## 9.1-9.5 Verification anchors

NFR-001: T-C-suite imports audit (the test asserts the module's import
set). NFR-002: T-C14. NFR-003: T-C9. NFR-004: T-K3 + every E2E asserting
empty stdout. NFR-005: T-C13 + T-U8 + T-C10.

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
- Verification: T-C1..T-C10, T-K1, T-K3 assert message text and exit code
  for every catalog class on a real subprocess.

### QC-2 <no output file is created or truncated on any failed run>
- Scope: every error class; both "absent" and "pre-existing" output
  targets.
- Mechanism: phase split (D-15 slot 7, §4.5 row 3) — S5 is structurally
  unreachable until S3 accepted every record; S5 opens the target only
  after full validation; mid-write failure triggers the D-33
  delete-on-failure compensation (§4.5).
- Assumptions: the compensation's `os.remove` can fail on device/permission
  paths — REQ-010 explicitly accepts and ignores that (harmless attempt).
- Failure: if removal fails on a REGULAR file (pathological: e.g. parent
  dir made unwritable between write and remove), a partial file may
  survive — the error is still reported and exit is 1; recorded as an
  accepted residual risk (R-1, §10.1), not silently folded.
- Verification: T-C1 (no file created), T-C8 (three write-failure forms
  incl. `/dev/full`), T-C8 pre-existing-file-unchanged assertion.

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
  `os.remove` itself fails on a regular file (QC-2 Failure). Likelihood:
  pathological. Mitigation: none required by any REQ; the error is still
  reported with exit 1. Owner: implementor to preserve the compensation
  order (remove BEFORE raising).
- R-2: two concurrent processes writing one target race at the OS level
  (§4.5 row 9). Out of scope per REQ §2; no lock is provided. Not a
  guarantee — an accepted scope boundary.
- R-3: a closed/broken stderr makes error reporting itself fail (QC-1
  Assumptions). Outside the tool's contract; same class as the user
  closing the terminal.

# 11. Traceability matrix

Every REQ/NFR → designing section → key invariant → failure behavior
(§6.3 id) → test layer + id → evidence. "Impl detail" rows are marked as
implementation details (not REQ-derived). Nothing uncovered; nothing
invented.

| REQ/NFR | designed in | invariant | failure id | test layer / id | evidence |
|---|---|---|---|---|---|
| REQ-001 | §4.1, §6.1 | argc==2 else prefixed usage; input-then-output | E-USAGE | E2E T-C1 | REQ AC; 10-fold-c5 F29 (argparse exit 2) |
| REQ-002 | §4.3.4, §3.1 | header verbatim; ≥1 field; dup error; empty name once | E-HEADER0/E-DUP | unit T-U4; E2E T-C5 | REQ ACs; P8 |
| REQ-003 | §4.3.5, §6.2.5 | one object/row, input order | — (success path) | unit T-U5; E2E T-C13 | P8 happy path |
| REQ-004 | §4.3.1, §4.3.3 | dialect-exact quoted fields; byte-exact in-quote newlines | E-UQ (only if unclosed) | unit T-U3; E2E T-C11 | P8 CRLF-in-field; REQ 05-batch-2 probes |
| REQ-005 | §4.4, §6.2.5 | all values JSON strings; "" not null; verbatim | — | unit T-U7; E2E T-C13 | P6; REQ ACs |
| REQ-006 | §4.3.5 | len(row)==len(header) per data row | E-COUNT | unit T-U5; E2E T-C6 | P8 count cases |
| REQ-007 | §6.3 catalog, §7.1 | prefix on ALL classes; (b)-(d) per class | all | contract T-K1 | catalog vs REQ examples |
| REQ-008 | §7.2, §5.1 | first error only; S5 unreachable on failure | all | E2E T-C8 (unchanged file), T-U6 | P8 ordering |
| REQ-009 | §4.3.4/§4.3.5/§4.3-end | 0-field model; blank=EMPTY; whitespace=data; one-trailer rule | E-EMPTY/E-HEADER0/E-COUNT | unit T-U4/T-U5; E2E T-C4/T-C6 | P8; 10-fold-c5 F31 |
| REQ-010 | §4.5, §7.1, QC-2 | validate-then-write; delete-on-failure; output-path naming | E-WRITE | E2E T-C8 | 10-fold-c5 F28 (/dev/full) |
| REQ-011 | §4.2, §7.1 | strict decode; byte cited at D-28 line | E-UTF8 | E2E T-C3 | P4 (line 4 case) |
| REQ-012 | §4.2 | one leading BOM stripped; U+FEFF elsewhere data | E-EMPTY (BOM-only) | E2E T-C15 | P8 BOM cases; D-31 |
| REQ-013 | §4.3.3, §5.3 S-9..S-11 | FSM per record; N=row start, M=open line; header included; no pre-pass | E-UQ | unit T-U3/T-U6; E2E T-C7 | P3/P8 all AC shapes |
| REQ-014 | §4.3.1 | newline='' handoff; no universal newlines anywhere | E-COUNT (CR crash shape gone) | E2E T-C11/T-C12 | P8 CR-only; REQ batch-2 |
| NFR-001 | §2.2, §9 | stdlib-only import set | — | imports audit (T-C suite) | §9 |
| NFR-002 | §9 | 3.9-safe syntax; behavior identical across floor | — | T-C14 | §9 |
| NFR-003 | §4.3.2, §9, QC-5 | O(input) pipeline; incremental line counting | E-MEM | T-C9 | §4.3.2 note |
| NFR-004 | §4.1, §6.4 | stdout empty on every path; one stderr line on failure | — | contract T-K3 | §6.4 |
| NFR-005 | §4.6, §7.1, QC-6 | limit raised; content inert; MemoryError contracted | E-MEM/E-NET | T-U8/T-C13/T-C10 | P5; REQ ACs |
| Impl detail | ADR-2 (§2.3) | offset-based line numbers (line_num lags) | — | T-U2 | P7 lag evidence |
| Impl detail | ADR-4 (§2.3) | no temp-file+rename (single-phase write suffices) | — | — | §2.3 rationale |
| Impl detail | §4.6 degrade loop | halving on OverflowError | — | T-U8 | P5 |

Decision-coverage check: D-01..D-36 are all DECIDED in
appendix/03-decision-register.md and all are bound to spec mechanisms —
D-01 (§4.1), D-02 (§4.1, §6.1), D-03 (§4.3.4), D-04 (§4.3.1), D-05
(§4.3.5), D-06 (§4.3.5, §4.4), D-07 (§9), D-08 (§2.4), D-09 (§4.5), D-10
(§7.2), D-11 (§4.4), D-11b (§4.1, §4.4), D-12 (§4.3.4), D-13 (§4.2), D-14
(§4.4), D-15 (§5.1), D-16 (§4.2), D-17 (§4.4), D-18 (§4.3.5), D-19
(§4.3.3), D-20 (§4.4), D-21 (§4.6), D-22 (§6.3), D-23 (§4.2), D-24
(§4.3.1), D-25 (§4.3.3), D-26 (§4.4), D-27 (§4.6), D-28 (§4.2), D-29
(§4.3.2), D-30 (§4.3.3), D-31 (§4.2), D-32 (register hygiene, not a spec
mechanism), D-33 (§4.5), D-34 (§4.1), D-35 (§4.5), D-36 (§4.3.5). No
decision is unbound; none is reinterpreted.

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
| unterminated quoted field | A record whose text ends while the FSM is in QUOTED (§4.3.3) — the E-UQ error with N (row-start line) and M (opening-quote line). A `"` in an unquoted field is never this (data, D-30). |
| row-start line / opened-at line | N = `line` at the record's start offset; M = N + record-relative opening line − 1 (§4.3.2/§4.3.3). |
| lossless | Every input cell's exact text appears unchanged in the JSON output: no coercion, trimming, newline rewriting, or replacement (Q-01/D-11). |
| error catalog | The closed E-* message set of §6.3; every failure prints exactly one catalog line. |
| silent success | Exit 0 with empty stdout and the output file written (Q-02/D-11b). |

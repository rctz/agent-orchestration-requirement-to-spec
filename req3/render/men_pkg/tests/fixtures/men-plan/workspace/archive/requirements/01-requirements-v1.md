# Requirements — csv2json

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | requirements |
| version | v1 |
| status | DEPRECATED |
| date | 2026-09-16 |
| author | req2-req-designer |
| intake | appendix/00-intake.md |

## 1. Goal & success condition

**Goal.** Provide a small, dependency-free command-line tool `csv2json` that
converts a CSV file with a header row into a JSON array of objects, one object
per data row, keyed by the header names.

**Success condition.** A user runs
`python csv2json.py input.csv output.json`;
`output.json` contains a valid JSON array in which each element maps header
names to that row's field values; rows with a field count different from the
header produce a clear error naming the line number, and the tool exits with a
non-zero status; no third-party packages are required.

**Source requirement (verbatim, from appendix/00-intake.md):**

> I need a small command-line tool: csv2json. It reads a CSV file (with a header row), converts each data row into a JSON object keyed by the header names, and writes the result as a JSON array to an output file. Must handle quoted fields containing commas, and report a clear error (with line number) when a row has a different number of fields than the header. Single-file Python script, stdlib only, run as: python csv2json.py input.csv output.json

## 2. Users and roles

| role | description |
|---|---|
| end user | A developer or technical operator who runs the script from a terminal. No admin role, no service account, no multi-tenant aspect. |

Single-user, single-invocation CLI. No authentication, no authorization, no
roles beyond "whoever can execute the script".

## 3. Scope

### 3.1 In scope

- Reading one UTF-8-ish text CSV file given as the first CLI argument, with a
  header row as its first row.
- RFC-4180-style parsing via the Python stdlib `csv` module: quoted fields,
  embedded commas, embedded quotes (doubled), embedded newlines inside quoted
  fields.
- Converting every data row to a JSON object keyed by header names; writing
  the array to the output file given as the second CLI argument.
- Field-count validation of every data row against the header, with a clear
  error message including the input line number.
- Meaningful exit codes (0 success, non-zero on failure) and error output on
  stderr.

### 3.2 Explicitly out of scope

- Type inference / type conversion: deciding whether `42` becomes the JSON
  number `42` or stays the string `"42"` is a behavioral question raised as
  Q-01; either way, no user-defined type mapping.
- Any Graphical or web UI; the tool is CLI-only.
- Configuration files, environment-variable configuration, or named options
  beyond the two positional arguments.
- Streaming/incremental output for files that do not fit in memory (see
  NFR-003 for the chosen size envelope).
- CSV dialect auto-detection beyond the stdlib default (sniffing semicolon or
  tab dialects is not offered).
- Reading input from stdin or writing output to stdout.
- Deduplication, sorting, filtering, or any transformation other than the
  row→object mapping.
- Windows-specific line-ending and code-page handling beyond what Python's
  default `newline=''` + UTF-8 handling already gives (recorded as D-08).

## 4. Functional requirements

Requirement IDs are `REQ-nnn` (kept stable across revisions). Each has
acceptance criteria concrete enough to test. Inline `Q-nn` marks points that
need a user decision; they are mirrored in appendix/02-open-questions.md.

### 4.1 Core conversion

**REQ-001 — CLI invocation form.**
The tool is a single Python file `csv2json.py`, executed as:
`python csv2json.py <input.csv> <output.json>`
Exactly two positional arguments, in that order (input first, output second).
*Acceptance:* running the command above with a valid input produces the output
file; running with zero, one, or three arguments fails with a usage message on
stderr and a non-zero exit code, and no output file is created.

**REQ-002 — header row defines keys.**
The first row of the CSV is always a header row; its fields, in order, are the
keys of every output object. Header fields are used verbatim (no trimming,
renaming, case-folding, or deduplication unless Q-03 says otherwise).
*Acceptance:* for input whose first row is `id,name`, every output object has
exactly the keys `id` and `name`, in that insertion order.

**REQ-003 — one object per data row.**
Each data row becomes one JSON object mapping each header key to the value of
the field at the same position. The output file contains a single JSON array
of these objects in input row order.
*Acceptance:* a 3-row CSV (plus header) yields a JSON array of exactly 3
objects in the same order.

**REQ-004 — quoted fields.**
Parsing handles quoted fields containing commas, escaped/doubled quotes
(`""` inside a quoted field), and newlines inside quoted fields
(RFC-4180 semantics via the stdlib `csv` module).
*Acceptance:* a row `"a,b",c` parses to two fields `a,b` and `c`; a field
`"say ""hi"""` parses to `say "hi"`; a quoted field spanning two physical
lines parses as one field.

**REQ-005 — value mapping.**
Every field value appears in the JSON object exactly as a string.
UNLESS Q-01 answers otherwise (user may opt into type inference).
*Acceptance (string mode):* CSV row `42,3.14,true,` produces JSON values
`"42"`, `"3.14"`, `"true"`, `""` (empty string, not null).

### 4.2 Validation & error handling

**REQ-006 — field-count validation.**
Every data row must have exactly the same number of fields as the header row.
A row with fewer or more fields is an error.
*Acceptance:* header of 3 columns; a data row with 2 or with 4 fields each
cause the run to fail per REQ-008.

**REQ-007 — error message content.**
Each error message must (a) start with a fixed prefix `csv2json: error:`,
(b) name the input file, (c) give the 1-based physical line number in the
input file where the offending row starts, and (d) give the expected vs.
actual field counts. Example shape:
`csv2json: error: input.csv line 4: expected 3 fields, found 2`
For rows containing embedded newlines, the reported number is the line where
the row *starts*.
*Acceptance:* a test file with a short row on physical line 4 yields exactly
that message on stderr (numbers match the physical file lines, not logical
row indexes).

**REQ-008 — fail-fast behavior.**
The tool stops at the FIRST invalid row, writes nothing to the output file
(see REQ-010), prints the REQ-007 message to stderr, and exits with code 1.
*Acceptance:* a file with two bad rows reports only the first one; output
file is absent or unchanged after the failed run.

**REQ-009 — empty / edge rows.**
- A file containing ONLY a header row produces `[]` and exits 0.
- A completely empty file (no header at all) is an error:
  `csv2json: error: input.csv: file is empty (no header row)`, exit 1.
- A blank physical line between data rows is an error like any wrong-field-count
  row (a truly empty line parses as a 1-field row `['']`), reported per
  REQ-007. Trailing newline at end of file is normal and not an error.
*Acceptance:* each of the three cases behaves as stated.

**REQ-010 — output file safety.**
On any error (bad arguments, unreadable input, parse error, validation error)
the tool must NOT create or truncate the output file. The output file is
written only after the whole input has been parsed and validated
successfully. If the output path is not writable, the tool exits 1 with a
clear `csv2json: error:` message.
*Acceptance:* run on an invalid CSV with a fresh output path → no output file
exists afterwards; run with an output path inside a non-writable directory →
exit 1 with a clear message.

## 5. Data & integrations

### 5.1 Entities & meaning

| entity | meaning | ownership |
|---|---|---|
| Input CSV | A text file whose first row is the header; subsequent rows are data rows. Owned by the user; the tool only reads it. | user |
| Header row | The first parsed row. Its field values, in order, are the object keys of the output. Used verbatim. | user (content), tool (interpretation) |
| Data row | Every parsed row after the header. Must have exactly `len(header)` fields. | user (content), tool (interpretation) |
| Field value | The string content of one CSV cell after quote processing. Meaning is whatever the user's data means; the tool assigns no semantics. | user |
| Output JSON | A JSON array of flat objects (no nesting ever produced). Written by the tool; if the file pre-exists, a successful run REPLACES it entirely. | tool (writes), user (owns destination) |

### 5.2 Formats

- Input: single-character CSV, `","` separator, `"` quote character, `""` as
  an escaped quote inside quoted fields — i.e. the stdlib `csv` module
  default dialect (RFC-4180-compatible). No custom delimiters (out of scope,
  §3.2).
- Output: single JSON document (UTF-8, no BOM). Whether it is pretty-printed
  or compact is part of Q-02 / D-11b (user decision), since it changes the
  bytes of every successful run's output.
- Encoding: see Q-04 — the tool's contract on non-UTF-8 bytes must be fixed
  by the user, since it changes observable behavior (error vs. mojibake).

## 6. Non-functional requirements

**NFR-001 — zero dependencies.**
The tool runs with the Python standard library only. No pip installs, no
third-party imports, no build step.
*Acceptance:* `grep` of the script shows imports only from the stdlib; the
tool runs on a bare Python installation.

**NFR-002 — target runtime.**
Python 3.9 or newer. The exact floor is implementor freedom (D-07):
observable behavior must be identical across all supported versions.
*Acceptance:* the script imports and runs on Python 3.9.

**NFR-003 — performance envelope.**
A 50 MB CSV (~250k rows) converts in under 30 seconds and under 1 GB RAM on a
typical laptop. In-memory processing is acceptable below this envelope;
larger files are out of scope (§3.2).
*Acceptance:* documented test with a generated 50 MB file completes within
the limits (spot check, not a hard gate).

**NFR-004 — error channel discipline.**
All errors go to stderr; only genuine results (if any) go to stdout. A
successful run prints nothing to stdout (silent success), unless Q-02 opts
into a confirmation message.
*Acceptance:* successful run → empty stdout; failed run → REQ-007 message on
stderr, exit 1.

**NFR-005 — robustness against malicious/pathological input.**
The tool never executes, evaluates, or interpolates input content; field
values are data only. JSON output must always be valid JSON with proper
escaping (via the stdlib `json` module). A row of any size (up to available
memory) is processed without crashing the interpreter.
*Acceptance:* input containing `<script>`, `",,,,"` sequences, 10 MB single
field — output stays valid JSON, exit code reflects validity of the CSV
structure only.

## 7. Decisions log

Live status is maintained in appendix/03-decision-register.md (machine-parsed).
Snapshot of open points that this revision raises for the user:

| Q | topic | why it matters | status |
|---|---|---|---|
| Q-01 | value types: strings vs. inferred numbers/booleans/null | changes every observable output value | OPEN |
| Q-02 | output shape & success noise (pretty vs compact; silent vs confirmation line) | observable behavior of every successful run | OPEN |
| Q-03 | duplicate header names policy | silently losing/overwriting data is a data-integrity behavior | OPEN |
| Q-04 | non-UTF-8 input handling | error vs. mojibake is an observable failure contract | OPEN |

The authoritative, machine-parsed status of every decision (including the
ones already settled this cycle, D-01..D-10) lives in
appendix/03-decision-register.md.

## 8. Glossary

| term | definition |
|---|---|
| header row | The first row of the input CSV. Its fields become the keys of every output object. Never treated as data. |
| data row | Any parsed row after the header row. |
| field | One CSV cell, i.e. one element of a parsed row, after quote processing. |
| field count | The number of fields in a parsed row. Data rows must match the header row's field count exactly. |
| physical line | A line as counted by newline characters in the raw input file (1-based). Error messages cite physical line numbers, because users see them in editors. |
| logical row | A parsed CSV row, which may span multiple physical lines when a quoted field contains newlines. |
| output object | One JSON object in the output array: a flat mapping of header names to that row's field values. |
| success condition | See §1. A run is successful iff it exits 0 and the output file contains the complete converted array. |

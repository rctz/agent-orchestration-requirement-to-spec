# Requirements — csv2json

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | requirements |
| version | v4 |
| status | DEPRECATED |
| date | 2026-09-16 |
| author | req2-req-designer |
| intake | appendix/00-intake.md |
| user decisions | appendix/01-user-decisions.md (round 1, 2026-09-16 17:38; round 2, 2026-09-16 17:53) |
| review folded | appendix/04-review-req-c1.md (req-review cycle 1, FAIL: F-01..F-12; folded as D-18..D-23) |

Note on names: the project slug `i-need-a-small-command-line-tool-csv2js` is
the board/workspace name (F-09); the tool and this document are `csv2json`.

## 1. Goal & success condition

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
the line number, and the tool exits with a non-zero status; a successful run
prints nothing to stdout; no third-party packages are required.

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

- Reading one UTF-8 text CSV file given as the first CLI argument, with a
  header row as its first row. Non-UTF-8 bytes are an error (REQ-011,
  user decision Q-04 → D-13); a leading UTF-8 BOM is stripped (REQ-012,
  user decision Q-05 → D-16).
- CSV parsing in the Python stdlib `csv` module **default dialect** — the
  operative definition, anchored once here and referred to everywhere as
  "the stdlib default dialect" (F-12): delimiter `,`, quote `"`, doubled
  quote `""` as the only escape, CRLF/CR/LF all treated as row terminators.
  RFC 4180 is approximated by this dialect, not guaranteed by it; wherever
  they disagree (blank lines, unclosed quotes), THIS document specifies the
  dialect's actual behavior (REQ-009, REQ-013). Quoted fields, embedded
  commas, embedded quotes (doubled), and embedded newlines inside quoted
  fields are handled per the dialect.
- Converting every data row to a JSON object keyed by header names; writing
  the array to the output file given as the second CLI argument.
- Field-count validation of every data row against the header, with a clear
  error message including the input line number.
- Meaningful exit codes (0 success, non-zero on failure) and error output on
  stderr.

### 3.2 Explicitly out of scope

- Type inference / type conversion: RESOLVED as "all strings" by the user
  (Q-01 → D-11); regardless, no user-defined type mapping exists.
- Any Graphical or web UI; the tool is CLI-only.
- Configuration files, environment-variable configuration, or named options
  beyond the two positional arguments.
- Streaming/incremental output for files that do not fit in memory (see
  NFR-003 for the chosen size envelope).
- CSV dialect auto-detection beyond the stdlib default (sniffing semicolon or
  tab dialects is not offered).
- Reading input from stdin or writing output to stdout.
- Pretty-printed / human-formatted JSON output: the user fixed the output
  shape as compact (Q-02 → D-11b); no formatting options are offered.
- Deduplication, sorting, filtering, or any transformation other than the
  row→object mapping.
- Windows-specific line-ending and code-page handling beyond what Python's
  default `newline=''` + UTF-8 handling already gives (recorded as D-08).

## 4. Functional requirements

Requirement IDs are `REQ-nnn` (kept stable across revisions; REQ-013 was
added in v4 — F-04 — with no renumbering). Each has
acceptance criteria concrete enough to test. All questions (Q-01..Q-04 in
round 1, Q-05..Q-06 in round 2) are answered; see §7 and
appendix/01-user-decisions.md.

### 4.1 Core conversion

**REQ-001 — CLI invocation form.**
The tool is a single Python file `csv2json.py`, executed as:
`python csv2json.py <input.csv> <output.json>`
Exactly two positional arguments, in that order (input first, output second).
*Acceptance:* running the command above with a valid input produces the output
file; running with zero, one, or three arguments fails with a usage message on
stderr and a non-zero exit code, and no output file is created. The usage
message is an error message like any other: it carries the fixed
`csv2json: error:` prefix (REQ-007 (a) applies to ALL error classes —
F-05), e.g. `csv2json: error: usage: csv2json.py <input.csv> <output.json>`.

**REQ-002 — header row defines keys.**
The first row of the CSV is always a header row; its fields, in order, are the
keys of every output object. Header fields are used verbatim (no trimming,
renaming, or case-folding). The header must contain at least one field: a
first parsed row of 0 fields is the invalid-header error of REQ-009 (it
would key every output object with nothing).
Duplicate header names are an error (user decision Q-03 → D-12): if any header
field value equals an earlier header field value, the tool fails per REQ-007
shape with line 1 and the duplicate name, e.g.
`csv2json: error: input.csv line 1: duplicate header name 'id'`.
*Acceptance:* for input whose first row is `id,name`, every output object has
exactly the keys `id` and `name`, in that insertion order; for header
`id,name,id` the run exits 1 with the duplicate-name error above and no output
file is created (REQ-010).

**REQ-003 — one object per data row.**
Each data row becomes one JSON object mapping each header key to the value of
the field at the same position. The output file contains a single JSON array
of these objects in input row order.
*Acceptance:* a 3-row CSV (plus header) yields a JSON array of exactly 3
objects in the same order.

**REQ-004 — quoted fields.**
Parsing handles quoted fields containing commas, escaped/doubled quotes
(`""` inside a quoted field), and newlines inside quoted fields, per the
stdlib default dialect (§3.1 — the operative definition; F-12).
*Acceptance:* a row `"a,b",c` parses to two fields `a,b` and `c`; a field
`"say ""hi"""` parses to `say "hi"`; a quoted field spanning two physical
lines parses as one field. For the unterminated-quote case at end of input
see REQ-013.

**REQ-005 — value mapping (strings only, lossless).**
Every field value appears in the JSON object exactly as a string — never as a
number, boolean, or null (user decision Q-01 → D-11). Empty cells become the
empty string `""`, never `null`. The mapping is lossless: leading zeros
(`"007"`), numeric-looking text (`"42"`, `"3.14"`), and boolean-looking text
(`"true"`) are preserved verbatim as strings.
*Acceptance:* CSV row `42,3.14,true,` produces JSON values
`"42"`, `"3.14"`, `"true"`, `""` (empty string, not null); row `007,`
produces `"007"`, `""`; no output value has a JSON type other than string.

### 4.2 Validation & error handling

**REQ-006 — field-count validation.**
Every data row must have exactly the same number of fields as the header row.
A row with fewer or more fields is an error.
*Acceptance:* header of 3 columns; a data row with 2 or with 4 fields each
cause the run to fail per REQ-008.

**REQ-007 — error message content.**
Every error message the tool can print — including usage/argument errors
and unreadable/unwritable-file errors, not only field-count and
duplicate-header errors — follows this shape (F-05):
(a) starts with the fixed prefix `csv2json: error:`,
(b) names the input file,
(c) gives the 1-based physical line number in the
input file where the offending row starts, and (d) gives the expected vs.
actual field counts. Example shape:
`csv2json: error: input.csv line 4: expected 3 fields, found 2`
For rows containing embedded newlines, the reported number is the line where
the row *starts*. (b)–(d) apply where they make sense for the error class
(a usage error has no line number; an unwritable-output error names the
output path); (a) applies to ALL error classes without exception.
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
- A completely empty file (zero bytes, no header at all) is an error:
  `csv2json: error: input.csv: file is empty (no header row)`, exit 1.
- A file whose FIRST parsed row is a 0-field row — e.g. a file containing
  ONLY blank physical lines (verified live: `csv.reader` on `"\n\n"` yields
  `[[], []]`), or a blank first line before any data — has no valid header:
  the header row must contain at least one field (a 0-field header would
  key every output object with nothing). This is an error with its own
  message, NOT the zero-byte empty-file error above and NOT a count
  comparison against a nonexistent header:
  `csv2json: error: input.csv line 1: invalid header row (found 0 fields)`,
  exit 1, no output file (REQ-010).
- Blank physical lines use the stdlib default dialect's row model (verified
  live, Python 3.13.5): a blank physical line parses as a **0-field row**
  (`[]`), never a 1-field row. It is therefore an ordinary wrong-field-count
  error per REQ-006, reported per REQ-007 with the count actually found
  (e.g. `... found 0`). (F-01: the v3 text wrongly modeled blank lines as
  `['']`.)
- Trailing newline discipline: exactly ONE terminator (`\n`, `\r\n`, or
  `\r`) after the last record is normal and produces no extra row; any
  further blank physical line — INCLUDING a trailing one (file ends
  `...\n\n`) — is the 0-field wrong-field-count error above, reported at
  that line number.
*Acceptance:* each of the five cases behaves as stated; in particular, a
1-column file `a\n\n1\n` FAILS at line 2 (`expected 1 fields, found 0`),
a 3-column file `a,b,c\n1,2,3\n\n` fails at line 3
(`expected 3 fields, found 0`), and a file of only blank lines `\n\n`
fails with the invalid-header error at line 1.

**REQ-010 — output file safety.**
On any error (bad arguments, unreadable input, parse error, validation error)
the tool must NOT create or truncate the output file. The output file is
written only after the whole input has been parsed and validated
successfully. If the output path is not writable, the tool exits 1 with a
clear `csv2json: error:` message.
*Acceptance:* run on an invalid CSV with a fresh output path → no output file
exists afterwards; run with an output path inside a non-writable directory →
exit 1 with a clear message.

**REQ-011 — strict UTF-8 input (user decision Q-04 → D-13).**
The input file is decoded as UTF-8, strictly. If the input contains bytes that
are not valid UTF-8 (e.g. Excel cp1252 or Windows-874 exports), the tool fails
BEFORE writing any output, with a clear `csv2json: error:` message naming the
input file, stating the byte sequence is not valid UTF-8, and giving the
1-based physical line number of the offending byte (F-06: the location form
is pinned as a 1-based line number, consistent with REQ-007; it is
"approximate" only in the ordinary sense that one line may contain several
bytes). Exits 1, no output file (REQ-010).
Lossy conversion (replacing undecodable bytes with U+FFFD or `?`) is
forbidden: the tool NEVER silently mangles text.
*Acceptance:* a file containing the single invalid byte sequence `0xFF` yields
an error message on stderr containing the input filename, the text "not valid
UTF-8" (or equivalent clear wording), and a `line N` reference (exit code 1,
no output file per REQ-010); an ASCII file and a UTF-8 file containing Thai
text (`ประเทศไทย`)
both convert successfully with the text intact in the JSON output.

**REQ-012 — UTF-8 BOM on input (user decision Q-05 → D-16).**
A leading UTF-8 byte-order mark (EF BB BF) is valid UTF-8, so REQ-011 does
not by itself decide its fate. The user decided: the BOM is STRIPPED from
the first header field, so keys come out clean — `id`, not `\ufeffid`
(user answer Q-05 (a), 2026-09-16 17:53). Only a BOM at the very start of
the file is removed; a U+FEFF appearing anywhere else in the input is data
and is carried through per REQ-005/D-14.
*Acceptance:* a valid CSV prefixed with a UTF-8 BOM whose header is
`id,name` produces objects keyed `id`, `name` (first key does NOT start
with U+FEFF), exit 0; the same file without the BOM produces
byte-identical output; a U+FEFF inside a cell (not at file start) is
preserved verbatim in the output string.

**REQ-013 — unterminated quoted field at end of input (F-04, D-19).**
If the input ends while a quoted field is still open (the file ends with an
odd number of quote characters inside a field started with `"` and never
closed — truncated transfer, editor accident), the tool treats this as a
structural error. Rationale: the stdlib default dialect is lenient here
(verified live: `csv.reader` returns the partial field content as a
complete row, e.g. `id,name\n"1,2` → `['1,2']`), and silently accepting
truncated input would violate the tool's contract of never mangling or
inventing data (REQ-011 preamble, D-11). The tool therefore pre-detects
unterminated quotes and reports, per the REQ-007 shape:

`csv2json: error: input.csv line 2: unterminated quoted field (opened at
line 2)`

- the cited line is the physical line where the unterminated field STARTS
  (consistent with REQ-007's row-start convention);
- the failure follows the full error contract: `csv2json: error:` prefix,
  stderr, exit 1, no output file (REQ-010), fail-fast precedence slot (7)
  in D-15, i.e. detected during row validation;
- this is a deliberate tightening over dialect leniency: a quote opened
  but never closed is an error EVEN IF the lenient parse would produce a
  field-count-valid row (the 1-column case `a\n"1` → `['1']` must error,
  not silently convert).
*Acceptance:* `id,name\n"1,2` (no closing quote) exits 1 with the message
above (line 2), no output file; `a\n"1` (1-column, lenient parse would be
a "valid" row) ALSO exits 1 with the same message shape at line 2;
`a,b\n1,2\n"x,y",2\n` (properly closed multi-line quote) converts
normally, exit 0.

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

- Input: CSV in the **stdlib default dialect** (F-10/F-12: the operative
  definition, §3.1) — delimiter `,`, quote `"`, doubled quote `""` as the
  only escape. No custom delimiters (out of scope, §3.2).
- Output: a single COMPACT JSON document (UTF-8, no BOM, no indentation, no
  trailing whitespace; a single trailing newline after the closing `]` is
  allowed), per user decision Q-02 → D-11b. Compact is contractual: it
  changes the bytes of every successful run's output, so it is fixed here, not
  left to the implementor. Non-ASCII characters are written as RAW UTF-8, not
  `\uXXXX` escapes (user decision Q-06 → D-17, `ensure_ascii=False`): a cell
  containing Thai `ประเทศไทย` appears in the output file as those actual
  characters.
- Output escape contract (D-14 as corrected by F-02): the serializer is
  `json.dumps(..., ensure_ascii=False)`, and the ONLY escapes it emits are
  - short two-char escapes where the JSON grammar provides them:
    `\f` (0x0C), `\b` (0x08), `\n` (0x0A), `\r` (0x0D), `\t` (0x09),
    `\"`, `\\`;
  - `\u00XX` (lowercase hex) for control characters WITHOUT a short form,
    e.g. NUL → `\u0000`, vertical tab 0x0B → `\u000b`;
  - everything else — including DEL 0x7F and the line separators
    U+2028/U+2029 — passes through RAW.
  Verified live on Python 3.13.5: form feed 0x0C serializes as the 2-char
  escape `\f` (v3's `\u000c` example was byte-wrong — F-02).
- Encoding: strict UTF-8 input per REQ-011 (user decision Q-04 → D-13);
  non-UTF-8 bytes are an error, never lossy-converted. A leading UTF-8 BOM
  is stripped per REQ-012 (user decision Q-05 → D-16).

## 6. Non-functional requirements

**NFR-001 — zero dependencies.**
The tool runs with the Python standard library only. No pip installs, no
third-party imports, no build step.
*Acceptance:* `grep` of the script shows imports only from the stdlib; the
tool runs on a bare Python installation.

**NFR-002 — target runtime.**
Python 3.9 or newer. The floor is a CONTRACT, not a freedom (F-07: v3's
"exact floor is implementor freedom" clause is deleted — it contradicted
the acceptance criterion below; register D-07 updated accordingly):
observable behavior must be identical on every supported version.
*Acceptance:* the script imports and runs on Python 3.9.

**NFR-003 — performance envelope.**
A 50 MB CSV (~250k rows) converts in under 30 seconds and under 1 GB RAM on a
typical laptop. In-memory processing is acceptable below this envelope;
larger files are out of scope (§3.2).
*Acceptance:* documented test with a generated 50 MB file completes within
the limits (spot check, not a hard gate).

**NFR-004 — error channel discipline.**
All errors go to stderr; only genuine results (if any) go to stdout. A
successful run prints NOTHING to stdout (silent success — user decision
Q-02 → D-11b).
*Acceptance:* successful run → empty stdout; failed run → REQ-007 message on
stderr, exit 1.

**NFR-005 — robustness against malicious/pathological input.**
The tool never executes, evaluates, or interpolates input content; field
values are data only. JSON output must always be valid JSON with proper
escaping (via the stdlib `json` module, §5.2 escape contract). A row of any
size (up to available memory) is processed without crashing the interpreter.
To make memory — not an arbitrary constant — the bound, the tool MUST raise
the csv module's per-field size limit to the maximum the platform allows
(e.g. `csv.field_size_limit(sys.maxsize)`) at startup (F-03: the stdlib
default limit is 131072 bytes per field — verified live — and raises
`_csv.Error("field larger than field limit")` for larger fields
regardless of available memory, which would fail NFR-005's own 10 MB
example). If memory is genuinely exhausted, the tool fails per the error
contract: `csv2json: error:` message naming the problem (e.g.
`csv2json: error: out of memory reading input.csv`), exit 1, no output
file (REQ-010).
*Acceptance:* input containing `<script>` sequences, a 10 MB single field,
and a single row totalling 10 MB spread across many fields — output stays
valid JSON, exit code reflects
validity of the CSV structure only, and none of them trips the 131072-byte
default field limit.

## 7. Decisions log

Live status is maintained in appendix/03-decision-register.md (machine-parsed).

### 7.1 Round-1 user answers (closed 2026-09-16)

All four open questions were answered by the user. Answers below are VERBATIM
from appendix/01-user-decisions.md (round 1, 2026-09-16 17:38):

> Q-01: (a) all values as strings, lossless. Empty cell stays empty string,
> not null. Q-02: (a) compact JSON, silent stdout on success. Q-03: (a) error
> out on duplicate header names, with line number 1. Q-04: (a) fail with a
> clear error on non-UTF-8 input, never lossy conversion.

| Q | topic | answer | where it landed |
|---|---|---|---|
| Q-01 | value types: strings vs. inferred numbers/booleans/null | (a) all strings, lossless; empty cell = `""`, never null | REQ-005, D-11 |
| Q-02 | output shape & success noise | (a) compact JSON, silent stdout on success | §1, §5.2, REQ-005, NFR-004, D-11b |
| Q-03 | duplicate header names policy | (a) error out, citing line 1 and the duplicate name | REQ-002, D-12 |
| Q-04 | non-UTF-8 input handling | (a) fail with a clear error, never lossy conversion | REQ-011, D-13 |

### 7.2 Points opened by the round-1 answers

Settling Q-01..Q-04 sharpens four points. Two are user-owned (they change
observable bytes/behavior of every run) and were asked as Q-05, Q-06 in
round 2; both are now ANSWERED (2026-09-16 17:53). The remaining two are
designer-owned contract details, decided in v2 as D-14, D-15:

> Q-05: (a) strip the leading UTF-8 BOM so header keys come out clean (id,
> not \ufeffid). Q-06: (a) raw UTF-8 output, ensure_ascii=False — keep real
> Thai characters in the JSON file.

(Verbatim from appendix/01-user-decisions.md, round 2, 2026-09-16 17:53.)

| Q | topic | why it matters | owner | status |
|---|---|---|---|---|
| Q-05 | UTF-8 BOM handling on input | a BOM is valid UTF-8, so Q-04's strictness does not decide it; keeping U+FEFF inside the first header key vs. stripping it changes every output object of BOM-prefixed files | user | ANSWERED: (a) strip → D-16 |
| Q-06 | non-ASCII output escaping (`ensure_ascii`) | changes the BYTES of every successful run containing non-ASCII text: Thai `ประเทศไทย` written as raw UTF-8 vs. as `\u0e1b\u0e23...` escapes — both are valid, compact JSON, but not byte-identical; the user's Q-02 answer fixed compactness only, not escaping | user | ANSWERED: (a) raw UTF-8 → D-17 |

Designer decisions closing the remaining consequence points (from v2,
with D-14 corrected in v4):

- **D-14 — exotic control characters are data.** Bytes that decode as valid
  UTF-8 control characters (NUL 0x00, form feed 0x0C, vertical tab 0x0B) in a
  cell are accepted and carried through, JSON-escaped, in the output. They
  are never treated as row separators or errors. The EXACT escaped forms are
  pinned by the §5.2 escape contract, which supersedes the escape examples
  given here in v3 (F-02: form feed serializes as the 2-char escape `\f`,
  NOT `\u000c`; NUL as `\u0000`; vertical tab as `\u000b`; short forms
  wherever the JSON grammar provides them).
  Rationale: per D-05/NFR-005 field content is data with no semantics, the
  stdlib `json` module escapes them to valid JSON, and this is the lossless
  behavior Q-01 mandates. (REQ-005/NFR-005 already imply this; recorded here
  to make it explicit and testable.)
- **D-15 — error precedence.** The tool validates in this fixed order and
  reports only the FIRST failure: (1) argument count (REQ-001); (2) input
  file readable; (3) whole-file strict UTF-8 decode (REQ-011 — before any
  parsing, because bytes must be decoded to parse); (4) empty file (REQ-009);
  (5) duplicate header names (REQ-002, line 1); (6) first structurally bad
  data row (REQ-006/007/008, fail-fast) — including unterminated-quote
  detection per REQ-013 (v4) and 0-field blank-line rows (v4 REQ-009);
  (7) output write (REQ-010 — output
  path writability is naturally discovered last, after the input is fully
  validated, preserving REQ-010's no-output-on-error guarantee). A file with
  both invalid bytes and structural errors therefore reports the UTF-8 error.

The authoritative, machine-parsed status of every decision (D-01..D-17
plus the v4 decisions D-18..D-23 below) lives in
appendix/03-decision-register.md.

### 7.3 Cycle-2 changes (v3 → v4, review findings F-01..F-12)

All twelve findings from appendix/04-review-req-c1.md (req-review cycle 1,
verdict FAIL) are folded. None required user input (all findings
`needs-user:false`; none contradicts a user decision — they refine the
stdlib mechanics underneath the six user answers). New designer decisions
D-18..D-23 (register updated); REQ-013 added (no renumbering); D-14's
escape examples corrected by the §5.2 escape contract; D-07's
freedom label dropped (F-07). Every stdlib-behavior claim was re-verified
live on Python 3.13.5 in this workspace (blank-line row model, escape
forms, field-size limit, unclosed-quote leniency) before folding.

| F | disposition | where it landed |
|---|---|---|
| F-01 | fixed | REQ-009: stdlib-faithful 0-field blank-line row model; `['']` model deleted; trailing-newline discipline pinned |
| F-02 | fixed | §5.2 escape contract (short forms `\f`, `\b`, ...; `\u00XX` otherwise; DEL/U+2028/U+2029 raw); D-14 cross-reference updated |
| F-03 | fixed | NFR-005: `csv.field_size_limit(sys.maxsize)` mandated; MemoryError behavior pinned to error contract |
| F-04 | fixed | REQ-013 (new): unterminated quote at EOF is a structural error; D-19 |
| F-05 | fixed | REQ-007: (a) applies to ALL error classes; REQ-001 usage message carries the prefix |
| F-06 | fixed | REQ-011: location = 1-based physical line number of offending byte |
| F-07 | fixed | NFR-002: floor is contract, not freedom; D-07 relabeled |
| F-08 | fixed | §7 pointer now cites D-01..D-17 + D-18..D-23 |
| F-09 | fixed | header note: slug is workspace name; tool/doc are `csv2json` |
| F-10 | fixed | §5.2 bullet 1: "stdlib default dialect" wording |
| F-11 | fixed | NFR-005 acceptance: `",,,,"` example dropped; 10 MB cases kept and made precise |
| F-12 | fixed | §3.1 anchor: "stdlib default dialect" is the operative term; RFC 4180 demoted to approximation |

## 8. Glossary

| term | definition |
|---|---|
| stdlib default dialect | The Python stdlib `csv` module's default dialect — the operative parsing definition of this document (§3.1): delimiter `,`, quote `"`, doubled quote `""` escape, blank physical line → 0-field row, unterminated quote at EOF → silently lenient (tightened to an error by REQ-013). Approximates RFC 4180 but is authoritative where they differ. |
| header row | The first row of the input CSV. Its fields become the keys of every output object. Never treated as data. |
| data row | Any parsed row after the header row. |
| field | One CSV cell, i.e. one element of a parsed row, after quote processing. |
| field count | The number of fields in a parsed row. Data rows must match the header row's field count exactly. |
| physical line | A line as counted by newline characters in the raw input file (1-based). Error messages cite physical line numbers, because users see them in editors. |
| logical row | A parsed CSV row, which may span multiple physical lines when a quoted field contains newlines. |
| output object | One JSON object in the output array: a flat mapping of header names to that row's field values. |
| compact JSON | The single-line JSON serialization chosen in Q-02: separators `,`/`:`, no indentation. Contractual output shape (§5.2). |
| BOM / U+FEFF | Byte-order mark: bytes EF BB BF at the start of a UTF-8 file, decoding to the character U+FEFF. STRIPPED from the file start per Q-05 → D-16 (REQ-012); a U+FEFF elsewhere is ordinary data (REQ-005). |
| lossless | The property (Q-01) that every input cell's exact text appears unchanged in the JSON output — no type coercion, no trimming, no character replacement. |
| success condition | See §1. A run is successful iff it exits 0 and the output file contains the complete converted array. |

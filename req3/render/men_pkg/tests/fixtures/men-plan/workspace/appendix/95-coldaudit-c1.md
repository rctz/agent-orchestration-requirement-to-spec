# Cold-handoff audit — cycle 1 (cold-audit c1)

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | coldaudit |
| cycle | 1 |
| date | 2026-09-20 |
| auditor | req2-cold-auditor |
| bundle read | requirements/07-requirements-v7.md (APPROVED); spec/16-spec-v16.md (APPROVED, v16); appendix/03-decision-register.md (D-01..D-59, all DECIDED); appendix/93-review-spec-c14.md (PASS, 0 findings); appendix/94-adv-c16.md (PASS, 0 P0/P1, 2 P2 + 1 P3 registered open in advisory-register.md); appendix/32-mechval-c16.md (PASS, 0 findings) |
| method | implementor simulation: read ONLY the bundle, build the implementation plan, record every stumble |
| verdict | READY (board: PASS) — zero blocking questions; 6 non-blocking assumptions, 3 evidence-status notes |

Nothing outside the named bundle was used. The register's two truncated-tail
rows (D-58/D-59) were re-read in full from the same bundle file; the spec's
truncated table rows (T-C8/T-C9/T-C16) were re-read in full from spec/16.
The advisory register (appendix/advisory-register.md) was consulted only to
confirm the adv-c16 P2/P3 dispositions are recorded (rows 226-228, owner
spec-designer, open).

## 1. Audit summary

The bundle is unusually complete. Sixteen spec-design cycles and eleven
adversarial cycles have pinned every trap a cold implementor would otherwise
hit: the newline='' handoff, the D-28 line basis with the tell()-span
arithmetic (csv.reader.line_num is contracted OUT for messages, with probe
evidence it lags), the per-record FSM with the CRLF-collapse counting rule
and the table-latch M, the header-checks-before-quote-scan order (S-9b
combined-defect case), the encode-before-open write order, the except-scoped
close-before-remove compensation with its D-53/D-54/D-57 window residues all
recorded as R-5/R-6 with owners, the closed 11-message catalog with verbatim
interpolation rules, the pinned import set, the two-valued exit contract with
manual dispatch as the ONE conforming shape, and the D-55 device-output
scope. Every stage's failure mode maps to a catalog id; every catalog id
maps to a test id; the mutation-contract table answers all 13 questions.

I was forced to make NO decision in the blocking categories (observable
behavior, lifecycle/state transitions, data integrity, security/
authorization, failure & recovery, persistence/ordering/retry/concurrency,
compatibility/limits, public interfaces, acceptance criteria). The three
open advisory items (adv-c16 F-01/F-02/F-03) are wording/gate-coverage
folds with zero behavior change and named owners — P2/P3 class, registered,
non-blocking by board policy.

Verdict: READY — the implementor builds csv2json.py from spec/16 alone.
Board mapping: verdict: PASS.

## 2. Implementation plan (what I would build, from the bundle alone)

Single file `csv2json.py`, stdlib imports pinned to `csv, io, json, os, sys`
(NFR-001/§9; D-52: argparse non-conforming). Layout order per §4: module
docstring, imports, limit-raise, exception types, pure helpers, stage
functions, main, entry guard.

Components (spec §2.1-§2.2, all contracts cited from spec/16):

1. **Limit raise** (§4.6, D-21/D-27) — module-level
   `csv.field_size_limit(sys.maxsize)` with the halving degrade loop on
   OverflowError. First code after imports; process-global.
2. **Exception hierarchy** (ADR-5, §6.3) — `ToolError` base;
   `InputReadError`, `InvalidUtf8Error`, `FieldError`, `OutputWriteError`
   subclasses carrying fully pre-formatted catalog messages; `main` is the
   single printer.
3. **`read_raw(path) -> bytes`** (§4.2) — binary whole-file read; any
   OSError -> `InputReadError` with `cannot read <path>: <strerror>`
   (E-READ).
4. **`decode_utf8(data, path) -> str`** (§4.2, REQ-011/012, D-13/D-16/D-23/
   D-28/D-31) — strict decode; on UnicodeDecodeError compute
   `line_of_offset(data[:e.start].decode("utf-8"), end)` and raise
   `<path> line <N>: byte 0x<hh> is not valid UTF-8` (lowercase hex,
   e.start lands on the sequence lead — adv-c16 probe 91 re-verified);
   after decode strip exactly one leading U+FEFF.
5. **`line_of_offset(text, offset)` + `count_line_breaks(text, i, j)`**
   (§4.2, D-28) — the ONE break basis: `\r\n` = one break (two chars),
   bare `\r` or `\n` = one break; VT/FF/NEL/U+2028/U+2029 = data.
   splitlines()-based counters are non-conforming.
6. **`parse(text, input_name) -> list[dict]`** (§4.3, the deep core) —
   see contract inventory below. I would implement the D-58 FUSED single
   pass (FSM transitions + break count + opening-line latch in one scan
   of each record span; remember line at every FIELD_START->QUOTED, never
   re-remember on CLOSED->QUOTED), because both forms are conforming and
   the fused form is the faster one at either binding (D-59 evidence).
7. **`serialize(rows) -> str`** (§4.4) — exactly
   `json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"`;
   no post-processing of escapes.
8. **`write_output(path, document)`** (§4.5) — encode FIRST
   (`document.encode("utf-8")`, D-43), then the reference shape verbatim:
   `fd = None; try: fd = open(path, "wb"); fd.write(payload); fd.flush();
   fd.close(); fd = None; except BaseException: (if fd is not None:
   best-effort close, then best-effort os.remove(path)) ; raise`.
   OSError -> `OutputWriteError` (`cannot write <out>: <strerror>`); KI
   re-raises (D-51, compensated); MemoryError propagates to main's net.
9. **`main(argv) -> int`** (§4.1) — manual `len(argv) != 2` branch ->
   prefixed usage line, return 1 (D-34/D-41/D-49/D-52). Two args: run
   stages in D-15 order. Handler chain (§7.3): `except MemoryError`
   FIRST (E-MEM phase form), then `except ToolError`, then
   `except Exception` (E-NET, repr form). One stderr write, return 1.
   Entry guard `sys.exit(main(sys.argv[1:]))`.

Build order: 1 -> 2 -> 5 -> 3 -> 4 -> 7 -> 8 -> 9 (shell last so every
stage's typed errors exist before the printer), then 6 (parse) wired into
main; parse is the only nontrivial logic and is pure, so it lands last
behind the already-tested decode/serialize/write stages.

Key build steps for parse (§4.3.2 loop): track running `line = 1`,
`start = 0`; per record `end = reader_file.tell()` AFTER `next()`;
record 1: 0-field check -> duplicate scan -> quote scan; every record:
quote scan -> count check; advance `line += count_line_breaks(text,
start, end)`; `start = end`. Raise at the first failing check of the
first failing record (D-29). Empty iteration (no record at all) ->
E-EMPTY (D-31).

## 3. Contract inventory (every API/schema/type/state machine I would implement)

| # | contract | source |
|---|---|---|
| C-1 | CLI: `python csv2json.py <in> <out>`, exactly 2 positionals; argc!=2 -> `csv2json: error: usage: csv2json.py <input.csv> <output.json>`, exit 1, no file created; manual dispatch is the ONE shape (argparse non-conforming) | spec §4.1, §6.1; REQ-001; D-34/D-41/D-49/D-52 |
| C-2 | Exit codes: 0 success / 1 EVERY failure (incl. usage); no exit 2 anywhere | spec §6.1, §6.4; REQ-001/008; D-34 |
| C-3 | Channels: stdout empty on every path (regular-file scope, D-55); exactly one stderr write per failed run; KI exits outside the matrix (signal 130) | spec §6.4, §4.1; NFR-004; D-51/D-55 |
| C-4 | Import set: `csv, io, json, os, sys` — closed; extra top-level import non-conforming | spec §4.1, §9 NFR-001; D-52 |
| C-5 | `read_raw(path) -> bytes`; OSError -> E-READ `csv2json: error: cannot read <in>: <strerror>` | spec §4.2, §6.3; D-15(2) |
| C-6 | `decode_utf8`: strict UTF-8; error -> `csv2json: error: <in> line <N>: byte 0x<hh> is not valid UTF-8` (N = D-28 line of the offending BYTE via prefix decode; 0x<hh> lowercase, e.start = sequence lead); lossy conversion forbidden | spec §4.2, §6.3 E-UTF8; REQ-011; D-13/D-23/D-28; adv-c16 probe 91 |
| C-7 | BOM: strip exactly one leading U+FEFF AFTER decode, BEFORE empty check; U+FEFF elsewhere is data | spec §4.2; REQ-012; D-16/D-31 |
| C-8 | `line_of_offset`/D-28 basis: `\n`, `\r\n` (ONE break), bare `\r` break; VT/FF/NEL/U+2028/U+2029 data; tool-wide; `str.splitlines()` non-conforming; `reader.line_num` never used for messages (lags on CRLF) | spec §4.2, ADR-2; D-28/D-38; QC-4 |
| C-9 | REQ-014 handoff: `csv.reader(io.StringIO(text, newline=""))` as parse's FIRST statement; universal newlines / plain StringIO / splitlines reconstruction forbidden | spec §4.3.1; REQ-014; D-24 |
| C-10 | Header rules (record 1 only, in order): 0-field -> `csv2json: error: <in> line 1: invalid header row (found 0 fields)`; duplicates (incl. 2nd empty name, verbatim `<name>`) -> `csv2json: error: <in> line 1: duplicate header name '<name>'`; empty name once = valid verbatim key; header verbatim, no trimming | spec §4.3.4, §6.3; REQ-002/009; D-12; F-33 |
| C-11 | Per-record check order: record 1 = header rules THEN quote scan (S-9b: `id,"id` -> E-DUP); data records = quote scan THEN count check; first failing check of first failing record wins; no pre-pass | spec §4.3.2, §5.2; REQ-013; D-15/D-25/D-29; SR1-F-02 |
| C-12 | Count rule: `len(row) != len(header)` -> `csv2json: error: <in> line <N>: expected <H> fields, found <F>` (N = row-start line); blank = EMPTY 0-field row -> `found 0`; whitespace-only line = 1-field data row, converts | spec §4.3.5, §6.3; REQ-006/009; D-36 |
| C-13 | Unterminated-quote FSM (4 states FIELD_START/UNQUOTED/QUOTED/CLOSED, per-record, over the record's own tell() span; quote opens ONLY at field start; `"` in unquoted field = data; post-close `"` re-opens, other -> UNQUOTED; record-relative counter collapses CRLF to ONE advance in every state; opening line latched at every FIELD_START->QUOTED) -> `csv2json: error: <in> line <N>: unterminated quoted field (opened at line <M>)`, N = row start, M = N + rel - 1; two-quantity or fused form both conforming | spec §4.3.2/§4.3.3; REQ-013; D-19/D-25/D-29/D-30/D-39/D-58 |
| C-14 | Row build: `dict(zip(header, record))`, input order; dict insertion order relied on (3.9+ promise) | spec §4.3.5; REQ-003/005; D-06 |
| C-15 | Empty iteration (no records after BOM strip) -> `csv2json: error: <in>: file is empty (no header row)` | spec §4.3 end, §6.3 E-EMPTY; REQ-009; D-31 |
| C-16 | `serialize`: `json.dumps(rows, ensure_ascii=False, separators=(",", ":"))` + one `\n`; escapes exactly json.dumps' forms (short forms; `\u00xx` lowercase; DEL/U+2028/U+2029 raw); no post-processing | spec §4.4, §6.2; REQ §5.2; D-11b/D-14/D-17/D-20/D-26 |
| C-17 | Output bytes: compact single line, ends `]\n` (0x5D 0x0A) on every platform; UTF-8 no BOM; raw non-ASCII; header-only -> `[]\n` (3 bytes) | spec §6.2; D-26/D-35; QC-3 |
| C-18 | Write stage: (1) `document.encode("utf-8")` COMPLETES before open (D-43); (2) `open(path, "wb")` binary ONLY (text-mode non-conforming, D-45); (3) write, flush, manual close, fd=None; except-scoped BaseException arm: if fd is not None -> best-effort close THEN best-effort `os.remove(path)`, then re-raise (D-48/D-50); at-open failures (fd None) run NO compensation, OSError forms leave target byte-untouched (D-46); KI/MemoryError-at-open = R-6 record (D-54/D-57) | spec §4.5; REQ-010; D-33/D-43/D-45/D-46/D-48/D-50/D-51/D-53/D-54/D-57 |
| C-19 | E-WRITE: `csv2json: error: cannot write <out>: <strerror>` (open/write/flush OSErrors; output path named) | spec §4.5, §6.3; REQ-007/010; D-33 |
| C-20 | E-MEM forms: read `out of memory reading <in>`; parse `out of memory while converting <in>`; serialize+write `out of memory writing <out>` (ONE output-named form, D-44); handler order MemoryError-first in main | spec §6.3, §7.3; NFR-005; D-44 |
| C-21 | E-NET: `csv2json: error: <in>: internal error: <exception repr>`; never a traceback; never swallows a cataloged class | spec §6.3, §7.3; REQ-007; D-42 |
| C-22 | Message-string verbatim rule: every interpolated slot (`<name>`, `<exception repr>`, `<strerror>`, `<path>`) verbatim, no escaping/sanitization; one stderr write; wire bytes environment-dependent (encoding-scope note) | spec §4.1 F-03 note, §6.3; adv-c8 F-04/adv-c9 F-04/F-05 |
| C-23 | Startup limit raise with halving degrade loop | spec §4.6; NFR-005; D-21/D-27 |
| C-24 | Run state machine: linear D-15 precedence (1 argc, 2 read, 3 decode, 3b handoff, 4 empty/header0, 5 dup, 6 per-record sequential, 7 write); S5 unreachable until parse accepts everything | spec §5.1-§5.2, §7.2; REQ-008; D-15 |
| C-25 | Signals: SIGINT-in-write compensated then re-raises (exit 130, outside matrix); double-KI / at-open KI / at-open MemoryError residues R-5/R-6 recorded; SIGKILL/SIGTERM-default out of scope | spec §6.4 note, §7.1, §10.1; D-51/D-53/D-54/D-57 |
| C-26 | Non-regular output paths: open/write/flush/close + exit 0 (D-55); same-path invocation = replace on success, R-4 on failed post-open; aliased targets R-1b; concurrent runs R-2 (out of scope) | spec §6.1/§6.4, §10.1; D-55; R-2/R-4/R-1b |
| C-27 | NFR-002 floor: 3.9-safe syntax (no match/`\|` at runtime), behavior identical across floor | spec §9; NFR-002; D-07 |
| C-28 | NFR-003 envelope: O(input) pipeline, incremental line counting, 50 MB/250k < 30 s/< 1 GB on the reference hardware class, diagnostic spot check | spec §9, QC-5; NFR-003; D-58/D-59 |

State machines implemented: the run-level linear machine (spec §5.1), the
parse-loop micro-states (§5.2), and the per-record 4-state FSM (§4.3.3)
with its counting rule (§4.3.3 normative paragraph) — three, all fully
specified with acceptance cases.

## 4. State & data ownership map

| state/data | owner | written where | lifetime |
|---|---|---|---|
| Input CSV file | user | never written by the tool (read-only; same-path R-4 exception documented) | beyond the run |
| Decoded text / record spans / row list | tool, in memory | parse stage only | process lifetime |
| Output JSON file | tool writes, user owns destination | write_output only: encode (no side effect) -> open("wb") -> write -> flush -> close; delete-on-failure compensation in the failure arm only | beyond the run; last successful run's bytes define it |
| csv.field_size_limit | tool, process-global | module import (§4.6) | process lifetime |
| stdout/stderr | tool (single printer in main) | one stderr write per failed run; nothing on success | process lifetime |
| Exit code | tool | main returns 0/1; KI exits via signal outside the matrix | observed by caller |

The output file is the ONLY mutable persistent state (spec §7.1); no
locks, no temp files, no persisted schema, no session. The mutation
contract (13 questions, §4.5 table) is fully answered — I verified all 13
rows exist and are mutually consistent with §5.1/§5.3/§6.3/§10.1,
including the R-4/R-5/R-6/R-1b residue cases.

## 5. Verification plan (what I would test, at which layer)

Mirror of spec §8 (the spec already enumerates it; I checked every catalog
id has a test id and every REQ AC appears):

- Unit (pure): T-U1 line_of_offset table; T-U2 record spans; T-U3 FSM
  incl. CRLF-interior and bare-CR-interior M=3 cases; T-U4 header rules;
  T-U5 count/blank/whitespace rules; T-U6 D-29 ordering + S-9b combined
  defect + `"id,name` -> E-UQ line 1; T-U7 serialize bytes; T-U8 limit.
- Contract: T-K1 all 11 templates parametrized over strerror, name forms
  (plain/empty/newline), path forms (incl. newline-bearing, verbatim);
  T-K2 golden bytes (happy, Thai, control chars, `[]\n`, CRLF-in-field);
  T-K3 exit/channel discipline (regular-file scope).
- E2E (real fs, subprocess): T-C1 usage incl. `-h` positionals both argc
  classes; T-C2 unreadable input (root-skips documented); T-C3 UTF-8
  incl. CR-only line 4; T-C4 empty/BOM-only/blank-lines; T-C5 duplicates;
  T-C6 count errors incl. whitespace-line converts; T-C7 all
  unterminated-quote shapes incl. N/M cases and `5" ruler` negative;
  T-C8 write failures (`/dev/full`, non-writable dir, read-only target,
  KI sub-case, at-open matrix entries); T-C9 envelope spot check
  (diagnostic); T-C10 E-NET no-traceback; T-C11/T-C12 byte-exactness and
  terminator mixes; T-C13 lossless/inert; T-C14 floor; T-C15 BOM E2E;
  T-C16 RLIMIT_AS E-MEM with phase-form-conditional state assertions.
- Static: import-set audit (NFR-001); 3.9 syntax check (T-C14).

The layer rule (unit for pure rules, contract for bytes/messages, real-fs
integration for the write stage, subprocess for channels) is stated and
followed; nothing material is certified mock-only (RLIMIT_AS is an
environment control, and the spec says so).

## 6. Required assumptions (guesses I had to make — all non-blocking)

| # | assumption | why the gap is non-blocking |
|---|---|---|
| A-1 | `parse` takes the input name as a second parameter — `parse(text, input_name)` — resolving the adv-c16 F-02 arity contradiction (Interface line says `parse(text: str)`, same bullet's prose says `parse(text, input_name)`). The reviewer's own disposition ("prefer the former — the messages need the name") and §2.2's responsibility table decide it; no message byte can differ between the shapes. | Local implementation detail; zero observable difference (F-02's own impact statement). Registered, owner spec-designer. |
| A-2 | `decode_utf8` receives the input path for its message (spec §4.2 interface lists `decode_utf8(data)` but the E-UTF8 template interpolates `<in>`). Same closure/parameter class as A-1. | Same class as A-1; §2.2's table already assigns decode the REQ-011 message duty. |
| A-3 | `read_raw` re-raises OSError content only as strerror text (directory-as-input -> E-READ) — validated live by adv-c16 probe 92 before I read it. | The "Any OSError -> E-READ" rule in §4.2 covers the class. |
| A-4 | Q-02's "silent" and NFR-004's "stdout empty" bind the tool's own writes; a `/dev/stdout` output target legitimately carries the document (D-55). I would not add a device check. | D-55 contracts exactly this, with live probes. |
| A-5 | For a data row that is BOTH count-bad and quote-unterminated in the SAME record, the quote scan (check 3) runs before the count check (check 4) per §4.3.2's pinned per-record order — E-UQ wins within the record. | §4.3.2 states the order explicitly ("on EVERY record the quote scan runs BEFORE the count check"); no guess was needed, recorded only because no acceptance case names this exact combination. |
| A-6 | The two-argument E-UTF8 formula uses `line_of_offset`'s second argument as the prefix's length (the formula in §4.2 is written `line_of_offset(data[:e.start].decode("utf-8"), len(...))` with a literal ellipsis). The probe-verified behavior (CR-only file -> line 4) pins the outcome; any implementation computing "D-28 line of byte offset e.start over the prefix" is equivalent. | The pinned acceptance case (REQ-011 AC, T-C3) fixes the observable; the ellipsis is prose compression, not ambiguity about behavior. |

## 7. Blocking questions

NONE. No gap in the blocking categories (observable behavior; lifecycle/
state transitions; data integrity; security/authorization — none exists,
REQ §2; failure & recovery — §6.3/§7.1 cover all 11 classes + KI windows;
persistence/ordering/retry/concurrency — §4.5 rows 7-9 + R-2;
compatibility/limits — NFR-001..005 + §6.1; public interfaces — §6 pinned
in full; acceptance criteria — every REQ AC has a pinned expected
outcome). No unreconcilable contradiction between bundle artifacts was
found: the requirements' D-15 precedence, the spec's §4.3.2 loop order,
and the S-9b/S-11 acceptance cases agree; the register's D-46/D-48/D-50/
D-53/D-54/D-57 chain matches spec §4.5's reference shape verbatim; mechval
c16 PASS and review c14 PASS with zero findings are consistent with the
text I read.

## 8. Claims without evidence (verification status of quality claims)

| # | claim | status |
|---|---|---|
| E-1 | "StringIO.tell() advances exactly with consumption for csv.reader" (QC-4 Assumption) | Probe-verified (P1, appendix/13, re-run in the c14 battery, rc=0). Evidence exists and was re-run — not a gap. |
| E-2 | json.dumps escape-form stability across 3.9..3.13 (QC-3 Assumption) | Probes ran on 3.13.5 only; single-interpreter host (adv-c16 §5.1 notes the same limitation for T-C14). Acknowledged assumption in the spec itself, with T-U7/T-K2 golden bytes as the detector. Acceptable. |
| E-3 | NFR-003 timing figures (25.7/14.9/19.9/9.1 s etc.) | Live, binding-controlled, run 3x (appendix/66; c14 re-ran 27/27 with the function-bound pair reproducing exactly and module-bound cells elevated under load with direction claims intact). Diagnostic, not a gate. |
| E-4 | "on default CPython stderr the Thai-name E-DUP message reaches the wire as verbatim UTF-8" (§6.3, §12) | TRUE for UTF-8-encodable messages (probe 93 W2) but over-broad as stated: an argv-borne raw-byte path (Linux surrogateescape) puts a lone surrogate in the message string and DEFAULT stderr's backslashreplace transliterates it (probe 93 W1). This is adv-c16 F-01 (P2, open, registered, wording-only, zero behavior change). Not a quality claim about the tool's own contract — the message STRING rule is honored; the wire form is environment-controlled, which the paragraph already says in its main clause. |
| E-5 | "Behavioral probes 66/77 and the permanent 13/14/15 are untouched and LIVE" (header) | True today (adv-c16 reviewer ran 66/14/15 green manually) but not machine-checked by gate 88 — adv-c16 F-03 (P3, open, registered). Evidence-hygiene note, not a contract claim. |
| E-6 | Windows-platform behaviors (close-before-remove vs PermissionError; `]\r\n` text-mode hazard) | No Windows host in evidence; contracted by mechanism with probe-backed reasoning (appendix/32 asserts fd.closed at remove time on POSIX). The pinned ordering is what rules the Windows mode out — the spec says exactly this in T-C8. Acceptable as contracted-mechanism claims. |

## 9. Verdict

verdict: READY (board mapping: PASS) — zero blocking questions.

The three open advisory items (adv-c16 F-01 P2 wire-form wording, F-02 P2
parse arity, F-03 P3 liveness-gate coverage) are registered in
appendix/advisory-register.md with owner spec-designer and are wording/
gate-coverage folds with no behavior change; per board policy P2/P3 never
block a verdict. A-1/A-2 track F-02 and resolve it the way the reviewer's
own disposition prefers; A-3..A-6 are bounded interpretation freedom that
cannot change any observable byte, exit code, or message.


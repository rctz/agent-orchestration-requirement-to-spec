# Review — requirements cycle 3 (csv2json)

| field | value |
|---|---|
| card | t_0350c9c6 [i-need-a-small-command-line-tool-csv2js#req-review#3] |
| kind | review-req-c3 |
| reviewer | req2-req-reviewer |
| date | 2026-09-16 |
| artifact | requirements/05-requirements-v5.md (v5, DRAFT) |
| verdict | FAIL (3 x P1, 2 x P2, 2 x P3) |
| method | Full read of v5 + appendix 00/01/02/03/advisory + archive v4 diff-check; every fold claim and every new finding grounded live on Python 3.13.5 (appendix/07-review-req-c3-probes.py, -probes2.py, -probes3.py, -probes4.py): newline-mode matrix re-run per F-13's verification clause, header-quote leniency per F-14's, separators/trailing-newline per F-19/F-20, plus new probes for physical-line counting, error ordering, quote-state corners, BOM-only files |

## Cycle-2 fold verification (F-13..F-20)

All eight cycle-2 findings (appendix/06-review-req-c2.md, verdict FAIL) are
verifiably folded into v5, re-verified live on Python 3.13.5 in this
workspace per each finding's "verification required" clause. No fold is
textual-only; each normative claim is backed by a passing probe.

| F | cycle-2 severity | verified fold |
|---|---|---|
| F-13 | P1 | REQ-014 (new) + §3.1 handoff bullet + D-15 step (3b) + D-24: `newline=''` handoff is normative ("MUST", "FORBIDDEN"), not an example. Newline matrix re-run live: CR-only `a,b\rc,d\r` → 2 rows under `newline=''` (probe 1); `"x\r\ny"` → `x\r\ny` and `"x\ry"` → `x\ry` byte-exact (probes 2–3); plain `io.StringIO(text)` still crashes with `_csv.Error` on CR-only (probe 4); universal-newline `newline=None` still mangles to `x\ny` (probe 5). REQ-004 gained byte-exact ACs; residual `_csv.Error` mapped onto REQ-007 ("never escapes as an unhandled traceback"). |
| F-14 | P1 | REQ-013 + D-25: detection "applies to the ENTIRE input, INCLUDING the header row", with the exact `"id,name` → exit-1-line-1 outcome as a new acceptance case, and the lenient `[['id,name']]` parse re-verified live (probe 6). Not routed through D-15 ambiguity anymore: D-15 slot (6) now says "including unterminated-quote detection over the ENTIRE input including the header per REQ-013". |
| F-15 | P2 | NFR-005 reworded to "largest value the running interpreter accepts — e.g. `csv.field_size_limit(sys.maxsize)`, degrading the requested value on OverflowError" + D-27. Matches the finding's required disposition verbatim. |
| F-16 | P2 | Register rows D-08/D-09/D-10 relabeled `DECIDED` with v5 sources, subjects folded into the row text; §3.2's D-08 bullet rewritten to cite the pinned contracts. Register now 27/27 DECIDED. |
| F-17 | P3 | REQ-009 bullets reordered — the two 0-field error classes sit adjacent (invalid-header bullet, then blank-line bullet) with the cross-reference sentence "(F-17 cross-reference: ...)". |
| F-18 | P3 | D-15 slot (4) reads "empty file / invalid header — 0-field first row (REQ-009; F-18: slot names both error classes ...)" and slot (5) "duplicate header names". |
| F-19 | P3 | §5.2: "terminated by exactly ONE trailing newline after the closing `]` (F-19: fixed as a MUST ...; the output file ends `]\\n`)". Permissive "allowed" deleted. |
| F-20 | P3 | §5.2: "COMPACT REQUIRES EXPLICIT SEPARATORS ... MUST pass `separators=(",", ":")` explicitly" + D-26. Re-verified live: `json.dumps` defaults produce `[{"id": "1"}]` (probe M), explicit separators produce `[{"id":"1"}]` (probe N). |

The cycle-2 theme ("observable-behavior forks the document never pinned")
is narrowed to two residual forks, both inside REQ-013's own wording
(F-22, F-24) and one counting-basis fork inside REQ-011/REQ-013 (F-21) —
see findings.

## Findings (P1 — blocking)

F-21 [P1|error-contract/line-counting-basis|needs-user:false]
  section/artifact: §8 glossary "physical line"; REQ-007(c); REQ-011; REQ-013
  bullets; REQ-009 line citations
  claim or missing contract: The glossary defines "physical line" as "a line
  as counted by newline characters in the raw input file" — but the document
  never pins WHICH characters count, and whether CRLF counts as one or two.
  This became load-bearing in v5: §3.1/REQ-014 (D-24) now make CR/CRLF/LF
  all row terminators, so CR-only and CRLF files are first-class valid
  inputs, and every line-citing error message must count lines in them.
  evidence: Live, Python 3.13.5 (appendix/07-review-req-c3-probes2.py,
  -probes3.py, -probes4.py):
  - CR-only file `a,b\rc,d\rc\r\xff`: REQ-011 decode error. Counting `\n`
    only → "line 1" (0 LF before byte 10); counting the terminator trio →
    "line 4" (3 CR). Two conforming messages for one input.
  - CRLF: `csv.reader.line_num` counts `\r\n` as ONE break (probe 1:
    rows at 1,2,3), but "counted by newline characters" read as
    count-each-char gives 2 per CRLF — a row on line 4 reported as line 7.
  - Data pollution: `str.splitlines()` — the natural prefix counter for the
    decode path — also breaks on VT 0x0B / FF 0x0C / NEL 0x85 (probes
    4a–4c), which D-14 and §5.2/D-20 classify as DATA (they can occur
    inside fields and must survive to the output). Prefix `a\nb\x0bc\n`
    before an invalid byte: LF-count basis → line 3; splitlines basis →
    line 4 — off by exactly the VT count.
  - `csv.reader.line_num` itself uses the trio, CRLF-as-one, VT/FF as data
    (probes 2, 3, 7) — i.e. one of the candidate bases, but the doc never
    says the decode-error basis must match it.
  minimal counterexample: `in.csv` = `a,b\rc,d\rc\r\xff` (CR-only, invalid
  byte on the 4th physical line). Implementation A (LF-count): `csv2json:
  error: input.csv line 1: ...not valid UTF-8`. Implementation B (trio,
  CRLF-as-one): `...line 4: ...`. Both satisfy every acceptance criterion
  in v5 (no AC pins a line number on any CR-terminated file).
  impact: Every error message's line number is unpinned for exactly the
  inputs v5 just legitimized (CR/CRLF files); spec-writer must guess the
  counter; tests cannot assert exact messages on half the terminator
  matrix.
  required disposition: One glossary-level definition, applied by REQ-007,
  REQ-011, REQ-013, REQ-009: a physical line break is exactly a row
  terminator per §3.1 — `\n`, `\r\n` (one break), or `\r` — counted in the
  DECODED text; VT/FF/NEL/U+2028/U+2029 are data and never break lines
  (consistent with D-14, D-20, and `csv.reader.line_num`, which conforming
  row-level implementations get for free). Add one AC: a CR-only file with
  a short row reports the trio-based line number.
  decision owner: req-designer
  verification required: req-review cycle 4 re-runs the CR/CRLF/splitlines
  probes against the revised glossary and checks the basis is normative
  (not an example).

F-22 [P1|error-precedence/pre-scan-vs-sequential|needs-user:false]
  section/artifact: REQ-013 ("The tool therefore pre-detects
  unterminated quotes over the whole decoded input") vs D-15 slot (6)
  ("detected during row validation ... detected at the offending row")
  claim or missing contract: REQ-013's "PRE-detects ... over the whole
  decoded input" mandates a whole-input pre-pass; D-15 slot (6) folds
  quote detection into "first structurally bad data row" fail-fast
  sequencing "at the offending row". When a field-count-bad row
  PRECEDES the row containing the unterminated quote, the two sentences
  produce different errors.
  evidence: Live (appendix/07-review-req-c3-probes.py batch 2):
  `id,name\n1\n"2,3` parses leniently to `[['id','name'], ['1'], ['2,3']]`
  — row 2 is count-bad (1 field ≠ 2), the quote opens in row 3 and never
  closes. Reading A (REQ-013 pre-pass first): `csv2json: error:
  input.csv line 3: unterminated quoted field (opened at line 3)`.
  Reading B (D-15 sequential first-bad-row): `csv2json: error:
  input.csv line 2: expected 2 fields, found 1`. No acceptance criterion
  in v5 covers the combination (REQ-013's four ACs all have the quote in
  the first thing that can fail).
  minimal counterexample: the file above; exit 1 either way, but the
  error class and cited line differ between two implementations each
  satisfying every AC.
  impact: spec-writer must guess the ordering; conformance tests written
  from either reading disagree.
  required disposition: Pick one ordering and delete the contradicting
  phrasing. Recommended: sequential fail-fast (the count error at line 2
  wins; the quote error fires when its row is reached) — it matches
  REQ-008/D-10's first-invalid-row philosophy, D-15's "at the offending
  row" wording, and keeps every existing REQ-013 AC outcome unchanged
  (`"id,name`→line 1, `a\n"1`→line 2, `id,name\n"1,2`→line 2 — verified:
  in each, the quote's row is the first thing that fails). Rewrite
  REQ-013's "pre-detects over the whole decoded input" to express SCOPE
  (the header row included, D-25), not a pre-PASS. Add one AC:
  `id,name\n1\n"2,3` → line 2 count error.
  decision owner: req-designer
  verification required: cycle 4 re-runs the counterexample probe and
  checks the AC exists.

F-23 [P1|error-contract/req013-two-line-numbers|needs-user:false]
  section/artifact: REQ-013 message shape and its first bullet
  claim or missing contract: The message carries TWO line numbers —
  `line N: unterminated quoted field (opened at line M)` — but the
  requirement defines only one ("the cited line is the physical line
  where the unterminated field STARTS") and every example/AC has N == M
  (the unterminated field is always its row's first field, opening at
  the row's start line). For a non-first unterminated field the mapping
  of N and M is undefined, and the bullet's equation of field-start
  with "REQ-007's row-start convention" is itself the confusion: the
  two conventions DIVERGE precisely in that case.
  evidence: Live (appendix/07-review-req-c3-probes2.py probe L):
  `h1,h2\n"a\nb",c,"d\ne` → one row starting at line 2 whose third
  field opens at line 3 and never closes. Defensible messages:
  (a) `line 2: ... (opened at line 3)` — N = row-start (REQ-007(c)),
  M = field-open; (b) `line 3: ... (opened at line 3)` — bullet-literal,
  N = field-open; (c) `line 2: ... (opened at line 2)` — both row-start.
  No AC decides.
  minimal counterexample: the file above; three conforming outputs.
  impact: spec-writer must invent the message for multi-field rows with
  late opening quotes — realistic whenever a wide row's last column is
  truncated.
  required disposition: Define both: N (the cited line) = the line where
  the offending ROW starts (REQ-007(c) convention); M ("opened at") =
  the line where the unterminated field's opening quote sits. Add one AC
  with a non-first-field case (e.g. the probe file → `line 2 ...
  (opened at line 3)`).
  decision owner: req-designer
  verification required: cycle 4 spot-check.

## Findings (P2 — minor, non-blocking)

F-24 [P2|detection-gloss/parity-misread|needs-user:false]
  section/artifact: REQ-013 parenthetical "(the file ends with an odd
  number of quote characters inside a field started with `"` and never
  closed)"
  claim or missing contract: Read carefully (quotes counted only inside
  the still-open section of a field that started with `"`), the gloss is
  consistent with the operative condition "the input ends while a quoted
  field is still open". But it is the only algorithm-shaped text in the
  requirement, and read loosely (whole-file quote parity) it mis-fires
  on valid files: `desc,qty\n5" ruler,2\n` has one quote character,
  parses cleanly to `[['desc','qty'],['5" ruler','2']]` (live,
  probes4.py probe 1), yet a parity scanner flags it "unterminated".
  Similarly `"a"b"c` → `[['ab"c']]` (closed section + junk quote; live,
  probe 5a). No AC in v5 covers a quote character inside an UNQUOTED
  field, so a parity implementation passes every published AC and still
  rejects valid input.
  evidence: probes4.py probes 1–2 (odd total, valid file), probes3.py
  5a–5d (dialect corners: `x"y` data, `"a""` unterminated, `say "hi"`
  data).
  minimal counterexample: `in.csv` = `desc,qty\n5" ruler,2\n`;
  parity-implementation exits 1 "unterminated quoted field",
  state-machine implementation exits 0 — both pass all v5 ACs.
  impact: bounded (the correct reading is determinable from §3.1 + the
  primary clause) but the failure is silent rejection of realistic data
  (inch marks, quoted speech in unquoted fields).
  required disposition: Replace the parenthetical with the explicit
  condition — quoted section opens only where a field STARTS with `"`
  (per the §3.1 dialect; a `"` elsewhere in an unquoted field is data) —
  and add a negative AC: a file with `5" ruler`-style data converts,
  exit 0.
  decision owner: req-designer
  verification required: cycle 4 spot-check.

F-25 [P2|error-routing/bom-only-file|needs-user:false]
  section/artifact: REQ-012 (BOM strip) × REQ-009 (empty/edge rows) ×
  D-15 slot (4)
  claim or missing contract: A file containing ONLY a UTF-8 BOM
  (`\xef\xbb\xbf`, 3 bytes) is decodable (REQ-011 passes), BOM-stripped
  per REQ-012 (yielding the empty string), and parses to ZERO rows
  (live, probes4.py probes 8–10: `list(csv.reader(io.StringIO("")))` =
  `[]` — not even a 0-field row). REQ-009's two no-header error classes
  do not cover it: the "file is empty (no header row)" bullet is
  conditioned on a ZERO-BYTE file (false here — 3 bytes), and the
  "invalid header row (found 0 fields)" bullet is conditioned on a
  first PARSED row with 0 fields (there is no parsed row). Both
  routings exit 1 with a REQ-007-shaped message, but the class and text
  differ.
  evidence: probes4.py probes 8–10 (decode → `\ufeff`, strip → `""`,
  reader → `[]`); REQ-009 bullets 2–3 conditions quoted above.
  minimal counterexample: `in.csv` = `\xef\xbb\xbf`. Outcome A:
  `csv2json: error: input.csv: file is empty (no header row)`.
  Outcome B: `csv2json: error: input.csv line 1: invalid header row
  (found 0 fields)`. Both defensible; no AC decides.
  impact: bounded (one pathological input, exit 1 either way), but the
  spec-writer must pick a message with no textual basis.
  required disposition: One sentence in REQ-009 or REQ-012: a file
  that is empty AFTER BOM stripping (BOM-only, or BOM + only blank
  lines... which already routes to invalid-header via the 0-field first
  row) takes the "file is empty (no header row)" error (recommended:
  the post-strip text is what the parser sees; "zero-byte" should read
  "no bytes other than an optional BOM"). Add the BOM-only AC.
  decision owner: req-designer
  verification required: cycle 4 spot-check.

## Findings (P3 — editorial)

F-26 [P3|editorial/fold-regression|needs-user:false]
  section/artifact: REQ-007, sentence after the example shape
  claim: v5 reads "For rows containing embedded newlines, the reported
  number is the line where / starts." — the v4 words "the row *starts*"
  lost their subject in the v4→v5 edit (verified against
  archive/requirements/04-requirements-v4.md line 172-173, which reads
  "...the line where / the row *starts*"). The sentence is now
  grammatically broken mid-contract; meaning remains recoverable from
  v4/context.
  required disposition: restore "the row *starts*".
  decision owner: req-designer

F-27 [P3|register-hygiene/d15-summary-stale|needs-user:false]
  section/artifact: appendix/03-decision-register.md row D-15 vs
    requirements/05-requirements-v5.md §7.2 D-15
  claim: The register's D-15 row still summarizes the v3 shape ("args →
  readable → strict UTF-8 → empty file → duplicate header → first bad
  row → output write", source `03-requirements-v3.md §7.2`) while the
  v5 §7.2 D-15 text has gained step (3b) (REQ-014 handoff), the
  slot-(4) error-class split, and the slot-(6) whole-input quote scope.
  No contradiction (the register order is compatible), but the summary
  and source are two revisions stale — same staleness class F-16
  policed last cycle.
  required disposition: refresh the D-15 register row (mention 3b and
  the header-inclusive slot 6; source `05-requirements-v5.md §7.2`).
  decision owner: req-designer

## Decision-closure audit (mandatory)

Register `appendix/03-decision-register.md` exists and parses as the
expected table. Audit result:

- Allowed status values: all 27 rows (D-01..D-27, including D-11b) read
  `DECIDED`. None stuck at `USER_DECISION_REQUIRED` /
  `DESIGN_DECISION_REQUIRED` / `BLOCKED` while the requirements claim
  completeness. No false closure on status grounds. The F-16 relabels
  (D-08/D-09/D-10) landed as required, with v5 sources.
- Closed questions map: Q-01→D-11, Q-02→D-11b, Q-03→D-12, Q-04→D-13,
  Q-05→D-16, Q-06→D-17 — every closed Q-nn has its DECIDED row, verbatim
  answers preserved in appendix/01-user-decisions.md (rounds 1–2), each
  reflected in the REQs (re-checked against v5: D-11→REQ-005;
  D-11b→§1/§5.2/NFR-004; D-12→REQ-002; D-13→REQ-011; D-16→REQ-012;
  D-17→§5.2/§1).
- Cycle-2 fold decisions D-24..D-27 all exist as DECIDED rows and match
  the v5 texts they cite (checked row-by-row against REQ-014/REQ-013/
  §5.2/NFR-005).
- IMPLEMENTOR_FREEDOM mislabel check: zero rows carry the label now.
  No product decision is hidden behind a freedom label.
- Register vs normative-text staleness: D-15's summary row is two
  revisions behind the v5 §7.2 text it summarizes — see F-27 (P3). Not
  a false closure (statuses honest, order compatible), but the same
  staleness class F-16 policed.
- Unspecified behavior classification: three corners remain neither
  freedom nor out-of-scope: (1) the line-counting basis for error
  messages on CR/CRLF files (F-21, P1); (2) quote-error vs count-error
  ordering when both exist (F-22, P1); (3) REQ-013's N/M line-number
  mapping for non-first unterminated fields (F-23, P1); plus the BOM-only
  file routing (F-25, P2). Everything else unspecified is classified
  (§3.2 out-of-scope list explicit; IMPLEMENTOR_FREEDOM empty).

## Verdict

verdict: FAIL — 3 x P1 (F-21, F-22, F-23), 2 x P2 (F-24, F-25), 2 x P3
(F-26, F-27).

The cycle-2 theme is fixed and then some: all eight prior findings are
verifiably folded, every stdlib claim live-re-verified, the register is
27/27 DECIDED with zero freedom mislabels, and the newline-mode matrix
that motivated REQ-014 passes on every input class. What remains is the
second-order consequence of those same folds: by legitimizing CR/CRLF
files (REQ-014) and whole-input quote detection (REQ-013/D-25), v5 made
line counting and error ordering load-bearing without ever defining
them:

- F-21 — "physical line" is defined as "counted by newline characters"
  but never says which characters or how CRLF counts; on the CR-only
  files v5 just legitimized, the decode-error line is 1 or 4 depending
  on the counter, and the natural `splitlines()` counter also counts
  VT/FF/NEL — which D-14/D-20 classify as data. Fix: one normative
  counting basis (terminator trio, CRLF = one break, in decoded text).
- F-22 — REQ-013's "pre-detects over the whole decoded input" contradicts
  D-15 slot (6)'s "detected at the offending row" when a count-bad row
  precedes the unterminated quote (`id,name\n1\n"2,3`: line 2 vs line
  3). Fix: pick sequential fail-fast (recommended; all existing ACs
  keep their outcomes) and rewrite "pre-detects" to express scope, not
  a pre-pass.
- F-23 — REQ-013's message carries two line numbers but defines only
  one, and every published example has them equal; for a non-first
  unterminated field three messages are conforming. Fix: define N
  (row start) and M (field-open quote) separately, add one AC.

All findings are `needs-user:false`; none contradicts a user decision —
F-21 enforces the observability of Q-04/D-13's "line number" promise,
F-22 enforces Q-03/D-05/D-10's first-error philosophy, F-23 enforces
REQ-013's own message contract. P2/P3 rows appended to
appendix/advisory-register.md.

Cycle count note: this is review cycle 3 of the board's 5-cycle cap.
The three P1s are one edit-session's worth of designer work (one
glossary definition, one ordering sentence, one two-line message
definition); none re-opens a settled user decision.

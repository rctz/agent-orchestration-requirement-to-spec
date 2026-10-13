# Review — requirements cycle 4 (csv2json)

| field | value |
|---|---|
| card | t_a158cfd0 [i-need-a-small-command-line-tool-csv2js#req-review#4] |
| kind | review-req-c4 |
| reviewer | req2-req-reviewer |
| date | 2026-09-17 |
| artifact | requirements/06-requirements-v6.md (v6, DRAFT) |
| verdict | FAIL (1 x P1, 3 x P2, 2 x P3) |
| method | Full read of v6 + appendix 00/01/02/03/advisory + archive v5 diff-check; all 9 designer fold probes re-run live (9/9 PASS, Python 3.13.5); new-corner probes for this cycle in appendix/09-review-req-c4-probes.py (8/8) and appendix/09b-review-req-c4-write-probes.py (2/2) |

## Cycle-3 fold verification (F-21..F-27)

All seven cycle-3 findings (appendix/07-review-req-c3.md, verdict FAIL) are
verifiably folded into v6 — verified three ways: (1) the v5→v6 diff contains
a targeted edit for each finding exactly where §7.5 claims it landed;
(2) the designer's fold probes `appendix/08-fold-c4-probes.py` re-run live
in this workspace, 9/9 PASS on Python 3.13.5; (3) each normative claim
re-checked against the live behavior where this review independently
exercised the same inputs (A4/A5/A6 below and the prior probes).

| F | cycle-3 severity | verified fold |
|---|---|---|
| F-21 | P1 | Glossary "physical line" redefined on the terminator-trio basis (CRLF = one break, VT/FF/NEL/U+2028/U+2029 are data), made normative in REQ-007(c) inline, REQ-011 cites it with the CR-only `a,b\rc,d\rc\r\xff` → `line 4` acceptance case; D-28. Basis is stated as contract, not example; `str.splitlines()` explicitly named non-conforming (probe re-verified live: 3 breaks vs D-28's 2). |
| F-22 | P1 | REQ-013 rewritten from "pre-detects" to "detects during the sequential validation pass"; SCOPE-vs-pre-PASS distinction explicit; D-15 slot (6) de-contradicted; new ordering AC `id,name\n1\n"2,3` → count error at line 2 present in REQ-013 acceptance; D-29. Lenient parse behind it re-verified live (fold probe D-29 + review probe A4 file shape). |
| F-23 | P1 | REQ-013's first bullet now defines N (cited line = row-start line, REQ-007(c) convention) and M ("opened at" = line of the opening quote) separately, with the N < M worked example and the exact-message AC `h1,h2\n"a\nb",c,"d\ne` → `line 2 ... (opened at line 3)`; D-30. |
| F-24 | P2 | Parity parenthetical replaced by the dialect-exact condition (a quoted section opens only where a field STARTS with `"`; a `"` elsewhere in an unquoted field is data), embedded in REQ-013's opening sentence; negative AC `desc,qty\n5" ruler,2\n` → exit 0 with a NON-CONFORMING clause for rejecting builds; D-30. Verified live (fold probe + review probe A3 for the adjacent `\"a\"b\"c` corner). |
| F-25 | P2 | REQ-009's empty-file bullet now reads "zero bytes, or no bytes other than a leading UTF-8 BOM"; BOM-only AC added in REQ-009 acceptance AND in REQ-012 acceptance; D-31. Parse-behind-it verified live (fold probe D-31: strip → `""` → zero rows). |
| F-26 | P3 | REQ-007: "the line where / the row *starts*" — subject restored, confirmed in the v5→v6 diff hunk. |
| F-27 | P3 | Register D-15 row refreshed: mentions (3b), the slot-(4) split, slot (6) sequential-scope-per-D-29, source re-cited as `06-requirements-v6.md §7.2`; standing hygiene rule recorded as D-32. Verified against the register text. |

Register hygiene note (informational, no finding): D-28's register row cites
"probes 08-fold-c4" while REQ-007(c)'s inline basis is already normative —
consistent; D-15's row is current. The advisory register now carries F-24..F-27
disposition rows (fixed-in-v6), so no P2/P3 is unregistered.

## Findings (P1 — blocking)

F-28 [P1|error-contract/write-phase-failure|needs-user:false]
  section/artifact: §5.2 Formats (output bullet); REQ-010 — output file
  safety; NFR-005 (MemoryError clause); D-15 slot (7)
  claim or missing contract: v6 pins the behavior of every pipeline stage
  EXCEPT the final one: what happens when the output write itself fails
  AFTER it has started (disk full mid-write, quota exceeded, I/O error
  during write/flush). The document's only write-phase contracts are:
  REQ-010 "If the output path is not writable, the tool exits 1 with a
  clear `csv2json: error:` message" (a pre-write condition) and "the
  output file is written only after the whole input has been parsed and
  validated successfully" (an ordering guarantee). Neither addresses the
  class where writing has BEGUN and then fails — the tool has already
  created/truncated the destination, bytes may already be flushed, and
  the process faces: report or crash, which message shape, and what
  disposition of the partially-written file.
  evidence: Live, Python 3.13.5 (appendix/09b-review-req-c4-write-probes.py
  probe W1): `open("/dev/full", "w")` + write + flush raises
  `OSError errno=28 (No space left on device)` at flush time — i.e. after
  the (empty) file was created at open, a genuinely mid-write failure
  class that reqs never classify. The spec-writer faces at least three
  defensible behaviors for `csv2json: error: <what>` + what to do with
  the partial file: (a) report per REQ-007 shape (naming the output
  path, like the unwritable-path class), exit 1, leave the partial file;
  (b) report, exit 1, delete the partial file; (c) let it escape as an
  unhandled traceback — (c) violates REQ-007's "NEVER escapes as an
  unhandled traceback" clause only if write failures count as "any
  residual parse-time exception", which the text scopes to parse-time.
  No AC decides among them.
  minimal counterexample: output path = /dev/full (or any full disk):
  valid input, valid destination per REQ-010's pre-write check, run
  starts writing, ENOSPC at flush. Implementation A exits 1 with
  `csv2json: error: cannot write output.json: No space left on device`;
  Implementation B exits 0 silently (swallowed exception); both satisfy
  every acceptance criterion in v6 (REQ-010's ACs test only pre-write
  unwritable paths and error-before-parse cases).
  impact: A material failure contract (disk full is the canonical CLI
  failure) is missing; the spec-writer must invent message shape, exit
  code, and partial-file disposition; two conforming builds can differ
  in observable behavior (silent success vs loud failure) on the same
  input, and a silent-success build loses data while claiming exit 0.
  required disposition: One paragraph in REQ-010 (and mirror in D-15
  slot (7)): any failure DURING the output write (OSError incl. ENOSPC,
  EIO, EDQUOT; flush/close errors) is reported per the REQ-007 shape
  with the `csv2json: error:` prefix naming the OUTPUT path, exit 1
  (REQ-008/§4.2), stderr (NFR-005 channel discipline), and the partially
  written file is REMOVED (best-effort) — never left as a plausible
  complete JSON document, and never a silent success. Optionally allow
  the residual-exception clause to explicitly cover write-time OSErrors
  so a traceback can never escape. Alternatively the designer may pin
  "partial file left in place" — any single pinned disposition is
  acceptable; the P1 is the absence of a contract, not the choice.
  decision owner: req-designer
  verification required: req-review cycle 5 spot-checks REQ-010/d slot (7)
  text and, if a delete-on-failure clause appears, its consistency with
  REQ-010's no-truncate spirit.

## Findings (P2 — minor, non-blocking)

F-29 [P2|message-contract/usage-exit-code|needs-user:false]
  section/artifact: REQ-001 (usage error contract); §4.2 preamble
  ("Meaningful exit codes (0 success, non-zero on failure)")
  claim or missing contract: REQ-001 pins the usage message shape (the
  REQ-007(a) `csv2json: error:` prefix, F-05 fold) but not the exit
  code, beyond §3.1's generic "non-zero". Meanwhile every other error
  class in v6 is pinned to exit exactly 1 (REQ-008, REQ-009, REQ-010,
  REQ-011, REQ-012, REQ-013, NFR-005 MemoryError). The natural
  implementation paths diverge live: `argparse` exits 2 on usage errors
  (verified live, probe A7), while a hand-rolled argv check exits 1.
  evidence: appendix/09-review-req-c4-probes.py probe A7: argparse with
  one positional arg missing raises SystemExit(2). Two conforming
  builds: argparse-based → exit 2, hand-rolled → exit 1; both satisfy
  every v6 AC (REQ-001's AC says only "fails with a usage message ...
  and a non-zero exit code").
  minimal counterexample: `python csv2json.py only-one` → implementation
  A exits 2, implementation B exits 1; both pass all ACs.
  impact: bounded (exit code is observable but the doc's own preamble
  only promises "non-zero"), yet it is the one error class where two
  equally natural implementations fork on a trivially testable value.
  required disposition: One sentence in REQ-001: usage/argument errors
  exit with code 1 (consistent with all other classes; then an
  argparse-based implementation must override argparse's default 2), OR
  explicitly permit 2 for usage errors only. Either pin ends the fork.
  decision owner: req-designer
  verification required: cycle-5 spot-check.

F-30 [P2|output-contract/write-newline-translation|needs-user:false]
  section/artifact: §5.2 Formats (output bullet: "terminated by exactly
  ONE trailing newline after the closing `]` ... the output file ends
  `]\n`")
  claim or missing contract: The output contract pins the CONTENT bytes
  (compact, raw UTF-8, escape forms, `]\n` ending) but never states
  WHICH newline the write path emits or forbids translation ON WRITE.
  REQ-014's prohibition ("universal-newline translation anywhere in the
  pipeline is FORBIDDEN") is scoped to the decode→parse handoff; the
  serialize→disk handoff has no analogous pin. On Windows, Python's
  text-mode write translates `\n` → `\r\n`, and `json.dumps` never
  emits `\r` for a cell containing CR (it emits the two-char escape
  `\r`), so only the trailing newline is at stake: text mode on Windows
  yields `]\r\n`, binary/`newline=""` mode yields `]\n`. On POSIX both
  agree (verified live, probe W2: text-mode write of `]\n`-class bytes
  keeps them verbatim).
  evidence: appendix/09b-review-req-c4-write-probes.py probe W2: on
  Linux `open(p,"w")` + write(`'["x\r\ny"]\n'`) produces bytes
  `b'["x\\r\\ny"]\n'` verbatim — no translation on POSIX; the Windows
  divergence is standard Python text-mode behavior (universal newlines
  default on write). v6 never pins the write mode or the trailing-newline
  byte sequence on Windows.
  impact: bounded to non-POSIX platforms (one byte of the final record
  separator), but it is exactly the D-08 class: "line endings beyond the
  pinned contracts" — and the output-side line ending is not among the
  pinned contracts. A byte-exact golden-file conformance test on Windows
  fails against a POSIX-built golden, or vice versa, with no text to
  adjudicate.
  required disposition: One sentence in §5.2: the output file is written
  so that no newline translation occurs — the byte after the closing `]`
  is exactly `\n` (0x0A) on every platform (e.g. binary mode or
  `newline=""` on the write path); `]\r\n` is non-conforming.
  decision owner: req-designer
  verification required: cycle-5 spot-check.

F-31 [P2|edge-input/whitespace-only-line|needs-user:false]
  section/artifact: REQ-009 fourth bullet ("Blank physical
  lines use the stdlib default dialect's row model ... a blank physical
  line parses as a **0-field row**") and the glossary term "physical
  line"
  claim or missing contract: "Blank physical line" is never defined.
  The live dialect distinguishes: a truly empty line (`\n`) parses as a
  0-field row `[]`, while a WHITESPACE-ONLY line (e.g. `  \n`) parses as
  a 1-field row whose value is the spaces `"  "` (verified live, probe
  A1). REQ-009's fourth bullet says "a blank physical line parses as a
  0-field row" — read as covering whitespace-only lines, that claim is
  factually WRONG for the dialect; read as "empty line only", it is
  right but never says so.
  evidence: appendix/09-review-req-c4-probes.py probes A1/A2:
  `a\n  \n1\n` → `[['a'], ['  '], ['1']]` (spaces line = 1-field data
  row), `a\n\n1\n` → `[['a'], [], ['1']]` (empty line = 0-field row).
  For a 1-column file, `a\n  \n1\n`: empty-line reading → line 2 is a
  valid 1-field row `"  "` → converts; 0-field reading → error at
  line 2. Two conforming behaviors.
  minimal counterexample: `in.csv` = `a\n  \n1\n` (1-column): does the
  run convert (row 2 = `"  "`) or fail `expected 1 fields, found 0` at
  line 2? Both readings satisfy the v6 text.
  impact: bounded (spaces-in-data corners), but the fourth bullet's
  "blank line → 0 fields" claim is presented as dialect-faithful fact
  and is wrong for one natural reading of "blank"; spec-writer must
  guess whether `  ` rows convert.
  required disposition: Define "blank physical line" as a line whose
  content is empty (zero characters between terminators) and state that
  whitespace-only lines are ordinary data rows (1-field row whose value
  is the whitespace, verbatim per REQ-005) — matching the live dialect.
  One AC: 1-column `a\n  \n1\n` converts to
  `[{"a":"  "},{"a":"1"}]`, exit 0.
  decision owner: req-designer
  verification required: cycle-5 spot-check.

## Findings (P3 — editorial)

F-32 [P3|cross-reference/§3.1-exit-code-wording|needs-user:false]
  section/artifact: §3.1 last bullet ("Meaningful exit codes (0 success,
  non-zero on failure) and error output on stderr")
  claim: The scope bullet's "non-zero on failure" is the loosest exit-code
  wording in the document; every error REQ pins exit 1 (and F-29 above
  shows the usage class is the only unpinned one). Not contradictory —
  REQ-008 etc. tighten it — but a spec-writer grepping §3.1 for the exit
  contract finds the weakest form of it.
  required disposition: Optionally tighten to "0 on success, 1 on every
  failure (usage errors included — see REQ-001/REQ-008)" once F-29 is
  resolved; or leave and rely on the REQ-level pins.
  decision owner: req-designer

F-33 [P3|edge-input/empty-header-name|needs-user:false]
  section/artifact: REQ-002 ("Header fields are used verbatim (no
  trimming, renaming, or case-folding)")
  claim: A header row may legally contain an empty field name
  (`a,,b\n1,2,3\n` — two consecutive delimiters). "Used verbatim" then
  produces a JSON object with an empty-string key `""`, which is valid,
  lossless JSON (verified live, probe A8:
  `[{"a":"1","":"2","b":"3"}]`). The document neither permits nor
  rejects this; it follows from "verbatim" + the duplicate rule (an
  empty name duplicates only if it appears twice). Low-impact: the
  behavior is derivable, and it is the lossless one.
  required disposition: Optionally add one clarifying sentence to
  REQ-002 (empty header names are permitted keys, converted verbatim;
  only a SECOND empty name is a duplicate error per Q-03/D-12) and an
  AC. Not blocking.
  decision owner: req-designer

## Decision-closure audit (mandatory)

Register `appendix/03-decision-register.md` exists and parses as the
expected table. Audit result:

- Allowed status values: all 32 rows (D-01..D-32, including D-11b) read
  `DECIDED`. None stuck at `USER_DECISION_REQUIRED` /
  `DESIGN_DECISION_REQUIRED` / `BLOCKED` while the requirements claim
  completeness. No false closure on status grounds.
- Closed questions map: Q-01→D-11, Q-02→D-11b, Q-03→D-12, Q-04→D-13,
  Q-05→D-16, Q-06→D-17 — every closed Q-nn has its DECIDED row, verbatim
  answers preserved in appendix/01-user-decisions.md (rounds 1–2), each
  reflected in the REQs (re-checked against v6: D-11→REQ-005;
  D-11b→§1/§5.2/NFR-004; D-12→REQ-002; D-13→REQ-011; D-16→REQ-012;
  D-17→§5.2/§1).
- Cycle-3 fold decisions D-28..D-32 all exist as DECIDED rows and match
  the v6 texts they cite (checked row-by-row against the glossary,
  REQ-007(c), REQ-011, REQ-013, REQ-009/REQ-012, §7.2 D-15/D-32).
- IMPLEMENTOR_FREEDOM mislabel check: zero rows carry the label. No
  product decision is hidden behind a freedom label.
- Register vs normative-text staleness: none found this cycle. D-15's
  register row was refreshed per F-27 and matches the v6 §7.2 shape
  (mentions (3b), the slot-(4) split, slot (6) sequential scope).
  D-28..D-32 rows cite `06-requirements-v6.md` sections that exist and
  carry the pinned content.
- Unspecified behavior classification: the write-phase failure contract
  (F-28, P1) is the one remaining unspecified behavior that is neither
  implementation freedom nor out of scope — it is a missing material
  failure contract on the tool's final pipeline stage. The usage exit
  code (F-29) and output-side write newline (F-30) are the same class
  at lower severity; whitespace-only-line routing (F-31) is a
  definitional gap inside an existing REQ. Everything else unspecified
  is classified (§3.2 out-of-scope list explicit; IMPLEMENTOR_FREEDOM
  empty).

## Verdict

verdict: FAIL — 1 x P1 (F-28), 3 x P2 (F-29, F-30, F-31), 2 x P3
(F-32, F-33).

The cycle-3 theme is fully fixed: all seven prior findings are
verifiably folded (diff-verified, fold probes re-run live 9/9 PASS),
the register is 32/32 DECIDED with zero freedom mislabels and zero
stale rows, and the line-counting / error-ordering / N-M message
contracts that motivated D-28..D-31 hold on every input class this
review re-probed. The document is now convergent: this cycle's hunt
across the terminator matrix, quote-state corners, ordering
combinations, output-byte contract, and register consistency found
exactly one blocker, and it is the last unpinned pipeline stage rather
than a defect in any fold:

- F-28 — mid-write failure (ENOSPC/EIO/EDQUOT at write/flush) has no
  contract: REQ-010 pins only pre-write unwritability and the
  parse-before-write ordering; whether a partial output file is left,
  removed, or silently successed is implementor's choice in v6 — a
  missing material failure contract (probe W1: /dev/full raises
  OSError 28 at flush after the file was created). Fix: one paragraph
  in REQ-010 + D-15 slot (7) mirroring it.

The P2/P3 rows are recorded in appendix/advisory-register.md. All
findings are `needs-user:false`; none contradicts a user decision
(F-28 enforces REQ-010/REQ-007/NFR-004's own guarantees on the write
stage; F-29..F-33 pin corners underneath Q-02/Q-03's settled answers).

Cycle count note: this is review cycle 4 of the board's 5-cycle cap.
One P1 remains and it is a single-paragraph designer edit; the board
has budget for the fix-and-review round.

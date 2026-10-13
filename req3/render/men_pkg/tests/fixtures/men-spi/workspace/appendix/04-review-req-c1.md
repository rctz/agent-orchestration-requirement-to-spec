# Review — requirements cycle 1 (csv2json)

| field | value |
|---|---|
| card | t_014a9cf6 [i-need-a-small-command-line-tool-csv2js#req-review#1] |
| kind | review-req-c1 |
| reviewer | req2-req-reviewer |
| date | 2026-09-16 |
| artifact | requirements/03-requirements-v3.md (v3, DRAFT) |
| verdict | FAIL (4 × P1, 3 × P2, 5 × P3) |
| method | Full read of v3 + appendix 00/01/02/03; every stdlib-behavior claim re-verified live on Python 3.13.5 (csv reader row model, field_size_limit, json.dumps ensure_ascii=False escape forms, BOM decode, unclosed-quote-at-EOF) |

## Findings (P1 — blocking)

F-01 [P1|correctness/factual-model|needs-user:false]
  section/artifact: REQ-009 (§4.2), blank/edge rows; interacts with REQ-006/007
  claim or missing contract: REQ-009 states "a truly empty line parses as a 1-field
    row `['']`" as the mechanism behind "blank physical line between data rows is an
    error like any wrong-field-count row".
  evidence: Live probe (Python 3.13.5, stdlib csv, the exact mechanism §3.1/§5.2
    mandate): a blank physical line parses as `[]` (0 fields), NOT `['']`.
    `list(csv.reader(io.StringIO("a,b\n\nc,d\n"))))` → `[['a','b'], [], ['c','d']]`.
    The doc's `['']` model is factually wrong about the mandated parser.
  minimal counterexample: (a) 1-column file `a\n\n1\n` → header `['a']` (1 field).
    Under the doc's `['']` model the blank line is a VALID 1-field row → output
    `[{"a":""}, {"a":"1"}]`, exit 0. Under mandated stdlib behavior the row is `[]`
    (0 ≠ 1) → error, exit 1. Opposite observable outcomes from the same document.
    (b) 3-column file with a blank line: REQ-007(d) message is "found 0" (stdlib)
    vs "found 1" (doc model) — the AC's exact-message assertion
    ("yields exactly that message") cannot yield a clear verdict either way.
  impact: Implementors split into two behaviors; acceptance tests for REQ-009 are
    self-contradictory; spec-writer must guess.
  required disposition: State the stdlib-faithful row model: a blank physical line
    after the header parses as a 0-field row and is therefore a wrong-field-count
    error per REQ-006/007/008 (message cites the count actually found, e.g.
    "found 0"). Delete the `['']` parenthetical. Also close the adjacent gap: a
    file ending with a blank line (`...\n\n`) is currently unspecified — the
    normative sentence only covers blank lines "between data rows", while
    "trailing newline at end of file is normal" plausibly covers it. Pin: exactly
    one `\n` after the last record produces no extra row (normal); any further
    blank physical line (including a trailing one) is the wrong-field-count error
    above.
  decision owner: req-designer
  verification required: req-review cycle 2 re-runs the live probes against the
    revised text.

F-02 [P1|byte-contract/factual-model|needs-user:false]
  section/artifact: D-14 (§7.2), also asserted in §5.2 bullet 2
  claim or missing contract: "The only escapes in the output are the
    JSON-mandatory ones (quote, backslash, and the control characters of D-14)" —
    with D-14 listing the escape FORMS as `\\u0000`, `\\u000c`, `\\u000b`.
  evidence: Live probe: with `ensure_ascii=False`, `json.dumps` emits `\f` for
    0x0C and `\u000b` for 0x0B (short two-char escapes where they exist, `\\uXXXX`
    only for the rest); DEL 0x7F and U+2028/U+2029 pass through RAW; NUL becomes
    `\\u0000`. The doc's `\\u000c` example is factually wrong about the mandated
    serializer.
  minimal counterexample: A cell containing form feed 0x0C: the doc's stated
    output is the 6-char sequence `\\u000c`; the mandated stdlib serializer
    produces the 2-char sequence `\f`. A byte-exact fixture (e.g. an AC asserting
    the escaped form) flips pass/fail depending on which the implementor follows.
  impact: D-14 was recorded specifically "to make it explicit and testable" yet
    its examples are byte-wrong; any spec-level fixture or golden-file test
    derived from them fails against the mandated implementation path.
  required disposition: D-14/§5.2 must pin the contract to the serializer's
    actual behavior: output escaping is exactly `json.dumps(..., ensure_ascii=False)`
    short-form (two-char) escapes where the JSON grammar provides them (`\f`, `\b`,
    `\n`, `\r`, `\t`, `\"`, `\\\\`), `\\u00XX` otherwise, DEL and U+2028/U+2029
    passed through raw. Or, if `\\uXXXX`-everywhere is truly wanted, that is a
    different observable-bytes decision and needs its own D-row — but it cannot
    stay as the current mix of wrong examples.
  decision owner: req-designer
  verification required: req-review cycle 2 re-checks D-14 against the live
    `json.dumps` probe output.

F-03 [P1|missing-contract/runtime-limits|needs-user:false]
  section/artifact: NFR-005 (§6); interacts with §5.2 (stdlib csv mandated)
    and NFR-002 (Python 3.9+)
  claim or missing contract: "A row of any size (up to available memory) is
    processed without crashing the interpreter" — but the stdlib `csv` module
    has a default per-field size limit of 131072 bytes that raises
    `_csv.Error("field larger than field limit")` regardless of available memory.
  evidence: Live probe: a single quoted field of 200000 bytes raises
    `Error: field larger than field limit (131072)` under the mandated
    implementation path; only after `csv.field_size_limit(...)` is raised does
    it parse.
  minimal counterexample: 10 MB single field — literally the AC's own example —
    crashes the mandated implementation path. The AC as written cannot pass
    against stdlib defaults: the tool would need to explicitly raise the limit
    (e.g. to sys.maxsize), which the requirements never state.
  impact: The AC either forces implementors to guess (raise the limit? to what?
    error with what message?) or guarantees failure of the stated acceptance
    test.
  required disposition: Add an explicit requirement: the tool raises the csv
    field-size limit to the maximum the platform allows (e.g.
    `csv.field_size_limit(sys.maxsize)`) so memory, not an arbitrary constant,
    is the bound; and specify the failure behavior when memory IS exhausted
    (MemoryError → `csv2json: error:` message, exit 1, no output file per
    REQ-010).
  decision owner: req-designer
  verification required: req-review cycle 2 re-runs the 10 MB single-field probe
    against the revised NFR-005/implementation notes.

F-04 [P1|missing-contract|needs-user:false]
  section/artifact: REQ-004 / whole document (gap)
  claim or missing contract: No REQ specifies behavior for a TRUNCATED CSV —
    an unterminated quoted field at end-of-input (e.g. file ends mid-row, or a
    quote opened but never closed).
  evidence: Live probe: `csv.reader` on `"a,b\n"1,2"` (quote never closed) does
    NOT error; it silently returns the partial field content `['1,2']` as a
    complete row (GNU-style leniency, documented as such in CPython docs).
    The doc never decides accept-as-data vs reject.
  minimal counterexample: `in.csv` = `id,name\n"1,2` (2 header fields). The csv
    module returns a row `['1,2']` with 1 field → wrong-field-count error at
    line 2 citing "expected 2 fields, found 1". But a user staring at "found 1"
    for a file whose visible last line looks like one row with a stray quote
    gets a misleading diagnosis; and for a 1-column header, `a\n"1` parses to
    `['1']` = valid row → silently ACCEPTED truncated garbage.
  impact: Unspecified observable behavior for a realistic failure mode
    (truncated transfer, editor accident); spec-writer must guess
    accept/reject + message shape.
  required disposition: Add a REQ (or extend REQ-004/REQ-006) deciding: is an
    unclosed quote at EOF a structural error (recommended: yes, with its own
    message naming the line where the unterminated field starts, mapped to the
    `csv2json: error:` prefix and REQ-010 no-output guarantee), or accepted
    as stdlib-lenient data? Either is defensible; unspecified is not.
  decision owner: req-designer
  verification required: req-review cycle 2 re-runs the unclosed-quote probes
    (1-column and multi-column variants) against the revised text.

## Findings (P2 — minor, non-blocking)

F-05 [P2|message-contract|needs-user:false]
  section/artifact: REQ-001, REQ-010, REQ-011 (error shapes outside REQ-007)
  claim or missing contract: REQ-007 pins the message shape only for
    field-count/duplicate-header errors. For the other failure classes — bad
    arguments (usage), input file missing/unreadable, output path unwritable,
    UTF-8 decode failure — the doc requires only "a clear `csv2json: error:`
    message". Whether the fixed prefix (REQ-007 (a)) applies to the USAGE
    message specifically is left open (argparse's default usage output carries
    no such prefix).
  evidence: REQ-001 AC: "fails with a usage message on stderr" (no prefix
    requirement); REQ-007 (a): "Each error message must ... start with a fixed
    prefix `csv2json: error:`" — read literally, REQ-007 (a) already covers the
    usage message, but the REQ-001 AC never says so and the natural argparse
    path violates it.
  impact: Bounded stderr-shape variance across implementations; conformance
    tests must guess.
  required disposition: One sentence in §4.2: the `csv2json: error:` prefix is
    mandatory for ALL error messages including usage/argument errors (or
    explicitly exempt usage). Suggested message shapes for missing input and
    unwritable output would remove the last guesswork.
  decision owner: req-designer
  verification required: cycle 2 spot-check.

F-06 [P2|message-contract|needs-user:false]
  section/artifact: REQ-011 (§4.2), "approximate location of the offending byte"
  claim or missing contract: The FORM of "approximate location" is unspecified —
    byte offset? 1-based line number? Both are "approximate locations".
  evidence: REQ-011 AC only requires the message to contain the filename and
    "not valid UTF-8"; the location form is never pinned, while REQ-007 took
    care to pin line-number semantics for structural errors.
  impact: Two conforming implementations produce differently-shaped messages;
    the AC passes either way, so it does not actually test the location promise.
  required disposition: Pin the form (recommended: 1-based line number of the
    offending byte, consistent with REQ-007's physical-line convention) or drop
    the location promise from the normative text.
  decision owner: req-designer
  verification required: cycle 2 spot-check.

F-07 [P2|internal-consistency|needs-user:false]
  section/artifact: NFR-002 (§6) and D-07 (appendix/03-decision-register.md)
  claim or missing contract: NFR-002 says "Python 3.9 or newer. The exact floor
    is implementor freedom" — but the AC says "the script imports and runs on
    Python 3.9", which pins the floor at 3.9 and leaves nothing free.
  evidence: An implementor exercising the stated freedom (requiring 3.12) fails
    the AC; an implementor ignoring the freedom passes. The two sentences
    disagree about whether the floor is a contract.
  impact: Bounded (the AC resolves it in practice), but the freedom label in
    the machine-parsed register contradicts the normative AC.
  required disposition: Either delete "exact floor is implementor freedom"
    (floor IS 3.9, matching the AC and updating D-07's status accordingly) or
    restate the AC as "runs on the documented floor, which must be ≤ 3.9".
  decision owner: req-designer
  verification required: cycle 2 consistency check NFR-002 ↔ register D-07.

## Findings (P3 — editorial)

F-08 [P3|editorial|needs-user:false]
  section/artifact: §7 / §7.2 vs appendix/03-decision-register.md
  claim: §7.2 says "The authoritative ... status of every decision (including
    the ones already settled this cycle, D-01..D-15)" — but the register carries
    D-01..D-17 by then (D-16/D-17 settled before v3 was written).
  required disposition: Update the range to D-01..D-17.
  decision owner: req-designer

F-09 [P3|editorial|needs-user:false]
  section/artifact: §1 heading is "Requirements — csv2json"; table `project`
    field is `i-need-a-small-command-line-tool-csv2js`
  claim: Cosmetic title/project-name mismatch vs the card and workspace naming;
    no behavioral effect.
  required disposition: Optional rename to `csv2json` everywhere or note the
    project slug is the workspace name.
  decision owner: req-designer

F-10 [P3|editorial|needs-user:false]
  section/artifact: §5.2 bullet 1
  claim: "Input: single-character CSV" — reads as if it describes the file; it
    means the dialect's delimiter/quote are single characters (the stdlib
    default dialect).
  required disposition: Reword to "Input: CSV in the stdlib default dialect
    (delimiter `,`, quote `"`, escape-by-doubling)".
  decision owner: req-designer

F-11 [P3|editorial|needs-user:false]
  section/artifact: NFR-005 AC
  claim: `\",,,,\"` sequences (4 commas → 5 empty fields) is fine as data, but
    the AC already covers generic adversarial data; the example adds little and
    the quoting in prose is awkward.
  required disposition: Optional cleanup; keep at least the 10 MB field case
    (which is F-03's subject).
  decision owner: req-designer

F-12 [P3|editorial|needs-user:false]
  section/artifact: whole document
  claim: "RFC-4180-style" / "RFC-4180-compatible" / "RFC-4180 semantics" are
    used interchangeably; RFC 4180 is only approximated by the stdlib dialect
    (blank lines, unclosed quotes, CRLF nuance).
  required disposition: Pick one phrase and anchor it to "the stdlib csv
    default dialect" as the operative definition (the findings F-01/F-04 are
    exactly the corners where "RFC-4180" overpromises).
  decision owner: req-designer

## Decision-closure audit (mandatory)

Register `appendix/03-decision-register.md` exists and parses as the expected
table. Audit result:

- Allowed status values, row by row: D-01..D-06, D-11..D-17 → `DECIDED`;
  D-07, D-08, D-09, D-10 → `IMPLEMENTOR_FREEDOM`. All within the six allowed
  values; none stuck at `USER_DECISION_REQUIRED` /
  `DESIGN_DECISION_REQUIRED` / `BLOCKED` while claiming completeness. No
  false closure on status grounds.
- Closed questions map: Q-01→D-11, Q-02→D-11b, Q-03→D-12, Q-04→D-13,
  Q-05→D-16, Q-06→D-17 — every closed Q-nn has its DECIDED row, and each
  DECIDED row is reflected in the REQs:
  D-11→REQ-005, D-11b→§5.2/NFR-004, D-12→REQ-002, D-13→REQ-011,
  D-16→REQ-012, D-17→§5.2/§1. D-14/D-15 (designer decisions) are reflected
  in §7.2 and govern REQ-005/NFR-005 and the §4.2 precedence — with the
  factual errors covered by F-02 (D-14) and, for D-15, no errors found.
  D-01..D-06 intake decisions are all reflected (§1, §2, §3.1, REQ-001..006).
- IMPLEMENTOR_FREEDOM rows mislabel check: D-07 is contradicted by its own AC
  (see F-07 — the AC pins the floor, the freedom label is a mislabel in
  effect). D-08/D-09/D-10 are genuinely local, reversible,
  behaviorally-equivalent-class freedoms. No product decision is hidden
  behind a freedom label beyond F-07.
- Unspecified behavior classification: the one genuinely unspecified corner —
  truncated input / unclosed quote at EOF — is neither freedom nor out-of-
  scope; it is an unspecified observable behavior → F-04 (P1). The blank-line
  row model contradiction is F-01. After F-01..F-04 are resolved, remaining
  interpretation space is bounded/local.

## Verdict

verdict: FAIL — 4 × P1 (F-01..F-04), 3 × P2 (F-05..F-07), 5 × P3 editorial. P1s are concentrated in one theme: the document
mandates the Python stdlib implementation path (§3.1, §5.2) and then states
facts about that path that are observably false (F-01: blank lines parse to
0-field rows, not `['']`; F-02: escape forms; F-03: field-size limit) or omits
its sharp edges (F-04: lenient unclosed-quote-at-EOF). Each forces the
spec-writer to guess between two observable behaviors. All four are
req-designer-fixable without further user input (the users' six answers are
faithfully folded and none of F-01..F-04 contradicts a user decision — they
refine the stdlib mechanics underneath them).


# Review — requirements cycle 2 (csv2json)

| field | value |
|---|---|
| card | t_14b3aec0 [i-need-a-small-command-line-tool-csv2js#req-review#2] |
| kind | review-req-c2 |
| reviewer | req2-req-reviewer |
| date | 2026-09-16 |
| artifact | requirements/04-requirements-v4.md (v4, DRAFT) |
| verdict | FAIL (2 x P1, 2 x P2, 4 x P3) |
| method | Full read of v4 + appendix 00/01/02/03/advisory; every stdlib-behavior claim re-verified live on Python 3.13.5 (appendix/05-review-req-c2-probes.py, appendix/05b-line-num-probe.py, appendix/05c-separators-probe.py): row model, terminators, unclosed-quote leniency, field-size limit + overflow mechanism, escape contract byte-forms, BOM decode, newline-mode matrix, REQ-004 ACs, line_num semantics, default separators |

## Cycle-1 fold verification (F-01..F-12)

All twelve cycle-1 findings (appendix/04-review-req-c1.md, verdict FAIL) are
verifiably folded into v4. Every stdlib-behavior claim the folding introduced
was re-verified live on Python 3.13.5 in this workspace; none is stale.

| F | cycle-1 severity | verified fold |
|---|---|---|
| F-01 | P1 | REQ-009 now pins the stdlib-faithful row model: blank physical line parses as `[]` (probe: `"\n\n"` → `[[], []]`), reported with the count found; `['']` model deleted; trailing-terminator discipline pinned (one `\n`/`\r\n`/`\r` after the last record → no extra row, probe-verified; any further blank line → 0-field error) |
| F-02 | P1 | §5.2 escape contract re-verified byte-for-byte: `\f` for 0x0C, `\b` for 0x08, `\n`/`\r`/`\t`, `\"`, `\\`, `\u00XX` for the rest (NUL → `\u0000`, VT 0x0B → `\u000b`), DEL 0x7F and U+2028/U+2029 raw; U+0085 raw |
| F-03 | P1 | NFR-005 mandates `csv.field_size_limit(sys.maxsize)` at startup (default 131072 re-verified; 200k field raises, parses after raise); MemoryError pinned to the error contract |
| F-04 | P1 | REQ-013 added: unclosed quote at EOF is a structural error with its own message shape; lenient parses re-verified (`id,name\n"1,2` → `['1,2']`; `a\n"1` → `['1']`) |
| F-05 | P2 | REQ-007(a) prefix applies to ALL error classes; REQ-001 usage message carries it (example present) |
| F-06 | P2 | REQ-011 location pinned as 1-based physical line number of the offending byte |
| F-07 | P2 | NFR-002 floor is a contract; D-07 relabeled DECIDED |
| F-08 | P3 | §7 pointer cites D-01..D-17 + D-18..D-23 (verified against the register) |
| F-09 | P3 | Header note: slug is workspace name; tool/doc are `csv2json` |
| F-10 | P3 | §5.2 bullet 1 reads "stdlib default dialect" |
| F-11 | P3 | NFR-005 AC `",,,,"` example dropped; 10 MB cases kept, made precise |
| F-12 | P3 | §3.1 anchors "stdlib default dialect" as the operative definition; RFC 4180 demoted to approximation; glossary entry added |

Cycle-1 P1 theme ("the document misstates the mandated implementation path")
is resolved: all four factual misstatements are now stdlib-accurate.

## Findings (P1 — blocking)

F-13 [P1|parsing-contract/newline-handoff|needs-user:false]
  section/artifact: §3.1 (stdlib default dialect bullet), §5.2 encoding bullet,
    D-15 (§7.2 precedence step 3 "whole-file strict UTF-8 decode ... before any
    parsing"), REQ-004 (multiline AC), REQ-005 (lossless), NFR-005
  claim or missing contract: The document mandates (i) §3.1 "CRLF/CR/LF all
    treated as row terminators" and REQ-004's "newlines inside quoted fields
    are handled per the dialect", (ii) D-15 step 3: decode the WHOLE file to a
    string before any parsing (needed for REQ-011's line-numbered UTF-8 error
    and REQ-013's whole-input quote pre-scan), and (iii) Q-01/D-11 lossless
    carry-through. It never pins HOW the decoded string reaches `csv.reader`.
    That handoff has three observably different behaviors in the stdlib, and
    the requirements are satisfiable by implementations that contradict both
    (i) and (iii).
  evidence: Live newline-mode matrix (appendix/05-review-req-c2-probes.py
    batch 2, Python 3.13.5) on the mandated pipeline decode-then-parse:
    - Construction A, `csv.reader(io.StringIO(text))` (StringIO default):
      CR-only file `a,b\rc,d\r` RAISES `_csv.Error: new-line character seen
      in unquoted field` — a crash on a file §3.1 declares valid ("CR ...
      treated as row terminator"), whose error class appears in NO requirement
      (not REQ-007 shape, no prefix guarantee, not in D-15's precedence).
    - Construction B, any universal-newline path (`io.StringIO(text,
      newline=None)`): CR-only file parses to 2 rows (matching §3.1), BUT a
      CRLF inside a quoted field is silently TRANSLATED to LF — probe:
      `'x\r\ny'` becomes `'x\ny'` — violating the lossless mandate (Q-01/D-11:
      "every input cell's exact text appears unchanged in the JSON output").
      The same silent rewrite happens with the common `str.splitlines()`
      reconstructions.
    - Construction C, `newline=''` semantics (`io.StringIO(text, newline="")`
      or `open(path, newline="")`): CR-only parses to 2 rows AND CRLF inside
      quotes is preserved byte-exactly — the only construction satisfying
      §3.1 + REQ-004 + REQ-005 simultaneously.
  minimal counterexample: `in.csv` = `h,k\n"x\r\ny",2\n` (2 physical lines;
    CRLF inside a quoted field — the exact class REQ-004's multiline AC
    covers). Construction B output: `{"h":"x\ny","k":"2"}` (exit 0, silent
    mangle of user data). Construction C output: `{"h":"x\r\ny","k":"2"}`
    (exit 0, lossless). Both implement every REQ as written; byte-different
    public output from the same input.
  impact: Spec-writer must guess the handoff; two conforming
    implementations produce different public bytes for quoted-field CRLF, and
    a third crashes with an unclassified error on CR-only files (a classic
    old-Mac/Excel-export reality that §3.1 explicitly claims to support).
  required disposition: Pin the handoff as a contract, not freedom: after the
    whole-file decode, the text must be handed to `csv.reader` with
    `newline=''` semantics (e.g. `csv.reader(io.StringIO(text,
    newline=""))`), i.e. no newline translation or splitting may occur
    between decode and parse (universal-newline translation is FORBIDDEN as a
    lossy rewrite of quoted-field data). Additionally classify the residual
    `_csv.Error` classes (or guarantee they cannot occur): any parse-time
    exception the tool can still hit must map onto the REQ-007 error contract
    (prefix, exit 1, no output file).
  decision owner: req-designer
  verification required: req-review cycle 3 re-runs the newline matrix
    (CR-only file, CRLF-in-quotes, CR-in-quotes) against the revised text and
    checks the pinned construction appears normatively (not as an example).

F-14 [P1|error-routing/unclassified-header-quote|needs-user:false]
  section/artifact: REQ-013 vs D-15 (§7.2), REQ-002/REQ-009 (header handling)
  claim or missing contract: REQ-013's rationale says "silently accepting
    truncated input would violate the tool's contract of never mangling or
    inventing data" and mandates pre-detection of unterminated quotes — but
    its normative sentence scopes only to a field opened in a row whose
    opening line is cited; the acceptance criteria cover data-row cases only.
    The unclosed-quote-in-the-HEADER case is routable two ways under the
    document as written: as a REQ-013 structural error (the rationale
    demands it) or as an ordinary slot-5/slot-6 event (the lenient parse
    yields a valid-looking header → run may succeed).
  evidence: Live probe (batch 1): `csv.reader` on `"id,name` (unclosed quote
    in the header line, file ends) returns `[['id,name']]` — ONE field, a
    valid non-empty header. No duplicate check trips, no count check applies
    to the header, no data rows exist → per the document the run converts
    successfully: output `[]`, exit 0. That is silently accepting truncated
    input with the first header key mangled (`id,name` as one key — the file
    visibly intended two columns), exactly what REQ-013's rationale forbids.
    (Cf. `strict=True` probe: RAISES `Error: unexpected end of data` for this
    input — the stdlib can detect it; the requirements just never say the
    tool must, for this input.)
  minimal counterexample: `in.csv` = `"id,name` (single line, 8 bytes).
    Outcome A (per REQ-013 rationale extended to headers): exit 1, message
    `csv2json: error: input.csv line 1: unterminated quoted field (opened at
    line 1)`, no output file. Outcome B (per the normative text as routed by
    D-15: lenient parse, slot-5/6 checks pass vacuously): output `[]`, exit
    0. Both defensible readings of the SAME document → not spec-able.
  impact: Spec-writer must guess accept-vs-reject for a realistic truncation
    (first line cut mid-quote); the two outcomes are opposite observables
    (exit 0 with `[]` vs exit 1 with an error).
  required disposition: Extend REQ-013 (or add a sentence): the
    unterminated-quote detection applies to the ENTIRE input, including the
    header row — a file whose header row ends with an unclosed quote is the
    same structural error, cited at line 1. Alternatively, state explicitly
    that the header is exempt (and why that is not "accepting truncated
    input") — but one of the two must be pinned.
  decision owner: req-designer
  verification required: req-review cycle 3 re-runs the `"id,name` probe
    against the revised text and confirms the outcome is pinned one way.

## Findings (P2 — minor, non-blocking)

F-15 [P2|portability/floor-vs-mechanism|needs-user:false]
  section/artifact: NFR-005 (§6) — "the tool MUST raise the csv module's
    per-field size limit to the maximum the platform allows (e.g.
    `csv.field_size_limit(sys.maxsize)`)"
  claim or missing contract: `csv.field_size_limit` accepts a bounded C
    integer (C ssize_t/long depending on build), not "whatever the platform
    allows": passing a value above the interpreter's binding limit raises
    OverflowError AT STARTUP. The normative "MUST raise ... (e.g.
    `csv.field_size_limit(sys.maxsize)`)" is therefore only satisfiable
    as written on builds where `sys.maxsize` fits the binding — historically
    not the case on Windows CPython (32-bit C long), the environment where
    the standard fallback loop (`while OverflowError: shrink`) originates.
    NFR-002 declares "Python 3.9 or newer" with no OS restriction, so such
    builds are inside the supported floor.
  evidence: Live probe (Python 3.13.5, Linux): `csv.field_size_limit(2**64)`
    raises `OverflowError: Python int too large to convert to C ssize_t` —
    the accepted domain is the binding's C integer width, and the current
    limit itself is a C value (`131072`). `sys.maxsize` itself succeeds on
    this platform (probe X); the overflow behavior is what is unpinned.
  minimal counterexample: An implementation that follows the letter of the
    example on a build whose binding is narrower than `sys.maxsize` crashes
    with an unhandled OverflowError before argv handling — an error class
    with no REQ-007 mapping, no prefix, no exit-code contract.
  impact: Bounded on the mainstream POSIX/macOS/Win64-with-wide-ssize_t
    builds the project will realistically run on; a strict reading still
    forces the spec-writer to decide the exact raise-to-what value and
    failure behavior for narrow-binding builds.
  required disposition: Reword the MUST to "raise the limit to the largest
    value the running interpreter accepts (e.g.
    `csv.field_size_limit(sys.maxsize)`, degrading the value on
    OverflowError)" — or pin the exact expression and explicitly scope
    narrow-binding builds out. One sentence; not a design decision.
  decision owner: req-designer
  verification required: cycle 3 spot-check.

F-16 [P2|decision-register-hygiene|needs-user:false]
  section/artifact: appendix/03-decision-register.md rows D-08, D-09, D-10
  claim or missing contract: Three rows are still labeled
    `IMPLEMENTOR_FREEDOM` although v4 has since pinned their subjects as
    contracts:
    - D-08 (line endings out of scope "beyond default `newline=''` + UTF-8
      handling") — v4 §3.1 pins CR/CRLF/LF as terminators (contract), and
      F-13 shows `newline=''` handoff is load-bearing, not freedom;
    - D-09 (output JSON UTF-8 without BOM) — v4 §5.2 states "UTF-8, no BOM"
      normatively; also `json.dumps` emits no BOM anyway, and D-14/D-20
      already pin byte forms;
    - D-10 (fail-fast, exit 1, prefix) — v4 REQ-008/REQ-007/D-15 pin all
      three normatively.
    A machine-parsed register whose labels contradict the normative text it
    is parsed against is a false-closure surface: the mechanical validator
    reads `IMPLEMENTOR_FREEDOM` and stops looking.
  evidence: Register rows quoted above vs v4 §3.1/§5.2/REQ-007/REQ-008.
  minimal counterexample: n/a (register consistency).
  impact: Bounded now (v4 text is normative), but the register is the
    machine-parsed source of truth; stale labels will mislead the spec stage
    and the cold auditor.
  required disposition: Relabel D-08/D-09/D-10 to `DECIDED` with source
    `04-requirements-v4.md` (and, for D-08, fold in F-13's handoff contract
    when fixed). Pure register edit; no user input needed.
  decision owner: relabeled by req-designer (D-09 may be absorbed into D-20)
  verification required: cycle 3 decision-closure audit re-checks labels
    against the normative text.

## Findings (P3 — editorial)

F-17 [P3|editorial|needs-user:false]
  section/artifact: REQ-009 fourth bullet vs first bullet
  claim: The 0-field-first-row error's message is given as
    `invalid header row (found 0 fields)` while the blank-line row error per
    REQ-006/007 uses `expected N fields, found 0`; two differently-shaped
    messages for two different conditions is intentional and clear, but the
    REQ-009 bullet order (empty-file case between them) makes the mapping
    table-to-condition slightly hard to scan.
  required disposition: optional: reorder bullets so the two 0-field errors
    sit adjacent, or add a line of cross-reference. No wording change needed.
  decision owner: req-designer

F-18 [P3|editorial|needs-user:false]
  section/artifact: D-15 (§7.2) step (4) "empty file (REQ-009)"
  claim: Step (4) is labeled "empty file" but REQ-009 covers three distinct
    error classes (zero-byte file, 0-field first row, blank-line row); the
    precedence list does not name where the 0-field-first-row (invalid
    header) error sits relative to duplicate-header (slot 5). From the REQ
    texts the order invalid-header → duplicate-header is implied (a 0-field
    header cannot contain duplicates), so no ambiguity survives, but the
    slot labels could name the specific error classes.
  required disposition: optional: name slot (4) "empty file / invalid header
    (0-field first row)" and slot (5) "duplicate header names" for
    scan-ability. Behavior already determinable.
  decision owner: req-designer

F-19 [P3|editorial|needs-user:false]
  section/artifact: §5.2 output bullet — "a single trailing newline after the
    closing `]` is allowed"
  claim: "allowed" is permissive where the rest of §5.2 is contractual
    ("Compact is contractual ... fixed here"). Whether the output file ends with `\n` or not is an
    observable byte difference between conforming implementations; the doc
    declines to fix it here but never says whether the implementor MUST, MAY,
    or MUST NOT add it.
  required disposition: optional: either fix it (RECOMMENDED: write exactly
    one trailing `\n` — POSIX text-file convention, and the natural write
    idiom) or state "implementor's choice, not part of the contract". As
    written, "allowed" reads as MAY, which is a pinned MAY — acceptable, but
    worth one clarifying word.
  decision owner: req-designer

F-20 [P3|editorial|needs-user:false]
  section/artifact: glossary "compact JSON" entry; §5.2 output bullet
  claim: Glossary pins the byte form (separators `,`/`:`, no spaces) —
    unambiguous at the contract level. But the serializer named in §5.2,
    `json.dumps(..., ensure_ascii=False)`, does NOT produce that form with
    default arguments (verified live, Python 3.13.5, appendix/
    05c-separators-probe.py): default separators are `", "` / `": "`, i.e.
    `[{"id": "1"}, ...]` with a space after every comma. The compact bytes
    the glossary mandates require passing `separators=(",", ":")`
    explicitly. The doc's own example pair (`json.dumps(...,
    ensure_ascii=False)` in §5.2 vs the glossary form) is therefore not
    self-executing: followed literally, it yields non-compact output that
    violates the Q-02 decision the section says it is fixing.
  required disposition: one sentence in §5.2: compact output requires
    explicit `separators=(",", ":")` (serializer defaults include spaces).
  decision owner: req-designer

## Decision-closure audit (mandatory)

Register `appendix/03-decision-register.md` exists and parses as the expected
table. Audit result:

- Allowed status values, row by row: D-01..D-07, D-11..D-23 → `DECIDED`;
  D-08, D-09, D-10 → `IMPLEMENTOR_FREEDOM`. All within the six allowed
  values; none stuck at `USER_DECISION_REQUIRED` /
  `DESIGN_DECISION_REQUIRED` / `BLOCKED` while the requirements claim
  completeness. No false closure on status grounds.
- Closed questions map: Q-01→D-11, Q-02→D-11b, Q-03→D-12, Q-04→D-13,
  Q-05→D-16, Q-06→D-17 — every closed Q-nn has its DECIDED row, verbatim
  answer preserved in appendix/01-user-decisions.md, and each is reflected
  in the REQs (D-11→REQ-005; D-11b→§1/§5.2/NFR-004; D-12→REQ-002; D-13→
  REQ-011; D-16→REQ-012; D-17→§5.2/§1). Round-2 answers were folded
  faithfully (REQ-012/§5.2 wording matches the verbatim answers).
- Cycle-1 fold decisions D-18..D-23 all exist as DECIDED rows and match the
  v4 texts they cite (checked row-by-row against REQ-009/REQ-013/§5.2/
  NFR-005/REQ-007+001/REQ-011).
- IMPLEMENTOR_FREEDOM mislabel check: D-08/D-09/D-10 remain labeled
  IMPLEMENTOR_FREEDOM although v4 has since pinned their subjects
  normatively — see F-16 (P2). No product decision is hidden behind a
  freedom label in the sense of overriding a user decision; the mislabels
  are staleness, and the normative text wins; but the register is the
  machine-parsed surface, so it must be relabeled.
- Unspecified behavior classification: two corners remain neither freedom
  nor out-of-scope: (1) the decode→parse newline handoff (F-13, P1) — an
  observable-behavior fork with a user-decision violation on one branch;
  (2) unclosed quote in the header (F-14, P1) — accept/reject undecided.
  Everything else unspecified is classified (§3.2 out-of-scope list is
  explicit and complete for the tool's surface).

## Verdict

verdict: FAIL — 2 x P1 (F-13, F-14), 2 x P2 (F-15, F-16), 4 x P3 (F-17..F-20).
The cycle-1 theme is fixed: all twelve prior findings are verifiably folded
and every stdlib claim they anchored is now live-verified accurate. The two
new P1s are second-order corners the folding exposed, both designer-fixable
without user input:

- F-13 — the document mandates whole-file decode (D-15) and a dialect that
  treats CR/CRLF/LF as terminators (§3.1), but never pins how decoded text
  reaches `csv.reader`; the three stdlib handoffs observably diverge (crash
  on CR-only files / silent `\r\n`→`\n` rewrite inside quoted fields — a
  lossless-contract violation / correct `newline=''`). Fix: pin the
  `newline=''` handoff as contract and map residual `_csv.Error` classes
  onto the REQ-007 error contract.
- F-14 — REQ-013's own rationale (never accept truncated input) is not
  wired for the header row: `"id,name` with an unclosed quote parses as a
  valid 1-field header and converts successfully (exit 0, `[]`) under the
  text as routed by D-15. Fix: one sentence extending REQ-013 to the whole
  input including the header (or an explicit exemption).

All findings are `needs-user:false`; none contradicts a user decision — F-13
enforces Q-01/D-11 (lossless) and Q-02's compactness byte contract, F-14
enforces REQ-013's rationale. P2/P3 rows appended to
appendix/advisory-register.md.

# Spec review — cycle 3 — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| kind | review-spec |
| cycle | 3 |
| reviewer | req2-spec-reviewer |
| date | 2026-09-17 |
| spec under review | spec/04-spec-v4.md (DRAFT, 2026-09-17) |
| requirements baseline | requirements/07-requirements-v7.md (APPROVED, 2026-09-17) |
| verdict | **FAIL** — 1×P1, 1×P2, 4×P3 |
| counterexample probes | appendix/23-review-spec-c3-probes.py (this cycle, 13 checks PASS, live host Python; prior suites re-run: 13→63/63, 20→21/21, 22→19/19 PASS, rev4 delta audit D1–D4 PASS) |

Finding ids are scoped to this review and prefixed `SR3-F-nn`.

## Summary

The v4 spec is strong and the cycle-3/v4 folds are genuine: the SR1-F-01
CRLF counting fix is now pinned in the §4.3.3 normative rule and verified
at NEW boundaries this cycle (record-internal blank lines, mixed CRLF+CR
interiors, doubled-quote reopen — probes R1–R6, all matching D-28 truth);
the SR1-F-02 header check order is wired through §4.3.2/§5.2/S-9b/T-U6/
T-C7; the adv-c3 F-01/F-02 disposition (D-43 encode-before-open +
every-post-open-exception compensation) is consistently bound across
§2.2/§4.5/S-14/§6.3/§7.1/QC-2/T-C8/T-C16 with live W/S-series evidence;
F-03/F-04/F-05 folds verified present. One P1 blocks READY: the §6.3
E-MEM cell pins TWO different serialize-phase MemoryError observables
(input-named template vs the cell's own output-named NFR-005 gloss), and
NFR-005's APPROVED clause plainly covers serialization in its
"reported like any other write-time failure" sentence.

## Findings index

| id | severity | axis | section | one line |
|---|---|---|---|---|
| SR3-F-01 | P1 | 1+2 | §6.3 E-MEM vs §4.4/§7.1, NFR-005 | serialize-phase E-MEM message: template says `while converting <in>` (input-named), the same cell's NFR-005 gloss says write/serialize → "the OUTPUT path named" — two observables, one catalog |
| SR3-F-02 | P2 | 2 | §1 vs header/§11/register | "D-01..D-42" stale; live register + header + §11 say D-01..D-43 (all DECIDED) |
| SR3-F-03 | P3 | 1 | §5.1 diagram | WRITE_OUTPUT failure edge lists only OSError; the S5 MemoryError → REPORTING(memory) path is missing from the state diagram |
| SR3-F-04 | P3 | 1 | §4.5 parenthetical | text-mode "equivalent alternative ... with the SAME encode-before-open order" is incoherent (text mode has no encode call to hoist; literal reading writes bytes to a text file) |
| SR3-F-05 | P3 | 1 | §6.3 E-NET, §6.4, §4.1 | E-NET `<exception repr>` may carry raw newlines; the F-03 one-write scoping note names only E-DUP `<name>` |
| SR3-F-06 | P3 | 3 | §8.3 T-C16, §8.4 | which E-MEM phase form trips under RLIMIT_AS is build-dependent — state that any of the three forms is the accepted assertion |

(Full records follow.)

## SR3-F-01 [P1 | axis 1+2: internal contradiction + spec/REQ consistency | needs-user:false]

- section/artifact: spec/04-spec-v4.md §6.3 E-MEM row (template vs the same
  cell's NFR-005 gloss), against §4.4 error-paths ("out of memory while
  converting <in>", §6.3 cited), §7.1 E-MEM row, and requirements/07
  NFR-005 (write/serialize clause).
- claim or missing contract: the catalog's serialize-phase template is
  `csv2json: error: out of memory while converting <in>` (input path named),
  and §4.4 pins exactly that. The SAME §6.3 cell then glosses NFR-005 as
  "(NFR-005: a MemoryError during the output write/serialize is reported
  like any other write-time failure — the OUTPUT path named, D-33. ...)".
  These pin two different stderr observables for the SAME event class:
  input-named (`while converting in.csv`) vs output-named
  (`... writing out.json`). REQ NFR-005 (APPROVED) reads: "If exhaustion
  strikes during the output write or serialization, the run fails per the
  same contract ... and a MemoryError there is caught and reported like any
  other write-time failure" — per D-33/REQ-007(b)'s output-path provision
  "like any other write-time failure" names the OUTPUT path, so the
  requirements-conforming serialize-phase message names the output path.
- evidence: §6.3 E-MEM template segment "parse/serialize phases:
  `csv2json: error: out of memory while converting <in>`"; the same cell,
  30 words later: "the OUTPUT path named, D-33"; §4.4 error-paths pins the
  input-named form; NFR-005 clause quoted above (requirements lines
  556–561). The cell contradicts itself and the template contradicts the
  APPROVED clause.
- minimal counterexample: valid ~180 MB CSV on a box whose RLIMIT_AS kills
  `json.dumps` mid-serialize: requirements-conforming build prints
  `csv2json: error: cannot write out.json: ...`-family output-named line;
  spec-template-conforming build prints `csv2json: error: out of memory
  while converting in.csv`. Same exit 1, different observable stderr —
  T-K1 (parametrized over every §6.3 template) and any contract test
  written from NFR-005 disagree with each other.
- impact: an implementor cannot satisfy both pins; whichever they pick,
  the other reading fails a contract test. T-C16's phase-form assertion
  (`out of memory reading/while converting/writing ...`) inherits the
  ambiguity for the serialize phase.
- required disposition: pick ONE serialize-phase form and make §4.4, §6.3
  template, §6.3 gloss, §7.1 E-MEM row, and T-K1/T-C16 assert it. Either
  (a) serialize-phase form names the OUTPUT path (aligns with NFR-005's
  clause and D-33 — recommended; e.g. `out of memory writing <out>`,
  with the compensation cell noting no file is open yet at serialize
  time), or (b) keep the input-named form and record an explicit,
  req-designer-acked deviation from NFR-005's sentence in the spec
  (the gloss sentence must then be deleted, not left contradicting the
  template).
- decision owner: spec-designer (req-designer ack required for (b)).
- verification required: spec-review cycle 4 checks §4.4/§6.3/§7.1/T-K1/
  T-C16 all assert the single chosen form; mechval re-run.

## SR3-F-02 [P2 | axis 2: authoritative-artifact agreement | needs-user:false]

- section/artifact: spec/04-spec-v4.md §1 first paragraph vs header row,
  §11 decision-coverage paragraph, appendix/03-decision-register.md.
- claim or missing contract: §1 says "D-01..D-42 in
  appendix/03-decision-register.md are all DECIDED" — the live register
  holds D-01..D-43 (D-43 added in this very revision), and the spec's own
  header ("D-01..D-43, all DECIDED") and §11 ("D-01..D-43 are all DECIDED")
  say 43. Same staleness class as SR1-F-03 (a v3 fix that regressed in the
  v4 edit of §1's opening paragraph).
- evidence: spec line 23 ("D-01..D-42") vs line 13 (header, "D-01..D-43")
  and line 1271 (§11, "D-01..D-43"); register row D-43 DECIDED
  (appendix/03-decision-register.md line 50).
- minimal counterexample: n/a (mechanical cross-check).
- impact: the enumeration the implementor and cold auditor read FIRST (§1)
  disagrees with the register; mechval's decision-coverage check reads the
  register — a tightening would gate on it. Trust erosion only; no
  behavior ambiguity.
- required disposition: refresh §1's enumeration to D-01..D-43.
- decision owner: spec-designer.
- verification required: cycle-4 read-back; mechval re-run.

## SR3-F-03 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/04-spec-v4.md §5.1 state diagram (WRITE_OUTPUT
  failure edge).
- claim or missing contract: the diagram's failure edge from WRITE_OUTPUT
  lists only `OSError(after remove-compensation)` → REPORTING(write). S5
  MemoryError is a contracted, cataloged outcome of the same state (§4.5,
  §6.3 E-MEM write-phase form, §7.1 E-MEM row, S-14(d)/(e)) and routes to
  REPORTING(memory) — no edge depicts it. (SERIALIZE's MemoryError edge
  exists; the S5 one is missing.)
- evidence: §5.1 ASCII diagram lines vs §4.5 "MemoryError → the residual
  net (§7.3), reported as E-MEM's write-phase form" and S-14(e).
- minimal counterexample: n/a (diagram/prose coverage gap).
- impact: editorial; the prose pins the behavior three times. A reader of
  the diagram alone misses the S5-memory path.
- required disposition: add the edge (e.g. `WRITE_OUTPUT ── MemoryError
  (after compensation) ──► REPORTING(memory) ──► exit 1`).
- decision owner: spec-designer.
- verification required: none.

## SR3-F-04 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/04-spec-v4.md §4.5 operation-order parenthetical
  ("Equivalent conforming alternative: text mode `open(path, "w",
  newline="", encoding="utf-8")` with the SAME encode-before-open order").
- claim or missing contract: in text mode there is no `document.encode()`
  call to hoist — the D-43 encode step does not exist in that shape, so
  "the SAME encode-before-open order" is incoherent for the alternative;
  read literally it implies passing `payload` bytes to a text-mode write.
  The parenthetical was updated for D-43 but not re-derived for the
  text-mode shape.
- evidence: §4.5 parenthetical vs §4.5 steps (1)–(3) which define the
  encode as a distinct pre-open step.
- minimal counterexample: n/a (wording-level; the normative pinned shape
  is binary mode and unambiguous).
- impact: bounded confusion at one parenthetical; an implementor choosing
  the alternative must invent its own encode placement.
- required disposition: reword the parenthetical for the text-mode shape
  (e.g. "... alternative: text mode; the encode becomes the implicit
  encoding of the write call, and the D-43 guarantee is delivered by the
  write path's own every-exception compensation plus no pre-open
  side-effect step") or drop the alternative.
- decision owner: spec-designer.
- verification required: none.

## SR3-F-05 [P3 | axis 1: internal quality | needs-user:false]

- section/artifact: spec/04-spec-v4.md §6.3 E-NET template
  (`... internal error: <exception repr>`), §6.4, §4.1 one-line scoping.
- claim or missing contract: an exception's repr may legally contain a
  raw newline; the F-03 one-write scoping note (§4.1/§6.3 E-DUP note/
  §6.4) names only E-DUP's `<name>` as the data-borne-wrap case. The
  same physical-wrap situation is reachable via E-NET's `<exception
  repr>` (and, on Windows, via E-READ/E-WRITE `<strerror>`), where the
  scoping language does not explicitly apply.
- evidence: `repr(Exception("a\nb"))` == `'a\nb'` (live, this cycle's
  host Python).
- minimal counterexample: fault-injected residual exception carrying a
  newline in its message → E-NET line physically wraps → §6.4's "one
  catalog message (one stderr write ...)" wording is measurably
  incomplete for E-NET if the scoping is read as E-DUP-only.
- impact: wording-level; the F-03 scoping rationale (the tool adds no
  newline of its own) obviously extends, but the text names one class.
- required disposition: generalize the scoping clause to "interpolated
  data (E-DUP `<name>`, E-NET `<exception repr>`, OS `<strerror>`)" in
  §4.1/§6.3 note/§6.4.
- decision owner: spec-designer.
- verification required: none.

## SR3-F-06 [P3 | axis 3: verification alignment | needs-user:false]

- section/artifact: spec/04-spec-v4.md §8.3 T-C16, §8.4 bullet 2.
- claim or missing contract: T-C16 asserts "stderr matches the E-MEM
  phase form (`out of memory reading/while converting/writing ...`)" —
  but under a single low RLIMIT_AS the phase that trips is
  build-dependent (a chunked write may OOM at write; a bulk read at
  read; the row-list build at parse), and the serialize-phase form is
  the subject of SR3-F-01. A test author needs to know whether ANY of
  the three forms passes, or whether a specific one must be forced.
- evidence: §8.3 T-C16 wording; SR1-F-04/SR1-F-05 history showing this
  exact class of ambiguity gets folded late.
- minimal counterexample: run T-C16 twice against two conforming builds
  (one streaming the write in chunks, one writing bulk): the first trips
  `out of memory writing ...`, the second `... while converting ...` —
  a strict single-form assertion fails one of them.
- impact: bounded (the test can be written permissively), but the spec
  should say so; also inherits SR3-F-01's serialize-form ambiguity.
- required disposition: one sentence in T-C16: "any of the three phase
  forms is the accepted assertion (which phase trips under RLIMIT_AS is
  build-dependent); the pre-existing-output variant is form-independent."
- decision owner: spec-designer.
- verification required: none (test-outline note).

## Prior-fold verification (no new findings)

- SR1-F-01 (CRLF M arithmetic): verified at NEW boundaries this cycle —
  record-internal blank line inside a quoted field (R1: N=2, M=4 = D-28
  truth), mixed CRLF+bare-CR interior (R3: M=4 = truth), doubled-quote
  reopen with interior CRLF (R4: M=3 = truth), interior-blank + late
  opening quote (R6: M=4 = truth). All match `line_of_offset`/D-28; the
  §4.3.3 normative counting rule is internally consistent and consistent
  with the csv dialect (spans/fields agree, R1d/R5).
- SR1-F-02 (header check order): pinned in §4.3.2 (mandatory WHY block),
  §4.3.4(iii), §5.2, S-9b, T-U6, T-C7; `id,"id` → E-DUP line 1 wired as
  AC; `"id,name` → E-UQ line 1 unchanged. Consistent everywhere cited.
- adv-c3 F-01/F-02 (D-43): §2.2/§4.5/S-14(d)(e)/§6.3 E-MEM/§7.1
  E-WRITE+E-MEM rows/QC-2/T-C8/T-C16 all describe the SAME order and
  compensation scope; probes 22 W1–W4/S1–S4 re-run PASS (19/19); my P1
  probe re-verifies the encode-fault isolation live.
- adv-c3 F-03 (one-line scoping, option (a)): §4.1, §6.1, §6.3 E-DUP
  note, §6.4, §12 glossary all carry the print-discipline wording; T-K1
  parametrized over the newline-bearing name. Consistent (modulo
  SR3-F-05's E-NET generalization).
- adv-c3 F-04 (E-UTF8 N basis): §4.2 F-04 note + U-series regression
  guard (22) + T-C3 pinned. Verified.
- adv-c3 F-05 (R-1 record): §10.1 R-1 now carries owner/rationale/
  impact/mitigation/verification. Verified.
- Traceability (§11): every REQ-001..014/NFR-001..005 row designed,
  tested, evidenced; spot-checked against the REQ text; no invented
  scope found (§2.4 absence list matches REQ §3.2); no REQ reinterpreted
  (checked REQ-001/002/005/007/009/010/011/012/013/014 acceptance
  outcomes one by one against spec scenarios S-1..S-16).
- Test layers vs risk layers: write semantics → real FS (`/dev/full`,
  non-writable dir, pre-existing byte assertions); E-MEM → RLIMIT_AS
  child (environment control, not a mock); E2E → subprocess; pure
  semantics → unit. Aligned (modulo SR3-F-06's determinism note).
- Evidence claims re-run this cycle: appendix/13 (63/63 PASS),
  appendix/20 (21/21 PASS), appendix/22 (19/19 PASS), rev4 delta audit
  D1–D4 PASS on the current files.

## Verdict block

```
verdict: FAIL
artifact: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/spec/04-spec-v4.md
findings_file: /home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/24-review-spec-c3.md
findings:
- [SR3-F-01|P1|needs-user:false] §6.3 E-MEM cell vs §4.4/§7.1/NFR-005: serialize-phase MemoryError pinned BOTH input-named (`out of memory while converting <in>`, template + §4.4) and output-named (the same cell's NFR-005 gloss "the OUTPUT path named, D-33"); NFR-005's APPROVED clause covers serialization in "reported like any other write-time failure" -> pick ONE form ((a) output-named recommended; (b) needs req-designer ack) and align §4.4/§6.3/§7.1/T-K1/T-C16
- [SR3-F-02|P2|needs-user:false] §1: "D-01..D-42" stale — header/§11/register say D-01..D-43; refresh §1's enumeration
- [SR3-F-03|P3|needs-user:false] §5.1 diagram: WRITE_OUTPUT has no MemoryError edge to REPORTING(memory) though S-14(e)/§4.5/§7.1 contract it; add the edge
- [SR3-F-04|P3|needs-user:false] §4.5 text-mode "equivalent alternative ... SAME encode-before-open order" is incoherent (no encode call exists in text mode); reword or drop
- [SR3-F-05|P3|needs-user:false] §6.3 E-NET `<exception repr>` may carry raw newlines; F-03 one-write scoping names only E-DUP `<name>`; generalize the clause to all interpolated data
- [SR3-F-06|P3|needs-user:false] §8.3 T-C16: which E-MEM phase form trips under RLIMIT_AS is build-dependent; state that any of the three forms is the accepted assertion
summary: 1xP1 (§6.3 E-MEM serialize-phase message: template vs same-cell NFR-005 gloss pin different observables; NFR-005's APPROVED clause covers serialization) + 1xP2 stale D-enumeration + 4xP3; all c1/c2/adv-c3 folds re-verified genuine (probes 13:63/63, 20:21/21, 22:19/19, delta audit D1-D4, new SR3 probes 13/13 incl. CRLF/interior-blank/reopen M-arithmetic at new boundaries)
```

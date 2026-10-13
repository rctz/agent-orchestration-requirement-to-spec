# Advisory register — i-need-a-small-command-line-tool-csv2js

P2/P3 findings from reviews; never blocking, but never lost. Disposition is
one of: `fixed-in-vN` / `accepted-risk (see constraint C-nn)` / `deferred (reason)`.

| F | severity | disposition | owner |
|---|---|---|---|
| F-05 | P2 | fixed-in-v4 (REQ-007 (a) covers all error classes; REQ-001 usage message carries the prefix) | req-designer |
| F-06 | P2 | fixed-in-v4 (REQ-011 location pinned as 1-based physical line number) | req-designer |
| F-07 | P2 | fixed-in-v4 (NFR-002 floor is contract; D-07 relabeled DECIDED) | req-designer |
| F-08 | P3 | fixed-in-v4 (§7 pointer cites D-01..D-17 + D-18..D-23) | req-designer |
| F-09 | P3 | fixed-in-v4 (header note: slug is the workspace name; tool/doc are `csv2json`) | req-designer |
| F-10 | P3 | fixed-in-v4 (§5.2 "stdlib default dialect" wording) | req-designer |
| F-11 | P3 | fixed-in-v4 (`",,,,"` example dropped; 10 MB cases kept, made precise) | req-designer |
| F-12 | P3 | fixed-in-v4 (§3.1 anchor + glossary entry: "stdlib default dialect" is the operative term) | req-designer |
| F-15 | P2 | fixed-in-v5 (NFR-005 MUST reworded: largest accepted value, degrade on OverflowError; D-27) | req-designer |
| F-16 | P2 | fixed-in-v5 (register rows D-08/D-09/D-10 relabeled DECIDED with v5 sources) | req-designer |
| F-17 | P3 | fixed-in-v5 (REQ-009 cross-reference between the two 0-field error classes) | req-designer |
| F-18 | P3 | fixed-in-v5 (D-15 slot (4)/(5) label their error classes) | req-designer |
| F-19 | P3 | fixed-in-v5 (§5.2: exactly one trailing newline is a MUST; output ends `]`\n`; D-26) | req-designer |
| F-20 | P3 | fixed-in-v5 (§5.2: explicit separators=(",", ":") mandated; D-26) | req-designer |
| F-24 | P2 | fixed-in-v6 (REQ-013 parity gloss replaced by the dialect-exact condition; negative AC `5" ruler` → exit 0; D-30, probe 08-fold-c4) | req-designer |
| F-25 | P2 | fixed-in-v6 (REQ-009 "zero-byte" reads "no bytes other than an optional BOM"; BOM-only → empty-file error; D-31, probes 08-fold-c4) | req-designer |
| F-26 | P3 | fixed-in-v6 (REQ-007: "the row *starts*" subject restored) | req-designer |
| F-27 | P3 | fixed-in-v6 (register D-15 row refreshed to the v6 §7.2 shape, source re-cited; standing rule D-32) | req-designer |
| F-29 | P2 | fixed-in-v7 (REQ-001: usage/argument errors exit 1; argparse default 2 must be overridden — probe 10-fold-c5 F29; D-34) | req-designer |
| F-30 | P2 | fixed-in-v7 (§5.2: write path performs no newline translation — byte after `]` is exactly `\n` on every platform; binary or `newline=""`; `]\r\n` non-conforming; D-35) | req-designer |
| F-31 | P2 | fixed-in-v7 (REQ-009: "blank" = EMPTY, zero characters; whitespace-only lines are 1-field data rows verbatim per REQ-005; AC `a\n  \n1\n` → `[{"a":"  "},{"a":"1"}]`; glossary term added; D-36, probes 10-fold-c5 F31) | req-designer |
| F-32 | P3 | fixed-in-v7 (§3.1 tightened: "0 on success, 1 on EVERY failure including usage errors"; §1 success condition aligned) | req-designer |
| F-33 | P3 | fixed-in-v7 (REQ-002: empty header name permitted verbatim; second empty name = duplicate error; AC `a,,b` → `[{"a":"1","","b":"3"}]`; probes 10-fold-c5 F33) | req-designer |
| F-34 | P3 | fixed-in-v5 (D-07's register source cell refreshed to 07-requirements-v7.md §6 NFR-002 per D-32 standing rule, on the cycle-5 register touch that appended D-44; contract unchanged) | req-designer |
| F-35 | P3 | deferred (REQ-013 restates the no-pre-pass/D-29 clarification three times — v5/v6 fold sediment; consolidate on next designer touch of REQ-013; found in review cycle 5, non-blocking) | req-designer |
| SR1-F-03 | P2 | fixed-in-v3 (spec/03-spec-v3.md: header/§1/§11 enumeration refreshed to D-01..D-42; D-38..D-42 bound explicitly in the §11 coverage paragraph) | spec-designer |
| SR1-F-04 | P2 | fixed-in-v3 (new T-C16 owns the E-MEM RLIMIT_AS fault-injection case; wired in §7.1 E-MEM row, §8.3, §8.4, QC-1 Verification, §9.1-9.5 anchors) | spec-designer |
| SR1-F-05 | P2 | fixed-in-v3 (§6.3 E-MEM now phase-form: read `out of memory reading <in>`, parse/serialize `... while converting <in>`, write `out of memory writing <out>` — write phase names the OUTPUT path per NFR-005/D-33; §4.2/§4.4/§7.1 aligned) | spec-designer |
| SR1-F-06 | P3 | fixed-in-v3 (§4.1 table row: MemoryError has its own handler ahead of the typed net per §7.3 order; E-MEM per phase form) | spec-designer |
| SR1-F-07 | P3 | fixed-in-v3 (header + §1.3 now cite "63 checks PASS / TOTAL FAILURES: 0" instead of the wrong 70/70 count) | spec-designer |
| SR1-F-08 | P3 | fixed-in-v3 (S-1 corrected to 46 bytes; live-verified by appendix/20 R4) | spec-designer |
| SR1-F-09 | P3 | fixed-in-v3 (§6.2.6 corrected to 3 bytes; live-verified by appendix/20 R4) | spec-designer |
| SR1-F-10 | P3 | fixed-in-v3 (§8.4 macOS fallback is now a read-only/non-writable-mount directory failing open(); explicit Do-NOT-use-`ulimit -f` note with the SIGXFSZ rationale; ENOSPC flush-failure shape marked Linux-CI-only) | spec-designer |
| SR3-01 | P3 | evidence note (appendix/17-review-spec-c1-probes2.py: its inline per-character demo block crashes with NameError `row_text` after the substantive checks all PASS; reviewer-file typo, does not affect the review's evidence — the divergence it demonstrates is confirmed by R1b's PASS lines and re-verified fixed in appendix/20 R1) | spec-designer |
| adv-c3-F-03 | P2 | fixed-in-v4 (option (a) taken: "exactly one line" scoped to the tool's print discipline — one stderr write, no tool-added newline; data-borne breaks in E-DUP's `<name>` may wrap the single message physically; name stays verbatim, escaping declared NON-CONFORMING; spec/04-spec-v4.md §4.1/§6.3/§6.4/§12, T-K1 parametrized) | spec-designer |
| adv-c3-F-04 | P3 | fixed-in-v4 (one-clause §4.2 note added: E-UTF8 N is the offending byte's own D-28 line, not a row-start line) | spec-designer |
| adv-c3-F-05 | P3 | fixed-in-v4 (§10.1 R-1 restructured into the full accepted-risk record: owner, rationale, impact, mitigation, verification) | spec-designer |
| SR3-F-02 | P2 | fixed-in-v5 (§1 enumeration refreshed to D-01..D-44; header/§11/register consistent; spec/05-spec-v5.md §1) | spec-designer |
| SR3-F-03 | P3 | fixed-in-v5 (WRITE_OUTPUT ── MemoryError(after compensation) ──► REPORTING(memory) edge added; spec/05-spec-v5.md §5.1) | spec-designer |
| SR3-F-04 | P3 | fixed-in-v5 (text-mode parenthetical reworded: encode is implicit in the write call, D-43 outcome via every-exception compensation + no pre-open side-effect step; spec/05-spec-v5.md §4.5) | spec-designer |
| SR3-F-05 | P3 | fixed-in-v5 (scoping generalized to ALL interpolated data — E-DUP `<name>`, E-NET `<exception repr>` (raw newline reachable via custom `__repr__`, appendix/25 M1), OS `<strerror>`; §4.1/§6.3/§6.4/§12) | spec-designer |
| SR3-F-06 | P3 | fixed-in-v5 (T-C16: ANY phase form is the accepted assertion; which phase trips is build-dependent; pre-existing-output variant form-independent; spec/05-spec-v5.md §8.3) | spec-designer |
| SR4-F-01 | P3 | fixed-in-v6 (§5.2 now cites S-9b for the combined-defect duplicate-wins outcome; S-9(c) miscite gone; re-verified by appendix/28b-rev6-reviewer-reaim-probes.py P-c1/P-c2) | spec-designer |
| SR4-F-02 | P3 | fixed-in-v6 (moot: the v5 revision row citing "§5.3 S-4" was replaced by the v6 revision row, which cites the D-44 align set via §5.3 S-14 correctly; re-verified by appendix/28b P-e1/P-e3) | spec-designer |
| SR4-F-03 | P3 | fixed-in-v6 (§4.3.3 FIELD_START terminator gloss reworded to state the full reachable set: record-internal empty line, trailing empty field `a,\n`, or the empty record; scan never crosses record spans; re-verified by appendix/28b P-b4/P-b5) | spec-designer |
| SR5-F-01 | P2 | deferred (§4.5 Error paths summary bullet "both after the compensation has run" predates the D-46 fold — at-open failures run NO compensation; the normative rule is pinned redundantly (§4.5 body, §6.3 E-WRITE, §7.1, QC-2, glossary) and T-C8's at-open sub-case guards it; fold the qualifier on the next designer touch of §4.5; found in review cycle 5, non-blocking) | spec-designer |
| SR5-F-02 | P3 | deferred (§5.1 diagram WRITE_OUTPUT failure-edge labels "after remove-compensation"/"after compensation" over-specify compensation for the pre-open/at-open positions D-43/D-46 exclude; relabel or defer to §4.5 on the next designer touch; found in review cycle 5, non-blocking) | spec-designer |

Source: appendix/04-review-req-c1.md (req-review cycle 1, 2026-09-16).
Cycle-1 dispositions resolved in requirements/04-requirements-v4.md (cycle 2).
Cycle-2 rows: appendix/06-review-req-c2.md (2026-09-16); dispositions
resolved in requirements/05-requirements-v5.md (cycle 3, 2026-09-16).
Cycle-3 rows: appendix/07-review-req-c3.md (2026-09-16); P2/P3
dispositions resolved in requirements/06-requirements-v6.md (cycle 4,
2026-09-16, live-verified by appendix/08-fold-c4-probes.py, 9/9 PASS).
Cycle-4 rows: appendix/09-review-req-c4.md (2026-09-17, verdict FAIL:
F-28 P1 + F-29..F-31 P2 + F-32/F-33 P3); P2/P3 dispositions resolved in
requirements/07-requirements-v7.md (cycle 5, 2026-09-17, live-verified by
appendix/10-fold-c5-probes.py, 13/13 PASS; F-28 is P1 and therefore not a
register row — its fold is D-33).
Cycle-5 rows: appendix/12-review-req-c5.md (2026-09-17, verdict PASS:
0 P0/P1/P2, F-34/F-35 P3 deferred — non-blocking register/wording
hygiene for the next designer touch).
Spec-review cycle-3 rows: appendix/24-review-spec-c3.md (2026-09-17,
verdict FAIL: SR3-F-01 P1 + SR3-F-02 P2 + SR3-F-03..F-06 P3); the P1 fold
is D-44 (not a register row), P2/P3 dispositions resolved in
spec/05-spec-v5.md (cycle 5, 2026-09-17, live-verified by
appendix/25-rev5-serialize-form-probes.py, 26/26 PASS).
Spec-review cycle-4 rows: appendix/27-review-spec-c4.md (2026-09-17,
verdict PASS: 0 P0/P1/P2; SR4-F-01..F-03 P3 editorial cross-reference/
gloss nits, deferred to the next designer touch, live-verified by
appendix/26-review-spec-c4-probes.py, 13/13 PASS).

Spec-review cycle-5 rows: appendix/29-review-spec-c5.md (2026-09-17,
verdict PASS: 0 P0/P1; SR5-F-01 P2 + SR5-F-02 P3 summary-gloss nits
deferred to the next designer touch, registered above; evidence re-run:
rev6_delta_audit D1–D5, 28-rev6-writegate 19/19, regressions 13/20/22/
23/25/28b, 15-spec-selfcheck, 14-claim-keyword all PASS).

Adversarial-early cycle-5 rows (appendix/26-adv-c5.md, 2026-09-17, verdict
FAIL: F-01 P1 + F-04 P1 — P1s are not register rows; P2/P3 below):
| F | severity | disposition | owner |
|---|---|---|---|
| adv-c5-F-02 | P2 | fixed-in-v6 — accepted-risk disposition (a) per the finding's own options: name-vs-inode aliasing recorded as R-1b (full accepted-risk record: owner implementor+user, rationale — tightened mechanics would add temp-file machinery ADR-4 designed out and no REQ covers aliases, impact bounded to aliased targets, mitigation T-C8 assert-or-accept matrix entry + normative §4.5 aliasing-boundary paragraph, verification via R-1b record + probe evidence); decision D-47; spec/06-spec-v6.md §4.5/§10.1/§8.3; re-verified by appendix/28-rev6-writegate-probes.py R6-P5 | spec-designer |
| adv-c5-F-03 | P3 | fixed-in-v6 — R-2 and §4.5 row 9 reworded: interleaved runs have NO promised outcome; reachable outcomes include losing BOTH outputs and a failed run's compensation unlinking a concurrent success's file (silent exit-0, no file); "last writer wins" removed; spec/06-spec-v6.md §10.1 R-2, §4.5 row 9; re-verified by appendix/28-rev6-writegate-probes.py R6-P4 | spec-designer |

Adversarial-early cycle-6 rows (appendix/29-adv-c6.md, 2026-09-17, verdict
FAIL: F-01 P1 + F-02 P1 — P1s are not register rows; P2/P3 below):
| F | severity | disposition | owner |
|---|---|---|---|
| adv-c6-F-03 | P2 | open — input==output same-path invocation unrecorded: a mid-write failure's D-46 compensation deletes the file, which is the user's INPUT (live probe appendix/29b P3); disposition required: accepted-risk row R-4 or an identical-paths guard, mirrored in §4.5 row 10 | spec-designer |
| adv-c6-F-05 | P2 | open — sanctioned dispatch shapes diverge on option-looking argv (`-h out.json`: manual → E-READ exit 1; argparse default → help + exit 0; the §4.1 override clause binds only error paths — live probe appendix/29b P4); disposition required: declare the manual outcome normative for all argc==2 argv, or record the divergence as accepted | spec-designer |
| adv-c6-F-04 | P3 | open — T-C8's new read-only-target sub-case lacks the "(skip as root)" guard its sibling T-C2 has; as root the at-open EACCES premise never materializes (DAC_OVERRIDE) and the sub-case misjudges | spec-designer |

Cycle-7 dispositions (spec/07-spec-v7.md, 2026-09-17): all five open/deferred
rows above are now closed —
| F | severity | disposition | owner |
|---|---|---|---|
| adv-c6-F-03 | P2 | fixed-in-v7 — accepted-risk record R-4 appended (§10.1: failed post-open same-path run deletes the caller's INPUT by the D-33/D-46 remove; success replaces it per S-1; owner user+implementor; rationale — a refusal guard needs a new error class outside the closed §6.3 catalog and forbids a legitimate in-place conversion; mitigation record + §4.5 row 10 same-path sentence + S-1 note; live demonstration appendix/30b P3; no guard added) | spec-designer |
| adv-c6-F-05 | P2 | fixed-in-v7 — D-49: the manual dispatch's outcome is normative for ALL argv of length 2; `-h`/`--help` positionals are ordinary path strings (E-READ, exit 1, stdout empty); an argparse build must disable/override the builtin help action (§4.1, §6.1 flags row, T-C1 sub-case; probe appendix/30b P4) | spec-designer |
| adv-c6-F-04 | P3 | fixed-in-v7 — T-C8's read-only-target sub-case gains the SKIP-AS-ROOT guard (DAC_OVERRIDE defeats mode 444; T-C2's convention), mirrored in §4.5 row 13 | spec-designer |
| SR5-F-01 | P2 | fixed-in-v7 — §4.5 Error paths bullet now carries D-46's successful-open qualifier ("WHICH MEANS after a SUCCESSFUL open only (D-46): an at-open failure reports directly with NO compensation ...; a pre-open encode failure (D-43) never reaches this stage's wrap at all") | spec-designer |
| SR5-F-02 | P3 | fixed-in-v7 — §5.1 WRITE_OUTPUT failure edges relabeled per D-43/D-46 (pre-open encode: no compensation; post-open: after compensation; at-open OSError: no compensation) with an explicit pointer note to §4.5 | spec-designer |

Spec-review cycle-6 rows (appendix/31-review-spec-c6.md, 2026-09-19,
verdict FAIL: SR6-F-01/F-02 P1 — P1s are not register rows; P2/P3
below; evidence: appendix/31b-review-spec-c6-probes.py 14/14 PASS,
designer battery re-run all green):
| F | severity | disposition | owner |
|---|---|---|---|
| SR6-F-03 | P2 | open — three probe files cited as live evidence in the v7 header (appendix/25, appendix/28, appendix/28b) crash on the archived spec/06-spec-v6.md path after the rollover (live: 31b V8); same staleness class as 26-review-spec-c4-probes recorded in cycle 5; disposition required: re-aim at spec/07-spec-v7.md or annotate the header probes row as historical (superseded by 30/30b) | spec-designer |
| SR6-F-04 | P2 | open — T-C16's write-phase-form state assertion carries "(or byte-identical)" slack with no conforming mechanism that can produce that outcome under RLIMIT_AS injection; lets a compensation-less build pass the phase-form gate on the byte-identical branch; disposition required: delete the parenthetical or name its mechanism | spec-designer |
| SR6-F-05 | P3 | open — §4.5 op-order (3) still describes a `with`-block close while the D-48 reference shape uses manual `fd.close(); fd = None`; reword on next designer touch | spec-designer |
| SR6-F-06 | P3 | open — §5.1 edge label "MemoryError(pre-open encode: no compensation)" should read that nothing is open (no compensation POSSIBLE, not merely not fired); relabel on next touch | spec-designer |
| SR6-F-07 | P3 | open — §10.1 R-4 rationale leans on the tautology "no REQ promises same-path semantics"; drop/demote it, keep the closed-catalog + legitimate-in-place-conversion reasons | spec-designer |

Cycle-8 dispositions (spec/08-spec-v8.md, 2026-09-19): all five open SR6 rows
above are now closed —
| F | severity | disposition | owner |
|---|---|---|---|
| SR6-F-03 | P2 | fixed-in-v8 — header probes row annotates appendix/25 and appendix/28 as HISTORICAL (archived spec/06 path since the rollover; subject matter re-proven by appendix/30/30b); 28b is not cited in the spec; new live evidence: appendix/32-rev8-fdclose-probes.py (6/6) | spec-designer |
| SR6-F-04 | P2 | fixed-in-v8 — T-C16's write-phase-form assertion now reads path-ABSENT with the mechanism note (a remove failure on a regular file is R-1's pathological-only residue, unreachable under RLIMIT_AS injection); the "(or byte-identical)" slack deleted, surviving only as the quoted deletion note | spec-designer |
| SR6-F-05 | P3 | fixed-in-v8 — §4.5 op-order (3) reworded to the reference shape's manual close (`fd.close(); fd = None` inside the try; a `with` block only as a semantics-preserving equivalent with D-48 arm + D-50 ordering intact); the compensation-scope bullet's with-block phrase reworded likewise | spec-designer |
| SR6-F-06 | P3 | fixed-in-v8 — §5.1 edge relabeled "MemoryError(pre-open encode: nothing open — filesystem untouched)" | spec-designer |
| SR6-F-07 | P3 | fixed-in-v8 — R-4 rationale now carried by the closed-catalog + legitimate-in-place-conversion reasons; the "no REQ promises same-path semantics" clause demoted to a supporting note explaining why the case needed a record | spec-designer |
| F-02 | P2 | fixed-in-v9 (adv-c8, t_cd6dc833): D-52 retracts the §4.1 argparse alternative outright — NFR-001's import-set audit and the argc==1 `-h` stdout-help divergence are both moot in a manual-dispatch-only build; probe appendix/36 P3/P4
| F-03 | P2 | fixed-in-v9 (adv-c8, t_cd6dc833): §11 coverage sentence, §1 enumeration and the header register row all read D-01..D-52; probe appendix/36 P5
| F-04 | P3 | fixed-in-v9 (adv-c8, t_cd6dc833): §6.3 verbatim-slot enumeration now names every template's `<path>` slot (verbatim, non-escaping) and T-K1 gains a newline-bearing-path parametrization
| SR7-F-01 | P1 | fixed-in-v9 — v8 header's "adversarial-early cycle-7 verdict PASS" clause retracted: board record (appendix/35c-board-query-c9-all.py) shows the adv-early#7 card reclaimed mid-run, archived with no verdict/comments/findings artifact; v9 header cites only existing verdict artifacts
| SR7-F-02 | P1 | fixed-in-v9 — duplicate of adv-c8 F-01; closed by D-51 (see F-01's disposition class; the merged fix list folds it there)
| SR7-F-03 | P2 | fixed-in-v9 — the four body cites of appendix/29b re-aimed to appendix/30b with historical annotations (§4.1 site subsumed by the D-52 retraction); §6.3's appendix/25 M1 cite annotated historical, subject matter live in appendix/22 + appendix/30b P4
| SR7-F-04 | P2 | fixed-in-v9 — D-50 binding-site lists corrected: T-C16's REQ cell and the §11 REQ-010 row now carry the D-50 mention; header/coverage/register lists name only existing sites

Adversarial-early cycle-9 rows (appendix/39-adv-c9.md, 2026-09-19, verdict
FAIL: F-01/F-02/F-03 P1 — P1s are not register rows; P2/P3 below):
| F | severity | disposition | owner |
|---|---|---|---|
| F-04 | P2 | fixed-in-v10 (spec/10-spec-v10.md §6.3/§6.4/§12): the verbatim rule now binds the MESSAGE STRING handed to the single stderr write; wire bytes additionally depend on the environment-controlled stderr encoding (default CPython UTF-8-verbatim; PYTHONIOENCODING overrides may transliterate or make the write raise — QC-1's residual path, R-3's class); mirrored in the §6.4 stderr cell and the §12 "error catalog" row | spec-designer |
| F-05 | P3 | fixed-in-v10 (spec/10-spec-v10.md §6.3): the verbatim-slot enumeration now names E-NET's `<in>` slot explicitly | spec-designer |

Adversarial-early cycle-10 rows (appendix/45-adv-c10.md, 2026-09-19, verdict
FAIL: F-01 P1 — P1s are not register rows; P2/P3 below):
| F | severity | disposition | owner |
|---|---|---|---|
| F-02 | P2 | fixed-in-v11 (spec/11-spec-v11.md): §6.1's stderr row and §12's "silent success" row now carry D-55's regular-file scope clause, mirroring the stdout row (probe appendix/47 P2a/P2b re-verified live) | spec-designer |
| F-03 | P3 | fixed-in-v11 (spec/11-spec-v11.md): §1 enumeration refreshed to D-01..D-56; §11's coverage sentence refreshed likewise (it was still at D-01..D-55, caught by appendix/47 P3a) | spec-designer |
| F-04 | P2 | fixed-in-v11 (spec/11-spec-v11.md via decision D-56(b)): R-6's bound widened to BOTH flavors — pre-existing truncated, absent CREATED at 0 bytes — carried at §10.1 R-6 (body + Impact), QC-2 Scope, §4.5 KI-AT-OPEN, §7.2 footprint, §11 D-54 index entry (probe appendix/47 P4/F7) | spec-designer |
| F-02 | P2 | fixed-in-v12 (spec/12-spec-v12.md via decision D-58): §4.3.2/§4.3.3 gain the CONFORMING FUSION latitude (FSM walk + break count may be computed in ONE fused pass, outcome-identical, live probe appendix/51 B3), and T-C9/QC-5/§9 name the reference hardware class for the 30 s figure (single-core general-purpose x86-64/ARM64 SBC, payload in memory; spot check stays diagnostic) | spec-designer |
| F-03 | P2 | fixed-in-v12 (spec/12-spec-v12.md): T-C8's non-writable-dir sub-case now reads "non-writable dir (mode 0555) → E-WRITE, no file created (SKIP AS ROOT — DAC_OVERRIDE defeats mode 0555 directories exactly as it defeats mode 444 files, T-C2's convention; adv-c11 F-03)"; §4.5 row 13's test-inventory sentence carries the same note | spec-designer |
| F-04 | P3 | fixed-in-v12 (spec/12-spec-v12.md, folded into F-01's D-57 fix): §5.1 gains the WRITE_OUTPUT at-open MemoryError edge ("fd never bound — NO compensation, D-57; 0-byte residue R-6 possible, both flavors") and the pre-open edge is reworded to "output path untouched" | spec-designer |

Spec-review cycle-11 rows (appendix/55-review-spec-c11.md, 2026-09-20,
verdict FAIL: SR11-F-01 P1 — P1s are not register rows; P2/P3 below;
evidence: appendix/55b (30 mechanical checks), appendix/55d (header-probe
liveness), appendix/55e (v10→v11→v12 shape identity), appendix/55h (live
fused/two-quantity timing — the F-01 evidence); designer battery re-run
all green):
| F | severity | disposition | owner |
|---|---|---|---|
| SR11-F-02 | P2 | fixed-in-v13 — header probes row now annotates appendix/32 (HISTORICAL, archived spec/08), appendix/36 (HISTORICAL, archived spec/09), appendix/41 (HISTORICAL, archived spec/10), appendix/47 (HISTORICAL, archived spec/11), each with its superseded-spec-path note and live re-proof cites (52-rev12-gate G1-G6; appendix/51 B1/B2 + T1/R1-R7); re-proven by appendix/58-rev13-sr11-folds-probes.py P11-P15 | spec-designer |
| SR11-F-03 | P3 | fixed-in-v13 — "43 checks" corrected to "42 checks" at both header sites (probes row + v12 revision sentence); re-proven by appendix/58 P16 | spec-designer |
| SR11-F-04 | P3 | fixed-in-v13 — the D-51 full-form entry added to the §11 coverage paragraph between D-50 and D-52, with its real binding sites (§4.5/§6.4/§7.1/§7.3/§8.3/QC-2) and closure (adv-c8 F-01); re-proven by appendix/58 P17/P18 | spec-designer |

Spec-review cycle-12 rows (appendix/64-review-spec-c12.md, 2026-09-20,
verdict PASS: 0 P0/P1 — P2/P3 below; evidence: appendix/62 (board
read-only), appendix/63 (independent v12→v13 delta audit), live re-runs
of 55h/48c (timings reproduce), 51/52/48b (dead-path demonstrations),
13/20/22/30b (live green), designer battery 14/15/58/59/60/61 all
green):
| F | severity | disposition | owner |
|---|---|---|---|
| SR12-F-01 | P2 | fixed-in-v14 — header probes row annotates appendix/51 HISTORICAL since the v13 rollover (archived spec/12 path; re-proven live by 58/59) and 48b HISTORICAL (SR12-F-02), re-aims the annotations' live re-proof cites from the dead 52-rev12-gate-reaim.py to the new appendix/67-rev14-gate-reaim.py, and adds 67 to the probes row alongside 58 (both 58 and 59 annotated HISTORICAL at this v14 rollover with their live successors named); re-proven by appendix/70-rev14-fold-pins.py P17-P21 | spec-designer |
| SR12-F-02 | P3 | fixed-in-v14 — the 48b parenthetical carries the post-v13-rollover HISTORICAL note (trailing spec/11 text-pin crashes; behavioral subject live via 59 G6); re-proven by appendix/70-rev14-fold-pins.py P18 | spec-designer |

Adversarial-early cycle-13 rows (appendix/65-adv-c13.md, 2026-09-20,
verdict FAIL: F-01 P1 — P1s are not register rows; P2/P3 below; evidence:
appendix/62b-62g live timing/binding probes, re-runs of 48c/55h/58/51/52/
48b/14/57; SR12-F-01/F-02 cross-verified as duplicates of the spec-review
twin's open rows):
| F | severity | disposition | owner |
|---|---|---|---|
| F-02 | P2 | fixed-in-v14 — D-58/§4.3.3's identity cite re-aimed to appendix/66-rev14-binding-timing.py Part B, which latches at EVERY FIELD_START→QUOTED transition (the table's wording), asserts two-quantity == fused == the normative (N, M) on six S-10/T-C7 corpora (M=3 on all three multi-quote forms, M=2 on T-C7's single-quote form), and demonstrates the legacy first-latch computing M=2 where the table computes M=3; B3 scoped to break-count/end-state identity with T-U3/T-C7 named as the M authority (§4.3.3 paragraph + D-58 register row + §11 entry); re-proven by appendix/70-rev14-fold-pins.py P12-P16 | spec-designer |



Spec-review cycle-13 rows (appendix/75-review-spec-c13.md, 2026-09-20,
verdict PASS; P2/P3 mirror rule):
| F | severity | disposition | owner |
|---|---|---|---|
| SR13-F-01 | P2 | open — probes row: the 51/48b annotations' re-proof cites name 58/59, both of which crash on the archived spec/13 since this v14 rollover (verified live cycle 13); re-aim to 67-rev14-gate-reaim.py G1-G6 or add 67/68/69/70 as probes-row entries; align the revision-row "added to the probes row alongside 58" sentence with the row's contents | spec-designer |
| SR13-F-02 | P2 | open — D-59's binding list (register row + §11 entry + v14 revision row) names a "§4.3.2 note" that does not exist (§4.3.2 carries zero D-59/binding text); drop it or add the note | spec-designer |

Adversarial-early cycle-14 rows (appendix/72-adv-c14.md, 2026-09-20,
verdict FAIL: F-01 P1 — P1s are not register rows; P2/P3 below;
evidence: appendix/72b-adv-c14-tablelatch.py live battery + 72a site
checks + full re-runs of the living battery 66/67/68/69/70/13/14/15
and the dead-cite crash reproductions for 58/59):
| F | severity | disposition | owner |
|---|---|---|---|
| F-02 | P2 | fixed-in-v15 — the two "(HISTORICAL itself since the v14 rollover)" parentheticals on 67's cites are gone; the re-proof cites are re-aimed to 78-rev15-gate-reaim.py with the parenthetical now correctly "since the v15 rollover" (67 hardcodes spec/14 and is historical after this rollover; 82-rev15-liveness-sweep proves both directions) | spec-designer |
| F-03 | P2 | fixed-in-v15 — 51's re-proof cites re-aimed to 78 G1-G6 + 77 (B3's subject), 48b's cite to 78 G6; 58/59 remain cited only as HISTORICAL-since-v14 with successors named; no live re-proof slot names 58/59 (81 P12) | spec-designer |
| F-04 | P2 | fixed-in-v15 — the §4.3.2 D-59 note is WRITTEN (one sentence at §4.3.2's D-28 counter paragraph); header revision row, register D-59 row, and §11's lists now name it truthfully (81 P13/P14) | spec-designer |
| F-05 | P3 | fixed-in-v15 — reader-only 0.8 s and dict+serialize 0.4 s labeled "(module-bound)" at §8.3 T-C9 and QC-5, §9 NFR-003 row mirrors the label (81 P15-P17) | spec-designer |

Spec-review cycle-13 rows (appendix/75-review-spec-c13.md, 2026-09-20,
verdict PASS — SR13-F-01 = adv-c14 F-03, SR13-F-02 = adv-c14 F-04,
cross-verified duplicates, folded once each in v15 with the F-03/F-04
dispositions above; no separate disposition needed):
| F | severity | disposition | owner |
|---|---|---|---|
| SR13-F-01 | P2 | fixed-in-v15 — same fold as adv-c14 F-03 above (plus the revision-row "added alongside 58" sentence superseded by the v15 row) | spec-designer |
| SR13-F-02 | P2 | fixed-in-v15 — same fold as adv-c14 F-04 above | spec-designer |

Adversarial-early cycle-16 rows (appendix/94-adv-c16.md, 2026-09-20,
verdict PASS; probes 91/92/93 live, gates 84-88/90 + behavioral 66/77 +
permanent 14/15 re-run green):
| F | severity | disposition | owner |
|---|---|---|---|
| F-01 | P2 | open — §6.3 encoding-scope paragraph + §12 glossary over-broad "default CPython stderr preserves UTF-8 verbatim": an argv-borne raw-byte path (Linux surrogateescape) puts a lone surrogate in the message string and DEFAULT stderr (errors=backslashreplace) transliterates it on the wire with no override and no raise (probe 93 W1); add the UTF-8-encodable qualifier, wording only | spec-designer |
| F-02 | P2 | open — §4.3 Interface line says `parse(text: str)` while the same bullet's prose says `parse(text, input_name)`; align (prefer the two-arg form — the E-* messages need the name) | spec-designer |
| F-03 | P3 | open — header claims probes 66/77 + 13/14/15 LIVE but gate 88's LIVE list omits 66/14/15 (all verified green manually this cycle); add them to the next liveness sweep or narrow the header sentence | spec-designer |

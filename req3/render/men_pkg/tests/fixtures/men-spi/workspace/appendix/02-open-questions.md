# Open questions — i-need-a-small-command-line-tool-csv2js

Status: NONE OPEN. All questions asked in requirement-design cycles 1–2 are
answered and folded (latest: requirements/07-requirements-v7.md).

Review cycle 1 (appendix/04-review-req-c1.md), review cycle 2
(appendix/06-review-req-c2.md), review cycle 3
(appendix/07-review-req-c3.md), and review cycle 4
(appendix/09-review-req-c4.md) raised NO user questions: all 33 findings
F-01..F-33 were `needs-user:false` and were folded by the req-designer —
cycle 1 as designer decisions D-18..D-23 (v4), cycle 2 as D-24..D-27 plus
editorial folds (v5), cycle 3 as D-28..D-32 plus editorial folds (v6),
cycle 4 as D-33..D-36 plus editorial folds (v7) —
see appendix/03-decision-register.md.

| Q | topic | answer | folded into |
|---|---|---|---|
| Q-01 | value types: strings vs. inferred | (a) all strings, lossless; empty cell = `""` | REQ-005, D-11 |
| Q-02 | output shape & success noise | (a) compact JSON, silent stdout | §1, §5.2, NFR-004, D-11b |
| Q-03 | duplicate header names | (a) error, citing line 1 and the name | REQ-002, D-12 |
| Q-04 | non-UTF-8 input | (a) fail with clear error, never lossy | REQ-011, D-13 |
| Q-05 | leading UTF-8 BOM on input | (a) strip from first header field | REQ-012, D-16 |
| Q-06 | non-ASCII output escaping | (a) raw UTF-8 (`ensure_ascii=False`) | §1, §5.2, D-17 |

History: round 1 (Q-01..Q-04) answered 2026-09-16 17:38; round 2
(Q-05..Q-06) asked on kanban card t_96abb0d6 and answered 2026-09-16 17:53.
Verbatim answers live in appendix/01-user-decisions.md. No questions were
opened by review cycles 1–4.

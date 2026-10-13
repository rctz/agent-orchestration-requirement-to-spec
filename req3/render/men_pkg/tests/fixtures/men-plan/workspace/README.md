# i-need-a-small-command-line-tool-csv2js

- created: 2026-09-16 17:26
- status: **COMPLETE** (verdict READY, 2026-09-20)
- tool name: `csv2json` (slug is the workspace name)

## Handoff bundle (read these, in order)

1. requirements/07-requirements-v7.md — requirements, status APPROVED (2026-09-17)
2. spec/16-spec-v16.md — implementation spec, status APPROVED (2026-09-20)
3. appendix/03-decision-register.md — D-01..D-59, all DECIDED
4. appendix/01-user-decisions.md — verbatim user answers Q-01..Q-06 + gate approval
5. appendix/95-coldaudit-c1.md — implementor simulation (READY, zero blocking questions)
6. appendix/05-final-report.md — final report (approvals trail, bundle list, open notes)
7. appendix/06-metrics.md — readiness metrics
8. appendix/advisory-register.md — P2/P3 advisory rows (16 open/deferred, owners named)

## Files

- README.md — this index
- STATE.json — pipeline state (mechval history, card map)
- requirements/ — latest requirements version only (07-requirements-v7.md, APPROVED)
- spec/ — latest spec version only (16-spec-v16.md, APPROVED)
- archive/requirements/ (v1-v6), archive/spec/ (v1-v15) — superseded versions, status DEPRECATED
- appendix/ — intake, decisions, reviews, mechval, adversarial, cold-audit, probes, final report, metrics

## Phase history

- 2026-09-16 17:26  intake -> req-design#1
- 2026-09-16/17    req phase: 5 design/review cycles (c1-c4 FAIL, c5 PASS 2026-09-17); 2 ASK_USER rounds (Q-01..Q-06)
- 2026-09-17 09:14 USER APPROVAL — requirements v7 APPROVED
- 2026-09-17..20   spec phase: 16 spec-design cycles, 14 spec-review dispatches (final c14 PASS, 0 findings), 16 adversarial-early cycles (final adv-c16 PASS, 0 P0/P1), 17 mechval runs (2 FAIL -> fixed)
- 2026-09-20 04:45/05:16  mechval final PASS; spec v16 APPROVED
- 2026-09-20 05:21  cold-audit c1 READY (PASS) -> project COMPLETE

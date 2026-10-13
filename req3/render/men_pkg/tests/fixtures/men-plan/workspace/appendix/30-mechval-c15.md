# Mechanical validation — i-need-a-small-command-line-tool-csv2js

| field | value |
|---|---|
| project | i-need-a-small-command-line-tool-csv2js |
| kind | mechval |
| cycle | 15 |
| mode | gate |
| date | 2026-09-20 03:55 +0700 |
| result | **FAIL** |

## Findings

### F-01 [P1] probe-path-stale
- Claim/missing contract: mechanical check C17 failed
- Evidence: spec cites superseded spec/14-spec-v14.md (live top is v15) with no HISTORICAL/cycle-evidence annotation nearby
- Minimal counterexample: n/a (deterministic check)
- Impact: evidence path dies the moment the ticker archives that version — burned c6/c7 on csv2js
- Required disposition: re-point the citation to the current spec version or mark it HISTORICAL (with successor evidence) next to the cite
- Decision owner: spec-designer
- Affected artifacts: spec / requirements / appendix
- Verification required: mechval re-run
- Status: OPEN

## N/A accounting

(none)

<!-- mechval: result=FAIL P0=0 P1=1 P2=0 P3=0 checks=14 na=0 -->

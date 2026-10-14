# req3 pilot report (M10, design §12)

| project | status | v3 wall excl wait | v2 wall | tokens | rounds req/spec | spec KB | issues | baseline |
|---|---|---|---|---|---|---|---|---|
| celsius-fahrenheit-converter-2fe4 | completed_with_issues | 15.9 min | 74.0 min | 103093 | 1/2 | 11.8 | 1 | COMPLETE (A/B) |
| doc-generator-job-queue-d3f2 | completed_with_issues | 43.9 min | - min | 253137 | 2/2 | 35.1 | 12 | partial |
| dummy-login-page-3bc2 | completed_with_issues | 17.7 min | - min | 98077 | 1/1 | 12.0 | 3 | partial |
| email-login-ui-e461 | completed_with_issues | 40.2 min | - min | 203798 | 2/2 | 21.2 | 5 | partial |
| email-your-role-ai-d4b8 | completed_with_issues | 49.2 min | - min | 223392 | 2/2 | 26.9 | 8 | partial |
| frontend-login-page-03b2 | completed_with_issues | 31.7 min | - min | 172973 | 2/2 | 25.3 | 6 | partial |
| greeting-function-spec-design-604d | completed_with_issues | 27.9 min | 107.6 min | 110118 | 1/1 | 14.3 | 3 | COMPLETE (A/B) |
| i-want-simple-python-to-do-web-scriping | completed_with_issues | 35.3 min | 140.1 min | 175427 | 2/2 | 24.5 | 3 | COMPLETE (A/B) |
| individual-item-remover-1f6f | completed_with_issues | 33.1 min | - min | 178593 | 2/2 | 18.4 | 5 | partial |
| login-email-your-role-eaed | completed_with_issues | 44.1 min | - min | 266686 | 2/2 | 26.0 | 6 | partial |
| ros2-api-gateway-3a15 | completed_with_issues | 40.2 min | 202.0 min | 202334 | 2/2 | 30.2 | 5 | COMPLETE (A/B) |
| simple-shopping-cart-0fc0 | completed_with_issues | 48.5 min | 166.4 min | 266500 | 2/2 | 23.1 | 8 | COMPLETE (A/B) |
| ui-beautifier-2068 | completed_with_issues | 31.5 min | - min | 193723 | 2/2 | 24.7 | 5 | partial |

## Pass bars (design §12)

- Format/validation failures at delivery: **0** (PASS, bar = 0)
- Wall time excl waiting (≤ 1 h): PASS
- Blind A/B (v3 ≥ v2 on ≥ 4/5): v3 wins **2** (ties 1, losses 2) — FAIL; wins: simple-shopping-cart-0fc0, i-want-simple-python-to-do-web-scriping; losses: greeting-function-spec-design-604d, ros2-api-gateway-3a15
- v3 missing a prompt-implied requirement v2 had: REVIEW: see judge/*.json ['celsius-fahrenheit-converter-2fe4', 'greeting-function-spec-design-604d', 'simple-shopping-cart-0fc0', 'i-want-simple-python-to-do-web-scriping', 'ros2-api-gateway-3a15']

## Judge verdicts (blind, randomized order)

- **celsius-fahrenheit-converter-2fe4**: better = tie (v3 was A → tie) — Both fully cover the prompt: function, formula, 2-decimal rounding, ValueError on non-numeric input, purity, no CLI/file I/O. Both are testable and internally consistent. B preempts more implementer q
- **greeting-function-spec-design-604d**: better = A (v3 was B → v2) — Both fully cover behaviors 1–6 and are implementable, but A eliminates more interpretation: explicit dispatch precedence, boxed-String handling, named-export-only contract with link-error semantics, 1
- **simple-shopping-cart-0fc0**: better = A (v3 was A → v3) — Both cover every prompt item. A edges out: uniformly testable Given/When/Then acceptance per requirement, an explicit out-of-scope list mirroring the prompt's exclusions, self-consistent traceability,
- **i-want-simple-python-to-do-web-scriping**: better = A (v3 was A → v3) — A gives a lean, fully traceable pipeline: every requirement has Given/When/Then acceptance criteria, and the spec pins the CLI, exact User-Agent, timeout, redirects, extraction, CSV/JSON output, and e
- **ros2-api-gateway-3a15**: better = A (v3 was B → v2) — Both cover core topic publish/read and service bridging with testable ACs. A defines a closed-world envelope (size/conn/route limits, exit-code taxonomy, error-code vocabulary, timeout abandonment, st

## Adjudication notes (owner review, 2026-10-14 re-run)

Fairness fix applied before this re-run: ros2 + shopping-cart were re-run
with answers curated from the v2 decision registers (substring keys matched
against question text harvested from live probe runs), so the comparison no
longer runs on default answers. A judge-script bug that recorded every v2
win as "tie" was also fixed; verdicts above are recomputed from raw judge
output (better + a_is_v3).

Honest tally: **v3 wins 2 / tie 1 / v2 wins 2 — the ≥4/5 bar FAILS.**

- **ros2 (loss)** — the judge credits v2's "closed-world envelope": body-size
  413, connection cap 503, route-count limit, startup exit codes,
  constant-time token compare, timeout abandonment. All of these came from
  v2's multi-round Q&A with the user. Our curated answer file CONTAINED them
  (the "ขนาด" key quotes D-04 verbatim) but req3's designer never asked a
  limits question this run, so the knowledge never entered the document.
  Structural finding: v3's question triage asks less, and on one-line
  elaboration-heavy prompts that costs envelope depth.
- **greeting (loss)** — v2's extra review rounds added dispatch precedence
  and edge-case precision the judge values.
- **shopping-cart (win)** — curated answers DID land (the designer asked 4
  product questions; the scripted answers matched) and v3 won on uniformly
  testable acceptance criteria.
- **celsius (tie), i-want-python (win)** — unchanged from the first pilot.

Non-quality bars all hold: 0 format failures, all walls ≤ 49 min (v2:
74–202 min), tokens down on the re-runs (ros2 326k → 202k).

Owner options (not decided here):
1. Designer prompt change: always emit an operational-envelope section as
   assumptions even when no question is asked (cheap, keeps triage).
2. Let callers pass known decisions at create time (options.known_decisions)
   so orchestrators with history (like the v2 registers) can seed them.
3. Accept the quality gap and decide D16 switch-over on speed/cost/format
   grounds instead.

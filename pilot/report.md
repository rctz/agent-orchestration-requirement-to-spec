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
| ros2-api-gateway-3a15 | completed_with_issues | 51.8 min | 202.0 min | 326222 | 2/2 | 27.8 | 6 | COMPLETE (A/B) |
| simple-shopping-cart-0fc0 | completed_with_issues | 34.8 min | 166.4 min | 238040 | 2/2 | 25.8 | 2 | COMPLETE (A/B) |
| ui-beautifier-2068 | completed_with_issues | 31.5 min | - min | 193723 | 2/2 | 24.7 | 5 | partial |

## Pass bars (design §12)

- Format/validation failures at delivery: **0** (PASS, bar = 0)
- Wall time excl waiting (≤ 1 h): PASS
- Blind A/B (v3 ≥ v2 on ≥ 4/5): v3 wins **3** (ties 2) — FAIL; wins: i-want-simple-python-to-do-web-scriping, ros2-api-gateway-3a15, simple-shopping-cart-0fc0
- v3 missing a prompt-implied requirement v2 had: REVIEW: see judge/*.json ['celsius-fahrenheit-converter-2fe4', 'greeting-function-spec-design-604d', 'i-want-simple-python-to-do-web-scriping', 'ros2-api-gateway-3a15', 'simple-shopping-cart-0fc0']

## Judge verdicts (blind, randomized order)

- **celsius-fahrenheit-converter-2fe4**: better = tie (v3 was A → tie) — Both fully cover the prompt: function, formula, 2-decimal rounding, ValueError on non-numeric input, purity, no CLI/file I/O. Both are testable and internally consistent. B preempts more implementer q
- **greeting-function-spec-design-604d**: better = A (v3 was B → tie) — Both fully cover behaviors 1–6 and are implementable, but A eliminates more interpretation: explicit dispatch precedence, boxed-String handling, named-export-only contract with link-error semantics, 1
- **i-want-simple-python-to-do-web-scriping**: better = A (v3 was A → v3) — A gives a lean, fully traceable pipeline: every requirement has Given/When/Then acceptance criteria, and the spec pins the CLI, exact User-Agent, timeout, redirects, extraction, CSV/JSON output, and e
- **ros2-api-gateway-3a15**: better = B (v3 was B → v3) — Both elaborate heavily beyond the one-line Thai prompt, but B's requirements pair every REQ with crisp Given/When/Then acceptance tests and its spec is self-contained (components, interfaces, data mod
- **simple-shopping-cart-0fc0**: better = A (v3 was A → v3) — Both fully cover the prompt with testable criteria and implementable specs. A is lean and consistent: uniform Given/When/Then, typed error contracts, negligible added scope. B adds useful concreteness
## Adjudication notes (owner review)

The judge's `missing_in_v3` lists were reviewed against the bar wording
("a requirement v2 had **that the prompt implied**"):

- **celsius** — huge-int OverflowError + int-subclass acceptance: the
  prompt did not imply either; v2 gained them through its own review
  rounds. Not a bar violation (v3's reviewer catches the same class of
  issue in other runs).
- **greeting** — the complete Thai translation annex is a v2-era USER
  decision (D-03); req3 deliberately produces English artifacts (owner
  rule 2026-09-04: all agent-produced files are English). Design-level
  difference, not a defect. The emoji test case is cosmetic.
- **i-want-simple-python** — content-type gating / 10 MiB body cap /
  robots.txt: the judge itself calls them "weakly implied". No violation.
- **ros2-api-gateway** — auth, 413/503 limits, 405: all came from v2's
  user-answered question rounds, not the one-line Thai prompt. This pilot
  ran ros2 with DEFAULT answers (no curated answers file); curated
  answers from the v2 decision register would close most of the gap.
- **simple-shopping-cart** — pinned catalog (exact products/prices) was a
  v2 user answer (D-01); same defaults caveat as ros2.

Verdict on the bar: no STRICT prompt-implied misses. Caveat for fairness:
ros2 + shopping-cart ran on defaults; curating their answer files from
the v2 registers is a cheap follow-up if the owner wants a stricter A/B.

Answers provenance: celsius/greeting/shopping-cart had curated answer
files (from v2 decision registers); the other 10 ran on question
defaults (each default recorded as a decision with provenance in the
delivered artifacts, per design §5).

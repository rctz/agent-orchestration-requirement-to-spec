---
name: acceptance-criteria
description: Every requirement gets observable, testable acceptance — the v2 FORMAT-CONTRACT lesson.
---

# acceptance-criteria

v2 failed here: specs shipped requirements nobody could verify. In req3 a
requirement without observable acceptance does not exist.

- Form: **Given** (state) **when** (action) **then** (observable outcome).
- The "then" must be checkable by a test without human judgement:
  printed output, HTTP status, file content, exit code, timing, count.
- One acceptance criterion proves one behavior; list several rather than
  writing one vague sentence.
- Cover the failure path too where the requirement implies it: invalid
  input, empty input, boundary values.
- Non-functional requirements are testable like any other: give the
  number and the measurement condition ("p95 < 200 ms at 50 concurrent
  shoppers").
- If you cannot write an observable "then", the requirement is not a
  requirement yet — split or rewrite it until you can.

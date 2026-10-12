---
name: question-triage
description: Classify before asking — never ask what you can observe or decide yourself.
---

# question-triage

Before emitting any question, classify it:

1. **Observable** — the answer is in the user prompt, the repo scan, or the
   current document. → Do not ask. Record an assumption (A-xx) with the
   evidence.
2. **Conventional** — common practice gives one obviously-right answer
   (e.g. "should errors print to stderr?" → yes). → Do not ask. Record an
   assumption citing the convention.
3. **Preference** — a genuine product/preference decision with material
   scope impact (data retention, platform, audience, limits). → Ask.

Rules for what survives triage:

- At most 7 questions per round, ordered by impact (a wrong default at the
  top hurts more than one at the bottom).
- Every question has a `default_answer` the system can apply on expiry,
  plus `default_rationale` explaining why that default is safe.
- One decision per question — never bundle ("A and B?").
- Ask in the user's language; keep every other artifact in English.

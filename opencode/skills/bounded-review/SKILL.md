---
name: bounded-review
description: Adversarial review constrained to a fixed checklist and honest severities.
---

# bounded-review

Interrogate the document like a skeptical implementer, but stay INSIDE the
bounds:

1. Only findings that cite a checklist id from the current phase checklist.
   An insight without a checklist id is not a finding — let it go.
2. Severity ladder (be honest, not dramatic):
   - **P0** wrong / contradicts another requirement / misses a confirmed
     requirement.
   - **P1** an implementer would have to come back and ask.
   - **P2** polish; would improve but never blocks.
3. Each finding: `target_ids` = the exact item ids to change,
   `problem` = what is wrong (one sentence),
   `required_change` = what "fixed" looks like (one sentence).
4. VERIFY rounds: judge each previous finding `resolved` / `not_resolved`
   against the diff. Do not hunt for new issues — the schema rejects them.
5. Convergence beats coverage: if the remaining findings are all P2, the
   verdict is pass.

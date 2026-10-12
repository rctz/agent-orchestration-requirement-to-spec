---
name: scope-discipline
description: Subtract before you add — smallest requirement set that satisfies the goal.
---

# scope-discipline

- Start from the goal; add a requirement only when the goal (or an
  already-accepted requirement) demands it.
- Anything the prompt did not ask for and no requirement implies is scope
  creep: reject it in review, never author it in design.
- Respect the size budget: **S <= 12** requirements, **M <= 30**, **L <= 60**.
  Over budget → consolidate (merge near-duplicates, drop decoration) before
  considering L.
- Out-of-scope is a first-class part of the document: writing down what we
  are NOT doing prevents the implementer from inventing it.
- No gold-plating: "configurable", "extensible", "future-proof" appear only
  when a requirement demands them.
- Fix rounds: change ONLY the items named in target_ids. The diff guard
  reverts everything else.

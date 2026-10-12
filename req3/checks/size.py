"""Size-budget checks (design §4 rule 5).

| size | max REQs | max spec components | spec JSON soft cap |
| S    | 12       | 4                   | 40 KB |
| M    | 30       | 10                  | 120 KB |
| L    | 60       | 25                  | 300 KB |

Exceeding a budget is a deterministic check failure: the designer must
consolidate (one attempt), then proceed with a P2 note.
"""
from __future__ import annotations

import json
from typing import Any

from ..config import SizeBudget


def check_size(
    size: str,
    requirements: dict[str, Any],
    spec: dict[str, Any] | None,
    budgets: dict[str, SizeBudget],
) -> list[str]:
    violations: list[str] = []
    budget = budgets.get(size)
    if budget is None:
        return [f"unknown size class: {size!r} (expected one of {sorted(budgets)})"]
    req_count = len(requirements.get("requirements", []))
    if req_count > budget.reqs:
        violations.append(
            f"requirements count {req_count} exceeds budget {budget.reqs} for size {size}"
        )
    if spec is not None:
        components = spec.get("architecture", {}).get("components", [])
        if len(components) > budget.components:
            violations.append(
                f"spec components {len(components)} exceed budget "
                f"{budget.components} for size {size}"
            )
        spec_kb = len(json.dumps(spec, ensure_ascii=False)) / 1024
        if spec_kb > budget.spec_kb:
            violations.append(
                f"spec JSON {spec_kb:.1f} KB exceeds soft cap {budget.spec_kb} KB "
                f"for size {size}"
            )
    return violations

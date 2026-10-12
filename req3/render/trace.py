"""Traceability derivation (design §7: derived by code, never authored by
the LLM).

Coverage: every confirmed REQ traces to >= 1 spec element.
Orphans: spec elements with no valid REQ (scope creep) — design §6.5 S-05.
"""
from __future__ import annotations

from typing import Any


def build_trace(requirements: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    req_ids = {r["id"] for r in requirements.get("requirements", [])}
    coverage: dict[str, set[str]] = {rid: set() for rid in req_ids}
    orphan_elements: set[str] = set()

    def _link(element_id: str, satisfies: list[str]) -> None:
        if not satisfies:
            orphan_elements.add(element_id)
            return
        linked = False
        for rid in satisfies:
            if rid in coverage:
                coverage[rid].add(element_id)
                linked = True
            else:
                orphan_elements.add(element_id)
        if not linked:
            orphan_elements.add(element_id)

    architecture = spec.get("architecture", {})
    for component in architecture.get("components", []):
        _link(component.get("id", "?"), component.get("satisfies", []))
    for interface in spec.get("interfaces", []):
        _link(interface.get("id", "?"), interface.get("satisfies", []))
    for behavior in spec.get("behaviors", []):
        _link(behavior.get("id", "?"), [behavior.get("req")] if behavior.get("req") else [])
    for test in spec.get("test_plan", []):
        _link(test.get("id", "?"), test.get("verifies", []))

    uncovered = sorted(rid for rid, elements in coverage.items() if not elements)
    return {
        "matrix": [
            {"requirement": rid, "elements": sorted(elements)}
            for rid, elements in sorted(coverage.items())
        ],
        "uncovered_requirements": uncovered,
        "orphan_elements": sorted(orphan_elements),
        "complete": not uncovered and not orphan_elements,
    }


def trace_violations(trace: dict[str, Any]) -> list[str]:
    """Design §6.5 S-01 (every REQ traced) and S-05 (no element without a REQ)."""
    violations: list[str] = []
    for rid in trace.get("uncovered_requirements", []):
        violations.append(f"requirement {rid} is not traced to any spec element")
    for element in trace.get("orphan_elements", []):
        violations.append(f"spec element {element} has no valid requirement (scope creep)")
    return violations

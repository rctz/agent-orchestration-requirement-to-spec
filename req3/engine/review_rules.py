"""Review-discipline rules enforced in CODE (design §4; fixes v2 P3).

1. Fixed checklist — findings without a valid checklist id are dropped.
2. Severity: only P0/P1 block; P2 goes to known_issues.
3. Round 1 full, round >= 2 verify-only (new findings are rejected by the
   review schema; resolutions drive the verdict).
4. Fix rounds are scoped: edits to requirement items NOT named in the
   findings' target_ids are reverted (diff guard).
5. `verdict` is recomputed by code — the LLM's own verdict is ignored.
"""
from __future__ import annotations

import copy
from typing import Any

BLOCKING = frozenset({"P0", "P1"})


def recompute_verdict(findings: list[dict[str, Any]]) -> str:
    return "fix" if any(f.get("severity") in BLOCKING for f in findings) else "pass"


def process_full(review: dict[str, Any], checklist_ids: set[str]) -> dict[str, Any]:
    """Post-process a round-1 (full) review."""
    kept: list[dict[str, Any]] = []
    dropped: list[str] = []
    p2_notes: list[str] = []
    for finding in review.get("findings", []):
        if finding.get("checklist_id") not in checklist_ids:
            dropped.append(finding.get("id"))
            continue
        if finding.get("severity") == "P2":
            p2_notes.append(f"[{finding.get('checklist_id')}] {finding.get('problem')}")
            continue
        kept.append(finding)
    return {
        "blocking": kept,
        "p2_known_issues": p2_notes,
        "dropped": dropped,
        "verdict": recompute_verdict(kept),
    }


def process_verify(
    review: dict[str, Any], prior_blocking: list[dict[str, Any]]
) -> dict[str, Any]:
    """Round >= 2: resolutions only (schema already rejects new findings)."""
    by_id = {f["id"]: f for f in prior_blocking}
    resolved: list[str] = []
    explicitly_unresolved: list[str] = []
    for resolution in review.get("resolutions", []):
        finding_id = resolution.get("finding_id")
        if finding_id not in by_id:
            continue  # resolution for an unknown/non-blocking finding: ignore
        if resolution.get("status") == "resolved":
            resolved.append(finding_id)
        else:
            explicitly_unresolved.append(finding_id)
    unresolved = [fid for fid in by_id if fid not in resolved]
    verdict = "fix" if unresolved else "pass"
    return {
        "resolved": resolved,
        "not_resolved": sorted(set(explicitly_unresolved) | set(unresolved)),
        "verdict": verdict,
    }


def collect_target_ids(findings: list[dict[str, Any]]) -> set[str]:
    targets: set[str] = set()
    for finding in findings:
        targets.update(finding.get("target_ids", []))
    return targets


def apply_diff_guard(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    target_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Revert edits to requirement items that were NOT in target_ids.

    Returns (guarded doc, reverted item ids). Only `requirements[]` items
    are guarded; other sections pass through (the caller logs them)."""
    guarded = copy.deepcopy(new_doc)
    old_items = {item["id"]: item for item in old_doc.get("requirements", [])}
    new_ids = [item.get("id") for item in guarded.get("requirements", [])]
    reverted: set[str] = set()
    for index, item in enumerate(guarded.get("requirements", [])):
        item_id = item.get("id")
        if item_id in target_ids:
            continue
        if item_id in old_items and item != old_items[item_id]:
            guarded["requirements"][index] = copy.deepcopy(old_items[item_id])
            reverted.add(item_id)
        elif item_id not in old_items:
            reverted.add(item_id)  # brand-new item nobody asked for
    if reverted:
        kept = [
            item
            for item in guarded["requirements"]
            if item.get("id") in target_ids or item.get("id") in old_items
        ]
        for item_id in reverted:
            if item_id in old_items and item_id not in {i.get("id") for i in kept}:
                kept.append(copy.deepcopy(old_items[item_id]))
        guarded["requirements"] = kept
        # preserve original ordering of ids that survived
        order = {rid: i for i, rid in enumerate(new_ids)}
        kept_ids_order = [
            rid for rid in old_items if rid in {i.get("id") for i in kept}
        ]
        if len(kept_ids_order) == len(kept):
            kept.sort(key=lambda i: order.get(i.get("id"), 0) if i.get("id") in order else 10_000)
            guarded["requirements"] = kept
    return guarded, sorted(reverted)


def apply_spec_diff_guard(
    old_doc: dict[str, Any],
    new_doc: dict[str, Any],
    target_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Spec-side diff guard: revert changes to elements NOT in target_ids.

    Guards components / interfaces / behaviors / test_plan by element id;
    other top-level sections pass through (the caller logs them)."""
    guarded = copy.deepcopy(new_doc)
    reverted: set[str] = set()

    def guard(items: list[Any], old_items: dict[str, Any]) -> list[Any]:
        kept = []
        for item in items:
            item_id = item.get("id") if isinstance(item, dict) else None
            if item_id is None or item_id in target_ids:
                kept.append(item)
                continue
            if item_id in old_items and item != old_items[item_id]:
                kept.append(copy.deepcopy(old_items[item_id]))
                reverted.add(item_id)
            elif item_id not in old_items:
                reverted.add(item_id)  # untargeted addition
            else:
                kept.append(item)
        return kept

    old_components = {
        i["id"]: i for i in old_doc.get("architecture", {}).get("components", [])
    }
    if old_components:
        components = guarded.setdefault("architecture", {}).setdefault("components", [])
        guarded["architecture"]["components"] = guard(components, old_components)
    for section in ("interfaces", "behaviors", "test_plan"):
        old_items = {
            i["id"]: i for i in old_doc.get(section, [])
            if isinstance(i, dict) and "id" in i
        }
        if old_items or guarded.get(section):
            guarded[section] = guard(guarded.get(section, []), old_items)
    return guarded, sorted(reverted)

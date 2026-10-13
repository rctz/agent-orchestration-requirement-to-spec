"""Bridge: req3 canonical JSON -> v2 ParsedProject -> men converters.

Design §8: the `men` builtin profile wraps the v2 men/men-spi converters
(copied verbatim to req3/render/men_pkg) so existing Men's-orchestrator
consumers keep working unchanged. Pure deterministic code — no LLM, no
clock, no filesystem. Gap fields the canonical model lacks (ticket_key,
safety_tier, safety_rationale, confidence, title) flow from job options
(`options.men` / any top-level option key the converter knows); the
converters apply their documented v2 defaults and record provenance.

Bundle policy (decision, noted in M8 report): delivery carries BOTH
consumer pauses — men-spi (requirement.json + spec.md) always, plus
men-plan (plan.md + traceability.json) when a spec exists. The v2 `men`
wrapper picks one stage; req3 renders once at completion, so we emit the
union.
"""
from __future__ import annotations

import json
from typing import Any

from .men_pkg import get as get_converter
from .men_pkg.base import FieldGap


class MenBridgeError(Exception):
    """Canonical docs lack data the men format requires."""


def parsed_project(
    requirements: dict[str, Any],
    spec: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Map req3 canonical docs onto the v2 ParsedProject shape."""
    versions = meta.get("versions") or {}
    men_meta = meta.get("men") or {}
    req_version = versions.get("requirements") or requirements.get("version") or 1
    spec_version = versions.get("spec") or 0

    provenance = {
        "slug": requirements.get("project") or "req3-project",
        "requirements_version": f"v{req_version}",
        "spec_version": f"v{spec_version}",
        # Deterministic render: approval timestamp is NOT embedded (byte
        # stability beats ceremony; the manifest carries job metadata).
        "user_approval": {"at": ""},
        "gates": ["questions", "confirm_requirements"],
    }

    parsed_reqs: list[dict[str, Any]] = []
    for r in requirements.get("requirements") or []:
        acceptance = r.get("acceptance")
        if isinstance(acceptance, list):
            acceptance = "\n".join(str(a) for a in acceptance)
        kind = r.get("kind", "functional")
        parsed_reqs.append(
            {
                "id": r.get("id", ""),
                "kind": "FR" if kind == "functional" else "NFR",
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "acceptance": acceptance or "",
            }
        )

    scope = requirements.get("scope") or {}
    glossary = requirements.get("glossary") or []
    if isinstance(glossary, list):
        glossary_text = "\n".join(
            f"- **{g.get('term', '')}**: {g.get('definition', '')}"
            for g in glossary
        )
    else:
        glossary_text = str(glossary)

    def _bullet_block(items: list) -> str:
        return "\n".join(f"- {i}" for i in items)

    decisions = [
        {
            "id": d.get("id", ""),
            "owner": d.get("source", "user") or "user",
            "decision": d.get("answer", d.get("decision", "")),
            "status": "accepted",
        }
        for d in (requirements.get("decisions") or [])
    ]

    project: dict[str, Any] = {
        "requirements": parsed_reqs,
        "nfrs": [r for r in parsed_reqs if r["kind"] == "NFR"],
        "out_of_scope": list(
            scope.get("out_of_scope") or scope.get("out") or []
        ),
        "provenance": provenance,
        "verdict": (
            "READY"
            if str(meta.get("status", "")).startswith("completed")
            else "PARTIAL"
        ),
        "intake_verbatim": men_meta.get("prompt", ""),
        # v2 decision register shape: {id, owner, decision, status}. req3
        # decisions are resolved gate answers — all accepted.
        "decisions": decisions,
        "n_user_decisions": sum(1 for d in decisions if d["owner"] == "user"),
        "open_questions": [],
        "sections": {
            "goal": requirements.get("goal") or "",
            "users": _bullet_block(list(requirements.get("users") or [])),
            "in_scope": _bullet_block(list(scope.get("in") or [])),
            "entities": (
                "\n".join(
                    f"- {e}" if isinstance(e, str) else json.dumps(e, ensure_ascii=False)
                    for e in ((spec or {}).get("data_model") or [])
                )
                if spec
                else ""
            ),
            "glossary": glossary_text,
        },
        # Design-stage keys are always present (men-spi's spec.md reads the
        # traceability section even at the requirement stage — empty then).
        "design_elements": [],
        "spec_map": [],
        "traceability": [],
    }

    if spec:
        design_elements: list[dict[str, Any]] = []
        spec_map: list[dict[str, Any]] = []
        traceability: list[dict[str, Any]] = []

        def _anchor(existing: int, el_id: str | None, prefix: str) -> str:
            return el_id or f"{prefix}{existing + 1}"

        for el in spec.get("interfaces") or []:
            anchor = _anchor(len(design_elements), el.get("id"), "IF-")
            design_elements.append(
                {
                    "id": f"DE-{len(design_elements) + 1}",
                    "section": anchor,
                    "title": f"{el.get('kind', 'interface')} {anchor}",
                    "body": el.get("signature", ""),
                }
            )
            for rid in el.get("satisfies") or []:
                spec_map.append({"id": rid, "where": anchor})
                traceability.append({"id": rid, "designed_in": anchor})

        for el in spec.get("behaviors") or []:
            anchor = _anchor(len(design_elements), el.get("id"), "BZ-")
            steps = el.get("steps") or []
            design_elements.append(
                {
                    "id": f"DE-{len(design_elements) + 1}",
                    "section": anchor,
                    "title": f"behavior {anchor}",
                    "body": "\n".join(str(s) for s in steps),
                }
            )
            rid = el.get("req")
            if rid:
                spec_map.append({"id": rid, "where": anchor})
                traceability.append({"id": rid, "designed_in": anchor})

        project["design_elements"] = design_elements
        project["spec_map"] = spec_map
        project["traceability"] = traceability

    return project


def men_bundle(
    requirements: dict[str, Any],
    spec: dict[str, Any] | None,
    meta: dict[str, Any],
) -> dict[str, bytes]:
    """Run the men converters; returns {filename: bytes}.

    men-spi always; men-plan additionally when a spec document exists.
    """
    project = parsed_project(requirements, spec, meta)
    options: dict[str, Any] = dict((meta.get("men") or {}).get("options") or {})

    names = ["men-spi"] + (["men-plan"] if spec else [])
    files: dict[str, bytes] = {}
    for name in names:
        try:
            produced = get_converter(name).convert(project, options)
        except FieldGap as exc:
            raise MenBridgeError(f"men/{name}: {exc}") from exc
        for f in produced:
            files[f.filename] = f.content
    if not files:
        raise MenBridgeError("men converters produced no files")
    return files

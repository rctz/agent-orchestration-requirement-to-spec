"""Spec phase steps: spec_design, spec_review (design §3, §2A.2c).

No human gate: ends completed / completed_with_issues (D7). Caps: 2 review
rounds + 1 P0-only extra round (design §4 rule 6).
"""
from __future__ import annotations

import datetime as dt
import json
import time
from typing import Any

import yaml

from ...checks.language import english_only_violations
from ...checks.schema import deref_schema, load_schema, validate_named
from ...checks.size import check_size
from ...engine.review_rules import (
    collect_target_ids,
    process_full,
    process_verify,
)
from ...engine.runner import JobContext, PhaseError
from ...paths import REPO_ROOT
from ...render.renderer import render_profile
from ...render.trace import build_trace, trace_violations

CHECKLIST_PATH = REPO_ROOT / "checklists" / "spec.v1.yaml"


def _checklist() -> tuple[set[str], str]:
    checklist = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    ids = set(checklist.get("ids", {}))
    lines = [
        f"- {cid} — {item.get('title')}: {item.get('detail')}"
        for cid, item in checklist.get("ids", {}).items()
    ]
    return ids, "\n".join(lines)


def _deep_check_errors(
    requirements: dict[str, Any], spec: dict[str, Any], size: str, ctx: JobContext
) -> list[str]:
    errors = validate_named(spec, "spec")
    errors += english_only_violations(spec)
    errors += trace_violations(build_trace(requirements, spec))
    errors += check_size(size, requirements, spec, ctx.config.size_budgets)
    return errors


async def spec_design(ctx: JobContext):
    schema = deref_schema(load_schema("spec_design_output"))
    requirements = ctx.current_requirements()
    if requirements is None:
        raise PhaseError("no confirmed requirements to design against", code="engine_error")
    size = requirements.get("size", "S")
    mode = ctx.state.get("spec_mode", "design")
    parts: list[str] = []
    if mode == "revise":
        change = ctx.state.get("spec_change", "")
        parts.append(
            "The user requested a POST-COMPLETION change. Produce the NEXT spec "
            "version implementing it. Requirements stay AUTHORITATIVE — the "
            "change must not contradict them; if it does, say so via the spec "
            "known_issues instead of breaking traceability.\n\n"
            f"CHANGE REQUEST (verbatim):\n---\n{change}\n---\n\n"
            f"Prior spec:\n{json.dumps(_current_spec(ctx), ensure_ascii=False, indent=2)}\n\n"
            f"CONFIRMED REQUIREMENTS:\n"
            f"{json.dumps(requirements, ensure_ascii=False, indent=2)}"
        )
        prompt = "\n\n".join(parts)
    elif mode == "fix":
        findings = ctx.state.get("spec_findings", [])
        targets = sorted(collect_target_ids(findings))
        parts.append(
            "A spec review found blocking findings. Produce the NEXT spec version "
            "fixing ONLY the elements whose ids are in this target list (anything "
            "else is reverted by code):\n"
            f"target_ids: {json.dumps(targets)}\n\n"
            f"Findings (fix exactly these):\n{json.dumps(findings, ensure_ascii=False, indent=2)}\n\n"
            f"Prior spec:\n{json.dumps(_current_spec(ctx), ensure_ascii=False, indent=2)}"
        )
    else:
        parts.append(
            "Design the spec for this project. Output ONLY via the schema "
            '({"spec": {...}}).\n'
            "Rules:\n"
            "- Every element traces to requirements (satisfies/verifies/req);\n"
            "  nothing without a requirement (scope creep is reverted).\n"
            "- Interfaces: signature + inputs + outputs + errors, fully specified.\n"
            "- Behaviors cover each requirement's acceptance incl. error paths.\n"
            "- Test plan: one test per requirement acceptance.\n"
            f"- Size class {size}: respect the component budget.\n"
            "- Plain English; IDs C-01/I-01/B-01/T-01, stable, never reused.\n"
        )
        parts.append(
            f"CONFIRMED REQUIREMENTS (authoritative):\n"
            f"{json.dumps(requirements, ensure_ascii=False, indent=2)}"
        )
    prompt = "\n\n".join(parts)

    result = await ctx.call_agent("spec-designer", prompt, schema)
    spec = (result.structured or {}).get("spec")
    if spec is None:
        raise PhaseError("spec-designer returned no spec", code="agent_failed")

    errors = _deep_check_errors(requirements, spec, size, ctx)
    repairs = 0
    while errors and repairs < 2:
        repairs += 1
        await ctx.event("spec_design_repair", {"attempt": repairs, "errors": errors[:10]})
        repair_prompt = (
            "Your spec failed deterministic checks. Fix ALL errors and return the "
            "full envelope again. Errors:\n" + "\n".join(f"- {e}" for e in errors[:20])
        )
        result = await ctx.call_agent("spec-designer", repair_prompt, schema)
        spec = (result.structured or {}).get("spec")
        if spec is None:
            raise PhaseError("spec-designer repair returned no spec", code="agent_failed")
        errors = _deep_check_errors(requirements, spec, size, ctx)
    if errors:
        raise PhaseError(
            f"spec failed deterministic checks after 2 repairs: {'; '.join(errors[:5])}",
            code="validation_failed",
        )

    if mode == "fix" and _current_spec(ctx) is not None:
        from ...engine.review_rules import apply_spec_diff_guard

        guarded, reverted = apply_spec_diff_guard(
            _current_spec(ctx), spec, collect_target_ids(ctx.state.get("spec_findings", []))
        )
        spec = guarded
        if reverted:
            await ctx.event("spec_fix_diff_guard", {"reverted_items": reverted})

    new_version = ctx.versions.get("spec", 0) + 1
    (ctx.workspace.canonical / f"spec.v{new_version}.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    versions = ctx.versions
    versions["spec"] = new_version
    state = dict(ctx.state)
    state["spec_mode"] = "design"
    await ctx.save(versions=versions, state=state)
    await ctx.event(
        "spec_version_created",
        {"version": new_version, "components": len(spec.get("architecture", {}).get("components", []))},
    )
    return ("continue", "spec_review")


def _current_spec(ctx: JobContext) -> dict[str, Any] | None:
    version = ctx.versions.get("spec", 0)
    if version < 1:
        return None
    path = ctx.workspace.canonical / f"spec.v{version}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _spec_diff_summary(old_doc: dict[str, Any] | None, new_doc: dict[str, Any]) -> str:
    if old_doc is None:
        return "(first version)"
    added, removed = [], []
    for section in ("components", "interfaces", "behaviors", "test_plan"):
        def ids(doc, key):
            if key == "components":
                return {i["id"] for i in doc.get("architecture", {}).get(key, [])}
            return {i["id"] for i in doc.get(key, []) if isinstance(i, dict) and "id" in i}

        old_ids, new_ids = ids(old_doc, section), ids(new_doc, section)
        added.extend(sorted(new_ids - old_ids))
        removed.extend(sorted(old_ids - new_ids))
        # changed detection is coarse: id present in both counts as changed
        # only when reviewed — keep summary simple
    return f"added: {added or 'none'}\nremoved: {removed or 'none'}"


async def spec_review(ctx: JobContext):
    schema = load_schema("review")  # no $refs; still safe to send
    checklist_ids, checklist_text = _checklist()
    spec = _current_spec(ctx)
    if spec is None:
        raise PhaseError("no canonical spec to review", code="engine_error")
    rounds = ctx.rounds
    round_n = rounds.get("spec_review", 0) + 1
    mode = "full" if round_n == 1 else "verify"
    if mode == "full":
        prompt = (
            "Review the spec strictly against this fixed checklist:\n"
            f"{checklist_text}\n\n"
            "You may delegate the three lenses (completeness, consistency, "
            "testability) to review-lens sub-agents and merge their findings. "
            "Report ONLY findings tied to these checklist ids. Severity: P0 wrong/"
            "missing a confirmed requirement; P1 ambiguity an implementer would "
            "ask about; P2 polish. Each finding lists target_ids (spec element "
            "ids to change).\n\n"
            f"Requirements (authoritative):\n"
            f"{json.dumps(ctx.current_requirements(), ensure_ascii=False, indent=2)}\n\n"
            f"Spec:\n{json.dumps(spec, ensure_ascii=False, indent=2)}"
        )
    else:
        prior = ctx.state.get("spec_findings", [])
        prior_spec_path = ctx.workspace.canonical / (
            f"spec.v{ctx.versions.get('spec', 1) - 1}.json"
        )
        prior_spec = (
            json.loads(prior_spec_path.read_text(encoding="utf-8"))
            if prior_spec_path.is_file()
            else None
        )
        prompt = (
            "VERIFY round: judge ONLY the previous findings against the diff "
            "(resolved / not_resolved each). New findings are rejected by the "
            "schema.\n\n"
            f"Previous findings:\n{json.dumps(prior, ensure_ascii=False, indent=2)}\n\n"
            f"Diff since the fix:\n{_spec_diff_summary(prior_spec, spec)}\n\n"
            f"Current spec:\n{json.dumps(spec, ensure_ascii=False, indent=2)}"
        )
    ctx.state["step_round"] = round_n
    result = await ctx.call_agent("spec-reviewer", prompt, schema)
    review = result.structured or {}

    known_issues = list(ctx.known_issues)
    if mode == "full":
        processed = process_full(review, checklist_ids)
        blocking = processed["blocking"]
        known_issues.extend(processed["p2_known_issues"])
        verdict = processed["verdict"]
        state = dict(ctx.state)
        state["spec_findings"] = blocking
    else:
        prior_blocking = ctx.state.get("spec_findings", [])
        processed = process_verify(review, prior_blocking)
        verdict = processed["verdict"]
        blocking = prior_blocking
        state = dict(ctx.state)
    rounds["spec_review"] = round_n
    (ctx.workspace.reviews / f"spec.r{round_n}.json").write_text(
        json.dumps({"round": round_n, "mode": mode, "raw": review,
                    "processed": processed}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    await ctx.save(round=rounds, known_issues=known_issues, state=state)
    await ctx.event(
        "spec_review_completed",
        {"round": round_n, "mode": mode, "verdict": verdict,
         "blocking": [f["id"] for f in blocking] if mode == "full" else processed.get("not_resolved", [])},
    )

    caps = ctx.config.review_caps
    if verdict == "pass":
        return await _render(ctx)
    if round_n >= caps.spec + (1 if state.get("p0_extra_round") else 0):
        # design §3: after round 2 with only P1/P2 -> render with issues;
        # P0 remaining -> ONE extra P0-only fix round, then render regardless
        p0_left = [f for f in blocking if f.get("severity") == "P0"]
        if p0_left and not state.get("p0_extra_round"):
            state = dict(state)
            state["p0_extra_round"] = True
            state["spec_mode"] = "fix"
            state["spec_findings"] = p0_left  # P0 only
            await ctx.save(state=state)
            await ctx.event("spec_p0_extra_round", {"targets": sorted(collect_target_ids(p0_left))})
            return ("continue", "spec_design")
        open_notes = [
            f"[{f.get('severity')}] {f.get('checklist_id')}: {f.get('problem')}"
            for f in blocking
        ]
        known_issues.extend(open_notes)
        spec["known_issues"] = sorted(set(known_issues))
        (ctx.workspace.canonical / f"spec.v{ctx.versions.get('spec', 1)}.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        await ctx.save(known_issues=known_issues)
        await ctx.event("spec_review_cap_reached", {"open_findings": open_notes})
        return await _render(ctx)
    # normal fix round
    state = dict(state)
    state["spec_mode"] = "fix"
    state["spec_findings"] = blocking
    await ctx.save(state=state)
    await ctx.event("spec_fix_round_started", {"targets": sorted(collect_target_ids(blocking))})
    return ("continue", "spec_design")


async def _render(ctx: JobContext):
    """Render artifacts via the output profile (design §8) and finish."""
    requirements = ctx.current_requirements()
    spec = _current_spec(ctx)
    if requirements is None or spec is None:
        raise PhaseError("missing canonical docs at render time", code="engine_error")
    profile_ref = ctx.job.output_profile
    if profile_ref is None or profile_ref in ("", "default"):
        profile = "default"
    elif isinstance(profile_ref, str):
        profile = profile_ref
    else:
        profile = json.loads(profile_ref) if isinstance(profile_ref, str) else profile_ref

    events = await ctx.db.list_events(ctx.job.job_id)
    tokens: dict[str, int] = {}
    for event in events:
        if event["type"] == "agent_completed":
            agent = (event["data"] or {}).get("agent")
            tokens[agent] = tokens.get(agent, 0) + ((event["data"] or {}).get("tokens") or 0)
    known_issues = list(ctx.known_issues)
    status = "completed" if not known_issues else "completed_with_issues"
    meta = {
        "job_id": ctx.job.job_id,
        "project": requirements.get("project"),
        "status": status,
        "versions": {
            "requirements": ctx.versions.get("requirements", 0),
            "spec": ctx.versions.get("spec", 0),
        },
        "profile": "default" if not isinstance(profile, dict) else profile.get("name", "custom"),
        "repo": json.loads(ctx.job.repo) if ctx.job.repo else None,
        "known_issues": known_issues,
        "metrics": {
            "duration_s": round(time.time() - _created_epoch(ctx.job.created_at), 1),
            "tokens": tokens,
        },
        "rendered_at": dt.datetime.now(dt.UTC).isoformat(),
    }
    try:
        outputs = render_profile(
            profile, requirements=requirements, spec=spec, meta=meta
        )
    except Exception as exc:
        raise PhaseError(f"render failed: {exc}", code="render_failed") from exc
    out_dir = ctx.workspace.out / f"v{ctx.versions.get('spec', 1)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for path, data in outputs.items():
        target = out_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    await ctx.event(
        "artifacts_rendered",
        {"version": ctx.versions.get("spec", 1), "files": sorted(outputs)},
    )
    return ("done", status, {"known_issues": known_issues})


def _created_epoch(created_at: str) -> float:
    try:
        return dt.datetime.fromisoformat(created_at).timestamp()
    except ValueError:
        return time.time()

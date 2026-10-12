"""Revise flow (design §3, D8; plan M6): post-completion change requests.

revise_analyze classifies the request into three paths:
  1. spec-only patch        -> spec_design (revise mode) -> spec_review -> render
  2. requirements affected  -> req_design (change_request) -> ... -> confirm gate
  3. questions needed       -> questions gate (answers carry the change forward)
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from ...checks.schema import deref_schema, load_schema, validate_named
from ...engine.runner import JobContext, PhaseError


async def revise_analyze(ctx: JobContext):
    change_text = ctx.state.get("change_request") or ""
    if not change_text:
        raise PhaseError("revise requested without change text", code="engine_error")
    schema = deref_schema(load_schema("revise"))
    requirements = ctx.current_requirements() or {}
    spec_version = ctx.versions.get("spec", 0)
    spec = None
    spec_path = ctx.workspace.canonical / f"spec.v{spec_version}.json"
    if spec_path.is_file():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

    prompt = (
        "A user requests a POST-COMPLETION change to a delivered project. "
        "Classify it (output via the schema only):\n"
        "- needs_questions: ONLY if a genuine product decision blocks the change\n"
        "  (suggest at most 3 questions, each with a safe default_answer).\n"
        "- requirements_affected: the change alters WHAT the system must do\n"
        "  (scope, behavior, acceptance) rather than HOW it is designed.\n"
        "- otherwise both false: it is a spec-only patch.\n"
        "Be conservative about questions — prefer defaults/assumptions.\n\n"
        f"CHANGE REQUEST (verbatim):\n---\n{change_text}\n---\n\n"
        f"REQUIREMENTS (summary):\n{json.dumps(_summary(requirements), ensure_ascii=False, indent=2)}\n\n"
        f"SPEC (summary):\n{json.dumps(_spec_summary(spec), ensure_ascii=False, indent=2)}"
    )
    result = await ctx.call_agent("revise-analyst", prompt, schema)
    analysis = result.structured or {}
    await ctx.event(
        "revise_analyzed",
        {
            "needs_questions": analysis.get("needs_questions"),
            "requirements_affected": analysis.get("requirements_affected"),
            "reason": str(analysis.get("reason", ""))[:200],
        },
    )

    if analysis.get("needs_questions"):
        questions = [
            q for q in (analysis.get("suggested_questions") or [])
            if not validate_named(q, "question")
        ][:7]
        if questions:
            state = dict(ctx.state)
            state["question_round"] = state.get("question_round", 0) + 1
            ttl = ctx.options.get("question_ttl_s", ctx.config.question_ttl_s)
            expire_at = (
                dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=int(ttl))
            ).isoformat()
            await ctx.save(state=state)
            return (
                "gate",
                "questions",
                {
                    "questions": questions,
                    "questions_expire_at": expire_at,
                    "event_type": "revise_questions_asked",
                },
            )
        # invalid questions fell through: treat as no-questions path

    if analysis.get("requirements_affected"):
        state = dict(ctx.state)
        state["req_mode"] = "design"
        state["change_request"] = change_text
        await ctx.save(state=state)
        return ("continue", "req_design")

    state = dict(ctx.state)
    state["spec_mode"] = "revise"
    state["spec_change"] = change_text
    await ctx.save(state=state)
    return ("continue", "spec_design")


def _summary(requirements: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": requirements.get("project"),
        "goal": requirements.get("goal"),
        "requirements": [
            {"id": r.get("id"), "title": r.get("title"), "priority": r.get("priority")}
            for r in requirements.get("requirements", [])
        ],
        "decisions": [
            {"id": d.get("id"), "answer": d.get("answer"), "source": d.get("source")}
            for d in requirements.get("decisions", [])
        ],
    }


def _spec_summary(spec: dict[str, Any] | None) -> dict[str, Any]:
    if not spec:
        return {"note": "no spec yet"}
    return {
        "overview": spec.get("overview", "")[:400],
        "components": [
            {"id": c.get("id"), "name": c.get("name")}
            for c in spec.get("architecture", {}).get("components", [])
        ],
        "interfaces": [{"id": i.get("id"), "kind": i.get("kind")} for i in spec.get("interfaces", [])],
        "known_issues": spec.get("known_issues", []),
    }

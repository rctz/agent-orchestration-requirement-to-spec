"""Requirement phase steps: req_design and req_review (design §3-§5).

Actions returned (consumed by runner.JobRunner):
  ("gate", "questions", {...})            — question gate, worker freed
  ("gate", "confirm_requirements", {...}) — human confirm gate
  ("continue", "req_design"|"req_review") — next phase step
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml

from ...checks.language import english_only_violations
from ...checks.schema import deref_schema, load_schema, validate_named
from ...checks.size import check_size
from ...config import SizeBudget
from ...engine.review_rules import (
    apply_diff_guard,
    collect_target_ids,
    process_full,
    process_verify,
)
from ...engine.runner import JobContext, PhaseError
from ...paths import REPO_ROOT

CHECKLIST_PATH = REPO_ROOT / "checklists" / "requirements.v1.yaml"


def _utcnow_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _load_checklist() -> dict[str, Any]:
    return yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))


def next_decision_id(doc: dict[str, Any]) -> str:
    numbers = [
        int(d["id"].split("-")[1]) for d in doc.get("decisions", []) if "-" in d.get("id", "")
    ]
    return f"D-{(max(numbers) + 1) if numbers else 1:02d}"


def append_decision(
    doc: dict[str, Any], question_id: str, answer: str, source: str
) -> str:
    decision_id = next_decision_id(doc)
    doc.setdefault("decisions", []).append(
        {"id": decision_id, "question_id": question_id, "answer": answer, "source": source}
    )
    return decision_id


def record_gate_decisions(
    workspace: Path, answers: dict[str, str], defaults_applied: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build decision entries for gate answers / expiry defaults.

    Entries are stored in engine state (the decision log is CODE-owned,
    design §7 spirit: never rely on the LLM to carry decisions forward).
    IDs are allocated against the latest canonical document."""
    files = sorted((workspace / "canonical").glob("requirements.v*.json"))
    existing: list[dict[str, Any]] = []
    if files:
        doc = json.loads(files[-1].read_text(encoding="utf-8"))
        existing = list(doc.get("decisions", []))

    def allocate() -> str:
        numbers = [
            int(d["id"].split("-")[1])
            for d in existing
            if isinstance(d.get("id"), str) and "-" in d["id"]
        ]
        return f"D-{(max(numbers) + 1) if numbers else 1:02d}"

    entries: list[dict[str, Any]] = []
    for question_id, answer in answers.items():
        decision_id = allocate()
        existing.append({"id": decision_id})
        entries.append(
            {"id": decision_id, "question_id": question_id, "answer": answer,
             "source": "user"}
        )
    for question in defaults_applied:
        decision_id = allocate()
        existing.append({"id": decision_id})
        entries.append(
            {"id": decision_id, "question_id": question.get("id", "Q-??"),
             "answer": question.get("default_answer", ""),
             "source": "system_default_expired"}
        )
    return entries


def merge_decisions(
    doc_decisions: list[dict[str, Any]], decision_log: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Union of LLM-authored decisions and the code-owned log, deduped by
    question_id (code entries win on conflict)."""
    merged = list(doc_decisions)
    seen = {
        d.get("question_id") for d in merged if d.get("question_id")
    }
    for entry in decision_log:
        if entry.get("question_id") not in seen:
            merged.append(entry)
            seen.add(entry.get("question_id"))
    return merged


# ---- req_design ------------------------------------------------------------


def _design_instructions(lang: str) -> str:
    return (
        "Produce the canonical requirements document for this job.\n"
        "Output ONLY through the provided schema "
        '({"requirements": {...}, "questions": [...]}).\n\n'
        "Rules:\n"
        "- All `requirements` fields in ENGLISH (artifacts are English).\n"
        f"- `questions` text/why in the USER'S LANGUAGE ({lang}); they are shown to the user.\n"
        "- Every requirement needs observable, testable acceptance criteria.\n"
        "- TRIAGE before asking: resolve anything you can from the prompt or common "
        "practice yourself and record it as an assumption; ask ONLY product/preference "
        "questions you cannot resolve (max 7, ordered by impact, each with a "
        "default_answer and default_rationale).\n"
        "- Classify size honestly: S (<=12 REQs), M (<=30), L (<=60).\n"
        "- IDs: REQ-001..., A-01..., D-01... (never reuse numbers).\n"
    )


def _build_design_prompt(ctx: JobContext) -> tuple[str, dict[str, Any] | None]:
    lang = ctx.options.get("user_language", "en")
    mode = ctx.state.get("req_mode", "design")
    prior = ctx.current_requirements()
    parts: list[str] = []
    if mode == "fix":
        findings = ctx.state.get("findings", [])
        targets = sorted(collect_target_ids(findings))
        parts.append(
            "A review found blocking findings. Produce the NEXT version of the "
            "requirements document fixing ONLY the requirement items whose ids are "
            "in this target list (any other edit will be reverted by code):\n"
            f"target_ids: {json.dumps(targets)}\n\n"
            f"Findings (fix exactly these):\n{json.dumps(findings, ensure_ascii=False, indent=2)}\n\n"
            f"Prior document:\n{json.dumps(prior, ensure_ascii=False, indent=2)}\n\n"
            "Do NOT add questions in fix mode (questions: [])."
        )
        return "\n".join(parts), prior
    parts.append(_design_instructions(lang))
    parts.append(f"USER PROMPT (verbatim):\n---\n{ctx.job.prompt}\n---")
    if ctx.state.get("repo_summary"):
        parts.append(
            "The user attached an EXISTING CODEBASE. Its scanned summary "
            "(stack, modules, conventions, interfaces, constraints) follows. "
            "New requirements MUST fit this codebase — cite the modules you "
            "would touch:\n"
            + json.dumps(ctx.state["repo_summary"], ensure_ascii=False, indent=2)
        )
    if ctx.state.get("change_request"):
        parts.append(
            "The user requested a change after seeing a previous version:\n"
            f"{ctx.state['change_request']}\n"
            "Produce a new version addressing it."
        )
        parts.append(f"Prior document:\n{json.dumps(prior, ensure_ascii=False, indent=2)}")
    elif ctx.state.get("answers"):
        parts.append(
            "The user answered clarifying questions. Merge them as decisions "
            "(source: user) and produce the next version accordingly:"
        )
        answered = "\n".join(f"- {qid}: {answer}" for qid, answer in ctx.state["answers"].items())
        parts.append(answered)
        if prior:
            parts.append(f"Prior document:\n{json.dumps(prior, ensure_ascii=False, indent=2)}")
    elif prior:
        parts.append(f"Prior document:\n{json.dumps(prior, ensure_ascii=False, indent=2)}")
    return "\n\n".join(parts), prior


def _deep_check_errors(doc: dict[str, Any], size: str, budgets: dict[str, SizeBudget]) -> list[str]:
    errors = validate_named(doc, "requirements")
    errors += english_only_violations(doc)
    errors += check_size(size, doc, None, budgets)
    return errors


async def req_design(ctx: JobContext):
    schema = deref_schema(load_schema("req_design_output"))
    prompt, prior = _build_design_prompt(ctx)
    budgets = ctx.config.size_budgets

    result = await ctx.call_agent("req-designer", prompt, schema)
    envelope = result.structured or {}
    doc = envelope.get("requirements")
    if doc is None:
        raise PhaseError("req-designer returned no requirements document", code="agent_failed")
    questions = list(envelope.get("questions") or [])

    size = ctx.options.get("size") or doc.get("size") or "S"
    errors = _deep_check_errors(doc, size, budgets)
    repairs = 0
    while errors and repairs < 2:  # design §2A.6: repair with exact errors, max 2
        repairs += 1
        repair_prompt = (
            "Your requirements document failed deterministic checks. Fix ALL errors "
            "and return the full envelope again.\n"
            f"Size class to respect: {size}\n"
            f"Errors:\n" + "\n".join(f"- {e}" for e in errors[:20])
        )
        await ctx.event("design_repair", {"attempt": repairs, "errors": errors[:10]})
        result = await ctx.call_agent("req-designer", repair_prompt, schema)
        envelope = result.structured or {}
        doc = envelope.get("requirements")
        if doc is None:
            raise PhaseError("req-designer repair returned no document", code="agent_failed")
        questions = list(envelope.get("questions") or [])
        errors = _deep_check_errors(doc, size, budgets)
    if errors:
        raise PhaseError(
            "requirements failed deterministic checks after 2 repairs: "
            + "; ".join(errors[:5]),
            code="validation_failed",
        )

    doc["size"] = size
    # the decision log is code-owned: merge gate/expiry decisions the LLM
    # did not (or should not) carry forward
    doc["decisions"] = merge_decisions(
        doc.get("decisions", []), ctx.state.get("decision_log", [])
    )
    mode = ctx.state.get("req_mode", "design")
    if mode == "fix" and prior is not None:
        targets = collect_target_ids(ctx.state.get("findings", []))
        doc, reverted = apply_diff_guard(prior, doc, targets)
        if reverted:
            await ctx.event("fix_diff_guard", {"reverted_items": reverted})

    # write next canonical version
    new_version = ctx.versions.get("requirements", 0) + 1
    ctx.workspace.canonical.mkdir(parents=True, exist_ok=True)
    (ctx.workspace.canonical / f"requirements.v{new_version}.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    rounds = ctx.rounds
    del rounds  # req_design does not change review rounds
    versions = ctx.versions
    versions["requirements"] = new_version
    state = dict(ctx.state)
    state["req_mode"] = "design"  # a fresh design pass may ask questions again
    state["answers"] = {}
    state["change_request"] = None
    state["question_round"] = state.get("question_round", 0)
    # The caller's project name (options.project_name) is the source of
    # truth. Adopt the LLM's doc.project only when the caller never named
    # the project — never overwrite a caller-provided name.
    await ctx.save(
        versions=versions,
        project=(ctx.job.project or doc.get("project")),
        state=state,
    )
    await ctx.event(
        "requirements_version_created",
        {"version": new_version, "requirements": len(doc.get("requirements", [])),
         "mode": mode},
    )

    # questions gate (design mode only)
    if mode == "design" and questions:
        question_round = state.get("question_round", 0) + 1
        if question_round > ctx.config.max_question_rounds:
            # design §3: proceed with explicit assumptions recorded as decisions
            doc = ctx.current_requirements() or doc
            for question in questions:
                append_decision(
                    doc, question.get("id", "Q-??"),
                    question.get("default_answer", ""), "agent_assumption",
                )
            (ctx.workspace.canonical / f"requirements.v{new_version}.json").write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            await ctx.event(
                "question_round_cap_reached",
                {"applied_defaults": [q.get("id") for q in questions]},
            )
            return ("continue", "req_review")
        valid_questions = []
        for question in questions[:7]:  # batch cap (design §5)
            if not validate_named(question, "question"):
                valid_questions.append(question)
            else:
                await ctx.event("question_dropped", {"question": question.get("id")})
        if valid_questions:
            state = dict(ctx.state)
            state["question_round"] = question_round
            ttl = ctx.options.get("question_ttl_s", ctx.config.question_ttl_s)
            expire_at = (
                dt.datetime.now(dt.UTC) + dt.timedelta(seconds=int(ttl))
            ).isoformat()
            await ctx.save(state=state)
            return (
                "gate",
                "questions",
                {
                    "questions": valid_questions,
                    "questions_expire_at": expire_at,
                    "event_type": "questions_asked",
                },
            )
    return ("continue", "req_review")


# ---- req_review ------------------------------------------------------------


def _checklist_text() -> tuple[set[str], str]:
    checklist = _load_checklist()
    ids = set(checklist.get("ids", {}))
    lines = []
    for cid, item in checklist.get("ids", {}).items():
        lines.append(f"- {cid} — {item.get('title')}: {item.get('detail')}")
    return ids, "\n".join(lines)


def _diff_summary(old_doc: dict[str, Any] | None, new_doc: dict[str, Any]) -> str:
    if old_doc is None:
        return "(first version)"
    old_items = {i["id"]: i for i in old_doc.get("requirements", [])}
    changed, added = [], []
    for item in new_doc.get("requirements", []):
        if item["id"] not in old_items:
            added.append(item["id"])
        elif item != old_items[item["id"]]:
            changed.append(item["id"])
    removed = [rid for rid in old_items if rid not in {i["id"] for i in new_doc.get("requirements", [])}]
    return (
        f"changed: {changed or 'none'}\nadded: {added or 'none'}\n"
        f"removed: {removed or 'none'}"
    )


async def req_review(ctx: JobContext):
    schema = load_schema("review")
    checklist_ids, checklist_text = _checklist_text()
    doc = ctx.current_requirements()
    if doc is None:
        raise PhaseError("no canonical requirements to review", code="engine_error")
    rounds = ctx.rounds
    round_n = rounds.get("req_review", 0) + 1
    mode = "full" if round_n == 1 else "verify"
    if mode == "full":
        prompt = (
            "Review the requirements document strictly against this fixed checklist:\n"
            f"{checklist_text}\n\n"
            "Report ONLY findings tied to these checklist ids. Severity: P0 = wrong/"
            "contradictory/missing a confirmed requirement; P1 = ambiguity an "
            "implementer would have to ask about; P2 = polish (never blocks). "
            "Each finding lists target_ids (the REQ ids to change).\n\n"
            f"Requirements document:\n{json.dumps(doc, ensure_ascii=False, indent=2)}"
        )
    else:
        prior_findings = ctx.state.get("findings", [])
        prior_doc_path = ctx.workspace.canonical / (
            f"requirements.v{ctx.versions.get('requirements', 1) - 1}.json"
        )
        prior_doc = (
            json.loads(prior_doc_path.read_text(encoding="utf-8"))
            if prior_doc_path.is_file()
            else None
        )
        prompt = (
            "VERIFY round: judge ONLY the previous findings against the diff. "
            "For every finding id return resolved or not_resolved "
            "(with a short note). Do NOT report new findings — the schema rejects them.\n\n"
            f"Previous findings:\n{json.dumps(prior_findings, ensure_ascii=False, indent=2)}\n\n"
            f"Diff since the fix:\n{_diff_summary(prior_doc, doc)}\n\n"
            f"Current document:\n{json.dumps(doc, ensure_ascii=False, indent=2)}"
        )
    ctx.state["step_round"] = round_n
    result = await ctx.call_agent("req-reviewer", prompt, schema)
    review = result.structured or {}

    known_issues = list(ctx.known_issues)
    if mode == "full":
        processed = process_full(review, checklist_ids)
        blocking = processed["blocking"]
        known_issues.extend(processed["p2_known_issues"])
        verdict = processed["verdict"]
        state = dict(ctx.state)
        state["findings"] = blocking
        if processed["dropped"]:
            await ctx.event(
                "findings_dropped", {"dropped": processed["dropped"]}
            )
    else:
        prior_blocking = ctx.state.get("findings", [])
        processed = process_verify(review, prior_blocking)
        verdict = processed["verdict"]
        blocking = prior_blocking  # unresolved stay as-is
        state = dict(ctx.state)
    rounds["req_review"] = round_n
    review_record = {
        "round": round_n,
        "mode": mode,
        "verdict": verdict,
        "raw": review,
        "processed": processed,
    }
    ctx.workspace.reviews.mkdir(parents=True, exist_ok=True)
    (ctx.workspace.reviews / f"req.r{round_n}.json").write_text(
        json.dumps(review_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    await ctx.save(
        round=rounds, known_issues=known_issues, state=state
    )
    await ctx.event(
        "req_review_completed",
        {
            "round": round_n,
            "mode": mode,
            "verdict": verdict,
            "blocking": [f["id"] for f in blocking] if mode == "full" else processed.get("not_resolved", []),
        },
    )

    cap = ctx.config.review_caps.requirements
    if verdict == "pass":
        return (
            "gate",
            "confirm_requirements",
            {
                "requirements_preview": doc,
                "questions_expire_at": _confirm_expiry(ctx),
                "event_type": "confirm_requirements_requested",
            },
        )
    if round_n >= cap:
        # design §3: cap hit with blocking findings -> confirm gate, findings open
        open_notes = [
            f"[{f.get('severity')}] {f.get('checklist_id')}: {f.get('problem')}"
            for f in blocking
        ]
        known_issues.extend(open_notes)
        await ctx.save(known_issues=known_issues)
        await ctx.event("review_cap_reached", {"open_findings": open_notes})
        return (
            "gate",
            "confirm_requirements",
            {
                "requirements_preview": doc,
                "questions_expire_at": _confirm_expiry(ctx),
                "event_type": "confirm_requirements_requested_with_open_items",
            },
        )
    # fix round (design §2A.6): designer fixes target_ids only
    state = dict(ctx.state)
    state["req_mode"] = "fix"
    state["findings"] = blocking
    await ctx.save(state=state)
    await ctx.event("fix_round_started", {"targets": sorted(collect_target_ids(blocking))})
    return ("continue", "req_design")


def _confirm_expiry(ctx: JobContext) -> str:
    ttl = ctx.options.get("question_ttl_s", ctx.config.question_ttl_s)
    return (
        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=int(ttl))
    ).isoformat()

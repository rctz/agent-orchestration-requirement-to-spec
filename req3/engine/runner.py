"""JobRunner: phase dispatch loop for one job (design §3, §2A.2b).

Code decides WHEN (phase order, gates, caps); the LLM only decides HOW
(inside a phase step via the Executor). Every step ends in a saved state
or a terminal failure with error.code/phase/message — no silent death.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ..config import Config
from ..executor.base import AgentResult, Executor
from ..store.db import Database, JobRecord
from ..store.workspace import Workspace
from .machine import TERMINAL_STATUS_VALUES

MAX_QUESTIONS_PER_ROUND = 7  # design §5


class PhaseError(Exception):
    """Terminal failure of a phase step (after retries)."""

    def __init__(self, message: str, *, code: str = "phase_error"):
        super().__init__(message)
        self.code = code


class JobContext:
    """Everything a phase needs: job record, workspace, engine state, calls."""

    def __init__(
        self,
        *,
        config: Config,
        db: Database,
        executor: Executor,
        job: JobRecord,
        workspace_root: Path,
    ):
        self.config = config
        self.db = db
        self.executor = executor
        self.job = job
        self.workspace = Workspace(workspace_root, job.job_id)
        self.state: dict[str, Any] = json.loads(job.engine_state or "{}")
        self.options: dict[str, Any] = json.loads(job.options or "{}")

    # ---- persistence -------------------------------------------------------

    async def save(self, **changes: Any) -> None:
        """Persist job columns; `state=` updates engine_state."""
        if "state" in changes:
            self.state = changes.pop("state")
            changes["engine_state"] = json.dumps(self.state, ensure_ascii=False)
        for json_key in ("round", "versions"):
            if json_key in changes and isinstance(changes[json_key], dict):
                changes[json_key] = json.dumps(changes[json_key])
        if "questions" in changes and isinstance(changes["questions"], list):
            changes["questions"] = json.dumps(changes["questions"], ensure_ascii=False)
        if "requirements_preview" in changes and isinstance(
            changes["requirements_preview"], dict
        ):
            changes["requirements_preview"] = json.dumps(
                changes["requirements_preview"], ensure_ascii=False
            )
        if "known_issues" in changes and isinstance(changes["known_issues"], list):
            changes["known_issues"] = json.dumps(
                changes["known_issues"], ensure_ascii=False
            )
        if "error" in changes and isinstance(changes["error"], dict):
            changes["error"] = json.dumps(changes["error"], ensure_ascii=False)
        await self.db.update_job(self.job.job_id, **changes)
        for name, value in changes.items():
            setattr(self.job, name, value)

    async def event(self, type_: str, data: dict[str, Any] | None = None) -> None:
        await self.db.append_event(self.job.job_id, type_, data or {})

    # ---- round/versions helpers -------------------------------------------

    @property
    def rounds(self) -> dict[str, int]:
        return json.loads(self.job.round or "{}")

    @property
    def versions(self) -> dict[str, int]:
        return json.loads(self.job.versions or "{}")

    @property
    def known_issues(self) -> list[str]:
        return json.loads(self.job.known_issues or "[]")

    def current_requirements(self) -> dict[str, Any] | None:
        version = self.versions.get("requirements", 0)
        if version < 1:
            return None
        path = self.workspace.canonical / f"requirements.v{version}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # ---- executor calls with retries + nonce (design §10 cache caveat) ----

    async def call_agent(self, agent: str, prompt: str, schema: dict[str, Any]) -> AgentResult:
        attempts = self.config.step_retries + 1
        last_error = ""
        for attempt in range(1, attempts + 1):
            self.state["attempt"] = attempt
            nonce = (
                f"[req3 nonce job={self.job.job_id} phase={self.job.phase} "
                f"round={self.state.get('step_round', 0)} attempt={attempt}]"
            )
            result = await self.executor.run_agent(
                self.workspace.root,
                agent,
                f"{nonce}\n{prompt}",
                schema=schema,
                attachments=None,
                timeout_s=self.config.step_timeout_s,
            )
            if result.error is None:
                await self.event(
                    "agent_completed",
                    {
                        "agent": agent,
                        "tokens": result.tokens,
                        "duration_s": result.duration_s,
                        "model": result.model,
                    },
                )
                return result
            last_error = result.error
            await self.event(
                "agent_error",
                {"agent": agent, "attempt": attempt, "error": result.error[:300]},
            )
            if attempt < attempts:
                await asyncio.sleep(2.0 * attempt)
        raise PhaseError(
            f"{agent} failed after {attempts} attempts: {last_error}",
            code="agent_failed",
        )


class JobRunner:
    """Runs one job from its current phase-step until a gate or terminal."""

    def __init__(
        self,
        config: Config,
        db: Database,
        executor: Executor,
        workspace_root: Path,
        webhooks=None,
    ):
        from .phases import requirement  # local import keeps module load light

        self._requirement = requirement
        self.webhooks = webhooks
        self.config = config
        self.db = db
        self.executor = executor
        self.workspace_root = workspace_root

    async def run(self, job_id: str) -> None:
        job = await self.db.get_job(job_id)
        if job is None or job.status in TERMINAL_STATUS_VALUES:
            return
        if job.status != "running":
            return  # gates and queued jobs are not run here
        ctx = JobContext(
            config=self.config,
            db=self.db,
            executor=self.executor,
            job=job,
            workspace_root=self.workspace_root,
        )
        while True:
            job = await self.db.get_job(job_id)
            if job is None or job.status in TERMINAL_STATUS_VALUES:
                return
            ctx.job = job
            phase = job.phase or "repo_resolve"
            if ctx.state.get("phase") != phase:
                ctx.state["phase"] = phase
                ctx.state["attempt"] = 1
                ctx.state["step_round"] = (
                    ctx.rounds.get("req_review", 0) if phase == "req_review" else 0
                )
            await ctx.event(
                "phase_entered",
                {"phase": phase, "attempt": ctx.state.get("attempt", 1)},
            )
            try:
                action = await self._dispatch(ctx, phase)
            except PhaseError as exc:
                # A cancel that landed while the agent call was in flight
                # must survive: re-check before writing failure state.
                fresh = await self.db.get_job(job_id)
                if fresh is not None and fresh.status in TERMINAL_STATUS_VALUES:
                    return
                await ctx.save(
                    status="failed",
                    error={"code": exc.code, "message": str(exc), "phase": phase},
                )
                await ctx.event(
                    "job_failed", {"phase": phase, "code": exc.code, "message": str(exc)}
                )
                self._notify_webhook(ctx.job, "job_failed", "failed")
                return
            # Same guard on the success path: the phase step may have taken
            # minutes (LLM call); a cancel during it must not be clobbered
            # by the transition save below.
            fresh = await self.db.get_job(job_id)
            if fresh is not None and fresh.status in TERMINAL_STATUS_VALUES:
                return
            kind = action[0]
            if kind == "continue":
                await ctx.save(phase=action[1], status="running", gate=None)
                continue
            if kind == "gate":
                _, gate, payload = action
                event_type = payload.pop("event_type", "input_required")
                await ctx.save(status="input_required", gate=gate, **payload)
                await ctx.event(event_type, {"gate": gate})
                self._notify_webhook(ctx.job, event_type, "input_required")
                return
            if kind == "done":
                _, status, payload = action
                await ctx.save(status=status, phase="done", gate=None, **payload)
                await ctx.event("job_completed", {"status": status})
                self._notify_webhook(ctx.job, "job_completed", status)
                return
            raise PhaseError(f"unknown action {kind!r}", code="engine_error")

    def _notify_webhook(self, job, event_type: str, status: str):
        if self.webhooks is None:
            return
        callback = getattr(job, "callback_url", None)
        if callback:
            self.webhooks.notify(job.job_id, callback, event_type, status)

    async def _dispatch(self, ctx: JobContext, phase: str):
        if phase == "repo_resolve":
            return await self._repo_resolve(ctx)
        if phase == "repo_scan":
            from .phases.repo import repo_scan

            return await repo_scan(ctx)
        if phase == "req_design":
            return await self._requirement.req_design(ctx)
        if phase == "req_review":
            return await self._requirement.req_review(ctx)
        if phase == "spec_design":
            from .phases import spec

            return await spec.spec_design(ctx)
        if phase == "spec_review":
            from .phases import spec

            return await spec.spec_review(ctx)
        if phase == "revise_analyze":
            from .phases import revise

            return await revise.revise_analyze(ctx)
        if phase in ("render", "publish"):
            # rendering happens inside spec_review completion; publish is M9+
            raise PhaseError(
                f"phase {phase!r} is not reachable in this flow yet",
                code="phase_unavailable",
            )
        raise PhaseError(f"unknown phase {phase!r}", code="engine_error")

    async def _repo_resolve(self, ctx: JobContext):
        """Design §10 / §2A.5: explicit field or prompt regex -> validate ->
        ambiguity handling -> fetch (shallow clone / snapshot) -> repo_scan."""
        from ..repo import fetch as repo_fetch
        from ..repo import resolve as rr

        cfg = ctx.config.repo
        state = dict(ctx.state)
        record = json.loads(ctx.job.repo) if ctx.job.repo else None
        ls_remote = rr.git_ls_remote

        # Answer to an earlier "which repo?" question (questions gate).
        if record is None and state.get("repo_question_pending"):
            answer = (state.get("answers", {}).get("Q-00") or "").strip()
            state.pop("repo_question_pending", None)
            state.pop("resume_phase", None)
            await ctx.save(state=state)
            cands = rr.extract_candidates(answer) if answer else []
            valid = await asyncio.to_thread(rr.validate, cands, cfg.allowed_roots, ls_remote)
            if not valid:
                await ctx.event("repo_resolved", {"repo": None, "note": "proceeding without repo"})
                return ("continue", "req_design")
            record = valid[0].as_record()
        elif record is not None and not record.get("kind"):
            # explicit request field: must be valid, otherwise fail loudly
            cand = rr.from_field(record)
            valid = await asyncio.to_thread(rr.validate, [cand], cfg.allowed_roots, ls_remote)
            if not valid:
                raise PhaseError("; ".join(cand.errors) or "invalid repo", code="invalid_repo")
            record = cand.as_record()
        elif record is None:
            cands = rr.extract_candidates(ctx.job.prompt)
            valid = await asyncio.to_thread(rr.validate, cands, cfg.allowed_roots, ls_remote)
            if len(valid) == 1:
                record = valid[0].as_record()
            elif len(valid) > 1 or (not valid and (cands or rr.mentions_repo(ctx.job.prompt))):
                # ambiguous: ask the caller once (default: proceed without repo)
                listed = ", ".join(c.url or c.path or "" for c in (valid or cands)) or "-"
                state["repo_question_pending"] = True
                state["resume_phase"] = "repo_resolve"
                await ctx.save(state=state)
                await ctx.event("repo_ambiguous", {
                    "candidates": [c.as_record() | {"errors": c.errors} for c in cands]})
                ttl = ctx.options.get("question_ttl_s", ctx.config.question_ttl_s)
                import datetime as dt

                return ("gate", "questions", {
                    "questions": [{
                        "id": "Q-00",
                        "text": "Which existing repository should this work build on? "
                                "Reply with a git URL or an absolute path, or 'none'.",
                        "why": f"The request mentions a codebase. Candidates found: {listed}",
                        "kind": "free_text",
                        "default_answer": "none",
                        "default_rationale": "Proceed without a repository.",
                    }],
                    "questions_expire_at": (
                        dt.datetime.now(dt.UTC) + dt.timedelta(seconds=int(ttl))
                    ).isoformat(),
                    "event_type": "questions_asked",
                })
            else:
                await ctx.event("repo_resolved", {"repo": None, "note": "no repo found"})
                return ("continue", "req_design")

        # fetch into data/jobs/<id>/repo (read-only copy; nothing is executed)
        dest = ctx.workspace.repo
        try:
            if record["kind"] == "git":
                cand = rr.Candidate("git", record["source"], url=record["url"],
                                    ref=record.get("ref"))
                info = await asyncio.to_thread(repo_fetch.clone, cand, dest, cfg.max_mb)
            elif cfg.path_mode == "snapshot":
                info = await asyncio.to_thread(
                    repo_fetch.snapshot, Path(record["path"]), dest, cfg.max_mb)
            else:
                info = {}
        except repo_fetch.FetchError as exc:
            raise PhaseError(str(exc), code="invalid_repo") from exc
        record.update({k: v for k, v in info.items() if k == "commit_sha" and v})
        record["scan_root"] = (
            str(dest) if record["kind"] == "git" or cfg.path_mode == "snapshot"
            else record["path"]
        )
        await ctx.save(repo=json.dumps(record), phase="repo_scan", status="running")
        await ctx.event("repo_resolved", {"repo": record, "scan": True})
        return ("continue", "repo_scan")

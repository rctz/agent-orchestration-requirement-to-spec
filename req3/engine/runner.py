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
    ):
        from .phases import requirement  # local import keeps module load light

        self._requirement = requirement
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
                await ctx.save(
                    status="failed",
                    error={"code": exc.code, "message": str(exc), "phase": phase},
                )
                await ctx.event(
                    "job_failed", {"phase": phase, "code": exc.code, "message": str(exc)}
                )
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
                return
            if kind == "done":
                _, status, payload = action
                await ctx.save(status=status, phase="done", gate=None, **payload)
                await ctx.event("job_completed", {"status": status})
                return
            raise PhaseError(f"unknown action {kind!r}", code="engine_error")

    async def _dispatch(self, ctx: JobContext, phase: str):
        if phase == "repo_resolve":
            return await self._repo_resolve(ctx)
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
        """Design §10 / §2A.5 — local_path repos scan; git_url is refused."""
        if ctx.job.repo:
            repo = json.loads(ctx.job.repo)
            if repo.get("git_url"):
                raise PhaseError(
                    "git_url repos are not supported yet (local path only for now)",
                    code="phase_unavailable",
                )
            # validate early so failures surface as job_failed, not later
            from .phases.repo import resolve_repo_root

            resolve_repo_root(repo.get("path", ""), ctx.config.repo.allowed_roots)
            await ctx.save(phase="repo_scan", status="running")
            await ctx.event("repo_resolved", {"repo": repo, "scan": True})
            from .phases.repo import repo_scan

            return await repo_scan(ctx)
        await ctx.event("repo_resolved", {"repo": None, "note": "no repo in request"})
        return ("continue", "req_design")


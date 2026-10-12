"""REST API v1 (design §9): jobs lifecycle surface for M1.

M1 scope: create (queued only — no engine yet), get, list, cancel,
OpenAPI document. Answers/revise/events/artifacts routes land with the
engine milestones (M4+).
"""
from __future__ import annotations

import json
import time
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..engine.machine import TERMINAL_STATUS_VALUES, JobStatus
from ..store.db import (
    IntegrityError,
    JobRecord,
    json_or_none,
    new_job_id,
    utcnow,
)
from ..store.workspace import Workspace
from .auth import require_api_key
from .errors import ApiError

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


# ---- request models -------------------------------------------------------


class RepoSpec(BaseModel):
    """repo: {"git_url": ..., "ref": ...} | {"path": "/abs/path"} (design §10)."""

    model_config = ConfigDict(extra="forbid")
    git_url: str | None = None
    ref: str | None = None
    path: str | None = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> RepoSpec:
        if bool(self.git_url) == bool(self.path):
            raise ValueError("repo needs exactly one of git_url or path")
        if self.ref and not self.git_url:
            raise ValueError("repo.ref requires repo.git_url")
        if self.path and not self.path.startswith("/"):
            raise ValueError("repo.path must be absolute")
        return self


class JobOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size: Literal["S", "M", "L"] | None = None
    question_ttl_s: int | None = Field(default=None, gt=0)
    user_language: str | None = None
    project_name: str | None = None


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    output_profile: str | dict[str, Any] | None = None
    repo: RepoSpec | None = None
    callback_url: str | None = Field(default=None, pattern=r"^https?://")
    options: JobOptions | None = None


# ---- response helpers -----------------------------------------------------


def _loads(text: str | None, default: Any) -> Any:
    if text is None:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def job_status_body(rec: JobRecord) -> dict[str, Any]:
    """Stable job status contract (design §9 'Job status shape')."""
    return {
        "job_id": rec.job_id,
        "project": rec.project,
        "status": rec.status,
        "phase": rec.phase,
        "gate": rec.gate,
        "round": _loads(rec.round, {}),
        "questions": _loads(rec.questions, []),
        "questions_expire_at": rec.questions_expire_at,
        "requirements_preview": _loads(rec.requirements_preview, None),
        "versions": _loads(rec.versions, {}),
        "known_issues": _loads(rec.known_issues, []),
        "error": _loads(rec.error, None),
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }


def created_body(rec: JobRecord) -> dict[str, Any]:
    return {
        "job_id": rec.job_id,
        "status": rec.status,
        "links": {
            "self": f"/v1/jobs/{rec.job_id}",
            "events": f"/v1/jobs/{rec.job_id}/events",
            "answers": f"/v1/jobs/{rec.job_id}/answers",
            "cancel": f"/v1/jobs/{rec.job_id}/cancel",
            "artifacts": f"/v1/jobs/{rec.job_id}/artifacts",
        },
    }


async def _get_job_or_404(request: Request, job_id: str) -> JobRecord:
    rec = await request.app.state.db.get_job(job_id)
    if rec is None:
        raise ApiError(404, "not_found", f"unknown job: {job_id}")
    return rec


async def _ensure_executor_healthy(request: Request) -> None:
    """Refuse new jobs when the executor is down/misconfigured (design §10).

    Health is cached for 30s so create stays cheap.
    """
    cache = getattr(request.app.state, "health_cache", None)
    now = time.time()
    if cache is not None and now - cache[0] < 30:
        if not cache[1].ok:
            raise ApiError(503, "executor_unavailable", cache[1].detail)
        return
    report = await request.app.state.executor.health()
    request.app.state.health_cache = (now, report)
    if not report.ok:
        raise ApiError(503, "executor_unavailable", report.detail)


# ---- routes ---------------------------------------------------------------


@router.post("/jobs", status_code=202)
async def create_job(body: CreateJobRequest, request: Request) -> dict[str, Any]:
    await _ensure_executor_healthy(request)
    db = request.app.state.db
    idem = request.headers.get("idempotency-key")
    if idem:
        existing = await db.get_job_by_idempotency_key(idem)
        if existing is not None:
            return created_body(existing)  # idempotent replay
    options = body.options.model_dump(exclude_none=True) if body.options else None
    repo = body.repo.model_dump(exclude_none=True) if body.repo else None
    profile = (
        body.output_profile
        if isinstance(body.output_profile, str)
        else json_or_none(body.output_profile)
    )
    rec = None
    for _ in range(5):
        candidate = JobRecord(
            job_id=new_job_id(),
            status=JobStatus.QUEUED.value,
            prompt=body.prompt,
            created_at=utcnow(),
            updated_at=utcnow(),
            idempotency_key=idem,
            project=(body.options.project_name if body.options else None),
            output_profile=profile,
            repo=json_or_none(repo),
            callback_url=body.callback_url,
            options=json_or_none(options),
        )
        try:
            await db.create_job(candidate)
            rec = candidate
            break
        except IntegrityError:
            if idem:
                existing = await db.get_job_by_idempotency_key(idem)
                if existing is not None:
                    return created_body(existing)  # lost a race: replay
    if rec is None:
        raise ApiError(500, "internal_error", "could not allocate a unique job id")
    workspace = Workspace(request.app.state.workspace_root, rec.job_id)
    workspace.create(prompt=body.prompt, options=options, profile=body.output_profile)
    await db.append_event(
        rec.job_id, "job_created", {"status": "queued", "idempotent": bool(idem)}
    )
    return created_body(rec)


@router.get("/jobs")
async def list_jobs(
    request: Request,
    status: JobStatus | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    rows, total = await request.app.state.db.list_jobs(
        status.value if status else None, limit, offset
    )
    return {
        "jobs": [job_status_body(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> dict[str, Any]:
    rec = await _get_job_or_404(request, job_id)
    return job_status_body(rec)


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request) -> dict[str, Any]:
    rec = await _get_job_or_404(request, job_id)
    if rec.status in TERMINAL_STATUS_VALUES:
        raise ApiError(409, "invalid_state", f"job already terminal: {rec.status}")
    if not await request.app.state.db.cancel_job(job_id):
        raise ApiError(409, "invalid_state", "job reached a terminal state")
    await request.app.state.db.append_event(
        job_id, "job_cancelled", {"from": rec.status}
    )
    updated = await _get_job_or_404(request, job_id)
    return job_status_body(updated)


@router.get("/openapi.json", include_in_schema=False)
async def openapi_document(request: Request) -> dict[str, Any]:
    """Serve the OpenAPI doc at /v1/openapi.json (design §9)."""
    return request.app.openapi()

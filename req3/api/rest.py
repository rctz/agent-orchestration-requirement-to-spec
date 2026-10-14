"""REST API v1 (design §9): jobs lifecycle surface.

M4: create (auto-submitted to the engine when active), get, list, cancel,
answers (questions gate + confirm gate), OpenAPI document.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response as FastAPIResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..engine.machine import TERMINAL_STATUS_VALUES, JobStatus
from ..engine.phases.requirement import record_gate_decisions
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
    # v2 compatibility: format selector v2 clients send; resolved to
    # output_profile at create time (never passed through to agents).
    output_format: str | None = None


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    output_profile: str | dict[str, Any] | None = None
    repo: RepoSpec | None = None
    callback_url: str | None = Field(default=None, pattern=r"^https?://")
    options: JobOptions | None = None


class ReviseRequest(BaseModel):
    """POST /v1/jobs/{id}/revise (design §3, D8; plan M6)."""

    model_config = ConfigDict(extra="forbid")

    text: str


class AnswerRequest(BaseModel):
    """POST /v1/jobs/{id}/answers (design §9)."""

    model_config = ConfigDict(extra="forbid")

    answers: dict[str, str] | None = None  # gate=questions: {Q-01: "..."}
    apply_defaults: bool = False  # apply default_answer to unanswered now
    action: Literal["confirm", "change_request"] | None = None
    text: str | None = None  # required with action=change_request


_THAI_SCRIPT = re.compile(r"[\u0e00-\u0e7f]")


def detect_language(prompt: str) -> str:
    return "th" if _THAI_SCRIPT.search(prompt) else "en"


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


def _builtin_profile_names() -> list[str]:
    from ..paths import PROFILES_DIR

    return sorted(
        p.parent.name
        for p in (PROFILES_DIR / "builtin").glob("*/profile.json")
    )


#: v2 compatibility aliases (design §9 A2A: v2 clients work unchanged).
#: v2 selected formats via options.output_format with these names; req3's
#: `men` profile emits BOTH men-spi and men-plan files in one bundle.
V2_PROFILE_ALIASES = {"men-spi": "men", "men-plan": "men", "canonical": "json"}


async def _resolve_profile_name(request: Request, name: str) -> str:
    """Builtin names pass through; registered names resolve to their
    stored definition (JSON text, re-parsed at render time); anything
    else is a fail-fast 422 (design §8/§9)."""
    if name in ("", "default") or name in _builtin_profile_names():
        return name
    registered = await request.app.state.db.get_profile(name)
    if registered is None:
        raise ApiError(
            422,
            "invalid_profile",
            f"unknown output_profile {name!r} — builtin: "
            f"{', '.join(_builtin_profile_names())}; register via "
            "POST /v1/output-profiles",
        )
    return json.dumps(registered, ensure_ascii=False)


class ProfileRegistration(BaseModel):
    definition: dict[str, Any]


@router.get("/output-profiles")
async def list_output_profiles(request: Request) -> dict[str, Any]:
    """Builtin profile names + registered custom profile definitions."""
    registered = await request.app.state.db.list_profiles()
    return {"builtin": _builtin_profile_names(), "registered": registered}


@router.post("/output-profiles", status_code=201)
async def register_output_profile(
    body: ProfileRegistration, request: Request
) -> dict[str, Any]:
    """Register a custom output profile by name (design §8)."""
    from ..render.renderer import validate_profile

    errors = validate_profile(body.definition)
    if errors:
        raise ApiError(422, "invalid_profile", "; ".join(errors))
    name = body.definition["name"]
    if name in _builtin_profile_names():
        raise ApiError(409, "invalid_profile", f"{name!r} is a builtin profile")
    await request.app.state.db.save_profile(name, body.definition)
    return {
        "name": name,
        "registered": True,
        "files": [f["path"] for f in body.definition["files"]],
    }


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
    options = dict(options or {})
    options.setdefault("user_language", detect_language(body.prompt))
    repo = body.repo.model_dump(exclude_none=True) if body.repo else None
    profile = (
        body.output_profile
        if isinstance(body.output_profile, str)
        else json_or_none(body.output_profile)
    )
    if isinstance(profile, str):
        profile = await _resolve_profile_name(request, profile)
    if profile is None:
        # v2 compat: options.output_format picks the profile (v2 default
        # was "men"). Consumed here so it does not linger in options.
        fmt = options.pop("output_format", None)
        if isinstance(fmt, str) and fmt:
            profile = await _resolve_profile_name(
                request, V2_PROFILE_ALIASES.get(fmt, fmt)
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
    engine = getattr(request.app.state, "engine", None)
    if engine is not None:
        engine.submit(rec.job_id)
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


@router.post("/jobs/{job_id}/revise")
async def request_revise(
    job_id: str, body: ReviseRequest, request: Request
) -> dict[str, Any]:
    """Post-completion change request (design §3, D8; plan M6)."""
    db = request.app.state.db
    rec = await _get_job_or_404(request, job_id)
    if rec.status not in ("completed", "completed_with_issues"):
        raise ApiError(
            409, "invalid_state", f"revise requires a completed job (got {rec.status!r})"
        )
    text = (body.text or "").strip()
    if not text:
        raise ApiError(422, "invalid_request", "text is required")
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise ApiError(503, "engine_unavailable", "engine is not active")
    state: dict[str, Any] = json.loads(rec.engine_state or "{}")
    state["change_request"] = text
    state["revise_count"] = state.get("revise_count", 0) + 1
    await db.update_job(
        job_id,
        status="running",
        phase="revise_analyze",
        gate=None,
        questions="[]",
        questions_expire_at=None,
        error=None,
        engine_state=json.dumps(state, ensure_ascii=False),
    )
    await db.append_event(
        job_id, "revise_requested", {"text": text[:300], "n": state["revise_count"]}
    )
    engine.submit(job_id)
    updated = await _get_job_or_404(request, job_id)
    return job_status_body(updated)


@router.post("/jobs/{job_id}/answers")
async def submit_answers(
    job_id: str, body: AnswerRequest, request: Request
) -> dict[str, Any]:
    """Answer questions / confirm / request changes (design §9)."""
    db = request.app.state.db
    rec = await _get_job_or_404(request, job_id)
    if rec.status != "input_required":
        raise ApiError(
            409, "invalid_state", f"job is {rec.status!r}, not input_required"
        )
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise ApiError(503, "engine_unavailable", "engine is not active")

    if rec.gate == "questions":
        questions = json.loads(rec.questions or "[]")
        state: dict[str, Any] = json.loads(rec.engine_state or "{}")
        answers = body.answers or {}
        valid_ids = {q["id"] for q in questions if "id" in q}
        unknown = sorted(set(answers) - valid_ids)
        if unknown:
            raise ApiError(422, "invalid_request", f"unknown question ids: {unknown}")
        if not answers and not body.apply_defaults:
            raise ApiError(422, "invalid_request", "no answers supplied")
        state.setdefault("answers", {}).update(answers)
        answered: dict[str, str] = state["answers"]
        all_answered = all(q["id"] in answered for q in questions)
        if not (body.apply_defaults or all_answered):
            # partial answers: record and keep waiting (design §5)
            await db.update_job(
                job_id, engine_state=json.dumps(state, ensure_ascii=False)
            )
            await db.append_event(
                job_id, "questions_answered", {"answers": sorted(answers)}
            )
            updated = await _get_job_or_404(request, job_id)
            return job_status_body(updated)
        unanswered = [q for q in questions if q["id"] not in answered]
        workspace = Workspace(request.app.state.workspace_root, job_id)
        entries = record_gate_decisions(
            workspace.root, answered, unanswered,
            defaults_source=("defaults_accepted" if body.apply_defaults
                             else "system_default_expired"),
        )
        state.setdefault("decision_log", []).extend(entries)
        await db.update_job(
            job_id,
            status="running",
            phase=state.get("resume_phase", "req_design"),
            gate=None,
            questions="[]",
            questions_expire_at=None,
            engine_state=json.dumps(state, ensure_ascii=False),
        )
        await db.append_event(
            job_id,
            "questions_answered",
            {
                "answers": sorted(answers),
                "defaults_applied": [q["id"] for q in unanswered],
            },
        )
        engine.submit(job_id)
        updated = await _get_job_or_404(request, job_id)
        return job_status_body(updated)

    if rec.gate == "confirm_requirements":
        if body.action == "confirm":
            await db.update_job(
                job_id,
                status="running",
                phase="spec_design",
                gate=None,
                questions_expire_at=None,
            )
            await db.append_event(job_id, "requirements_confirmed", {})
            engine.submit(job_id)
        elif body.action == "change_request":
            if not body.text:
                raise ApiError(422, "invalid_request", "change_request requires text")
            state = json.loads(rec.engine_state or "{}")
            state["change_request"] = body.text
            state["req_mode"] = "design"
            await db.update_job(
                job_id,
                status="running",
                phase="req_design",
                gate=None,
                questions_expire_at=None,
                engine_state=json.dumps(state, ensure_ascii=False),
            )
            await db.append_event(
                job_id, "change_request", {"text": body.text[:200]}
            )
            engine.submit(job_id)
        else:
            raise ApiError(
                422,
                "invalid_request",
                "confirm gate expects {action: confirm|change_request}",
            )
        updated = await _get_job_or_404(request, job_id)
        return job_status_body(updated)

    raise ApiError(409, "invalid_state", f"unknown gate {rec.gate!r}")


@router.get("/jobs/{job_id}/artifacts")
async def list_artifacts(
    job_id: str, request: Request, version: int | None = None
) -> dict[str, Any]:
    """Manifest + file list of rendered artifacts (?version=N)."""
    rec = await _get_job_or_404(request, job_id)
    versions = json.loads(rec.versions or "{}")
    spec_version = version or versions.get("spec", 0)
    out_dir = Path(request.app.state.workspace_root) / job_id / "out" / f"v{spec_version}"
    if not out_dir.is_dir():
        raise ApiError(404, "not_found", f"no artifacts for version {spec_version}")
    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else None
    files = sorted(
        str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file()
    )
    return {"job_id": job_id, "version": spec_version, "manifest": manifest, "files": files}


@router.get("/jobs/{job_id}/artifacts/{path:path}")
async def get_artifact(
    job_id: str, path: str, request: Request, version: int | None = None
) -> FastAPIResponse:
    """One rendered artifact file (?version=N)."""
    await _get_job_or_404(request, job_id)
    versions = json.loads((await request.app.state.db.get_job(job_id)).versions or "{}")
    spec_version = version or versions.get("spec", 0)
    out_dir = (Path(request.app.state.workspace_root) / job_id / "out" / f"v{spec_version}").resolve()
    target = (out_dir / path).resolve()
    if not str(target).startswith(str(out_dir)) or not target.is_file():
        raise ApiError(404, "not_found", f"no artifact: {path}")
    media = "application/json" if target.suffix == ".json" else "text/markdown"
    return FastAPIResponse(content=target.read_bytes(), media_type=media)


@router.get("/jobs/{job_id}/artifacts.zip")
async def get_artifacts_zip(
    job_id: str, request: Request, version: int | None = None
) -> FastAPIResponse:
    """Bundle all rendered artifacts of a version."""
    import io
    import zipfile

    await _get_job_or_404(request, job_id)
    versions = json.loads((await request.app.state.db.get_job(job_id)).versions or "{}")
    spec_version = version or versions.get("spec", 0)
    out_dir = Path(request.app.state.workspace_root) / job_id / "out" / f"v{spec_version}"
    if not out_dir.is_dir():
        raise ApiError(404, "not_found", f"no artifacts for version {spec_version}")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        for file in sorted(p for p in out_dir.rglob("*") if p.is_file()):
            bundle.write(file, arcname=str(file.relative_to(out_dir)))
    return FastAPIResponse(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{job_id}-v{spec_version}.zip"'},
    )


@router.get("/openapi.json", include_in_schema=False)
async def openapi_document(request: Request) -> dict[str, Any]:
    """Serve the OpenAPI doc at /v1/openapi.json (design §9)."""
    return request.app.openapi()

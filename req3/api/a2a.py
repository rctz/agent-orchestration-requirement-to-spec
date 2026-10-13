"""A2A adapter (design §9, D14): JSON-RPC `/a2a` + agent card, mapped onto
the REST v1 handlers. Ports v2's parse_parts/message shapes so existing v2
clients work unchanged (message/send, tasks/get, tasks/cancel; the APPROVE /
REJECT: text convention on the confirm gate)."""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from . import rest
from .auth import require_api_key as require_auth
from .errors import ApiError

# v2-compatible aliases
SEND_ALIASES = {"message/send", "SendMessage", "send_message", "message/sendAsync"}
GET_ALIASES = {"tasks/get", "GetTask", "get_task"}
CANCEL_ALIASES = {"tasks/cancel", "CancelTask", "cancel_task"}

STATE_MAP = {
    "queued": "submitted",
    "running": "working",
    "input_required": "input-required",
    "completed": "completed",
    "completed_with_issues": "completed",
    "failed": "failed",
}


# ------------------------------------------------------------ v2 part helpers
def parse_parts(message: dict) -> tuple[str, dict, list]:
    """v2-compatible: return (text, data, files) from a message's parts."""
    text_parts: list[str] = []
    options: dict[str, Any] = {}
    files: list[dict] = []
    for p in message.get("parts", []):
        kind = p.get("kind") or (
            "data" if "data" in p
            else "text" if "text" in p
            else "file" if "file" in p
            else "?"
        )
        if kind == "text" and p.get("text"):
            text_parts.append(str(p["text"]))
        elif kind == "data" and isinstance(p.get("data"), dict):
            options.update(p["data"])
        elif kind == "file" and isinstance(p.get("file"), dict):
            files.append(p["file"])
    return "\n".join(text_parts).strip(), options, files


def tx(s: str) -> dict:
    return {"kind": "text", "text": s}


def dt(d: dict) -> dict:
    return {"kind": "data", "data": d}


def agent_msg(parts: list) -> dict:
    return {"role": "agent", "parts": parts}


AGENT_CARD = {
    "name": "req3",
    "description": "Requirements & spec service: prompt -> clarifying "
    "questions -> confirmed requirements -> reviewed spec, delivered as "
    "versioned artifacts.",
    "version": "1.0.0",
    "capabilities": {"streaming": False, "pushNotifications": True},
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "skills": [
        {
            "id": "requirements-and-spec",
            "name": "Requirements & spec authoring",
            "description": "Send a project prompt; answer clarifying questions; "
            "APPROVE the requirements; receive spec artifacts.",
        }
    ],
}


async def agent_card(request: Request) -> dict:
    card = dict(AGENT_CARD)
    base = str(request.base_url).rstrip("/")
    card["url"] = f"{base}/a2a"
    return card


def _task_from_job(job: dict[str, Any], base_url: str) -> dict:
    state = STATE_MAP.get(job["status"], "working")
    base = {"id": job["job_id"], "contextId": job["job_id"], "kind": "task"}
    if state == "input-required":
        if job.get("gate") == "confirm_requirements":
            parts = [
                tx("Requirements are ready for review. Reply APPROVE to "
                   "continue, or REJECT: <reason> to send them back."),
                dt({
                    "phase": job.get("phase"),
                    "gate": "confirm_requirements",
                    "requirements_preview": job.get("requirements_preview"),
                    "versions": job.get("versions"),
                }),
            ]
        else:
            parts = [
                tx("Clarifying questions (reply with answers):"),
                dt({
                    "phase": job.get("phase"),
                    "gate": "questions",
                    "questions": job.get("questions") or [],
                    "questions_expire_at": job.get("questions_expire_at"),
                }),
            ]
        return {**base, "status": {"state": state, "message": agent_msg(parts)}}
    if state == "failed":
        err = job.get("error") or {}
        return {
            **base,
            "status": {
                "state": "failed",
                "message": agent_msg([
                    tx(f"Job failed at {err.get('phase', '?')}: "
                       f"[{err.get('code', '?')}] {err.get('message', '')}")
                ]),
            },
        }
    if state == "completed":
        links = {
            name: f"{base_url}/v1/jobs/{job['job_id']}/artifacts/{name}"
            for name in ("requirement.md", "spec.md", "manifest.json")
        }
        return {
            **base,
            "status": {
                "state": "completed",
                "message": agent_msg([
                    tx(f"Job {job['status']}: requirements "
                       f"v{job['versions']['requirements']}, spec "
                       f"v{job['versions'].get('spec', 0)} delivered."),
                    dt({
                        "status": job["status"],
                        "versions": job.get("versions"),
                        "known_issues": job.get("known_issues") or [],
                        "artifacts": links,
                    }),
                ]),
            },
        }
    return {
        **base,
        "status": {
            "state": state,
            "message": agent_msg([tx(f"Working: phase {job.get('phase', '?')}.")]),
        },
    }


async def _map_answer(text: str, data: dict, job: dict) -> dict:
    """v2 conventions -> req3 answers body (or a revise marker)."""
    if isinstance(data.get("answers"), dict):
        return {"answers": data["answers"]}
    action = data.get("action")
    if action == "confirm":
        return {"action": "confirm"}
    if action == "change_request":
        return {"action": "change_request", "text": data.get("text") or text}
    if action == "revise":
        return {"__revise__": True, "text": data.get("text") or text}
    upper = text.strip().upper()
    if upper == "APPROVE":
        return {"action": "confirm"}
    if upper.startswith("REJECT"):
        reason = text.strip()[6:].lstrip(": ").strip() or "rejected by user"
        return {"action": "change_request", "text": reason}
    if data.get("apply_defaults"):
        return {"apply_defaults": True}
    if text:
        return {"__revise__": True, "text": text}
    raise ApiError(422, "invalid_request", "cannot interpret message as an answer")


async def a2a(request: Request) -> JSONResponse:
    """POST /a2a — JSON-RPC 2.0 (v2-compatible method aliases)."""
    await require_auth(request)
    body = await request.json()
    req_id = body.get("id")
    method = str(body.get("method", ""))
    params = body.get("params") or {}
    base_url = str(request.base_url).rstrip("/")

    try:
        if method in SEND_ALIASES:
            message = params.get("message") or {}
            text, data, _files = parse_parts(message)
            task_id = (
                message.get("taskId") or params.get("taskId") or data.get("task_id")
            )
            if not task_id:
                if not text:
                    raise ApiError(422, "invalid_request",
                                   "message/send needs text for a new job")
                payload: dict[str, Any] = {"prompt": text}
                if isinstance(data.get("options"), dict):
                    # v2/contract wire shape: the data part carries an
                    # "options" object (output_format, project_name, ...).
                    # It maps to CreateJobRequest.options (JobOptions) —
                    # flattening it onto the top level 500s because
                    # CreateJobRequest is extra="forbid".
                    payload["options"] = data["options"]
                if isinstance(data.get("repo"), dict):
                    payload["repo"] = data["repo"]
                if data.get("callback_url"):
                    payload["callback_url"] = data["callback_url"]
                created = await rest.create_job(
                    rest.CreateJobRequest(**payload), request
                )
                job = await rest.get_job(created["job_id"], request)
                return _rpc_ok(req_id, _task_from_job(job, base_url))

            job = await rest.get_job(task_id, request)
            answer = await _map_answer(text, data, job)
            if answer.get("__revise__"):
                out = await rest.request_revise(
                    task_id, rest.ReviseRequest(text=answer["text"]), request
                )
            else:
                out = await rest.submit_answers(
                    task_id, rest.AnswerRequest(**answer), request
                )
            return _rpc_ok(req_id, _task_from_job(out, base_url))

        if method in GET_ALIASES:
            task_id = params.get("id") or (params.get("message") or {}).get("taskId")
            if not task_id:
                raise ApiError(422, "invalid_request", "tasks/get needs id")
            job = await rest.get_job(task_id, request)
            return _rpc_ok(req_id, _task_from_job(job, base_url))

        if method in CANCEL_ALIASES:
            task_id = params.get("id")
            if not task_id:
                raise ApiError(422, "invalid_request", "tasks/cancel needs id")
            out = await rest.cancel_job(task_id, request)
            return _rpc_ok(req_id, _task_from_job(out, base_url))

        return _rpc_err(req_id, -32601, f"method not supported: {method}")
    except ApiError as exc:
        return _rpc_err(req_id, -32000, f"{exc.code}: {exc.message}")


def _rpc_ok(req_id, result) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def _rpc_err(req_id, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )

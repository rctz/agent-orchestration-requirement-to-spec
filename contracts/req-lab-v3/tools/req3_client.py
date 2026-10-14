#!/usr/bin/env python3
"""req3_client — stdlib-only caller client for the req3 Requirement & Spec
service (contract pack). Commands: info / start / status /
answer / approve / reject / wait / download / cancel.

Usage:  python3 req3_client.py [--url URL] [--api-key KEY] <command> ...
Env:    REQ3_URL (default https://req3.rctz.online), REQ3_API_KEY
Auth:   X-API-Key header (also accepted: Authorization: Bearer).
Long-running: minutes. `wait` polls until a gate or terminal state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("REQ3_URL", "https://req3.rctz.online")


def _api_key() -> str:
    key = os.environ.get("REQ3_API_KEY", "")
    if not key:
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("API_KEY.txt", "../API_KEY.txt"):
            path = os.path.join(here, name)
            if os.path.isfile(path):
                key = open(path).read().strip()
                break
    if not key:
        sys.exit("error: no API key (env REQ3_API_KEY or API_KEY.txt beside this file)")
    return key


def call(base: str, method: str, path: str, body: dict | None = None,
         raw: bool = False, timeout: int = 60):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "X-API-Key": _api_key(),
            "Content-Type": "application/json",
            "User-Agent": "req3-client/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return resp.status, (data if raw else (json.loads(data) if data else {}))
    except urllib.error.HTTPError as exc:
        payload = exc.read()[:400]
        try:
            payload = json.loads(payload)
        except Exception:
            payload = payload.decode("utf-8", "replace")
        return exc.code, payload


# ---- A2A envelope ---------------------------------------------------------


def rpc(base: str, method: str, params: dict) -> tuple[int, dict]:
    status, body = call(base, "POST", "/a2a",
                        {"jsonrpc": "2.0", "id": 1, "method": method,
                         "params": params})
    if status != 200:
        sys.exit(f"gateway error ({status}): {body}")
    if body.get("error"):
        # JSON-RPC errors ride on HTTP 200 — surface them loudly; a silent
        # no-op here strands jobs at their gate (observed live).
        err = body["error"]
        sys.exit(f"req3 rejected the call: "
                 f"[{err.get('code')}] {err.get('message')}")
    result = body.get("result", {})
    if not isinstance(result, dict) or "id" not in result:
        sys.exit(f"unexpected reply from req3: {str(body)[:300]}")
    return status, result


def _fmt_task(task: dict) -> str:
    """Render a task so a human OR an agent can act on it: every gate shows
    the full questions / instructions, nothing important is truncated."""
    state = task.get("status", {}).get("state", "?")
    parts = task.get("status", {}).get("message", {}).get("parts", [])
    data = next((p.get("data", {}) for p in parts if p.get("kind") == "data"), {})
    out = f"task {task.get('id', '?')}: {state}"
    gate = data.get("gate")

    if state == "input-required" and gate == "questions":
        out += ("\n  ACTION REQUIRED: these are PRODUCT DECISIONS owned by the"
                "\n  requester. RELAY every question below to your user and"
                "\n  submit THEIR replies — do not invent answers yourself,"
                "\n  unless the user explicitly delegated the answers to you.")
        out += f"\n    req3_client.py answer {task.get('id', '<id>')} Q-01=\"user's reply\" Q-02=\"...\""
        qs = data.get("questions") or []
        for q in qs:
            out += f"\n  {q.get('id')} [{q.get('kind')}] {q.get('text', '')}"
            for opt in q.get("options") or []:
                out += f"\n      - {opt}"
            out += f"\n      default: {q.get('default_answer', '')}"
        if data.get("questions_expire_at"):
            out += ("\n  (unanswered questions expire at "
                    f"{data['questions_expire_at']}; the default is applied automatically)")
    elif state == "input-required" and gate == "confirm_requirements":
        prev = data.get("requirements_preview") or {}
        reqs = prev.get("requirements") or []
        out += ("\n  ACTION REQUIRED: the APPROVE/REJECT decision belongs to"
                "\n  YOUR USER, not to you. Show them the requirements"
                "\n  (command below prints the full draft), get their explicit"
                "\n  verdict, then submit it. If the gate expires unused, the"
                "\n  system auto-approves — so make sure the user really saw it.")
        out += f"\n    {len(reqs)} requirements, goal: {str(prev.get('goal', ''))[:200]}"
        out += f"\n    req3_client.py preview {task.get('id', '<id>')}   # full draft to show"
        out += f"\n  User says OK:      req3_client.py approve {task.get('id', '<id>')}"
        out += f"\n  User wants changes: req3_client.py reject {task.get('id', '<id>')} \"their reason\""
    elif state == "completed":
        out += "\n  DONE. Download the artifacts with:"
        out += f"\n    req3_client.py download {task.get('id', '<id>')} --out <dir>"
    elif state == "failed":
        err = data.get("error") or {}
        out += (f"\n  FAILED (phase {err.get('phase', '?')}): "
                f"[{err.get('code')}] {err.get('message', '')}")
    else:
        text = next((p.get("text", "") for p in parts if p.get("kind") == "text"), "")
        if text:
            out += f"\n  {text[:500]}"
        if data:
            out += f"\n  {json.dumps(data, ensure_ascii=False)[:500]}"
    return out


# ---- commands -------------------------------------------------------------


def cmd_info(a):
    status, card = call(a.url, "GET", "/.well-known/agent.json")
    if status != 200:
        sys.exit(f"gateway unreachable ({status}): {card}")
    print(json.dumps(card, indent=2, ensure_ascii=False))
    return 0


def cmd_start(a):
    data: dict = {"options": {"output_format": a.output_format}}
    if a.project:
        data["options"]["project_name"] = a.project
    if a.callback_url:
        data["options"]["callback_url"] = a.callback_url
    status, task = rpc(a.url, "message/send", {"message": {
        "role": "user",
        "parts": [
            {"kind": "text", "text": a.requirement},
            {"kind": "data", "data": data},
        ],
    }})
    if status != 200:
        sys.exit(f"start failed ({status}): {task}")
    print(_fmt_task(task))
    print("\ntrack with:  req3_client.py status", task["id"])
    return 0


def cmd_status(a):
    status, task = rpc(a.url, "tasks/get", {"id": a.task_id})
    if status != 200:
        sys.exit(f"status failed ({status}): {task}")
    print(_fmt_task(task))
    return 0


def cmd_answer(a):
    answers = dict(item.split("=", 1) for item in a.answers)
    data: dict = {"answers": answers}
    if getattr(a, "defaults", False):
        data["apply_defaults"] = True
    status, task = rpc(a.url, "message/send", {"message": {
        "role": "user", "taskId": a.task_id,
        "parts": [{"kind": "data", "data": data}],
    }})
    if status != 200:
        sys.exit(f"answer failed ({status}): {task}")
    print(_fmt_task(task))
    return 0


def cmd_approve(a):
    return _reply_text(a, "APPROVE")


def cmd_reject(a):
    return _reply_text(a, f"REJECT: {a.reason}")


def _reply_text(a, text):
    status, task = rpc(a.url, "message/send", {"message": {
        "role": "user", "taskId": a.task_id,
        "parts": [{"kind": "text", "text": text}],
    }})
    if status != 200:
        sys.exit(f"reply failed ({status}): {task}")
    print(_fmt_task(task))
    return 0


def cmd_wait(a):
    deadline = time.time() + a.timeout
    last = ""
    while time.time() < deadline:
        status, task = rpc(a.url, "tasks/get", {"id": a.task_id})
        state = task.get("status", {}).get("state", "?")
        if state != last:
            print(f"[{time.strftime('%H:%M:%S')}] {state}", flush=True)
            last = state
        if state in ("input-required", "completed", "failed"):
            print(_fmt_task(task))
            return 0
        time.sleep(a.poll)
    print("timeout waiting")
    return 1


def cmd_download(a):
    job = a.task_id
    status, listing = call(a.url, "GET", f"/v1/jobs/{job}/artifacts")
    if status != 200:
        sys.exit(f"artifacts failed ({status}): {listing}")
    out_dir = a.out or job
    os.makedirs(out_dir, exist_ok=True)
    for name in listing.get("files", []):
        code, content = call(a.url, "GET",
                             f"/v1/jobs/{job}/artifacts/{name}", raw=True)
        if code != 200:
            print(f"  SKIP {name} ({code})")
            continue
        path = os.path.join(out_dir, name.replace("/", os.sep))
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(content)
        print(f"  {path} ({len(content)} bytes)")
    return 0


def cmd_preview(a):
    status, task = rpc(a.url, "tasks/get", {"id": a.task_id})
    parts = task.get("status", {}).get("message", {}).get("parts", [])
    data = next((p.get("data", {}) for p in parts if p.get("kind") == "data"), {})
    prev = data.get("requirements_preview")
    if not prev:
        sys.exit(f"no requirements preview available (state must be the "
                 f"confirm gate); got gate={data.get('gate')!r}")
    print(f"PROJECT : {prev.get('project')}  (v{prev.get('version')}, "
          f"size {prev.get('size')})")
    print(f"GOAL    : {prev.get('goal')}")
    print(f"USERS   : {'; '.join(prev.get('users', []))}")
    scope = prev.get("scope") or {}
    print(f"IN SCOPE:")
    for i in scope.get("in", []):
        print(f"  + {i}")
    print(f"OUT OF SCOPE:")
    for o in scope.get("out", []):
        print(f"  - {o}")
    decs = prev.get("decisions") or []
    if decs:
        print("\nDECISIONS (from the user's answers):")
        for d in decs:
            print(f"  {d.get('id')} [{d.get('source')}] {str(d.get('answer'))[:160]}")
    print(f"\nREQUIREMENTS ({len(prev.get('requirements', []))}):")
    for r in prev.get("requirements", []):
        print(f"\n  {r.get('id')} [{r.get('priority', '?')}] {r.get('title')}")
        print(f"    {r.get('body')}")
        for i, ac in enumerate(r.get("acceptance", []) or [], 1):
            print(f"    AC-{i}: {ac}")
    ki = prev.get("known_issues") or []
    if ki:
        print("\nOPEN NOTES:")
        for k in ki:
            print(f"  ! {k}")
    return 0


DESCR = {
    "default": "requirement.md + spec.md (+ manifest.json) — markdown, best for humans/agents",
    "json": "requirements.json + spec.json — raw canonical JSON",
    "men": "orchestrator bundle: requirement.json + spec.md + plan.md + traceability.json",
}


def cmd_formats(a):
    status, body = call(a.url, "GET", "/v1/output-profiles")
    if status != 200:
        sys.exit(f"formats failed ({status}): {body}")
    print("output formats (pick one at start: --output-format NAME; fixed for the job):")
    for name in body.get("builtin", []):
        print(f"  {name:10s} {DESCR.get(name, 'builtin profile')}")
    for name in body.get("registered", []):
        print(f"  {name:10s} custom registered profile")
    if not body.get("registered"):
        print("  (no custom profiles registered)")
    return 0


def cmd_cancel(a):
    status, task = rpc(a.url, "tasks/cancel", {"id": a.task_id})
    if status != 200:
        sys.exit(f"cancel failed ({status}): {task}")
    print(_fmt_task(task))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--api-key", dest="api_key", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info").set_defaults(fn=cmd_info)

    sub.add_parser("formats").set_defaults(fn=cmd_formats)

    p = sub.add_parser("preview")
    p.add_argument("task_id")
    p.set_defaults(fn=cmd_preview)

    p = sub.add_parser("start")
    p.add_argument("requirement")
    p.add_argument("--output-format", default="men",
                   help="men (default) | default | json | registered name")
    p.add_argument("--project", default=None)
    p.add_argument("--callback-url", default=None,
                   help="webhook: req3 POSTs gate/completion events (HMAC-signed)")
    p.set_defaults(fn=cmd_start)

    p = sub.add_parser("status")
    p.add_argument("task_id")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("answer")
    p.add_argument("task_id")
    p.add_argument("answers", nargs="*", metavar="Q-ID=answer")
    p.add_argument("--defaults", action="store_true",
                   help="accept the default answer for every unanswered question")
    p.set_defaults(fn=cmd_answer)

    p = sub.add_parser("approve")
    p.add_argument("task_id")
    p.set_defaults(fn=cmd_approve)

    p = sub.add_parser("reject")
    p.add_argument("task_id")
    p.add_argument("reason")
    p.set_defaults(fn=cmd_reject)

    p = sub.add_parser("wait")
    p.add_argument("task_id")
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--poll", type=float, default=10)
    p.set_defaults(fn=cmd_wait)

    p = sub.add_parser("download")
    p.add_argument("task_id")
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_download)

    p = sub.add_parser("cancel")
    p.add_argument("task_id")
    p.set_defaults(fn=cmd_cancel)

    args = ap.parse_args()
    if args.api_key:
        os.environ["REQ3_API_KEY"] = args.api_key
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

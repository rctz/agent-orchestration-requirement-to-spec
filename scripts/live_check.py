#!/usr/bin/env python3
"""Live smoke test for a req3 deployment: submit a prompt, drive it to a
gate (or terminal), print a summary (questions, tokens per agent, wall
time, event tail). Stdlib only — runs anywhere.

Usage:
  live_check.py <base_url> <api_key_file> [--prompt-file F] [--prompt TEXT]
      [--answers-json '{"Q-01": "..."}'] [--confirm] [--timeout 900]
      [--job-id j_...] (resume polling an existing job)
The api key file is read once (never printed).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

TERMINAL = {"completed", "completed_with_issues", "failed", "cancelled"}


def request(base: str, key: str, method: str, path: str, body: dict | None = None,
            timeout: int = 60):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            return exc.code, {"error": raw[:200]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("api_key_file")
    parser.add_argument("--prompt-file")
    parser.add_argument("--prompt")
    parser.add_argument("--answers-json", default=None)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--job-id")
    parser.add_argument("--poll", type=float, default=2.0)
    args = parser.parse_args()

    key = open(args.api_key_file, encoding="utf-8").read().strip()
    started = time.monotonic()

    job_id = args.job_id
    if job_id is None:
        prompt = (
            open(args.prompt_file, encoding="utf-8").read()
            if args.prompt_file
            else args.prompt
        )
        assert prompt, "need --prompt or --prompt-file"
        status, body = request(
            args.base_url, key, "POST", "/v1/jobs", {"prompt": prompt}
        )
        print(f"create -> {status} {json.dumps(body)[:200]}")
        assert status == 202, body
        job_id = body["job_id"]

    gate_seen: dict[str, bool] = {}
    while True:
        status, body = request(args.base_url, key, "GET", f"/v1/jobs/{job_id}")
        assert status == 200, body
        marker = f"[{round(time.monotonic() - started):>4}s] {body['status']}"
        if body.get("phase"):
            marker += f"/{body['phase']}"
        if body.get("gate"):
            marker += f"/{body['gate']}"
        print(marker, flush=True)
        if body["status"] in TERMINAL:
            print("final error:", json.dumps(body.get("error")))
            break
        if body["status"] == "input_required":
            gate = body["gate"]
            if gate == "questions" and args.answers_json is not None and not gate_seen.get("answered"):
                gate_seen["answered"] = True
                answers = json.loads(args.answers_json)
                print("answering:", json.dumps(answers), flush=True)
                status, reply = request(
                    args.base_url, key, "POST",
                    f"/v1/jobs/{job_id}/answers", {"answers": answers},
                )
                print(f"answers -> {status}", flush=True)
            elif gate == "confirm_requirements" and args.confirm and not gate_seen.get("confirmed"):
                gate_seen["confirmed"] = True
                status, reply = request(
                    args.base_url, key, "POST",
                    f"/v1/jobs/{job_id}/answers", {"action": "confirm"},
                )
                print(f"confirm -> {status}", flush=True)
            elif not gate_seen.get(gate):
                gate_seen[gate] = True
                if gate == "questions":
                    print("questions:", json.dumps(body.get("questions"), indent=1)[:1500], flush=True)
        if time.monotonic() - started > args.timeout:
            print("TIMEOUT waiting for job to finish")
            return 2
        time.sleep(args.poll)

    status, events = request(
        args.base_url, key, "GET",
        f"/v1/jobs/{job_id}/events?format=json",
    )
    types = [e["type"] for e in events["events"]]
    tokens = {}
    for event in events["events"]:
        if event["type"] == "agent_completed":
            agent = event["data"].get("agent")
            tokens[agent] = tokens.get(agent, 0) + (event["data"].get("tokens") or 0)
    print("\n== summary ==")
    print("job:", job_id)
    print("wall (incl. polling):", round(time.monotonic() - started, 1), "s")
    print("tokens per agent:", json.dumps(tokens))
    print("rounds:", json.dumps(body.get("round")))
    print("known_issues:", json.dumps(body.get("known_issues"))[:400])
    print("events:", " ".join(types))
    return 0


if __name__ == "__main__":
    sys.exit(main())

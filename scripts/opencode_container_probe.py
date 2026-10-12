#!/usr/bin/env python3
"""Standalone probe: one structured call against an opencode server.

Used to prove the Dockerized opencode works from another container on the
same network (plan M2). Stdlib only — runs in python:*-slim.

Usage: python3 opencode_container_probe.py <base_url>
Reads OPENCODE_SERVER_PASSWORD (and OPENCODE_SERVER_USERNAME, default
"opencode") from the environment.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request


def main() -> None:
    base_url = sys.argv[1].rstrip("/")
    username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
    password = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
    auth = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()

    def req(method: str, path: str, body: dict | None = None, timeout: int = 300):
        request = urllib.request.Request(
            base_url + path,
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json", "Authorization": auth},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode()
            return json.loads(text) if text.strip() else None

    agents = req("GET", "/agent")
    names = sorted(a["name"] for a in agents)
    print("agents:", names)
    assert "req-designer" in names, "req-designer agent missing (config not loaded?)"

    session = req("POST", "/session", {"title": "container-probe"})
    session_id = session["id"]
    schema = {
        "type": "object",
        "properties": {"reply": {"type": "string"}, "n": {"type": "integer"}},
        "required": ["reply", "n"],
        "additionalProperties": False,
    }
    started = time.time()
    message = req(
        "POST",
        f"/session/{session_id}/message",
        {
            "agent": "req-designer",
            "parts": [{
                "type": "text",
                "text": "Say hello and give n=99. Container probe nonce C1.",
            }],
            "format": {"type": "json_schema", "schema": schema},
        },
    )
    info = message.get("info", {})
    print("structured:", json.dumps(info.get("structured")))
    print("model:", info.get("modelID"), "| wall:", round(time.time() - started, 1), "s")
    structured = info.get("structured") or {}
    assert structured.get("n") == 99, f"unexpected structured result: {structured}"
    print("PROBE OK")


if __name__ == "__main__":
    main()

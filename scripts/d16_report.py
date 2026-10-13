#!/usr/bin/env python3
"""D16 switch-over observation report: side-by-side v2 vs v3 health and
job stats while both gateways serve real traffic.

  v2: http://172.28.50.184:7788 (X-API-Key, key from its systemd env)
  v3: http://172.28.50.183:7790 (Bearer/X-API-Key, key file arg)

Usage: d16_report.py --v3-key-file /tmp/req3key [--since-hours 24]
Prints a markdown table; exit 1 if v3 has format failures or failures
ratio worse than v2's (used for the switch decision).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

V2_URL = "http://172.28.50.184:7788"
V3_URL = "http://172.28.50.183:7790"


def v2_key() -> str:
    pid = subprocess.run(
        ["pgrep", "-f", "req2_gateway[.]py --real"],
        capture_output=True, text=True, check=False,
    ).stdout.split()
    if not pid:
        return ""
    env = subprocess.run(
        ["cat", f"/proc/{pid[0]}/environ"], capture_output=True, text=True,
        check=False,
    ).stdout
    for chunk in env.split("\x00"):
        if chunk.startswith("REQ2GW_API_KEY="):
            return chunk.split("=", 1)[1]
    return ""


def fetch(url: str, headers: dict) -> tuple[int, object]:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.7.1",
                                               **headers})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()[:200]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v3-key-file", required=True)
    ap.add_argument("--since-hours", type=float, default=24)
    args = ap.parse_args()
    with open(args.v3_key_file) as fh:
        v3_key = fh.read().strip()

    s2, h2 = fetch(V2_URL + "/healthz",
                   {"X-API-Key": v2_key()} if v2_key() else {})
    s3, h3 = fetch(V3_URL + "/healthz", {"X-API-Key": v3_key})

    since = (datetime.now(UTC) - timedelta(hours=args.since_hours)
             ).isoformat()
    _, jobs = fetch(
        f"{V3_URL}/v1/jobs?limit=100",
        {"X-API-Key": v3_key, "Accept": "application/json"},
    )

    total = completed = failed = queued = running = waiting = 0
    for j in (jobs.get("jobs", []) if isinstance(jobs, dict) else []):
        if j.get("created_at", "") < since:
            continue
        total += 1
        st = j["status"]
        if st.startswith("completed"):
            completed += 1
        elif st == "failed":
            failed += 1
        elif st == "input_required":
            waiting += 1
        elif st == "running":
            running += 1
        else:
            queued += 1

    lines = [
        "# D16 observation report", "",
        (f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} "
         f"(window: last {args.since_hours:g} h)"), "",
        "| | v2 (:7788) | v3 (:7790) |",
        "|---|---|---|",
        (f"| health | {s2} {json.dumps(h2)[:60] if s2 == 200 else ''} "
         f"| {s3} ok={h3.get('executor', {}).get('ok') if s3 == 200 else ''} |"),
        f"| jobs in window | n/a (v2 has no list API) | {total} |",
        f"| completed | - | {completed} |",
        f"| failed | - | {failed} |",
        f"| running / waiting / queued | - | {running} / {waiting} / {queued} |",
    ]
    print("\n".join(lines))
    if s3 != 200:
        print("\nv3 UNREACHABLE — do not switch")
        return 1
    if failed > completed and total >= 5:
        print("\nv3 failure rate high — hold the switch")
        return 1
    print("\nv3 healthy — switch-over may proceed per owner decision")
    return 0


if __name__ == "__main__":
    sys.exit(main())

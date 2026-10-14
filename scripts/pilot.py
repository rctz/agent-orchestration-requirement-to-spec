#!/usr/bin/env python3
"""Run the v2-benchmark pilot (M10, design §12).

Replays every ~/hermes-workspaces/req-lab-v2 project that has an intake
prompt (appendix/00-intake.md, verbatim), with scripted answers from
pilot/answers/<project>.yaml (substring-matched, default_answer
fallback), collects the design §12 metrics per project and writes
pilot/report.md with a pass/fail verdict per bar. Optionally runs the
blind A/B quality judge (glm-5.3, rubric §12, randomized order) for the
5 v2-COMPLETE projects and stores raw judge output in pilot/judge/.

Usage:
  pilot.py --base-url http://localhost:7790 --api-key-file /tmp/req3key \
           [--v2-root ~/hermes-workspaces/req-lab-v2] [--only NAME ...] \
           [--judge] [--skip-runs]
Exit 0 = report written; 1 = infra failure before any run started.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
V2_COMPLETE = (
    "celsius-fahrenheit-converter-2fe4",
    "greeting-function-spec-design-604d",
    "i-want-simple-python-to-do-web-scriping",
    "ros2-api-gateway-3a15",
    "simple-shopping-cart-0fc0",
)
RUBRIC = (
    "completeness of requirements vs prompt, acceptance testability, "
    "spec implementability without questions, consistency, absence of "
    "scope creep"
)


def http(method: str, url: str, key: str, body: dict | None = None,
         timeout_s: int = 90) -> tuple[int, object]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": "curl/8.7.1",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw[:500]


class Gateway:
    def __init__(self, base_url: str, key: str):
        self.base = base_url.rstrip("/")
        self.key = key

    def create(self, prompt: str, project: str) -> dict:
        status, body = http("POST", f"{self.base}/v1/jobs", self.key, {
            "prompt": prompt,
            "options": {"project_name": project},
        })
        if status != 202:
            raise RuntimeError(f"create failed {status}: {body}")
        return body

    def job(self, job_id: str) -> dict:
        _, body = http("GET", f"{self.base}/v1/jobs/{job_id}", self.key)
        return body

    def events(self, job_id: str) -> list[dict]:
        _, body = http(
            "GET",
            f"{self.base}/v1/jobs/{job_id}/events?format=json",
            self.key,
        )
        if isinstance(body, dict):
            return body.get("events", [])
        return []

    def answer(self, job_id: str, payload: dict) -> dict:
        status, body = http(
            "POST", f"{self.base}/v1/jobs/{job_id}/answers", self.key, payload
        )
        if status != 200:
            raise RuntimeError(f"answer failed {status}: {body}")
        return body

    def artifact(self, job_id: str, name: str) -> bytes:
        url = f"{self.base}/v1/jobs/{job_id}/artifacts/{name}"
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self.key}",
                          "User-Agent": "curl/8.7.1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()


def load_answers(answers_dir: Path, project: str) -> list[tuple[str, str]]:
    path = answers_dir / f"{project}.yaml"
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        print(f"    WARNING: {path.name} is invalid YAML ({exc}) — "
              "using defaults", flush=True)
        return []
    return [(str(k), str(v)) for k, v in data.items()]


def pick_answers(job: dict, scripted: list[tuple[str, str]]) -> dict:
    answers: dict[str, str] = {}
    for q in job.get("questions") or []:
        chosen = None
        for substr, ans in scripted:
            if substr.lower() in q["text"].lower():
                chosen = ans
                break
        answers[q["id"]] = chosen if chosen is not None else q["default_answer"]
    return answers


def run_project(gw: Gateway, project: str, prompt: str,
                scripted: list[tuple[str, str]], timeout_s: int) -> dict:
    created = gw.create(prompt, project)
    job_id = created["job_id"]
    started = time.monotonic()
    deadline = time.monotonic() + timeout_s
    last = ""
    while time.monotonic() < deadline:
        time.sleep(8)
        job = gw.job(job_id)
        state = f"{job['status']}/{job.get('phase')}/{job.get('gate')}"
        if state != last:
            print(f"    [{int(time.monotonic() - started):4d}s] {state}",
                  flush=True)
            last = state
        if job["status"] == "input_required":
            if job.get("gate") == "questions":
                answers = pick_answers(job, scripted)
                print(f"    answering {len(answers)} question(s)", flush=True)
                gw.answer(job_id, {"answers": answers})
            else:
                print("    confirming requirements", flush=True)
                gw.answer(job_id, {"action": "confirm"})
        elif job["status"] in ("completed", "completed_with_issues", "failed"):
            return {"job_id": job_id, "job": job,
                    "wall_s": round(time.monotonic() - started, 1)}
    return {"job_id": job_id, "job": gw.job(job_id), "wall_s": None,
            "timeout": True}


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def collect_metrics(gw: Gateway, result: dict) -> dict:
    job = result["job"]
    events = gw.events(result["job_id"])
    tokens: dict[str, int] = {}
    waiting_s = 0.0
    gate_at: float | None = None
    rounds = {"req_review": 0, "spec_review": 0}
    for ev in events:
        epoch = _epoch(ev["ts"])
        if ev["type"] == "agent_completed":
            data = ev.get("data") or {}
            agent = data.get("agent", "?")
            tokens[agent] = tokens.get(agent, 0) + (data.get("tokens") or 0)
        elif ev["type"] in ("questions_asked", "confirm_requirements_requested"):
            gate_at = epoch
        elif ev["type"] in ("questions_answered", "requirements_confirmed") \
                and gate_at is not None:
            waiting_s += max(0.0, epoch - gate_at)
            gate_at = None
        elif ev["type"] == "req_review_completed":
            rounds["req_review"] += 1
        elif ev["type"] == "spec_review_completed":
            rounds["spec_review"] += 1
    metrics = {
        "job_id": result["job_id"],
        "status": job["status"],
        "wall_s": result.get("wall_s"),
        "waiting_s": round(waiting_s, 1),
        "tokens": tokens,
        "tokens_total": sum(tokens.values()),
        "rounds": rounds,
        "versions": job.get("versions"),
        "known_issues": len(job.get("known_issues") or []),
        "error": (job.get("error") or {}).get("code"),
    }
    if not result.get("timeout") and job["status"].startswith("completed"):
        try:
            spec = gw.artifact(result["job_id"], "spec.md")
            metrics["spec_size_kb"] = round(len(spec) / 1024, 1)
        except Exception as exc:  # noqa: BLE001 — record and continue
            metrics["format_failure"] = f"spec.md: {exc}"
    return metrics


# ---- A/B judge -------------------------------------------------------------


def judge_call(prompt: str) -> dict:
    """glm-5.3 reasons before answering: budget generously (a long rubric
    input makes reasoning exceed small max_tokens and content comes back
    EMPTY with finish_reason=length — observed live in the pilot)."""
    import os
    base = os.environ["LITELLM_BASE_URL"].rstrip("/")
    key = os.environ["LITELLM_API_KEY"]
    last_err = ""
    for attempt, max_tokens in enumerate((8000, 16000), 1):
        status, resp = http("POST", f"{base}/chat/completions", key, {
            "model": "glm-5.3",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }, timeout_s=420)
        if status != 200:
            last_err = f"judge LLM {status}: {str(resp)[:200]}"
            continue
        choice = resp["choices"][0]
        text = choice["message"].get("content") or ""
        if not text.strip():
            last_err = (f"empty content (finish={choice.get('finish_reason')}, "
                        f"usage={resp.get('usage', {}).get('completion_tokens')}"
                        " completion tokens)")
            continue
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            last_err = f"no JSON in: {text[:200]}"
            continue
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            last_err = f"bad JSON ({exc}): {text[:200]}"
    raise RuntimeError(last_err or "judge failed")


def _latest_md(folder: Path) -> str:
    files = sorted(folder.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"no markdown in {folder}")
    return files[-1].read_text()


def run_judge(gw: Gateway, project: str, v2_dir: Path, out_dir: Path) -> dict:
    v2_req = _latest_md(v2_dir / "requirements")
    v2_spec = _latest_md(v2_dir / "spec")
    metrics = json.loads((out_dir / "metrics" / f"{project}.json").read_text())
    r3_req = gw.artifact(metrics["job_id"], "requirement.md").decode()
    r3_spec = gw.artifact(metrics["job_id"], "spec.md").decode()

    seed = int(hashlib.sha256(project.encode()).hexdigest()[:8], 16)
    a_is_v3 = random.Random(seed).random() < 0.5
    docs_a = (r3_req, r3_spec) if a_is_v3 else (v2_req, v2_spec)
    docs_b = (v2_req, v2_spec) if a_is_v3 else (r3_req, r3_spec)

    intake = (v2_dir / "appendix" / "00-intake.md").read_text()[:4000]
    prompt = (
        "You are a blind requirements/spec quality judge. Two teams (A and B) "
        "each produced a requirements document and a design spec from the same "
        f"user prompt. Judge on: {RUBRIC}.\n\n"
        f"USER PROMPT:\n---\n{intake}\n---\n\n"
        f"TEAM A REQUIREMENTS:\n---\n{docs_a[0][:12000]}\n---\n"
        f"TEAM A SPEC:\n---\n{docs_a[1][:16000]}\n---\n\n"
        f"TEAM B REQUIREMENTS:\n---\n{docs_b[0][:12000]}\n---\n"
        f"TEAM B SPEC:\n---\n{docs_b[1][:16000]}\n---\n\n"
        'Return ONLY a JSON object: {"better": "A"|"B"|"tie", '
        '"missing_in_a": [...], "missing_in_b": [...], '
        '"reasons": "<=80 words"}. missing_in_* lists requirements or topics '
        "present in the OTHER team's documents but absent in this one's, that "
        "the user prompt implied."
    )
    verdict = judge_call(prompt)
    verdict["a_is_v3"] = a_is_v3
    # Map the blind letter onto teams honestly: "tie" only when the judge
    # says tie. (A bug recorded every v2 win as "tie" — fixed 2026-10-14;
    # historical judge files were recomputed from their raw fields.)
    if verdict.get("better") == "tie":
        verdict["better_is_v3"] = "tie"
    elif verdict.get("better") in ("A", "B"):
        verdict["better_is_v3"] = (
            "v3" if (verdict["better"] == "A") == a_is_v3 else "v2"
        )
    else:
        verdict["better_is_v3"] = "unparsed"
    (out_dir / "judge").mkdir(parents=True, exist_ok=True)
    (out_dir / "judge" / f"{project}.json").write_text(
        json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    return verdict


# ---- report ----------------------------------------------------------------

_FMT_TIMES = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S")


def _parse_ts(s: str) -> datetime | None:
    s = s.strip()
    for fmt in _FMT_TIMES:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def v2_wall_minutes(v2_dir: Path) -> float | None:
    state = v2_dir / "STATE.json"
    if not state.is_file():
        return None
    try:
        data = json.loads(state.read_text())
        created = _parse_ts(data.get("created", ""))
        complete = _parse_ts(data.get("complete_at", ""))
        if created and complete:
            return round((complete - created).total_seconds() / 60, 1)
    except Exception:  # noqa: BLE001
        return None
    return None


def write_report(out_dir: Path, v2_root: Path, judge_results: dict) -> None:
    rows = []
    for mf in sorted((out_dir / "metrics").glob("*.json")):
        m = json.loads(mf.read_text())
        m["v2_wall_min"] = v2_wall_minutes(v2_root / m["project"])
        m["v3_wall_min_excl_wait"] = (
            round((m["wall_s"] - m["waiting_s"]) / 60, 1)
            if m.get("wall_s") is not None else None)
        rows.append(m)

    lines = [
        "# req3 pilot report (M10, design §12)", "",
        ("| project | status | v3 wall excl wait | v2 wall | tokens | "
         "rounds req/spec | spec KB | issues | baseline |"),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        lines.append(
            f"| {m['project']} | {m['status']} | "
            f"{m.get('v3_wall_min_excl_wait', '-')} min | "
            f"{m.get('v2_wall_min') or '-'} min | {m['tokens_total']} | "
            f"{m['rounds']['req_review']}/{m['rounds']['spec_review']} | "
            f"{m.get('spec_size_kb', '-')} | {m['known_issues']} | "
            f"{'COMPLETE (A/B)' if m['project'] in V2_COMPLETE else 'partial'} |")

    fmt_fail = sum(1 for m in rows if m.get("format_failure")
                   or m["status"] == "failed")
    lines += [
        "", "## Pass bars (design §12)", "",
        (f"- Format/validation failures at delivery: **{fmt_fail}** "
         f"({'PASS' if fmt_fail == 0 else 'FAIL'}, bar = 0)"),
    ]
    over = [m["project"] for m in rows
            if m.get("v3_wall_min_excl_wait") is not None
            and m["v3_wall_min_excl_wait"] > 60]
    lines.append(
        f"- Wall time excl waiting (≤ 1 h): "
        f"{'PASS' if not over else 'FAIL: ' + ', '.join(over)}")

    if judge_results:
        wins = [p for p, v in judge_results.items()
                if v.get("better_is_v3") == "v3"]
        ties = [p for p, v in judge_results.items()
                if v.get("better_is_v3") == "tie"]
        losses = [p for p, v in judge_results.items()
                  if v.get("better_is_v3") == "v2"]
        missing = {
            p: (v.get("missing_in_a") if v.get("a_is_v3")
                else v.get("missing_in_b"))
            for p, v in judge_results.items() if "error" not in v
        }
        missing_real = {p: x for p, x in missing.items() if x}
        lines += [
            (f"- Blind A/B (v3 ≥ v2 on ≥ 4/5): v3 wins **{len(wins)}** "
             f"(ties {len(ties)}, losses {len(losses)}) — "
            f"{'PASS' if len(wins) + len(ties) >= 4 else 'FAIL'}; wins: "
            f"{', '.join(wins) or '-'}; losses: {', '.join(losses) or '-'}"),
            (f"- v3 missing a prompt-implied requirement v2 had: "
             f"{'none — PASS' if not missing_real else 'REVIEW: see judge/*.json ' + str(list(missing_real))}"),
            "", "## Judge verdicts (blind, randomized order)", "",
        ]
        for p, v in judge_results.items():
            if "error" in v:
                lines.append(f"- **{p}**: judge error — {v['error'][:120]}")
                continue
            lines.append(
                f"- **{p}**: better = {v['better']} "
                f"(v3 was {'A' if v['a_is_v3'] else 'B'} → "
                f"{v['better_is_v3']}) — {str(v.get('reasons', ''))[:200]}")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:7790")
    ap.add_argument("--api-key-file", required=True)
    ap.add_argument("--v2-root",
                    default=str(Path.home() / "hermes-workspaces" / "req-lab-v2"))
    ap.add_argument("--out", default=str(REPO / "pilot"))
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--per-project-timeout", type=int, default=3600)
    ap.add_argument("--skip-runs", action="store_true",
                    help="rebuild report/judge from saved metrics only")
    ap.add_argument("--judge", action="store_true")
    args = ap.parse_args()

    with open(args.api_key_file) as fh:
        gw = Gateway(args.base_url, fh.read().strip())
    v2_root = Path(args.v2_root).expanduser()
    out_dir = Path(args.out)
    (out_dir / "metrics").mkdir(parents=True, exist_ok=True)
    answers_dir = out_dir / "answers"

    projects = sorted(
        p.name for p in v2_root.iterdir()
        if (p / "appendix" / "00-intake.md").is_file()
    )
    if args.only:
        projects = [p for p in projects if p in args.only]
    print(f"pilot projects ({len(projects)}): {', '.join(projects)}", flush=True)

    if not args.skip_runs:
        for project in projects:
            prompt = (v2_root / project / "appendix" / "00-intake.md").read_text()
            scripted = load_answers(answers_dir, project)
            print(f"== {project} ({len(scripted)} scripted answers)", flush=True)
            result = run_project(gw, project, prompt, scripted,
                                 args.per_project_timeout)
            metrics = collect_metrics(gw, result)
            metrics["project"] = project
            (out_dir / "metrics" / f"{project}.json").write_text(
                json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
            print(f"   -> {metrics['status']} tokens={metrics['tokens_total']} "
                  f"wall={metrics['wall_s']}s wait={metrics['waiting_s']}s",
                  flush=True)

    judge_results: dict = {}
    if args.judge:
        for project in V2_COMPLETE:
            if not (out_dir / "metrics" / f"{project}.json").is_file():
                continue
            if (out_dir / "judge" / f"{project}.json").is_file():
                print(f"== judge {project} (cached)", flush=True)
                judge_results[project] = json.loads(
                    (out_dir / "judge" / f"{project}.json").read_text())
                continue
            print(f"== judge {project}", flush=True)
            try:
                judge_results[project] = run_judge(
                    gw, project, v2_root / project, out_dir)
                print(f"   -> better_is_v3="
                      f"{judge_results[project]['better_is_v3']}", flush=True)
            except Exception as exc:  # noqa: BLE001
                judge_results[project] = {"error": str(exc)}
                print(f"   -> judge failed: {exc}", flush=True)

    write_report(out_dir, v2_root, judge_results)
    print(f"report: {out_dir / 'report.md'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

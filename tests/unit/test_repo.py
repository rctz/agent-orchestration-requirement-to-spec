"""Repo integration tests (plan M7): scan flow, root validation, summary
feeding the designer — with the FakeExecutor."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app
from tests.fakes import (
    FakeExecutor,
    design_reply,
    make_doc,
    make_spec,
    review_full,
)

API_KEY = "test-key"
AUTH = {"Authorization": f"Bearer {API_KEY}"}

SUMMARY = {
    "stack": ["python 3.13", "fastapi"],
    "modules": [
        {"path": "app/main.py", "purpose": "entry point", "key_exports": ["create_app"]}
    ],
    "conventions": ["src layout", "pytest under tests/"],
    "existing_interfaces": [
        {"name": "create_app()", "kind": "function", "summary": "app factory"}
    ],
    "constraints": ["async first", "no new deps"],
}


def _config(tmp_path) -> Config:
    return Config(
        data_dir=str(tmp_path / "data"),
        api_key=API_KEY,
        max_concurrent_jobs=2,
    )


def _wait_status(client, job_id, statuses, timeout_s=10.0):
    import time

    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        last = client.get(f"/v1/jobs/{job_id}", headers=AUTH).json()
        if last["status"] in statuses:
            return last
        time.sleep(0.05)
    pytest.fail(f"job never reached {statuses}; last: {last}")


@pytest.fixture()
def repo(tmp_path):
    root = tmp_path / "repos" / "demo"
    (root / "app").mkdir(parents=True)
    (root / "README.md").write_text("# Demo service\nFastAPI demo.\n", encoding="utf-8")
    (root / "app" / "main.py").write_text(
        "def create_app():\n    return 'app'\n", encoding="utf-8"
    )
    return root


def _fake():
    return FakeExecutor(
        [
            SUMMARY,                                    # repo-scanner
            design_reply(make_doc(reqs=("REQ-001",))),  # req-designer
            review_full([], verdict="pass"),            # req-reviewer
            {"spec": make_spec(("REQ-001",))},          # spec-designer
            review_full([], verdict="pass"),            # spec-reviewer
        ]
    )


def test_repo_scan_feeds_designer(tmp_path, repo):
    cfg = _config(tmp_path)
    cfg.repo.allowed_roots = [str(tmp_path / "repos")]
    app = create_app(cfg, executor=_fake())
    with TestClient(app) as client:
        body = {
            "prompt": "Add a health endpoint",
            "repo": {"path": str(repo)},
        }
        job_id = client.post("/v1/jobs", json=body, headers=AUTH).json()["job_id"]
        gated = _wait_status(client, job_id, {"input_required", "failed"})
        assert gated["gate"] == "confirm_requirements", gated.get("error")
        client.post(
            f"/v1/jobs/{job_id}/answers", json={"action": "confirm"}, headers=AUTH
        )
        done = _wait_status(client, job_id, {"completed", "failed"})
        assert done["status"] == "completed", done.get("error")
        summary_file = (
            tmp_path / "data" / "jobs" / job_id / "repo_summary.json"
        )
        assert summary_file.is_file()
        assert json.loads(summary_file.read_text())["stack"] == ["python 3.13", "fastapi"]
        # designer saw the summary
        events = client.get(
            f"/v1/jobs/{job_id}/events?format=json", headers=AUTH
        ).json()["events"]
        types = [e["type"] for e in events]
        assert "repo_scanned" in types


def test_repo_outside_roots_fails_job(tmp_path, repo):
    cfg = _config(tmp_path)
    cfg.repo.allowed_roots = [str(tmp_path / "elsewhere")]
    app = create_app(cfg, executor=_fake())
    with TestClient(app) as client:
        job_id = client.post(
            "/v1/jobs",
            json={"prompt": "x", "repo": {"path": str(repo)}},
            headers=AUTH,
        ).json()["job_id"]
        failed = _wait_status(client, job_id, {"failed"})
        assert failed["error"]["code"] == "invalid_repo"


def _git_repo(tmp_path):
    """A real local git repo (offline) usable as a clone source."""
    import subprocess

    src = tmp_path / "gitsrc"
    (src / "svc").mkdir(parents=True)
    (src / "README.md").write_text("# Git demo\n", encoding="utf-8")
    (src / "svc" / "api.py").write_text("def handler():\n    return 1\n", encoding="utf-8")
    run = lambda *a: subprocess.run(["git", "-C", str(src), *a], check=True,
                                    capture_output=True)
    run("init", "-q", "-b", "main")
    run("-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return src


def test_repo_git_url_cloned_and_scanned(tmp_path, monkeypatch):
    src = _git_repo(tmp_path)
    cfg = _config(tmp_path)
    app = create_app(cfg, executor=_fake())
    monkeypatch.setattr("req3.repo.resolve.git_ls_remote", lambda url, ref: None)
    with TestClient(app) as client:
        job_id = client.post(
            "/v1/jobs",
            json={"prompt": "x", "repo": {"git_url": f"file://{src}", "ref": "main"}},
            headers=AUTH,
        ).json()["job_id"]
        gated = _wait_status(client, job_id, {"input_required", "failed"})
        assert gated["status"] == "input_required", gated.get("error")
        clone = tmp_path / "data" / "jobs" / job_id / "repo"
        assert (clone / "svc" / "api.py").is_file()
        assert not (clone / ".git").exists()
        events = client.get(f"/v1/jobs/{job_id}/events?format=json",
                            headers=AUTH).json()["events"]
        resolved = [e for e in events if e["type"] == "repo_resolved"][-1]["data"]["repo"]
        assert resolved["kind"] == "git" and len(resolved["commit_sha"]) == 40


def test_repo_detected_in_prompt(tmp_path, repo):
    cfg = _config(tmp_path)
    cfg.repo.allowed_roots = [str(tmp_path / "repos")]
    app = create_app(cfg, executor=_fake())
    with TestClient(app) as client:
        job_id = client.post(
            "/v1/jobs", json={"prompt": f"Add a health endpoint to {repo}."},
            headers=AUTH,
        ).json()["job_id"]
        gated = _wait_status(client, job_id, {"input_required", "failed"})
        assert gated["gate"] == "confirm_requirements", gated.get("error")
        snap = tmp_path / "data" / "jobs" / job_id / "repo" / "app" / "main.py"
        assert snap.is_file()  # snapshot, not the live tree


def test_repo_ambiguous_prompt_asks_question(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    cfg.repo.allowed_roots = [str(tmp_path)]
    fake = FakeExecutor([design_reply(make_doc(reqs=("REQ-001",))),
                         review_full([], verdict="pass")])
    app = create_app(cfg, executor=fake)
    monkeypatch.setattr("req3.repo.resolve.git_ls_remote", lambda url, ref: "unreachable")
    with TestClient(app) as client:
        job_id = client.post(
            "/v1/jobs",
            json={"prompt": "Extend our repo github.com/acme/missing with login"},
            headers=AUTH,
        ).json()["job_id"]
        gated = _wait_status(client, job_id, {"input_required", "failed"})
        assert gated["gate"] == "questions", gated.get("error")
        assert gated["questions"][0]["id"] == "Q-00"
        assert gated["questions"][0]["default_answer"] == "none"
        client.post(f"/v1/jobs/{job_id}/answers", json={"answers": {"Q-00": "none"}},
                    headers=AUTH)
        # proceeds without repo: scanner skipped, designer runs next
        nxt = _wait_status(client, job_id, {"input_required", "failed"})
        assert nxt["gate"] == "confirm_requirements", nxt.get("error")
        assert fake.agents[0] == "req-designer"  # scanner skipped


# ---- resolve.py pure functions (design §10 step b/c) -----------------------

from req3.repo import resolve as rr


@pytest.mark.parametrize("prompt,expect", [
    ("Add login to https://github.com/acme/shop (branch dev)",
     [("git", "https://github.com/acme/shop", None)]),
    ("see github.com/acme/shop/tree/dev for code",
     [("git", "https://github.com/acme/shop", "dev")]),
    ("clone git@github.com:acme/shop.git please",
     [("git", "git@github.com:acme/shop.git", None)]),
    ("https://gitlab.com/g/p.git/tree/release/1.2",
     [("git", "https://gitlab.com/g/p.git", "release/1.2")]),
    ("The project is at /home/pi/projects/shop.", [("path", "/home/pi/projects/shop", None)]),
    ("code in ~/work/shop", [("path", "~/work/shop", None)]),
    ("Build a converter", []),
    ("https://github.com/a/one and https://github.com/b/two",
     [("git", "https://github.com/a/one", None), ("git", "https://github.com/b/two", None)]),
])
def test_extract_candidates(prompt, expect):
    got = [(c.kind, c.url or c.path, c.ref) for c in rr.extract_candidates(prompt)]
    assert got == expect


def test_path_outside_roots_and_symlink_escape(tmp_path):
    root = tmp_path / "allowed"
    (root / "ok").mkdir(parents=True)
    (tmp_path / "secret").mkdir()
    (root / "link").symlink_to(tmp_path / "secret")
    assert rr.path_allowed(str(root / "ok"), [str(root)])[1] is None
    assert "not under" in rr.path_allowed("/etc", [str(root)])[1]
    assert "not under" in rr.path_allowed(str(root / "link"), [str(root)])[1]
    assert "disabled" in rr.path_allowed(str(root / "ok"), [])[1]


def test_mentions_repo():
    assert rr.mentions_repo("extend our existing project")
    assert not rr.mentions_repo("build a temperature converter")

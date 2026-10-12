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


def test_repo_git_url_refused(tmp_path):
    cfg = _config(tmp_path)
    cfg.repo.allowed_roots = [str(tmp_path)]
    app = create_app(cfg, executor=_fake())
    with TestClient(app) as client:
        job_id = client.post(
            "/v1/jobs",
            json={"prompt": "x", "repo": {"git_url": "https://example.com/r.git"}},
            headers=AUTH,
        ).json()["job_id"]
        failed = _wait_status(client, job_id, {"failed"})
        assert failed["error"]["code"] == "phase_unavailable"

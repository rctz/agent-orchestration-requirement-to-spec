"""Contract tests for REST API v1 (plan M1 verify list).

No LLM involved: the app runs with a stub executor and a temp SQLite DB.
"""
from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app

API_KEY = "test-key-123"
AUTH = {"Authorization": f"Bearer {API_KEY}"}
CREATE_BODY = {
    "prompt": "Build a Celsius to Fahrenheit converter CLI",
    "options": {"size": "S"},
}

EXPECTED_STATUS_KEYS = {
    "job_id", "project", "status", "phase", "gate", "round", "questions",
    "questions_expire_at", "requirements_preview", "versions", "known_issues",
    "error", "created_at", "updated_at",
}


@pytest.fixture()
def client(tmp_path):
    app = create_app(Config(data_dir=str(tmp_path / "data"), api_key=API_KEY))
    with TestClient(app) as test_client:
        yield test_client


def _create(client, **overrides):
    body = {**CREATE_BODY, **overrides}
    response = client.post("/v1/jobs", json=body, headers=AUTH)
    assert response.status_code == 202, response.text
    return response.json()


def test_healthz_open_without_auth(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["executor"]["ok"] is True


def test_auth_required_everywhere_except_healthz(client):
    assert client.post("/v1/jobs", json=CREATE_BODY).status_code == 401
    wrong = {"Authorization": "Bearer wrong-key"}
    assert client.post("/v1/jobs", json=CREATE_BODY, headers=wrong).status_code == 401
    assert client.get("/v1/jobs").status_code == 401
    assert client.get("/v1/jobs/j_whatever").status_code == 401
    assert client.post("/v1/jobs/j_whatever/cancel").status_code == 401
    assert client.get("/v1/openapi.json").status_code == 401
    for response in (
        client.post("/v1/jobs", json=CREATE_BODY, headers=wrong),
        client.get("/v1/jobs", headers=wrong),
    ):
        assert response.json()["error"]["code"] == "unauthorized"


def test_create_job_returns_202_with_links(client):
    body = _create(client)
    assert body["job_id"].startswith("j_")
    assert body["status"] == "queued"
    for key in ("self", "events", "answers", "cancel", "artifacts"):
        assert key in body["links"]
    self_link = body["links"]["self"]
    assert client.get(self_link, headers=AUTH).status_code == 200


def test_get_job_stable_shape(client):
    job_id = _create(client)["job_id"]
    body = client.get(f"/v1/jobs/{job_id}", headers=AUTH).json()
    assert set(body) == EXPECTED_STATUS_KEYS
    assert body["status"] == "queued"
    assert body["round"] == {"req_review": 0, "spec_review": 0}
    assert body["versions"] == {"requirements": 0, "spec": 0}
    assert body["questions"] == []
    assert body["known_issues"] == []
    assert body["error"] is None
    assert body["phase"] is None and body["gate"] is None


def test_unknown_job_404_error_envelope(client):
    response = client.get("/v1/jobs/j_nope", headers=AUTH)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_idempotency_replay_returns_same_job(client):
    headers = {**AUTH, "Idempotency-Key": "abc-1"}
    first = client.post("/v1/jobs", json=CREATE_BODY, headers=headers).json()
    second = client.post("/v1/jobs", json=CREATE_BODY, headers=headers).json()
    assert first["job_id"] == second["job_id"]
    listing = client.get("/v1/jobs", headers=AUTH).json()
    assert listing["total"] == 1


def test_list_filter_and_pagination(client):
    for _ in range(3):
        _create(client)
    queued = client.get("/v1/jobs?status=queued", headers=AUTH).json()
    assert queued["total"] == 3 and len(queued["jobs"]) == 3
    done = client.get("/v1/jobs?status=completed", headers=AUTH).json()
    assert done["total"] == 0 and done["jobs"] == []
    page = client.get("/v1/jobs?limit=2", headers=AUTH).json()
    assert len(page["jobs"]) == 2 and page["total"] == 3
    bogus = client.get("/v1/jobs?status=bogus", headers=AUTH)
    assert bogus.status_code == 422
    assert bogus.json()["error"]["code"] == "invalid_request"


def test_cancel_queued_job_and_events(client, tmp_path):
    job_id = _create(client)["job_id"]
    response = client.post(f"/v1/jobs/{job_id}/cancel", headers=AUTH)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    again = client.post(f"/v1/jobs/{job_id}/cancel", headers=AUTH)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "invalid_state"
    cancel_unknown = client.post("/v1/jobs/j_nope/cancel", headers=AUTH)
    assert cancel_unknown.status_code == 404
    # audit trail: job_created + job_cancelled events recorded
    connection = sqlite3.connect(tmp_path / "data" / "req3.db")
    try:
        types = [
            row[0]
            for row in connection.execute(
                "SELECT type FROM events WHERE job_id = ? ORDER BY seq", (job_id,)
            )
        ]
    finally:
        connection.close()
    assert types == ["job_created", "job_cancelled"]


def test_validation_error_envelope(client):
    missing = client.post("/v1/jobs", json={"prompt": ""}, headers=AUTH)
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "invalid_request"
    bad_size = client.post(
        "/v1/jobs", json={**CREATE_BODY, "options": {"size": "XL"}}, headers=AUTH
    )
    assert bad_size.status_code == 422
    bad_repo = client.post(
        "/v1/jobs", json={**CREATE_BODY, "repo": {"path": "relative"}}, headers=AUTH
    )
    assert bad_repo.status_code == 422
    extra = client.post("/v1/jobs", json={**CREATE_BODY, "who": "me"}, headers=AUTH)
    assert extra.status_code == 422


def test_openapi_documented_and_protected(client):
    response = client.get("/v1/openapi.json", headers=AUTH)
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/v1/jobs" in paths and "/v1/jobs/{job_id}" in paths


def test_workspace_input_files_written(client, tmp_path):
    job_id = _create(client)["job_id"]
    job_dir = tmp_path / "data" / "jobs" / job_id
    prompt = (job_dir / "input" / "prompt.txt").read_text(encoding="utf-8")
    assert prompt.startswith("Build a Celsius")
    options = json.loads((job_dir / "input" / "options.json").read_text())
    assert options == {"size": "S"}
    profile = json.loads((job_dir / "input" / "profile.json").read_text())
    assert profile == {"name": "default"}
    for sub in ("repo", "context", "canonical", "reviews", "out"):
        assert (job_dir / sub).is_dir()


def test_create_refused_when_executor_unhealthy(tmp_path):
    """Design §10: refuse jobs when the executor self-check fails (503)."""
    from req3.executor.base import HealthReport

    class UnhealthyExecutor:
        async def health(self):
            return HealthReport(ok=False, detail="missing agents: ['req-designer']")

    app = create_app(Config(data_dir=str(tmp_path / "data"), api_key=API_KEY))
    with TestClient(app) as test_client:
        app.state.executor = UnhealthyExecutor()
        app.state.health_cache = None
        response = test_client.post("/v1/jobs", json=CREATE_BODY, headers=AUTH)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "executor_unavailable"
        assert "req-designer" in response.json()["error"]["message"]

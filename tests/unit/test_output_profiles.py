"""Output-profile registry tests (M8, design §8/§9): builtin listing,
registration validation, name shadowing, and create-time resolution."""
from __future__ import annotations

from contextlib import contextmanager

from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app
from tests.fakes import FakeExecutor

API_KEY = "test-key-123"
AUTH = {"Authorization": f"Bearer {API_KEY}"}

VALID_PROFILE = {
    "name": "jira-lite",
    "files": [
        {
            "path": "tickets.json",
            "template": "{% for r in requirements.requirements %}"
                        "{{ r.id }}\n{% endfor %}",
        },
    ],
}


@contextmanager
def _client(tmp_path):
    app = create_app(
        Config(data_dir=str(tmp_path / "data"), api_key=API_KEY),
        executor=FakeExecutor([]),
    )
    with TestClient(app) as client:
        yield client


def test_builtin_listed(tmp_path):
    with _client(tmp_path) as client:
        body = client.get("/v1/output-profiles", headers=AUTH).json()
        assert set(body["builtin"]) >= {"default", "json", "men"}
        assert body["registered"] == []


def test_register_then_list_and_unknown_rejected(tmp_path):
    with _client(tmp_path) as client:
        created = client.post(
            "/v1/output-profiles",
            headers=AUTH,
            json={"definition": VALID_PROFILE},
        )
        assert created.status_code == 201, created.text
        assert created.json()["name"] == "jira-lite"

        listed = client.get("/v1/output-profiles", headers=AUTH).json()
        assert [r["name"] for r in listed["registered"]] == ["jira-lite"]

        bad = client.post(
            "/v1/jobs",
            headers=AUTH,
            json={"prompt": "p", "output_profile": "nope"},
        )
        assert bad.status_code == 422


def test_register_rejects_invalid_and_builtin(tmp_path):
    with _client(tmp_path) as client:
        invalid = client.post(
            "/v1/output-profiles",
            headers=AUTH,
            json={"definition": {"name": ""}},
        )
        assert invalid.status_code == 422

        shadow = client.post(
            "/v1/output-profiles",
            headers=AUTH,
            json={"definition": {**VALID_PROFILE, "name": "men"}},
        )
        assert shadow.status_code == 409

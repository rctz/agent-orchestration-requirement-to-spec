"""Revise flow tests (plan M6): spec-only patch, requirements affected,
questions needed — all against the FakeExecutor."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app
from tests.fakes import (
    QUESTION,
    FakeExecutor,
    design_reply,
    make_doc,
    make_spec,
    review_full,
)

API_KEY = "test-key"
AUTH = {"Authorization": f"Bearer {API_KEY}"}


def _config(tmp_path) -> Config:
    return Config(data_dir=str(tmp_path / "data"), api_key=API_KEY, max_concurrent_jobs=2)


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


def _completed_client(tmp_path, fake) -> tuple[TestClient, str]:
    app = create_app(_config(tmp_path), executor=fake)
    client = TestClient(app)
    client.__enter__()
    job_id = client.post("/v1/jobs", json={"prompt": "demo"}, headers=AUTH).json()["job_id"]
    _wait_status(client, job_id, {"input_required"})
    client.post(f"/v1/jobs/{job_id}/answers", json={"action": "confirm"}, headers=AUTH)
    _wait_status(client, job_id, {"completed", "failed"})
    return client, job_id


def analyst_reply(**over) -> dict:
    base = {
        "needs_questions": False,
        "requirements_affected": False,
        "reason": "doc-only change",
        "suggested_questions": [],
    }
    base.update(over)
    return base


BASE_RUN = [
    design_reply(make_doc(reqs=("REQ-001",))),
    review_full([], verdict="pass"),
    {"spec": make_spec(("REQ-001",))},
    review_full([], verdict="pass"),
]


def test_revise_spec_only_patch(tmp_path):
    fake = FakeExecutor(
        BASE_RUN
        + [
            analyst_reply(),                                   # revise-analyst
            {"spec": make_spec(("REQ-001",), version=2)},      # spec patch
            review_full([], verdict="pass"),                   # spec review
        ]
    )
    client, job_id = _completed_client(tmp_path, fake)
    body = client.post(
        f"/v1/jobs/{job_id}/revise",
        json={"text": "Document the module filename as temperature.py"},
        headers=AUTH,
    )
    assert body.status_code == 200
    assert body.json()["phase"] == "revise_analyze"
    done = _wait_status(client, job_id, {"completed", "failed"})
    assert done["status"] == "completed", done.get("error")
    assert done["versions"]["spec"] == 2

    v2 = client.get(f"/v1/jobs/{job_id}/artifacts?version=2", headers=AUTH).json()
    assert v2["version"] == 2
    v1 = client.get(f"/v1/jobs/{job_id}/artifacts?version=1", headers=AUTH).json()
    assert v1["version"] == 1  # previous version still downloadable
    events = [
        e["type"]
        for e in client.get(f"/v1/jobs/{job_id}/events?format=json", headers=AUTH).json()[
            "events"
        ]
    ]
    assert "revise_requested" in events and "revise_analyzed" in events


def test_revise_requirements_affected_goes_back_to_confirm(tmp_path):
    fake = FakeExecutor(
        BASE_RUN
        + [
            analyst_reply(requirements_affected=True, reason="adds new capability"),
            design_reply(make_doc(reqs=("REQ-001", "REQ-002"), version=2)),
            review_full([], verdict="pass"),
        ]
    )
    client, job_id = _completed_client(tmp_path, fake)
    body = client.post(
        f"/v1/jobs/{job_id}/revise",
        json={"text": "Also support Kelvin input"},
        headers=AUTH,
    )
    assert body.status_code == 200
    gated = _wait_status(client, job_id, {"input_required", "failed"})
    assert gated["gate"] == "confirm_requirements", gated.get("error")
    assert gated["versions"]["requirements"] == 2


def test_revise_needs_questions_then_answers(tmp_path):
    question = dict(QUESTION)
    question["text"] = "Which persistence backend?"
    fake = FakeExecutor(
        BASE_RUN
        + [
            analyst_reply(
                needs_questions=True,
                reason="storage choice changes REQ-002 acceptance",
                suggested_questions=[question],
            ),
            design_reply(make_doc(reqs=("REQ-001",), version=2)),
            review_full([], verdict="pass"),
        ]
    )
    client, job_id = _completed_client(tmp_path, fake)
    client.post(
        f"/v1/jobs/{job_id}/revise",
        json={"text": "Persist the cart across page refreshes"},
        headers=AUTH,
    )
    gated = _wait_status(client, job_id, {"input_required", "failed"})
    assert gated["gate"] == "questions"
    assert gated["questions"][0]["id"] == "Q-01"
    client.post(
        f"/v1/jobs/{job_id}/answers",
        json={"answers": {"Q-01": "localStorage"}},
        headers=AUTH,
    )
    again = _wait_status(client, job_id, {"input_required", "failed"})
    assert again["gate"] == "confirm_requirements", again.get("error")


def test_revise_rejects_non_completed(tmp_path):
    fake = FakeExecutor(list(BASE_RUN))
    client, _completed_id = _completed_client(tmp_path, fake)
    # make a new job that is queued, not completed
    other = client.post("/v1/jobs", json={"prompt": "x"}, headers=AUTH).json()["job_id"]
    resp = client.post(f"/v1/jobs/{other}/revise", json={"text": "change"}, headers=AUTH)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"
    client.__exit__(None, None, None)

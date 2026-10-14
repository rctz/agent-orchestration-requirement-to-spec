"""Engine + requirement-phase tests (plan M4 verify: every §3 transition
row, review rules, gates, expiry, resume) — all with the FakeExecutor."""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app
from tests.fakes import (
    QUESTION,
    FakeExecutor,
    design_reply,
    finding,
    make_doc,
    make_spec,
    review_full,
    review_verify,
)

API_KEY = "test-key"
AUTH = {"Authorization": f"Bearer {API_KEY}"}


def _config(tmp_path) -> Config:
    return Config(data_dir=str(tmp_path / "data"), api_key=API_KEY, max_concurrent_jobs=2)


def _wait_status(client, job_id, statuses, timeout_s=10.0):
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        body = client.get(f"/v1/jobs/{job_id}", headers=AUTH).json()
        last = body
        if body["status"] in statuses:
            return body
        time.sleep(0.05)
    pytest.fail(f"job never reached {statuses}; last: {last}")


def _create(client, prompt="Build a demo tool", **options):
    body = {"prompt": prompt}
    if options:
        body["options"] = options
    response = client.post("/v1/jobs", json=body, headers=AUTH)
    assert response.status_code == 202, response.text
    return response.json()["job_id"]


def _events(client, job_id):
    response = client.get(
        f"/v1/jobs/{job_id}/events", params={"format": "json"}, headers=AUTH
    )
    assert response.status_code == 200
    return [event["type"] for event in response.json()["events"]]


# ---- happy path: questions -> answers -> confirm gate ----------------------


def test_happy_path_questions_then_confirm(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc(reqs=("REQ-001", "REQ-002")), [QUESTION]),
            design_reply(make_doc(reqs=("REQ-001", "REQ-002"), version=2)),
            review_full([], verdict="pass"),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        gate = _wait_status(client, job_id, {"input_required"})
        assert gate["gate"] == "questions"
        assert gate["questions"][0]["id"] == "Q-01"
        assert gate["questions_expire_at"]
        answered = client.post(
            f"/v1/jobs/{job_id}/answers",
            json={"answers": {"Q-01": "Yes"}},
            headers=AUTH,
        )
        assert answered.status_code == 200
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"
        preview = confirm["requirements_preview"]
        assert preview["project"] == "demo"
        decisions = [d for d in preview["decisions"] if d["question_id"] == "Q-01"]
        assert decisions and decisions[0]["source"] == "user"
        types = _events(client, job_id)
        assert "questions_asked" in types
        assert "req_review_completed" in types
        assert "confirm_requirements_requested" in types
        # canonical files exist
        canonical = tmp_path / "data" / "jobs" / job_id / "canonical"
        assert (canonical / "requirements.v1.json").is_file()
        assert (canonical / "requirements.v2.json").is_file()
        # nonce present in every prompt (cache mitigation, design §10)
        assert fake.prompts and all("[req3 nonce job=" in p for p in fake.prompts)


def test_partial_answers_wait_then_apply_defaults(tmp_path):
    questions = [
        QUESTION,
        {**QUESTION, "id": "Q-02", "text": "Second?", "default_answer": "Maybe"},
    ]
    fake = FakeExecutor(
        [
            design_reply(make_doc(), questions),
            design_reply(make_doc(version=2)),
            review_full([], verdict="pass"),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        partial = client.post(
            f"/v1/jobs/{job_id}/answers",
            json={"answers": {"Q-01": "Yes"}},
            headers=AUTH,
        )
        assert partial.status_code == 200
        assert partial.json()["status"] == "input_required"  # still waiting
        resume = client.post(
            f"/v1/jobs/{job_id}/answers", json={"apply_defaults": True}, headers=AUTH
        )
        assert resume.status_code == 200
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"
        sources = {d["question_id"]: d["source"] for d in confirm["requirements_preview"]["decisions"]}
        assert sources["Q-01"] == "user"
        assert sources["Q-02"] == "system_default_expired"


def test_unknown_question_id_rejected(tmp_path):
    fake = FakeExecutor([design_reply(make_doc(), [QUESTION])])
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        bad = client.post(
            f"/v1/jobs/{job_id}/answers",
            json={"answers": {"Q-99": "x"}},
            headers=AUTH,
        )
        assert bad.status_code == 422
        assert bad.json()["error"]["code"] == "invalid_request"


# ---- review discipline: fix round, diff guard, caps -------------------------


def test_fix_round_with_diff_guard_and_verify(tmp_path):
    doc_v1 = make_doc(reqs=("REQ-001", "REQ-002"))
    fix_doc = make_doc(reqs=("REQ-001", "REQ-002", "REQ-009"), version=2)
    # designer "fixes" REQ-001 (targeted) but also tampers REQ-002 and adds REQ-009
    fix_doc["requirements"][1]["title"] = "TAMPERED REQ-002"
    fake = FakeExecutor(
        [
            design_reply(doc_v1),
            review_full([finding("F-01", "P1", ["REQ-001"])]),
            design_reply(fix_doc),
            review_verify([{"finding_id": "F-01", "status": "resolved"}]),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"
        types = _events(client, job_id)
        assert "fix_round_started" in types
        assert "fix_diff_guard" in types
        guarded = json.loads(
            (tmp_path / "data" / "jobs" / job_id / "canonical" / "requirements.v2.json")
            .read_text()
        )
        by_id = {r["id"]: r for r in guarded["requirements"]}
        assert by_id["REQ-002"]["title"] == "Title REQ-002"  # reverted
        assert "REQ-009" not in by_id  # untargeted addition dropped
        rounds = confirm["round"]
        assert rounds["req_review"] == 2


def test_review_cap_reaches_confirm_with_open_items(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc()),
            review_full([finding("F-01", "P1", ["REQ-001"])]),
            design_reply(make_doc(version=2)),
            review_verify([{"finding_id": "F-01", "status": "not_resolved"}]),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"
        assert any("F-01" in issue or "R-01" in issue for issue in confirm["known_issues"])
        assert "review_cap_reached" in _events(client, job_id)


def test_p2_go_to_known_issues_not_blocking(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc()),
            review_full([finding("F-01", "P2", ["REQ-001"])]),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"  # P2 did not block
        assert confirm["known_issues"]


# ---- gates: cancel / change_request / confirm -> M5 stub --------------------


def test_cancel_from_questions_gate(tmp_path):
    fake = FakeExecutor([design_reply(make_doc(), [QUESTION])])
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        response = client.post(f"/v1/jobs/{job_id}/cancel", headers=AUTH)
        assert response.json()["status"] == "cancelled"


def test_change_request_loops_back_to_req_design(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc()),
            review_full([], verdict="pass"),
            design_reply(make_doc(version=2)),  # after change_request
            review_full([], verdict="pass"),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        change = client.post(
            f"/v1/jobs/{job_id}/answers",
            json={"action": "change_request", "text": "Add reporting"},
            headers=AUTH,
        )
        assert change.status_code == 200
        confirm = _wait_status(client, job_id, {"input_required"})
        assert confirm["gate"] == "confirm_requirements"
        assert "change_request" in _events(client, job_id)


def test_confirm_proceeds_into_spec_phase(tmp_path):
    """M5: confirm now continues into the spec phases (no longer a stub)."""
    fake = FakeExecutor(
        [
            design_reply(make_doc()),
            review_full([], verdict="pass"),
            {"spec": make_spec(("REQ-001",))},
            review_full([], verdict="pass"),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        confirmed = client.post(
            f"/v1/jobs/{job_id}/answers", json={"action": "confirm"}, headers=AUTH
        )
        assert confirmed.status_code == 200
        done = _wait_status(client, job_id, {"completed", "completed_with_issues", "failed"})
        assert done["status"] == "completed", done.get("error")


# ---- expiry ----------------------------------------------------------------


def test_expiry_applies_defaults_and_resumes(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc(), [QUESTION]),
            design_reply(make_doc(version=2)),
            review_full([], verdict="pass"),
        ]
    )
    config = _config(tmp_path)
    app = create_app(config, executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})

        # run the expiry tick on the app's event loop (TestClient thread)
        import asyncio as aio

        from req3.engine.expiry import tick

        async def _force():
            await app.state.db.update_job(
                job_id, questions_expire_at="2000-01-01T00:00:00+00:00"
            )
            await tick(app.state.db, app.state.engine)

        loop = app.state.engine._workers[0].get_loop()
        aio.run_coroutine_threadsafe(_force(), loop).result(timeout=10)

        confirm = _wait_status(client, job_id, {"input_required", "failed"})
        assert confirm["gate"] == "confirm_requirements"
        types = _events(client, job_id)
        assert "questions_expired" in types
        preview_decisions = confirm["requirements_preview"]["decisions"]
        assert any(d["source"] == "system_default_expired" for d in preview_decisions)


# ---- resume after restart ----------------------------------------------------


def test_restart_resumes_mid_phase(tmp_path):
    fake1 = FakeExecutor(block_first=True)
    config = _config(tmp_path)
    app1 = create_app(config, executor=fake1)
    with TestClient(app1) as client:
        job_id = _create(client)
        # status "running" is saved before the phase; wait until the
        # designer call is actually in flight (fixes a timing flake)
        deadline = time.monotonic() + 10
        running = {}
        while time.monotonic() < deadline:
            running = client.get(f"/v1/jobs/{job_id}", headers=AUTH).json()
            if running.get("phase") == "req_design" and fake1.prompts:
                break
            time.sleep(0.02)
        assert running["phase"] == "req_design", running
    # app1 shut down mid-call; job persists as running/req_design
    fake2 = FakeExecutor(
        [
            design_reply(make_doc(), [QUESTION]),
        ]
    )
    app2 = create_app(Config(data_dir=str(tmp_path / "data"), api_key=API_KEY),
                      executor=fake2)
    with TestClient(app2) as client2:
        gate = _wait_status(client2, job_id, {"input_required"})
        assert gate["gate"] == "questions"
        assert "questions_asked" in _events(client2, job_id)


# ---- SSE ---------------------------------------------------------------------


def test_sse_json_snapshot_and_since(tmp_path):
    fake = FakeExecutor([design_reply(make_doc(), [QUESTION])])
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create(client)
        _wait_status(client, job_id, {"input_required"})
        events = client.get(
            f"/v1/jobs/{job_id}/events", params={"format": "json"}, headers=AUTH
        ).json()["events"]
        assert events[0]["type"] == "job_created"
        later = client.get(
            f"/v1/jobs/{job_id}/events",
            params={"format": "json", "since": events[0]["seq"]},
            headers=AUTH,
        ).json()["events"]
        assert later and later[0]["seq"] > events[0]["seq"]


@pytest.mark.asyncio()
async def test_cancel_during_phase_is_not_clobbered(tmp_path):
    """Live bug (2026-10-13): a cancel landing while the runner is inside a
    phase step (LLM call in flight) was overwritten by the next transition
    save — the job kept running after `cancelled`. The runner must re-check
    status after dispatch and abort without saving."""
    import asyncio

    import httpx

    fake = FakeExecutor(
        [design_reply(make_doc(reqs=("REQ-001",)), [])], block_first=True
    )
    app = create_app(_config(tmp_path), executor=fake)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            created = await client.post(
                "/v1/jobs", json={"prompt": "demo tool"}, headers=AUTH
            )
            assert created.status_code == 202, created.text
            job_id = created.json()["job_id"]
            deadline = time.monotonic() + 5
            while not fake.agents and time.monotonic() < deadline:
                await asyncio.sleep(0.02)
            assert fake.agents, "first agent call never started"
            cancelled = await client.post(
                f"/v1/jobs/{job_id}/cancel", headers=AUTH
            )
            assert cancelled.status_code == 200, cancelled.text
            assert cancelled.json()["status"] == "cancelled"
            fake.gate.set()  # release the in-flight agent call
            await asyncio.sleep(0.5)  # let the runner step finish
            body = (await client.get(f"/v1/jobs/{job_id}", headers=AUTH)).json()
            assert body["status"] == "cancelled"

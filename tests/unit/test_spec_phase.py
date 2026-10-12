"""Spec phase + delivery tests (plan M5): full flow, spec diff guard,
P0 extra round, artifacts endpoints — all with the FakeExecutor."""
from __future__ import annotations

import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from req3.config import Config
from req3.main import create_app
from tests.fakes import (
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
    import time

    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        body = client.get(f"/v1/jobs/{job_id}", headers=AUTH).json()
        last = body
        if body["status"] in statuses:
            return body
        import time as _t

        _t.sleep(0.05)
    pytest.fail(f"job never reached {statuses}; last: {last}")


def _create_and_confirm(client, fake_replies_tail):
    """design -> review pass -> confirm, then the given spec-phase replies."""
    body = {"prompt": "Build a demo tool"}
    job_id = client.post("/v1/jobs", json=body, headers=AUTH).json()["job_id"]
    _wait_status(client, job_id, {"input_required"})
    client.post(f"/v1/jobs/{job_id}/answers", json={"action": "confirm"}, headers=AUTH)
    return job_id


def test_full_flow_to_completed_with_artifacts(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc(reqs=("REQ-001", "REQ-002"))),
            review_full([], verdict="pass"),
            {"spec": make_spec(("REQ-001", "REQ-002"))},
            review_full([], verdict="pass"),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create_and_confirm(client, fake)
        done = _wait_status(client, job_id, {"completed", "failed"})
        assert done["status"] == "completed", done.get("error")
        assert done["phase"] == "done"

        listing = client.get(f"/v1/jobs/{job_id}/artifacts", headers=AUTH).json()
        assert listing["version"] == 1
        assert set(listing["files"]) == {"requirement.md", "spec.md", "manifest.json"}
        manifest = listing["manifest"]
        assert manifest["status"] == "completed"
        assert manifest["metrics"]["tokens"]

        # file endpoint serves real bytes; manifest sha matches
        spec_md = client.get(
            f"/v1/jobs/{job_id}/artifacts/spec.md", headers=AUTH
        )
        assert spec_md.status_code == 200
        assert b"# Design Spec" in spec_md.content
        import hashlib

        for entry in manifest["files"]:
            served = client.get(
                f"/v1/jobs/{job_id}/artifacts/{entry['path']}", headers=AUTH
            ).content
            assert hashlib.sha256(served).hexdigest() == entry["sha256"]

        bundle = client.get(f"/v1/jobs/{job_id}/artifacts.zip", headers=AUTH)
        assert bundle.status_code == 200
        with zipfile.ZipFile(io.BytesIO(bundle.content)) as zf:
            assert sorted(zf.namelist()) == [
                "manifest.json", "requirement.md", "spec.md",
            ]

        # unknown artifact -> 404 envelope
        missing = client.get(f"/v1/jobs/{job_id}/artifacts/nope.md", headers=AUTH)
        assert missing.status_code == 404


def test_spec_fix_round_with_diff_guard(tmp_path):
    good = make_spec(("REQ-001", "REQ-002"))
    tampered = make_spec(("REQ-001", "REQ-002"), version=2)
    tampered["interfaces"][0]["errors"] = ["CHANGED WITHOUT TARGET"]  # untargeted edit
    fake = FakeExecutor(
        [
            design_reply(make_doc(reqs=("REQ-001", "REQ-002"))),
            review_full([], verdict="pass"),
            {"spec": good},
            review_full([finding("F-01", "P1", ["B-01"], checklist_id="S-04")]),
            {"spec": tampered},
            review_verify([{"finding_id": "F-01", "status": "resolved"}]),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create_and_confirm(client, fake)
        done = _wait_status(client, job_id, {"completed", "failed"})
        assert done["status"] == "completed", done.get("error")
        spec_v2 = json.loads(
            (tmp_path / "data" / "jobs" / job_id / "canonical" / "spec.v2.json").read_text()
        )
        assert spec_v2["interfaces"][0]["errors"] == ["ValueError on invalid input"]
        assert done["round"]["spec_review"] == 2


def test_p0_extra_round_then_completed_with_issues(tmp_path):
    fake = FakeExecutor(
        [
            design_reply(make_doc(reqs=("REQ-001",))),
            review_full([], verdict="pass"),
            {"spec": make_spec(("REQ-001",))},
            review_full([finding("F-01", "P0", ["C-01"], checklist_id="S-01")]),
            {"spec": make_spec(("REQ-001",), version=2)},
            review_verify([{"finding_id": "F-01", "status": "not_resolved"}]),
            {"spec": make_spec(("REQ-001",), version=3)},   # P0 extra fix attempt
            review_verify([{"finding_id": "F-01", "status": "not_resolved"}]),
        ]
    )
    app = create_app(_config(tmp_path), executor=fake)
    with TestClient(app) as client:
        job_id = _create_and_confirm(client, fake)
        done = _wait_status(client, job_id, {"completed_with_issues", "failed"})
        assert done["status"] == "completed_with_issues", done.get("error")
        assert done["known_issues"], "open findings must be visible"
        assert done["round"]["spec_review"] == 3  # 2 rounds + 1 P0-only extra
        manifest = client.get(
            f"/v1/jobs/{job_id}/artifacts", headers=AUTH
        ).json()["manifest"]
        assert manifest["known_issues"]

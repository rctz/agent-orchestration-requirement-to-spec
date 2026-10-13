"""A2A adapter tests (M8): v2-compatible part parsing, answer mapping,
task-state projection, JSON-RPC envelope, and auth on /a2a."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from req3.api import a2a
from req3.api.errors import ApiError
from req3.config import Config
from req3.main import create_app
from tests.fakes import FakeExecutor

API_KEY = "test-key-123"
AUTH = {"Authorization": f"Bearer {API_KEY}"}


def _msg(parts, task_id=None):
    message = {"role": "user", "parts": parts}
    if task_id:
        message["taskId"] = task_id
    return message


# ---- parse_parts ----------------------------------------------------------


def test_parse_parts_text_data_file():
    message = {
        "parts": [
            {"kind": "text", "text": "hello "},
            {"kind": "text", "text": "world"},
            {"kind": "data", "data": {"options": {"size": "S"}}},
            {"kind": "file", "file": {"name": "x.csv", "bytes": "..."}},
        ]
    }
    text, data, files = a2a.parse_parts(message)
    assert text == "hello \nworld"  # v2 joins text parts with newline
    assert data == {"options": {"size": "S"}}
    assert files == [{"name": "x.csv", "bytes": "..."}]


def test_parse_parts_untyped_fallback():
    message = {"parts": [{"text": "bare"}, {"data": {"k": 1}}]}
    text, data, _ = a2a.parse_parts(message)
    assert text == "bare"
    assert data == {"k": 1}


# ---- _map_answer (v2 conventions) -----------------------------------------


@pytest.mark.asyncio()
async def test_map_answer_approve_reject():
    assert await a2a._map_answer("APPROVE", {}, {}) == {"action": "confirm"}
    out = await a2a._map_answer("REJECT: missing Kelvin", {}, {})
    assert out["action"] == "change_request"
    assert out["text"] == "missing Kelvin"


@pytest.mark.asyncio()
async def test_map_answer_structured_variants():
    assert await a2a._map_answer("", {"answers": {"Q-01": "yes"}}, {}) == {
        "answers": {"Q-01": "yes"}
    }
    assert await a2a._map_answer("", {"action": "confirm"}, {}) == {
        "action": "confirm"
    }
    revise = await a2a._map_answer("use SQLite", {"action": "revise"}, {})
    assert revise["__revise__"] and revise["text"] == "use SQLite"
    bare = await a2a._map_answer("please add Kelvin", {}, {})
    assert bare["__revise__"] is True


@pytest.mark.asyncio()
async def test_map_answer_uninterpretable():
    # Empty text with no structured data cannot be interpreted (whitespace-
    # only text is treated as a revise request by _map_answer).
    with pytest.raises(ApiError):
        await a2a._map_answer("", {}, {})


# ---- _task_from_job state projection --------------------------------------


def _job(**over):
    base = {
        "job_id": "j_1",
        "status": "running",
        "phase": "req_design",
        "gate": None,
        "questions": [],
        "questions_expire_at": None,
        "requirements_preview": None,
        "versions": {"requirements": 1, "spec": 0},
        "known_issues": [],
        "error": None,
    }
    base.update(over)
    return base


def test_task_states():
    assert a2a._task_from_job(_job(), "http://x")["status"]["state"] == "working"
    assert (
        a2a._task_from_job(_job(status="queued"), "http://x")["status"]["state"]
        == "submitted"
    )
    failed = a2a._task_from_job(
        _job(status="failed", error={"code": "agent_error", "message": "boom",
                                     "phase": "req_design"}),
        "http://x",
    )
    assert failed["status"]["state"] == "failed"
    assert "boom" in failed["status"]["message"]["parts"][0]["text"]

    done = a2a._task_from_job(
        _job(status="completed", phase="done"), "http://x"
    )
    assert done["status"]["state"] == "completed"
    data_part = done["status"]["message"]["parts"][1]["data"]
    assert data_part["artifacts"]["requirement.md"].startswith("http://x/")


def test_task_input_required_variants():
    questions = a2a._task_from_job(
        _job(status="input_required", gate="questions",
             questions=[{"id": "Q-01", "text": "Numeric only?"}]),
        "http://x",
    )
    payload = questions["status"]["message"]["parts"][1]["data"]
    assert payload["questions"][0]["id"] == "Q-01"

    confirm = a2a._task_from_job(
        _job(status="input_required", gate="confirm_requirements",
             requirements_preview={"goal": "g"}),
        "http://x",
    )
    text = confirm["status"]["message"]["parts"][0]["text"]
    assert "APPROVE" in text


# ---- HTTP surface ----------------------------------------------------------


@pytest.fixture()
def client(tmp_path):
    app = create_app(
        Config(data_dir=str(tmp_path / "data"), api_key=API_KEY),
        executor=FakeExecutor([]),
    )
    with TestClient(app) as test_client:
        yield test_client


def test_agent_card_public(client):
    response = client.get("/.well-known/agent.json")
    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "req3"
    assert card["url"].endswith("/a2a")


def test_a2a_requires_auth(client):
    response = client.post("/a2a", json={"jsonrpc": "2.0", "id": 1,
                                        "method": "tasks/get",
                                        "params": {"id": "j_none"}})
    assert response.status_code == 401


def test_a2a_unknown_method_and_task(client):
    bad = client.post("/a2a", headers=AUTH,
                      json={"jsonrpc": "2.0", "id": 2, "method": "nope"})
    assert bad.status_code == 200
    assert bad.json()["error"]["code"] == -32601

    missing = client.post(
        "/a2a", headers=AUTH,
        json={"jsonrpc": "2.0", "id": 3, "method": "tasks/get",
              "params": {"id": "j_missing"}},
    )
    assert missing.status_code == 200
    assert "not_found" in missing.json()["error"]["message"]


def test_a2a_message_send_creates_job(client):
    response = client.post(
        "/a2a",
        headers=AUTH,
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "message/send",
            "params": {"message": _msg([{"kind": "text",
                                         "text": "Build a tiny CLI"}])},
        },
    )
    assert response.status_code == 200, response.text
    task = response.json()["result"]
    assert task["id"].startswith("j_")
    assert task["status"]["state"] in {"submitted", "working"}

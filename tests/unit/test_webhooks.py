"""Webhook tests (M8): HMAC signing, retry-on-5xx with backoff,
status filter, and silence on loader failure. No network."""
from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from req3.api import webhooks
from req3.api.webhooks import WebhookSender, verify_signature

SECRET = "whsec-test"


def test_verify_signature_roundtrip():
    body = b'{"job_id": "j_1", "event": "completed"}'
    sender = WebhookSender(SECRET, None)
    header = sender._sign(body)
    assert header.startswith("sha256=")
    assert verify_signature(SECRET, body, header)
    assert not verify_signature(SECRET, b"tampered", header)
    assert not verify_signature(SECRET, body, None)
    assert not verify_signature(SECRET, body, "md5=abc")
    assert not verify_signature("other", body, header)


def test_status_filter_and_missing_callback_do_nothing():
    sender = WebhookSender(SECRET, None)
    sender.notify("j_1", "http://x/hook", "progress", "running")  # filtered status
    sender.notify("j_1", "", "job_completed", "completed")  # no callback
    assert not sender._tasks


@pytest.mark.asyncio()
async def test_retry_on_500_then_success(monkeypatch):
    monkeypatch.setattr(webhooks, "RETRY_DELAYS", (0, 0, 0, 0, 0))
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) < 3:
            return httpx.Response(500)
        return httpx.Response(200)

    async def load(job_id):
        return {"job_id": job_id, "status": "completed"}

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sender = WebhookSender(SECRET, load, client=client)
    sender.notify("j_9", "http://receiver/hook", "job_completed", "completed")
    for _ in range(50):
        if not sender._tasks:
            break
        await asyncio.sleep(0.02)
    await sender.close()

    assert len(calls) == 3, "must retry 5xx and stop on 2xx"
    body = calls[0].read()
    assert verify_signature(SECRET, body, calls[0].headers["X-Req3-Signature"])
    payload = json.loads(body)
    assert payload["event"] == "job_completed"
    assert payload["job_id"] == "j_9"


@pytest.mark.asyncio()
async def test_gives_up_after_all_retries(monkeypatch):
    monkeypatch.setattr(webhooks, "RETRY_DELAYS", (0, 0))
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(503)

    async def load(job_id):
        return {"job_id": job_id, "status": "failed"}

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sender = WebhookSender(SECRET, load, client=client)
    sender.notify("j_x", "http://receiver/hook", "job_failed", "failed")
    for _ in range(50):
        if not sender._tasks:
            break
        await asyncio.sleep(0.02)
    await sender.close()
    assert len(attempts) == 3, "1 initial + RETRY_DELAYS attempts"


@pytest.mark.asyncio()
async def test_loader_failure_is_silent():
    async def boom(job_id):
        raise RuntimeError("db gone")

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200))
    )
    sender = WebhookSender(SECRET, boom, client=client)
    sender.notify("j_z", "http://receiver/hook", "job_completed", "completed")
    for _ in range(50):
        if not sender._tasks:
            break
        await asyncio.sleep(0.02)
    await sender.close()  # no exception raised = pass

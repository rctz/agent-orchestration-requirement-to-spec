"""Signed webhooks (design §9): POST the job status on input_required,
completed, completed_with_issues, failed. Convenience only — polling/SSE
always works. X-Req3-Signature: sha256=HMAC-SHA256(body, secret).
Retries with backoff, never blocks the engine."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Any

import httpx

log = logging.getLogger("req3.webhooks")

RETRY_DELAYS = (1, 2, 4, 8, 16)
NOTIFY_STATUSES = {
    "input_required",
    "completed",
    "completed_with_issues",
    "failed",
}


class WebhookSender:
    def __init__(
        self,
        secret: str | None,
        status_loader,
        timeout_s: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ):
        self._secret = secret.encode() if secret else None
        self._load_status = status_loader  # async (job_id) -> dict body
        self._timeout = timeout_s
        self._client = client  # injectable for tests (MockTransport)
        self._tasks: set[asyncio.Task] = set()

    def _sign(self, body: bytes) -> str:
        if not self._secret:
            return ""
        return "sha256=" + hmac.new(self._secret, body, hashlib.sha256).hexdigest()

    def notify(self, job_id: str, callback_url: str, event_type: str, status: str):
        """Fire-and-forget delivery; safe to call from the engine loop."""
        if status not in NOTIFY_STATUSES or not callback_url:
            return
        task = asyncio.create_task(self._deliver(job_id, callback_url, event_type))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _deliver(self, job_id: str, callback_url: str, event_type: str):
        try:
            body_dict = await self._load_status(job_id)
        except Exception:
            log.exception("webhook: cannot load status for %s", job_id)
            return
        body_dict["event"] = event_type
        body = json.dumps(body_dict, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "req3-webhook/1.0",
        }
        sig = self._sign(body)
        if sig:
            headers["X-Req3-Signature"] = sig
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        started = time.monotonic()
        last_error: str | None = None
        for attempt, delay in enumerate((0, *RETRY_DELAYS)):
            if delay:
                await asyncio.sleep(delay)
            try:
                resp = await self._client.post(callback_url, content=body, headers=headers)
                if resp.status_code < 500:
                    log.info(
                        "webhook %s -> %s %s (attempt %d, %.1fs)",
                        job_id, callback_url, resp.status_code, attempt + 1,
                        time.monotonic() - started,
                    )
                    return
                last_error = f"HTTP {resp.status_code}"
            except Exception as exc:  # noqa: BLE001 — report, keep retrying
                last_error = f"{type(exc).__name__}: {exc}"
        log.error(
            "webhook %s -> %s FAILED after %d attempts: %s",
            job_id, callback_url, len(RETRY_DELAYS) + 1, last_error,
        )

    async def close(self):
        for task in list(self._tasks):
            task.cancel()
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def verify_signature(secret: str, body: bytes, header: str | None) -> bool:
    """Constant-time check of an incoming X-Req3-Signature header."""
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)


def status_body_for(job: dict[str, Any], event_type: str) -> dict[str, Any]:
    """Compose the webhook payload (job status shape + event)."""
    payload = dict(job)
    payload["event"] = event_type
    return payload

"""SSE event stream + JSON polling for job events (design §9).

GET /v1/jobs/{id}/events         -> text/event-stream (?since=seq)
GET /v1/jobs/{id}/events?format=json -> snapshot list
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..engine.machine import TERMINAL_STATUS_VALUES
from .auth import require_api_key
from .errors import ApiError

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])

POLL_INTERVAL_S = 1.0
KEEPALIVE_S = 15.0


async def _get_job_or_404(request: Request, job_id: str):
    record = await request.app.state.db.get_job(job_id)
    if record is None:
        raise ApiError(404, "not_found", f"unknown job: {job_id}")
    return record


@router.get("/jobs/{job_id}/events")
async def job_events(
    job_id: str,
    request: Request,
    since: int = 0,
    format: str | None = None,
):
    record = await _get_job_or_404(request, job_id)
    del record  # existence check only
    if format == "json":
        events = await request.app.state.db.list_events(job_id, since=since)
        return JSONResponse({"events": events})
    return StreamingResponse(
        _stream(request, job_id, since),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream(request: Request, job_id: str, since: int):
    last_seq = since
    last_send = 0.0
    import time

    while True:
        if await request.is_disconnected():
            return
        events = await request.app.state.db.list_events(job_id, since=last_seq)
        terminal = False
        for event in events:
            last_seq = event["seq"]
            last_send = time.monotonic()
            payload = json.dumps({"seq": event["seq"], "ts": event["ts"],
                                  "type": event["type"], "data": event["data"]},
                                 ensure_ascii=False)
            yield f"id: {event['seq']}\nevent: {event['type']}\ndata: {payload}\n\n"
        record = await request.app.state.db.get_job(job_id)
        if record is not None and record.status in TERMINAL_STATUS_VALUES:
            terminal = True
        if terminal and not events:
            yield "event: stream-end\ndata: {}\n\n"
            return
        if time.monotonic() - last_send > KEEPALIVE_S:
            last_send = time.monotonic()
            yield ": keepalive\n\n"
        await asyncio.sleep(POLL_INTERVAL_S)

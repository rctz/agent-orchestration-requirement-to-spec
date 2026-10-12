"""Expiry ticker (design §5, D5): unanswered questions expire.

A 1-minute ticker applies each expired question's default_answer, records
the decision with source=system_default_expired and continues the job.
The confirm gate expires as confirmed (recorded).
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ..store.db import Database, utcnow
from ..store.workspace import Workspace
from .phases.requirement import record_gate_decisions
from .queue import Engine

logger = logging.getLogger("req3.expiry")

TICK_INTERVAL_S = 60.0


async def expiry_loop(db: Database, engine: Engine, interval_s: float = TICK_INTERVAL_S) -> None:
    while True:
        try:
            await tick(db, engine)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - the ticker must survive anything
            logger.warning("expiry tick failed: %s", exc)
        await asyncio.sleep(interval_s)


async def tick(db: Database, engine: Engine) -> int:
    now = utcnow()
    expired = 0
    for record in await db.expired_gate_jobs(now):
        expired += 1
        if record.gate == "questions":
            await _expire_questions(db, engine, record)
        elif record.gate == "confirm_requirements":
            await db.update_job(
                record.job_id,
                status="running",
                phase="spec_design",
                gate=None,
                questions_expire_at=None,
            )
            await db.append_event(
                record.job_id, "confirmed_by_expiry", {"note": "confirm gate expired"}
            )
            engine.submit(record.job_id)
    return expired


async def _expire_questions(db: Database, engine: Engine, record: Any) -> None:
    questions = json.loads(record.questions or "[]")
    state: dict[str, Any] = json.loads(record.engine_state or "{}")
    answered: dict[str, str] = state.get("answers", {})
    unanswered = [q for q in questions if q.get("id") not in answered]
    workspace = Workspace(engine.runner.workspace_root, record.job_id)
    # record defaults as code-owned decisions (merged into the doc by req_design)
    entries = record_gate_decisions(workspace.root, answered, unanswered)
    state.setdefault("decision_log", []).extend(entries)
    state["answers"] = answered
    state["expiry_defaults"] = [q.get("id") for q in unanswered]
    await db.update_job(
        record.job_id,
        status="running",
        phase="req_design",
        gate=None,
        questions="[]",
        questions_expire_at=None,
        engine_state=json.dumps(state, ensure_ascii=False),
    )
    await db.append_event(
        record.job_id,
        "questions_expired",
        {
            "defaults_applied": [
                {"question": q.get("id"), "default": q.get("default_answer")}
                for q in unanswered
            ]
        },
    )
    engine.submit(record.job_id)

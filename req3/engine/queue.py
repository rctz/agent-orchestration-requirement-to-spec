"""Engine: asyncio queue + worker pool (design §10).

- max_concurrent_jobs workers (default 5, configurable).
- Jobs waiting on a gate do NOT hold a worker: the runner returns at the
  gate and the job is re-submitted when answers/confirm/expiry arrive.
- No silent death: any worker exception marks the job failed with an
  error record.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from ..config import Config
from ..executor.base import Executor
from ..store.db import Database
from .runner import JobRunner


class Engine:
    def __init__(
        self,
        config: Config,
        db: Database,
        executor: Executor,
        workspace_root: Path,
        webhooks=None,
    ):
        self.config = config
        self.db = db
        self.runner = JobRunner(config, db, executor, workspace_root, webhooks)
        self.webhooks = webhooks
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []

    # ---- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        for index in range(self.config.max_concurrent_jobs):
            self._workers.append(
                asyncio.create_task(self._worker(index), name=f"req3-worker-{index}")
            )

    async def stop(self) -> None:
        for worker in self._workers:
            worker.cancel()
        for worker in self._workers:
            try:
                await worker
            except asyncio.CancelledError:
                pass
        self._workers.clear()

    # ---- submission --------------------------------------------------------

    def submit(self, job_id: str) -> None:
        """Queue a job for processing (idempotent; duplicates are skipped)."""
        self._queue.put_nowait(job_id)

    async def resume_running_jobs(self) -> int:
        """On startup: re-enqueue jobs interrupted mid-phase (design §10)."""
        count = 0
        for record in await self.db.jobs_with_status("running"):
            self.submit(record.job_id)
            count += 1
        return count

    # ---- workers -----------------------------------------------------------

    async def _worker(self, index: int) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                record = await self.db.get_job(job_id)
                if record is None or record.status == "cancelled":
                    continue
                if record.status == "queued":
                    await self.db.update_job(job_id, status="running")
                    await self.db.append_event(
                        job_id, "job_started", {"worker": index}
                    )
                    record = await self.db.get_job(job_id)
                await self.runner.run(job_id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - design §10: no silent death
                try:
                    await self.db.update_job(
                        job_id,
                        status="failed",
                        error={
                            "code": "engine_error",
                            "message": f"{type(exc).__name__}: {exc}",
                            "phase": "engine",
                        },
                    )
                    await self.db.append_event(
                        job_id, "job_failed", {"code": "engine_error", "message": str(exc)[:300]}
                    )
                except Exception:  # noqa: BLE001, S110 - best effort inside failure handling
                    pass
            finally:
                self._queue.task_done()

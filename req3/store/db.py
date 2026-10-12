"""SQLite store: jobs, events, profiles (design §3, §13; WAL mode).

Every state transition appends an `events` row — the audit trail that
replaces v2's per-card logs and feeds SSE (design §3).
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiosqlite

IntegrityError = aiosqlite.IntegrityError

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id               TEXT PRIMARY KEY,
    idempotency_key      TEXT UNIQUE,
    project              TEXT,
    status               TEXT NOT NULL,
    phase                TEXT,
    gate                 TEXT,
    prompt               TEXT NOT NULL,
    output_profile       TEXT,
    repo                 TEXT,
    callback_url         TEXT,
    options              TEXT,
    "round"              TEXT NOT NULL,
    questions            TEXT NOT NULL,
    questions_expire_at  TEXT,
    requirements_preview TEXT,
    versions             TEXT NOT NULL,
    known_issues         TEXT NOT NULL,
    error                TEXT,
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs (created_at DESC);

CREATE TABLE IF NOT EXISTS events (
    job_id TEXT NOT NULL,
    seq    INTEGER NOT NULL,
    ts     TEXT NOT NULL,
    type   TEXT NOT NULL,
    data   TEXT,
    PRIMARY KEY (job_id, seq)
);

CREATE TABLE IF NOT EXISTS profiles (
    name       TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

_TERMINAL_SQL = "('completed', 'completed_with_issues', 'failed', 'cancelled')"

_JOB_COLUMNS = (
    "job_id, idempotency_key, project, status, phase, gate, prompt, "
    "output_profile, repo, callback_url, options, \"round\", questions, "
    "questions_expire_at, requirements_preview, versions, known_issues, "
    "error, created_at, updated_at"
)
_JOB_PLACEHOLDERS = ", ".join("?" for _ in range(20))


def utcnow() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def new_job_id() -> str:
    return "j_" + secrets.token_hex(6)


def json_or_none(value: Any) -> str | None:
    return None if value is None else json.dumps(value, ensure_ascii=False)


@dataclass
class JobRecord:
    """One row of the `jobs` table. JSON-valued columns are stored as text."""

    job_id: str
    status: str
    prompt: str
    created_at: str
    updated_at: str
    idempotency_key: str | None = None
    project: str | None = None
    phase: str | None = None
    gate: str | None = None
    output_profile: str | None = None  # plain profile name OR JSON text
    repo: str | None = None
    callback_url: str | None = None
    options: str | None = None
    round: str = '{"req_review": 0, "spec_review": 0}'
    questions: str = "[]"
    questions_expire_at: str | None = None
    requirements_preview: str | None = None
    versions: str = '{"requirements": 0, "spec": 0}'
    known_issues: str = "[]"
    error: str | None = None


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._db: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("database not opened")
        return self._db

    async def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA busy_timeout=5000")
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    # ---- jobs -------------------------------------------------------------

    async def create_job(self, rec: JobRecord) -> None:
        values = (
            rec.job_id, rec.idempotency_key, rec.project, rec.status, rec.phase,
            rec.gate, rec.prompt, rec.output_profile, rec.repo, rec.callback_url,
            rec.options, rec.round, rec.questions, rec.questions_expire_at,
            rec.requirements_preview, rec.versions, rec.known_issues, rec.error,
            rec.created_at, rec.updated_at,
        )
        await self.conn.execute(
            f"INSERT INTO jobs ({_JOB_COLUMNS}) VALUES ({_JOB_PLACEHOLDERS})", values
        )
        await self.conn.commit()

    async def get_job(self, job_id: str) -> JobRecord | None:
        cur = await self.conn.execute(
            f"SELECT {_JOB_COLUMNS} FROM jobs WHERE job_id = ?", (job_id,)
        )
        row = await cur.fetchone()
        return JobRecord(**dict(row)) if row else None

    async def get_job_by_idempotency_key(self, key: str) -> JobRecord | None:
        cur = await self.conn.execute(
            f"SELECT {_JOB_COLUMNS} FROM jobs WHERE idempotency_key = ?", (key,)
        )
        row = await cur.fetchone()
        return JobRecord(**dict(row)) if row else None

    async def list_jobs(
        self, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[JobRecord], int]:
        where, args = ("WHERE status = ?", [status]) if status else ("", [])
        cur = await self.conn.execute(
            f"SELECT {_JOB_COLUMNS} FROM jobs {where} "
            "ORDER BY created_at DESC, job_id LIMIT ? OFFSET ?",
            (*args, limit, offset),
        )
        rows = await cur.fetchall()
        cur = await self.conn.execute(f"SELECT COUNT(*) FROM jobs {where}", args)
        total = (await cur.fetchone())[0]
        return [JobRecord(**dict(r)) for r in rows], total

    async def cancel_job(self, job_id: str) -> bool:
        """queued/running/input_required -> cancelled; terminal stays put."""
        cur = await self.conn.execute(
            f"UPDATE jobs SET status = 'cancelled', updated_at = ? "
            f"WHERE job_id = ? AND status NOT IN {_TERMINAL_SQL}",
            (utcnow(), job_id),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    # ---- events -----------------------------------------------------------

    async def append_event(
        self, job_id: str, type_: str, data: dict[str, Any] | None = None
    ) -> int:
        cur = await self.conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE job_id = ?", (job_id,)
        )
        seq = (await cur.fetchone())[0]
        await self.conn.execute(
            "INSERT INTO events (job_id, seq, ts, type, data) VALUES (?, ?, ?, ?, ?)",
            (job_id, seq, utcnow(), type_, json_or_none(data)),
        )
        await self.conn.commit()
        return seq

    async def list_events(self, job_id: str, since: int = 0) -> list[dict[str, Any]]:
        cur = await self.conn.execute(
            "SELECT seq, ts, type, data FROM events WHERE job_id = ? AND seq > ? "
            "ORDER BY seq",
            (job_id, since),
        )
        rows = await cur.fetchall()
        return [
            {
                "seq": r["seq"],
                "ts": r["ts"],
                "type": r["type"],
                "data": json.loads(r["data"]) if r["data"] else None,
            }
            for r in rows
        ]

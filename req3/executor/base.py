"""Executor interface (design §2.1) — the ONLY abstraction agents run through.

Everything above this module talks to the Executor protocol, never to a
backend directly. Implementations: StubExecutor (M1 default),
executor/opencode.py (M2). Selected by config: `executor: stub|opencode`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class HealthReport:
    """Result of Executor.health(): agents/models/MCP present (design §10)."""

    ok: bool
    agents: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class AgentResult:
    """Result of one agent run (design §2 interface)."""

    structured: dict[str, Any] | None = None
    text: str = ""
    tokens: int | None = None
    model: str | None = None
    duration_s: float | None = None
    session_id: str | None = None
    error: str | None = None


class Executor(Protocol):
    async def health(self) -> HealthReport: ...

    async def run_agent(
        self,
        job_dir: Path,
        agent: str,
        prompt: str,
        schema: dict[str, Any] | None,
        attachments: list[Path],
        timeout_s: int,
    ) -> AgentResult: ...

    async def cancel(self, run_id: str) -> None: ...


class StubExecutor:
    """M1 placeholder: healthy, but runs no agents (opencode backend = M2)."""

    async def health(self) -> HealthReport:
        return HealthReport(
            ok=True,
            agents=[],
            models=[],
            detail="stub executor (M1; opencode backend lands in M2)",
        )

    async def run_agent(self, *args: Any, **kwargs: Any) -> AgentResult:
        raise NotImplementedError("no engine phases until M4")

    async def cancel(self, run_id: str) -> None:
        return None

    async def aclose(self) -> None:
        return None


def get_executor(
    config: Any,
    required_agents: tuple[str, ...] | list[str] = (),
    required_models: tuple[str, ...] | list[str] = (),
) -> Executor:
    """Select the executor backend by config (design §2.1)."""
    if config.executor == "stub":
        return StubExecutor()
    if config.executor == "opencode":
        from .opencode import OpencodeExecutor  # lazy: keeps stub path import-free

        return OpencodeExecutor(
            config.opencode_url,
            password=config.opencode_server_password,
            required_agents=required_agents,
            required_models=required_models,
        )
    raise ValueError(f"unknown executor backend: {config.executor!r}")

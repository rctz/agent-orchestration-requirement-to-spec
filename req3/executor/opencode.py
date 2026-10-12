"""opencode backend for the Executor interface (design §2.1, §6, §11).

The ONLY module coupled to opencode (import-lint enforced): talks HTTP to
`opencode serve` (pinned 1.19.0). API shapes verified by probe on .184
(2026-10-12, opencode 1.19.0):

- server auth: set env OPENCODE_SERVER_PASSWORD on the server; requests use
  HTTP Basic with username OPENCODE_SERVER_USERNAME (default "opencode").
- GET  /agent                      -> [{"name": ..., "mode": ...}, ...]
- GET  /config/providers           -> {"providers": [{"id", "models": {...}}]}
- POST /session?directory=<dir>    -> {"id": "ses_..."}
- POST /session/{id}/message       -> {"info": {"structured", "modelID",
  "tokens": {"total"}, "error"}, "parts": [...]}
  with body {"agent", "parts": [{"type": "text", "text"}], "format":
  {"type": "json_schema", "schema": {...}}} -> validated JSON in
  info.structured.
- POST /session/{id}/abort         -> cancel a running session.

One fresh session per run_agent call (design §2: new executor session per
phase-step). Transport retries and the schema-repair loop are separate
(plan §3 M2; design §7: max 2 each).
"""
from __future__ import annotations

import asyncio
import base64
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import httpx
import jsonschema

from .base import AgentResult, HealthReport

_RETRYABLE_STATUS = frozenset({502, 503, 504})


class OpencodeExecutor:
    """Executor backed by `opencode serve` (design §2.1 protocol)."""

    def __init__(
        self,
        base_url: str,
        password: str = "",
        username: str = "opencode",
        *,
        required_agents: Iterable[str] = (),
        required_models: Iterable[str] = (),
        transport_retries: int = 2,
        schema_repairs: int = 2,
        backoff_s: float = 1.0,
    ) -> None:
        headers = {"User-Agent": "req3-gateway"}
        if password:
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        self.required_agents = list(required_agents)
        self.required_models = list(required_models)
        self._transport_retries = transport_retries
        self._schema_repairs = schema_repairs
        self._backoff_s = backoff_s
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(30.0, read=900.0),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---- health (design §10 startup self-check) ---------------------------

    async def health(self) -> HealthReport:
        try:
            agents_resp = await self._client.get("/agent")
            agents_resp.raise_for_status()
            providers_resp = await self._client.get("/config/providers")
            providers_resp.raise_for_status()
            agents = agents_resp.json()
            providers = providers_resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            return HealthReport(ok=False, detail=f"opencode unreachable: {exc}")
        names = (
            {a.get("name") for a in agents if isinstance(a, dict)}
            if isinstance(agents, list)
            else set()
        )
        models: set[str] = set()
        for provider in providers.get("providers", []):
            pid = provider.get("id")
            for model_id in provider.get("models") or {}:
                models.add(f"{pid}/{model_id}")
        missing_agents = sorted(set(self.required_agents) - names)
        missing_models = sorted(set(self.required_models) - models)
        ok = not missing_agents and not missing_models
        if ok:
            detail = (
                f"opencode healthy: {len(names)} agents, "
                f"required models present"
            )
        else:
            detail = (
                f"missing agents: {missing_agents}; "
                f"missing models: {missing_models}"
            )
        return HealthReport(
            ok=ok,
            agents=sorted(names & set(self.required_agents)),
            models=sorted(models & set(self.required_models)),
            detail=detail,
        )

    # ---- run one agent -----------------------------------------------------

    async def run_agent(
        self,
        job_dir: Path,
        agent: str,
        prompt: str,
        schema: dict[str, Any] | None = None,
        attachments: list[Path] | None = None,
        timeout_s: int = 900,
    ) -> AgentResult:
        started = time.monotonic()
        directory = str(Path(job_dir).resolve())
        parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for attachment in attachments or []:
            # Inline text attachments (design §6.1 allows inline text); the
            # file-part shape of opencode 1.19 was not part of the probe —
            # revisit in M4 when phases actually attach files.
            content = Path(attachment).read_text(encoding="utf-8", errors="replace")
            parts.append(
                {
                    "type": "text",
                    "text": f"[attached file: {Path(attachment).name}]\n{content}",
                }
            )
        body: dict[str, Any] = {"agent": agent, "parts": parts}
        if schema is not None:
            body["format"] = {"type": "json_schema", "schema": schema}

        session_id: str | None = None
        message: dict[str, Any] | None = None
        last_error = ""
        for attempt in range(self._transport_retries + 1):
            try:
                if session_id is None:
                    session_resp = await self._client.post(
                        "/session", json={"title": agent}, params={"directory": directory}
                    )
                    session_resp.raise_for_status()
                    session_id = session_resp.json()["id"]
                response = await self._client.post(
                    f"/session/{session_id}/message",
                    json=body,
                    params={"directory": directory},
                    timeout=httpx.Timeout(30.0, read=float(timeout_s)),
                )
                if response.status_code in _RETRYABLE_STATUS and attempt < self._transport_retries:
                    raise httpx.TransportError(f"HTTP {response.status_code}")
                response.raise_for_status()
                message = response.json()
                break
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self._transport_retries:
                    await asyncio.sleep(self._backoff_s * (attempt + 1))
                    continue
        if message is None:
            return AgentResult(
                error=f"transport error after {self._transport_retries + 1} attempts: {last_error}",
                session_id=session_id,
                duration_s=round(time.monotonic() - started, 3),
            )

        info = message.get("info", {}) or {}
        structured = info.get("structured")

        # Schema validation + repair loop (design §7: exact validator errors).
        if schema is not None:
            errors = self._validation_errors(structured, schema)
            repairs = 0
            while errors and repairs < self._schema_repairs:
                repairs += 1
                fix_prompt = (
                    "Your previous reply failed JSON Schema validation.\n"
                    "Errors:\n"
                    + "\n".join(f"- {e}" for e in errors)
                    + "\nReply again with corrected JSON that satisfies the "
                    "schema exactly. Output JSON only."
                )
                try:
                    repair_resp = await self._client.post(
                        f"/session/{session_id}/message",
                        json={
                            "agent": agent,
                            "parts": [{"type": "text", "text": fix_prompt}],
                            "format": {"type": "json_schema", "schema": schema},
                        },
                        params={"directory": directory},
                        timeout=httpx.Timeout(30.0, read=float(timeout_s)),
                    )
                    repair_resp.raise_for_status()
                    message = repair_resp.json()
                except (httpx.HTTPError, ValueError) as exc:
                    return AgentResult(
                        error=f"schema repair call failed: {exc}",
                        session_id=session_id,
                        duration_s=round(time.monotonic() - started, 3),
                    )
                info = message.get("info", {}) or {}
                structured = info.get("structured")
                errors = self._validation_errors(structured, schema)
            if errors:
                return AgentResult(
                    structured=None,
                    text=self._text_of(message),
                    error="schema validation failed after "
                    f"{self._schema_repairs} repairs: {'; '.join(errors[:3])}",
                    session_id=session_id,
                    duration_s=round(time.monotonic() - started, 3),
                )

        tokens = (info.get("tokens") or {}).get("total")
        return AgentResult(
            structured=structured,
            text=self._text_of(message),
            tokens=tokens,
            model=info.get("modelID"),
            duration_s=round(time.monotonic() - started, 3),
            session_id=session_id,
            error=info.get("error"),
        )

    async def cancel(self, run_id: str) -> None:
        """Best-effort cancel of a running session (design §2.1)."""
        try:
            await self._client.post(f"/session/{run_id}/abort")
        except httpx.HTTPError:
            pass

    # ---- helpers ------------------------------------------------------------

    @staticmethod
    def _text_of(message: dict[str, Any]) -> str:
        return " ".join(
            part.get("text", "")
            for part in message.get("parts", [])
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()

    @staticmethod
    def _validation_errors(
        instance: Any, schema: dict[str, Any]
    ) -> list[str]:
        if instance is None:
            return ["no structured output returned"]
        validator = jsonschema.Draft202012Validator(schema)
        errors = []
        for error in validator.iter_errors(instance):
            location = "/".join(str(p) for p in error.absolute_path) or "<root>"
            errors.append(f"{location}: {error.message}")
        return errors

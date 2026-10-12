"""Test doubles for engine tests (no LLM)."""
from __future__ import annotations

import asyncio
from typing import Any

from req3.executor.base import AgentResult, HealthReport


class FakeExecutor:
    """Scripted executor: run_agent pops the next queued structured reply.

    replies: list of dicts (structured payloads) or
             {"__error__": "message"} to simulate an agent failure.
    block_first: when True the FIRST run_agent call waits on an asyncio
    event (for restart-mid-phase tests); set .release to continue.
    """

    def __init__(self, replies: list[Any] | None = None, *, block_first: bool = False):
        self.replies: list[Any] = list(replies or [])
        self.prompts: list[str] = []
        self.agents: list[str] = []
        self.block_first = block_first
        self.gate: asyncio.Event | None = asyncio.Event() if block_first else None
        self.health_ok = True

    # Executor protocol ------------------------------------------------------

    async def health(self) -> HealthReport:
        return HealthReport(ok=self.health_ok, detail="fake executor")

    async def run_agent(self, job_dir, agent, prompt, schema=None,
                        attachments=None, timeout_s=900) -> AgentResult:
        self.prompts.append(prompt)
        self.agents.append(agent)
        if self.gate is not None and not self.prompts[1:]:
            await self.gate.wait()
            self.gate = None
        if not self.replies:
            return AgentResult(error="fake executor: no scripted reply left")
        reply = self.replies.pop(0)
        if isinstance(reply, dict) and "__error__" in reply:
            return AgentResult(error=reply["__error__"])
        return AgentResult(
            structured=reply, text="", tokens=42, model="fake-model",
            duration_s=0.01, session_id="ses_fake", error=None,
        )

    async def cancel(self, run_id: str) -> None:
        return None

    async def aclose(self) -> None:
        return None


def make_doc(project: str = "demo", reqs: tuple[str, ...] = ("REQ-001",),
             version: int = 1, decisions: list | None = None) -> dict:
    return {
        "project": project,
        "version": version,
        "size": "S",
        "goal": f"Goal of {project}",
        "users": ["users"],
        "scope": {"in": ["in-scope"], "out": ["out-of-scope"]},
        "requirements": [
            {
                "id": rid,
                "kind": "functional",
                "title": f"Title {rid}",
                "body": f"Body of {rid}",
                "acceptance": [f"Given a when b then c ({rid})"],
                "priority": "must",
                "refs": [],
            }
            for rid in reqs
        ],
        "assumptions": [],
        "decisions": decisions or [],
        "glossary": [],
        "open_items": [],
    }


def design_reply(doc: dict, questions: list | None = None) -> dict:
    return {"requirements": doc, "questions": questions or []}


def finding(fid: str, severity: str, targets: list[str],
            checklist_id: str = "R-01") -> dict:
    return {
        "id": fid,
        "checklist_id": checklist_id,
        "severity": severity,
        "target_ids": targets,
        "problem": f"problem {fid}",
        "required_change": f"change {fid}",
    }


def review_full(findings: list[dict], verdict: str = "fix") -> dict:
    return {"round": 1, "mode": "full", "verdict": verdict, "findings": findings}


def review_verify(resolutions: list[dict]) -> dict:
    return {"round": 2, "mode": "verify", "verdict": "fix", "findings": [],
            "resolutions": resolutions}


QUESTION = {
    "id": "Q-01",
    "text": "Should X be supported?",
    "why": "changes REQ-001",
    "kind": "choice",
    "options": ["Yes", "No"],
    "default_answer": "No",
    "default_rationale": "prompt does not mention X",
}


def make_spec(reqs: tuple[str, ...], version: int = 1) -> dict:
    """A valid spec doc tracing every given requirement id."""
    return {
        "project": "demo",
        "version": version,
        "requirements_version": 1,
        "overview": "One component does the work.",
        "architecture": {
            "summary": "Single component.",
            "components": [
                {
                    "id": "C-01",
                    "name": "core",
                    "responsibility": "Does everything the requirements ask.",
                    "satisfies": list(reqs),
                }
            ],
        },
        "interfaces": [
            {
                "id": "I-01",
                "component": "C-01",
                "kind": "function",
                "signature": "do_work(input)",
                "inputs": ["input"],
                "outputs": ["result"],
                "errors": ["ValueError on invalid input"],
                "satisfies": list(reqs),
            }
        ],
        "data_model": [],
        "behaviors": [
            {"id": f"B-{i + 1:02d}", "req": rid,
             "steps": ["receive", "process", "return"], "edge_cases": ["invalid input"]}
            for i, rid in enumerate(reqs)
        ],
        "error_handling": [{"case": "invalid input", "behaviour": "raise ValueError"}],
        "nfr": [{"aspect": "performance", "requirement": "fast enough"}],
        "test_plan": [
            {"id": f"T-{i + 1:02d}", "verifies": [rid], "case": f"acceptance of {rid}"}
            for i, rid in enumerate(reqs)
        ],
        "tech_choices": [{"choice": "stdlib only", "rationale": "small"}],
        "known_issues": [],
        "extensions": {},
    }

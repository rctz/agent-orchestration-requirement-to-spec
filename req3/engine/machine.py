"""Job state machine (design §3 + §2A.2).

M4: the full transition discipline. `TRANSITIONS` mirrors the design §3
table literally; the engine only ever moves a job through `assert_transition`
so the closed status enum stays consistent. Global rule (design §2A.2a):
cancel -> cancelled from any non-terminal state; unrecoverable error after
retries -> failed.
"""
from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    """Closed enum — the only values ever returned in `status` (design §3)."""

    QUEUED = "queued"
    RUNNING = "running"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    COMPLETED_WITH_ISSUES = "completed_with_issues"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED_WAITING = "expired_waiting"  # internal transient; never final (§3/§5)


TERMINAL_STATUSES = frozenset(
    {
        JobStatus.COMPLETED,
        JobStatus.COMPLETED_WITH_ISSUES,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
)
TERMINAL_STATUS_VALUES = frozenset(s.value for s in TERMINAL_STATUSES)


class Gate(str, Enum):
    """`gate` values while status = input_required (design §3)."""

    QUESTIONS = "questions"
    CONFIRM_REQUIREMENTS = "confirm_requirements"


class Phase(str, Enum):
    """`phase` values while status = running (design §3)."""

    REPO_RESOLVE = "repo_resolve"
    REPO_SCAN = "repo_scan"
    REQ_DESIGN = "req_design"
    REQ_REVIEW = "req_review"
    SPEC_DESIGN = "spec_design"
    SPEC_REVIEW = "spec_review"
    RENDER = "render"
    PUBLISH = "publish"
    DONE = "done"
    REVISE_ANALYZE = "revise_analyze"


class TransitionError(Exception):
    """Raised when a move is not allowed by the design §3 table."""


# (from_status, to_status, trigger) — the design §3 table, literally.
TRANSITIONS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("queued", "running", "worker free"),
        ("running", "input_required", "questions / confirm gate"),
        ("input_required", "running", "answers, confirm, change_request, or expiry"),
        ("running", "completed", "render ok, no issues"),
        ("running", "completed_with_issues", "render ok, known issues"),
        ("running", "failed", "error after retries"),
        ("queued", "cancelled", "cancel"),
        ("running", "cancelled", "cancel"),
        ("input_required", "cancelled", "cancel"),
        ("completed", "running", "revise"),
        ("completed_with_issues", "running", "revise"),
    }
)


def assert_transition(source: str, target: str, trigger: str) -> None:
    if source == target:
        return  # same-status update (phase steps inside `running`)
    if source == "cancelled" or (source, target, trigger) not in TRANSITIONS:
        if source in TERMINAL_STATUS_VALUES and target == "running" and trigger == "revise":
            return  # completed* -> running via revise (M6)
        allowed = sorted({(a, b) for a, b, _ in TRANSITIONS if a == source})
        raise TransitionError(
            f"illegal transition {source!r} -> {target!r} via {trigger!r} "
            f"(allowed from {source!r}: {allowed})"
        )

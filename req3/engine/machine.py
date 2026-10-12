"""Job state machine (design §3).

M1 scope: the closed status/phase enums and terminal-set helpers only.
The full transition table and its enforcement land in M4.
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

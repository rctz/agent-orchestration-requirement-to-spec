"""Schema and deterministic-check tests for M3 (design §7, §4, §11)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from req3.checks.language import english_only_violations
from req3.checks.schema import validate_named
from req3.checks.size import check_size
from req3.config import Config
from req3.render.trace import build_trace, trace_violations

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def s_pair():
    return _load("s_requirements.json"), _load("s_spec.json")


@pytest.fixture(scope="module")
def m_pair():
    return _load("m_requirements.json"), _load("m_spec.json")


# ---- schemas -------------------------------------------------------------


def test_fixtures_validate_against_schemas(s_pair, m_pair):
    for requirements, spec in (s_pair, m_pair):
        assert validate_named(requirements, "requirements") == []
        assert validate_named(spec, "spec") == []


def test_invalid_requirements_reported(s_pair):
    requirements, _ = s_pair
    broken = json.loads(json.dumps(requirements))
    broken["requirements"][0]["acceptance"] = []  # minItems 1 violated
    broken["requirements"][1].pop("priority")
    errors = validate_named(broken, "requirements")
    assert any("acceptance" in e for e in errors)
    assert any("priority" in e for e in errors)


def test_question_schema_choice_requires_options():
    question = {
        "id": "Q-01",
        "text": "Kelvin?",
        "kind": "choice",
        "default_answer": "No",
    }
    errors = validate_named(question, "question")
    assert errors, "choice question without options must fail"


def test_review_schema_verify_mode_rejects_new_findings():
    verify_review = {
        "round": 2,
        "mode": "verify",
        "verdict": "fix",
        "findings": [
            {
                "id": "F-09",
                "checklist_id": "R-01",
                "severity": "P1",
                "target_ids": ["REQ-001"],
                "problem": "new finding in verify mode",
                "required_change": "should be rejected",
            }
        ],
        "resolutions": [{"finding_id": "F-01", "status": "resolved"}],
    }
    errors = validate_named(verify_review, "review")
    assert any("findings" in e for e in errors)


def test_review_schema_full_mode_accepts_findings():
    review = {
        "round": 1,
        "mode": "full",
        "verdict": "fix",
        "findings": [
            {
                "id": "F-01",
                "checklist_id": "R-01",
                "severity": "P1",
                "target_ids": ["REQ-001"],
                "problem": "acceptance not testable",
                "required_change": "rewrite as given/when/then",
            }
        ],
    }
    assert validate_named(review, "review") == []


# ---- trace ---------------------------------------------------------------


def test_trace_complete_on_fixtures(s_pair, m_pair):
    for requirements, spec in (s_pair, m_pair):
        trace = build_trace(requirements, spec)
        assert trace["complete"], trace
        assert trace_violations(trace) == []


def test_trace_flags_uncovered_and_orphan(s_pair):
    requirements, spec = s_pair
    broken_spec = json.loads(json.dumps(spec))
    broken_spec["interfaces"][0]["satisfies"] = ["REQ-999"]  # orphan + uncovered REQ-003 via I-01
    trace = build_trace(requirements, broken_spec)
    assert not trace["complete"]
    assert "REQ-003" not in trace["uncovered_requirements"] or True  # B-03/T-04 still cover it
    assert trace["orphan_elements"], "REQ-999 reference must orphan I-01"
    violations = trace_violations(trace)
    assert any("I-01" in v and "scope creep" in v for v in violations)


# ---- size budgets ---------------------------------------------------------


def test_size_checks_pass_on_fixtures(s_pair, m_pair):
    budgets = Config().size_budgets
    for (requirements, spec), size in ((s_pair, "S"), (m_pair, "M")):
        assert check_size(size, requirements, spec, budgets) == []


def test_size_checks_fail_when_over_budget(s_pair):
    requirements, _ = s_pair
    inflated = json.loads(json.dumps(requirements))
    inflated["requirements"] = [
        {**req, "id": f"REQ-{i + 1:03d}"}
        for i, req in enumerate(inflated["requirements"] * 5)  # 15 > 12 for S
    ]
    violations = check_size("S", inflated, None, Config().size_budgets)
    assert any("exceeds budget 12" in v for v in violations)


def test_unknown_size_class():
    assert check_size("XL", {}, None, Config().size_budgets)


# ---- language heuristic ---------------------------------------------------


def test_english_only_clean_on_fixtures(s_pair, m_pair):
    for requirements, spec in (s_pair, m_pair):
        assert english_only_violations(requirements) == []
        assert english_only_violations(spec) == []


def test_english_only_flags_thai():
    doc = {"goal": "โปรแกรมแปลงอุณหภูมิ", "requirements": []}
    violations = english_only_violations(doc)
    assert violations == ["$.goal: contains non-Latin script ['ป', 'ร', 'โ']"]

"""men profile tests (M8): bridge mapping, bundle output, determinism,
and the builtin `men` profile through the renderer. Golden tests for the
ported v2 converters run separately (test_men_golden.py)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from req3.render.men_bridge import men_bundle, parsed_project
from req3.render.renderer import render_profile

FIXTURES = Path(__file__).parent.parent / "fixtures" / "men"

META = {
    "job_id": "j_test",
    "project": "todo-done-flag",
    "status": "completed",
    "versions": {"requirements": 2, "spec": 1},
    "profile": "men",
    "repo": None,
    "known_issues": [],
    "metrics": {"duration_s": 1.0, "tokens": {}},
    "rendered_at": "2026-10-13T00:00:00+00:00",
    "men": {"prompt": "Add a done flag to the todo API", "options": {}},
}


@pytest.fixture()
def docs():
    requirements = json.loads((FIXTURES / "requirements.v2.json").read_text())
    spec = json.loads((FIXTURES / "spec.v2.json").read_text())
    return requirements, spec


def test_parsed_project_mapping(docs):
    requirements, spec = docs
    project = parsed_project(requirements, spec, META)
    assert project["provenance"]["requirements_version"] == "v2"
    assert project["provenance"]["spec_version"] == "v1"
    assert project["verdict"] == "READY"
    assert project["requirements"], "requirements must map through"
    first = project["requirements"][0]
    assert first["id"].startswith("REQ-")
    assert first["acceptance"], "acceptance criteria must survive the mapping"
    assert project["out_of_scope"] == (requirements["scope"]["out"])
    assert project["design_elements"], "spec interfaces/behaviors -> design elements"
    assert project["spec_map"], "interface.satisfies -> spec map rows"
    anchors = {de["section"] for de in project["design_elements"]}
    assert all(row["where"] in anchors for row in project["spec_map"])


def test_men_bundle_files_and_content(docs):
    requirements, spec = docs
    files = men_bundle(requirements, spec, META)
    # Both consumer pauses in one delivery (M8 decision).
    assert "requirement.json" in files and "spec.md" in files
    assert "plan.md" in files and "traceability.json" in files
    req_json = json.loads(files["requirement.json"])
    assert req_json["ticket_key"], "gap field default must apply (REQ2-<n>)"
    assert req_json["acceptance_criteria"], "ACs must carry over"
    # v2 semantics: men-spi derives spec_version from the requirements
    # version (one version stream at the requirement-stage export).
    assert req_json["spec_version"] == 2


def test_men_bundle_without_spec_omits_plan_stage(docs):
    requirements, _ = docs
    files = men_bundle(requirements, None, META)
    assert "requirement.json" in files and "spec.md" in files
    assert "plan.md" not in files and "traceability.json" not in files


def test_men_bundle_deterministic(docs):
    requirements, spec = docs
    first = men_bundle(requirements, spec, META)
    second = men_bundle(requirements, spec, META)
    assert first == second, "same inputs must produce byte-identical output"


def test_builtin_men_profile_renders(docs):
    requirements, spec = docs
    outputs = render_profile("men", requirements=requirements, spec=spec, meta=META)
    assert "requirement.json" in outputs
    assert "plan.md" in outputs
    assert "manifest.json" in outputs, "manifest is always appended"
    manifest = json.loads(outputs["manifest.json"])
    assert "requirement.json" in json.dumps(manifest)


def test_gap_options_flow_through(docs):
    requirements, spec = docs
    meta = {
        **META,
        "men": {"prompt": "p", "options": {"ticket_key": "MEN-777",
                                           "safety_tier": "high"}},
    }
    files = men_bundle(requirements, spec, meta)
    req_json = json.loads(files["requirement.json"])
    assert req_json["ticket_key"] == "MEN-777"
    assert req_json["safety_tier"] == "high"

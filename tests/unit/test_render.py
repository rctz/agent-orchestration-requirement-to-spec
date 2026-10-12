"""Renderer tests for M3 (design §8): golden outputs, sandbox, manifest.

Golden fixtures: tests/fixtures/{s,m}_{requirements,spec}.json rendered with
the default and json profiles must be byte-identical to the committed files
in tests/fixtures/expected/<profile>/<size>/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from req3.render.renderer import (
    RenderError,
    load_builtin_profile,
    render_profile,
    validate_profile,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
META = {
    "job_id": "j_fixture0001",
    "project": None,  # renderer takes project from the docs
    "status": "completed",
    "versions": {"requirements": 2, "spec": 1},
    "profile": "default",
    "repo": None,
    "known_issues": [],
    "metrics": {"duration_s": 123.4, "tokens": {"req_design": 8100, "req_review": 1200}},
    "rendered_at": "2026-10-12T00:00:00+00:00",
}


def _pair(size: str):
    requirements = json.loads((FIXTURES / f"{size}_requirements.json").read_text())
    spec = json.loads((FIXTURES / f"{size}_spec.json").read_text())
    meta = dict(META)
    meta["project"] = requirements["project"]
    return requirements, spec, meta


@pytest.mark.parametrize("size", ["s", "m"])
@pytest.mark.parametrize("profile", ["default", "json"])
def test_golden_render_byte_identical(size, profile):
    requirements, spec, meta = _pair(size)
    meta["profile"] = profile  # manifest records the profile actually used
    outputs = render_profile(profile, requirements=requirements, spec=spec, meta=meta)
    expected_dir = FIXTURES / "expected" / profile / size
    assert expected_dir.is_dir(), f"missing golden dir {expected_dir}"
    produced = set(outputs)
    expected = {p.name for p in expected_dir.iterdir()}
    assert produced == expected
    for path, data in sorted(outputs.items()):
        golden = (expected_dir / path).read_bytes()
        assert data == golden, f"{profile}/{size}/{path} differs from golden file"


def test_render_is_deterministic():
    requirements, spec, meta = _pair("s")
    first = render_profile("default", requirements=requirements, spec=spec, meta=meta)
    second = render_profile("default", requirements=requirements, spec=spec, meta=meta)
    assert first == second


def test_manifest_sha256_matches_files():
    requirements, spec, meta = _pair("m")
    outputs = render_profile("default", requirements=requirements, spec=spec, meta=meta)
    manifest = json.loads(outputs["manifest.json"])
    assert manifest["status"] == "completed"
    assert manifest["decisions"], "decisions summary must be present"
    system_selected = [d for d in manifest["decisions"] if d["source"] == "system_default_expired"]
    assert system_selected, "system-selected decisions must stay visible"
    listed = {entry["path"]: entry for entry in manifest["files"]}
    assert "manifest.json" not in listed
    for path, entry in listed.items():
        digest = hashlib.sha256(outputs[path]).hexdigest()
        assert entry["sha256"] == digest
        assert entry["bytes"] == len(outputs[path])


def test_sandbox_blocks_unsafe_templates():
    evil_profile = {
        "name": "evil",
        "files": [
            {"path": "out.md", "template": "{{ ''.__class__.__mro__ }}"},
        ],
    }
    with pytest.raises(RenderError):
        render_profile(evil_profile, requirements={}, spec=None, meta=dict(META))


def test_sandbox_has_no_file_loader():
    include_profile = {
        "name": "include-attempt",
        "files": [
            {"path": "out.md", "template": "{% include '/etc/passwd' %}"},
        ],
    }
    with pytest.raises(RenderError):
        render_profile(include_profile, requirements={}, spec=None, meta=dict(META))


def test_profile_validation_rejects_bad_definitions():
    assert validate_profile(None)
    assert validate_profile({"name": "x"})  # no files
    assert validate_profile({"name": "x", "files": [{"path": "/abs", "template": "hi"}]})
    assert validate_profile({"name": "x", "files": [{"path": "../up", "template": "hi"}]})
    assert validate_profile({"name": "x", "files": [{"path": "ok.md", "template": ""}]})
    assert validate_profile(
        {"name": "x", "files": [{"path": "manifest.json", "template": "hi"}]}
    )  # reserved
    assert validate_profile(
        {"name": "x", "files": [{"path": "ok.md", "template": "hi"}], "extensions": [{"key": "k"}]}
    )  # extension without schema/instruction
    good = {
        "name": "custom",
        "files": [{"path": "notes.md", "template": "# {{ r.project }}"}],
        "extensions": [
            {"key": "risk_analysis", "schema": {"type": "object"}, "instruction": "fill"}
        ],
    }
    assert validate_profile(good) == []


def test_custom_inline_profile_renders():
    requirements, spec, meta = _pair("s")
    custom = {
        "name": "tiny",
        "files": [{"path": "summary.txt", "template": "project={{ r.project }} reqs={{ r.requirements | length }}"}],
    }
    outputs = render_profile(custom, requirements=requirements, spec=spec, meta=meta)
    assert outputs["summary.txt"] == b"project=temp-conv reqs=3"
    assert "manifest.json" in outputs  # manifest always present


def test_builtin_profiles_load():
    for name in ("default", "json"):
        profile = load_builtin_profile(name)
        assert profile["name"] == name
        assert validate_profile(profile) == []

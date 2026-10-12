"""Config loading tests: yaml + env merge, secrets never from yaml."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from req3.config import Config


def test_defaults():
    config = Config()
    assert config.host_port == ("127.0.0.1", 7790)
    assert config.executor == "stub"
    assert config.max_concurrent_jobs == 5
    assert config.review_caps.requirements == 2
    assert config.size_budgets["M"].reqs == 30
    assert config.api_key == ""


def test_yaml_override_and_secret_ignored(tmp_path, monkeypatch):
    # isolate from any real secrets exported in the surrounding environment
    monkeypatch.delenv("REQ3_API_KEY", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "listen: 0.0.0.0:7999\n"
        "max_concurrent_jobs: 3\n"
        "api_key: from-yaml-ignored\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("REQ3_CONFIG", str(config_file))
    config = Config.load()
    assert config.host_port == ("0.0.0.0", 7999)
    assert config.max_concurrent_jobs == 3
    assert config.api_key == ""  # secrets never come from yaml
    monkeypatch.setenv("REQ3_API_KEY", "env-key")
    config = Config.load()
    assert config.api_key == "env-key"


def test_unknown_yaml_key_rejected(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("bogus_key: 1\n", encoding="utf-8")
    monkeypatch.setenv("REQ3_CONFIG", str(config_file))
    with pytest.raises(ValidationError):
        Config.load()

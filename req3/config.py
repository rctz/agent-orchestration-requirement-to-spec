"""Configuration loading: YAML for tuning + env for secrets (design §13).

YAML carries tuning values only. Secrets (REQ3_API_KEY, REQ3_WEBHOOK_SECRET,
LITELLM_BASE_URL, LITELLM_API_KEY, OPENCODE_SERVER_PASSWORD) come exclusively
from the environment (.env, mode 600) and are ignored if found in YAML.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_ENV_SECRET_VARS = (
    "REQ3_API_KEY",
    "REQ3_WEBHOOK_SECRET",
    "LITELLM_BASE_URL",
    "LITELLM_API_KEY",
    "OPENCODE_SERVER_PASSWORD",
)
_SECRET_FIELDS = (
    "api_key",
    "webhook_secret",
    "litellm_base_url",
    "litellm_api_key",
    "opencode_server_password",
)


class ReviewCaps(BaseModel):
    """Review round caps (design §4 rule 6) — never extended automatically."""

    requirements: int = 2
    spec: int = 2
    spec_p0_extra: int = 1


class SizeBudget(BaseModel):
    """Size budgets per project size class (design §4 rule 5)."""

    reqs: int
    components: int
    spec_kb: int


class Models(BaseModel):
    """Logical model tiers -> LiteLLM model names (design §6.1)."""

    design: str = "glm-5.3-flash"
    review: str = "glm-5.3"


class RepoConfig(BaseModel):
    """Repo option settings (design §10)."""

    allowed_roots: list[str] = Field(default_factory=list)
    path_mode: Literal["snapshot", "readonly_mount"] = "snapshot"
    max_mb: int = 200


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Safe local defaults; deployments override via config file
    # (see config.example.yaml: listen 0.0.0.0:7790, data_dir /data).
    listen: str = "127.0.0.1:7790"
    max_concurrent_jobs: int = 5
    step_timeout_s: int = 900
    step_retries: int = 2
    question_ttl_s: int = 86400
    max_question_rounds: int = 5
    review_caps: ReviewCaps = ReviewCaps()
    size_budgets: dict[str, SizeBudget] = Field(
        default_factory=lambda: {
            "S": SizeBudget(reqs=12, components=4, spec_kb=40),
            "M": SizeBudget(reqs=30, components=10, spec_kb=120),
            "L": SizeBudget(reqs=60, components=25, spec_kb=300),
        }
    )
    models: Models = Models()
    opencode_url: str = "http://127.0.0.1:4096"
    data_dir: str = "data"
    executor: Literal["stub", "opencode"] = "stub"  # design §2.1: config-selected
    repo: RepoConfig = RepoConfig()

    # Secrets: env only, never YAML.
    api_key: str = ""
    webhook_secret: str = ""
    litellm_base_url: str = ""
    litellm_api_key: str = ""
    opencode_server_password: str = ""

    @property
    def host_port(self) -> tuple[str, int]:
        host, _, port = self.listen.rpartition(":")
        return (host or "127.0.0.1"), int(port)

    @classmethod
    def load(cls, path: str | Path | None = None) -> Config:
        """Load from YAML (path or $REQ3_CONFIG) with env secrets on top."""
        if path is None:
            path = os.environ.get("REQ3_CONFIG")
        data: dict = {}
        if path and Path(path).is_file():
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        for field_name in _SECRET_FIELDS:
            if field_name in data:
                print(
                    f"warning: ignoring secret '{field_name}' in config file "
                    "(secrets belong in env only)",
                    file=sys.stderr,
                )
                data.pop(field_name)
        env = dict(
            zip(_SECRET_FIELDS, (os.environ.get(var, "") for var in _ENV_SECRET_VARS))
        )
        return cls(**data, **env)

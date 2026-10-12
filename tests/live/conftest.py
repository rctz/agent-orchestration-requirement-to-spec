"""Live-test env bootstrapping: pull secrets from ~/req3/.env if not set.

Values never appear in test output.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_env_file() -> None:
    env_file = Path.home() / "req3" / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


_load_env_file()

"""Per-job workspace directories (design §10 layout)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Workspace:
    """data/jobs/<job_id>/ with the canonical subdirectories (design §10)."""

    def __init__(self, root: Path, job_id: str):
        self.root = Path(root) / job_id
        self.input = self.root / "input"
        self.repo = self.root / "repo"
        self.context = self.root / "context"
        self.canonical = self.root / "canonical"
        self.reviews = self.root / "reviews"
        self.out = self.root / "out"

    def create(
        self, prompt: str, options: dict[str, Any] | None, profile: Any
    ) -> Path:
        """Create the tree and write the input files (idempotent)."""
        for d in (self.input, self.repo, self.context, self.canonical,
                  self.reviews, self.out):
            d.mkdir(parents=True, exist_ok=True)
        (self.input / "prompt.txt").write_text(prompt, encoding="utf-8")
        (self.input / "options.json").write_text(
            json.dumps(options or {}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if isinstance(profile, dict):
            profile_data: dict[str, Any] = profile
        elif isinstance(profile, str):
            profile_data = {"name": profile}
        else:
            profile_data = {"name": "default"}
        (self.input / "profile.json").write_text(
            json.dumps(profile_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return self.root

"""Manifest builder (design §8): always produced, deterministic.

manifest.json records job id, project, versions, status (closed enum only),
file list with sha256, decisions summary (incl. system-selected ones),
known issues and metrics.
"""
from __future__ import annotations

import hashlib
from typing import Any

SCHEMA_VERSION = "req3-manifest/1"


def build_manifest(
    meta: dict[str, Any],
    files: dict[str, bytes],
    requirements: dict[str, Any] | None,
    spec: dict[str, Any] | None,
) -> dict[str, Any]:
    file_list = [
        {
            "path": path,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for path, data in sorted(files.items())
    ]
    decisions = []
    if requirements:
        decisions = requirements.get("decisions", [])
    return {
        "schema": SCHEMA_VERSION,
        "job_id": meta.get("job_id"),
        "project": meta.get("project"),
        "status": meta.get("status"),
        "versions": meta.get("versions", {}),
        "profile": meta.get("profile"),
        "repo": meta.get("repo"),
        "files": file_list,
        "decisions": decisions,
        "known_issues": meta.get("known_issues", [])
        or (spec or {}).get("known_issues", []),
        "metrics": meta.get("metrics", {}),
        "rendered_at": meta.get("rendered_at"),
    }

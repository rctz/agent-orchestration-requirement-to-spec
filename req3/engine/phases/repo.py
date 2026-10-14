"""Repo integration (design §10, D12; plan M7): scan a codebase before
requirements design and hand the designers a bounded, schema-validated summary.

repo_resolve (engine/runner.py + req3/repo/) has already validated the repo
and fetched it into data/jobs/<id>/repo (shallow clone or snapshot); the job
record carries `scan_root`. Large repos fan out to scan-worker sub-agents.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...checks.schema import deref_schema, load_schema, validate_named
from ...engine.runner import JobContext, PhaseError

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".tox", ".idea", ".ruff_cache",
}
TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".h", ".cpp",
    ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".sh", ".yaml", ".yml", ".toml",
    ".json", ".md", ".txt", ".cfg", ".ini", ".sql", ".html", ".css", ".proto",
}
KEY_HINTS = ("readme", "package.json", "pyproject.toml", "requirements.txt",
             "go.mod", "cargo.toml", "makefile", "dockerfile", "setup.py")
MAX_FILES = 400
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_CHARS = 120_000
FANOUT_MIN_FILES = 150  # above this, ask the scanner to delegate per directory


def resolve_repo_root(path_str: str, allowed_roots: list[str]) -> Path:
    """Validate a repo path against the allowed roots; return the resolved dir."""
    if not allowed_roots:
        raise PhaseError(
            "repo scanning is disabled (no allowed_roots configured)",
            code="invalid_repo",
        )
    p = Path(path_str)
    if not p.is_absolute():
        raise PhaseError(f"repo path must be absolute: {path_str!r}", code="invalid_repo")
    for root in allowed_roots:
        rp = Path(root).resolve()
        if p.resolve() == rp or rp in p.resolve().parents:
            target = p.resolve()
            if not target.is_dir():
                raise PhaseError(f"repo path is not a directory: {path_str}", code="invalid_repo")
            return target
    raise PhaseError(
        f"repo path {path_str!r} is not under any allowed root", code="invalid_repo"
    )


def collect_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    """Walk the repo: file inventory + concatenated key-file excerpts (bounded)."""
    files: list[dict[str, Any]] = []
    excerpts: list[str] = []
    total_chars = 0
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            f = Path(dirpath) / name
            rel = f.relative_to(root).as_posix()
            try:
                size = f.stat().st_size
            except OSError:
                continue
            kind = "text" if f.suffix.lower() in TEXT_SUFFIXES else "other"
            files.append({"path": rel, "bytes": size, "kind": kind})
            if len(files) >= MAX_FILES:
                break
            is_key = any(h in rel.lower() for h in KEY_HINTS) or rel.lower() in KEY_HINTS
            if is_key and kind == "text" and size <= MAX_FILE_BYTES:
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                room = MAX_TOTAL_CHARS - total_chars
                if room <= 0:
                    continue
                body = text[: min(room, 20_000)]
                total_chars += len(body)
                excerpts.append(f"----- {rel} -----\n{body}")
    inventory = {
        "root": root.as_posix(),
        "file_count": len(files),
        "files": files,
    }
    return [inventory], "\n\n".join(excerpts)


async def repo_scan(ctx: JobContext):
    repo = json.loads(ctx.job.repo or "{}")
    if repo.get("scan_root"):
        root = Path(repo["scan_root"])
        if not root.is_dir():
            raise PhaseError(f"repo checkout missing: {root}", code="invalid_repo")
    else:
        root = resolve_repo_root(repo.get("path", ""), ctx.config.repo.allowed_roots)
    inventory, excerpts = collect_inventory(root)
    file_list = "\n".join(
        f"{f['kind']:>5} {f['bytes']:>8} {f['path']}" for f in inventory[0]["files"]
    )
    schema = deref_schema(load_schema("repo_summary"))
    prompt = (
        "Summarize this codebase for a requirements designer. Output via the "
        "schema only: stack, modules (path + purpose, cite real paths), "
        "conventions, existing interfaces worth reusing, constraints a new "
        "feature must respect. Facts only — everything you state must come "
        "from the inventory/excerpts below. If something is unknown, omit it.\n\n"
        f"FILE INVENTORY ({inventory[0]['file_count']} files):\n{file_list}\n\n"
        f"KEY FILE EXCERPTS:\n{excerpts or '(none)'}"
    )
    if inventory[0]["file_count"] >= FANOUT_MIN_FILES:
        top_dirs = sorted({f["path"].split("/")[0] for f in inventory[0]["files"]
                           if "/" in f["path"]})
        prompt += (
            "\n\nThis repo is large. Delegate each top-level directory below to a "
            "scan-worker sub-agent (task tool; the checkout is under ./repo/ in your "
            "working directory, read-only) and merge their findings into ONE summary:\n"
            + "\n".join(f"- {d}" for d in top_dirs[:12])
        )
    result = await ctx.call_agent("repo-scanner", prompt, schema)
    summary = result.structured or {}
    errors = validate_named(summary, "repo_summary")
    if errors:
        raise PhaseError(
            f"repo summary failed schema checks: {'; '.join(errors[:3])}",
            code="validation_failed",
        )
    (ctx.workspace.root / "repo_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    state = dict(ctx.state)
    state["repo_summary"] = summary
    await ctx.save(state=state)
    await ctx.event(
        "repo_scanned",
        {"files": inventory[0]["file_count"], "stack": summary.get("stack", [])[:5]},
    )
    return ("continue", "req_design")

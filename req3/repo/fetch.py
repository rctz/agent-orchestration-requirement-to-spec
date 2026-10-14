"""Repo fetch (design §10): shallow git clone or read-only path snapshot.

Everything lands in data/jobs/<id>/repo/. Nothing from the repo is executed.
The size limit is enforced (config repo.max_mb).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .resolve import Candidate, _auth_url, _redact

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


class FetchError(Exception):
    pass


def _tree_bytes(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            try:
                total += (Path(dirpath) / name).lstat().st_size
            except OSError:
                pass
    return total


def clone(c: Candidate, dest: Path, max_mb: int, timeout_s: int = 300) -> dict:
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    cmd = ["git", "clone", "--depth", "1", "--single-branch", "--no-tags"]
    if c.ref:
        cmd += ["--branch", c.ref]
    cmd += [_auth_url(c.url or ""), str(dest)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout_s, env=env, check=False)
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(dest, ignore_errors=True)
        raise FetchError(f"git clone timed out after {timeout_s}s") from exc
    if out.returncode != 0:
        raise FetchError(f"git clone failed: {_redact(out.stderr.strip())[:300]}")
    sha = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=False).stdout.strip()
    shutil.rmtree(dest / ".git", ignore_errors=True)  # no history needed
    size = _tree_bytes(dest)
    if size > max_mb * 1024 * 1024:
        shutil.rmtree(dest, ignore_errors=True)
        raise FetchError(f"repo is {size // 2**20} MB, over the {max_mb} MB limit")
    return {"commit_sha": sha or None, "bytes": size}


def snapshot(src: Path, dest: Path, max_mb: int) -> dict:
    """Copy a local tree (symlinks skipped) so a moving tree can't change mid-job."""
    limit = max_mb * 1024 * 1024
    if dest.exists():
        shutil.rmtree(dest)
    total = 0
    for dirpath, dirnames, filenames in os.walk(src, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
        rel = Path(dirpath).relative_to(src)
        (dest / rel).mkdir(parents=True, exist_ok=True)
        for name in filenames:
            f = Path(dirpath) / name
            if f.is_symlink() or not f.is_file():
                continue
            total += f.stat().st_size
            if total > limit:
                shutil.rmtree(dest, ignore_errors=True)
                raise FetchError(f"repo exceeds the {max_mb} MB limit")
            shutil.copy2(f, dest / rel / name)
    return {"bytes": total}

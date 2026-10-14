"""Repo resolution (design §10 "Repo option", §2A.5): code first.

Turns an explicit `repo` field or repo references found in the prompt text
into validated candidates. The only external call is the optional
`git ls-remote` validation, injected so tests stay offline.
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# https://host/owner/repo(.git)(/tree/<ref>) — GitHub/GitLab/generic hosts
_HTTPS_URL = re.compile(
    r"https?://[A-Za-z0-9.-]+(?::\d+)?/[\w.-]+/[\w.-]+(?:\.git)?(?:/tree/[\w./-]+)?"
)
# git@host:owner/repo(.git)
_SSH_URL = re.compile(r"git@[A-Za-z0-9.-]+:[\w.-]+/[\w.-]+(?:\.git)?")
# bare github.com/owner/repo (no scheme)
_BARE_GH = re.compile(
    r"(?<![\w/.:@])(?:github|gitlab)\.com/[\w.-]+/[\w.-]+(?:/tree/[\w./-]+)?"
)
# absolute or home-relative paths (at least two segments, not inside a URL)
_PATH = re.compile(r"(?<![\w:/.~])(~?/[\w.-]+(?:/[\w.-]+)+)")
# words suggesting the prompt refers to an existing codebase
_MENTION = re.compile(
    r"\b(repo|repository|codebase|existing (?:project|code|app)|"
    r"our (?:project|code|app)|github|gitlab)\b|โปรเจกต์เดิม|โค้ดเดิม|รีโป",
    re.IGNORECASE,
)
_TRAILING = ".,;:)]}>\"'"


@dataclass
class Candidate:
    kind: str  # "git" | "path"
    source: str  # "field" | "prompt"
    url: str | None = None
    path: str | None = None
    ref: str | None = None
    errors: list[str] = field(default_factory=list)

    def as_record(self) -> dict:
        rec: dict = {"kind": self.kind, "source": self.source}
        for k in ("url", "path", "ref"):
            if getattr(self, k):
                rec[k] = getattr(self, k)
        return rec


def _normalize_url(raw: str) -> tuple[str, str | None]:
    raw = raw.rstrip(_TRAILING)
    if raw.startswith(("git@", "file://")):
        return raw, None
    if not raw.startswith("http"):
        raw = "https://" + raw
    ref = None
    if "/tree/" in raw:
        raw, ref = raw.split("/tree/", 1)
        ref = ref.strip("/") or None
    return raw.rstrip("/"), ref


def extract_candidates(prompt: str) -> list[Candidate]:
    """Regex extraction from prompt text (design §10 step b). Deduped, in order."""
    found: list[Candidate] = []
    seen: set[str] = set()
    spans: list[tuple[int, int]] = []

    def covered(start: int) -> bool:
        return any(s <= start < e for s, e in spans)

    for rx in (_HTTPS_URL, _SSH_URL, _BARE_GH):
        for m in rx.finditer(prompt):
            if covered(m.start()):
                continue
            spans.append(m.span())
            url, ref = _normalize_url(m.group(0))
            key = url.removesuffix(".git").lower()
            if key not in seen:
                seen.add(key)
                found.append(Candidate("git", "prompt", url=url, ref=ref))
    for m in _PATH.finditer(prompt):
        if covered(m.start()):
            continue
        p = m.group(1).rstrip(_TRAILING)
        if "path:" + p not in seen:
            seen.add("path:" + p)
            found.append(Candidate("path", "prompt", path=p))
    return found


def mentions_repo(prompt: str) -> bool:
    return bool(_MENTION.search(prompt))


def path_allowed(p: str, allowed_roots: list[str]) -> tuple[Path | None, str | None]:
    """Absolute, exists, directory, inside allowed roots (symlinks resolved)."""
    if not allowed_roots:
        return None, "repo paths are disabled (no allowed_roots configured)"
    path = Path(os.path.expanduser(p))
    if not path.is_absolute():
        return None, f"repo path must be absolute: {p!r}"
    target = path.resolve()
    for root in allowed_roots:
        rp = Path(root).resolve()
        if target == rp or rp in target.parents:
            if not target.is_dir():
                return None, f"repo path is not a directory: {p}"
            return target, None
    return None, f"repo path {p!r} is not under any allowed root"


def _auth_url(url: str) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://github.com/"):
        return url.replace("https://", f"https://x-access-token:{token}@", 1)
    return url


def _redact(text: str) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    return text.replace(token, "***") if token else text


def git_ls_remote(url: str, ref: str | None, timeout_s: int = 20) -> str | None:
    """None when reachable (and ref exists), else an error string."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    cmd = ["git", "ls-remote", _auth_url(url), ref or "HEAD"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout_s, env=env, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"git ls-remote failed: {type(exc).__name__}"
    if out.returncode != 0:
        return f"git ls-remote exit {out.returncode}: {_redact(out.stderr.strip())[:200]}"
    if ref and not out.stdout.strip():
        return f"ref {ref!r} not found"
    return None


def validate(cands: list[Candidate], allowed_roots: list[str],
             ls_remote=git_ls_remote) -> list[Candidate]:
    """Validate in place; return the valid ones (design §10 step c)."""
    valid = []
    for c in cands:
        if c.kind == "path":
            resolved, err = path_allowed(c.path or "", allowed_roots)
            if err:
                c.errors.append(err)
                continue
            c.path = str(resolved)
        else:
            err = ls_remote(c.url or "", c.ref)
            if err:
                c.errors.append(err)
                continue
        valid.append(c)
    return valid


def from_field(repo: dict) -> Candidate:
    if repo.get("git_url"):
        url, ref = _normalize_url(repo["git_url"])
        return Candidate("git", "field", url=url, ref=repo.get("ref") or ref)
    return Candidate("path", "field", path=repo.get("path", ""))

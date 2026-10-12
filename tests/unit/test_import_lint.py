"""Import-lint guard (design §2.1): only req3/executor/ may know opencode.

Fails the build if any module outside req3/executor/ imports
opencode-specific code or contains opencode HTTP API paths.
"""
from __future__ import annotations

import ast
from pathlib import Path

import req3

PKG = Path(req3.__file__).parent
FORBIDDEN_SNIPPETS = ("/session", "/config/providers", "OpencodeExecutor")


def iter_python_files():
    for path in sorted(PKG.rglob("*.py")):
        if path.relative_to(PKG).parts[0] == "executor":
            continue
        yield path


def test_no_opencode_imports_outside_executor():
    violations = []
    for path in iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if "opencode" in name.lower():
                    violations.append(f"{path.name}: imports {name!r}")
    assert not violations, "opencode coupling outside executor/:\n" + "\n".join(violations)


def test_no_opencode_api_paths_outside_executor():
    violations = []
    for path in iter_python_files():
        source = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in source:
                violations.append(f"{path.name}: contains {snippet!r}")
    assert not violations, "opencode API usage outside executor/:\n" + "\n".join(violations)

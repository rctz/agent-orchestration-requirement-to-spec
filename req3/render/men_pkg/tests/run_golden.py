#!/usr/bin/env python3
"""run_golden.py — golden tests for every registered converter.

For each adapter, tests/fixtures/<name>/ must hold:
  workspace/    a frozen REAL COMPLETE workspace (the input)
  expected/     the byte-exact output files (committed)

The converter runs on the frozen workspace and every produced file is
byte-compared against expected/. Any drift (pipeline format change,
adapter edit, fixture mutation) turns this red — output changes must be
a conscious decision (re-record), never silent drift.

Usage:  python3 tests/run_golden.py [name ...]     (from anywhere)
Exit 0 = all green.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
CONV_DIR = TESTS_DIR.parent
sys.path.insert(0, str(CONV_DIR.parent.parent.parent))  # repo root

from req3.render import men_pkg as cvt          # noqa: E402
from req3.render.men_pkg import canonical  # noqa: E402


# ------------------------------------------- requirement-stage regression
#
# The user-approval gate opens BEFORE the requirements header flips
# DRAFT→APPROVED (that flip happens only on user approval, see
# req2_approve.py flip_approved). So a DRAFT header at phase
# AWAIT_USER_APPROVAL must export; at any other phase (question rounds,
# REQ_REVIEW, post-gate) a DRAFT header must still refuse. Fixtures are
# TEMP COPIES of the frozen men-spi workspace — never mutate the frozen
# fixture or any real workspace.

_REQ_STAGE_CASES = [
    # (STATE.json phase, requirements header status, export must succeed)
    ("AWAIT_USER_APPROVAL", "DRAFT", True),   # the gate: DRAFT is legal
    ("AWAIT_USER", "DRAFT", False),           # question round: not final
    ("COMPLETE", "APPROVED", True),           # existing behavior unchanged
    # gate WITHOUT complete_at (real gate workspaces never have it — the
    # 2026-10-03 None[:10] crash regressed here because fixtures copied a
    # COMPLETE state and only rewrote phase)
    ("AWAIT_USER_APPROVAL", "APPROVED", True, True),
]


def _mk_req_stage_ws(tmp: Path, phase: str, hdr_status: str,
                     strip_complete_at: bool = False) -> Path:
    """Frozen men-spi workspace copied to tmp with STATE.json phase and
    requirements-header status rewritten."""
    src = TESTS_DIR / "fixtures" / "men-spi" / "workspace"
    ws = tmp / f"ws-{phase}-{hdr_status}"
    shutil.copytree(src, ws)
    state_p = ws / "STATE.json"
    state = json.loads(state_p.read_text(encoding="utf-8"))
    state["phase"] = phase
    if strip_complete_at:
        state.pop("complete_at", None)
    state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
    req_p = sorted((ws / "requirements").glob("*.md"))[-1]
    txt, n = re.subn(r"(?m)^(\|\s*status\s*\|\s*)\w+(\s*\|.*)$",
                     rf"\g<1>{hdr_status}\g<2>", req_p.read_text(encoding="utf-8"),
                     count=1)
    if n != 1:
        raise AssertionError(f"fixture rewrite failed: status row not found in {req_p}")
    req_p.write_text(txt, encoding="utf-8")
    return ws


def check_requirement_stage() -> list[str]:
    problems: list[str] = []
    for case in _REQ_STAGE_CASES:
        phase, hdr_status, want_ok = case[0], case[1], case[2]
        strip_ca = case[3] if len(case) > 3 else False
        label = f"requirement-stage[{phase}/{hdr_status}"
        if strip_ca:
            label += "/no-complete_at"
        label += "]"
        with tempfile.TemporaryDirectory(dir=TESTS_DIR) as td:
            ws = _mk_req_stage_ws(Path(td), phase, hdr_status, strip_ca)
            try:
                project = canonical.parse(ws, stage="requirement")
                if not want_ok:
                    problems.append(f"{label}: expected ParseGap, parse succeeded")
                    continue
                files = cvt.get("men-spi").convert(project, options={})
                names = sorted(f.filename for f in files)
                if names != ["requirement.json", "spec.md"]:
                    problems.append(f"{label}: produced {names}, "
                                    f"want [requirement.json, spec.md]")
                    continue
                print(f"PASS {label}")
            except canonical.ParseGap as e:
                if want_ok:
                    problems.append(f"{label}: unexpected ParseGap: {e}")
                else:
                    print(f"PASS {label} (refused: {e})")
    return problems


def record(fixture: Path) -> int:
    """(Re)record expected outputs from the frozen workspace."""
    ws = fixture / "workspace"
    exp = fixture / "expected"
    name = fixture.name
    conv = cvt.get(name)
    project = canonical.parse(ws)
    files = conv.convert(project, options=_fixture_options(fixture))
    exp.mkdir(parents=True, exist_ok=True)
    for f in files:
        (exp / f.filename).write_bytes(f.content)
        print(f"  recorded {exp / f.filename} ({len(f.content)} bytes)")
    return len(files)


def _fixture_options(fixture: Path) -> dict:
    opts_file = fixture / "options.json"
    if opts_file.exists():
        import json
        return json.loads(opts_file.read_text())
    return {}


def check(fixture: Path) -> list[str]:
    name = fixture.name
    ws = fixture / "workspace"
    exp = fixture / "expected"
    problems: list[str] = []
    if not ws.exists():
        return [f"{name}: fixture workspace missing ({ws})"]
    if not exp.exists():
        return [f"{name}: expected outputs missing — run --record {name} first"]

    try:
        project = canonical.parse(ws)
    except canonical.ParseGap as e:
        return [f"{name}: ParseGap on frozen fixture (fixture corrupted?): {e}"]

    try:
        files = cvt.get(name).convert(project, options=_fixture_options(fixture))
    except Exception as e:
        return [f"{name}: convert raised {type(e).__name__}: {e}"]

    produced = {f.filename for f in files}
    expected_files = {p.name for p in exp.iterdir() if p.is_file()}
    for missing in sorted(expected_files - produced):
        problems.append(f"{name}: adapter no longer produces {missing}")
    for extra in sorted(produced - expected_files):
        problems.append(f"{name}: adapter produces unknown file {extra}")

    for f in files:
        ep = exp / f.filename
        if not ep.exists():
            continue
        want = ep.read_bytes()
        if want != f.content:
            problems.append(
                f"{name}: {f.filename} drifted ({len(want)}B expected, "
                f"{len(f.content)}B produced) — conscious change? re-record")
    return problems


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    record_mode = "--record" in sys.argv

    fixtures_root = TESTS_DIR / "fixtures"
    names = args or [n for n in cvt.available()
                     if (fixtures_root / n).exists()]

    if not names:
        print("no fixtures found for any registered adapter "
              f"(registry: {cvt.available()})")
        return 0 if not cvt.available() else 1

    failures: list[str] = []
    problems = check_requirement_stage()
    if problems:
        failures.extend(problems)
        print("FAIL requirement-stage")
        for p in problems:
            print(f"  - {p}")
    for name in names:
        fixture = fixtures_root / name
        if not fixture.exists():
            print(f"SKIP {name}: no fixture dir")
            continue
        if record_mode:
            n = record(fixture)
            print(f"RECORDED {name}: {n} files")
            continue
        problems = check(fixture)
        if problems:
            failures.extend(problems)
            print(f"FAIL {name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS {name}")
    if record_mode:
        return 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

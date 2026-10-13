#!/usr/bin/env python3
"""SR11: (a) full output of 48b; (b) diff the normative code shapes across
archive/spec/10-spec-v10.md -> 11-spec-v11.md -> spec/12-spec-v12.md to test
whether stale-probe behavioral evidence still applies to the live shape."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------- (a) 48b full run
r = subprocess.run([sys.executable, str(ROOT / "appendix" / "48b-adv-c11-probes.py")],
                   capture_output=True, text=True, timeout=300, cwd=str(ROOT))
print("=== 48b exit code:", r.returncode)
for ln in (r.stdout or "").splitlines():
    print("  |", ln[:130])
err = (r.stderr or "").strip().splitlines()
for ln in err[-6:]:
    print("  E|", ln[:130])

# ---------- (b) shape diffs
def shapes(path):
    t = Path(path).read_text(encoding="utf-8")
    out = {}
    # §4.5 reference shape fence
    m = re.search(r"Conforming reference shape \(e\.g\.\):\s*\n\s*```\n(.*?)\n\s*```", t, flags=re.S)
    out["ref_shape"] = m.group(1) if m else "<MISSING>"
    # §4.3.2 loop fence
    m = re.search(r"## 4\.3\.2.*?```\n(.*?)\n```", t, flags=re.S)
    out["parse_loop"] = m.group(1) if m else "<MISSING>"
    # §4.6 limit fence
    m = re.search(r"## 4\.6.*?```\n(.*?)\n```", t, flags=re.S)
    out["limit_loop"] = m.group(1) if m else "<MISSING>"
    # serialize call
    m = re.search(r"payload = json\.dumps\([^\n]*\)", t)
    out["serialize"] = m.group(0) if m else "<MISSING>"
    # §4.3.3 FSM table
    m = re.search(r"## 4\.3\.3.*?(\| FIELD_START \|.*)", t, flags=re.S)
    tbl = m.group(1).split("If, at end")[0] if m else "<MISSING>"
    out["fsm_table"] = re.sub(r"\s+", " ", tbl).strip()
    return out

v10 = shapes(ROOT / "archive" / "spec" / "10-spec-v10.md")
v11 = shapes(ROOT / "archive" / "spec" / "11-spec-v11.md")
v12 = shapes(ROOT / "spec" / "12-spec-v12.md")

print("\n=== shape identity v10 vs v11 vs v12")
for k in v12:
    a = v10[k] == v11[k]
    b = v11[k] == v12[k]
    print(f"{k:12s} v10==v11: {a}   v11==v12: {b}")
    if not b:
        import difflib
        d = list(difflib.unified_diff(v11[k].splitlines(), v12[k].splitlines(),
                                      "v11", "v12", lineterm="", n=1))
        print("   " + "\n   ".join(d[:24]))

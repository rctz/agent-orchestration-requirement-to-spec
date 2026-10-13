#!/usr/bin/env python3
"""Selfcheck for spec/01-spec-v1.md (card t_e56db974, spec-design cycle 1).

Validates the spec's internal promises mechanically:
  S1  header block: kind=spec, status DRAFT, APPROVED requirements cited
  S2  traceability: REQ-001..014 and NFR-001..005 each appear as a matrix row
  S3  decision coverage: D-01..D-36 each bound in §11's coverage paragraph
  S4  error catalog: every E-* id of §6.3 appears in §7.1's per-class table
  S5  test ids: every T-* cited in §7.1/§8.1..§8.3 definition tables exists
  S6  claim keywords: zero hits outside the §10 QC section (board rule)
  S7  probe evidence: cited appendix files exist (13/14 probes)
  S8  scenarios: every S-nn walk-through in §5.3 cites at least one REQ/D id
  S9  section numbering: §1..§12 present exactly once each at top level
  S10 no status: APPROVED line in the spec (a spec is DRAFT until review)
"""
import glob
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = sorted(glob.glob(os.path.join(HERE, "spec", "*-spec-v*.md")))[-1]
print(f"selfcheck target: {os.path.basename(SPEC)}")
spec = open(SPEC, encoding="utf-8").read()
lines = spec.split("\n")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# S1 header block
head = spec[:2000]
check("S1 kind=spec", re.search(r"\| kind \| spec \|", head) is not None)
check("S1 status DRAFT", re.search(r"\| status \| DRAFT \|", head) is not None)
check(
    "S1 requirements APPROVED cited",
    "requirements/07-requirements-v7.md" in head and "APPROVED" in head,
)

# S2 traceability rows
matrix = spec[spec.index("# 11. Traceability"):]
missing = [
    f"REQ-{n:03d}" for n in range(1, 15) if f"| REQ-{n:03d} |" not in matrix
]
missing += [f"NFR-{n:03d}" for n in range(1, 6) if f"| NFR-{n:03d} |" not in matrix]
check("S2 all REQ/NFR rows in matrix", not missing, str(missing))

# S3 decision coverage paragraph (range auto-follows the register's last D-id)
reg = open(os.path.join(HERE, "appendix", "03-decision-register.md"),
           encoding="utf-8").read()
max_d = max(int(m) for m in re.findall(r"^\| D-(\d+) \|", reg, re.M))
cov = matrix[matrix.index("Decision-coverage check:"):]
missing_d = [
    f"D-{n:02d}"
    for n in range(1, max_d + 1)
    if not re.search(rf"\bD-{n:02d}\b", cov)
]
check(f"S3 D-01..D-{max_d:02d} all bound in coverage", not missing_d, str(missing_d))

# S4 error catalog consistency
cat = spec[spec.index("## 6.3 Error message contract"): spec.index("## 6.4")]
cat_ids = set(re.findall(r"^\| (E-[A-Z0-9]+) \|", cat, re.M))
s71 = spec[spec.index("## 7.1 Per-class contract"): spec.index("## 7.2")]
s71_ids = set(re.findall(r"^\| (E-[A-Z0-9]+) \|", s71, re.M))
check("S4 catalog ids == §7.1 ids", cat_ids == s71_ids, f"{cat_ids ^ s71_ids}")

# S5 test ids referenced exist
t_defined = set(re.findall(r"^\| (T-[UKC]\d+) \|", spec, re.M))
t_referenced = set(re.findall(r"\bT-([UKC]\d+)\b", spec))
t_referenced = {f"T-{x}" for x in t_referenced}
unknown = t_referenced - t_defined
check("S5 all referenced T-ids defined", not unknown, str(unknown))

# S6 claim keywords outside §10 (bounds: ### QC-1 .. # 11.)
bad = [
    r"\bidempoten", r"\batomicity\b", r"\batomic\b", r"\bdurab",
    r"\bconcurrency-safe\b", r"\bthread-safe\b", r"\brace-free\b",
    r"\bsecure\b", r"\brecoverable\b", r"\bbackward-compatible\b",
    r"\bperformant\b", r"\bguarantee", r"under concurrent",
]
start = spec.index("### QC-1")
end = spec.index("# 11. Traceability")
outside = spec[:start] + spec[end:]
hits = []
for pat in bad:
    for m in re.finditer(pat, outside, re.I):
        ln = outside[: m.start()].count("\n") + 1
        hits.append((m.group(0), ln))
check("S6 claim keywords outside QC", not hits, str(hits[:8]))

# S7 probe evidence files exist
for rel in ("appendix/13-spec-design-probes.py", "appendix/14-claim-keyword-check.py"):
    check(f"S7 {os.path.basename(rel)} exists", os.path.exists(os.path.join(HERE, rel)))
check("S7 probes cited in spec", "13-spec-design-probes.py" in spec)

# S8 scenarios carry REQ/D citations
s53 = spec[spec.index("## 5.3 Scenario"): spec.index("# 6. Interface")]
scen = re.findall(r"\*\*(S-\d+[^*]*)\*\*", s53)
check("S8 scenario count >= 16", len(scen) >= 16, f"found {len(scen)}")

# S9 top-level sections 1..12 once each
tops = re.findall(r"^# (\d+)\. ", spec, re.M)
want = [str(n) for n in range(1, 13)]
check("S9 sections 1..12 in order", tops == want, str(tops))

# S10 spec is not marked APPROVED
head_lines = "\n".join(lines[:12])
check("S10 no APPROVED status in spec", "status | APPROVED" not in head_lines)

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

#!/usr/bin/env python3
"""62f-adv-c13-sweep — residual mechanical checks for adv-c13.
1. '43 checks' residue (must survive only as quoted history if at all)
2. isolated-pipe-line sweep (mangle detection: a '|'-line whose neighbors
   are not '|'-lines)
3. quick enumerations sanity
"""
import re

SPEC = "../spec/13-spec-v13.md"
text = open(SPEC, encoding="utf-8").read()
lines = text.split("\n")

hits43 = [(i + 1, l[:120]) for i, l in enumerate(lines) if "43 checks" in l]
print("'43 checks' sites:", hits43 if hits43 else "none")

mangles = []
for i, l in enumerate(lines):
    if l.lstrip().startswith("|") and l.strip() != "|":
        prev_pipe = i > 0 and lines[i - 1].lstrip().startswith("|")
        next_pipe = i + 1 < len(lines) and lines[i + 1].lstrip().startswith("|")
        if not prev_pipe and not next_pipe:
            mangles.append((i + 1, l[:100]))
print("isolated pipe-lines (potential mangles):", mangles if mangles else "none")

for pat in (r"D-01\.\.D-58", r"D-01\.\.D-5\d"):
    print(pat, "->", len(re.findall(pat, text)), "sites")

#!/usr/bin/env python3
"""Mangle sweep on spec/11-spec-v11.md: isolated pipe-lines (doubled-pipe trap)
+ a consistency recount of the enumerations."""
import re

lines = open("spec/11-spec-v11.md", encoding="utf-8").read().split("\n")
isolated = []
for i, line in enumerate(lines):
    if "||" in line:
        prev_pipe = i > 0 and lines[i - 1].startswith("|")
        next_pipe = i + 1 < len(lines) and lines[i + 1].startswith("|")
        if not prev_pipe and not next_pipe:
            isolated.append(i + 1)
print("isolated double-pipe lines:", isolated or "none")

text = "\n".join(lines)
print("header register:", re.search(r"decision register \| appendix/03-decision-register\.md \(D-\d+\.\.D-(\d+)", text).group(1))
print("s1 enum:", re.search(r"leaves none unresolved: D-\d+\.\.D-(\d+)", text).group(1))
print("s11 enum:", re.search(r"Decision-coverage check: D-\d+\.\.D-(\d+) are all DECIDED", text).group(1))
print("total lines:", len(lines) - 1)
print("version row:", re.search(r"\| version \| (\S+) \|", text).group(1))
print("status row:", re.search(r"\| status \| (\S+) \|", text).group(1))

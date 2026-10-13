#!/usr/bin/env python3
"""One-off: isolated-pipe check on the adv-c16 report itself."""
import re

p = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js/appendix/94-adv-c16.md"
lines = open(p, encoding="utf-8").read().splitlines()
bad = []
for i, l in enumerate(lines, 1):
    if l.startswith("|") and not l.rstrip().endswith("|"):
        bad.append((i, l[:80]))
print("unterminated pipe rows:", bad if bad else "none")
print("total lines:", len(lines))
# doubled-pipe mangles: a line containing '||' whose neighbors are not table rows
for i, l in enumerate(lines, 1):
    if "||" in l.replace("||", "", 1) and "||" in l:
        prev = lines[i - 2] if i >= 2 else ""
        nxt = lines[i] if i < len(lines) else ""
        if not (prev.startswith("|") or nxt.startswith("|")):
            print("isolated || at line", i, l[:60])
print("done")

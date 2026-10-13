"""Cycle-16 closeout: F-01 detector re-run — no unannotated superseded-spec cite in v16.

For every spec/NN-spec-vM.md cite in the LIVE spec, require an annotation
keyword (HISTORICAL/historical/rev16/rev15/revision evidence) within the
same line. C17 passes iff this reports 0 stale cites.
"""
import re

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
spec = open(HERE + "/spec/16-spec-v16.md", encoding="utf-8").read()
lines = spec.split("\n")

# the live top file number (must be this spec's own version — 16)
import glob
import os
live = sorted(glob.glob(HERE + "/spec/*-spec-v*.md"))[-1]
live_m = re.search(r"(\d+)-spec-v(\d+)\.md$", live)
live_n = int(live_m.group(1))
print("live spec file:", os.path.basename(live))

stale = 0
for i, ln in enumerate(lines, 1):
    for m in re.finditer(r"spec/(\d+)-spec-v(\d+)\.md", ln):
        n = int(m.group(1))
        if n >= live_n:
            continue  # cites of the current file are live by definition
        window = ln[max(0, m.start() - 400): m.end() + 400].lower()
        annotated = any(k in window for k in (
            "historical", "archived", "rev16", "rev15", "revision evidence",
            "cycle-11", "cycle-10", "cycle-16",
        ))
        if not annotated:
            stale += 1
            s = max(0, m.start() - 120)
            print("STALE line %d [%s]: ...%s..." % (i, m.group(0), ln[s:m.end() + 120][:280]))

print("\nTOTAL: %d stale cite(s)" % stale)
# also: banned-phrase substring sweep (substring trap discipline)
for banned in ("under concurrent execution guarantees",
               "platform-independent", "never leaves a partial file"):
    if banned in spec.lower():
        print("BANNED-PHRASE present:", banned)
print("banned-phrase sweep done")

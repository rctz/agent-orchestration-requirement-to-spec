#!/usr/bin/env python3
"""63-sr12-vdiff.py — independent v12->v13 diff audit (spec-review cycle 12).

Streams unified diffs between archive/spec/12-spec-v12.md and
spec/13-spec-v13.md, classifies each hunk against the four SR11 folds,
and sweeps for isolated pipe-lines (the multi-line patch trap).
"""
import difflib
import re

old = open("archive/spec/12-spec-v12.md", encoding="utf-8").read().splitlines()
new = open("spec/13-spec-v13.md", encoding="utf-8").read().splitlines()

diff = list(difflib.unified_diff(old, new, lineterm="", n=0))
hunks = []
cur = None
for line in diff:
    if line.startswith("@@"):
        if cur:
            hunks.append(cur)
        cur = {"hdr": line, "added": [], "removed": []}
    elif cur is not None:
        if line.startswith("+") and not line.startswith("+++"):
            cur["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            cur["removed"].append(line[1:])
if cur:
    hunks.append(cur)

fold_markers = {
    "F-01 timings": ("27.3", "25.8", "24.9", "9.1", "0.8 s", "0.4 s",
                     "55h", "reader-like", "20 s", "3-5 s", "9-15"),
    "F-02 historical": ("HISTORICAL", "52-rev12-gate-reaim", "SR11-F-02",
                        "re-proven", "re-proof"),
    "F-03 count": ("42 checks",),
    "F-04 D-51": ("D-51 (",),
    "revision-row": ("cycle-13", "v13", "SR11-F-0", "58-rev13",
                     "59-rev13", "62", "61", "60"),
}

print(f"total hunks: {len(hunks)}")
unclassified = []
for h in hunks:
    text = " ".join(h["added"])
    tags = []
    for tag, keys in fold_markers.items():
        if any(k in text for k in keys):
            tags.append(tag)
    if not tags and not h["added"]:
        tags.append("[pure deletion]")
    if not tags:
        unclassified.append(h)
    print(f"{h['hdr']}  +{len(h['added'])}/-{len(h['removed'])}  -> {tags or 'UNCLASSIFIED'}")
    for a in h["added"][:3]:
        print(f"    + {a[:150]}")

print()
print(f"unclassified hunks: {len(unclassified)}")

# isolated pipe-line sweep over the whole new spec
lines = new
iso = []
for i, ln in enumerate(lines):
    s = ln.strip()
    if s.startswith("|") and s.endswith("|") and s.count("|") <= 2 and s != "||":
        prev = lines[i - 1].strip() if i else ""
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if not (prev.startswith("|") and nxt.startswith("|")):
            iso.append((i + 1, s[:100]))
if "||" in "\n".join(lines):
    for i, ln in enumerate(lines):
        if "||" in ln.replace("|||", ""):
            iso.append((i + 1, "DOUBLE-PIPE: " + ln[:100]))

print(f"isolated/double pipe candidates: {len(iso)}")
for n, s in iso[:20]:
    print(f"  line {n}: {s}")

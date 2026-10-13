#!/usr/bin/env python3
"""Cross-check: run the sibling project's claim-keyword rule against THIS
project's draft spec (spec/01-spec-v1.md). Report every hit outside the
QC section with line numbers, so the QC section can be written with a
complete, validator-clean inventory the first time."""
import glob
import re

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SIBLING = "/home/pi/hermes-workspaces/req-lab-v2/i-want-ui-to-display-overall-hospital-in"

bad = [
    r"\bidempoten", r"\batomicity\b", r"\batomic\b", r"\bdurab",
    r"\bconcurrency-safe\b", r"\bthread-safe\b", r"\brace-free\b",
    r"\bsecure\b", r"\brecoverable\b", r"\bbackward-compatible\b",
    r"\bperformant\b", r"\bguarantee", r"under concurrent",
]


def hits_outside(spec_text, qc_start_marker="### QC-1", section_end_marker="# 11."):
    if qc_start_marker in spec_text and section_end_marker in spec_text:
        start = spec_text.index(qc_start_marker)
        end = spec_text.index(section_end_marker, start)
        outside = spec_text[:start] + spec_text[end:]
        base_lines_outside = 0
        # line mapping: outside text = spec[:start] + spec[end:]
        len_head = start
    else:
        outside = spec_text
        len_head = 0
    found = []
    for pat in bad:
        for m in re.finditer(pat, outside, re.I):
            off = m.start()
            if len_head and off >= len_head:
                # in the tail copy: real line = head_lines + (off-len_head offset in original tail)
                tail_off = off - len_head + start
                line = spec_text[:tail_off].count("\n") + 1
            else:
                line = outside[:off].count("\n") + 1
            ctx = spec_text[max(0, off - 70): off + 50].replace("\n", " ")
            found.append((m.group(0), line, ctx))
    return found


# 1) sanity: run against the SIBLING's live spec with its own section bounds
sib_specs = sorted(glob.glob(SIBLING + "/spec/*-spec-v*.md"))
if sib_specs:
    sib = open(sib_specs[-1], encoding="utf-8").read()
    sib_hits = hits_outside(sib)
    print(f"SIBLING live spec: {sib_specs[-1].split('/')[-1]} — hits outside QC: {len(sib_hits)}")
    for w, ln, ctx in sib_hits[:10]:
        print(f"   {w} line {ln}: ...{ctx}...")

# 2) our current draft (highest running NN spec file)
ours_path = sorted(glob.glob(HERE + "/spec/*-spec-v*.md"))[-1]
ours = open(ours_path, encoding="utf-8").read()
print(f"OUR draft spec {ours_path.split('/')[-1]} — keyword hits (whole file, QC not yet written): {len(ours_hits := hits_outside(ours))}")
for w, ln, ctx in ours_hits:
    print(f"   {w} line {ln}: ...{ctx}...")

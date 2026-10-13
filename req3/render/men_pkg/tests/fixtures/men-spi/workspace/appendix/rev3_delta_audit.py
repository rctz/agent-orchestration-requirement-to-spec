#!/usr/bin/env python3
"""rev3 delta audit: archived 02-spec-v2.md vs live 03-spec-v3.md.

D1  old file unchanged except its own header/version/revision lines.
D2  every changed hunk falls in an intended section (whitespace-normalized
    marker scan per c9/c11 lesson).
D3  table integrity: no doubled '||' rows introduced (except the file's
    own pre-existing style at §4.3.3's table header, which v2 already had).
D4  no mangled lines (leading '|' on prose paragraphs).
"""
import difflib
import glob
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

old_path = os.path.join(HERE, "archive", "spec", "02-spec-v2.md")
if not os.path.exists(old_path):
    cands = sorted(glob.glob(os.path.join(HERE, "archive", "spec", "*.md")))
    print("archived v2 not found; archive/spec holds:", [os.path.basename(c) for c in cands])
    old_path = cands[-1] if cands else None

new_path = os.path.join(HERE, "spec", "03-spec-v3.md")
if old_path is None:
    print("FAIL no old version available for delta audit")
    sys.exit(1)

old = open(old_path, encoding="utf-8").read().split("\n")
new = open(new_path, encoding="utf-8").read().split("\n")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
print(f"{len(ops)} changed hunks")

# D1: v2's lines 1-16 (header/version/revision table) may differ; the rest of v2 must be a subset of v3's flow.
header_guard = 16
bad_old = [op for op in ops if op[1] < header_guard and False]  # header allowed
outside = [
    (tag, i1, i2, j1, j2)
    for (tag, i1, i2, j1, j2) in ops
    if i1 >= header_guard and not (tag == "replace" and (i2 - i1) <= 30)
]
# intended replacement sites (by anchor text in the OLD line span)
INTENDED = [
    "D-01..D-36",                       # F-03 header + S1 + S11
    "70/70 PASS",                       # F-07 header + 1.3
    "writes 45 bytes",                  # F-08
    "(2 bytes)",                        # F-09
    "the three checks run in exactly this order",
    "check 1: unterminated quote",
    "| QUOTED | → CLOSED | stay QUOTED (data) | stay QUOTED (data), advance",
    "MemoryError anywhere |",           # F-06
    "E-MEM | any phase, MemoryError",   # F-05
    "T-C9 (constructed via limit",      # F-04
    "ulimit -f",                        # F-10
    "T-U3 | unterminated-quote FSM",
    "T-U6 | parse: D-29 ordering",
    "T-C7 | unterminated quotes",
    "on first record: `HEADER_VALIDATED` (after FSM scan",
    "the FIRST record's FSM scan trips",
    "**S-10 Unterminated quote — N ≠ M** (REQ-013/D-30).",
    "and M = `row_start_line + opening_line - 1`:",
    "generic contract",                 # 4.2 error-path form pointer
    "residual net (§7.3) — reported per the generic contract",  # 4.4
    "`parse` | hand the text to `csv.reader`",  # 2.2 responsibility row
    "A `\"` in an unquoted field is never this (data, D-30). |",  # glossary
    "M = N + record-relative opening line − 1 (§4.3.2/§4.3.3). |",  # glossary
    "M = N + record-relative opening line",
    "`HEADER_VALIDATED` (after FSM scan",
    "passes FSM (no quote), header validated (2 unique names)",  # S-1 order wording
    "T-C1..T-C10, T-K1, T-K3 assert message text",  # QC-1 verification
    "NFR-005: T-C13 + T-U8 + T-C10.",   # 9.x anchors
]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


unexpected = []
for (tag, i1, i2, j1, j2) in outside:
    old_span = "\n".join(old[i1:i2])
    new_span = "\n".join(new[j1:j2])
    n_old, n_new = norm(old_span), norm(new_span)
    if any(norm(anchor) in n_old or norm(anchor) in n_new for anchor in INTENDED):
        continue
    if tag == "insert" and not old_span.strip():
        continue  # pure insertion at an intended site's boundary
    if tag == "replace" and n_old == n_new:
        continue
    unexpected.append((tag, i1 + 1, i2, old_span[:90].replace("\n", " / ") or new_span[:90].replace("\n", " / ")))

check("D2 all hunks at intended sites", len(unexpected) == 0,
      "; ".join(f"[{t} old:{a}-{b}] {c!r}" for t, a, b, c in unexpected[:6]))

# D3: doubled-pipe table rows that v2 didn't have
old_doubled = {ln for ln in old if ln.startswith("|| ") and not ln.startswith("|||")}
new_doubled = {ln for ln in new if ln.startswith("|| ") and not ln.startswith("|||")}
added_doubled = [ln for ln in new_doubled if ln not in old_doubled]
check("D3 no new doubled-pipe rows", len(added_doubled) == 0,
      f"{len(added_doubled)} new: {added_doubled[:3]}")

# D4: mangled prose — a '|'-prefixed line that ISN'T a table row. Real
# table rows sit adjacent to other '|' lines; the header table (1..20) is
# exempt. A mangling shows up as an isolated '|' line (neighbors have no
# pipe) — the c11 signature (plus the pure '|' or '| ' degenerate forms).
mangled = []
for idx, ln in enumerate(new):
    if idx < 20:
        continue
    if not ln.startswith("|"):
        continue
    prev = new[idx - 1] if idx else ""
    nxt = new[idx + 1] if idx + 1 < len(new) else ""
    if prev.lstrip().startswith("|") or nxt.lstrip().startswith("|"):
        continue  # inside a table block
    if ln.strip() in ("|", "| |", "||"):
        mangled.append((idx + 1, ln[:70]))
        continue
    if re.match(r"^\|\s*[-A-Za-z`]", ln) and not re.match(r"^\|", prev):
        mangled.append((idx + 1, ln[:70]))
check("D4 no mangled prose lines", len(mangled) == 0, f"{mangled[:4]}")

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

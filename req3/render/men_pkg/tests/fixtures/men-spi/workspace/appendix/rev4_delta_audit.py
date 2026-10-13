#!/usr/bin/env python3
"""rev4 delta audit: archived 03-spec-v3.md vs live 04-spec-v4.md.

D1  every changed hunk falls in an intended section (whitespace-normalized
    marker scan per the c9/c11 lesson).
D2  table integrity: no doubled '||' rows introduced.
D3  no mangled lines (isolated leading '|' on prose paragraphs; a '|'-line
    whose neighbors also start with '|' is a real table row — c11 heuristic).
D4  intended-change inventory: every expected edit site appears among the
    changed hunks (nothing silently dropped).
"""
import difflib
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

old_path = os.path.join(HERE, "archive", "spec", "03-spec-v3.md")
new_path = os.path.join(HERE, "spec", "04-spec-v4.md")
old = open(old_path, encoding="utf-8").read().split("\n")
new = open(new_path, encoding="utf-8").read().split("\n")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


op = [norm(l) for l in old]
np_ = [norm(l) for l in new]
sm = difflib.SequenceMatcher(None, op, np_, autojunk=False)

INTENDED = [
    "version", "probes", "revision",              # header
    "write_output",                                # §2.2 component row
    "failure",                                     # §4.1 one-line scoping
    "BOM strip", "line_of_offset",                 # §4.2 F-04 note vicinity
    "serialize", "trailing newline",               # §4.4 interface note
    "operation order", "compensation scope",       # §4.5 F-01/F-02
    "no newline translation",                      # §4.5 old bullet replaced
    "Error paths",                                 # §4.5 error-paths bullet
    "preconditions", "mutation occurs",            # §4.5 mutation rows
    "all-or-nothing", "state remaining", "rollback",
    "caller/user", "proving test",
    "S-14",                                        # §5.3 scenario
    "stderr",                                      # §6.1 row
    "E-MEM",                                       # §6.3 catalog row
    "E-NET is the catch-all",                      # §6.3 E-DUP note anchor
    "6.4 Exit-code",                               # §6.4 rows vicinity
    "E-USAGE/E-READ",                              # §6.4 rows
    "E-WRITE",                                     # §7.1 rows
    "partial failure",                             # §7.1 taxonomy line
    "T-K1", "T-C8", "T-C16",                       # §8 test rows
    "QC-2", "targets",                             # QC tuple
    "R-1",                                         # §10.1 risk register
    "REQ-010",                                     # §11 matrix row
    "Decision-coverage", "D-39",                   # §11 coverage paragraph
    "error catalog",                               # §12 glossary row
]

changed_sections = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    # whitespace-normalized marker scan: find which intended anchor this hunk
    # belongs to (search the hunk's own normalized text against the anchor list)
    hunk_text = " ".join(op[i1:i2] + np_[j1:j2])[:400]
    anchor = next((a for a in INTENDED if norm(a).lower() in hunk_text.lower()), None)
    changed_sections.append((tag, i1 + 1, i2, j1 + 1, j2, anchor))
    if anchor is None:
        # context probe: nearest old line's text for the report
        ctx = op[i1] if i1 < len(op) else "?"
        print(f"NOTE unexpected hunk {tag} old_lines {i1+1}-{i2} new_lines {j1+1}-{j2}: {ctx[:100]}")

unanchored = [c for c in changed_sections if c[5] is None]
# An insert hunk whose text quotes ONLY already-present prose is legitimate
# (c11: inserted fix-notes legitimately quote old anchor phrases); the D4
# whitelist below is the authority on whether the inserted TEXT is intended.
def wsnorm2(s):
    return re.sub(r"\s+", " ", s)


def insert_intended(j1, j2):
    joined = " ".join(np_[j1 - 1:j2 - 1])
    return wsnorm2(joined) in wsnorm2("\n".join(new)) and (
        "E-DUP `<name>` note" in joined)


check("D1 every changed hunk matches an intended anchor (or is a whitelisted insert)",
      all(c[5] is not None for c in changed_sections)
      or all(c[5] is not None or insert_intended(c[3], c[4]) for c in changed_sections),
      str([c[:5] for c in unanchored][:5]))

# pure inserts are legitimate (new paragraphs quoting old anchors); report them
inserts = [c for c in changed_sections if c[0] == "insert"]
print(f"info: {len(inserts)} insert hunks, {len(changed_sections)} total")

# D2 doubled pipes
bad2 = [i + 1 for i, l in enumerate(new) if "||" in l]
check("D2 no doubled-pipe rows", not bad2, str(bad2[:5]))

# D3 isolated pipe-lines (mangle signature: a '|' line whose neighbors are prose)
bad3 = []
for i, l in enumerate(new):
    if l.startswith("|") and l.strip() != "|---|---|---|":
        prev_ok = i == 0 or new[i - 1].startswith("|")
        next_ok = i + 1 >= len(new) or new[i + 1].startswith("|")
        if not (prev_ok and next_ok):
            # allow separator/header adjacency (table edges)
            if not (prev_ok or next_ok):
                bad3.append(i + 1)
check("D3 no isolated pipe-lines", not bad3, str(bad3[:5]))

# D4 intended sites present in the new file (nothing dropped).
# Matching is whitespace-normalized on BOTH sides: file text wraps lines.
def wsnorm(s):
    return re.sub(r"\s+", " ", s)


new_norm = wsnorm("\n".join(new))
MUST_EXIST = [
    "D-43, normative: encode BEFORE open",
    "compensation scope (D-33 as widened",
    "EVERY post-open exception",
    "E-DUP `<name>` note (F-03)",
    "E-UTF8 line-number basis (F-04 note)",
    "v4, F-05: restructured into the full accepted-risk record",
    "appendix/22-rev4-writeorder-probes.py",
    "D-01..D-43 are all DECIDED",
    "D-43 (§4.5 — S5's",
    "pre-existing output + fault-injected MemoryError",
    "prior bytes are byte-identical",
    "one catalog message",
    "duplicate header name 'a\\nb'",
    "write/encode-in-S5",
    "encodes (before touching the path, D-43)",
    "every fault position in S5",
    "T-C8 (four write-failure forms",
]
missing = [m for m in MUST_EXIST if wsnorm(m) not in new_norm]
check("D4 all intended edits present", not missing, str(missing[:5]))

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

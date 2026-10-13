#!/usr/bin/env python3
"""rev5 delta audit: archived 04-spec-v4.md vs live 05-spec-v5.md.

D1  every changed hunk falls in an intended section (whitespace-normalized
    marker scan per the c9/c11 lesson).
D2  table integrity: no doubled '||' rows introduced.
D3  no mangled lines (isolated leading '|' on prose paragraphs; a '|'-line
    whose neighbors also start with '|' is a real table row — c11 heuristic).
D4  intended-change inventory: every expected edit site appears among the
    changed hunks / new file (nothing silently dropped).

Revision scope (cycle-5, findings appendix/24-review-spec-c3.md):
SR3-F-01 (P1, D-44 serialize E-MEM output-named), SR3-F-02 (P2, §1
enumeration), SR3-F-03..F-06 (P3: diagram edge, text-mode parenthetical,
interpolated-data scoping, T-C16 permissive phase form).
"""
import difflib
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

old_path = os.path.join(HERE, "archive", "spec", "04-spec-v4.md")
new_path = os.path.join(HERE, "spec", "05-spec-v5.md")
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
    "D-01..D-44",                                  # header + §1 enumeration (F-02)
    "failure",                                     # §4.1 one-line scoping (F-05 generalized)
    "interpolated",                                # §4.1 scoping: ANY message slot
    "serialize", "trailing newline",               # §4.4 error paths (D-44)
    "E-MEM form",                                  # §4.4 OUTPUT-named form
    "operation order",                             # §4.5 text-mode parenthetical (F-04)
    "encode implicitly",                           # §4.5 parenthetical NEW text
    "S-14",                                        # §5.3 scenario header
    "WRITE_OUTPUT",                                # §5.1 diagram edge (F-03)
    "stderr",                                      # §6.1 row
    "E-MEM",                                       # §6.3 catalog row + E-DUP note (D-44/F-05)
    "verbatim discipline",                         # §6.3 E-DUP note NEW text
    "6.4 Exit-code",                               # §6.4 rows
    "E-WRITE",                                     # §7.1 rows vicinity
    "T-C16",                                       # §8.3 test row (F-06)
    "QC-2",                                        # QC tuple serialize no-side-effect note
    "REQ-010",                                     # §11 matrix row unchanged context
    "Decision-coverage", "D-43", "D-44",           # §11 coverage paragraph
]
# c11 lesson: skip the trailing delete-hunk (j1 >= len(new), all-delete) and
# guard insert hunks with empty old_spans before flagging them.
changed_sections = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    if j1 >= len(np_) and i1 >= len(op):
        continue
    hunk_text = " ".join(op[i1:i2] + np_[j1:j2])[:1200]
    anchor = next((a for a in INTENDED if norm(a).lower() in hunk_text.lower()), None)
    if anchor is None and hunk_text.strip() == \
            "| status | DEPRECATED | | status | DRAFT |":
        anchor = "archive status stamp vs live DRAFT (expected)"
    changed_sections.append((tag, i1 + 1, i2, j1 + 1, j2, anchor))
    if anchor is None:
        ctx = op[i1] if i1 < len(op) else "?"
        print(f"NOTE unexpected hunk {tag} old_lines {i1+1}-{i2} new_lines {j1+1}-{j2}: {ctx[:100]}")

unanchored = [c for c in changed_sections if c[5] is None]


def insert_intended(j1, j2):
    joined = " ".join(np_[j1 - 1:j2 - 1])
    return ("D-44" in joined) or ("WRITE_OUTPUT ── MemoryError" in joined)


check("D1 every changed hunk matches an intended anchor (or is a whitelisted insert)",
      all(c[5] is not None for c in changed_sections)
      or all(c[5] is not None or insert_intended(c[3], c[4]) for c in changed_sections),
      str([c[:5] for c in unanchored][:5]))

inserts = [c for c in changed_sections if c[0] == "insert"]
print(f"info: {len(inserts)} insert hunks, {len(changed_sections)} total")

# D2 doubled pipes
bad2 = [i + 1 for i, l in enumerate(new) if "||" in l]
check("D2 no doubled-pipe rows", not bad2, str(bad2[:5]))

# D3 isolated pipe-lines
bad3 = []
for i, l in enumerate(new):
    if l.startswith("|") and l.strip() != "|---|---|---|":
        prev_ok = i == 0 or new[i - 1].startswith("|")
        next_ok = i + 1 >= len(new) or new[i + 1].startswith("|")
        if not (prev_ok and next_ok):
            if not (prev_ok or next_ok):
                bad3.append(i + 1)
check("D3 no isolated pipe-lines", not bad3, str(bad3[:5]))

# D4 intended sites present in the new file.
def wsnorm(s):
    return re.sub(r"\s+", " ", s)


new_norm = wsnorm("\n".join(new))
MUST_EXIST = [
    # SR3-F-01 (P1): single output-named serialize observable, everywhere
    "serialize/write phases: `csv2json: error: out of memory writing <out>`",
    "there is no input-named serialize form",
    "OUTPUT-named E-MEM form",
    "(`out of memory writing <out>`, §6.3, D-44)",
    "serialize and write share the output-named form, D-44",
    "serialize-phase MemoryError per D-44",
    "under D-44 the serialize phase asserts the SAME output-named template",
    # SR3-F-02 (P2)
    "D-01..D-44 in",
    "D-01..D-44 are all DECIDED",
    "D-01..D-44, all DECIDED",
    # SR3-F-03 (P3)
    "WRITE_OUTPUT ── MemoryError(after compensation) ──► REPORTING(memory)",
    # SR3-F-04 (P3)
    "text mode performs the encode implicitly inside the write call",
    # SR3-F-05 (P3)
    "an exception repr may legally contain a raw newline —",
    "custom `__repr__` override",
    "data-borne breaks inside ANY interpolated slot",
    # SR3-F-06 (P3)
    "ANY of the phase forms is the accepted assertion",
    # decision register cross-consistency
    "D-44 (§4.4/§6.3 — the E-MEM serialize",
    "v5: D-44 appended for the SR3-F-01 disposition",
]
missing = [m for m in MUST_EXIST if wsnorm(m) not in new_norm]
check("D4 all intended edits present", not missing, str(missing[:5]))

# D5 the OLD contradicting form is gone from the live file (both stale sites)
stale = [
    "parse/serialize phases: `csv2json: error: out of memory while converting <in>`",
    "E-MEM serialize-phase form",
    "(`out of memory while converting <in>`, §6.3)",
    "D-01..D-42",
    "SAME encode-before-open order",
    "a newline inside an E-DUP header name",
]
present = [s for s in stale if wsnorm(s) in new_norm]
check("D5 no stale contradicting text remains", not present, str(present[:5]))

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

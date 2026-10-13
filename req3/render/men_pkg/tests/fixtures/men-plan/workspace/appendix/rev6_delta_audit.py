#!/usr/bin/env python3
"""rev6 delta audit: archived 05-spec-v5.md vs live 06-spec-v6.md.

D1  every changed hunk falls in an intended section (whitespace-normalized
    marker scan per the c9/c11 lesson; trailing delete-hunk skipped; insert
    hunks with empty old_spans guarded).
D2  table integrity: no doubled '||' rows introduced.
D3  no mangled lines (isolated leading '|' on prose paragraphs; a '|'-line
    whose neighbors also start with '|' is a real table row — c11 heuristic).
D4  intended-change inventory: every expected edit site appears in the new
    file (nothing silently dropped).
D5  the superseded contradicting forms are gone from the live file.

Revision scope (cycle-6, findings appendix/26-adv-c5.md + 27-review-spec-c4.md):
F-01 (P1, D-45 single binary write shape, text-mode parenthetical DELETED),
F-04 (P1, D-46 compensation trigger = every exception after a SUCCESSFUL
open; S-14(b) rewritten; "EACCES at open" trigger wording superseded),
F-02 (P2, D-47 aliasing boundary + R-1b accepted-risk record + T-C8 matrix
entry), F-03 (P3, R-2 reword), SR4-F-01..F-03 (P3 advisories: S-9b cite,
revision-row pointer, FIELD_START reachability gloss).
"""
import difflib
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

old_path = os.path.join(HERE, "archive", "spec", "05-spec-v5.md")
new_path = os.path.join(HERE, "spec", "06-spec-v6.md")
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
    "version", "probes", "revision",                    # header
    "D-01..D-47",                                       # header + §1 enumeration
    "S-9b",                                             # SR4-F-01 §5.2 cite
    "record-internal terminator",                       # SR4-F-03 FSM gloss
    "Single implemented shape",                         # F-01/D-45 block NEW
    "text mode NON-CONFORMING",                         # F-01/D-45
    "trigger narrowed per D-46",                        # F-04 compensation scope
    "At-open failures are NOT compensation triggers",   # F-04/D-46 NEW
    "trigger scope",                                    # D-46 compensation bullet
    "Aliasing boundary",                                # F-02/D-47 NEW
    "all-or-nothing boundary",                          # table row 6
    "on retry",                                         # table row 7
    "overlap in time",                                  # table row 9 (F-03)
    "state remaining",                                  # table row 10
    "rollback",                                         # table row 11
    "proving test",                                     # table row 13
    "S-14 Write-phase failure",                         # §5.3 S-14(b)/(e)
    "b1",                                               # S-14(b) split
    "E-WRITE",                                          # §6.3 row + §7.1 rows
    "E-MEM",                                            # §7.1 E-MEM row
    "E-NET",                                            # §7.1 E-NET row
    "partial failure",                                  # taxonomy note
    "T-C8",                                             # §8.3 test row
    "QC-2",                                             # QC tuple
    "R-1b",                                             # risk register NEW
    "R-2",                                              # risk register reword
    "REQ-010",                                          # §11 matrix row
    "Decision-coverage", "D-43", "D-45", "D-46", "D-47",  # coverage paragraph
    "successful open",                                  # glossary entry
]
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
    return ("D-45" in joined or "D-46" in joined or "D-47" in joined
            or "R-1b" in joined or "successful open" in joined)


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
    # F-01 (P1, D-45)
    "Single implemented shape — text mode NON-CONFORMING for this stage",
    "D-45, closes adv-c5 F-01",
    "there is NO conforming text-mode alternative",
    "T-C8/T-C16 apply only to the binary shape",
    # F-04 (P1, D-46)
    "exception raised AFTER A SUCCESSFUL OPEN first runs the compensation",
    "At-open failures are NOT compensation triggers (D-46)",
    "D-46, closes adv-c5 F-04",
    "survives a failed run byte-identical",
    "(b2) pre-existing READ-ONLY target in a WRITABLE directory",
    "non-conforming since v6",
    "compensation runs only if the open SUCCEEDED (D-46)",
    "pre-existing READ-ONLY target (mode 444) in a writable dir",
    "at-open failures excluded per D-46",
    # F-02 (P2, D-47)
    "Aliasing boundary (D-47, accepted risk R-1b)",
    "- R-1b: under an ALIASED output target",
    "accepted-risk disposition",
    "ALIASED target (symlink to a regular file)",
    # F-03 (P3)
    "interleaved runs can lose BOTH outputs",
    "leaving a silent exit-0 run with NO file at all",
    "with NO promised outcome",
    # SR4-F-01/F-03 (P3)
    "the duplicate error wins, S-9b",
    "reachable for a record-internal empty line, a trailing empty field",
    # enumeration + coverage
    "D-01..D-47",
    "D-45 (§4.5 — the write stage has ONE",
    "D-46 (§4.5 — the D-33",
    "D-47 (§4.5 aliasing boundary",
    "v6: D-45/D-46/D-47 appended for the adv-c5",
    # glossary
    "successful open (compensation trigger basis)",
]
missing = [m for m in MUST_EXIST if wsnorm(m) not in new_norm]
check("D4 all intended edits present", not missing, str(missing[:5]))

# D5 the superseded forms are gone from the live file.
# Scope: the normative body (everything after the header's revision row).
# The header revision row legitimately QUOTES superseded wording as
# history ("the §4.5 'Equivalent conforming alternative' text-mode
# parenthetical is DELETED") — the c11 insert-quotes-old-anchor case.
head_end = next(i for i, l in enumerate(new) if l.startswith("# 1. Overview"))
body_norm = wsnorm("\n".join(new[head_end:]))
stale = [
    "Equivalent conforming alternative",
    "text mode performs the encode implicitly inside the write call",
    "EACCES at open, ...) and equally any non-OSError",
    "compensation trigger is EVERY post-open exception",
    "race at the OS level and the last writer wins",
    "harmless no-op (ENOENT\nignored)",
    "only possible for a record-internal empty line, never across records",
    "the duplicate error wins, S-9(c)",
    "§4.4/§5.3 S-4/§6.3/§7.1/T-C16 aligned",
]
present = [s for s in stale if wsnorm(s) in body_norm]
check("D5 no stale contradicting text remains in the normative body",
      not present, str(present[:5]))

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

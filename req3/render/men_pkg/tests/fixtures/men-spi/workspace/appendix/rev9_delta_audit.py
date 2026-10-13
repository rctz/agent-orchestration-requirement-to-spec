#!/usr/bin/env python3
"""rev9 delta audit: spec/08-spec-v8.md (archived) -> spec/09-spec-v9.md.
Uses the same fold-marker heuristics as rev6/rev8: whitespace-NORMALIZED
spans, insert hunks with empty old_span guarded, trailing all-delete hunk
skipped. Asserts every hunk lands on the cycle-9 fix list; anything else
is printed as UNEXPECTED."""
import difflib, io, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old = io.open(os.path.join(HERE, "archive", "spec", "08-spec-v8.md"), encoding="utf-8").read().split("\n")
# the ticker archives within ~3 min; fall back to the live v8 sibling if not yet
if not os.path.exists(os.path.join(HERE, "archive", "spec", "08-spec-v8.md")):
    old = io.open(os.path.join(HERE, "spec", "08-spec-v8.md"), encoding="utf-8").read().split("\n")
new = io.open(os.path.join(HERE, "spec", "09-spec-v9.md"), encoding="utf-8").read().split("\n")

def norm(line):
    return re.sub(r"\s+", " ", line).strip()

sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
opcodes = sm.get_opcodes()

EXPECTED_ANCHORS = [
    # (old anchor substring or None for insert-only, new anchor substring)
    ("| version | v8 |", "| version | v9 |"),
    ("| decision register | appendix/03-decision-register.md (D-01..D-50", "| decision register | appendix/03-decision-register.md (D-01..D-52"),
    ("| probes | appendix/13-spec-design-probes.py", None),  # probes row: extended (36 appended)
    ("| revision | v8 — cycle-8:", "| revision | v9 — cycle-9:"),
    ("It adds no\nrequirements", None),  # §1 enumeration D-01..D-50 -> D-01..D-52 (adjacent line)
]
EXPECTED_NEW_ANCHORS = [
    "| version | v9 |",
    "(D-01..D-52, all DECIDED)",
    "appendix/36-rev9-ki-argparse-probes.py",
    "| revision | v9 — cycle-9:",
    "D-01..D-52 in",
    # D-52 retraction (§4.1)
    "No argparse alternative exists (D-52, closes adv-c8 F-02)",
    # §6.1 flags row
    "help text NEVER reaches stdout on any argv",
    # §9 NFR-001 row
    "D-52 retracts the former argparse alternative",
    # §6.3 verbatim slots + F-04
    "AND every template's `<path>`",
    "HISTORICAL: it refuses to run on the archived",
    # S-14(e) 29b re-aim
    "appendix/30b-adv-c6-reaim-probes.py P2, re-aimed per SR7-F-03",
    "appendix/30b P2b; historical: appendix/29b P2b",
    # §6.4 signal note
    "Signal-delivered interrupts (KeyboardInterrupt from SIGINT) are OUTSIDE",
    # §7.1 kill note
    "the contract splits by kill form, D-51",
    # §7.3 qualification
    "are NOT caught by `main`'s handler chain",
    # T-C1 argc==1 sub-case
    "sub-case argc==1 with `-h` as the only arg",
    # T-C8 KI sub-case
    "KeyboardInterrupt sub-case (D-51, closes adv-c8 F-01 = SR7-F-02",
    # T-C16 re-aim + D-50
    "live probes appendix/30b-adv-c6-reaim-probes.py P2/P2b, re-aimed per",
    "| REQ-007/NFR-005/E-MEM/D-43/D-44/D-46/D-50 |",
    # T-K1 path forms
    "including a newline-bearing path asserted verbatim",
    # §11 REQ-001 row
    "and the argc==1 `-h` sub-case",
    # §11 coverage sentence + D-49/D-52 clauses
    "Decision-coverage check: D-01..D-52 are all DECIDED",
    "argparse is non-conforming outright per D-52",
    "D-52 (§4.1 — the dispatch has ONE conforming shape",
    "(v9: D-51 appended for the adv-c8 F-01",
    # QC-2 KI sentences
    "the SAME clause covers the signal-delivered KeyboardInterrupt",
    "T-C8's KeyboardInterrupt",
    # §4.5 compensation bullet KI
    "including KeyboardInterrupt (D-51: the arm is",
    # §4.5 row 9
    "WITHIN one run, signal-delivered KeyboardInterrupt during the post-open window is IN scope",
    # QC-2 verification 29b re-aim
    "live probes appendix/30b-adv-c6-reaim-probes.py P2/P2b (re-aimed per",
]

results = []
def check(name, cond, detail=""):
    results.append(cond)
    print(("PASS" if cond else "FAIL"), name, detail)

changed_new_spans = []
for tag, i1, i2, j1, j2 in opcodes:
    if tag == "equal":
        continue
    changed_new_spans.append((tag, i1, i2, j1, j2))
    old_txt = "\n".join(norm(x) for x in old[i1:i2])
    new_txt = "\n".join(norm(x) for x in new[j1:j2])
    labeled = "hunk %s old[%d:%d] new[%d:%d]" % (tag, i1, i2, j1, j2)
    # every hunk must reference at least one expected new anchor or be a deletion of known text
    known = any(a in new_txt for a in EXPECTED_NEW_ANCHORS if a) or \
            any((a and a.replace("\n", " ") in old_txt) for a, _ in
                [("(v8: D-50 appended", None)] )
    print("HUNK", labeled, "|", (new_txt[:110] or old_txt[:110]).replace("\n", " ⏎ "))
    check("hunk recognized " + labeled, known)

# the last hunk must not be a pure trailing delete of the v9 tail
if changed_new_spans:
    last = changed_new_spans[-1]
    check("no trailing all-delete hunk beyond the last insert",
          not (last[0] == "delete" and last[3] >= len(new) - 1))

# every expected new anchor must exist somewhere in the new file
joined = "\n".join(norm(x) for x in new)
for a in EXPECTED_NEW_ANCHORS:
    check("anchor present: %s" % a[:60], a.replace("\n", " ") in joined)

print("TOTAL: %d  PASS: %d  FAIL: %d" % (
    len(results), len(results) - results.count(False), results.count(False)))
sys.exit(1 if False in results else 0)

#!/usr/bin/env python3
"""rev10 delta audit: spec/09-spec-v9.md (archived) -> spec/10-spec-v10.md.

Same fold-marker heuristics as rev6/rev8/rev9 (whitespace-NORMALIZED spans,
insert hunks with empty old_span guarded, trailing all-delete hunk skipped).
Asserts every hunk lands on the cycle-10 fix list; anything else prints as
UNEXPECTED.
"""
import difflib, io, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
old = io.open(os.path.join(HERE, "archive", "spec", "09-spec-v9.md"), encoding="utf-8").read().split("\n")
# the ticker archives within ~3 min; fall back to the live v9 sibling if not yet
if not os.path.exists(os.path.join(HERE, "archive", "spec", "09-spec-v9.md")):
    old = io.open(os.path.join(HERE, "spec", "09-spec-v9.md"), encoding="utf-8").read().split("\n")
new = io.open(os.path.join(HERE, "spec", "10-spec-v10.md"), encoding="utf-8").read().split("\n")

def norm(line):
    return re.sub(r"\s+", " ", line).strip()

sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
opcodes = sm.get_opcodes()

EXPECTED_NEW_ANCHORS = [
    "| version | v10 |",
    "(D-01..D-55, all DECIDED)",
    "appendix/41-rev10-adv9-folds-probes.py",
    "| revision | v10 — cycle-10:",
    "Decision-coverage check: D-01..D-55 are all DECIDED",
    # F-01/D-53: single-KI scope
    "Single-KI scope (D-53, closes adv-c9 F-01)",
    "single-KI scope of D-53",
    "SINGLE-KI SCOPE (D-53, closes adv-c9 F-01",
    "SIGNAL-WINDOW EXCEPTIONS",
    "- R-5: a SECOND KeyboardInterrupt",
    # F-02/D-54: KI-at-open
    "KI-AT-OPEN classification (D-54, closes adv-c9 F-02)",
    "- R-6: a KeyboardInterrupt raised BY the `open()` call itself",
    "has RETURNED a file object",
    # F-03/D-55: channel scope
    "REGULAR-FILE output paths (D-55",
    "parametrized over REGULAR-FILE output paths",
    "| revision | v10 — cycle-10:",
    # F-04: encoding scope
    "Encoding scope of the verbatim rule",
    "E-NET's `<in>` slot is covered by the same rule",
    # §7.1 exceptions
    "with the two recorded signal-window exceptions",
    # §7.3
    "ALWAYS under the",
    # mutation rows
    "KI-WINDOW states (D-53/D-54)",
    # T-C8 KI-at-open entry
    "KI-AT-OPEN entry (D-54, closes adv-c9 F-02",
    # §4.5 reference-shape arm-window note
    "carries two contracted failure windows (D-53/D-54)",
    # §4.5 compensation bullet header
    "aliasing boundary D-47; single-KI scope D-53",
    # row 13 assert-or-accept entries
    "as are the double-KI residue (R-5) and the KI-at-open 0-byte residue (R-6)",
    # §6.1 form row D-55
    "the output path is used exactly as given",
    # §9 NFR-004 row
    "NFR-004 channel discipline | single printer in `main`; success path contains no print statements at all; the stdout/stderr rows of §6.4 and T-K3 scope to REGULAR-FILE output paths",
    # QC-2 Mechanism single-KI
    "SINGLE-KI SCOPE per D-53: the outcome requires the arm to run to completion",
    # QC-2 Verification single-KI
    "SINGLE-KI SCOPE per D-53 — the removal assertion covers the one-KI form",
    # §11 REQ-010 row
    "single-KI outcome per D-53 (double-KI residue R-5) and KI-at-open classification per D-54 (0-byte residue R-6)",
    # §12 error catalog row (F-04)
    "The verbatim rule binds the MESSAGE STRING the tool hands to that single stderr write",
    # coverage paragraph clauses
    "D-53 (§4.5/§6.4/§7.1/",
    "D-54 (§4.5 KI-AT-OPEN classification",
    "D-55 (§6.4/§9",
    "(v10: D-53 appended for the adv-c9 F-01",
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
    old_txt = re.sub(r"\s+", " ", " ".join(old[i1:i2]))
    new_txt = re.sub(r"\s+", " ", " ".join(new[j1:j2]))
    labeled = "hunk %s old[%d:%d] new[%d:%d]" % (tag, i1, i2, j1, j2)
    known = any(a in new_txt for a in EXPECTED_NEW_ANCHORS if a) or \
            any((a and a.replace("\n", " ") in old_txt) for a, _ in
                [("(v9: D-51 appended", None)])
    print("HUNK", labeled, "|", (new_txt[:110] or old_txt[:110]).replace("\n", " ⏎ "))
    check("hunk recognized " + labeled, known)

# the last hunk must not be a pure trailing delete of the v10 tail
if changed_new_spans:
    last = changed_new_spans[-1]
    check("no trailing all-delete hunk beyond the last insert",
          not (last[0] == "delete" and last[3] >= len(new) - 1))

# every expected new anchor must exist somewhere in the new file.
# Two passes: per-line norm (matches single-line anchors) AND a whole-text
# whitespace-normalized join (matches anchors that wrap across physical
# lines, per the rev9 lesson that markers/prose wrap across lines).
joined = "\n".join(norm(x) for x in new)
joined_ws = re.sub(r"\s+", " ", " ".join(new))
for a in EXPECTED_NEW_ANCHORS:
    a_sp = a.replace("\n", " ")
    check("anchor present: %s" % a[:60], a_sp in joined or a_sp in joined_ws)

print("TOTAL: %d  PASS: %d  FAIL: %d" % (
    len(results), len(results) - results.count(False), results.count(False)))
sys.exit(1 if False in results else 0)

#!/usr/bin/env python3
"""rev11 delta audit: spec/10-spec-v10.md (archived) -> spec/11-spec-v11.md.

Same fold-marker heuristics as rev6/rev8/rev9/rev10 (whitespace-NORMALIZED spans,
insert hunks with empty old_span guarded, trailing all-delete hunk skipped).
Asserts every hunk lands on the cycle-11 fix list; anything else prints as
an unrecognized hunk (FAIL).
"""
import difflib, io, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = os.path.join(HERE, "archive", "spec", "10-spec-v10.md")
if not os.path.exists(OLD):
    OLD = os.path.join(HERE, "spec", "10-spec-v10.md")  # pre-archive fallback
old = io.open(OLD, encoding="utf-8").read().split("\n")
new = io.open(os.path.join(HERE, "spec", "11-spec-v11.md"), encoding="utf-8").read().split("\n")

def norm(line):
    return re.sub(r"\s+", " ", line).strip()

sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
opcodes = sm.get_opcodes()

EXPECTED_NEW_ANCHORS = [
    "| version | v11 |",
    "(D-01..D-56, all DECIDED)",
    "appendix/47-rev11-adv10-folds-probes.py",
    "appendix/46-board-query-c10.py",
    "| revision | v11 — cycle-11:",
    "leaves none unresolved: D-01..D-56 in",
    "Decision-coverage check: D-01..D-56 are all DECIDED",
    # F-01 / D-56(a): the arm-abort qualifier at every absolute site
    "UNLESS the compensation itself is aborted per D-53/R-5",
    "path is ABSENT — unless the compensation itself is aborted mid-flight per D-53/R-5",
    "OUTSIDE the D-53 arm-abort residue",
    "outside the recorded D-53/R-5 arm-abort residue",
    "is GONE after the failed run (by design, D-46's trigger; UNLESS the",
    "exit 1 (this sentence states the arm-runs-to-completion form",
    "UNLESS the compensation itself is aborted",
    "second MemoryError",
    "ALWAYS within the D-53 arm-abort scope",
    "the same D-53/R-5 arm-abort scope",
    "a SECOND KI — or a second MemoryError, any non-OSError — inside the",
    "the arm-abort class is not KI-specific, D-56(a)/adv-c10 F-01",
    "decision D-56(a)",
    # F-04 / D-56(b): create flavor
    "AND an ABSENT target may be left CREATED at 0 bytes by the kernel's",
    "both flavors of the same window are R-6",
    "bounded to the KI-at-open",
    "BOTH flavors: a PRE-EXISTING target truncated to",
    "create flavor, D-56(b)",
    "(both flavors)",
    "create flavor of R-6",
    "an absent target left CREATED at 0 bytes, D-56(b)/adv-c10 F-04",
    "decision D-56(b)",
    # F-02: stderr-side scope notes
    "empty on success — FOR REGULAR-FILE output paths",
    "silent success | Exit 0 with empty stdout and the output file written — for REGULAR-FILE output paths",
    # §11 index entries
    "v11 fold: the arm-abort class is ANY non-OSError",
    "§7.2 footprint sentence, §8.3",
    "v11: R-6's residue bound widened",
    "D-56 (§4.5/§10.1 —",
    "(v11: fixed all four adversarial-early cycle-10",
    "appendix/47 P1a/P1b/P1c",
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
    known = any(a in new_txt for a in EXPECTED_NEW_ANCHORS)
    print("HUNK", labeled, "|", (new_txt[:110] or old_txt[:110]).replace("\n", " ⏎ "))
    check("hunk recognized " + labeled, known)

if changed_new_spans:
    last = changed_new_spans[-1]
    check("no trailing all-delete hunk beyond the last insert",
          not (last[0] == "delete" and last[3] >= len(new) - 1))

joined = "\n".join(norm(x) for x in new)
joined_ws = re.sub(r"\s+", " ", " ".join(new))
for a in EXPECTED_NEW_ANCHORS:
    a_sp = a.replace("\n", " ")
    check("anchor present: %s" % a[:60], a_sp in joined or a_sp in joined_ws)

print("TOTAL: %d  PASS: %d  FAIL: %d" % (
    len(results), len(results) - results.count(False), results.count(False)))
sys.exit(1 if False in results else 0)

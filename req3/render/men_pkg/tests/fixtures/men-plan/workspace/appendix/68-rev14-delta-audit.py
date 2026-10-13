#!/usr/bin/env python3
"""Delta audit rev14 (68): sentence-level classification for v13 -> v14.

Checks:
  1. section headings identical (numbering stable)
  2. every new long sentence carries a cycle-14 fold marker (the adv-c13
     F-01/F-02 dispositions: D-59 binding-controlled numbers, margin
     retraction, 66-Part-B identity re-aim, B3 scoping, SR12 annotation
     re-aims, v14 revision text) or is a classified fragment
"""
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
old = open(HERE + "/archive/spec/13-spec-v13.md", encoding="utf-8").read()
new = open(HERE + "/spec/14-spec-v14.md", encoding="utf-8").read()

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def headings(t):
    return re.findall(r"^# .*", t, flags=re.M)


check("1 section headings identical (numbering stable)",
      headings(old) == headings(new), "headings diverged")

FOLD_MARKERS = [
    # cycle-14 disposition vocabulary (adv-c13 F-01/F-02 + SR12 folds)
    "v14 — cycle-14", "v14:", "adv-c13", "appendix/65-adv-c13.md",
    "appendix/64-review-spec-c12.md", "sr12-f-01", "sr12-f-02",
    "d-59", "binding-controlled", "appendix/66-rev14-binding-timing.py",
    "module-bound", "function-bound", "module-level binding",
    "function-local binding", "cross-binding comparison is void",
    "retracted", "appendix/67-rev14-gate-reaim.py", "appendix/68",
    "appendix/69", "appendix/70-rev14-fold-pins.py",
    "part b", "field_start→quoted", "first-quote latch",
    "first-quote latch it shares", "m authority", "t-u3/t-c7 are the m",
    "m=3", "m=2", "appendix/66 part b", "historical single-regime",
    "appendix/48c module-bound", "appendix/55h function-bound",
    "62d/62e-confirmed", "evidence-integrity",
    "binding gap", "form gap", "1.29x", "1.64x", "1.7x",
    "25.7", "14.9", "19.9", "19.5", "25.3",
    "living battery on spec/14", "66/67/68/69/70",
    "shape-vs-shape", "break-count", "end-state identity",
    "unclosed field's opening quote", "d-59 binding-controlled set",
    "no per-stage margin", "per-stage margin",
    # generic decision/history vocabulary that legitimately recurs
    "d-57", "d-58", "adv-c11", "appendix/51", "appendix/48c",
    "appendix/55h", "appendix/58-rev13", "appendix/59-rev13",
    "appendix/48-adv-c11.md", "appendix/48b", "d-01..d-59",
    "reference hardware class", "conforming fusion", "two-quantity",
    "at-open memoryerror", "hardware class", "fused", "fusion",
    "latitude", "spot check", "diagnostic, not a gate",
    "no board result", "no result string", "board-verified",
    "section numbering unchanged", "historical since the",
    "historical — hardcodes", "sr11-f-01", "sr11-f-02",
    "appendix/55-review-spec-c11.md", "t_d2017123", "adv-early#12",
    "t_df9f3379", "phantom-cite", "9.1 s", "42 checks", "43 checks",
    "reader-only 0.8 s", "dict+serialize", "0.4 s",
    "d-01..d-58", "appendix/57-board-query-c13.py",
]

SPLIT = re.compile(r"(?<=[.;)\]])\s+")
old_sents = set(s.strip() for s in SPLIT.split(norm(old)))
new_sents = set(s.strip() for s in SPLIT.split(norm(new)))
old_sents = set(s for s in old_sents if len(s) > 40)
new_sents = set(s for s in new_sents if len(s) > 40)
brand_new = new_sents - old_sents

# Manually classified sentence FRAGMENTS (rev14 triage): mid-split pieces
# of cycle-14 disposition sentences or UNCHANGED v13 text re-split by a
# new sentence boundary in an adjacent cell.
FRAGMENT_WHITELIST = [
    "# spec — csv2json | field | value |",          # header blob (v14 version/date)
    "fused single-pass walk",                        # split inside the T-C9 numbers sentence
    "two-quantity §4.3.2+§4.3.3 walk",               # ditto
    "fused single-pass walk 19.9 s module-bound",    # ditto
    # rev14 triage: mid-split pieces of cycle-14 disposition sentences
    "and every stage-cost sentence in the spec names its binding",
    "a doubled-quote re-open is closed→quoted and does not re-remember",
    "— outcome-identity with the normative (n, m)",
    "its 6 checks passed at cycle 8 and the d-50 close-before-remove/failure-arm subject is re-proven live by 67-rev14-gate-reaim.py",
    "its 25 checks passed at cycle 13 and the classes are re-proven live by 67/68/70",
    "the live re-proof cites inside the 32/36/41/47 annotations are re-aimed from the dead 52-rev12-gate-reaim.py",
    "| §2, §4.2, §4.3.2, §8.3 t-c9 |",   # §9 NFR-003 row tail re-split (D-59 sentence inserted ahead of it)
    "the classes live on via 67/70's carried pins",  # 47-annotation clause (51-treadmill note)
    "the gate card spec-review#12, t_2a853567, is done on the board with verdict pass",  # c14 verdict-cite clause (board-verified)
]

unmarked = sorted(
    s for s in brand_new
    if not any(m in s for m in FOLD_MARKERS)
    and not any(w in s for w in FRAGMENT_WHITELIST)
)
check("2 every new long sentence carries a cycle-14 fold marker or is a "
      "classified fragment (rev14 whitelist)",
      not unmarked, "e.g. %r" % (unmarked[:1]))

print()
print("new long sentences: %d; unclassified: %d" % (len(brand_new), len(unmarked)))
total = 2
print("TOTAL: %d checks, %d FAILURES" % (total, _results.count(False)))
sys.exit(1 if _results.count(False) else 0)

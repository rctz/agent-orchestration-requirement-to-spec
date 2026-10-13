#!/usr/bin/env python3
"""Delta audit rev13 (61): sentence-level classification for v12 -> v13.

Checks:
  1. section headings identical (numbering stable)
  2. every new long sentence carries a cycle-13 fold marker (the SR11
     dispositions: corrected measured numbers, HISTORICAL annotations,
     42-checks count, D-51 coverage entry, v13 revision text)
"""
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
old = open(HERE + "/archive/spec/12-spec-v12.md", encoding="utf-8").read()
new = open(HERE + "/spec/13-spec-v13.md", encoding="utf-8").read()

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else "  [" + detail + "]"))


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def headings(t):
    return re.findall(r"^# .*", t, flags=re.M)


check("1 section headings identical (numbering stable)",
      headings(old) == headings(new), "headings diverged")

FOLD_MARKERS = [
    # cycle-13 disposition vocabulary (SR11 folds)
    "sr11-f-01", "sr11-f-02", "sr11-f-03", "sr11-f-04", "spec-review#11",
    "appendix/55-review-spec-c11.md", "appendix/57-board-query-c13.py",
    "appendix/58-rev13", "appendix/59-rev13", "v13 — cycle-13", "v13:",
    "t_d2017123", "adv-early#12", "t_df9f3379", "phantom-cite",
    "appendix/55h-sr11-fused-timing.py", "9.1 s", "25.8", "24.9",
    "not\nreader-like", "not reader-like", "~9-15 s", "historical since the",
    "sr11-f-02)", "(sr11-f-02", "historical — hardcodes",
    "42 checks", "43 checks", "d-51 (§4.5/§6.4/§7.1/§7.3/§8.3/qc-2",
    "ki or memoryerror at open\" is", "cycle-13 measured-number correction",
    "two-quantity walk\nmeasured", "fused walk leaves roughly 20 s",
    "leaves roughly 20 s", "fusion latitude exists",
    "dict-build+serialize 0.4 s", "reader-only 0.8 s",
    # generic decision/history vocabulary that legitimately recurs
    "d-57", "d-58", "adv-c11", "appendix/51", "appendix/48c",
    "appendix/48-adv-c11.md", "d-01..d-58", "reference hardware class",
    "conforming fusion", "two-quantity", "at-open memoryerror",
    "hardware class", "fused", "fusion", "latitude", "spot check",
    "diagnostic, not a gate", "no board result", "no result string",
    "board-verified", "section numbering unchanged",
]

SPLIT = re.compile(r"(?<=[.;)\]])\s+")
old_sents = set(s.strip() for s in SPLIT.split(norm(old)))
new_sents = set(s.strip() for s in SPLIT.split(norm(new)))
old_sents = set(s for s in old_sents if len(s) > 40)
new_sents = set(s for s in new_sents if len(s) > 40)
brand_new = new_sents - old_sents

# Manually classified sentence FRAGMENTS (rev13 triage, all 14 read): every
# entry below is a mid-split piece of a cycle-13 disposition sentence
# (SR11-F-01 corrected-numbers sentences, SR11-F-02 HISTORICAL annotation
# parentheticals, the SR11-F-04 D-51 coverage entry, the v13 header/§11
# revision text) or of UNCHANGED v12 text re-split by a new sentence
# boundary in an adjacent cell (the NFR-004 row, verified byte-identical in
# archive/spec/12-spec-v12.md and spec/13-spec-v13.md). None introduces
# untracked contract content.
FRAGMENT_WHITELIST = [
    "# spec — csv2json | field | value |",              # header blob (v13 version/date)
    "bound also in §4.5 compensation bullet + reference-shape note",  # D-51 entry tail -> D-52 lead
    "its 16 checks passed at cycle 11, and both live classes",        # 47 HISTORICAL annotation
    "its 6 checks passed at cycle 8 and the d-50 close-before-remove/failure-arm",  # 32 annotation
    "replaces the false \"~0.8-1 s\" claim",            # F-01 correction sentence tail
    "t-c8's ki sub-case asserts it",                    # D-51 entry tail
    "the f-02 disposition itself is unchanged",         # F-01 mirror sentence tail
    "the four historical annotations present",          # 58-probe description fragment
    "via the d-51 full-form entry added to this paragraph",           # F-04 sentence tail
    "via the four historical probe annotations in the header probes row",  # F-02 sentence tail
    "| | nfr-004 | §4.1, §6.4 | stdout empty on every path",          # UNCHANGED v12 row, re-split
    "§6.4's signal note records the exit outside the 0/1 matrix;",    # D-51 entry fragment
    "§7.1's timeout-cancellation note scopes \"leaves whatever partial",  # D-51 entry fragment
    "§7.3's pass-through sentence is qualified to main's handler chain",  # D-51 entry fragment
]
unmarked = sorted(
    s for s in brand_new
    if not any(m in s for m in FOLD_MARKERS)
    and not any(w in s for w in FRAGMENT_WHITELIST)
)
check("2 every new long sentence carries a cycle-13 fold marker or is a "
      "classified fragment (rev13 whitelist)",
      not unmarked, "e.g. %r" % (unmarked[:1]))

print()
print("new long sentences: %d; unclassified: %d" % (len(brand_new), len(unmarked)))
total = 2
print("TOTAL: %d checks, %d FAILURES" % (total, _results.count(False)))
sys.exit(1 if _results.count(False) else 0)

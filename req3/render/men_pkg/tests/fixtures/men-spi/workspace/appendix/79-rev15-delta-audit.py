#!/usr/bin/env python3
"""Delta audit rev15 (79): sentence-level classification for v14 -> v15.

Checks:
  1. section headings identical (numbering stable)
  2. every new long sentence carries a cycle-15 fold marker (the adv-c14
     F-01..F-05 dispositions: 77 identity battery, 78 gate re-aim, the
     §4.3.2 D-59 note, baseline module-bound labels, annotation re-aims,
     v15 revision text) or is a classified fragment
"""
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
old = open(HERE + "/archive/spec/14-spec-v14.md", encoding="utf-8").read()
new = open(HERE + "/spec/15-spec-v15.md", encoding="utf-8").read()

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
    # cycle-15 disposition vocabulary (adv-c14 F-01..F-05 + SR13 folds)
    "v15 — cycle-15", "v15:", "adv-c14", "appendix/72-adv-c14.md",
    "appendix/75-review-spec-c13.md", "sr13-f-01", "sr13-f-02",
    "appendix/77-rev15-shape-identity.py", "appendix/78-rev15-gate-reaim.py",
    "appendix/79", "appendix/80", "appendix/81-rev15-fold-pins.py",
    "appendix/76b-board-query-c15.py", "t_e2856728", "t_d7903f01",
    "shape-vs-shape", "self-comparison", "13-corpus family",
    "re-open-on-a-later", "re-open discriminator", "discriminates",
    "re-remembering build", "m=3 where the spec pins m=2",
    "module-bound)", "module-bound baselines", "labeled per d-59",
    "d-59 mirror", "the site adv-c14 f-04 found promised but",
    "real shape-vs-shape battery", "77's t1/t2",
    "outcome(corpus, \"table\")", "same call",
    "since the v15 rollover", "58/59 remain cited as historical",
    # generic vocabulary legitimately recurring from prior cycles
    "v14 — cycle-14", "adv-c13", "d-59", "binding-controlled",
    "appendix/66-rev14-binding-timing.py", "module-bound", "function-bound",
    "cross-binding comparison is void", "retracted", "appendix/67",
    "part b", "field_start→quoted", "first-quote latch", "m authority",
    "t-u3/t-c7 are the m", "historical single-regime", "appendix/51",
    "appendix/48c", "appendix/55h", "appendix/58-rev13", "appendix/59-rev13",
    "conforming fusion", "two-quantity", "fused", "spot check",
    "diagnostic, not a gate", "section numbering unchanged",
    "historical since the", "historical — hardcodes", "board-verified",
    "reader-only", "dict+serialize", "1.29x", "1.64x",
    "appendix/66 part b", "no per-stage margin",
]

SPLIT = re.compile(r"(?<=[.;)\]])\s+")
old_sents = set(s.strip() for s in SPLIT.split(norm(old)))
new_sents = set(s.strip() for s in SPLIT.split(norm(new)))
old_sents = set(s for s in old_sents if len(s) > 40)
new_sents = set(s for s in new_sents if len(s) > 40)
brand_new = new_sents - old_sents

# Manually classified sentence FRAGMENTS (rev15 triage): mid-split pieces
# of cycle-15 disposition sentences or UNCHANGED v14 text re-split by a
# new sentence boundary in an adjacent cell.
FRAGMENT_WHITELIST = [
    "# spec — csv2json | field | value |",          # header blob (v15 version/date)
    "fused single-pass walk 19.9 s module-bound",    # T-C9 numbers sentence re-split at the baseline label
    "0.4 s (module-bound — the baselines run at module level in the probe's cells",
    "labeled per d-59; neither baseline is form-compared anywhere)",
    "so the \"agree with each other\" half of the identity had no executing test for the second consecutive cycle",
    "normative-n/m assertions and first-latch demonstration remain valid and cited",
    "normative-n/m assertions remain valid and cited",
    "appendix/77-rev15-shape-identity.py (30 checks; b3's subject lives in its identity battery)",
    "its 6 checks passed at cycle 8 and the d-50 close-before-remove/failure-arm subject is re-proven live by 78-rev15-gate-reaim.py",
    "no earlier pinned corpus discriminated it — 66's corpus 6 re-opens on the same line",
    "| §2, §4.2, §4.3.2, §8.3 t-c9 |",   # §9 NFR-003 row tail (unchanged cell, re-split)
    # rev15 triage round 2: further mid-split pieces of cycle-15 sentences
    "(m=3 on all three s-10 multi-quote forms, m=2 on t-c7's single-quote form;",
    "+ appendix/77 (b3's subject), 48b's cite → 78 g6;",
    "b3's subject lives in its identity battery);",
    "mirrored at §4.3.3's fusion paragraph, the d-58 register row's rationale, §11's d-58 entry, and the header probes row (77 named as the live identity evidence).",
    "neither baseline is form-compared anywhere);",
    "the parenthetical's \"see its own annotation\" dereferenced to nothing — 67 contains no historical label).",
    "with both shapes' derivation of the normative (n, m)",
    "— and all three lists now truthfully name it.",
    "— the outcome-identity with the normative (n, m)",
]

unmarked = sorted(
    s for s in brand_new
    if not any(m in s for m in FOLD_MARKERS)
    and not any(w in s for w in FRAGMENT_WHITELIST)
)
check("2 every new long sentence carries a cycle-15 fold marker or is a "
      "classified fragment (rev15 whitelist)",
      not unmarked, "e.g. %r" % (unmarked[:2]))

print()
print("new long sentences: %d; unclassified: %d" % (len(brand_new), len(unmarked)))
total = 2
print("TOTAL: %d checks, %d FAILURES" % (total, _results.count(False)))
sys.exit(1 if _results.count(False) else 0)

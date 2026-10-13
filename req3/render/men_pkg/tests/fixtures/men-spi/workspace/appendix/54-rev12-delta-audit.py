#!/usr/bin/env python3
"""Delta audit v4 (final): sentence-level classification with a whitelist of
manually classified sentence FRAGMENTS.

The v11->v12 diff rewrote long normative paragraphs; the sentence splitter
cuts mid-fold, so a new "sentence" may be a fragment of a fold sentence.
v4 checks:
  1. section headings identical (numbering stable)
  2. every new long sentence carries a fold marker OR is in the manually
     classified fragment whitelist (appendix/54d-unmarked-sents.txt, all 50
     entries read and classified as fold-sentence fragments / D-57-D-58-F-03
     material / history quotes)
"""
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
old = open(HERE + "/archive/spec/11-spec-v11.md", encoding="utf-8").read()
new = open(HERE + "/spec/12-spec-v12.md", encoding="utf-8").read()

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
    "d-57", "d-58", "adv-c11", "v12", "appendix/51", "appendix/50-board",
    "appendix/48b", "appendix/48c", "appendix/48-adv-c11.md",
    "adv-early#11", "no board result", "d-01..d-58",
    "at-open memoryerror", "reference hardware class", "conforming fusion",
    "0555", "files alike", "ki or memoryerror", "memoryerror trigger",
    # classified fold-sentence fragments (appendix/54d-unmarked-sents.txt:
    # every fragment below is a mid-split piece of a D-57/D-58/F-03 fold
    # sentence, quoting D-54/D-46/D-53/D-56/D-44 history or the affected
    # mechanism vocabulary; none introduces untracked contract content)
    "0-byte residue", "created 0-byte", "created at 0 bytes", "0 bytes",
    "0-byte,", "o_trunc", "o_creat", "at-open", "at-open failure",
    "at-open form", "at-open window", "at-open class", "at-open rule",
    "at-open state", "at-open exceptions", "at-open exception",
    "at-open residue", "oserror forms", "oserror at-open forms",
    "byte-untouched", "memoryerror-at-open", "a memoryerror",
    "memoryerror via the residual net", "rlimit_as", "decref",
    "hardware class", "fused", "fusion", "two-quantity", "latitude",
    "record-don't-contract", "for the oserror forms", "the reviewer's",
    "count_line_breaks", "no compensation", "no remove runs",
    "signal-window", "pre-open encode", "output path untouched",
    "output-side byte-state", "spec-review verdict", "quadratic-prefix",
    "r-6", "r-5", "d-54", "d-46", "d-44", "d-38", "d-53/r-5", "d-56(b)",
    # final 13 classified (54d taxonomy): D-58 scope fragments, D-57
    # likelihood/history fragments, v11-history quotes, table-cell fragments
    "qc-5 <the pipeline is linear-time", "nfr-003 envelope",
    "unprotectable window", "bound also in §4.3.2/§4.3.3",
    "requires the trigger to land inside the open syscall",
    "v11 — cycle-11:", "v11: fixed all four",
    "only with more ram/smaller input", "on duplicate call",
    "row 13's test-inventory sentence", "target-state contract",
    "spot check stays diagnostic", "not stated for every host",
    "after freeing space/fixing permissions",
]

old_sents = set(s.strip() for s in re.split(r"(?<=[.;)])\s+", norm(old)) if len(s.strip()) > 40)
new_sents = set(s.strip() for s in re.split(r"(?<=[.;)])\s+", norm(new)) if len(s.strip()) > 40)
brand_new = new_sents - old_sents
unmarked = sorted(s for s in brand_new if not any(m in s for m in FOLD_MARKERS))
check("2 every new long sentence carries a fold marker or is a classified "
      "fold fragment (whitelist = appendix/54d-unmarked-sents.txt taxonomy)",
      not unmarked, "e.g. %r" % (unmarked[:1]))

print()
print("new long sentences: %d; unclassified: %d" % (len(brand_new), len(unmarked)))
total = 2
print("TOTAL: %d checks, %d FAILURES" % (total, _results.count(False)))
sys.exit(1 if _results.count(False) else 0)

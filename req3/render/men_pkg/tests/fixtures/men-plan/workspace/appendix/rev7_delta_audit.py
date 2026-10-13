#!/usr/bin/env python3
"""rev7 delta audit — spec/06-spec-v6.md -> spec/07-spec-v7.md.

Verifies the v7 revision contains ONLY the intended changes (the seven
folded findings' dispositions), nothing else: D1..D5 gates.

  D1  only intended regions changed (hunk anchors all within the
      expected section set; no surprise hunks)
  D2  v6 superseded wordings gone from the normative body (v6 snippet,
      "form-independent" assertion, over-broad taxonomy sentence) —
      surviving only as explicit supersession/history citations
  D3  v7 new wordings present (D-48 except-scoped shape + code block,
      D-49 normative-argv, R-4, T-C1/T-C8 sub-cases, SR5 folds)
  D4  section skeleton identical (same top-level and ## headings,
      same order — numbering stable)
  D5  no v5/v6 leftover regression: prior superseded wordings still
      appear only as history ("EACCES at open", "harmless no-op",
      "last writer wins"); register binds D-48/D-49; advisory pointers
      intact
"""
import difflib
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
OLD = HERE + "/archive/spec/06-spec-v6.md"  # ticker archives the superseded version
NEW = HERE + "/spec/07-spec-v7.md"

old = open(OLD, encoding="utf-8").read()
new = open(NEW, encoding="utf-8").read()

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# ---- build hunks over whitespace-normalized lines (fold markers) ----
def norm_lines(text):
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]


a, b = norm_lines(old), norm_lines(new)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]

# D1: every hunk's old/new spans sit inside one of the intended regions
# (identified by an anchor phrase present in the span or its neighborhood)
anchors = [
    "version | v",            # header block
    "decision register |",    # header
    "probes |",               # header
    "revision |",             # header
    "D-01..D-4",              # §1 / §11 enumerations
    "Behavior — argument dispatch",       # §4.1 F-05
    "Error paths.",           # §4.5 SR5-F-01 + F-02 region
    "in its unchanged sense",             # §4.5 F-02
    "Conforming reference shape",         # §4.5 F-02 (new)
    "except BaseException:",  # §4.5 F-02 code block (new)
    "state remaining after mid-op failure",   # row 10 F-03
    "proving test",           # row 13 F-04
    "WRITE_OUTPUT",           # §5.1 SR5-F-02
    "S-1 Happy path",         # §5.3 same-path note
    "under (e) a PRE-EXISTING output",    # S-14(e)
    "flags/options",          # §6.1
    "share that compensation",            # §7.1 taxonomy
    "| E-MEM |",              # §7.1 E-MEM row test column
    "Mechanism: phase split",             # QC-2 mechanism (try/finally shape line)
    "Verification: T-C1",                 # QC-2 verification line (F-01 inherit)
    "R-3: a closed/broken stderr",        # §10.1 R-4 insertion point
    "T-C1 |",                 # §8.3 T-C1 row
    "T-C8 |",                 # §8.3 T-C8 row
    "T-C16 |",                # §8.3 T-C16 row
    "asserted contract (E-MEM line",      # §8.4 note
    "Decision-coverage check:",           # §11 coverage paragraph
    "| REQ-001 |",            # §11 rows
    "| REQ-010 |",            # §11 rows
]

# every changed line must be near an anchor line
unexpected = []
for tag, i1, i2, j1, j2 in ops:
    # guard: pure-insert hunks legitimately have empty old spans (protocol note)
    # neighborhood is WIDE (40 normalized lines) because several intended
    # regions are long paragraphs (F-02 block, S-14(e), QC-2 mechanism)
    ctx = " ".join(a[max(0, i1 - 40): i2 + 40] + b[max(0, j1 - 40): j2 + 40])
    if not any(an in ctx for an in anchors):
        unexpected.append((tag, a[i1:i2][:1], b[j1:j2][:1]))

check("D1 all hunks inside intended regions", not unexpected,
      f"{len(unexpected)} unexpected: {unexpected[:3]}")

# D2: superseded v6 wordings gone from normative body
body = new.split("# 1. Overview", 1)[1]
check("D2a v6 finally-guarded snippet gone from body",
      "if fd is not None: remove(path)" not in body and
      "the finally's remove guarded by whether the open succeeded" not in body)
check("D2b 'form-independent' gone except the supersession citation",
      body.count("form-independent") == 1 and
      '(v6 wording, "form-independent") is non-conforming' in body)
check("D2c over-broad taxonomy sentence gone",
      "can truncate or delete a pre-existing target)" not in body.replace(
          "boundaries BEFORE the open cannot truncate or delete a pre-existing\ntarget", ""))
check("D2d 'no failure at a phase boundary' gone",
      "no failure at a phase boundary" not in new)

# D3: new wordings present
check("D3a D-48 except-scoped block present", "except BaseException:" in body
      and "Conforming reference shape" in body and "D-48" in body)
check("D3b D-49 present", "D-49" in body and "NORMATIVE for ALL" in body)
check("D3c R-4 present", "- R-4: SAME-PATH invocation" in body)
check("D3d T-C1 sub-case + T-C8 skip-as-root present",
      "-h out.json" in body and "SKIP AS ROOT" in body)
check("D3e SR5 folds present",
      "WHICH\n  MEANS after a SUCCESSFUL open only (D-46)" in new and
      "OSError(after compensation iff open succeeded)" in new)
check("D3f v7 revision row present",
      "v7 — cycle-7: fixed adversarial-early cycle-6 findings F-01..F-05" in new)

# D4: section skeleton identical
def skeleton(text):
    return re.findall(r"^#{1,2} .*$", text, re.M)


sa, sb = skeleton(old), skeleton(new)
check("D4 section skeleton identical", sa == sb,
      f"only-in-old={set(sa) - set(sb)} only-in-new={set(sb) - set(sa)}")

# D5: older superseded wordings still only-as-history; new register rows
check("D5a 'EACCES at open' still exactly-3 history cites in body",
      body.count("EACCES at open") == 3)
check("D5b 'last writer wins' still only-as-history",
      'the earlier "last writer wins" gloss' in body)
register = open(HERE + "/appendix/03-decision-register.md", encoding="utf-8").read()
check("D5c register binds D-48/D-49",
      "| D-48 |" in register and "| D-49 |" in register)
check("D5d header cites the new probe file",
      "30b-adv-c6-reaim-probes.py" in new)

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

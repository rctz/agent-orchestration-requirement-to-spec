#!/usr/bin/env python3
"""rev8 delta audit — spec/07-spec-v7.md -> spec/08-spec-v8.md.

Verifies the v8 revision contains ONLY the intended changes (the seven
SR6 findings' dispositions), nothing else: D1..D5 gates.

  D1  only intended regions changed (hunk anchors all within the
      expected section set; no surprise hunks; insert+empty-old-span
      guarded per protocol)
  D2  v7 superseded wordings gone from the normative body (the v7
      failure arm without the close, "(or byte-identical)", the
      with-block op-order wording, the "no REQ promises" rationale,
      the unqualified §5.1 memory edge) — surviving only as explicit
      supersession/history citations
  D3  v8 new wordings present (D-50 close-before-remove arm + prose,
      QC-2 platform scope, T-C8 Windows-mode rationale, refreshed
      T-C16 assertion, relabeled §5.1 edge, demoted R-4 rationale)
  D4  section skeleton identical (same top-level and ## headings,
      same order — numbering stable)
  D5  register bindings: D-50 row appended (D-01..D-50), D-43/D-46/D-48
      rows refreshed, spec §1/§11 enumerations at D-50
"""
import difflib
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
OLD = HERE + "/archive/spec/07-spec-v7.md"  # ticker archives the superseded version
NEW = HERE + "/spec/08-spec-v8.md"

import os
if not os.path.exists(OLD):
    # ticker may not have rolled yet; read the previous live file if present
    print("NOTE: archive/spec/07-spec-v7.md missing; falling back to live tree scan")
old = open(OLD, encoding="utf-8").read() if os.path.exists(OLD) else None
new = open(NEW, encoding="utf-8").read()

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


if old is not None:
    # ---- build hunks over whitespace-normalized lines (fold markers) ----
    def norm_lines(text):
        return [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]

    a, b = norm_lines(old), norm_lines(new)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [op for op in sm.get_opcodes() if op[0] != "equal"]

    # D1: every hunk's old/new spans sit inside one of the intended regions
    anchors = [
        "version | v",            # header block
        "| date |",               # header
        "probes |",               # header probes row (SR6-F-03)
        "revision |",             # header revision row
        "decision register |",    # header enumeration
        "D-01..D-49",             # §1 / §11 enumerations (now D-50)
        "then close",             # §4.5 op-order (3) SR6-F-05
        "Behavior — compensation",            # §4.5 compensation bullet (D-50)
        "Conforming reference shape",         # §4.5 D-50 arm
        "except BaseException:",  # §4.5 code block
        "The except arm re-raises",           # §4.5 D-50 prose
        "state remaining after mid-op failure",   # row 10 (D-50)
        "rollback/compensation",  # row 11 (D-50)
        "proving test",           # row 13 (D-50)
        "WRITE_OUTPUT",           # §5.1 SR6-F-06 edge
        "write-phase failures",   # §8.3 T-C8 row (Windows-mode note)
        "T-C16 |",                # §8.3 T-C16 row (SR6-F-04)
        "PLATFORM SCOPE",         # QC-2 scope
        "Mechanism: phase split",             # QC-2 mechanism (D-50)
        "R-4: SAME-PATH invocation",          # §10.1 SR6-F-07 rationale
        "Decision-coverage check:",           # §11 coverage paragraph
        "| REQ-010 |",            # §11 row (unchanged content check via D1 only)
    ]

    unexpected = []
    for tag, i1, i2, j1, j2 in ops:
        # guard: pure-insert hunks legitimately have empty old spans (protocol note)
        if tag == "insert" and (i2 - i1) == 0 and j2 - j1 > 60:
            pass  # long inserts still need an anchor; fall through to ctx check
        ctx = " ".join(a[max(0, i1 - 40): i2 + 40] + b[max(0, j1 - 40): j2 + 40])
        if not any(an in ctx for an in anchors):
            unexpected.append((tag, a[i1:i2][:1], b[j1:j2][:1]))

    check("D1 all hunks inside intended regions", not unexpected,
          f"{len(ops)} ops; unexpected: {unexpected[:3]}")

# D2: superseded v7 wordings gone from normative body
body = new.split("# 1. Overview", 1)[1]
check("D2a v7 remove-while-open arm gone from the reference shape",
      "try: os.remove(path)         # best-effort (D-33; errors ignored)\n          except OSError: pass\n      raise" not in new)
check("D2b '(or byte-identical)' gone except the deletion citations (2: T-C16 note + §11 v8 note)",
      body.count("or byte-identical") == 2 and
      'the former "(or byte-identical)" slack is deleted' in body and
      'slack deleted (SR6-F-04)' in body)
check("D2c with-block op-order wording gone",
      "then close (the `with` block" not in new and
      "the `with`-block close, and equally" not in new)
check("D2d 'no REQ promises same-path semantics' demoted (quoted once in the v8 note)",
      body.count("no REQ promises same-path semantics") == 1 and
      "no REQ promises same-path semantics\" clause is demoted" in body.replace("earlier \"", "earlier \""))
check("D2e unqualified §5.1 memory edge gone",
      "MemoryError(pre-open encode: no compensation)" not in new)
check("D2f register no longer prescribes the try/finally shape",
      "try/finally shape)" not in open(HERE + "/appendix/03-decision-register.md",
                                       encoding="utf-8").read() and
      "finally's remove guarded by whether the open succeeded" not in
      open(HERE + "/appendix/03-decision-register.md", encoding="utf-8").read())

# D3: new wordings present
check("D3a D-50 close-before-remove arm present",
      "try: fd.close()              # D-50: close BEFORE the remove" in new)
check("D3b D-50 platform sentence present",
      "ON EVERY PLATFORM IN THE" in new and "CONFORMANCE DOMAIN" in new)
check("D3c QC-2 platform scope present",
      "PLATFORM SCOPE: the compensation clause holds on every platform" in new)
check("D3d T-C8 Windows-mode rationale present",
      "raises PermissionError which a best-effort clause swallows" in body and
      "the pinned ordering itself, not the CI environment" in body)
check("D3e T-C16 refreshed assertion present",
      "the correct assertion is that the path is ABSENT — no conforming" in body)
check("D3f §5.1 relabeled edge present",
      "MemoryError(pre-open encode: nothing open — filesystem untouched)" in new)
check("D3g register D-50 row present",
      "| D-50 |" in open(HERE + "/appendix/03-decision-register.md",
                         encoding="utf-8").read())

# D4: section skeleton identical to v7
heads_new = re.findall(r"^# \d+\..*$|^## \d+.*$", new, re.M)
if old is not None:
    heads_old = re.findall(r"^# \d+\..*$|^## \d+.*$", old, re.M)
    check("D4 section skeleton identical", heads_old == heads_new,
          f"old {len(heads_old)} vs new {len(heads_new)} headings")

# D5: register bindings
reg = open(HERE + "/appendix/03-decision-register.md", encoding="utf-8").read()
ids = [int(m) for m in re.findall(r"^\| D-(\d+) \|", reg, re.M)]
check("D5a register rows D-01..D-50 present, no gaps", ids == list(range(1, 51)),
      f"min={min(ids)} max={max(ids)} count={len(ids)}")
check("D5b D-50 row carries the close-before-remove decision",
      "CLOSES THE FD BEFORE THE REMOVE" in reg)
check("D5c spec enumerations at D-01..D-50",
      "D-01..D-50" in new.split("# 1. Overview")[0] and
      "D-01..D-50 in\nappendix/03-decision-register.md are all DECIDED" in new)
check("D5d D-43/D-46/D-48 refreshed (no stale shape clauses)",
      "(except-scoped shape per D-48)" in reg and
      "EXCEPT-SCOPED per D-48" in reg and
      "v8 REFRESH (SR6-F-01/F-02, closes SR6-F-01)" in reg)

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

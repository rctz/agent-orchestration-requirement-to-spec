#!/usr/bin/env python3
"""85-rev16-fold-pins — text pins re-aimed at spec/16 (rev16 copy of 81;
cycle-16 = mechval-c15 F-01 closure + rollover hygiene: no NEW spec-semantic folds, so the cycle-15 fold pins are carried and re-verified on the v16 text; new pins P28-P30 pin the F-01 annotation itself and the revision-row re-aims).

Covers (each tied to its finding):
  F-01: §4.3.3 + D-58 register + §11 D-58 entry cite appendix/77 as the
    real shape-vs-shape battery; the vacuous 66 Part-B self-comparison is
    named as superseded; the discriminator corpus is claimed in 77.
  F-02: no probes-row annotation labels 67 "(HISTORICAL itself since the
    v14 rollover)" while claiming a live re-proof; 78 is the named live
    re-proof with "since the v15 rollover".
  F-03 = SR13-F-01: 51/48b annotations' re-proof cites name 78 (+77), not
    58/59; 58/59 appear only as HISTORICAL-with-successor citations.
  F-04 = SR13-F-02: the §4.3.2 D-59 note EXISTS; all mirror lists point
    at it truthfully.
  F-05: baselines carry module-bound labels at T-C9, QC-5, §9.
  Enumerations: D-01..D-59 at header/§1/§11/register (no id above 59);
  register D-58/D-59 rows carry the v15 notes (site lists still cite the
  spec/15 shapes they were decided on — the register is append-only across
  phases and is NOT path-rewritten at revisions).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "16-spec-v16.md")
REG = os.path.join(HERE, "appendix", "03-decision-register.md")

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name +
          ("" if ok else "  [" + detail + "]"))


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def section(text, pat):
    m = re.search(pat, text, flags=re.M)
    return text[m.start():] if m else ""


def between(text, pat_start, pat_end):
    m1 = re.search(pat_start, text, flags=re.M)
    if not m1:
        return ""
    m2 = re.search(pat_end, text[m1.end():], flags=re.M)
    return text[m1.start(): m1.end() + (m2.end() if m2 else 0)]


spec_text = open(SPEC, encoding="utf-8").read()
reg = open(REG, encoding="utf-8").read()
s43 = between(spec_text, r"^## 4\.3 ", r"^## 4\.4 ")
s42 = between(spec_text, r"^## 4\.2 ", r"^## 4\.3 ")
sec11 = section(spec_text, r"^# 11\. ")
header_lines = spec_text.split("\n# 1.")[0]
n_s43 = norm(s43)
n_s42 = norm(s42)
n_sec11 = norm(sec11)
n_spec = norm(spec_text)

# ---------------------------------------------------------------- F-01 pins
check("P01 §4.3.3 fusion paragraph cites 77 as the real identity battery",
      "appendix/77-rev15-shape-identity.py" in n_s43 and
      "builds both shapes" in n_s43,
      "77 identity cite missing in §4.3.3")
check("P02 §4.3.3 names the 66 Part-B self-comparison as superseded",
      "self-comparison" in n_s43 and "same call" in n_s43,
      "66 Part-B defect not scoped in §4.3.3")
check("P03 §4.3.3 keeps B3 scoping + M authority (P13/P14 regression)",
      "break count and end-state identity" in n_s43 and
      "t-u3/t-c7 are the m authority" in n_s43 and
      "at every field_start→quoted transition" in n_s43,
      "v14 F-02 pins regressed")
check("P04 register D-58 row re-aims identity to 77 with the discriminator",
      "appendix/77-rev15-shape-identity.py" in norm(reg) and
      "re-open-on-a-later-record-relative-line" in norm(reg) and
      "re-remembering build m=3" in norm(reg),
      "register D-58 row not re-aimed")
check("P05 §11 D-58 entry carries the re-aimed cite",
      "appendix/77-rev15-shape-identity.py" in n_sec11 and
      "13-corpus family" in n_sec11,
      "§11 D-58 entry stale")
check("P06 probes row carries 77 as its own entry with the 30-check count",
      "appendix/77-rev15-shape-identity.py (cycle-15 live identity evidence, 30 checks" in n_spec,
      "77 probes-row entry missing")
check("P07 battery 77 runs 30/0 against its own corpus set (live)",
      os.system("cd %s && python3 appendix/77-rev15-shape-identity.py > /dev/null 2>&1" % HERE) == 0,
      "battery 77 not green")

# ---------------------------------------------------------------- F-02 pins
check("P08 no probe annotation labels 67 'HISTORICAL itself since the v14 "
      "rollover' while citing it as the live re-proof",
      norm("re-proven live by 67-rev14-gate-reaim.py G1-G6 on the live §4.5 "
           "shape (HISTORICAL itself since the v14 rollover") not in n_spec and
      norm("re-proven live by 67-rev14-gate-reaim.py G1-G6 (HISTORICAL itself "
           "since the v14 rollover") not in n_spec,
      "false HISTORICAL parenthetical surviving")
check("P09 32/36 re-proof cites name 84 (rev16); the v15-rollover wording "
      "survives as history (F-01 annotation + carried v15 text)",
      n_spec.count("re-proven live by 84-rev16-gate-reaim.py") >= 2 and
      "historical since the v15 rollover" in n_spec,
      "count=%d" % n_spec.count("re-proven live by 84-rev16-gate-reaim.py"))

# ---------------------------------------------------------------- F-03 pins
check("P10 51 annotation's re-proof cites name 84 + 77 (not 58/59, not the dead 78)",
      "re-proven live on the current shape by appendix/84-rev16-gate-reaim.py" in n_spec and
      "appendix/77-rev15-shape-identity.py (30 checks; b3's subject lives in its identity battery)" in n_spec,
      "51 annotation re-proof stale")
check("P11 48b annotation's re-proof cite names 84 G6 (not 59 G6, not the dead 78)",
      norm("its behavioral checks (P1×6, P2a, P2b) passed when last runnable and their subject is re-proven live on the current shape by appendix/84-rev16-gate-reaim.py G6") in n_spec,
      "48b annotation re-proof stale")
check("P12 no live re-proof slot still names 58 or 59",
      "re-proven live on the current shape by appendix/58-rev13-sr11-folds-probes.py" not in n_spec and
      norm("re-proven live by appendix/59-rev13-gate-reaim.py G6") not in n_spec,
      "dead 58/59 re-proof cite surviving")

# ---------------------------------------------------------------- F-04 pins
check("P13 §4.3.2 carries the D-59 binding note",
      "binding note (d-59 mirror" in n_s42 and
      "names its cpython name binding per d-59" in n_s42,
      "§4.3.2 D-59 note missing")
check("P14 register D-59 row names the v15 note addition",
      "v15 additions" in norm(reg) and "adv-c14 f-04" in norm(reg) and
      "adv-c14 f-05" in norm(reg),
      "register D-59 row missing the v15 additions")

# ---------------------------------------------------------------- F-05 pins
check("P15 T-C9 baselines carry module-bound labels",
      "reader-only baseline 0.8 s (module-bound)" in n_spec and
      "dict-build+serialize 0.4 s (module-bound" in n_spec,
      "T-C9 baseline labels missing")
check("P16 QC-5 baselines carry module-bound labels",
      "reader-only 0.8 s (module-bound)" in n_spec and
      "dict+serialize\n  0.4 s (module-bound" in spec_text,
      "QC-5 baseline labels missing")
check("P17 §9 NFR-003 row mirrors the baseline label",
      "module-bound baselines, labeled per d-59" in n_spec,
      "§9 NFR-003 baseline label missing")

# ------------------------------------------------- enumerations / register
check("P18 register D-58 row site list still cites the spec/15 shapes (append-only register, not path-rewritten)",
      "spec/15-spec-v15.md §4.3.2/§4.3.3 counting-rule paragraph" in reg,
      "register D-58 site list drifted")
check("P19 register D-59 row site list still cites the spec/15 shapes (append-only register)",
      "spec/15-spec-v15.md §8.3 T-C9, QC-5 Verification" in reg,
      "register D-59 site list drifted")
mreg = re.search(r"^\| D-59 \|", reg, flags=re.M)
check("P20 register carries the D-59 row (DECIDED, spec-designer)",
      mreg is not None and
      re.search(r"^\| D-59 \|.*\| DECIDED \| spec-designer \|", reg,
                flags=re.M) is not None,
      "D-59 row missing/malformed")
check("P21 §11 coverage sentence stays at D-59 (no new decision this cycle)",
      (lambda m: m is not None and m.group(1) == "59")(
          re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED",
                    sec11)),
      "§11 enumeration moved")
ids = set(re.findall(r"D-(\d+)", sec11))
check("P22 no D id above 59 named in §11",
      all(int(b) <= 59 for b in ids if b.isdigit()),
      str(sorted(b for b in ids if b.isdigit() and int(b) > 59)))
check("P23 header decision-register row stays at D-59",
      "appendix/03-decision-register.md (D-01..D-59, all DECIDED)" in header_lines,
      "header register row stale")
check("P24 §1 overview enumeration at D-59",
      re.search(r"D-01\.\.D-59 in\s*\nappendix/03-decision-register\.md are all DECIDED",
                spec_text) is not None,
      "§1 enumeration stale")
check("P25 header version row is v16 and the revision row leads with the v16 text",
      "| version | v16 |" in header_lines and
      "| revision | v16 — cycle-16: mechanical-validation fix only" in spec_text,
      "header version/revision rows stale")
check("P26 v15 revision row names the board-verified gate verdicts",
      "t_e2856728" in spec_text and "t_d7903f01" in spec_text and
      "appendix/76b-board-query-c15.py" in spec_text,
      "verdict cites missing")
check("P27 §11 v15 history note names the cycle-15 probes",
      "78-rev15-gate-reaim.py" in n_sec11 and "81-rev15-fold-pins.py" in n_sec11,
      "§11 v15 note missing probes")
check("P28 §11 v16 history note names the cycle-16 probes and the F-01 closure",
      "84-rev16-gate-reaim.py" in n_sec11 and "85-rev16-fold-pins.py" in n_sec11
      and "mechval-c15 f-01" in n_sec11,
      "§11 v16 note missing probes/F-01 closure")

# ------------------------------------------------- cycle-16 pins (F-01 closure)
check("P29 the F-01 stale cite carries the HISTORICAL annotation + live successor",
      norm("re-aimed at spec/14-spec-v14.md (HISTORICAL since the v15 rollover") in n_spec
      and "appendix/84-rev16-gate-reaim.py" in spec_text
      and "mechval-c15 f-01" in n_spec,
      "F-01 annotation missing")
check("P30 probes-row live re-proof cites name 84 (not the dead 78) at 32/36/48b/51",
      n_spec.count("re-proven live by 84-rev16-gate-reaim.py") >= 2 and
      n_spec.count("re-proven live on the current shape by appendix/84-rev16-gate-reaim.py") >= 2 and
      "re-proven live by 78-rev15-gate-reaim.py" not in n_spec and
      "re-proven live on the current shape by appendix/78-rev15-gate-reaim.py" not in n_spec,
      "live re-proof cites not re-aimed to 84")
check("P31 the rev15 gate set is labeled HISTORICAL since the v16 rollover in the probes row",
      "78-rev15-gate-reaim.py (HISTORICAL since the v16 rollover" in spec_text and
      "83-rev15-final-gate.py (HISTORICAL since the v16 rollover" in spec_text,
      "rev15 set not annotated historical")

print()
print("TOTAL: %d checks, %d FAILURES" % (len(_results), _results.count(False)))
sys.exit(1 if _results.count(False) else 0)

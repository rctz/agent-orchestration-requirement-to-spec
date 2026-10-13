#!/usr/bin/env python3
"""70-rev14-fold-pins — text pins for the cycle-14 folds on spec/14.

Covers (each tied to its finding):
  F-01 / D-59: T-C9 + QC-5 + §9 NFR-003 row + header + register carry the
    binding-controlled numbers with the binding named; the cross-binding
    comparison is declared void; 48c/55h are scoped as historical
    single-regime artifacts; no margin narrative survives in a normative
    site; no stale unqualified 27.3/9.1 pair remains normative.
  F-02: §4.3.3 + D-58 row scope B3 to break-count/end-state identity,
    name 66 Part B as the identity cite and T-U3/T-C7 as the M authority.
  SR12-F-01/F-02: 51/48b HISTORICAL annotations present with live re-proof
    cites; 52-cites re-aimed to 67; 58/59/67 battery named in the probes row.
  Enumerations: D-01..D-59 at header/§1/§11/register; no id above 59.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "14-spec-v14.md")
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
s83 = between(spec_text, r"^## 8\.3 ", r"^## 8\.4 ")
qc5 = between(spec_text, r"^### QC-5 ", r"^### QC-6 ")
s9 = between(spec_text, r"^# 9\. ", r"^# 10\. ")
s43 = between(spec_text, r"^## 4\.3 ", r"^## 4\.4 ")
sec11 = section(spec_text, r"^# 11\. ")
header_lines = spec_text.split("\n# 1.")[0]
n_s83 = norm(s83)
n_qc5 = norm(qc5)
n_s9 = norm(s9)
n_s43 = norm(s43)
n_sec11 = norm(sec11)
n_spec = norm(spec_text)

# ---------------------------------------------------------------- F-01 pins
check("P01 T-C9 cites the D-59 binding-controlled set with its artifact",
      "binding-controlled stage costs (d-59" in n_s83 and
      "appendix/66-rev14-binding-timing.py" in n_s83,
      "T-C9 D-59 sentence missing")
check("P02 T-C9 numbers all carry their binding",
      "25.7 s at module-level binding" in n_s83 and
      "14.9 s at function-local binding" in n_s83 and
      "19.9 s module-bound" in n_s83 and "9.1 s function-bound" in n_s83,
      "binding labels missing")
check("P03 T-C9 declares cross-binding comparison void",
      "cross-binding comparison is void" in n_s83,
      "void clause missing")
check("P04 T-C9 scopes 48c/55h as historical single-regime",
      "appendix/48c module-bound two-quantity" in n_s83 and
      "appendix/55h function-bound fused 9.1 s" in n_s83,
      "historical single-regime scoping missing")
check("P05 T-C9 retracts the margin narratives",
      "retracted" in n_s83 and "~20 s left" in n_s83 and "~3-5 s" in n_s83,
      "retraction sentence missing")
check("P06 T-C9 keeps the diagnostic envelope framing (51 T2 pin class)",
      "diagnostic spot check asserting the envelope outcome" in n_s83 and
      "< 30 s" in n_s83 and "not a gate" in n_s83,
      "framing changed")
check("P07 T-C9 keeps the hardware-class sentence (51 T2 pin)",
      norm("REFERENCE HARDWARE CLASS for the envelope — a single-core "
           "general-purpose x86-64 or ARM64 SBC-class machine") in n_s83,
      "hardware-class needle broken")
check("P08 QC-5 Verification carries the same binding-controlled numbers",
      "binding-controlled stage" in n_qc5 and
      "25.7 s module-bound / 14.9 s function-bound" in n_qc5 and
      "19.9 s module-bound / 9.1 s" in n_qc5 and
      "cross-binding comparison is void" in n_qc5,
      "QC-5 not mirrored")
check("P09 §9 NFR-003 row cites 66 with the D-59 scoping",
      "appendix/66-rev14-binding-timing.py" in n_s9 and
      "binding-controlled per d-59" in n_s9 and
      "cross-binding comparison is void" in n_s9,
      "NFR-003 evidence cell stale")
check("P10 NO normative site still pairs 27.3 with 9.1 as one comparison",
      all("27.3" not in body for body in (n_s83, n_qc5, n_s9)),
      "stale 27.3 in a normative site")
check("P11 NO normative site keeps the ~3-5 s margin story as fact",
      all("leaves only ~3-5 s" not in body or "retracted" in body
          for body in (n_s83, n_qc5)),
      "margin story surviving unqualified")

# ---------------------------------------------------------------- F-02 pins
check("P12 §4.3.3 fusion paragraph re-aims identity to 66 Part B",
      "appendix/66-rev14-binding-timing.py part b" in n_s43,
      "66 Part B cite missing")
check("P13 §4.3.3 fusion paragraph scopes B3 and names the M authority",
      "break count and end-state identity" in n_s43 and
      "t-u3/t-c7 are the m authority" in n_s43,
      "B3 scoping missing")
check("P14 §4.3.3 pins the every-transition latch",
      "at every field_start→quoted transition" in n_s43,
      "table-latch wording missing")
check("P15 §11 D-58 entry carries the re-based identity cite",
      "appendix/66-rev14-binding-timing.py part b" in n_sec11 and
      "first-quote latch computes m=2 where the" in n_sec11,
      "D-58 §11 entry stale")
check("P16 register D-58 row re-based (66 Part B, B3 scoped, M authority)",
      "appendix/66-rev14-binding-timing.py Part B" in reg and
      "T-U3/T-C7 are the M authority" in reg and
      "spec/14-spec-v14.md" in reg,
      "register D-58 row not re-based")

# ------------------------------------------------- SR12-F-01/F-02 pins
check("P17 probes row annotates 51 HISTORICAL since v13 with live re-proofs",
      "appendix/51-rev12-adv11-folds-probes.py (historical since the v13 rollover" in n_spec and
      "appendix/58-rev13-sr11-folds-probes.py (25/25)" in n_spec and
      "appendix/59-rev13-gate-reaim.py (12/12" in n_spec,
      "51 annotation missing/wrong")
check("P18 probes row annotates 48b HISTORICAL since v13 (SR12-F-02)",
      "appendix/48b-adv-c11-probes.py (adversarial-early cycle-11 evidence, reviewer file, cited as evidence only; historical since the v13 rollover" in n_spec,
      "48b annotation missing")
check("P19 no probes-row live re-proof cite still names 52 G1-G6",
      norm("re-proven live by 52-rev12-gate-reaim.py G1-G6 on the live") not in n_spec and
      norm("re-proven live by 52-rev12-gate-reaim.py G1-G6, while") not in n_spec,
      "dead 52 cite surviving in a live re-proof slot")
check("P20 67-rev14-gate-reaim.py named as the live re-proof",
      n_spec.count("67-rev14-gate-reaim.py") >= 3,
      "count=%d" % n_spec.count("67-rev14-gate-reaim.py"))
check("P21 v14 revision row names the living battery",
      "living battery on spec/14 is 66/67/68/69/70" in n_spec,
      "battery enumeration missing")

# ------------------------------------------------- enumerations
mreg = re.search(r"^\| D-59 \|", reg, flags=re.M)
check("P22 register carries the D-59 row (DECIDED, spec-designer)",
      mreg is not None and
      re.search(r"^\| D-59 \|.*\| DECIDED \| spec-designer \|", reg,
                flags=re.M) is not None,
      "D-59 row missing/malformed")
check("P23 §11 coverage sentence at D-59",
      (lambda m: m is not None and m.group(1) == "59")(
          re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED",
                    sec11)),
      "§11 enumeration stale")
ids = set(re.findall(r"D-(\d+)", sec11))
check("P24 no D id above 59 named in §11",
      all(int(b) <= 59 for b in ids if b.isdigit()),
      str(sorted(b for b in ids if b.isdigit() and int(b) > 59)))
check("P25 §11 carries the D-59 full-form entry",
      "D-59\n(§8.3 T-C9/QC-5" in spec_text or
      norm("D-59 (§8.3 T-C9/QC-5/§9/§11 NFR-003 row") in n_sec11,
      "D-59 entry missing")
check("P26 header decision-register row at D-59",
      "appendix/03-decision-register.md (D-01..D-59, all DECIDED)" in header_lines,
      "header register row stale")
check("P27 §1 overview enumeration at D-59",
      norm("D-01..D-59 in\nappendix/03-decision-register.md are all DECIDED") in
      norm(spec_text).replace("  ", " ") or
      re.search(r"D-01\.\.D-59 in\s*\nappendix/03-decision-register\.md are all DECIDED",
                spec_text) is not None,
      "§1 enumeration stale")

print(f"TOTAL: {len(_results)} checks, {_results.count(False)} FAILURES")
sys.exit(1 if _results.count(False) else 0)

#!/usr/bin/env python3
"""Rev13 probes (cycle 13, card t_6d826436) — SR11 fold checks on
spec/13-spec-v13.md.

Closes the four spec-review cycle-11 findings:
  F-01 (P1): T-C9/QC-5/D-58-register now carry the REAL measured numbers
             (fused 9.1 s, appendix/55h) and the false "~0.8-1 s" claim is
             gone from every normative site (section-scoped absence — the
             header/§11 legitimately QUOTE the deleted phrase as history).
  F-02 (P2): header probes row annotates 32/36/41/47 HISTORICAL with their
             archived spec paths and live re-proof cites.
  F-03 (P3): "43 checks" -> "42 checks" at both header sites.
  F-04 (P3): §11 coverage paragraph carries the D-51 full-form entry.
Plus regression guards: the 51 T2 text pins (hardware class, fusion rule,
QC-5 mechanism) still match, enumerations still agree at D-01..D-58, and
register D-57/D-58 stay DECIDED.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "13-spec-v13.md")
REG = os.path.join(HERE, "appendix", "03-decision-register.md")

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else "  [" + detail + "]"))


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def section(text, pat):
    m = re.search(pat, text, flags=re.M)
    if not m:
        return ""
    nxt = re.search(r"^# ", text[m.end():], flags=re.M)
    end = m.end() + (nxt.start() if nxt else len(text) - m.end())
    return text[m.start():end]


def subsection(text, pat, stop_pat):
    m = re.search(pat, text, flags=re.M)
    if not m:
        return ""
    n = re.search(stop_pat, text[m.end():], flags=re.M)
    return text[m.start():m.end() + (n.start() if n else len(text) - m.end())]


spec_text = open(SPEC, encoding="utf-8").read()
reg = open(REG, encoding="utf-8").read()
s83 = section(spec_text, r"^## 8\.3 ")
qc5 = subsection(spec_text, r"^### QC-5 ", r"^### QC-6 ")
s43 = section(spec_text, r"^## 4\.3 ")
sec11 = section(spec_text, r"^# 11\. ")
header_lines = spec_text.split("\n# 1.")[0]

# ---------------------------------------------------------------------------
# F-01 — corrected measured numbers cite artifacts that contain them
# ---------------------------------------------------------------------------
m = re.search(r"^\| T-C9 \|(.*?)\| NFR-003 \|$", s83, flags=re.M)
check("P1 T-C9 row extractable from §8.3", m is not None, "T-C9 row missing")
tc9 = m.group(1) if m else ""
check("P2 T-C9 names the two-quantity measurement 27.3 s with its artifact",
      "27.3 s" in tc9 and "appendix/48c-adv-c11-50mb.py" in tc9,
      "two-quantity number/cite missing")
check("P3 T-C9 names the fused measurement 9.1 s with appendix/55h",
      "9.1 s" in tc9 and "appendix/55h-sr11-fused-timing.py" in tc9,
      "fused number/cite missing")
check("P4 T-C9 states the non-reader-like qualification",
      "NOT reader-like" in tc9 and "~9-15 s" in tc9,
      "qualification sentence missing")
check("P5 T-C9 normative site carries NO ~0.8-1 s claim (section-scoped)",
      norm("~0.8-1 s") not in norm(s83) and "~0.8-1" not in tc9,
      "the deleted false claim survives in §8.3")
check("P6 T-C9 keeps the diagnostic-not-gate framing",
      "diagnostic, not a gate" in tc9 and "< 30 s" in tc9,
      "framing changed")
check("P7 QC-5 Verification carries the same corrected numbers",
      "9.1 s" in qc5 and "appendix/55h-sr11-fused-timing.py" in qc5 and
      "27.3 s" in qc5 and norm("~0.8-1 s") not in norm(qc5),
      "QC-5 verification not mirrored")

# ---------------------------------------------------------------------------
# F-01 regression — 51's T2 pins must still match after the rewrite
# ---------------------------------------------------------------------------
check("P8 §8.3 hardware-class sentence intact (51 T2 pin)",
      norm("The 30 s figure is stated on the documented REFERENCE HARDWARE "
           "CLASS for the envelope — a single-core general-purpose x86-64 or "
           "ARM64 SBC-class machine") in norm(s83),
      "hardware-class needle broken")
check("P9 QC-5 Mechanism fused-scan wording intact (51 T2 pin)",
      norm("one decode; per record one tell/slice + ONE O(record) scan that "
           "may fuse the FSM state walk and the break count in a single "
           "pass (D-58") in norm(qc5),
      "QC-5 mechanism needle broken")
check("P10 §4.3 fusion rule intact (51 T2 pin)",
      norm("CONFORMING FUSION (D-58, closes adv-c11 F-02): the FSM and the "
           "break count may be computed in ONE fused pass") in norm(s43),
      "fusion-rule needle broken")

# ---------------------------------------------------------------------------
# F-02 — HISTORICAL annotations in the header probes row
# ---------------------------------------------------------------------------
check("P11 header annotates appendix/32 HISTORICAL with archived spec/08",
      "appendix/32-rev8-fdclose-probes.py (HISTORICAL" in spec_text and
      "spec/08-spec-v8.md" in spec_text and
      norm("re-proven live by 52-rev12-gate-reaim.py G1-G6") in norm(header_lines),
      "32 annotation missing/incomplete")
check("P12 header annotates appendix/36 HISTORICAL with archived spec/09",
      "appendix/36-rev9-ki-argparse-probes.py (HISTORICAL" in spec_text and
      "spec/09-spec-v9.md" in spec_text,
      "36 annotation missing")
check("P13 header annotates appendix/41 HISTORICAL with archived spec/10",
      "appendix/41-rev10-adv9-folds-probes.py (HISTORICAL" in spec_text and
      "spec/10-spec-v10.md" in spec_text,
      "41 annotation missing")
check("P14 header annotates appendix/47 HISTORICAL with archived spec/11",
      "appendix/47-rev11-adv10-folds-probes.py (HISTORICAL" in spec_text and
      "spec/11-spec-v11.md" in spec_text,
      "47 annotation missing")
check("P15 the four HISTORICAL annotations carry the SR11-F-02 marker",
      spec_text.count("(SR11-F-02)") >= 4,
      "marker count %d" % spec_text.count("(SR11-F-02)"))

# ---------------------------------------------------------------------------
# F-03 — 42 checks at both header sites
# ---------------------------------------------------------------------------
check("P16 '43 checks:' citation form gone; both header citation sites say 42",
      "43 checks:" not in spec_text and
      "(cycle-12 revision evidence, 42 checks:" in spec_text and
      "appendix/51-rev12-adv11-folds-probes.py (42 checks: behavioral" in
      spec_text,
      "citation sites wrong (43-form=%d)" % spec_text.count("43 checks:"))

# ---------------------------------------------------------------------------
# F-04 — D-51 full-form entry in the §11 coverage paragraph
# ---------------------------------------------------------------------------
i50 = sec11.find("D-50 (§4.5")
i51 = sec11.find("D-51 (§4.5/§6.4/§7.1/§7.3/§8.3/QC-2")
i52 = sec11.find("D-52 (§4.1")
check("P17 §11 carries the D-51 full-form entry between D-50 and D-52",
      0 <= i50 < i51 < i52,
      "positions: D-50=%d D-51=%d D-52=%d" % (i50, i51, i52))
check("P18 the D-51 entry names its real binding sites and closure",
      norm("the KeyboardInterrupt/SIGINT window is INSIDE the D-48/D-50 "
           "compensation contract") in norm(sec11) and
      "closes adv-c8 F-01" in sec11[i51:i52],
      "D-51 entry content wrong")

# ---------------------------------------------------------------------------
# Regression guards — enumerations, register, verdict hygiene
# ---------------------------------------------------------------------------
check("P19 register still D-58 DECIDED / spec-designer with 55h evidence",
      re.search(r"^\| D-58 \|.*appendix/55h-sr11-fused-timing\.py.*\| DECIDED \| spec-designer \|",
                reg, flags=re.M) is not None,
      "D-58 register row changed shape or lost 55h")
check("P20 register D-58 row carries the v13 correction note",
      "SR11-F-01" in reg and "9.1 s" in reg,
      "register lacks the corrected numbers")
check("P21 enumerations agree at D-01..D-58 (§1, header, §11 sentence)",
      "D-01..D-58 in appendix/03-decision-register.md are all DECIDED" in
      norm(spec_text).replace("  ", " ") or
      re.search(r"D-01\.\.D-58 in\s*\nappendix/03-decision-register\.md are all DECIDED",
                spec_text) is not None,
      "§1 enumeration not at D-58")
m3 = re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED", sec11)
check("P22 §11 coverage sentence at D-58", m3 is not None and m3.group(1) == "58",
      m3.group(1) if m3 else "absent")
bound = set(re.findall(r"D-(\d+)", sec11))
check("P23 no D id above 58 named in §11",
      all(int(b) <= 58 for b in bound if b.isdigit()),
      str(sorted(b for b in bound if b.isdigit() and int(b) > 58)))
check("P24 no adversarial-early#12 verdict claimed (no-result card)",
      "adv-early#12" in spec_text and "NO result string" in spec_text and
      norm("adversarial-early verdict PASS\" names") in norm(spec_text) and
      "adv-early#12 verdict PASS" not in spec_text and
      norm("the adversarial-early verdict is PASS") not in norm(spec_text),
      "phantom adv verdict pattern present")
check("P25 spec-review#11 cited as the FAIL record it is",
      "spec-review#11" in spec_text and "t_d2017123" in spec_text and
      "appendix/55-review-spec-c11.md" in spec_text,
      "c11 findings record not cited")

print()
total = len(_results)
fails = _results.count(False)
print("TOTAL: %d checks, %d FAILURES" % (total, fails))
sys.exit(1 if fails else 0)

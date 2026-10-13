#!/usr/bin/env python3
"""Cycle-11 spec-review mechanical probes (SR11).

Three-axis review of spec/12-spec-v12.md against APPROVED
requirements/07-requirements-v7.md. This file holds the MECHANICAL
evidence only (cross-references, mirrored-site consistency, enumeration
agreement); the analytical findings live in appendix/55-review-spec-c11.md.

Run: python3 appendix/55b-review-spec-c11-probes.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "12-spec-v12.md"
REQS = ROOT / "requirements" / "07-requirements-v7.md"
REG = ROOT / "appendix" / "03-decision-register.md"

fails = []
passes = []


def check(name, cond, detail=""):
    (passes if cond else fails).append(f"{name}" + (f" — {detail}" if detail else ""))


spec = SPEC.read_text(encoding="utf-8")
reqs = REQS.read_text(encoding="utf-8")
reg = REG.read_text(encoding="utf-8")

# ---------------------------------------------------------------- P1: every appendix cite in the spec exists on disk
cites = set(re.findall(r"appendix/([0-9][0-9a-zA-Z_-]*\.(?:py|md))\b", spec))
missing = [c for c in sorted(cites) if not (ROOT / "appendix" / c).exists()]
check("P1 every appendix cite exists on disk", not missing, f"missing: {missing}")

# ---------------------------------------------------------------- P2: every § cross-ref inside the spec resolves
secs = set(re.findall(r"^#{1,3} (#?\d[\d.]*[a-z]?)\.?", spec, flags=re.M))
sec_ids = {s.lstrip('#') for s in secs}
internal = set(re.findall(r"§(\d+(?:\.\d+)?)", spec))
top = {i.split(".")[0] for i in internal}
known_top = {"1","2","3","4","5","6","7","8","9","10","11","12"}
bad_top = [t for t in top if t not in known_top]
check("P2 no § reference to a nonexistent top-level section", not bad_top, f"bad: {sorted(bad_top)}")

# ---------------------------------------------------------------- P3: traceability matrix rows == REQ/NFR set in the requirements doc
req_ids = sorted(set(re.findall(r"\*\*(REQ-\d{3}|NFR-\d{3}) —", reqs)))
tr = re.search(r"^# 11\. Traceability matrix(.*)^# 12\.", spec, flags=re.S | re.M)
tr_text = tr.group(1) if tr else ""
matrix_ids = sorted(set(re.findall(r"\| (REQ-\d{3}|NFR-\d{3}) \|", tr_text)))
check("P3 traceability matrix covers every REQ/NFR exactly", req_ids == matrix_ids,
      f"reqs={req_ids} matrix={matrix_ids}")

# ---------------------------------------------------------------- P4: mutation contract has 13 rows, one per question
mc = re.search(r"Mutation contract \(the 13 questions\)(.*?)^## 4\.6", spec, flags=re.S)
rows = re.findall(r"^\| (\d+) \|", mc.group(1), flags=re.M) if mc else []
check("P4 mutation contract rows == 1..13", rows == [str(i) for i in range(1, 14)], f"rows={rows}")

# ---------------------------------------------------------------- P5: QC tuples — six present, five elements each
qc_tuples = re.findall(r"### (QC-\d)", spec)
check("P5 QC tuple count == 6", len(qc_tuples) == 6, f"found {qc_tuples}")
for q in ["QC-1","QC-2","QC-3","QC-4","QC-5","QC-6"]:
    m = re.search(rf"### {q} .*?^- (Scope|Mechanism|Assumptions|Failure|Verification):", spec, flags=re.S | re.M)
    blk = re.search(rf"### {q} (.*?)(?=### QC-|# 11\.)", spec, flags=re.S)
    elems = [e for e in ["Scope:","Mechanism:","Assumptions:","Failure:","Verification:"] if e in (blk.group(1) if blk else "")]
    check(f"P5 {q} complete EV tuple (5/5)", len(elems) == 5, f"has {elems}")

# ---------------------------------------------------------------- P6: catalog ids in §6.3 == §7.1 row ids
cat = re.search(r"^## 6\.3 (.*?)^## 6\.4", spec, flags=re.S | re.M).group(1)
cat_ids = re.findall(r"^\| (E-[A-Z0-9]+) \|", cat, flags=re.M)
p71 = re.search(r"^## 7\.1 (.*?)^## 7\.2", spec, flags=re.S | re.M).group(1)
p71_ids = re.findall(r"^\| (E-[A-Z0-9]+) \|", p71, flags=re.M)
check("P6 §6.3 catalog ids == §7.1 contract ids (same set, same order)", cat_ids == p71_ids,
      f"catalog={cat_ids} p71={p71_ids}")

# ---------------------------------------------------------------- P7: register D ids == spec coverage D ids
reg_ids = set(re.findall(r"^\| (D-\d+b?) \|", reg, flags=re.M))
cov = re.search(r"Decision-coverage check:(.*?)\(v12:", spec, flags=re.S).group(1)
cov_ids = set(re.findall(r"(D-\d+b?) \(", cov))
check("P7 §11 coverage ids == register ids", reg_ids == cov_ids,
      f"only-register={sorted(reg_ids-cov_ids)} only-coverage={sorted(cov_ids-reg_ids)}")

# ---------------------------------------------------------------- P8: enumeration agreement §1 / §11 / header / register max
declared_max = max(int(re.sub(r"\D","",d)) for d in reg_ids if "b" not in d)
e1 = re.search(r"D-01\.\.D-(\d+) in", spec)
e11 = re.search(r"are all DECIDED in\s+appendix/03-decision-register\.md and all are bound.*?D-01 \(§4\.1\)", spec, flags=re.S)
check("P8 §1 enumeration at register max", e1 and int(e1.group(1)) == declared_max,
      f"§1 says D-01..D-{e1.group(1) if e1 else '?'} vs register max {declared_max}")
cov_sent = re.search(r"D-01\.\.D-(\d+) are all DECIDED", spec)
check("P8 §11 enumeration at register max", cov_sent and int(cov_sent.group(1)) == declared_max,
      f"§11 says D-01..D-{cov_sent.group(1) if cov_sent else '?'}")
hdr = re.search(r"decision register \| appendix/03-decision-register\.md \(D-01\.\.D-(\d+), all DECIDED\)", spec)
check("P8 header row at register max", hdr and int(hdr.group(1)) == declared_max,
      f"header says D-01..D-{hdr.group(1) if hdr else '?'}")

# ---------------------------------------------------------------- P9: mangle sweep — isolated pipe lines / doubled pipes
bad_lines = []
for i, ln in enumerate(spec.splitlines(), 1):
    s = ln.strip()
    if s.startswith("|") and s.endswith("|"):
        body = s[1:-1]
        if "||" in body:
            bad_lines.append((i, "doubled pipe", s[:60]))
check("P9 no doubled-pipe table mangling", not bad_lines, f"{bad_lines[:5]}")
isolated = []
lines_s = spec.splitlines()
for i, ln in enumerate(lines_s):
    s = ln.strip()
    if re.fullmatch(r"\|.{0,3}", s) or (s.startswith("|") and i + 1 < len(lines_s)
                                        and not lines_s[i + 1].strip().startswith("|")
                                        and not lines_s[i - 1].strip().startswith("|")
                                        and not re.match(r"^\|[^|]+\|$", s)):
        isolated.append((i + 1, s[:60]))
check("P9 no isolated pipe-line mangling", not isolated, f"{isolated[:5]}")

# ---------------------------------------------------------------- P10: D-57 mirror-site consistency — the at-open MemoryError fold
# Every site that names the at-open trigger must name BOTH triggers (KI or MemoryError) or point to D-57.
sites = {
    "§4.5 KI-AT-OPEN paragraph": spec[spec.find("At-open MemoryError joins this class"):spec.find("Earlier revisions worded the trigger")],
    "§10.1 R-6": spec[spec.find("R-6: a KeyboardInterrupt — or a MemoryError"):spec.find("Likelihood: low", spec.find("R-6: a KeyboardInterrupt"))],
    "QC-2 Scope": spec[spec.find("SIGNAL-WINDOW EXCEPTIONS"):spec.find("- Mechanism: phase split")],
    "§12 glossary successful-open": spec[spec.find("successful open (compensation trigger basis)")],
}
for name, body in sites.items():
    has_mem = "MemoryError" in body and ("D-57" in body or "D-54/D-57" in body)
    check(f"P10 {name} carries the D-57 MemoryError trigger", has_mem, body[:100])

# every R-6 mention site also carries the widened trigger, or cites D-57, or is a cross-ref list
r6_sites = [m.start() for m in re.finditer(r"R-6", spec)]
unqualified = []
for pos in r6_sites:
    ctx = spec[max(0, pos - 400):pos + 400]
    if "MemoryError" not in ctx and "D-57" not in ctx and "R-6/D-57" not in ctx:
        unqualified.append(spec[max(0, pos - 60):pos + 20].replace("\n", " "))
check("P10 every R-6 mention carries the widened trigger or a D-57 cite", not unqualified,
      f"{len(unqualified)} unqualified of {len(r6_sites)}: {unqualified[:3]}")

# ---------------------------------------------------------------- P11: T-C16 carve-out sentence present and correctly scoped
t16 = [l for l in spec.splitlines() if l.startswith("| T-C16 ")][0]
check("P11 T-C16 carries the at-open carve-out",
      "an at-open failure (OSError or MemoryError, D-46/D-57) never ran the compensation" in t16)
check("P11 T-C16 still pins the D-53/R-5 arm-abort scope", "D-53/R-5" in t16 and "D-56(a)" in t16)

# ---------------------------------------------------------------- P12: §5.1 diagram edge inventory
d51 = spec[spec.find("## 5.1"):spec.find("## 5.2")]
check("P12 §5.1 has at-open MemoryError edge",
      "MemoryError(at-open: fd never bound — NO compensation, D-57" in d51)
check("P12 §5.1 pre-open edge reworded to output-path-untouched",
      "MemoryError(pre-open encode: nothing open — output path untouched)" in d51)
check("P12 §5.1 footnote scopes byte-untouched to OSError forms",
      "shares the no-compensation" in d51 and "NOT the byte-untouched clause" in d51)

# ---------------------------------------------------------------- P13: T-C8 skip-as-root notes (adv-c11 F-03)
t8 = [l for l in spec.splitlines() if l.startswith("| T-C8 ")][0]
check("P13 T-C8 non-writable-dir sub-case skips as root",
      "non-writable dir (mode 0555)" in t8 and "SKIP AS ROOT — DAC_OVERRIDE defeats mode 0555" in t8)
check("P13 T-C8 read-only-target sub-case still skips as root",
      "SKIP AS ROOT — DAC_OVERRIDE defeats mode 444" in t8)

# ---------------------------------------------------------------- P14: D-58 fusion — no site may still mandate two passes as the only form
s43 = spec[spec.find("## 4.3"):spec.find("## 4.4")]
check("P14 §4.3 carries the CONFORMING FUSION latitude", "CONFORMING FUSION (D-58" in s43)
check("P14 neither form mandated", "neither form is" in s43 and "required" in s43)
qc5 = spec[spec.find("### QC-5"):spec.find("### QC-6")]
check("P14 QC-5 Mechanism names the fused option", "may" in qc5 and "fuse" in qc5)
tc9 = [l for l in spec.splitlines() if l.startswith("| T-C9 ")][0]
check("P14 T-C9 names the reference hardware class", "REFERENCE HARDWARE CLASS" in tc9 and "SBC" in tc9)

# ---------------------------------------------------------------- P15: forbidden claim-keyword substrings outside §10 (board list + phrase forms)
sec10 = spec[spec.find("# 10. Quality-claim evidence tuples"):spec.find("# 11. Traceability")]
outside = spec[:spec.find("# 10. Quality-claim evidence tuples")] + sec10[sec10.find("# 11. Traceability"):] if "# 11." in sec10 else spec.replace(sec10, "")
kw = ["idempoten","atomicity"," atomic","durab","concurrency-safe","thread-safe","race-free",
      "recoverable","backward-compat","performant","platform-independent","form-independent",
      "under concurrent"]
hits = []
for k in kw:
    for m in re.finditer(re.escape(k), outside, flags=re.I):
        pos = m.start()
        line_no = outside.count("\n", 0, pos) + 1
        hits.append((k, line_no, outside[max(0,pos-40):pos+40].replace("\n"," ")))
check("P15 claim-keyword board list clean outside §10", not hits, f"{hits[:6]}")

# ---------------------------------------------------------------- report
print(f"PASS {len(passes)} / FAIL {len(fails)}")
for p in passes:
    print("PASS -", p)
for f in fails:
    print("FAIL -", f)
sys.exit(1 if fails else 0)

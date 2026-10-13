#!/usr/bin/env python3
"""Spec-review cycle 10 (SR10) probes — independent evidence for the review of
spec/11-spec-v11.md against APPROVED requirements/07-requirements-v7.md
(card t_6f1d1e67; findings in appendix/48-review-spec-c10.md).

Checks (all runnable on any cycle after v11 by re-aiming SPEC):
  L1  appendix/47 runs clean on v11 (17 checks, 0 failures) — the v11
      revision-evidence battery (D-56(a) cascade P1a/P1b/P1c, D-55 devices
      P2a/P2b, enumerations P3a, fold-checks F1-F10, R-6 create flavor P4/F7).
  L2  appendix/30b runs clean (8/8) — the live-cited re-aim probe.
  L3  appendix/13/20/22 (designer base batteries) run clean.
  L4  STALENESS PROOF (SR10-F-01): each of appendix/32, 36, 39b, 41 raises
      FileNotFoundError on its archived spec path (08/09/09/10) — they are
      cited in the v11 header/body without the HISTORICAL annotation the
      SR6-F-03/SR7-F-03 convention requires. 45b shown too (revision-row
      dated cite — acceptable, noted in the finding).
  T1-T6   D-56(a) fold: the arm-abort qualifier ("second MemoryError" /
      "any non-OSError") present at §5.3 S-14(e), §6.3 E-MEM, §7.2,
      §8.3 T-C16, QC-2 Verification, §7.1 taxonomy.
  T7      D-56(b) fold: R-6 create flavor at the six mirrored sites.
  T8      D-55 stderr-side scope at §6.1 stderr row + §12 silent success.
  T9      §1 and §11 enumerations read D-01..D-56.
  C1      register D-01..D-56 present, all DECIDED (57 rows incl. D-11b).
  H1      (documents SR10-F-02) header says "16/16 PASS" for appendix/47
      while the file prints 17 checks — count-arithmetic nit, PASS records
      the discrepancy, does not fail.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "11-spec-v11.md")
REGISTER = os.path.join(HERE, "appendix", "03-decision-register.md")
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + detail if detail else ""))


def run_probe(fname):
    """Run appendix/<fname>; return (returncode, tail-of-output)."""
    p = os.path.join(HERE, "appendix", fname)
    r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=300)
    tail = (r.stdout + r.stderr).strip().split("\n")[-1] if (r.stdout or r.stderr) else ""
    return r.returncode, tail


spec = open(SPEC, encoding="utf-8").read()
reg = open(REGISTER, encoding="utf-8").read()

# --- L1/L2/L3: live batteries -------------------------------------------------
rc, tail = run_probe("47-rev11-adv10-folds-probes.py")
check("L1 appendix/47 on v11", rc == 0 and "0 failures" in tail, tail)
rc, tail = run_probe("30b-adv-c6-reaim-probes.py")
check("L2 appendix/30b live", rc == 0 and "FAIL: 0" in tail, tail)
for f in ("13-spec-design-probes.py", "20-rev3-order-probes.py",
          "22-rev4-writeorder-probes.py"):
    rc, tail = run_probe(f)
    check("L3 appendix/" + f, rc == 0 and "FAILURES: 0" in tail, tail)

# --- L4: staleness proof -------------------------------------------------------
STALE = {
    "32-rev8-fdclose-probes.py": "08-spec-v8.md",
    "36-rev9-ki-argparse-probes.py": "09-spec-v9.md",
    "39b-adv-c9-probes.py": "09-spec-v9.md",
    "41-rev10-adv9-folds-probes.py": "10-spec-v10.md",
    "45b-adv-c10-probes.py": "10-spec-v10.md",
}
for f, arch in STALE.items():
    rc, tail = run_probe(f)
    crashed = rc != 0 and arch in (tail or "")
    check("L4 stale %s (archived %s)" % (f, arch), crashed, tail[:110])

print()

# --- T1-T6: D-56(a) arm-abort qualifier at the five absolute sites ------------
def site(name, needle, desc):
    check(name, needle in spec, desc)

site("T1 S-14(e) arm-abort qualifier",
     "UNLESS the\ncompensation itself is aborted mid-flight per D-53/R-5 — a second KI\nor a second MemoryError",
     "§5.3 S-14(e) 'the file is GONE ... UNLESS' clause")
site("T2 §6.3 E-MEM row qualifier",
     "UNLESS the compensation itself is aborted per D-53/R-5: a second MemoryError (or second KI)",
     "E-MEM 'so no partial file survives — UNLESS' clause")
site("T3 §7.2 footprint qualifier",
     "UNLESS the compensation itself is aborted\n  mid-flight per D-53/R-5 (a second KI or a second MemoryError",
     "§7.2 footprint sentence")
site("T4 T-C16 qualifier",
     "unless the compensation itself is aborted mid-flight per D-53/R-5 (a SECOND KI, or a second MemoryError",
     "§8.3 T-C16 write-phase branch")
site("T5 QC-2 Verification qualifier",
     "D-53/R-5 arm-abort scope: a second KI or second MemoryError inside\n  the failure arm leaves the partial file",
     "QC-2 Verification T-C16 clause")
site("T6 §7.1 taxonomy qualifier",
     "a SECOND KI — or a second MemoryError, any non-OSError — inside the\nfailure arm leaves the partial file (R-5;",
     "§7.1 partial-failure taxonomy sentence")

# --- T7: D-56(b) R-6 create flavor at mirrored sites ---------------------------
for needle, desc in [
    ("ABSENT target may be left CREATED at 0 bytes by the kernel's\n  O_CREAT — the same window's two flavors", "§4.5 KI-AT-OPEN paragraph"),
    ("an ABSENT target may be left CREATED at 0 bytes by the kernel's\n  O_CREAT — both flavors of the same window are R-6", "QC-2 Scope"),
    ("or an ABSENT target CREATED at 0 bytes by the kernel's\n  O_CREAT (adv-c10 F-04; decision D-56(b))", "§10.1 R-6 body"),
    ("or at a path that did not exist before (create flavor,\n  D-56(b))", "§10.1 R-6 Impact"),
    ("an absent target CREATED empty (adv-c10 F-04)", "§11 D-54 index entry"),
]:
    check("T7 create-flavor @ " + desc, needle in spec, needle[:60])

# §7.2's create-flavor needle (single-line form)
check("T7 create-flavor @ §7.2 footprint",
      "a CREATED 0-byte file (the kernel applied O_CREAT before the signal\n  struck" in spec,
      "§7.2 footprint sentence, single-line form")

# --- T8: D-55 stderr-side scope ------------------------------------------------
check("T8a §6.1 stderr row scope",
      "stderr | empty on success — FOR REGULAR-FILE output paths" in spec, "§6.1")
check("T8b §12 silent-success scope",
      "silent success | Exit 0 with empty stdout and the output file written — for REGULAR-FILE output paths" in spec, "§12")

# --- T9: enumeration consistency ----------------------------------------------
s1 = re.search(r"D-01\.\.D-(\d+) in\nappendix/03-decision-register\.md are all DECIDED", spec)
s11 = re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED", spec)
check("T9 §1/§11 enumerations = 56", bool(s1 and s11 and s1.group(1) == s11.group(1) == "56"),
      "§1=%s §11=%s" % (s1 and s1.group(1), s11 and s11.group(1)))

# --- C1: register completeness --------------------------------------------------
ids = re.findall(r"^\| (D-\d+b?) \|", reg, re.M)
want = {"D-%02d" % i for i in range(1, 57)} | {"D-11b"}
missing = want - set(ids)
all_decided = all(re.search(r"^\| %s \|.*\| DECIDED \|" % re.escape(i), reg, re.M) for i in ids)
check("C1 register D-01..D-56 + D-11b all DECIDED", not missing and all_decided,
      "rows=%d missing=%s" % (len(ids), sorted(missing)))

# --- H1: header count nit (documents SR10-F-02; PASS = discrepancy recorded) ----
m = re.search(r"appendix/47-rev11-adv10-folds-probes\.py \(cycle-11 revision evidence, (\d+)/\1 PASS", spec)
check("H1 header '16/16' vs file's 17 checks (SR10-F-02)",
      bool(m) and m.group(1) == "16",
      "header claims 16/16; the probe prints 17 checks (16 adv-c10 checks + F-series renumbered); count-arithmetic nit only")

print()
fails = [r for r in results if not r[1]]
print("TOTAL: %d checks, %d failures" % (len(results), len(fails)))
for n, _, d in fails:
    print("  FAILED: " + n + " :: " + d)
sys.exit(1 if fails else 0)

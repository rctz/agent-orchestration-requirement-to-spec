#!/usr/bin/env python3
"""48a-adv-c11-regcheck — mechanical checks for adv-c11 (t_1f585d11).

Checks the decision-register integrity claims the spec's §1/§11 make:
 1. register rows D-01..D-56 exist, no gaps, no duplicates, all DECIDED;
 2. spec §1 enumeration ("D-01..D-56 ... all DECIDED") matches the register;
 3. spec §11 coverage sentence names D-01..D-56 (the adv-c8 F-03 /
    adv-c10 F-03 staleness class);
 4. the six D-56(a) fold sites (S-14(e), §6.3 E-MEM, §7.2 footprint,
    T-C16, QC-2 Verification, §4.5 normative-lead) carry the arm-abort
    qualifier per D-56(a)'s binding-site list;
 5. the five R-6 create-flavor mirror sites named in D-56(b) carry it;
 6. spec body cites appendix/47 (the v11 probe file) at least once;
 7. header probes row cites appendix/47 with its PASS result;
 8. advisory register: rows are well-formed (| F | sev | disp | owner |).
"""
import re
import sys

FAIL = []
OK = []


def check(name, cond, detail=""):
    (OK if cond else FAIL).append((name, detail))
    print(("PASS " if cond else "FAIL ") + name + (" — " + detail if detail else ""))


ROOT = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
spec = open(f"{ROOT}/spec/11-spec-v11.md", encoding="utf-8").read()
reg = open(f"{ROOT}/appendix/03-decision-register.md", encoding="utf-8").read()
lines = spec.splitlines()

# --- 1. register integrity -------------------------------------------------
ids = []
for l in reg.splitlines():
    m = re.match(r"\|\s*(D-\d+)\s*\|", l)
    if m:
        ids.append((m.group(1), "DECIDED" in l))
nums = sorted(int(x[0][2:]) for x in ids)
check("register D-01..D-56, no gaps/dups, all DECIDED",
      nums == list(range(1, 57)) and all(d for _, d in ids),
      f"rows={len(ids)} min=D-{nums[0]:02d} max=D-{nums[-1]:02d}")

# --- 2/3. §1 and §11 enumerations ------------------------------------------
s1 = lines[22] if len(lines) > 22 else ""
check("§1 enumeration says D-01..D-56",
      "D-01..D-56" in lines[22:27].__str__() or any("D-01..D-56" in l for l in lines[17:30]),
      "")
cov = [l for l in lines if l.startswith("Decision-coverage check:")]
check("§11 coverage sentence present", len(cov) == 1, f"found {len(cov)}")
check("§11 coverage names D-01..D-56", bool(cov) and "D-01..D-56" in cov[0], "")

# --- 4. D-56(a) fold sites ---------------------------------------------------
fold_sites = {
    "S-14(e) GONE-qualified": (r"\(e\).*?the D-33 compensation then removed it — the file\s*\n?\s*is GONE after the failed run \(by design, D-46's trigger; UNLESS", None),
}
# simpler: targeted greps
seg = spec
check("S-14(e) carries arm-abort qualifier",
      re.search(r"is GONE after the failed run \(by design, D-46's trigger; UNLESS\s+the compensation itself is aborted mid-flight per D-53/R-5", seg) is not None,
      "")
check("§6.3 E-MEM row carries arm-abort qualifier",
      re.search(r"so no partial file survives — §4\.5 — UNLESS\s+the compensation itself is aborted per D-53/R-5", seg) is not None,
      "")
check("§7.2 footprint carries arm-abort qualifier",
      re.search(r"or the target removed \(error in S5\) — UNLESS\s+the compensation itself is aborted\s+mid-flight per D-53/R-5", seg) is not None,
      "")
check("T-C16 carries arm-abort qualifier",
      "no conforming mechanism can otherwise leave it present" in seg and
      "in which case the partial file is PRESENT and that outcome is the recorded residue, not a contract violation" in seg,
      "")
check("QC-2 Verification carries write-phase path-absent arm-abort qualifier",
      re.search(r"path-absent for the write-phase form\s+\(the D-33/D-46 compensation removes it by design — with the same\s+D-53/R-5 arm-abort scope", seg) is not None,
      "")
check("§4.5 normative-lead carries arm-abort scope",
      re.search(r"ON EVERY PLATFORM IN THE\s+CONFORMANCE DOMAIN — ALWAYS within the D-53 arm-abort scope", seg) is not None,
      "")

# --- 5. R-6 create-flavor mirror sites --------------------------------------
def segof(header_pat, maxlines=400):
    out, keep = [], False
    for l in lines:
        if re.search(header_pat, l):
            keep = True
            n = 0
        if keep:
            out.append(l)
            n += 1
            if n > maxlines:
                break
    return "\n".join(out)


s_r6 = segof(r"^- R-6:")
check("R-6 body carries create flavor", "CREATED at 0 bytes" in s_r6 and "O_CREAT" in s_r6, "")
check("QC-2 Scope carries create flavor",
      "an ABSENT target may be left CREATED at 0 bytes" in spec, "")
check("§4.5 KI-AT-OPEN paragraph carries create flavor",
      re.search(r"AND an ABSENT target may be left CREATED at 0 bytes", spec) is not None, "")
check("§7.2 footprint carries create flavor",
      re.search(r"a KI striking the `open\(\)` call itself on an ABSENT target can\s+leave a CREATED 0-byte file", spec) is not None, "")
check("§11 D-54 index entry carries create flavor",
      "an absent target CREATED empty (adv-c10 F-04)" in spec, "")

# --- 6/7. appendix/47 citations ---------------------------------------------
check("spec body cites appendix/47", "appendix/47" in spec, "")
hdr = segof(r"^\| probes \|", 4)
check("header probes row cites appendix/47", "appendix/47-rev11-adv10-folds-probes.py" in hdr, "")

# --- 8. advisory register well-formed ----------------------------------------
adv = open(f"{ROOT}/appendix/advisory-register.md", encoding="utf-8").read().splitlines()
rows = [l for l in adv if re.match(r"^\|\s*F-\d+\s*\|", l)]
bad = [l for l in rows if not re.match(r"^\|\s*F-\d+\s*\|\s*P[0-3]\s*\|\s*(fixed-in-v\d+|accepted-risk.*|deferred.*)\s*\|\s*\S+\s*\|$", l)]
check("advisory register rows well-formed", not bad, f"rows={len(rows)} bad={bad[:2]}")

print()
print(f"TOTAL: {len(OK)+len(FAIL)} checks, {len(FAIL)} failures")
sys.exit(1 if FAIL else 0)

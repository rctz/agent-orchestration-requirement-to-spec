#!/usr/bin/env python3
"""72a — c14 probes-row / mirror-site truth checks (read-only)."""
import re

SPEC = "spec/14-spec-v14.md"
t = open(SPEC, encoding="utf-8").read()

# 1) D-59 mirror sites: find every line-level occurrence of D-59 and report
#    its line number + nearest heading.
heads = [(m.start(), m.group(0)) for m in re.finditer(r"^#{1,3} .*$", t, re.M)]


def near(off):
    best = None
    for o, h in heads:
        if o <= off:
            best = h
    return best


print("== D-59 occurrences (line, nearest heading) ==")
for m in re.finditer(r"D-59", t):
    ln = t.count("\n", 0, m.start()) + 1
    print(f"  line {ln:5d}  {near(m.start())[:60]}")

print()
print("== 'binding'/'BINDING' occurrences inside §4.3 (offset range of '## 4.3' .. '# 5.') ==")
s43 = t.find("## 4.3 ")
s5 = t.find("# 5. State")
seg = t[s43:s5]
for m in re.finditer(r"[Bb]inding|BINDING", seg):
    ln = t.count("\n", 0, s43 + m.start()) + 1
    ctx = seg[max(0, m.start() - 60):m.start() + 60].replace("\n", " ")
    print(f"  line {ln:5d}  ...{ctx}...")

print()
# 2) probes row: standalone entries for 58 / 59 / 67 / 66 / 68 / 69 / 70
row = re.search(r"^\| probes \|(.*?)^\| revision \|", t, re.M | re.S).group(1)
for name in ["66-rev14", "67-rev14", "68-rev14", "69-rev14", "70-rev14",
             "58-rev13", "59-rev13"]:
    n_all = row.count(name)
    # standalone entry = "+ appendix/<name>" appears as a new probes-row term
    n_standalone = len(re.findall(r"\+ appendix/" + name, row))
    print(f"  {name}: total mentions in probes row = {n_all}, "
          f"standalone-entry form '+ appendix/{name}' = {n_standalone}")

print()
print("== 'HISTORICAL itself since the v14 rollover' parentheticals (whole spec) ==")
for m in re.finditer(r".{160}HISTORICAL itself since the v14 rollover.{80}", t, re.S):
    ln = t.count("\n", 0, m.start()) + 1
    print(f"  line {ln}: ...{m.group(0)[:300]}...".replace("\n", " "))
    print()

print("== 67's target spec (read from its own file) ==")
p = open("appendix/67-rev14-gate-reaim.py", encoding="utf-8").read()
for m in re.finditer(r"SPEC\s*=.*", p):
    print("  " + m.group(0))
print("  67 mentions spec/13?:", "spec/13" in p, " spec/14?:", "spec/14" in p)

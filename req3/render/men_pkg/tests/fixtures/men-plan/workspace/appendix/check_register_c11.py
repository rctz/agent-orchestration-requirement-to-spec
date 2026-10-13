#!/usr/bin/env python3
"""Verify register D-id continuity D-01..D-56 and all-DECIDED status."""
import re

text = open("appendix/03-decision-register.md").read()
ids = re.findall(r"^\| (D-\d+) \|", text, re.M)
nums = sorted(int(i.split("-")[1]) for i in ids)
expected = list(range(1, max(nums) + 1))
missing = [n for n in expected if n not in nums]
dupes = [n for n in set(nums) if nums.count(n) > 1]
non_decided = [
    line.split("|")[1].strip()
    for line in text.split("\n")
    if re.match(r"^\| D-\d+ \|", line) and " DECIDED " not in line
]
print("rows:", len(nums), "max:", max(nums))
print("missing:", missing)
print("dupes:", dupes)
print("non-DECIDED:", non_decided)
print("OK" if not missing and not dupes and not non_decided else "PROBLEM")

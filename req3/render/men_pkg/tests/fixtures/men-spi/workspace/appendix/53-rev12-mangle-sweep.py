#!/usr/bin/env python3
"""Mangle sweep for spec/12-spec-v12.md:
1. isolated pipe-lines: a line starting with '|' whose NEIGHBORS do not
   start with '|' -> patch mangle (real table rows have '|'-neighbors)
2. doubled pipes inside a line ('||' not at a table separator boundary)
3. every mirrored absolute-claim phrase carries its qualifier (D-57 fold
   mirror check): 'byte-untouched' at-open sentences must either scope to
   OSError or carry the R-6/D-57 exception nearby.
"""
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = HERE + "/spec/12-spec-v12.md"
lines = open(SPEC, encoding="utf-8").read().split("\n")

failures = []


def fail(msg):
    failures.append(msg)
    print("FAIL -", msg)


def ok(msg):
    print("PASS -", msg)


# 1. isolated pipe-lines
mangles = []
for i, line in enumerate(lines):
    if line.startswith("|"):
        prev_pipe = i > 0 and lines[i - 1].startswith("|")
        next_pipe = i + 1 < len(lines) and lines[i + 1].startswith("|")
        if not (prev_pipe or next_pipe):
            mangles.append((i + 1, line[:90]))
if mangles:
    for ln, txt in mangles:
        fail("isolated pipe-line at %d: %r" % (ln, txt))
else:
    ok("no isolated pipe-lines (mangle sweep 1)")

# 2. '||' outside header separators
bad_pipes = []
for i, line in enumerate(lines):
    if line.strip() == "|---|---|" or line.startswith("|---"):
        continue
    if "||" in line:
        bad_pipes.append((i + 1, line[:90]))
if bad_pipes:
    for ln, txt in bad_pipes:
        fail("doubled '||' at %d: %r" % (ln, txt))
else:
    ok("no doubled pipes (mangle sweep 2)")

# 3. mirrored at-open 'byte-untouched' sentences carry the scoping/exception
text = open(SPEC, encoding="utf-8").read()
norm = re.sub(r"\s+", " ", text).lower()
sites = [
    m.start() for m in re.finditer(r"byte-untouched", norm)
]
uns = []
for s in sites:
    window = norm[max(0, s - 260):s + 260]
    has_scoping = ("d-46" in window and "oserror" in window) or \
                  ("d-57" in window) or ("r-6" in window) or \
                  ("pre-open encode" in window) or ("encode, d-43" in window) or \
                  ("e-write" in window) or \
                  ("error before s5" in window)
    if not has_scoping:
        uns.append(norm[max(0, s - 60):s + 80])
if uns:
    for u in uns:
        fail("byte-untouched without OSError scoping or D-57/R-6 exception: ...%s..." % u)
else:
    ok("every 'byte-untouched' site is scoped or carries the D-57/R-6 exception (%d sites)" % len(sites))

# 4. 'filesystem untouched' claims (the F-01 textual shadow) only in
# serialize/encode contexts
fs_sites = [m.start() for m in re.finditer(r"filesystem untouched", norm)]
bad_fs = []
for s in fs_sites:
    window = norm[max(0, s - 200):s + 120]
    if not any(k in window for k in ("serialize", "encode", "d-44", "d-43",
                                     "nothing is open", "nothing open")):
        bad_fs.append(norm[max(0, s - 60):s + 80])
if bad_fs:
    for u in bad_fs:
        fail("'filesystem untouched' outside serialize/encode context: ...%s..." % u)
else:
    ok("all 'filesystem untouched' sites are serialize/encode-scoped (%d sites)" % len(fs_sites))

print()
total = 4
print("TOTAL: %d sweeps, %d FAILURES" % (total, len(failures)))
sys.exit(1 if failures else 0)

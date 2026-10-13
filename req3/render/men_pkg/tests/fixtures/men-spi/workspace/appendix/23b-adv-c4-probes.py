# 23b-adv-c4-probes.py — adversarial-early cycle 4 live probes
# Target spec: spec/04-spec-v4.md (DRAFT)
# Focus: S5 compensation on OPEN-failure paths (F-01 candidate), plus
# span/StopIteration sanity (A1) and E-MEM phase-form textual checks.
# Run: python3 23b-adv-c4-probes.py   (host interpreter, sandbox dir)

import csv
import io
import os
import sys
import tempfile

FAILED = []

def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name} — {detail}")
    if not cond:
        FAILED.append(name)

# ---------------------------------------------------------------- P1: open-failure compensation destroys pre-existing target
# Spec 4.5: "ANY exception raised after the open — OSError (..., EACCES at
# open, ...) — first runs the compensation"; compensation = best-effort
# os.remove(path) "of the exact path this stage opened", with "IGNORE any
# exception from the remove (including ENOENT when open itself fails...)".
# Counterexample environment: pre-existing output.json, chmod 0o444 (owner
# read-only), parent dir writable, POSIX. open(path,'wb') -> EACCES;
# os.remove(path) -> succeeds (needs only dir write permission).
def probe_openfail_compensation():
    d = tempfile.mkdtemp(prefix="adv4_of_")
    target = os.path.join(d, "output.json")
    with open(target, "wb") as f:
        f.write(b'{"prior":"good run"}\n')
    os.chmod(target, 0o444)          # owner read-only; dir stays writable
    dstat = os.stat(d)
    opened = False
    removed = False
    try:
        try:
            fh = open(target, "wb")   # expected: PermissionError (EACCES)
            opened = True
            fh.close()
        except OSError:
            # spec-pinned compensation: runs on EACCES-at-open too
            try:
                os.remove(target)
                removed = True
            except OSError:
                removed = False
    finally:
        pass
    exists_after = os.path.exists(target)
    # restore for cleanup
    if exists_after:
        os.chmod(target, 0o644)
    return opened, removed, exists_after

opened, removed, exists_after = probe_openfail_compensation()
check("P1a open('wb') on chmod-444 pre-existing file raises EACCES (non-root)",
      (not opened) or os.geteuid() == 0,
      f"opened={opened} euid={os.geteuid()}")
check("P1b best-effort os.remove on that unopened path SUCCEEDS on POSIX",
      os.geteuid() == 0 or (removed and not exists_after),
      f"removed={removed} exists_after={exists_after} euid={os.geteuid()}")

# Same shape with a symlink whose target is unwritable: open fails through
# the link, os.remove unlinks the SYMLINK itself.
def probe_symlink_variant():
    if os.geteuid() == 0:
        return None  # root bypasses EACCES; variant not observable as root
    d = tempfile.mkdtemp(prefix="adv4_sl_")
    real = os.path.join(d, "real.json")
    with open(real, "wb") as f:
        f.write(b"prior-good\n")
    os.chmod(real, 0o444)
    link = os.path.join(d, "link.json")
    os.symlink(real, link)
    opened = False
    try:
        try:
            fh = open(link, "wb")
            opened = True
            fh.close()
        except OSError:
            try:
                os.remove(link)
            except OSError:
                pass
    finally:
        pass
    link_gone = not os.path.lexists(link)
    real_intact = os.path.exists(real)
    os.chmod(real, 0o644)
    return opened, link_gone, real_intact

r = probe_symlink_variant()
check("P1c EACCES-at-open via read-only symlink target: compensation deletes the symlink itself",
      r is None or (r[0] is False and r[1] is True and r[2] is True),
      f"result={r} (None = skipped as root)")

# Reference contrast: the REQ-010/D-33 license scopes removal to "the path
# the tool opened" / "the partially written file" — on EACCES-at-open no
# open succeeded and no partial file of THIS run exists. Textual anchors:
REQ010 = "a best-effort `os.remove` of the path the tool opened"
SPEC45 = "EACCES at open"
with open("spec/04-spec-v4.md", "r", encoding="utf-8") as f:
    SPEC = f.read()
with open("requirements/07-requirements-v7.md", "r", encoding="utf-8") as f:
    REQS = f.read()
check("P1d REQ-010 removal license wording present verbatim",
      REQ010 in REQS, "requirements line 292 area")
check("P1e spec 4.5 lists 'EACCES at open' as a compensation trigger",
      SPEC45 in SPEC, "spec 4.5 Behavior write-then-flush clause")
check("P1f spec 4.5 compensates 'of the exact path this stage opened'",
      "the exact path this stage opened" in SPEC, "compensation definition")

# ---------------------------------------------------------------- P2: E-MEM serialize-phase path naming gloss vs template
check("P2a E-MEM template names <in> for parse/serialize phases",
      "parse/serialize phases: `csv2json: error: out of memory while converting <in>`" in SPEC,
      "6.3 E-MEM template cell")
check("P2b E-MEM parenthetical gloss claims 'the OUTPUT path named' for write/serialize",
      "the OUTPUT path named" in SPEC,
      "same cell's parenthetical")

# ---------------------------------------------------------------- A1: tell()-span + StopIteration on trailing-terminator files
def spans(text):
    rf = io.StringIO(text, newline="")
    rd = csv.reader(rf)
    out = []
    start = 0
    while True:
        try:
            rec = next(rd)
        except StopIteration:
            break
        end = rf.tell()
        out.append((rec, text[start:end]))
        start = end
    return out, start

for label, txt in [
    ("CRLF final terminator", "a,b\r\nc,d\r\n"),
    ("CR final terminator", "a,b\rc,d\r"),
    ("LF final terminator", "a,b\nc,d\n"),
    ("no final terminator", "a,b\nc,d"),
    ("unterminated last record", 'a,b\n"c,d'),
]:
    recs, final_start = spans(txt)
    total = len(txt)
    check(f"A1[{label}] last span ends at EOF; no phantom empty record",
          final_start == total and all(r is not None for r, _ in recs),
          f"records={len(recs)} start_end={final_start} len={len(txt)}")

# KeyboardInterrupt is a BaseException, not an Exception: try/finally runs on
# it, except Exception does not — the two reference readings of 4.5 diverge.
check("A2 KeyboardInterrupt is not an Exception subclass (except Exception misses it; finally still runs)",
      not issubclass(KeyboardInterrupt, Exception),
      "compensation shape divergence for Ctrl-C mid-write")

print(f"TOTAL FAILURES: {len(FAILED)}")
sys.exit(1 if FAILED else 0)

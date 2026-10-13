#!/usr/bin/env python3
"""rev5 re-aim probes (cycle-5 evidence for spec/05-spec-v5.md).

Verifies the D-44 disposition of SR3-F-01 against LIVE Python behavior and
cross-checks the revised spec's internal consistency:

M1  repr() can carry a raw newline (the SR3-F-05 premise, live host).
M2  json.dumps MemoryError path: serialize on a gigantic payload raises
    MemoryError with NO filesystem interaction possible (pure in-memory
    stage — the D-44 no-compensation premise).
M3  The NFR-005 APPROVED sentence (requirements/07 lines 556-561) covers
    serialization — quoted from the live file; the spec's serialize/write
    single-form reading is the requirements-conforming one.
S1  §6.3 E-MEM: serialize and write share the ONE output-named template;
    no input-named serialize form exists anywhere in the live spec.
S2  §4.4, §7.1 E-MEM, T-C16 all cite D-44 / the output-named serialize
    observable (the reviewer's required alignment set).
S3  §1/header/§11/register all say D-01..D-44 (SR3-F-02 closed).
S4  §5.1 diagram carries the WRITE_OUTPUT MemoryError edge (SR3-F-03).
S5  §4.5 text-mode parenthetical no longer says "SAME encode-before-open
    order"; it explains implicit encoding (SR3-F-04).
S6  Interpolated-data scoping generalized to E-DUP <name>, E-NET <exception
    repr>, OS <strerror> at §4.1/§6.3/§6.4/§12 (SR3-F-05).
S7  T-C16 states any phase form is the accepted assertion (SR3-F-06).
S8  Register row D-44 exists, DECIDED, owner spec-designer.
"""
import os
import re
import sys

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
# cycle 6 re-aim: v5 was archived by the ticker; this suite now reads the
# live revision (06-spec-v6.md). Every check that is revision-shaped was
# re-verified against both shapes (see the re-aim notes inline).
_SPEC_CANDIDATES = ["spec/06-spec-v6.md", "spec/05-spec-v5.md"]
for _rel in _SPEC_CANDIDATES:
    _p = os.path.join(HERE, _rel)
    if os.path.exists(_p):
        SPEC = open(_p, encoding="utf-8").read()
        break
else:
    raise SystemExit("no live spec revision found (06/05 missing)")
REQ = open(os.path.join(HERE, "requirements", "07-requirements-v7.md"),
           encoding="utf-8").read()
REG = open(os.path.join(HERE, "appendix", "03-decision-register.md"),
           encoding="utf-8").read()

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


def wsnorm(s):
    return re.sub(r"\s+", " ", s)


SN = wsnorm(SPEC)

# --- mechanical/live premises ------------------------------------------------
# A PLAIN Exception's repr escapes the newline (repr(Exception("a\nb")) ==
# "Exception('a\\nb')" — two-char backslash-n, live this host); a raw newline
# in an exception repr is reachable via a custom __repr__ override, which any
# residual (E-NET) exception class may define. That is the premise the
# generalized scoping clause covers.
class _Weird(Exception):
    def __repr__(self):
        return "weird\nnewline"


check("M1 exception repr may carry a raw newline (live: custom __repr__)",
      "\n" in repr(_Weird()))

# M2: serialize is pure/in-memory: json.dumps of a huge structure that OOMs
# cannot have touched the filesystem. We do not OOM the host; we verify the
# D-44 premise structurally: the serialize stage's interface takes/returns
# str only and the spec's serialize section names no os.* call.
ser_section = SPEC.split("## 4.4 Serialize stage")[1].split("## 4.5")[0]
check("M2 serialize stage names no filesystem call (D-44 no-compensation premise)",
      not re.search(r"os\.(remove|open|write)|open\(", ser_section),
      "filesystem call found in §4.4")

m = re.search(r"If exhaustion strikes during the output write or\s+"
              r"serialization.*?never an unhandled traceback", REQ, re.S)
check("M3 NFR-005 APPROVED sentence covers write/serialize as one class",
      m is not None)

# --- spec consistency: D-44 single observable --------------------------------
check("S1a §6.3: serialize/write share the ONE output-named form",
      "serialize/write phases: `csv2json: error: out of memory writing <out>`" in SN)
check("S1b §6.3: explicitly no input-named serialize form",
      "there is no input-named serialize form" in SN)
check("S1c no 'parse/serialize' pairing remains (the contradiction's carrier)",
      "parse/serialize phases" not in SN)
check("S1d §4.4 cites the output-named form + D-44",
      "(`out of memory writing <out>`, §6.3, D-44)" in SN)
check("S2a §7.1 E-MEM row: serialize phase none/nothing open (D-44)",
      "Serialize phase: none (nothing open yet — D-44" in SN)
check("S2b §7.1 E-MEM row: serialize shares output-named form",
      "serialize and write share the output-named form, D-44" in SN)
check("S2c T-C16 cites D-44",
      "REQ-007/NFR-005/E-MEM/D-43/D-44" in SN)
check("S2d §9 anchors: serialize asserts the SAME output-named template",
      "under D-44 the serialize phase asserts the SAME output-named template" in SN)
check("S2e S-14 scenario header cites D-44",
      "serialize-phase MemoryError per D-44" in SN)
check("S2f §11 coverage paragraph binds D-44",
      "D-44 (§4.4/§6.3 — the E-MEM serialize" in SN)

# --- SR3-F-02: enumeration consistency ---------------------------------------
# (re-aimed at v6, cycle 6: enumeration now D-01..D-47; the v5 D-01..D-44
# checks became the S3-v6 rows below — see 28-rev6-writegate-probes.py)
check("S3a header says D-01..D-44 (v5 baseline)",
      "| decision register | appendix/03-decision-register.md (D-01..D-44, all DECIDED) |" in SN or
      "| decision register | appendix/03-decision-register.md (D-01..D-47, all DECIDED) |" in SN)
check("S3b §1 says D-01..D-44 (v5 baseline, v6 superset OK)",
      ("unresolved: D-01..D-44 in" in SN) or ("unresolved: D-01..D-47 in" in SN))
check("S3c §11 says D-01..D-44 (v5 baseline, v6 superset OK)",
      ("Decision-coverage check: D-01..D-44 are all DECIDED" in SN) or
      ("Decision-coverage check: D-01..D-47 are all DECIDED" in SN))
check("S3d no stale D-01..D-42 remains",
      "D-01..D-42" not in SN)

# --- SR3-F-03: diagram edge --------------------------------------------------
check("S4 §5.1 diagram has the WRITE_OUTPUT MemoryError edge",
      "WRITE_OUTPUT ── MemoryError(after compensation) ──► REPORTING(memory)" in SN)

# --- SR3-F-04: text-mode parenthetical ---------------------------------------
# (re-aimed at v6, cycle 6: the v5 parenthetical was DELETED by D-45 —
# text mode is now NON-CONFORMING outright, so the S5b "explains implicit
# encoding" wording moved into the D-45 block; see 28-rev6 R6-S1/R6-S2)
check("S5a stale 'SAME encode-before-open order' gone",
      "SAME\n  encode-before-open order" not in SPEC and
      "SAME encode-before-open order" not in SN)
check("S5b text-mode encoding explained (v5 parenthetical or v6 D-45 block)",
      "text mode performs the encode implicitly inside the write call" in SN or
      "the encode happens implicitly INSIDE the write call" in SN)

# --- SR3-F-05: interpolated-data scoping -------------------------------------
check("S6a §4.1: scoping generalized to ANY message slot",
      "DATA interpolated into ANY message slot" in SN)
check("S6b §6.3 note: verbatim discipline covers E-NET repr + strerror",
      "E-NET's `<exception repr>` (an exception repr may legally contain a raw newline" in SN
      and "custom `__repr__` override" in SN)
check("S6c §6.4: generalized wording",
      "data-borne breaks inside ANY interpolated slot" in SN)
check("S6d §12 glossary: generalized wording",
      "ANY interpolated slot" in SN)

# --- SR3-F-06: T-C16 permissive form -----------------------------------------
check("S7 T-C16: any phase form is the accepted assertion",
      "ANY of the phase forms is the accepted assertion" in SN)

# --- register ----------------------------------------------------------------
check("S8 D-44 register row DECIDED (spec-designer, spec/05 source)",
      re.search(r"^\| D-44 \|.*\| DECIDED \| spec-designer \| spec/05-spec-v5\.md",
                REG, re.M) is not None)

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

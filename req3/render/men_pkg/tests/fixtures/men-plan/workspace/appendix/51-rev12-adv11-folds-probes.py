#!/usr/bin/env python3
"""Rev12 probes (card t_8c30c86b): close adv-c11 F-01..F-04 on spec/12-spec-v12.md.

Findings source: appendix/48-adv-c11.md (adv-early#11; card t_1f585d11 has no
board result, so this revision cites the findings ARTIFACT, not a verdict).

Sections:
  B  behavioral re-proofs, live (D-57 mechanism + D-58 fused-scan identity)
  T  text pins, RED before the fold, GREEN after (all mirrored sites)
  R  regression: the five D-56(a) arm-abort qualifier sites still carry their
     folds (the D-57 edits must not erase them)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "..", "spec", "12-spec-v12.md")
REGISTER = os.path.join(HERE, "..", "appendix", "03-decision-register.md")
PY = sys.executable

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else "  [" + detail + "]"))


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def section(text, pat):
    """Extract from a top-level '# N.' heading (regex pat) to the next one.
    re.M is MANDATORY: without it every section returns '' (c10 lesson)."""
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

# ---------------------------------------------------------------------------
# B — behavioral: the at-open MemoryError window (D-57 classification basis)
# ---------------------------------------------------------------------------
# §4.5 reference shape with open() faulted at the wrapper-allocation point:
# raw fd created (kernel applies O_CREAT|O_TRUNC), closed by CPython's DECREF
# cleanup, then MemoryError — `fd` never binds. Mechanism class of the
# reviewer's appendix/48b P2a/P2b; re-proven live here as OUR evidence.

WRITER_ATOPEN_MEM = r'''
import os, sys

def _open_faulted(path):
    raw = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o666)
    os.close(raw)          # CPython cleanup: FileIO DECREF closes the fd
    raise MemoryError()    # wrapper allocation failed; fd never binds

def write_output(path, payload):
    fd = None
    try:
        fd = _open_faulted(path)
        fd.write(payload); fd.flush()
        fd.close(); fd = None
    except BaseException:
        if fd is not None:
            try: fd.close()
            except OSError: pass
            fd = None
            try: os.remove(path)
            except OSError: pass
        raise

def main(argv):
    out = argv[0]
    try:
        write_output(out, b'[{"a":"1"}]\n')
    except MemoryError:
        sys.stderr.write("csv2json: error: out of memory writing %s\n" % out)
        return 1
    except OSError as e:
        sys.stderr.write("csv2json: error: cannot write %s: %s\n" % (out, e.strerror))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def probe_behavioral():
    d = tempfile.mkdtemp()
    # (a) absent target -> CREATED 0-byte, E-MEM write-phase line, exit 1
    out1 = os.path.join(d, "absent.json")
    p1 = subprocess.run([PY, "-c", WRITER_ATOPEN_MEM, out1],
                        capture_output=True, text=True, timeout=30)
    st1 = (os.path.exists(out1), os.path.getsize(out1) if os.path.exists(out1) else None)
    check("B1 at-open MemoryError, ABSENT target: CREATED 0-byte, E-MEM write-phase, exit 1 (R-6/D-57 window live)",
          p1.returncode == 1 and "out of memory writing" in p1.stderr and st1 == (True, 0),
          "rc=%r stderr=%r state=%r" % (p1.returncode, p1.stderr.strip()[:90], st1))
    # (b) pre-existing target -> TRUNCATED 0-byte, same form
    out2 = os.path.join(d, "prior.json")
    with open(out2, "wb") as f:
        f.write(b'[{"prior":"good"}]\n' * 40)
    p2 = subprocess.run([PY, "-c", WRITER_ATOPEN_MEM, out2],
                        capture_output=True, text=True, timeout=30)
    st2 = (os.path.exists(out2), os.path.getsize(out2) if os.path.exists(out2) else None)
    check("B2 at-open MemoryError, PRE-EXISTING target: TRUNCATED 0-byte, E-MEM write-phase, exit 1",
          p2.returncode == 1 and "out of memory writing" in p2.stderr and st2 == (True, 0),
          "rc=%r stderr=%r state=%r" % (p2.returncode, p2.stderr.strip()[:90], st2))
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# B3 — D-58 fused-scan outcome identity: a fused single pass must produce the
# same N/M/row-start lines as the two-quantity reference on a CRLF/quote corpus
# ---------------------------------------------------------------------------

CORPUS = [
    "h1,h2\n1,x\n2,y\n",
    "h1,h2\n\"a\r\nb\",c,\"d\ne",           # CRLF interior, unterminated (T-U3 case)
    "h1,h2\n\"a\rb\",c,\"d\re",             # bare-CR interior
    "a,b\rc,d\rc\r",                        # CR-only records
    "h,k\n\"x\r\n\r\ny\",2\n",              # blank line inside quoted field
    "id,\"id\n1,2\n",                       # unterminated on header row
]


def two_pass_span(record_text):
    """§4.3.3 FSM with own record-relative counter (the D-28 collapse)."""
    st, i, c, opening = 0, 0, 0, None
    L = len(record_text)
    while i < L:
        ch = record_text[i]
        if ch == '"':
            st = {0: 2, 2: 3, 3: 2}.get(st, st)
            if st == 2 and opening is None:
                opening = c
            i += 1
        elif ch == ",":
            if st in (1, 3):
                st = 0
            i += 1
        elif ch in "\r\n":
            c += 1
            i += 2 if (ch == "\r" and record_text[i + 1:i + 2] == "\n") else 1
            if st in (0, 1, 3):
                st = 0
        else:
            st = 1 if st == 0 else st
            i += 1
    return st, opening, c


def fused_span(record_text):
    """D-58 fused shape: ONE pass computing the FSM state AND the break count
    from the same walk (the counter advances exactly where the reference's
    count_line_breaks does; the FSM transitions are unchanged)."""
    st, i, c, opening = 0, 0, 0, None
    L = len(record_text)
    while i < L:
        ch = record_text[i]
        if ch in "\r\n":
            c += 1
            i += 2 if (ch == "\r" and record_text[i + 1:i + 2] == "\n") else 1
            if st in (0, 1, 3):
                st = 0
            continue
        if ch == '"':
            st = {0: 2, 2: 3, 3: 2}.get(st, st)
            if st == 2 and opening is None:
                opening = c
        elif ch == ",":
            if st in (1, 3):
                st = 0
        elif st == 0:
            st = 1
        i += 1
    return st, opening, c


def probe_fused_identity():
    ok = True
    detail = ""
    for text in CORPUS:
        import csv as _csv
        import io as _io
        buf = _io.StringIO(text, newline="")
        reader = _csv.reader(buf)
        start, line = 0, 1
        while True:
            try:
                record = next(reader)
            except StopIteration:
                break
            end = buf.tell()
            span = text[start:end]
            a = two_pass_span(span)
            b = fused_span(span)
            n_two = line + (a[2] if a[0] == 2 else 0) - 1
            n_fus = line + (b[2] if b[0] == 2 else 0) - 1
            if a != b or n_two != n_fus:
                ok = False
                detail = "text=%r span=%r two=%r fused=%r" % (text, span, a, b)
                break
            line += a[2]
            start = end
    check("B3 D-58 fused single pass is outcome-identical to the two-quantity reference (6 corpora)",
          ok, detail)


probe_behavioral()
probe_fused_identity()

# ==== PART 2 (text pins + regressions) ====

# ---------------------------------------------------------------------------
# T1 — F-01/F-04 site fold: at-open MemoryError classified per D-57 at every
# mirrored site, each needle extracted FROM the section (site-specific wording,
# c11 F5 lesson — never reuse one site's phrase at another)
# ---------------------------------------------------------------------------

sec45 = section(spec_text, r"^## 4\.5 ")
sec51 = section(spec_text, r"^# 5\. ")
sec53 = section(spec_text, r"^## 5\.3 ")
sec63 = section(spec_text, r"^## 6\.3 ")
sec71 = section(spec_text, r"^## 7\.1 ")
sec72 = section(spec_text, r"^## 7\.2 ")
sec83 = section(spec_text, r"^## 8\.3 ")
sec101 = section(spec_text, r"^## 10\.1 ")
sec12g = section(spec_text, r"^# 12\. ")
qc2 = subsection(spec_text, r"^### QC-2 ", r"^### QC-3 ")


def site_has(sec, needle, name, note):
    site_has.counter += 1
    check("T1-%s %s" % (site_has.counter, name), norm(needle) in norm(sec), note)


site_has.counter = 0

# (1) §4.5 error paths: the at-open story now covers OSError AND MemoryError
site_has(sec45,
         "at-open failure — the open itself raising, whether OSError or "
         "MemoryError (D-57) — reports directly with NO compensation",
         "S4.5 error-paths: at-open failure class widened to OSError or MemoryError (D-57)",
         "exact folded sentence missing from §4.5 Error paths")

# (2) §4.5 KI-AT-OPEN paragraph gains the MemoryError trigger widening
site_has(sec45,
         "a MemoryError raised by the open call itself (fd never bound) is "
         "classified by the SAME observable",
         "S4.5 KI-AT-OPEN: MemoryError-at-open joins the D-54 classification (D-57)",
         "D-57 classification sentence missing from §4.5 at-open paragraph")

# (3) §5.1 diagram: the at-open MemoryError edge exists (F-04's operative fix)
site_has(sec51,
         "WRITE_OUTPUT ── MemoryError(at-open: fd never bound — NO compensation, D-57",
         "S5.1 diagram: at-open MemoryError edge present (F-04)",
         "the new WRITE_OUTPUT at-open MemoryError edge is missing")

# (4) §5.1 pre-open edge wording: 'filesystem untouched' must be scoped to
# encode only (F-01 evidence: the old wording was false for the at-open class)
site_has(sec51,
         "MemoryError(pre-open encode: nothing open — output path untouched)",
         "S5.1 pre-open encode edge: 'output path untouched' scoping",
         "pre-open edge not reworded to the output-path scoping")

# (5) §5.3 S-14: new (f) sub-case for the at-open MemoryError both flavors
site_has(sec53,
         "(f) a MemoryError striking the open call itself (fd never bound, D-57, "
         "closes adv-c11 F-01): the arm runs NO compensation and the E-MEM "
         "write-phase form is reported",
         "S5.3 S-14: (f) at-open MemoryError sub-case present",
         "S-14(f) missing")

# (6) §6.3 E-MEM row: phase-form note for the at-open MemoryError
site_has(sec63,
         "an at-open MemoryError (D-57) reports this write-phase form while the "
         "compensation has NOT run",
         "S6.3 E-MEM row: at-open MemoryError phase-form note",
         "E-MEM row lacks the D-57 at-open sentence")

# (7) §7.1 partial-failure taxonomy: the before-open survival rule carries the
# R-6/D-57 exception
site_has(sec71,
         "with the recorded at-open exceptions (R-6: a KI — or a MemoryError, D-57 — "
         "striking the open call itself",
         "S7.1 taxonomy: at-open exception covers KI or MemoryError",
         "taxonomy sentence not widened to the MemoryError trigger")

# (8) §7.2 footprint: the R-6 exception names both trigger classes
site_has(sec72,
         "a KI — or a MemoryError (D-57) — striking the open call itself",
         "S7.2 footprint: R-6 exception names both trigger classes",
         "footprint sentence not widened")

# (9) §8.3 T-C16: the 'no conforming mechanism' sentence reconciled with D-57
site_has(sec83,
         "no conforming mechanism can otherwise leave it present: after a "
         "successful open the every-exception compensation removes the target",
         "S8.3 T-C16: qualified no-conforming-mechanism sentence retained",
         "T-C16 core sentence lost in the fold")

site_has(sec83,
         "and an at-open failure (OSError or MemoryError, D-46/D-57) never ran "
         "the compensation — its 0-byte residue is the recorded R-6/D-57 class, "
         "not this sentence's concern",
         "S8.3 T-C16: at-open carve-out appended",
         "T-C16 lacks the at-open carve-out reconciling the reviewer's P2c")

# (10) QC-2 Scope: exception enumeration gains the at-open MemoryError
site_has(qc2,
         "the KI-at-open form and the MemoryError-at-open form (both: open "
         "itself raises, fd never bound, no compensation runs; a PRE-EXISTING "
         "target may be left 0-byte and an ABSENT target may be left CREATED "
         "at 0 bytes — both flavors R-6, §10.1, decisions D-54/D-57; the "
         "MemoryError trigger added per adv-c11 F-01",
         "QC-2 Scope: at-open exception enumerates KI and MemoryError",
         "QC-2 Scope exception enumeration not widened")

# (11) §10.1 R-6: trigger widened to 'KI or MemoryError'
site_has(sec101,
         "a KeyboardInterrupt — or a MemoryError (decision D-57, closing "
         "adv-c11 F-01) — raised BY the `open()` call itself",
         "S10.1 R-6: trigger widened to KI or MemoryError",
         "R-6 body not widened")

# (12) §12 glossary 'successful open' row: same widening
site_has(sec12g,
         "this includes a KeyboardInterrupt — or a MemoryError (D-57) — raised "
         "BY the open call",
         "S12 glossary: successful-open row widened to both triggers",
         "glossary row not widened")

# ---------------------------------------------------------------------------
# T2 — F-02 fold: D-58 fused scan + T-C9 hardware-class naming
# ---------------------------------------------------------------------------
site_has.counter = 0
site_has(section(spec_text, r"^## 4\.3 "),
         "CONFORMING FUSION (D-58, closes adv-c11 F-02): the FSM and the break "
         "count may be computed in ONE fused pass",
         "S4.3: D-58 fused-scan permission present",
         "§4.3 lacks the D-58 fusion rule")

site_has(section(spec_text, r"^## 8\.3 "),
         "The 30 s figure is stated on the documented REFERENCE HARDWARE CLASS "
         "for the envelope — a single-core general-purpose x86-64 or ARM64 "
         "SBC-class machine",
         "S8.3 T-C9: reference hardware class named",
         "T-C9 lacks the hardware-class sentence")

site_has(subsection(spec_text, r"^### QC-5 ", r"^### QC-6 "),
         "one decode; per record one tell/slice + ONE O(record) scan that may "
         "fuse the FSM state walk and the break count in a single pass (D-58",
         "QC-5 Mechanism: single fused scan wording",
         "QC-5 not reworded to the fused form")

# ---------------------------------------------------------------------------
# T3 — F-03 fold: T-C8 non-writable-dir sub-case carries the skip-as-root note
# ---------------------------------------------------------------------------
site_has.counter = 0
site_has(section(spec_text, r"^## 8\.3 "),
         "non-writable dir (mode 0555) → E-WRITE, no file created (SKIP AS "
         "ROOT — DAC_OVERRIDE defeats mode 0555 directories exactly as it "
         "defeats mode 444 files, T-C2's convention; adv-c11 F-03)",
         "S8.3 T-C8: non-writable-dir sub-case carries SKIP AS ROOT",
         "the skip-as-root note is missing from the non-writable-dir sub-case")

# ---------------------------------------------------------------------------
# R — regressions: D-56(a) five-site arm-abort qualifier must survive the edit
# ---------------------------------------------------------------------------
site_has.counter = 0
regress = [
    ("R1 S5.3 S-14(e) arm-abort qualifier",
     "UNLESS the compensation itself is aborted mid-flight per D-53/R-5"),
    ("R2 S6.3 E-MEM arm-abort residue",
     "the partial file PRESENT is the recorded residue (decision D-56(a), adv-c10 F-01; probe appendix/47 P1a"),
    ("R3 S7.2 footprint arm-abort clause",
     "UNLESS the compensation itself is aborted mid-flight per D-53/R-5 (a second KI or a second MemoryError inside the failure arm)"),
    ("R4 S8.3 T-C16 arm-abort scope",
     "unless the compensation itself is aborted mid-flight per D-53/R-5 (a SECOND KI, or a second MemoryError"),
    ("R5 QC-2 Scope double-KI residue",
     "a second KI inside the failure arm aborts the compensation mid-flight; the partial file survives — R-5"),
    ("R6 S7.1 taxonomy D-56(a) clause",
     "the arm-abort class is not KI-specific, D-56(a)/adv-c10 F-01"),
]
for name, needle in regress:
    check(name, norm(needle) in norm(spec_text), "D-56(a) fold erased at " + name)

# R7: the R-6 create flavor (D-56(b)) still present at its mirrored sites
for name, sec in [("R7a S4.5 KI-AT-OPEN", sec45),
                  ("R7b S7.2 footprint", sec72),
                  ("R7c §10.1 R-6", sec101),
                  ("R7d QC-2 Scope", qc2)]:
    ns = norm(sec).upper()
    check(name + " carries the create flavor",
          ("CREATED AT 0 BYTES" in ns) or ("CREATED 0-BYTE" in ns) or ("CREATED, 0-BYTE" in ns),
          "create flavor missing at " + name)

# ---------------------------------------------------------------------------
# T4 — register: D-57/D-58 appended, still DECIDED, coverage sentences current
# ---------------------------------------------------------------------------
reg = open(REGISTER, encoding="utf-8").read()
check("T4-1 register carries D-57 (DECIDED, owner spec-designer)",
      re.search(r"^\| D-57 \|.*\| DECIDED \| spec-designer \|", reg, flags=re.M) is not None,
      "D-57 row missing or not DECIDED/spec-designer")
check("T4-2 register carries D-58 (DECIDED, owner spec-designer)",
      re.search(r"^\| D-58 \|.*\| DECIDED \| spec-designer \|", reg, flags=re.M) is not None,
      "D-58 row missing or not DECIDED/spec-designer")

m = re.search(r"D-01\.\.D-(\d+) in\s*\nappendix/03-decision-register\.md are all DECIDED", spec_text)
check("T4-3 §1 enumeration refreshed to D-01..D-58",
      m is not None and m.group(1) == "58",
      "§1 enumeration at %s (expected 58)" % (m.group(1) if m else "??"))

m2 = re.search(r"decision register \| appendix/03-decision-register\.md \(D-01\.\.D-(\d+), all DECIDED\)", spec_text)
check("T4-4 header decision-register row at D-58",
      m2 is not None and m2.group(1) == "58",
      "header row at %s (expected 58)" % (m2.group(1) if m2 else "??"))

sec11 = section(spec_text, r"^# 11\. ")
m3 = re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED", sec11)
check("T4-5 §11 coverage sentence at D-58",
      m3 is not None and m3.group(1) == "58",
      "§11 coverage at %s (expected 58)" % (m3.group(1) if m3 else "??"))

# every D id bound in the §11 coverage paragraph actually exists in the register
bound = set(re.findall(r"D-(\d+[a-z]?)", sec11))
reg_ids = set(re.findall(r"^\| D-(\d+) \|", reg, flags=re.M))
phantom = sorted(int(b) for b in bound if b.isdigit() and int(b) > int(m3.group(1) if m3 else 0))
check("T4-6 no phantom D ids above the declared max in §11", not phantom, str(phantom))

# ---------------------------------------------------------------------------
# T5 — version/annotation hygiene
# ---------------------------------------------------------------------------
check("T5-1 header version row says v12",
      re.search(r"\| version \| v12 \|", spec_text) is not None, "version row not bumped")
check("T5-2 header status DRAFT", "| status | DRAFT |" in spec_text, "status not DRAFT")
check("T5-3 header revision row closes adv-c11 findings",
      "48-adv-c11.md" in spec_text, "revision row does not cite the findings file")
check("T5-4 probes row cites this probe file",
      "51-rev12-adv11-folds-probes.py" in spec_text, "probes row missing 51")
check("T5-5 no spec-review#11 verdict cited (card has no board result)",
      norm("spec-review#11 verdict PASS") not in norm(spec_text) and
      norm("the spec-review verdict is PASS") not in norm(spec_text) and
      "spec-review#11 PASS" not in spec_text,
      "phantom spec-review verdict cited")
check("T5-6 findings artifact cited with its no-result annotation",
      "adv-early#11" in spec_text and "no board result" in spec_text,
      "adv-c11 citation lacks the no-result annotation")

print()
total = len(_results)
fails = _results.count(False)
print("TOTAL: %d checks, %d FAILURES" % (total, fails))
sys.exit(1 if fails else 0)


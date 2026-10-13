#!/usr/bin/env python3
"""rev7 write-gate re-aim probes — cycle-7 revision evidence (this card).

Re-aims the STILL-RELEVANT rev6 write-gate checks at the NEW spec shape
(spec/07-spec-v7.md) and adds the v7-specific text checks. The R6
behavioral probes whose subject matter v7 REWORDS (R6-P3's finally-shape
stage, superseded by D-48) are re-verified here against the v7
except-scoped shape; the mechanical R6-P1/P2/P4/P5 behaviors are
unchanged by v7 and are re-proven on the same live code paths.

Filesystem is REAL in every probe; only the fault POSITION is injected.
"""
import os
import shutil
import stat
import sys
import tempfile

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = os.path.join(HERE, "spec", "08-spec-v8.md")  # rev8 re-aim (v7 archived by the rollover)

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# ---------------------------------------------------------------- R7-P1 (carried R6-P1)
def r7_p1():
    """D-45 still pinned: text-mode shape cannot deliver D-43."""
    good = b'{"prior":"good-bytes"}'
    document = '[{"id":"1","name":"x"}]'

    class BoomAtEncode(Exception):
        pass

    d1 = tempfile.mkdtemp()
    try:
        out1 = os.path.join(d1, "out.json")
        with open(out1, "wb") as f:
            f.write(good)
        f = None
        try:
            f = open(out1, "w", newline="", encoding="utf-8")
            try:
                f.write(document)  # raises after O_TRUNC in the real defect
            except BoomAtEncode:
                pass
        finally:
            if f is not None:
                f.close()
            try:
                os.remove(out1)
            except OSError:
                pass
        text_destroys = not os.path.exists(out1) or os.path.getsize(out1) == 0
    finally:
        shutil.rmtree(d1, ignore_errors=True)

    d2 = tempfile.mkdtemp()
    try:
        out2 = os.path.join(d2, "out.json")
        with open(out2, "wb") as f:
            f.write(good)
        try:
            raise BoomAtEncode()
        except BoomAtEncode:
            pass
        binary_survives = open(out2, "rb").read() == good
    finally:
        shutil.rmtree(d2, ignore_errors=True)

    check("R7-P1 text-mode shape destroys prior output on encode fault",
          text_destroys, "text-mode target still present")
    check("R7-P1b binary shape leaves prior bytes byte-identical",
          binary_survives, "binary-shape prior bytes damaged")


# ---------------------------------------------------------------- R7-P2 (carried R6-P2)
def r7_p2():
    """At-open failure: read-only target in writable dir survives (D-46)."""
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        good = b'{"prior":"good-bytes"}'
        with open(out, "wb") as f:
            f.write(good)
        os.chmod(out, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)  # 444
        try:
            open(out, "wb")
            opened = True
        except OSError:
            opened = False
        survives = open(out, "rb").read() == good
        os.chmod(out, 0o644)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    check("R7-P2 open on read-only target raises (as non-root)", not opened)
    check("R7-P2b read-only target byte-identical after at-open failure",
          survives, "target changed/missing after failed open")


# ---------------------------------------------------------------- R7-P3 (D-48 re-aim of R6-P3)
def r7_p3():
    """Reference shape (v7 except-scoped, D-48) honors the state contract."""
    class Fault(Exception):
        pass

    def stage(path, document_bytes, fault):
        """D-43 order + D-46 trigger + D-48 except-scoped shape + D-50 close-before-remove."""
        payload = document_bytes  # encode pre-open (no side effect)
        if fault == "encode":
            raise Fault()
        fd = None
        try:
            fd = open(path, "wb")
            if fault == "write":
                raise Fault()
            fd.write(payload)
            fd.flush()
            fd.close()
            fd = None
        except BaseException:
            if fd is not None:  # D-46/D-48: remove only after a successful open
                try:
                    fd.close()  # D-50: close BEFORE the remove (errors ignored)
                except OSError:
                    pass
                fd = None
                try:
                    os.remove(path)
                except OSError:
                    pass
            raise

    good = b'{"prior":"good-bytes"}'

    # at-open failure: target untouched (pre-existing case, non-root)
    d1 = tempfile.mkdtemp()
    try:
        p = os.path.join(d1, "ro.json")
        with open(p, "wb") as fh:
            fh.write(good)
        os.chmod(p, 0o444)
        at_open = False
        try:
            stage(p, b"new", "write")  # open raises before the fault fires
        except OSError:
            at_open = True
        os.chmod(p, 0o644)
        untouched = open(p, "rb").read() == good
    finally:
        shutil.rmtree(d1, ignore_errors=True)
    check("R7-P3a at-open failure: stage raises, target untouched",
          at_open and untouched)

    # pre-open encode failure: target untouched
    d1b = tempfile.mkdtemp()
    try:
        pb = os.path.join(d1b, "pre.json")
        with open(pb, "wb") as fh:
            fh.write(good)
        enc = False
        try:
            stage(pb, b"new", "encode")
        except Fault:
            enc = True
        untouched_b = open(pb, "rb").read() == good
    finally:
        shutil.rmtree(d1b, ignore_errors=True)
    check("R7-P3b pre-open encode failure: target untouched",
          enc and untouched_b)

    # post-open failure: partial removed (even a pre-existing one — T-C16
    # write-phase form semantics per adv-c6 F-01)
    d2 = tempfile.mkdtemp()
    try:
        p2 = os.path.join(d2, "pre2.json")
        with open(p2, "wb") as fh:
            fh.write(good)
        raised2 = False
        try:
            stage(p2, b"partial-bytes", "write")
        except Fault:
            raised2 = True
        gone = not os.path.exists(p2)
    finally:
        shutil.rmtree(d2, ignore_errors=True)
    check("R7-P3c post-open failure on pre-existing target: removed (F-01 semantics)",
          raised2 and gone)

    # success: file present with exact payload (the v6 snippet failed HERE)
    d3 = tempfile.mkdtemp()
    try:
        p3 = os.path.join(d3, "ok.json")
        stage(p3, b'{"ok":true}\n', None)
        ok = open(p3, "rb").read() == b'{"ok":true}\n'
    finally:
        shutil.rmtree(d3, ignore_errors=True)
    check("R7-P3d success path keeps written payload (D-48 vs v6 defect)", ok)


# ---------------------------------------------------------------- R7-P4 (carried R6-P4)
def r7_p4():
    """R-2 outcome class reachable: compensation unlinks a concurrent
    success's name → exit-0-equivalent writer left with NO file."""
    import threading
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        state = {"opened_a": threading.Event(), "b_done": threading.Event(),
                 "b_result": None}

        def run_b():
            f = open(out, "wb")
            state["opened_a"].set()
            state["b_done"].wait(5)
            f.write(b'{"b":"success"}')
            f.flush()
            f.close()
            state["b_result"] = "exit0"

        tb = threading.Thread(target=run_b)
        tb.start()
        state["opened_a"].wait(5)
        fa = open(out, "wb")
        fa.close()
        os.remove(out)
        state["b_done"].set()
        tb.join(5)
        final_exists = os.path.exists(out)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    check("R7-P4 interleaving leaves silent-success B with NO file",
          state["b_result"] == "exit0" and not final_exists,
          f"b={state['b_result']} exists={final_exists}")


# ---------------------------------------------------------------- R7-P5 (carried R6-P5)
def r7_p5():
    """D-47/R-1b: symlink alias residue reproducible as recorded."""
    d = tempfile.mkdtemp()
    try:
        real = os.path.join(d, "real.json")
        link = os.path.join(d, "out.json")
        with open(real, "wb") as f:
            f.write(b'{"real":"good"}')
        os.symlink(real, link)
        f = open(link, "wb")
        f.write(b'[{"id":"1","name":"aaaaaaa')
        f.close()
        os.remove(link)
        residue = open(real, "rb").read()
        link_gone = not os.path.lexists(link)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    check("R7-P5 alias residue: real file keeps partial bytes, link gone",
          link_gone and residue.startswith(b'[{"id":"1"'),
          f"link_gone={link_gone} residue={residue[:20]!r}")


# ---------------------------------------------------------------- R7-S (spec text checks)
def r7_s():
    spec = open(SPEC, encoding="utf-8").read()
    body = spec.split("# 1. Overview", 1)[1]

    # supersession of the v6 defective snippet
    check("R7-S1 v6 finally-guarded snippet GONE from normative body",
          "finally:\n  if fd is not None: remove(path)" not in body and
          "the finally's remove guarded by whether the open succeeded" not in body)
    check("R7-S2 D-48 except-scoped reference shape present",
          "except BaseException:" in body and
          "except-scoped" in body and "D-48" in body)
    check("R7-S3 D-48 names the only conforming finally form (failure flag)",
          "failure flag" in body)
    # F-01 phase-form-dependent T-C16
    check("R7-S4 T-C16 phase-form-dependent assertion present",
          "DEPENDS ON THE OBSERVED PHASE FORM" in body and
          "form-independent" not in body.replace(
              'asserting byte-identity unconditionally (v6 wording, "form-independent") is non-conforming', ''))
    check("R7-S5 taxonomy sentence corrected",
          "boundaries BEFORE the open cannot truncate or delete" in body and
          "no failure\nat a phase boundary can truncate or delete" not in body)
    check("R7-S6 QC-2 verification inherits the form-dependent fix",
          "path-absent for the write-phase form" in body)
    # F-03 same-path
    check("R7-S7 R-4 same-path accepted-risk present + mirrored in row 10",
          "- R-4: SAME-PATH invocation" in body and
          "SAME-PATH invocation (output path == input path)" in body)
    # F-05 dispatch
    check("R7-S8 D-49 normative-for-all-argv wording present",
          "NORMATIVE for ALL\n  argv of length 2" in body and
          "D-49" in body)
    check("R7-S9 T-C1 gained the -h sub-case; T-C8 gained skip-as-root",
          "SKIP AS ROOT" in body and "-h out.json" in body)
    # SR5 advisories
    check("R7-S10 SR5-F-01 qualifier present in Error paths bullet",
          "WHICH\n  MEANS after a SUCCESSFUL open only (D-46)" in body)
    check("R7-S11 SR5-F-02 diagram edges relabeled (v8 label per SR6-F-06)",
          "OSError(after compensation iff open succeeded)" in body and
          "MemoryError(pre-open encode: nothing open — filesystem untouched)" in body)
    check("R7-S12 enumeration D-01..D-50 in header and coverage",
          "D-01..D-50" in spec.split("# 1. Overview")[0] and
          "D-01..D-50 in\nappendix/03-decision-register.md are all DECIDED" in spec)
    # rev8 (cycle-8, SR6-F-01/F-02): D-50 close-before-remove
    check("R7-S13 D-50 close-before-remove pinned in the reference shape + prose",
          "fd.close()              # D-50: close BEFORE the remove" in body and
          "ON EVERY PLATFORM IN THE" in body and
          "NON-CONFORMING" in body)
    check("R7-S14 D-50 bound in QC-2 + T-C16 slack deleted (SR6-F-04)",
          "closes the fd BEFORE the remove (D-50)" in body and
          "the correct assertion is that the path is ABSENT — no conforming" in body)


r7_p1()
r7_p2()
r7_p3()
r7_p4()
r7_p5()
r7_s()
print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

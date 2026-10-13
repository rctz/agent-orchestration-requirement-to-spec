#!/usr/bin/env python3
"""adv-c6 probes — adversarial-early cycle 6 evidence (card t_f9c9d08e).

Executes the counterexamples for the cycle-6 findings against the NEW
v6 shapes (spec/06-spec-v6.md):

  P1  F-02: the §4.5 D-46 "reference shape" try/finally, taken as
      written, runs its finally on the SUCCESS path too — the guard
      `if fd is not None` is TRUE after a successful open — so it
      REMOVES the just-written output on every successful run (and
      never closes the fd). Contrast: the obviously-intended
      except-scoped shape behaves correctly on both paths.
  P2  F-01: a conforming chunked-write build whose MemoryError strikes
      POST-OPEN (T-C16's own accepted "out of memory writing <out>"
      form — the spec names "a chunked write may OOM at write")
      leaves a pre-existing output ABSENT (open truncated it, D-33
      compensation removed it) — T-C16's "prior bytes are byte-identical
      ... form-independent" assertion fails for this conforming outcome.
  P3  F-03: input==output same-path run with a mid-write failure — the
      pinned compensation deletes the file, which IS the user's input;
      source data destroyed, E-WRITE correctly reported, exit 1.
  P4  F-05: the pinned manual dispatch on `csv2json.py -h out.json`
      (argc==2) treats `-h` as a path -> E-READ exit 1; argparse's
      default on the same argv prints help and exits 0 — the two
      sanctioned shapes observably diverge (the §4.1 override clause
      exists but names no winner for option-looking positional args).
  P5  text checks: the contradiction sites coexist in the v6 draft
      (reference-shape finally snippet; T-C16 form-independent
      byte-identity; §7.1 "no failure at a phase boundary can truncate
      or delete a pre-existing target"; S-14(e) "partial file is
      removed"; T-C2 "(skip as root)" present while T-C8's read-only
      sub-case has no root guard; §7.1 E-MEM verification "prior bytes
      survive").

Filesystem is REAL in every probe; only the fault POSITION is injected
(mirroring the spec's own W-series / R6-series evidence method).
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = os.path.join(HERE, "spec", "06-spec-v6.md")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if not cond else detail)
    if not cond:
        fails.append(name)


# ---------------------------------------------------------------- P1 (F-02)
def p1():
    """Reference shape as written deletes the output on SUCCESS."""
    payload = b'[{"id":"1"}]\n'

    # --- shape exactly as §4.5 lines 616-620 give it:
    #     fd = None; try: fd = open(...); ... write/flush ...
    #     finally: if fd is not None: remove(path)
    def stage_as_written(path):
        fd = None
        try:
            fd = open(path, "wb")
            fd.write(payload)   # write
            fd.flush()          # flush
        finally:
            if fd is not None:
                try:
                    os.remove(path)
                except OSError:
                    pass

    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "out.json")
        stage_as_written(p)          # SUCCESS run, no exception
        exists_after_success = os.path.exists(p)
        check("P1 reference shape (as written) REMOVES output on success",
              not exists_after_success,
              f"file unexpectedly exists: {exists_after_success}")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # --- contrast: the intended except-scoped compensation
    def stage_intended(path, fault):
        fd = None
        try:
            fd = open(path, "wb")
            if fault:
                raise fault
            fd.write(payload)
            fd.flush()
        except BaseException:
            if fd is not None:
                try:
                    os.remove(path)
                except OSError:
                    pass
            raise

    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "out.json")
        stage_intended(p, None)
        ok_success = os.path.exists(p) and open(p, "rb").read() == payload
        try:
            stage_intended(p, MemoryError())
            raised = False
        except MemoryError:
            raised = True
        ok_failure = raised and not os.path.exists(p)
        check("P1b intended except-shape: success keeps file, failure removes",
              ok_success and ok_failure)
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- P2 (F-01)
def p2():
    """T-C16's form-independence claim refuted by its own accepted
    write-phase (post-open) form on a conforming chunked-write build."""
    class OOM_mid_write(Exception):
        pass

    def write_output_chunked(path, document):
        """Conforming chunked-write stage: D-43 encode BEFORE open,
        post-open every-exception compensation (D-46), E-MEM write-phase
        report (D-44 message shape)."""
        payload = document.encode("utf-8")          # (1) encode first
        half = len(payload) // 2
        fd = None
        try:
            fd = open(path, "wb")                    # (2) open
            fd.write(payload[:half])                 # (3a) chunk 1
            raise OOM_mid_write()                    # fault: chunk 2 OOMs
        except BaseException as e:                   # D-33/D-46: post-open
            if fd is not None:
                try:
                    os.remove(path)
                except OSError:
                    pass
            if isinstance(e, MemoryError) or isinstance(e, OOM_mid_write):
                # E-MEM write-phase form (D-44/§6.3)
                return 1, f"csv2json: error: out of memory writing {path}"
            raise

    good = b'{"prior":"good-bytes"}'
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        with open(out, "wb") as f:
            f.write(good)
        code, msg = write_output_chunked(out, '[{"id":"1","name":"x"}]')
        gone = not os.path.exists(out)
        form_accepted_by_tc16 = msg.startswith(
            "csv2json: error: out of memory writing ")
        check("P2 write-phase (post-open) E-MEM form removes pre-existing "
              "output -> T-C16 byte-identical assertion FAILS for this "
              "conforming outcome",
              code == 1 and form_accepted_by_tc16 and gone,
              f"code={code} msg={msg!r} gone={gone}")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # contrast: the encode-phase (pre-open) form DOES preserve bytes —
    # this is the only form T-C16's byte-identity claim is true for.
    class BoomStr(str):
        def encode(self, *a, **k):
            raise MemoryError()          # fault at the encode step

    def write_output_encode_oom(path, document):
        try:
            document.encode("utf-8")     # (1) D-43 encode first
        except MemoryError:
            return 1, f"csv2json: error: out of memory writing {path}"

    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        with open(out, "wb") as f:
            f.write(good)
        code, msg = write_output_encode_oom(out, BoomStr('[{"id":"1"}]'))
        survived = open(out, "rb").read() == good
        check("P2b encode-phase (pre-open) form preserves prior bytes "
              "(the claim is form-DEPENDENT)",
              code == 1 and survived and
              msg.startswith("csv2json: error: out of memory writing "))
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- P3 (F-03)
def p3():
    """input==output: mid-write failure's compensation deletes the INPUT."""
    class EIO_mid_write(Exception):
        pass

    d = tempfile.mkdtemp()
    try:
        path = os.path.join(d, "data.csv")   # SAME path for input & output
        csv_bytes = b'id,name\n1,x\n2,y\n'
        with open(path, "wb") as f:
            f.write(csv_bytes)

        # pipeline per §2.1: read_raw completes BEFORE the write stage
        data = open(path, "rb").read()               # S1 (input in memory)
        text = data.decode("utf-8")                  # S2
        rows = [{"id": "1", "name": "x"}, {"id": "2", "name": "y"}]
        import json
        document = json.dumps(rows, ensure_ascii=False,
                              separators=(",", ":")) + "\n"   # S4

        # S5 per §4.5: encode -> open -> write (fault) -> compensation
        payload = document.encode("utf-8")
        fd = None
        msg = None
        try:
            fd = open(path, "wb")
            raise EIO_mid_write()          # fault position: mid-write EIO
        except BaseException:
            if fd is not None:
                try:
                    os.remove(path)
                except OSError:
                    pass
            msg = f"csv2json: error: cannot write {path}: Input/output error"

        input_destroyed = not os.path.exists(path)
        check("P3 input==output mid-write failure DELETES the user's input "
              "(pinned mechanism; case unrecorded in spec)",
              msg.startswith("csv2json: error: cannot write ") and
              input_destroyed,
              f"msg={msg!r} input_destroyed={input_destroyed}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- P4 (F-05)
def p4():
    """Option-looking 2nd-arg divergence between sanctioned dispatches."""
    d = tempfile.mkdtemp()
    try:
        # manual dispatch (the pinned shape, §4.1/D-41): argc==2 -> paths
        argv = ["-h", os.path.join(d, "out.json")]
        if len(argv) == 2:
            try:
                open(argv[0], "rb").read()
                manual = "unexpected-success"
            except OSError as e:
                manual = (1, f"csv2json: error: cannot read {argv[0]}: "
                             f"{e.strerror}")
        # argparse default on the same argv: -h is built-in help -> exit 0
        ap = os.path.join(d, "ap.py")
        with open(ap, "w") as f:
            f.write("import argparse\n"
                    "p = argparse.ArgumentParser()\n"
                    "p.add_argument('input'); p.add_argument('output')\n"
                    "p.parse_args()\n")
        r = subprocess.run([sys.executable, ap, "-h", "out.json"],
                           capture_output=True, text=True)
        argparse_exit0_help = r.returncode == 0 and "help" in r.stdout.lower()
        check("P4 `-h out.json`: manual shape -> E-READ exit 1; argparse "
              "default -> help + exit 0 (sanctioned shapes diverge; the "
              "§4.1 override clause names no winner for option-looking "
              "positionals)",
              manual[0] == 1 and
              manual[1].startswith("csv2json: error: cannot read -h:") and
              argparse_exit0_help,
              f"manual={manual} argparse_rc={r.returncode}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- P5 (text)
def p5():
    raw = open(SPEC, encoding="utf-8").read()
    text = " ".join(raw.split())   # normalize line-wraps
    check("P5a §4.5 reference-shape finally snippet present",
          "finally:" in text and "if fd is not None: remove(path)" in text)
    check("P5b T-C16 claims byte-identical + form-independent",
          "byte-identical after the failed run" in text and
          "this pre-existing-output variant is form-independent" in text)
    check("P5c §7.1 taxonomy: 'no failure at a phase boundary can truncate "
          "or delete a pre-existing target' present",
          "no failure at a phase boundary can truncate or delete a "
          "pre-existing target" in text)
    check("P5d S-14(e) pins mid-write MemoryError removal",
          "the partial file is removed" in text)
    check("P5e T-C2 has skip-as-root, T-C8 read-only sub-case does not",
          "(skip as root)" in text and
          "pre-existing READ-ONLY target (mode 444)" in text and
          "read-only target (mode 444) (skip as root)" not in text)
    check("P5f §7.1 E-MEM verification: 'prior bytes survive' present",
          "pre-existing-output case asserts prior bytes survive" in text)
    check("P5g QC-2 Verification repeats T-C16 byte-identical claim",
          "RLIMIT_AS variant with a pre-existing output asserted "
          "byte-identical" in text)


if __name__ == "__main__":
    p1(); p2(); p3(); p4(); p5()
    print(f"TOTAL FAILURES: {len(fails)}" + (f" -> {fails}" if fails else ""))
    sys.exit(1 if fails else 0)

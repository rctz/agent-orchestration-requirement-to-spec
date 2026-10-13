#!/usr/bin/env python3
"""appendix/39b — adversarial-early cycle 9 live probes (spec/09-spec-v9.md).

Targets:
  P1  D-51 double-SIGINT inside the §4.5 compensation arm (F-01)
  P1c control: single KI -> removed (reproduces appendix/36 P1)
  P2  KI raised BY open() (FIFO, live) + interrupted-open-after-truncate
      mechanism demo (F-02)
  P3  /dev/stdout and /dev/stderr as output path on a conforming build (F-03)
  P4  stderr encoding vs verbatim interpolation under C locale (F-04)
  P5  mechanical: §11 sentence names D-01..D-52; argparse -h control (D-52)
"""
import io, json, os, signal, subprocess, sys, tempfile, textwrap

SPEC = "spec/09-spec-v9.md"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))


# ---------------------------------------------------------------- P1 / P1c
# write_output implemented EXACTLY per the §4.5 reference shape, with two
# legal CPython interrupt points made injectable: inside fd.write (the
# ordinary D-51 window) and inside fd.close as called by the FAILURE ARM
# (a second SIGINT landing mid-compensation — KI is raisable at ANY
# bytecode boundary / from within close, and the arm catches only OSError).
def write_output_refshape(path, document, ki_in_write=False, ki_close_call=None,
                          ki_after_truncate=False):
    payload = document.encode("utf-8")          # D-43: encode before open
    remove_ran = []

    class KIFile:
        def __init__(self, real):
            self._real, self._closes = real, 0

        def write(self, b):
            if ki_in_write:
                self._real.write(b[: len(b) // 2])   # half lands, then Ctrl-C
                raise KeyboardInterrupt
            return self._real.write(b)

        def flush(self):
            return self._real.flush()

        def close(self):
            self._closes += 1
            if ki_close_call == self._closes:
                raise KeyboardInterrupt             # 2nd SIGINT, inside the arm
            return self._real.close()

    # Simulates "kernel applied O_CREAT|O_TRUNC, SIGINT raised before the
    # open call's result was bound to fd" — the bytecode-gap window every
    # CPython eval loop has between CALL and STORE_FAST; P2a proves live
    # that open() itself raises KI (FIFO + SIGINT).
    def open_shim(p, mode):
        if ki_after_truncate:
            fdno = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.close(fdno)                     # truncation is already durable
            raise KeyboardInterrupt            # delivered before binding
        return open(p, mode)

    fd = None
    try:
        fd = open_shim(path, "wb") if ki_after_truncate else KIFile(open(path, "wb"))
        fd.write(payload)
        fd.flush()
        fd.close()
        fd = None
    except BaseException:
        if fd is not None:
            try:
                fd.close()
            except OSError:
                pass
            fd = None
            try:
                os.remove(path)
                remove_ran.append(True)
            except OSError:
                pass
        raise
    return remove_ran


def p1():
    doc = json.dumps([{"id": str(i), "name": "x" * 40} for i in range(50)],
                     ensure_ascii=False, separators=(",", ":")) + "\n"
    half = doc.encode("utf-8")[: len(doc.encode("utf-8")) // 2]
    with tempfile.TemporaryDirectory() as d:
        # control: single KI in write -> arm completes, target removed (D-51)
        p = os.path.join(d, "ctrl.json")
        open(p, "wb").write(b"PRIOR-GOOD")
        try:
            write_output_refshape(p, doc, ki_in_write=True)
        except KeyboardInterrupt:
            pass
        check("P1c single-KI: partial target REMOVED (D-51 holds)",
              not os.path.exists(p))
        # attack: second KI lands inside the arm's fd.close()
        p = os.path.join(d, "atk.json")
        open(p, "wb").write(b"PRIOR-GOOD")
        try:
            r = write_output_refshape(p, doc, ki_in_write=True, ki_close_call=1)
            raised = False
        except KeyboardInterrupt:
            raised, r = True, []
        check("P1a double-SIGINT: KI propagates from the arm", raised)
        check("P1b double-SIGINT: os.remove NEVER ran; partial file SURVIVES "
              "with half the JSON bytes (QC-2/§6.4 'never leaves a partial "
              "target' falsified)",
              os.path.exists(p) and open(p, "rb").read() == half,
              "surviving bytes=%d of %d" % (os.path.getsize(p), len(doc)))


# ---------------------------------------------------------------- P2
def p2():
    with tempfile.TemporaryDirectory() as d:
        fifo = os.path.join(d, "blk.fifo")
        os.mkfifo(fifo)
        child = textwrap.dedent("""
            import sys
            try:
                fd = open(%r, "wb")   # blocks: FIFO, no reader yet
                print("OPENED", flush=True)
            except KeyboardInterrupt:
                print("KI-FROM-OPEN", flush=True)
        """ % fifo)
        proc = subprocess.Popen([sys.executable, "-c", child],
                                stdout=subprocess.PIPE)
        try:
            import time
            time.sleep(0.6)            # let the child block in open()
            proc.send_signal(signal.SIGINT)
            out = proc.communicate(timeout=10)[0].decode()
        finally:
            if proc.poll() is None:
                proc.kill()
        check("P2a live: SIGINT while blocked in open() makes open() itself "
              "raise KeyboardInterrupt (fd never bound)", "KI-FROM-OPEN" in out,
              out.strip())
        # mechanism demo: open syscall completed (O_CREAT|O_TRUNC applied),
        # KI delivered before open returned -> reference shape sees fd=None,
        # no compensation, pre-existing prior-good target left at 0 bytes.
        tgt = os.path.join(d, "prior.json")
        open(tgt, "wb").write(b"PRIOR-GOOD-DOCUMENT")
        try:
            write_output_refshape(tgt, "[]\n", ki_after_truncate=True)
            raised = False
        except KeyboardInterrupt:
            raised = True
        check("P2b interrupted-open-after-truncate: KI propagates, fd is None",
              raised)
        check("P2b prior good target DESTROYED to 0 bytes, no remove ran "
              "(QC-2 'no output file is created or truncated' falsified for "
              "the KI class it claims)",
              os.path.exists(tgt) and os.path.getsize(tgt) == 0)


def _touched(match, real_open, p, f, m):
    fdno = real_open(p, f, m)          # file created / truncated HERE
    os.close(fdno)
    if match:
        raise KeyboardInterrupt        # 'interrupted before open returned'
    return real_open(p, f, m)


# ---------------------------------------------------------------- P3
MINI_TOOL = textwrap.dedent("""
    import csv, io, json, sys, os
    def main(argv):
        if len(argv) != 2:
            print("csv2json: error: usage: csv2json.py <input.csv> <output.json>",
                  file=sys.stderr); return 1
        inp, out = argv
        try:
            data = open(inp, "rb").read()
        except OSError as e:
            print("csv2json: error: cannot read %s: %s" % (inp, e.strerror),
                  file=sys.stderr); return 1
        text = data.decode("utf-8")
        rows = list(csv.reader(io.StringIO(text, newline="")))
        header, recs = rows[0], rows[1:]
        document = json.dumps([dict(zip(header, r)) for r in recs],
                              ensure_ascii=False, separators=(",", ":")) + "\\n"
        fd = None
        try:
            fd = open(out, "wb"); fd.write(document.encode("utf-8"))
            fd.flush(); fd.close(); fd = None
        except BaseException:
            if fd is not None:
                try: fd.close()
                except OSError: pass
                fd = None
                try: os.remove(out)
                except OSError: pass
            raise
        return 0
    sys.exit(main(sys.argv[1:]))
""")


def p3():
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "in.csv")
        open(inp, "wb").write(b"id,name\n1,x\n")
        tool = os.path.join(d, "mini_csv2json.py")
        open(tool, "w").write(MINI_TOOL)
        r = subprocess.run([sys.executable, tool, inp, "/dev/stdout"],
                           capture_output=True)
        check("P3a output=/dev/stdout: exit 0", r.returncode == 0)
        check("P3a output=/dev/stdout: the JSON DOCUMENT is on stdout — "
              "NFR-004 letter 'stdout empty on every path' / §6.4 success row "
              "/ T-K3 falsified on a legal argv",
              r.stdout.startswith(b'[{"id":"1"'),
              repr(r.stdout[:40]))
        r2 = subprocess.run([sys.executable, tool, inp, "/dev/stderr"],
                            capture_output=True)
        check("P3b output=/dev/stderr: exit 0 with document on stderr — "
              "§6.4 'success | stderr empty' falsified",
              r2.returncode == 0 and r2.stderr.startswith(b'[{"id":"1"'))


# ---------------------------------------------------------------- P4
P4_CHILD = textwrap.dedent("""
    import sys
    name = "\u0e1b\u0e23\u0e30\u0e40\u0e17\u0e28\u0e44\u0e17\u0e22"  # Thai
    print("csv2json: error: in.csv line 1: duplicate header name '%s'" % name,
          file=sys.stderr)
""")


def p4():
    with tempfile.TemporaryDirectory() as d:
        script = os.path.join(d, "child.py")
        open(script, "w").write(P4_CHILD)
        thai = "ประเทศไทย".encode("utf-8")
        for label, env_extra in [
            ("utf8-locale", {}),
            ("c-locale-nocoerce", {"LC_ALL": "C", "LANG": "C",
                                   "PYTHONCOERCECLOCALE": "0"}),
            ("pyioencoding-ascii", {"PYTHONIOENCODING": "ascii:backslashreplace"}),
        ]:
            env = dict(os.environ, **env_extra)
            r = subprocess.run([sys.executable, script], capture_output=True,
                               env=env)
            verbatim = thai in r.stderr
            check("P4[%s] stderr carries the Thai name verbatim (UTF-8)" % label,
                  verbatim,
                  ("verbatim" if verbatim else "MANGLED: %r" % r.stderr[-60:]))


# ---------------------------------------------------------------- P5
def p5():
    txt = open(SPEC, encoding="utf-8").read()
    check("P5a §11 coverage sentence names D-01..D-52",
          "D-01..D-52 are all DECIDED" in txt)
    r = subprocess.run([sys.executable, "-c",
                        "import argparse,sys;"
                        "p=argparse.ArgumentParser(prog='csv2json.py');"
                        "p.parse_args(['-h'])"],
                       capture_output=True)
    check("P5b argparse control: bare '-h' prints help to STDOUT and exits 0 "
          "(D-52 retraction premise reproduced)",
          r.returncode == 0 and b"usage" in r.stdout and len(r.stdout) > 0,
          "rc=%d stdout=%dB" % (r.returncode, len(r.stdout)))


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
    p1(); p2(); p3(); p4(); p5()
    print("\nTOTAL PASS: %d / FAILURES: %d" % (len(PASS), len(FAIL)))
    sys.exit(1 if FAIL else 0)

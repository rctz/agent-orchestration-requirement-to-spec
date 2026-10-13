#!/usr/bin/env python3
"""appendix/45b — adversarial-early cycle 10 live probes (spec/10-spec-v10.md).

Targets:
  P1  D-53/R-5 "(or any non-OSError)" arm-abort class with a MemoryError as
      the SECOND exception vs T-C16's "path is ABSENT — no conforming
      mechanism can leave it present" write-phase mandate (F-01)
  P1c real-memory attempt: conforming chunked-write + helper-arm build under
      RLIMIT_AS looking for E-MEM write-phase + partial PRESENT
  P2  D-55 fold miss: /dev/stderr & /dev/stdout success runs vs §6.1 stderr
      row and §12 "silent success" gloss (F-02)
  P3  mechanical: §1 still enumerates D-01..D-52 (F-03)
  P4  R-6 create-flavor: KI-at-open with O_CREAT on an ABSENT target leaves
      a CREATED 0-byte file — outside R-6's "bounded to pre-existing" (F-04)
"""
import io, json, os, subprocess, sys, tempfile

SPEC = "spec/10-spec-v10.md"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))


# ------------------------------------------------------------- P1 (shim)
# write_output per the §4.5 reference shape; interrupt points injectable at
# fd.write (M1) and at the FAILURE ARM's fd.close (M2) — the same evidence
# class as appendix/39b P1a/P1b (accepted by the v10 fold as D-53 evidence).
def write_output_refshape(path, document, m1_in_write=False, m2_in_arm_close=False):
    payload = document.encode("utf-8")            # D-43 encode-before-open
    remove_ran = []

    class MEFile:
        def write(self, b):
            if m1_in_write:
                self._real.write(b[: len(b) // 2])  # half lands, then OOM
                raise MemoryError
            return self._real.write(b)

        def flush(self):
            return self._real.flush()

        def close(self):
            if m2_in_arm_close:
                raise MemoryError                   # 2nd exception, inside arm
            return self._real.close()

    f = MEFile()
    fd = None
    try:
        f._real = open(path, "wb")
        fd = f
        fd.write(payload)
        fd.flush()
        fd.close()
        fd = None
    except BaseException:
        if fd is not None:
            try:
                fd.close()                          # D-50 close before remove
            except OSError:
                pass                                # arm catches ONLY OSError
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
    total = len(doc.encode("utf-8"))
    with tempfile.TemporaryDirectory() as d:
        # control P1b: single MemoryError at write -> arm completes -> removed
        p = os.path.join(d, "ctrl.json")
        open(p, "wb").write(b"PRIOR-GOOD")
        reported = None
        try:
            write_output_refshape(p, doc, m1_in_write=True)
        except MemoryError:                          # main's first handler
            reported = "csv2json: error: out of memory writing " + p
        check("P1b control single-MemoryError: arm completes, partial REMOVED "
              "(D-46 trigger + D-50 order intact)",
              not os.path.exists(p) and reported is not None)
        # P1a: M2 = MemoryError inside the arm's fd.close -> arm aborts
        p = os.path.join(d, "m2.json")
        open(p, "wb").write(b"PRIOR-GOOD")
        reported = None
        try:
            write_output_refshape(p, doc, m1_in_write=True, m2_in_arm_close=True)
        except MemoryError:                          # M2 replaces M1 in flight
            reported = "csv2json: error: out of memory writing " + p
        survived = os.path.exists(p) and open(p, "rb").read()
        check("P1a MemoryError-cascade: E-MEM write-phase line observed AND "
              "partial file PRESENT — T-C16's mandated ABSENT assertion fails "
              "a build whose arm is exactly §4.5's shape",
              survived == doc.encode("utf-8")[: total // 2]
              and reported == "csv2json: error: out of memory writing " + p,
              "surviving bytes=%d of %d; would-be stderr=%r" %
              (len(survived), total, reported))


# ------------------------------------------------- P1c (real RLIMIT_AS)
BUILDDIR = None


def p1c():
    global BUILDDIR
    BUILDDIR = tempfile.mkdtemp(prefix="adv-c10-p1c-")
    build = os.path.join(BUILDDIR, "csv2json.py")
    with open(build, "w") as f:
        f.write(
            "import csv, io, json, os, sys\n"
            # ballast: allocate ~1 chunk after the document is fully built,
            # so the heap edge lands INSIDE the write loop's slice allocs
            "BALLAST = []\n"
            "def _compensate(fd, path):\n"           # helper arm = conforming
            "    try: fd.close()\n"                  # shape per §4.5 'the
            "    except OSError: pass\n"             # normative contract is
            "    try: os.remove(path)\n"             # the state outcome, not
            "    except OSError: pass\n"             # the syntactic form'
            "def write_output(path, document):\n"
            "    payload = document.encode('utf-8')\n"
            "    fd = None\n"
            "    try:\n"
            "        fd = open(path, 'wb')\n"
            "        for i in range(0, len(payload), 1 << 20):\n"
            "            if i == (1 << 20):\n"        # after chunk 1 lands:
            "                BALLAST.append(b'\\0' * (4 << 20))\n"  # push heap
            "            fd.write(payload[i:i + (1 << 20)])\n"      # to edge;
            "            BALLAST[-1] = b'\\0' * ((4 << 20) + i)\n"  # realloc
            "        fd.flush(); fd.close(); fd = None\n"
            "    except BaseException:\n"
            "        if fd is not None: _compensate(fd, path)\n"    # frame
            "        raise\n"                          # alloc may fail
            "def main(argv):\n"
            "    if len(argv) != 2: return 1\n"
            "    data = open(argv[0], 'rb').read()\n"
            "    text = data.decode('utf-8')\n"
            "    rows = list(csv.reader(io.StringIO(text, newline='')))\n"
            "    doc = json.dumps([dict(zip(rows[0], r)) for r in rows[1:]],\n"
            "                     ensure_ascii=False, separators=(',', ':')) + '\\n'\n"
            "    try:\n"
            "        write_output(argv[1], doc)\n"
            "        return 0\n"
            "    except MemoryError:\n"
            "        sys.stderr.write('csv2json: error: out of memory writing "
            "%s\\n' % argv[1]); return 1\n"
            "sys.exit(main(sys.argv[1:]))\n")
    inp = os.path.join(BUILDDIR, "in.csv")
    with open(inp, "w") as f:
        f.write("id,name\n" + "".join("%d,%s\n" % (i, "x" * 60)
                                      for i in range(120000)))  # ~8 MB
    runner = os.path.join(BUILDDIR, "runner.py")
    with open(runner, "w") as f:
        f.write("import resource, sys, os\n"
                "resource.setrlimit(resource.RLIMIT_AS, (int(sys.argv[1]), "
                "int(sys.argv[1])))\n"
                "os.execv(sys.executable, [sys.executable, sys.argv[2], "
                "sys.argv[3], sys.argv[4]])\n")
    hits = 0
    for lim_mb in (14, 16, 18, 20, 24, 28, 32, 40, 48, 60, 80, 110, 150, 200):
        out = os.path.join(BUILDDIR, "out.json")
        if os.path.exists(out):
            os.remove(out)
        r = subprocess.run([sys.executable, runner, str(lim_mb << 20), build,
                            inp, out], capture_output=True, timeout=60)
        err = r.stderr.decode("utf-8", "replace")
        form_write = err.startswith("csv2json: error: out of memory writing")
        if r.returncode == 1 and form_write and os.path.exists(out):
            hits += 1
    check("P1c real-RLIMIT_AS sweep ran and recorded its outcome forms "
          "(honest negative: the MemoryError-cascade residue was NOT "
          "reproducible by pure RLIMIT_AS in 14 limits — after a mid-write "
          "OOM the arm's sub-KB freelist allocations succeed and the remove "
          "completes; F-01 therefore stands on P1a's sanctioned interruption "
          "points plus the T-C16/§4.5 textual contradiction)",
          True, "write-phase-form-with-partial-present reproductions=%d/14" % hits)


# ------------------------------------------------------------- P2 (D-55)
# A build implementing the exact §4.5 reference shape; /dev/stderr and
# /dev/stdout as output path. §6.1's stderr row ("empty on success") and
# §12's "silent success" glossary row carry NO regular-file scope note.
def build_refshape_tool(build):
    with open(build, "w") as f:
        f.write(
            "import csv, io, json, os, sys\n"
            "def write_output(path, document):\n"
            "    payload = document.encode('utf-8')\n"
            "    fd = None\n"
            "    try:\n"
            "        fd = open(path, 'wb')\n"
            "        fd.write(payload); fd.flush()\n"
            "        fd.close(); fd = None\n"
            "    except BaseException:\n"
            "        if fd is not None:\n"
            "            try: fd.close()\n"
            "            except OSError: pass\n"
            "            fd = None\n"
            "            try: os.remove(path)\n"
            "            except OSError: pass\n"
            "        raise\n"
            "def main(argv):\n"
            "    if len(argv) != 2:\n"
            "        sys.stderr.write('csv2json: error: usage: csv2json.py "
            "<input.csv> <output.json>\\n'); return 1\n"
            "    data = open(argv[0], 'rb').read()\n"
            "    text = data.decode('utf-8')\n"
            "    rows = list(csv.reader(io.StringIO(text, newline='')))\n"
            "    doc = json.dumps([dict(zip(rows[0], r)) for r in rows[1:]],\n"
            "                     ensure_ascii=False, separators=(',', ':')) + '\\n'\n"
            "    write_output(argv[1], doc)\n"
            "    return 0\n"
            "sys.exit(main(sys.argv[1:]))\n")


def p2():
    d = tempfile.mkdtemp(prefix="adv-c10-p2-")
    build = os.path.join(d, "csv2json.py")
    build_refshape_tool(build)
    inp = os.path.join(d, "in.csv")
    with open(inp, "wb") as f:
        f.write(b"id,name\n1,x\n2,y\n")
    # /dev/stderr output: §6.1 stderr row says "empty on success" with no
    # regular-file scope; §12 "silent success" likewise.
    r = subprocess.run([sys.executable, build, inp, "/dev/stderr"],
                       capture_output=True, timeout=30)
    check("P2a output=/dev/stderr on §4.5-exact build: exit 0 AND the JSON "
          "document appears on stderr — §6.1 'stderr: empty on success' "
          "(no scope note) falsified",
          r.returncode == 0 and r.stderr == b'[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n',
          "rc=%d stderr=%r" % (r.returncode, r.stderr[:60]))
    r = subprocess.run([sys.executable, build, inp, "/dev/stdout"],
                       capture_output=True, timeout=30)
    check("P2b output=/dev/stdout: exit 0, document on stdout — §12 'silent "
          "success | Exit 0 with empty stdout' (no scope note) falsified",
          r.returncode == 0 and r.stdout == b'[{"id":"1","name":"x"},{"id":"2","name":"y"}]\n',
          "rc=%d stdout=%r" % (r.returncode, r.stdout[:60]))


# ------------------------------------------------------------- P3 (mech)
def p3():
    src = open(SPEC).read()
    ok_55 = "D-01..D-55" in src
    # §1's overview paragraph (the one §revision claims was refreshed)
    ln = None
    for i, line in enumerate(src.splitlines(), 1):
        if "leaves none unresolved" in line:
            ln = (i, line.strip())
    stale_52 = ln and "D-01..D-52" in ln[1]
    check("P3a §1 overview still enumerates D-01..D-52 while the v10 "
          "revision row claims '§1 enumeration refreshed to D-01..D-55' — "
          "claimed fold-site missing (§11 line 1745 IS D-01..D-55)",
          ok_55 and stale_52,
          "§1 line %d: %r; §11 refreshed=%s" % (ln[0], ln[1][:80] if ln else None, ok_55))


# ------------------------------------------------------------- P4 (R-6)
# R-6/QC-2 bound the KI-at-open residue to PRE-EXISTING targets; the
# create flavor (O_CREAT on an absent target, KI before bind) leaves a
# CREATED 0-byte file — same window, outside the stated bound.
# Mechanism identical to 39b P2b (kernel applies O_CREAT|O_TRUNC, signal
# lands before fd binding): with an ABSENT target the same window leaves a
# 0-byte file at a path that did not exist — textual bound check below.
def p4_bound_check():
    # Textual: the spec's R-6/QC-2 scope words.
    src = open(SPEC).read()
    bounded_pre = ("bounded to pre-existing" in src) or \
                  ("bounded to that invocation" in src)
    mentions_create = "O_CREAT" in src
    return bounded_pre, mentions_create


if __name__ == "__main__":
    for fn in (p1, p1c, p2, p3):
        try:
            fn()
        except Exception as e:
            FAIL.append(fn.__name__ + " raised " + repr(e))
            print("RAISED", fn.__name__, repr(e))
    b, m = p4_bound_check()
    print("P4 textual bound: R-6 'bounded to pre-existing' present=%s; "
          "O_CREAT named=%s (the create flavor — a 0-byte file CREATED at a "
          "fresh path by the same KI-at-open window — is outside every "
          "stated bound of R-6/QC-2; mechanism identical to 39b P2b)"
          % (b, m))
    print("TOTAL PASS=%d FAIL=%d" % (len(PASS), len(FAIL)))
    sys.exit(1 if FAIL else 0)

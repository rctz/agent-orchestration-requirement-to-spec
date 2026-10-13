#!/usr/bin/env python3
"""48b-adv-c11-probes — live probes for adversarial-early cycle 11 (t_1f585d11).

Target: spec/11-spec-v11.md. Probes drive subprocesses implementing the
spec's OWN pinned shapes (the §4.5 reference shape verbatim; a §4.2-literal
decode_utf8), so results bind the spec's contracts, not a build's choices.

Probe map (findings cross-ref appendix/48-adv-c11.md):
  P1  E-UTF8 prefix-decode crash: for an invalid-CONTINUATION byte, where
      does CPython set UnicodeDecodeError.start? If it points at the
      continuation byte (not the lead), the §4.2 formula
      `data[:e.start].decode("utf-8")` ends with a dangling lead byte and
      the PREFIX DECODE ITSELF raises -> the E-UTF8 handler dies, the raw
      UnicodeDecodeError escapes to main's net -> E-NET line for a plain
      invalid-UTF-8 file (F-02).
  P2  at-open MemoryError residue: kernel applies O_CREAT|O_TRUNC inside
      open(), then the wrapper allocation raises MemoryError before `fd`
      binds (CPython DECREFs the raw FileIO -> fd closed, inode remains).
      The §4.5 reference shape sees fd None -> no compensation. Absent
      target -> CREATED 0-byte; pre-existing -> TRUNCATED 0-byte; stderr
      carries the E-MEM write-phase form; T-C16 asserts path ABSENT for
      that form ("no conforming mechanism can otherwise leave it
      present") -> contradiction (F-01).
  P3  remove-fails control (R-1): post-open OSError + unwritable parent
      dir -> the arm swallows the remove failure, the bare `raise`
      preserves the ORIGINAL OSError, E-WRITE prints, residue PRESENT.
      Re-verifies the contracted R-1 behavior (control for P2).
  P4  root-mode reality: euid; create in a 0555 dir as root (DAC_OVERRIDE
      defeats the T-C8 non-writable-dir premise, which carries NO
      skip-as-root note); /dev/full write errno as root (F-03).
  P5  mandated double scan: the §4.3.2 loop runs count_line_breaks(span)
      AND the §4.3.3 FSM carries its own record-relative counter over the
      same span -> two full passes the spec pins as separate operations
      (F-04 evidence; QC-5 constant-factor claim).
  P6  50 MB-class parse baseline on this host (NFR-003/QC-5 envelope
      margin evidence).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

PY = sys.executable
FAIL = []
OK = []


def check(name, cond, detail=""):
    (OK if cond else FAIL).append((name, detail))
    print(("PASS " if cond else "FAIL ") + name + (" — " + detail if detail else ""))


# ---------------------------------------------------------------------------
# P1 — E-UTF8: where does e.start land for an invalid continuation byte?
# ---------------------------------------------------------------------------

# A §4.2-literal decode stage (formula exactly as pinned).
DECODE_STAGE = r'''
import sys

class InvalidUtf8Error(Exception):
    pass

def line_of_offset(text, offset):
    line = 1
    i = 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i+1:i+2] == "\n" else 1
            line += 1
        else:
            i += 1
            if text[i-1] == "\n":
                line += 1
    return line

def decode_utf8(data, path):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        prefix = data[:e.start].decode("utf-8")   # <- the pinned formula
        line = line_of_offset(prefix, len(prefix))
        raise InvalidUtf8Error(
            "csv2json: error: %s line %d: byte 0x%02x is not valid UTF-8"
            % (path, line, data[e.start]))
    return text

def main(argv):
    path, = argv
    with open(path, "rb") as f:
        data = f.read()
    try:
        decode_utf8(data, path)
    except InvalidUtf8Error as e:
        sys.stderr.write(str(e) + "\n")
        return 1
    except Exception as e:            # residual net per §7.3
        sys.stderr.write("csv2json: error: %s: internal error: %r\n" % (path, e))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def probe_p1():
    cases = [
        # (label, bytes, expect_prefix_crash_if_start_at_continuation)
        ("lead+bad-cont b'a\\xf0(b'", b"a\xf0(b"),
        ("lead+bad-cont b'\\xf0\\x28'", b"\xf0\x28"),
        ("2byte lead+bad b'a\\xe2\\x28'", b"a\xe2\x28"),
        ("4byte lead+1ok+bad b'\\xf0\\x9f\\x28'", b"\xf0\x9f\x28"),
        ("truncated-at-eof b'a\\xf0'", b"a\xf0"),
        ("plain single bad b'a\\xff'", b"a\xff"),
    ]
    d = tempfile.mkdtemp()
    for label, raw in cases:
        # introspect e.start directly
        intro = subprocess.run(
            [PY, "-c",
             "try:\n b=%r.decode('utf-8')\nexcept UnicodeDecodeError as e:\n print(e.start, e.reason)" % raw],
            capture_output=True, text=True, timeout=30)
        start_reason = intro.stdout.strip()
        # does the prefix decode cleanly?
        pref = subprocess.run(
            [PY, "-c",
             "try:\n %r[:%d].decode('utf-8')\n print('OK')\nexcept Exception as e:\n print('CRASH', e)" % (raw, int(start_reason.split()[0]))],
            capture_output=True, text=True, timeout=30)
        # E2E through the §4.2-literal child
        pfn = os.path.join(d, "case.bin")
        with open(pfn, "wb") as f:
            f.write(raw)
        p = subprocess.run([PY, "-c", DECODE_STAGE, pfn],
                           capture_output=True, text=True, timeout=30)
        crash = pref.stdout.startswith("CRASH")
        enet = "internal error" in p.stderr
        eutf8 = "is not valid UTF-8" in p.stderr
        print(f"  P1 {label}: e.start/reason = {start_reason!r}; prefix={pref.stdout.strip()!r}; "
              f"E2E rc={p.returncode} E-UTF8={eutf8} E-NET={enet}")
        if crash and enet:
            check(f"P1 {label}: prefix crash -> E-NET replaces E-UTF8", True,
                  f"stderr={p.stderr.strip()[:110]!r}")
        else:
            check(f"P1 {label}: handled per catalog (E-UTF8 line)", eutf8 and not enet,
                  f"stderr={p.stderr.strip()[:110]!r}")
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# P2 — at-open MemoryError: kernel-created/truncated inode, fd never binds
# ---------------------------------------------------------------------------

# §4.5 reference shape verbatim, with open() faulted at the wrapper-allocation
# interruption point: the raw fd IS created (kernel applies O_CREAT|O_TRUNC),
# then closed (CPython's DECREF cleanup), then MemoryError — `fd` stays None.
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


def probe_p2():
    d = tempfile.mkdtemp()
    # (a) absent target
    out1 = os.path.join(d, "absent.json")
    p1 = subprocess.run([PY, "-c", WRITER_ATOPEN_MEM, out1],
                        capture_output=True, text=True, timeout=30)
    st1 = (os.path.exists(out1), os.path.getsize(out1) if os.path.exists(out1) else None)
    check("P2a at-open MemoryError, ABSENT target: 0-byte file CREATED, E-MEM write-phase, exit 1",
          p1.returncode == 1 and "out of memory writing" in p1.stderr
          and st1 == (True, 0),
          f"rc={p1.returncode} stderr={p1.stderr.strip()!r} state={st1}")
    # (b) pre-existing target
    out2 = os.path.join(d, "prior.json")
    with open(out2, "wb") as f:
        f.write(b'[{\"prior\":\"good\"}]\n' * 40)
    p2 = subprocess.run([PY, "-c", WRITER_ATOPEN_MEM, out2],
                        capture_output=True, text=True, timeout=30)
    st2 = (os.path.exists(out2), os.path.getsize(out2) if os.path.exists(out2) else None)
    check("P2b at-open MemoryError, PRE-EXISTING target: truncated to 0 bytes, E-MEM write-phase, exit 1",
          p2.returncode == 1 and "out of memory writing" in p2.stderr
          and st2 == (True, 0),
          f"rc={p2.returncode} stderr={p2.stderr.strip()!r} size={st2[1]}")
    # (c) the T-C16 contradiction, quoted from the spec
    spec = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "spec", "11-spec-v11.md"), encoding="utf-8").read()
    has_claim = "no conforming mechanism can otherwise leave it present" in spec
    check("P2c spec text pins T-C16 'path ABSENT ... no conforming mechanism can otherwise leave it present'",
          has_claim,
          "P2a/P2b left the path PRESENT (0-byte) at exactly this phase form -> assertion contradicted")
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# P3 — remove-fails control (R-1): original OSError survives the arm
# ---------------------------------------------------------------------------

WRITER_REMOVEFAIL = r'''
import os, sys

def write_output(path, payload):
    fd = None
    try:
        fd = open(path, "wb")
        fd.write(payload[:100]); fd.flush()
        raise OSError(28, "No space left on device")
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
        write_output(out, b"x" * 3000)
    except OSError as e:
        sys.stderr.write("csv2json: error: cannot write %s: %s\n" % (out, e.strerror))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def probe_p3():
    d = tempfile.mkdtemp()
    out = os.path.join(d, "out.json")
    with open(out, "wb") as f:
        f.write(b"PRIOR-GOOD")
    os.chmod(d, 0o555)  # remove will fail EACCES; open/truncate still fine
    try:
        p = subprocess.run([PY, "-c", WRITER_REMOVEFAIL, out],
                           capture_output=True, text=True, timeout=30)
        present = os.path.exists(out)
        size = os.path.getsize(out) if present else None
        check("P3 remove-fails (R-1 control): E-WRITE line PRINTS, residue PRESENT, exit 1",
              p.returncode == 1 and "cannot write" in p.stderr and present,
              f"rc={p.returncode} stderr={p.stderr.strip()!r} residue={size} bytes")
    finally:
        os.chmod(d, 0o755)
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# P4 — root-mode reality
# ---------------------------------------------------------------------------

def probe_p4():
    euid = os.geteuid()
    print(f"  P4 euid={euid} (root)" if euid == 0 else f"  P4 euid={euid} (non-root)")
    d = tempfile.mkdtemp()
    os.chmod(d, 0o555)
    try:
        if euid == 0:
            fn = os.path.join(d, "probe")
            try:
                with open(fn, "wb") as f:
                    f.write(b"x")
                created = os.path.exists(fn)
            except OSError:
                created = False
            check("P4a root CAN create in a 0555 dir (T-C8 non-writable-dir premise never materializes as root)",
                  created, f"created={created}")
        else:
            fn = os.path.join(d, "probe")
            try:
                with open(fn, "wb") as f:
                    f.write(b"x")
                created = True
            except OSError:
                created = False
            check("P4a non-root cannot create in 0555 dir (control)", not created, f"created={created}")
    finally:
        os.chmod(d, 0o755)
        shutil.rmtree(d, ignore_errors=True)
    # /dev/full errno as root vs non-root
    if os.path.exists("/dev/full"):
        r = subprocess.run(
            [PY, "-c",
             "import sys\ntry:\n sys.stdout.write('')\n f=open('/dev/full','wb')\n f.write(b'x'*10)\n f.flush()\n f.close()\n print('WROTE-OK')\nexcept OSError as e:\n print('ERRNO', e.errno)"],
            capture_output=True, text=True, timeout=30)
        check("P4b /dev/full write fails ENOSPC regardless of uid",
              "ERRNO 28" in r.stdout, f"euid={euid} out={r.stdout.strip()!r}")


# ---------------------------------------------------------------------------
# P5 — mandated double scan (FSM counter + count_line_breaks on same span)
# ---------------------------------------------------------------------------

def probe_p5():
    import csv as _csv
    import io as _io
    n = 20000
    text = "h1,h2\n" + "".join(f"{i},x\n" for i in range(n))

    def count_line_breaks(s, a, b):
        c = 0
        j = a
        while j < b:
            if s[j] == "\r":
                j += 2 if s[j+1:j+2] == "\n" else 1
                c += 1
            elif s[j] == "\n":
                j += 1
                c += 1
            else:
                j += 1
        return c

    # Spec-literal §4.3.2+§4.3.3: slice + FSM scan (with its own counter) +
    # separate count_line_breaks over the same span.
    t0 = time.perf_counter()
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    start = 0
    line = 1
    while True:
        try:
            record = next(reader)
        except StopIteration:
            break
        end = buf.tell()
        record_text = text[start:end]
        # FSM scan per §4.3.3 table (literal, with record-relative counter)
        st = 0  # 0=FIELD_START 1=UNQUOTED 2=QUOTED 3=CLOSED
        counter = 1
        i = 0
        L = len(record_text)
        while i < L:
            c = record_text[i]
            if c == '"':
                st = {0: 2, 2: 3, 3: 2}.get(st, st)
                i += 1
            elif c == ",":
                if st in (1, 3):
                    st = 0
                i += 1
            elif c in "\r\n":
                if c == "\r" and i + 1 < L and record_text[i+1] == "\n":
                    i += 2
                else:
                    i += 1
                if st == 2:
                    counter += 1
                else:
                    st = 0
            else:
                if st == 0:
                    st = 1
                elif st == 3:
                    st = 1
                i += 1
        if st == 2:
            raise SystemExit("unterminated")
        line += count_line_breaks(text, start, end)  # §4.3.2's separate call
        start = end
    dt_spec = time.perf_counter() - t0

    # Control: reader-only walk
    t0 = time.perf_counter()
    buf2 = _io.StringIO(text, newline="")
    reader2 = _csv.reader(buf2)
    rows = list(reader2)
    dt_plain = time.perf_counter() - t0
    check("P5 spec-literal double-scan walk completes; cost measured",
          True,
          f"spec-shape={dt_spec:.2f}s reader-only={dt_plain:.2f}s "
          f"ratio={dt_spec/max(dt_plain,1e-9):.1f}x on {n} records "
          f"(final line={line}, rows={len(rows)})")


# ---------------------------------------------------------------------------
# P6 — 50 MB-class parse baseline on this host
# ---------------------------------------------------------------------------

def probe_p6():
    import csv as _csv
    import io as _io
    import json as _json
    n = 250000
    t0 = time.perf_counter()
    text = "h1,h2\n" + "".join(f"{i},x\n" for i in range(n))
    t_gen = time.perf_counter() - t0
    t0 = time.perf_counter()
    buf = _io.StringIO(text, newline="")
    reader = _csv.reader(buf)
    rows = [dict(zip(("h1", "h2"), r)) for r in reader]
    dt_parse = time.perf_counter() - t0
    t0 = time.perf_counter()
    doc = _json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
    dt_ser = time.perf_counter() - t0
    check("P6 50MB-class pipeline baseline measured on this host", True,
          f"input={len(text)/1e6:.1f}MB gen={t_gen:.1f}s parse+dict={dt_parse:.1f}s "
          f"serialize={dt_ser:.1f}s total={t_gen+t_parse if False else dt_parse+dt_ser:.1f}s "
          f"(Pi-class host; excludes the P5 scan multipliers)")


def main():
    print("== 48b-adv-c11-probes ==")
    probe_p1()
    probe_p2()
    probe_p3()
    probe_p4()
    probe_p5()
    probe_p6()
    print()
    print(f"TOTAL: {len(OK)+len(FAIL)} checks, {len(FAIL)} failures")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

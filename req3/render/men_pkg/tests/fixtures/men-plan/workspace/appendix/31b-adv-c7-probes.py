#!/usr/bin/env python3
"""appendix/31b-adv-c7-probes.py — adversarial-early cycle-7 live probes.

Target: spec/07-spec-v7.md (DRAFT). Five probe families:
  P1/P1c  SIGINT mid-write (writer blocked on a full FIFO): the §4.5
          except-BaseException reference shape REMOVES the target; an
          §7.1-faithful narrow (except Exception) wrap LEAVES it — the two
          sections contract opposite durable states for the same event.
  P2      output path /dev/stdout and /dev/stderr on a SUCCESSFUL run:
          §6.1/§6.4 "stdout/stderr empty on success" is observably false;
          no conforming behavior exists (the §6.3 catalog is closed — no
          refusal class).
  P3      ASCII stderr (LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0):
          a Thai-bearing E-DUP message crashes the REPORTING print with
          UnicodeEncodeError -> traceback — contra §4.1 "never a traceback"
          unless the QC-1-Assumptions "wrapped best-effort" print (specified
          nowhere in §4.1/§7.3) exists.
  P4      concurrent at-open failure vs a truncating writer: §6.3 E-WRITE's
          at-open note "the target is left byte-untouched" is observably
          false at B's report moment (0-byte target), while §4.5 row 9 / R-2
          disclaim concurrency.
  P5      BOM + lone-surrogate byte: E-UTF8 precedence sanity (boundary class).
"""
import os, subprocess, sys, tempfile, time

PY = sys.executable
REF_TOOL = r'''
import csv, io, json, os, sys
def write_output(path, document):
    payload = document.encode("utf-8")            # D-43 encode-before-open
    fd = None
    try:
        fd = open(path, "wb")                      # D-45 binary shape
        fd.write(payload); fd.flush()
        fd.close(); fd = None
    except __WRAPCLS__:
        if fd is not None:                         # D-46 successful-open guard
            try: os.remove(path)                   # D-33 best-effort
            except OSError: pass
        raise
def main(argv):
    if len(argv) != 2:
        sys.stderr.write("csv2json: error: usage: csv2json.py <input.csv> <output.json>\n"); return 1
    inp, outp = argv
    try:
        data = open(inp, "rb").read()
    except OSError as e:
        sys.stderr.write("csv2json: error: cannot read %s: %s\n" % (inp, e.strerror)); return 1
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        sys.stderr.write("csv2json: error: %s line ?: byte 0x%02x is not valid UTF-8\n" % (inp, data[e.start])); return 1
    if text.startswith("\ufeff"): text = text[1:]
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader)
    rows = [dict(zip(header, rec)) for rec in reader]
    doc = json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
    try:
        write_output(outp, doc)
    except MemoryError:
        sys.stderr.write("csv2json: error: out of memory writing %s\n" % outp); return 1
    except OSError as e:
        sys.stderr.write("csv2json: error: cannot write %s: %s\n" % (outp, e.strerror)); return 1
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''.replace("__WRAPCLS__", "BaseException")

NARROW_TOOL = REF_TOOL.replace("except BaseException:", "except Exception:")

WRITER_TMPL = r'''
import os, sys
path = sys.argv[1]
payload = b"[" + b'"x",' * 300000 + b'"x"]\n'      # ~1.8 MB > FIFO capacity
fd = None
try:
    fd = open(path, "wb")
    fd.write(payload); fd.flush()
    fd.close(); fd = None
except __WRAPCLS__:
    if fd is not None:
        try: os.remove(path)
        except OSError: pass
    raise
'''

A_CHILD = r'''
import os, sys, time
p = sys.argv[1]
fd = os.open(p, os.O_WRONLY | os.O_TRUNC)          # the truncating open
time.sleep(2.0)
os.write(fd, b"X" * 512)
os.close(fd)
'''

MINI_DUP = r'''
import sys
name = "\u0e1b\u0e23\u0e30\u0e40\u0e17\u0e28\u0e44\u0e17\u0e22"      # Thai (quoted header field)
sys.stderr.write("csv2json: error: in.csv line 1: duplicate header name '%s'\n" % name)
sys.exit(1)
'''

RESULTS = []
def record(pid, ok, detail):
    RESULTS.append((pid, ok, detail))
    print("%-6s %s  %s" % (pid, "PASS" if ok else "OBSERVED", detail))

def run(src, args, **kw):
    return subprocess.run([PY, "-c", src] + args, capture_output=True, **kw)

def main():
    tmp = tempfile.mkdtemp(prefix="adv-c7-")
    print("interpreter:", sys.version.split()[0], " host:", os.uname().sysname)
    # ---- P1 / P1c: SIGINT mid-write, blocked FIFO write ----
    for tag, src, expect_removed in (("P1", WRITER_TMPL.replace("__WRAPCLS__", "BaseException"), True),
                                     ("P1c", WRITER_TMPL.replace("__WRAPCLS__", "Exception"), False)):
        fifo = os.path.join(tmp, tag + ".fifo"); os.mkfifo(fifo)
        reader = subprocess.Popen([PY, "-c", "import time; f=open(%r); time.sleep(30)" % fifo],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        child = subprocess.Popen([PY, "-c", src, fifo], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1.5)                              # child now blocked in write()
        child.send_signal(subprocess.signal.SIGINT if hasattr(subprocess, "signal") else 2)
        out, err = child.communicate(timeout=10)
        reader.kill(); reader.wait()
        removed = not os.path.exists(fifo)
        record(tag, removed == expect_removed,
               "SIGINT mid-write rc=%d removed=%s ki_in_stderr=%s (§4.5 BaseException shape removes; §7.1 taxonomy says kill 'leaves whatever partial output existed')" %
               (child.returncode, removed, b"KeyboardInterrupt" in err))
    # ---- P2: /dev/stdout and /dev/stderr as output on a SUCCESSFUL run ----
    inp = os.path.join(tmp, "in.csv")
    with open(inp, "w", encoding="utf-8") as f: f.write("id,name\n1,x\n")
    r = run(REF_TOOL, [inp, "/dev/stdout"])
    record("P2", r.returncode == 0 and r.stdout.startswith(b'[{"id"'),
           "output=/dev/stdout rc=%d stdout=%r — §6.1 'stdout: empty on success' FALSE, exit 0" % (r.returncode, r.stdout[:40]))
    r = run(REF_TOOL, [inp, "/dev/stderr"])
    record("P2b", r.returncode == 0 and r.stderr.startswith(b'[{"id"'),
           "output=/dev/stderr rc=%d stderr=%r — §6.4 success row 'stderr empty' FALSE" % (r.returncode, r.stderr[:40]))
    # ---- P3: ASCII stderr MANGLES the verbatim E-DUP name (runtime
    #         backslashreplace) — §6.3 declares escaped names NON-CONFORMING,
    #         §6.1 claims locale-independence ----
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C", "LANG": "C",
           "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
    enc = subprocess.run([PY, "-c", "import sys; print(sys.stderr.encoding, sys.stderr.errors)"],
                         capture_output=True, env=env).stdout.decode().strip()
    r = run(MINI_DUP, [], env=env)
    thai_utf8 = "\u0e1b\u0e23\u0e30\u0e40\u0e17\u0e28\u0e44\u0e17\u0e22".encode("utf-8")
    record("P3", thai_utf8 not in r.stderr and b"Traceback" not in r.stderr and b"\\u0e1b" in r.stderr,
           "stderr=%s rc=%d escaped=%s crash=%s — verbatim Thai UNREACHABLE under LC_ALL=C; runtime escaping §6.3 forbids" %
           (enc, r.returncode, b"\\u0e1b" in r.stderr, b"Traceback" in r.stderr))
    # ---- P3b: surrogate-bearing argv path (undecodable byte) into E-READ ----
    bad_arg = os.fsdecode(b"in\xff.csv")            # lone surrogate
    r = run(REF_TOOL, [bad_arg, os.path.join(tmp, "o3b.json")], env=env)
    record("P3b", r.returncode == 1 and b"cannot read" in r.stderr and b"Traceback" not in r.stderr,
           "argv surrogates rc=%d msg=%r — no crash (backslashreplace), bytes not the raw path" %
           (r.returncode, r.stderr.strip()[:50]))
    # ---- P4: at-open EACCES while a concurrent writer already truncated ----
    out = os.path.join(tmp, "out.json")
    with open(out, "wb") as f: f.write(b"PRIOR")
    a = subprocess.Popen([PY, "-c", A_CHILD, out])  # A: truncates to 0, sleeps 2s
    time.sleep(0.7)                                 # A's open(O_TRUNC) has run
    os.chmod(out, 0o444)                            # target read-only only now
    r = run(REF_TOOL, [inp, out])                   # B: open fails EACCES
    os.chmod(out, 0o644); a.wait()                  # A then writes 512 X's
    size_at_report = os.path.getsize(out) if os.path.exists(out) else -1
    record("P4", r.returncode == 1 and b"cannot write" in r.stderr and size_at_report == 512,
           "B at-open EACCES rc=%d msg_ok=%s final_size=%d — during B's report the target held A's 0-byte truncation; §6.3 'byte-untouched' unqualified vs §4.5 row 9" %
           (r.returncode, b"cannot write" in r.stderr, size_at_report))
    # ---- P5: BOM + lone surrogate -> E-UTF8 precedence ----
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "wb") as f: f.write(b"\xef\xbb\xbf" + b"a,b\n\xed\xa0\x80c\n")
    r = run(REF_TOOL, [bad, os.path.join(tmp, "o5.json")])
    record("P5", r.returncode == 1 and b"not valid UTF-8" in r.stderr,
           "BOM+surrogate rc=%d msg=%r" % (r.returncode, r.stderr.strip()[:60]))
    print("\n%d probes" % len(RESULTS))

if __name__ == "__main__":
    main()

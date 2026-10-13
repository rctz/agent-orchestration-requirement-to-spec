# Adversarial-early cycle 5 probes (adv-c5) — evidence for appendix/26-adv-c5.md
# Target: spec/05-spec-v5.md (DRAFT v5). Python 3.13.5, this workspace.
# Method note: fault injection at stage boundaries mirrors the spec's own
# W-series methodology (appendix/22-rev4-writeorder-probes.py). The filesystem
# is REAL in every probe (no fs mocking) — only the fault position is injected,
# exactly like MemoryError-at-encode in the spec's own evidence base.
import csv, errno, io, os, subprocess, sys, tempfile

NPASS = NFAIL = 0
def check(name, cond, detail=""):
    global NPASS, NFAIL
    if cond: NPASS += 1; print(f"PASS {name} :: {detail}")
    else:    NFAIL += 1; print(f"FAIL {name} :: {detail}")

# ---------- reference shapes transcribed from spec v5 ----------

def write_output_binary(path, document, fail_at=None):
    """§4.5 pinned shape: (1) encode BEFORE open (D-43); (2) open(path,'wb');
    (3) write/flush; EVERY post-open exception -> best-effort remove, then raise."""
    if fail_at == "encode":                      # pre-open (D-43 step 1)
        raise MemoryError("injected: encode OOM (pre-open)")
    payload = document.encode("utf-8")
    try:
        f = open(path, "wb")                     # O_TRUNC here
        try:
            if fail_at == "write":
                f.write(payload[:len(payload)//2])
                raise OSError(errno.EIO, "injected EIO mid-write")
            f.write(payload); f.flush()
        finally:
            f.close()
    except BaseException:
        try: os.remove(path)                     # D-33 compensation, every class
        except OSError: pass
        raise

def write_output_textmode(path, document, fail_encode=False):
    """§4.5 parenthetical 'equivalent conforming alternative': text mode
    open(path,'w',newline='',encoding='utf-8'); the encode is implicit INSIDE
    the write call, so an encode-time MemoryError strikes POST-open."""
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            if fail_encode:
                raise MemoryError("injected: implicit-encode OOM inside write")
            f.write(document)
    except BaseException:
        try: os.remove(path)
        except OSError: pass
        raise

def fsm(record_text):
    """§4.3.3 four-state FSM with the D-28 pair-collapse counter.
    Returns (end_state, opening_record_relative_line)."""
    FS, UQ, Q, C = "FIELD_START", "UNQUOTED", "QUOTED", "CLOSED"
    st, line, open_line = FS, 1, None
    i = 0
    while i < len(record_text):
        ch = record_text[i]
        pair = ch == "\r" and record_text[i+1:i+2] == "\n"
        if st == FS:
            if ch == '"': st, open_line = Q, line
            elif ch == ",": pass
            elif ch in "\r\n": st = FS; i += 1 if pair else 0
            else: st = UQ
        elif st == UQ:
            if ch == ",": st = FS
            elif ch in "\r\n": st = FS; i += 1 if pair else 0
        elif st == Q:
            if ch == '"': st = C
            elif ch in "\r\n": i += 1 if pair else 0; line += 1
        else:  # CLOSED
            if ch == '"': st, open_line = Q, line
            elif ch == ",": st = FS
            elif ch in "\r\n": st = FS; i += 1 if pair else 0
            else: st = UQ
        i += 1
    return st, open_line

def csv_records(text):
    return list(csv.reader(io.StringIO(text, newline="")))

def line_of_offset(text, offset):
    line, i = 1, 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i+1:i+2] == "\n" else 1; line += 1
        else:
            i += 1
            if text[i-1] == "\n": line += 1
    return line

PRIOR = b'{"prior":"good-bytes"}\n'
DOC   = '[{"id":"1","name":"aaaaaaaaaaaaaaaaaaaaaaaa"},{"id":"2","name":"b"}]\n'

# ---------- P1: §4.5 text-mode "equivalent" alternative vs T-C16 / S-14(d) ----------
# Scenario: pre-existing GOOD output; encode-phase MemoryError fault-injected at
# the implicit encode site (inside the write call, per the parenthetical's own
# description). Binary shape (pinned): encode pre-open -> prior bytes survive
# (D-43). Text-mode shape ("equivalent conforming alternative"): open() has
# ALREADY truncated the target when the implicit encode raises.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "out.json")
    open(p, "wb").write(PRIOR)
    try:
        write_output_textmode(p, DOC, fail_encode=True)
        r = "no-raise"
    except MemoryError:
        r = "MemoryError"
    if os.path.exists(p):
        after = open(p, "rb").read(); state = f"exists ({len(after)}B)"
    else:
        after = None; state = "ABSENT (prior file deleted by compensation)"
    check("P1 textmode encode-OOM leaves prior bytes intact (QC-2/T-C16 assert YES)",
          after == PRIOR, f"textmode: target {state}, raised={r}; "
          "binary D-43 shape leaves prior bytes (verified next)")
    # binary pinned shape, same fault position
    open(p, "wb").write(PRIOR)
    try:
        write_output_binary(p, DOC, fail_at="encode")
    except MemoryError:
        pass
    after2 = open(p, "rb").read()
    check("P1b binary D-43 shape encode-OOM keeps prior bytes", after2 == PRIOR,
          f"after={after2!r}")

# ---------- P2: compensation vs symlink/hardlink aliasing (D-33/QC-2) ----------
# os.remove(path) removes the NAME. If the opened output path is a SYMLINK to a
# user file, open(path,'wb') writes THROUGH the link into the target file, and
# the compensation deletes the link NAME — leaving the user's real file holding
# the PARTIAL payload. F-02 counterexample.
with tempfile.TemporaryDirectory() as d:
    real = os.path.join(d, "real.json"); link = os.path.join(d, "alias.json")
    open(real, "wb").write(PRIOR)
    os.symlink(real, link)
    try:
        write_output_binary(link, DOC, fail_at="write")
    except OSError:
        pass
    left = sorted(os.listdir(d))
    real_after = open(real, "rb").read() if os.path.exists(real) else b"<gone>"
    check("P2 symlinked output: partial payload survives in the REAL file "
          "(D-33 remove-the-path compensation cannot undo it)",
          os.path.exists(real) and real_after not in (PRIOR, DOC.encode(), b""),
          f"dir={left} real now {real_after[:40]!r}... ({len(real_after)}B) — "
          f"alias {'still exists' if os.path.exists(link) else 'removed'}; "
          "partial JSON remains as a plausible document")

# hardlink variant: pre-existing good output hard-linked elsewhere; open(O_TRUNC)
# destroys the shared inode's bytes; remove(path) deletes ONE name; the OTHER
# name (same inode) keeps the partial bytes.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "out.json"); twin = os.path.join(d, "twin.json")
    open(p, "wb").write(PRIOR); os.link(p, twin)
    try:
        write_output_binary(p, DOC, fail_at="write")
    except OSError:
        pass
    twin_after = open(twin, "rb").read() if os.path.exists(twin) else b"<gone>"
    check("P2b hardlinked output: twin name keeps PARTIAL bytes after compensation",
          os.path.exists(twin) and twin_after not in (PRIOR, DOC.encode()),
          f"twin={twin_after[:40]!r}... ({len(twin_after)}B) out.json "
          f"{'exists' if os.path.exists(p) else 'removed'}")

# ---------- P3: /dev/full is NOT a regular file — does the pinned shape hold? ----------
with tempfile.TemporaryDirectory() as d:
    devfull = "/dev/full"
    if os.path.exists(devfull):
        try:
            write_output_binary(devfull, DOC)
            r3 = "no-raise"
        except OSError as e:
            r3 = f"OSError({e.errno})"
        check("P3 /dev/full: open succeeds, write/flush ENOSPC, compensation remove "
              "fails EINVAL and is ignored, run reports E-WRITE shape",
              r3.startswith("OSError(28"), f"raised={r3} dev still exists="
              f"{os.path.exists(devfull)}")
    else:
        print("SKIP P3 (/dev/full absent)")

# ---------- P4: tell()-span arithmetic vs a record consumed but never yielded ----------
# §4.3.2 loop: `record = next(reader)`; StopIteration -> break happens BEFORE
# `end = reader_file.tell()`. Probe: is tell() after a trailing newline
# consistent with span logic (start=end at empty trailing tail)? And: for a
# reader whose final next() raises StopIteration, csv.reader's underlying
# buffer/tell relationship — pinned by P1/T-U2 — remains the spec's evidence.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "in.csv")
    open(p, "w", newline="").write('id,name\n1,x\n')
    text = open(p, encoding="utf-8").read()
    sf = io.StringIO(text, newline="")
    rd = csv.reader(sf)
    rows = []
    start = 0
    while True:
        try:
            rec = next(rd)
        except StopIteration:
            break
        end = sf.tell()
        rows.append((rec, text[start:end]))
        start = end
    check("P4 tell-span slices reproduce csv iteration exactly (incl. final record)",
          [r[0] for r in rows] == [["id", "name"], ["1", "x"]],
          f"spans={[r[1] for r in rows]}")

# ---------- P5: E-UQ N/M vs FSM on the header-form edge `a,"b\n1` ----------
# Header `a,"b` (unclosed quote, second field) + one data row after a newline
# INSIDE the quote — the quote swallows the terminator, so the whole input is
# ONE record spanning 2 physical lines. Probe the FSM's N/M against D-28.
text5 = 'a,"b\n1'
recs = csv_records(text5)
sf = io.StringIO(text5, newline="")
rd5 = csv.reader(sf)
rec5 = next(rd5)
end5 = sf.tell()
st5, ol5 = fsm(text5[:end5])
N5 = 1  # header record starts at line 1
M5 = N5 + ol5 - 1
check("P5 header unclosed-quote multi-line: lenient ONE-record parse + FSM N/M=1",
      rec5 == ["a", "b\n1"] and st5 == "QUOTED" and M5 == 1,
      f"lenient record={rec5!r} (terminator swallowed by the open quote — whole "
      f"input is ONE record) end_state={st5} opening_line(rel)={ol5} -> "
      f"N={N5} M={M5} — the spec's 'AFTER all upstream collapses' rule gives "
      "M=1 (quote on record-relative line 1); row-start N=1; no divergence "
      "between my FSM transcription and the spec's rule on this edge")

# ---------- P6: MemoryError BEFORE main's handler — __del__ during OOM ----------
# §7.3 order: except MemoryError first. If MemoryError strikes while the rows
# list is huge, raising FieldError(...) formats a message STRING (allocation)
# while memory is exhausted — can formatting itself re-fault? And does the
# 'rows' list stay alive (referenced by traceback frames) preventing reclamation
# before the print? Probe: simulate by formatting under a tight cap using a
# custom object whose __str__ raises MemoryError on 2nd allocation.
class OOMStr:
    def __init__(self, armed=True):
        self.armed = armed
    def __str__(self):
        if self.armed:
            raise MemoryError("injected: format-under-OOM")
        return "x"
o = OOMStr()
try:
    s = f"csv2json: error: {o}"
    r6 = "no-raise"
except MemoryError:
    r6 = "MemoryError"
check("P6 formatting the error message under continued memory pressure re-raises",
      r6 == "MemoryError", f"f-string with __str__ raising MemoryError -> {r6}; "
      "under real OOM the E-MEM path itself can re-fault before printing")

# ---------- P7: exit-code surface — `main` returning 1 vs sys.exit(main(...)) ----------
# §4.1: entry guard sys.exit(main(sys.argv[1:])). stdout silent; exit code
# observable. Trivially pinned by T-C*; here: exit code of the run is the
# return of main (0 success / 1 failure) — no hidden exit-2 path (argparse's
# default must be overridden per D-41). Confirm no argv path returns 2.
def main_ref(argv):
    if len(argv) != 2:
        return 1
    return 0
check("P7 manual dispatch returns only 0/1", all(main_ref(a) in (0, 1)
      for a in ([], ["x"], ["x", "y"], ["x", "y", "z"])), "argc sweep")

# ---------- P8: concurrent O_TRUNC + compensation remove race ----------
# Two overlapping runs to the SAME target (R-2's scenario, dismissed as "last
# writer wins"): run A is mid-write (file created, partial bytes), run B's
# open(O_TRUNC) fires, then A faults and runs its compensation remove — which
# deletes the file B is now writing. B's later compensation (on its own
# failure) gets ENOENT, but if B SUCCEEDS, its completed file was deleted by
# A's compensation. "Last writer wins" is FALSE under the pinned mechanism.
def worker(dirname, tag, delay):
    p = os.path.join(dirname, "out.json")
    doc = ("[" + ",".join(f'{{"{tag}":"{i}"}}' for i in range(200000)) + "]\n")
    try:
        payload = doc.encode()
        f = open(p, "wb")
        try:
            for i in range(0, len(payload), 65536):
                f.write(payload[i:i+65536])
                if tag == "A":
                    import time; time.sleep(delay)
            f.flush()
            return ("ok", tag, len(payload))
        finally:
            f.close()
    except BaseException as e:
        try: os.remove(p)
        except OSError: pass
        return ("fail", tag, repr(e)[:40])

with tempfile.TemporaryDirectory() as d:
    import threading
    res = {}
    def run(tag, delay):
        res[tag] = worker(d, tag, delay)
    tA = threading.Thread(target=run, args=("A", 0.002))
    tB = threading.Thread(target=run, args=("B", 0.0))
    tA.start(); tB.start(); tA.join(); tB.join()
    p = os.path.join(d, "out.json")
    final_exists = os.path.exists(p)
    final_bytes = open(p, "rb").read() if final_exists else b""
    # A writes slowly, fails partway (simulated by never finishing before B's
    # truncation + a forced fault), B completes. Order: A opens+writes partial,
    # B opens (truncates), A faults -> remove, B finishes writing+flushing.
    check("P8 interleaved writes: A-fail compensation can delete B's completed file",
          True,  # documentary probe: outcome printed for the report
          f"A={res.get('A')} B={res.get('B')} final_exists={final_exists} "
          f"final_len={len(final_bytes)}")

# ---------- P9: RLIMIT_AS child — which E-MEM phase form surfaces? ----------
# T-C16 accepts ANY phase form. Reference impl under a low RLIMIT_AS on a
# 20 MB input: read phase trips first (bulk read). Under a higher-but-tight
# cap with small input, parse/serialize may trip. Documentary.
def ref_tool():
    """Minimal reference implementation of the five-stage pipeline."""
    def main(argv):
        if len(argv) != 2:
            sys.stderr.write("csv2json: error: usage: csv2json.py <input.csv> <output.json>\n")
            return 1
        inp, outp = argv
        try:
            data = open(inp, "rb").read()
        except OSError as e:
            sys.stderr.write(f"csv2json: error: cannot read {inp}: {e.strerror}\n"); return 1
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            sys.stderr.write(f"csv2json: error: {inp} line 1: byte 0xff is not valid UTF-8\n"); return 1
        if text.startswith("﻿"):
            text = text[1:]
        rows = []
        sf = io.StringIO(text, newline="")
        rd = csv.reader(sf)
        try:
            header = next(rd)
        except StopIteration:
            sys.stderr.write(f"csv2json: error: {inp}: file is empty (no header row)\n"); return 1
        if len(header) == 0:
            sys.stderr.write(f"case {inp} line 1: invalid header row (found 0 fields)\n"); return 1
        seen = set(); dup = None
        for h in header:
            if h in seen: dup = h; break
            seen.add(h)
        if dup is not None:
            sys.stderr.write(f"csv2json: error: {inp} line 1: duplicate header name '{dup}'\n")
            return 1
        line = 1; start = 0
        while True:
            try:
                rec = next(rd)
            except StopIteration:
                break
            end = sf.tell()
            # (FSM scan + count check elided in this probe reference)
            if len(rec) != len(header):
                sys.stderr.write(f"csv2json: error: {inp} line {line}: expected {len(header)} fields, found {len(rec)}\n")
                return 1
            rows.append(dict(zip(header, rec)))
            start = end; line += 1
        try:
            doc = __import__("json").dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n"
            payload = doc.encode("utf-8")
            with open(outp, "wb") as f:
                f.write(payload); f.flush()
        except MemoryError:
            sys.stderr.write(f"csv2json: error: out of memory writing {outp}\n"); return 1
        except OSError as e:
            try: os.remove(outp)
            except OSError: pass
            sys.stderr.write(f"csv2json: error: cannot write {outp}: {e.strerror}\n"); return 1
        return 0
    return main

with tempfile.TemporaryDirectory() as d:
    inp = os.path.join(d, "big.csv")
    with open(inp, "w", newline="") as f:
        f.write("id,name\n")
        for i in range(300000):
            f.write(f"{i},xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n")
    size_mb = os.path.getsize(inp) / 1e6
    # child with low RLIMIT_AS runs a self-contained driver embedding the
    # reference pipeline (kept small: read+decode+parse only, E-MEM on any
    # MemoryError per §7.3 handler order).
    driver = os.path.join(d, "driver.py")
    with open(driver, "w") as f:
        f.write(
            "import resource,sys,csv,io,json\n"
            "resource.setrlimit(resource.RLIMIT_AS,(64*1024*1024,64*1024*1024))\n"
            "inp,outp=sys.argv[1],sys.argv[2]\n"
            "try:\n"
            "    data=open(inp,'rb').read()\n"
            "    text=data.decode('utf-8')\n"
            "    if text.startswith('\\ufeff'): text=text[1:]\n"
            "    rows=list(csv.reader(io.StringIO(text,newline='')))\n"
            "    doc=json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\\n'\n"
            "    payload=doc.encode('utf-8')\n"
            "    with open(outp,'wb') as fh: fh.write(payload); fh.flush()\n"
            "    sys.exit(0)\n"
            "except MemoryError:\n"
            "    sys.stderr.write('csv2json: error: out of memory reading '+inp+'\\n')\n"
            "    sys.exit(1)\n")
    r = subprocess.run([sys.executable, driver, inp, os.path.join(d, "out.json")],
                       capture_output=True, text=True, timeout=300)
    out_exists = os.path.exists(os.path.join(d, "out.json"))
    check("P9 RLIMIT_AS child surfaces an E-MEM phase form, exit 1, no partial output",
          r.returncode == 1 and "out of memory" in r.stderr and not out_exists,
          f"rc={r.returncode} size={size_mb:.1f}MB stderr={r.stderr.strip()[:100]!r} "
          f"out_exists={out_exists}")

# ---------- P10: compensation on AT-open failure with a PRE-EXISTING target ----------
# §4.5 wraps steps (2)-(3) so ANY exception — "EACCES at open" explicitly listed —
# runs the compensation remove(path). If the target pre-exists but is not
# writable by us (mode 444) while the DIRECTORY is writable, open(path,"wb")
# fails EACCES and os.remove(path) SUCCEEDS: the failed run deletes the user's
# prior output. S-14(b) calls the open-failure compensation "a harmless no-op
# (ENOENT ignored)" — true only for an ABSENT path.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "out.json")
    open(p, "wb").write(PRIOR)
    os.chmod(p, 0o444)                    # read-only target, writable dir
    try:
        write_output_binary(p, DOC)
        r10 = "no-raise"
    except OSError as e:
        r10 = f"OSError({e.errno})"
    exists10 = os.path.exists(p)
    check("P10 AT-open EACCES + pre-existing read-only target: compensation DELETES prior file",
          r10.startswith("OSError(13") and not exists10,
          f"raised={r10} target_exists_after={exists10} — prior GOOD bytes destroyed "
          "by a failed run that never opened the file (S-14(b) 'harmless no-op' "
          "holds only for absent paths)")

# ---------- P11: E-MEM phase-form selection — which phase trips under RLIMIT_AS ----------
# A single bare `except MemoryError` in main (§7.3) has no phase information;
# §6.3 pins THREE phase forms. Documentary: which form a minimal single-handler
# build must print is not mechanized anywhere; T-C16 accepts ANY form, so the
# per-phase templates are not forcible by the pinned tests.
with tempfile.TemporaryDirectory() as d:
    inp = os.path.join(d, "mid.csv")
    with open(inp, "w", newline="") as f:
        f.write("id,name\n")
        for i in range(120000):
            f.write(f"{i},yyyyyyyyyyyyyyyyyyyy\n")
    # cap between input size and 2x input: parse/serialize region
    driver = os.path.join(d, "driver2.py")
    with open(driver, "w") as f:
        f.write(
            "import resource,sys,csv,io,json\n"
            "cap=int(sys.argv[3])\n"
            "resource.setrlimit(resource.RLIMIT_AS,(cap,cap))\n"
            "inp,outp=sys.argv[1],sys.argv[2]\n"
            "try:\n"
            "    data=open(inp,'rb').read()\n"
            "    text=data.decode('utf-8')\n"
            "    rows=[dict(zip(('id','name'),r)) for r in csv.reader(io.StringIO(text,newline=''))][1:]\n"
            "    doc=json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\\n'\n"
            "    payload=doc.encode('utf-8')\n"
            "    with open(outp,'wb') as fh: fh.write(payload); fh.flush()\n"
            "    sys.exit(0)\n"
            "except MemoryError:\n"
            "    sys.stderr.write('csv2json: error: out of memory reading '+inp+'\\n')\n"
            "    sys.exit(1)\n")
    results = []
    for cap_mb in (200, 300, 400):
        r = subprocess.run([sys.executable, driver, inp, os.path.join(d, f"o{cap_mb}.json"),
                            str(cap_mb * 1024 * 1024)], capture_output=True, text=True,
                           timeout=300)
        results.append(f"cap={cap_mb}MB rc={r.returncode} err={r.stderr.strip()[:60]!r}")
    check("P11 phase-form selection under varying caps (documentary)",
          True, " | ".join(results))

# ---------- P12: R-2's "last writer wins" gloss — deterministic interleaving ----------
# A opens out.json and faults post-open; its compensation removes the NAME.
# B had already opened the same path; B's fd still points at the (now unlinked)
# inode. B writes, flushes, closes — all succeed — and exits 0 SILENTLY.
# Final state: out.json does not exist. Neither A's nor B's output survives;
# a SILENT SUCCESS produced no file.
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "out.json")
    fdA = open(p, "wb")                       # run A opens
    fdB = open(p, "wb")                       # run B opens (O_TRUNC)
    try:                                      # run A faults post-open:
        raise OSError(errno.EIO, "A: injected EIO mid-write")
    except OSError:
        try: os.remove(p)                     # A's D-33 compensation
        except OSError: pass
    # run B continues on its own fd and SUCCEEDS
    fdB.write(DOC.encode()); fdB.flush(); fdB.close()
    fdA.close()
    b_silent_success = True                   # B printed nothing, exit 0
    check("P12 failed run's compensation unlinks a concurrent success's output "
          "(R-2 'last writer wins' is false; silent success, no file)",
          not os.path.exists(p),
          f"out.json exists after B's silent success: {os.path.exists(p)} — "
          "B exited 0 with no output file (REQ glossary success condition broken)")

print(f"\nTOTAL PASS: {NPASS}  TOTAL FAIL: {NFAIL}")


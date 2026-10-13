#!/usr/bin/env python3
"""Rev11 probes (card t_57766173): re-run adv-c10's checks against spec/11-spec-v11.md
plus the five-site fold-check greps and the R-6 create-flavor textual check.

Re-aims appendix/45b-adv-c10-probes.py (whose subject was spec/10-spec-v10.md):
  P1a/P1b behavioral — the §4.5 reference shape under a MemoryError at fd.write with
      (P1a) a second MemoryError at the arm's fd.close() [partial file PRESENT] and
      (P1b) a completing arm [partial REMOVED];
  P2a/P2b behavioral — a minimal conforming build writing to /dev/stderr and /dev/stdout
      (exit 0, document on that device);
  P3a textual — §1 and §11 decision enumerations agree;
  P4 textual — R-6's residue bound names the create flavor (inverted from 45b's P4,
      which proved it was missing on v10);
NEW cycle-11 fold-checks F1..F9 — the D-53/R-5 arm-abort qualifier present at all five
absolute write-phase-removal sites (S-14(e), §6.3 E-MEM, §7.2 footprint, T-C16,
QC-2 Verification), the §4.5 normative-lead fold, and the F-02 scope notes.
"""
import csv
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
SPEC = os.path.join(HERE, "spec", "11-spec-v11.md")
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS" if ok else "FAIL"), name, ("— " + detail) if detail else "")


def norm(s):
    return re.sub(r"\s+", " ", s)


def between(text, start_pat, end_pat):
    m1 = re.search(start_pat, text, re.M)
    m2 = re.search(end_pat, text, re.M)
    return text[m1.start():m2.start()] if (m1 and m2) else ""


text = open(SPEC, encoding="utf-8").read()
s45 = between(text, r"^## 4\.5 ", r"^## 4\.6 ")
s53 = between(text, r"^## 5\.3 ", r"^# 6\. ")
s63 = between(text, r"^## 6\.3 ", r"^## 6\.4 ")
s72 = between(text, r"^## 7\.2 ", r"^## 7\.3 ")
s83 = between(text, r"^## 8\.3 ", r"^## 8\.4 ")
qc2 = between(text, r"^### QC-2 ", r"^### QC-3 ")
r6 = between(text, r"^- R-6: ", r"^- R-7: ")
if not r6:
    r6 = between(text, r"^- R-6: ", r"^# 11\. ")

# ---------- P3a: enumerations agree at D-01..D-56 ----------
m1 = re.search(r"leaves none unresolved: D-\d+\.\.D-(\d+)", text)
m2 = re.search(r"Decision-coverage check: D-\d+\.\.D-(\d+) are all DECIDED", text)
check("P3a", bool(m1 and m2 and m1.group(1) == m2.group(1) == "56"),
      "§1=%s §11=%s" % (m1 and m1.group(1), m2 and m2.group(1)))

# ---------- P4 (re-aimed): R-6 names the create flavor; the old bound is gone ----------
n = norm(text)
check("P4", "bounded to pre-existing targets" not in norm(r6)
      and "bounded to pre-existing targets" not in norm(qc2)
      and "bounded to pre-existing targets" not in norm(s45)
      and "bounded to pre-existing targets" not in norm(s72)
      and "ABSENT target CREATED at 0 bytes" in norm(r6)
      and "create flavor" in norm(r6) and "D-56(b)" in norm(r6))

# ---------- F1..F9: the fold needles ----------
check("F1 S-14e", "UNLESS the" in norm(s53) and "D-53/R-5" in norm(s53)
      and "second MemoryError" in norm(s53))
check("F2 6.3-E-MEM", "UNLESS the compensation itself is aborted per D-53/R-5" in norm(s63)
      and "second MemoryError (or second KI)" in norm(s63))
check("F3 7.2-footprint", "UNLESS the compensation itself is aborted" in norm(s72)
      and "second MemoryError" in norm(s72)
      and "create flavor of R-6" in norm(s72) and "CREATED 0-byte" in norm(s72))
check("F4 T-C16", "path is ABSENT — unless the compensation itself is aborted mid-flight per D-53/R-5" in norm(s83)
      and "second MemoryError" in norm(s83)
      and "OUTSIDE the D-53 arm-abort residue" in norm(s83))
check("F5 QC-2", "D-53/R-5 arm-abort scope" in norm(qc2)
      and "second MemoryError" in norm(qc2)
      and "ABSENT target may be left CREATED at 0 bytes" in norm(qc2)
      and "D-56(a)" in norm(qc2) and "D-56(b)" in norm(qc2))
check("F6 4.5-lead", "ALWAYS within the D-53 arm-abort scope" in norm(s45)
      and "second MemoryError" in norm(s45))
check("F7 R-6-widen", "truncated to 0 bytes, or an ABSENT target CREATED at 0 bytes" in norm(r6)
      and "D-56(b)" in norm(r6))
gone = re.search(r"the file is GONE after the failed run \(by design, D-46's trigger; UNLESS the.{0,400}?second MemoryError", norm(s53))
check("F8 GONE-qualified", bool(gone))
check("F9 stderr-scope", "empty on success — FOR REGULAR-FILE output paths" in n
      and "silent success | Exit 0 with empty stdout and the output file written — for REGULAR-FILE output paths" in n)
s71 = between(text, r"^## 7\.1 ", r"^## 7\.2 ")
check("F10 7.1-E-MEM-row", "the D-53 arm-abort scope applies — a second MemoryError" in norm(s71)
      and "no partial output outside the D-53/R-5 arm-abort residue" in norm(s71))

# ---------- P1a/P1b: the reference shape under MemoryError faults ----------
REF_SHAPE = """
fd = None
try:
    fd = open(path, "wb")
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
"""


class FakeFD:
    def __init__(self, real, payload, write_half_then_raise, close_raises):
        self.real = real
        self.payload = payload
        self.write_fault = write_half_then_raise
        self.close_fault = close_raises
        self.wrote = False

    def write(self, data):
        if self.write_fault and not self.wrote:
            self.real.write(self.payload[: len(self.payload) // 2])
            self.real.flush()
            self.wrote = True
            raise MemoryError
        return self.real.write(data)

    def flush(self):
        return self.real.flush()

    def close(self):
        if self.close_fault:
            raise MemoryError
        return self.real.close()


def run_shape(out_path, payload, write_fault, close_fault):
    captured = {}

    def fake_open(p, mode="rb", *a, **k):
        if p == out_path and mode == "wb":
            real = open(p, mode)
            captured["fd"] = FakeFD(real, payload, write_fault, close_fault)
            return captured["fd"]
        return open(p, mode, *a, **k)

    ns = {"os": os, "open": fake_open, "path": out_path, "payload": payload}
    reported = None
    try:
        exec(REF_SHAPE, ns)
    except MemoryError:
        reported = "csv2json: error: out of memory writing " + os.path.basename(out_path)
    except KeyboardInterrupt:
        reported = "<KeyboardInterrupt>"
    return reported, captured


with tempfile.TemporaryDirectory() as td:
    payload = (b'{"a":"' + b"x" * 26 + b'"},') * 103  # 3096 bytes, ~45b's scale
    payload = payload[:3092]
    # P1a: MemoryError at fd.write + second MemoryError at the arm's fd.close()
    out = os.path.join(td, "out.json")
    reported, cap = run_shape(out, payload, write_fault=True, close_fault=True)
    present = os.path.exists(out)
    size = os.path.getsize(out) if present else 0
    try:
        cap["fd"].real.close()
    except Exception:
        pass
    check("P1a", reported == "csv2json: error: out of memory writing out.json"
          and present and size == len(payload) // 2,
          "reported=%r present=%s size=%d/%d" % (reported, present, size, len(payload)))
    # P1b: control — single MemoryError, arm completes, file REMOVED
    out = os.path.join(td, "out2.json")
    reported, cap = run_shape(out, payload, write_fault=True, close_fault=False)
    present = os.path.exists(out)
    check("P1b", reported == "csv2json: error: out of memory writing out2.json" and not present,
          "reported=%r present=%s" % (reported, present))

    # P1c: honest negative — pure RLIMIT_AS sweep (no fault injection)
    child = os.path.join(td, "sweep_child.py")
    with open(child, "w") as f:
        f.write(
            "import os, resource, sys\n"
            "limit, out_path, nbytes = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])\n"
            "resource.setrlimit(resource.RLIMIT_AS, (limit, limit))\n"
            "fd = None\n"
            "try:\n"
            "    payload = b'x' * nbytes\n"
            "    fd = open(out_path, 'wb')\n"
            "    fd.write(payload); fd.flush()\n"
            "    fd.close(); fd = None\n"
            "except MemoryError:\n"
            "    if fd is not None:\n"
            "        try: fd.close()\n"
            "        except OSError: pass\n"
            "        fd = None\n"
            "        try: os.remove(out_path)\n"
            "        except OSError: pass\n"
            "    print('OMEM')\n"
        )
    reproduced = 0
    for limit in (24 * 1024 * 1024, 32 * 1024 * 1024, 48 * 1024 * 1024, 64 * 1024 * 1024):
        out = os.path.join(td, "sweep_out.json")
        if os.path.exists(out):
            os.remove(out)
        r = subprocess.run([sys.executable, child, str(limit), out, str(limit * 3 // 2)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            continue  # interpreter could not even start under the limit — not evidence
        if os.path.exists(out):
            reproduced += 1
    check("P1c", reproduced == 0,
          "cascade reproduced in %d/4 natural-RLIMIT_AS runs (honest negative)" % reproduced)

    # P2a/P2b: minimal conforming build, device outputs
    build = os.path.join(td, "csv2json_build.py")
    with open(build, "w") as f:
        f.write(
            "import csv, io, json, os, sys\n"
            "def main(argv):\n"
            "    if len(argv) != 2:\n"
            "        sys.stderr.write('csv2json: error: usage: csv2json.py <input.csv> <output.json>\\n')\n"
            "        return 1\n"
            "    text = open(argv[0], 'rb').read().decode('utf-8')\n"
            "    if text.startswith('\\ufeff'): text = text[1:]\n"
            "    rows = list(csv.reader(io.StringIO(text, newline='')))\n"
            "    header, data = rows[0], rows[1:]\n"
            "    doc = json.dumps([dict(zip(header, r)) for r in data],\n"
            "                     ensure_ascii=False, separators=(',', ':')) + '\\n'\n"
            "    fd = None\n"
            "    try:\n"
            "        fd = open(argv[1], 'wb')\n"
            "        fd.write(doc.encode('utf-8')); fd.flush()\n"
            "        fd.close(); fd = None\n"
            "    except BaseException:\n"
            "        if fd is not None:\n"
            "            try: fd.close()\n"
            "            except OSError: pass\n"
            "            fd = None\n"
            "            try: os.remove(argv[1])\n"
            "            except OSError: pass\n"
            "        raise\n"
            "    return 0\n"
            "sys.exit(main(sys.argv[1:]))\n"
        )
    in_csv = os.path.join(td, "in.csv")
    with open(in_csv, "w") as f:
        f.write("desc,qty\n5\" ruler,2\n")
    expected_doc = json.dumps([{"desc": "5\" ruler", "qty": "2"}],
                              ensure_ascii=False, separators=(",", ":")) + "\n"
    r = subprocess.run([sys.executable, build, in_csv, "/dev/stderr"],
                       capture_output=True, text=True, timeout=60)
    check("P2a", r.returncode == 0 and r.stderr == expected_doc and r.stdout == "",
          "rc=%d stderr=%r stdout=%r" % (r.returncode, r.stderr[:40], r.stdout[:20]))
    r = subprocess.run([sys.executable, build, in_csv, "/dev/stdout"],
                       capture_output=True, text=True, timeout=60)
    check("P2b", r.returncode == 0 and r.stdout == expected_doc and r.stderr == "",
          "rc=%d stdout=%r stderr=%r" % (r.returncode, r.stdout[:40], r.stderr[:20]))

failures = [nme for nme, ok in results if not ok]
print("TOTAL: %d checks, %d failures" % (len(results), len(failures)))
sys.exit(1 if failures else 0)

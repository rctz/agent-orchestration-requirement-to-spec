# Cycle-5 fold probes (v6 -> v7): live re-verification of every stdlib
# behavior claim pinned by the F-28..F-33 folds, Python 3.13.5.
# Run: python3 appendix/10-fold-c5-probes.py   (exit 0 = all PASS)
import csv, io, json, os, subprocess, sys, tempfile

fails = []
def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, detail)
    if not cond:
        fails.append(name)

# --- F-28 / D-33: mid-write failure (probe W1 basis) --------------------
# /dev/full accepts open() (file created) but fails write/flush with ENOSPC.
devfull = os.path.exists("/dev/full")
if devfull:
    try:
        f = open("/dev/full", "w")
        try:
            f.write('[{"a":"1"}]\n')
            try:
                f.flush()
                check("F28.flush-enospc", False, "no OSError raised")
            except OSError as e:
                check("F28.flush-enospc", e.errno == 28, f"errno={e.errno}")
        finally:
            try:
                f.close()
            except OSError:
                pass  # closing a failed handle may raise again; the flush above is the evidence
    except OSError as e:
        check("F28.flush-enospc", e.errno == 28, f"errno at open/write {e.errno}")
else:
    check("F28.flush-enospc", False, "/dev/full missing")

# Buffered file object with a small buffer raises at flush/close, not write():
# demonstrates the "failure AFTER write() returned" class the contract covers.
class FailingRaw(io.RawIOBase):
    def writable(self):
        return True
    def write(self, b):
        raise OSError(28, "No space left on device")
try:
    fh = io.TextIOWrapper(io.BufferedWriter(FailingRaw()), encoding="utf-8")
    fh.write("x")
    fh.flush()
    check("F28.late-failure-class", False, "no OSError at flush")
    fh.close()
except OSError as e:
    check("F28.late-failure-class", e.errno == 28, f"errno={e.errno}")

# Best-effort removal of a created-but-failed output file (temp analog).
d = tempfile.mkdtemp()
p = os.path.join(d, "out.json")
open(p, "w").close()
os.remove(p)
check("F28.partial-removal-viable", not os.path.exists(p))

# --- F-29 / D-34: argparse usage-error exit code is 2 (must be overridden)
r = subprocess.run([sys.executable, "-c",
    "import argparse\n"
    "p = argparse.ArgumentParser(prog='csv2json.py')\n"
    "p.add_argument('input')\n"
    "p.add_argument('output')\n"
    "p.parse_args(['only-one'])\n"],
    capture_output=True, text=True)
check("F29.argparse-default-2", r.returncode == 2, f"rc={r.returncode}")

# --- F-30 / D-35: write-path newline translation ------------------------
d2 = tempfile.mkdtemp()
# (a) POSIX default text mode: '\n' stays '\n' (translation is a Windows behavior)
pa = os.path.join(d2, "a.json")
with open(pa, "w", encoding="utf-8") as f:
    f.write('[{"x\r\ny"}]\n' .replace('["', '["'))
with open(pa, "rb") as f:
    raw = f.read()
check("F30.posix-text-verbatim", raw.endswith(b"]\n") and b"\r\n" in raw.replace(b"\\r\\n", b""), repr(raw[-8:]))
# (b) pinned write modes produce exactly b']\n' after ']'
for kw, tag in (({"mode": "wb"}, "binary"), ({"mode": "w", "newline": ""}, "newline=''")):
    pp = os.path.join(d2, tag.replace("=", "").replace("'", "") + ".json")
    if "b" in kw["mode"]:
        with open(pp, **kw) as f:
            f.write('[{"a":"1"}]\n'.encode("utf-8"))
    else:
        with open(pp, **kw) as f:
            f.write('[{"a":"1"}]\n')
    with open(pp, "rb") as f:
        check(f"F30.{tag}-ends-LF-only", f.read() == b'[{"a":"1"}]\n')

# --- F-31 / D-36: blank (empty) vs whitespace-only physical lines --------
rows = list(csv.reader(io.StringIO("a\n  \n1\n", newline="")))
check("F31.whitespace-1field", rows == [["a"], ["  "], ["1"]], repr(rows))
rows = list(csv.reader(io.StringIO("a\n\n1\n", newline="")))
check("F31.empty-0field", rows == [["a"], [], ["1"]], repr(rows))
out = json.dumps([dict(zip(["a"], r)) for r in [["  "], ["1"]]],
                 ensure_ascii=False, separators=(",", ":"))
check("F31.ac-bytes", out == '[{"a":"  "},{"a":"1"}]', out)

# --- F-33: empty header name is a permitted verbatim key -----------------
rows = list(csv.reader(io.StringIO("a,,b\n1,2,3\n", newline="")))
obj = dict(zip(rows[0], rows[1]))
s = json.dumps([obj], ensure_ascii=False, separators=(",", ":"))
check("F33.empty-key", s == '[{"a":"1","":"2","b":"3"}]', s)
check("F33.parses-back", json.loads(s) == [{"a": "1", "": "2", "b": "3"}])
dup = list(csv.reader(io.StringIO("a,,b,\n1,2,3,4\n", newline="")))[0]
empties = [i for i, v in enumerate(dup) if v == ""]
check("F33.second-empty-is-duplicate", len(empties) == 2, repr(dup))

print(f"\n{len(fails)} failure(s)" if fails else "\nALL PASS")
sys.exit(1 if fails else 0)

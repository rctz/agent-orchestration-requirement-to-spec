#!/usr/bin/env python3
"""rev9 re-aim probes (cycle 9, card t_5fb98c6a) — spec/10-spec-v10.md.

Subject: the D-51 KI-window contract (KeyboardInterrupt inside the §4.5
except-scoped arm compensates then re-raises; the except-Exception control
leaves the partial and is NON-CONFORMING), the D-52 dispatch shape
(argc==1 -h -> usage/stderr/exit 1; argc==2 -h positional -> E-READ), and
the v9 text pins (§11 coverage range D-01..D-52, §9 NFR-001 argparse-free,
§7.1 kill-note scoping).

Method: P1 EXECs the spec's own fenced §4.5 code block (textwrap-dedented)
with an instrumented open/os injected into the exec namespace — zero
transcription drift; the probe fails automatically if the spec's shape
changes. P2 builds the FORBIDDEN except-Exception control from §7.3's old
sanctioned reading to demonstrate the divergence D-51 closes.
"""
import os, subprocess, sys, tempfile, textwrap, io, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "10-spec-v10.md")
sys.path.insert(0, HERE)

RESULTS = []
def check(name, cond, detail=""):
    RESULTS.append((name, cond))
    print(("PASS" if cond else "FAIL"), name, detail)

text = io.open(SPEC, encoding="utf-8").read()

# ---------- P1: exec the spec's own fenced shape under KeyboardInterrupt ----------
def exec_shape_with(ki_during_write, wrap):
    """Extract §4.5's fenced block, exec it with instrumented open/os.
    Returns (removed, exception_class_name, wrote_bytes)."""
    m = re.search(r"Conforming reference shape[^\n]*\n\n  ```\n(.*?)\n  ```\n", text, re.S)
    assert m, "fenced §4.5 reference shape not found in v9"
    block = textwrap.dedent(m.group(1))
    ns = {"path": os.path.join(tempfile.mkdtemp(), "unused"), "payload": b"X" * 64}
    ns["path"] = None  # set below once target is known
    real_open = open
    state = {"wrote": 0}
    target_holder = {}
    class FakeFD:
        def __init__(self, path):
            self.path = path; self.closed = False
        def write(self, b):
            if ki_during_write and state["wrote"] == 0:
                state["wrote"] = 1
                raise KeyboardInterrupt
            state["wrote"] = 1
            with real_open(self.path, "ab") as f:
                f.write(b)
        def flush(self): pass
        def close(self): self.closed = True
    def fake_open(path, mode="r", **kw):
        if mode == "wb":
            with real_open(path, "wb") as f:  # O_TRUNC semantics
                pass
            return FakeFD(path)
        return real_open(path, mode, **kw)
    fake_os = type(os)("os")  # module-like namespace
    fake_os.remove = os.remove
    ns["open"] = fake_open
    ns["os"] = fake_os
    if wrap == "base":
        inner = block
    else:
        # the FORBIDDEN build: the stage arm catches only Exception —
        # the §7.3-sanctioned "KI is not caught" reading REPLACES the
        # BaseException arm, so a KI skips the compensation entirely
        assert "except BaseException:" in block
        inner = block.replace("except BaseException:", "except Exception:")
    body = "try:\n" + textwrap.indent(inner, "    ") + "\nexcept BaseException:\n    raise"
    target = os.path.join(tempfile.mkdtemp(), "out.json")
    ns["path"] = target
    with real_open(target, "wb") as f:
        f.write(b'PRIOR')
    exc_name = None
    try:
        exec(compile(body, "<spec-shape>", "exec"), ns)
    except BaseException as e:
        exc_name = type(e).__name__
    removed = not os.path.exists(target)
    return removed, exc_name

removed, exc = exec_shape_with(ki_during_write=True, wrap="base")
check("P1 KI inside §4.5 try: target REMOVED, KI propagates (D-51)",
      removed and exc == "KeyboardInterrupt",
      "removed=%s exc=%s" % (removed, exc))

# ---------- P2: the forbidden except-Exception control (old §7.3 reading) ----------
removed2, exc2 = exec_shape_with(ki_during_write=True, wrap="exc")
check("P2 control: except-Exception build LEAVES the partial (the divergence D-51 forbids)",
      (not removed2) and exc2 == "KeyboardInterrupt",
      "removed=%s exc=%s" % (removed2, exc2))

# ---------- P3/P4: dispatch behavior via a reference minimal implementation ----------
ref = os.path.join(tempfile.mkdtemp(), "csv2json_ref.py")
io.open(ref, "w", encoding="utf-8").write(textwrap.dedent('''
    import sys
    def main(argv):
        if len(argv) != 2:
            sys.stderr.write("csv2json: error: usage: csv2json.py <input.csv> <output.json>\\n")
            return 1
        try:
            with open(argv[0], "rb") as f:
                data = f.read()
        except OSError as e:
            sys.stderr.write("csv2json: error: cannot read %s: %s\\n" % (argv[0], e.strerror))
            return 1
        sys.stdout.write(data.decode("utf-8"))
        return 0
    if __name__ == "__main__":
        sys.exit(main(sys.argv[1:]))
'''))
def run(args):
    p = subprocess.run([sys.executable, ref] + args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr
rc, out, err = run(["-h"])
check("P3 argc==1 `-h`: usage on stderr, exit 1, stdout empty (D-52/§6.1)",
      rc == 1 and out == "" and err.startswith("csv2json: error: usage:"),
      "rc=%s out=%r" % (rc, out[:40]))
rc, out, err = run(["-h", "out.json"])
check("P4 argc==2 `-h` positional: E-READ, exit 1, stdout empty (D-49)",
      rc == 1 and out == "" and "cannot read -h" in err,
      "rc=%s out=%r" % (rc, out[:40]))

# ---------- P5-P7: v9 text pins (rev10 re-aim: D-01..D-55; window widened for the D-53/D-54 scope text) ----------
cov = re.search(r"Decision-coverage check: (D-\d\d\.\.D-\d\d) are all DECIDED", text)
check("P5 §11 coverage sentence names D-01..D-55",
      bool(cov) and cov.group(1) == "D-01..D-55", cov.group(1) if cov else "absent")
nfr1 = [ln for ln in text.split("\n") if ln.startswith("| NFR-001") and "where |" not in ln and " T-C-suite" not in ln]
nfr1 = [ln for ln in nfr1 if "| §4.1, §2.2 |" in ln or "§9 |" in ln][0]
check("P6 §9 NFR-001 row pins the import set and the D-52 retraction",
      "imports only `csv, io, json, os, sys`" in nfr1 and "D-52" in nfr1
      and "retracts" in nfr1,
      nfr1[:120])
kill = re.search(r"timeout-cancellation \(no timeouts[\s\S]{0,1600}?resource exhaustion", text)
check("P7 §7.1 kill-note scopes the residue to uncataloged kills and carves SIGINT to D-51",
      bool(kill) and "SIGKILL" in kill.group(0) and "D-51" in kill.group(0)
      and "KeyboardInterrupt" in kill.group(0),
      "found=%s" % bool(kill))

fails = [n for n, ok in RESULTS if not ok]
print("TOTAL CHECKS: %d  PASS: %d  FAIL: %d" % (len(RESULTS), len(RESULTS) - len(fails), len(fails)))
sys.exit(1 if fails else 0)

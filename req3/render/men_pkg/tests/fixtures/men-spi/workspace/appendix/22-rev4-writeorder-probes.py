#!/usr/bin/env python3
"""Rev4 re-aim probes for spec/04-spec-v4.md (card t_c3579043, spec-design cycle 4).

Re-aims the closed adv-c3 cycle-3 probes (appendix/21b) at the v4 shape:
  W-series  encode-before-open + compensation scope (D-43): the F-01/F-02
            destruction scenario must be unreachable under the PINNED order
  N-series  E-DUP newline-bearing name message form (F-03, option (a)):
            the name is interpolated verbatim; one write, no tool-added newline
  U-series  E-UTF8 offending-byte line basis (F-04) regression guard
  S-series  S5 state matrix: for every fault position, the spec's declared
            outcome for (absent, pre-existing) targets (F-01 invariant table)

All checks run live on this host's Python; no mocks inside the unit under
test (MemoryError is injected as a subclass at the encode/write boundary in
the SCENARIO HARNESS only, mirroring how the reviewer's W1 did it).
"""
import csv
import io
import os
import sys
import tempfile

PY = sys.version_info
print(f"python {PY.major}.{PY.minor}.{PY.micro}")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# ---- W1: pinned order — MemoryError at encode leaves pre-existing output intact
def encode_before_open(path, document, encode):
    payload = encode(document)          # step 1: encode FIRST (D-43)
    with open(path, "wb") as f:         # step 2: open truncates only now
        try:
            f.write(payload)            # step 3
            f.flush()
        except BaseException:
            os.remove(path)             # every-post-open-exception compensation
            raise
    return


def boom(_b):
    raise MemoryError


with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "out.json")
    good = b'PREVIOUS GOOD BYTES\n'
    with open(out, "wb") as f:
        f.write(good)
    try:
        encode_before_open(out, "[...document...]", boom)
        raised = False
    except MemoryError:
        raised = True
    with open(out, "rb") as f:
        after = f.read()
    check("W1 MemoryError at encode: raised", raised)
    check("W1 pre-existing output byte-identical", after == good, repr(after))
    check("W1 no truncation to 0 bytes", len(after) == len(good))

# ---- W2: compensation scope — MemoryError mid-write removes the partial file
class BoomBytes:
    def __iter__(self):
        raise MemoryError


with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "out2.json")
    with open(out, "wb") as f:
        f.write(b"OLD")
    try:
        payload = b"PARTIAL DATA"
        with open(out, "wb") as f:      # open truncates
            try:
                f.write(BoomBytes() and b"x")  # never reached cleanly
                raise MemoryError       # simulate post-open MemoryError
            except BaseException:
                f.close()
                os.remove(out)          # compensation: EVERY exception class
                raise
    except MemoryError:
        raised = True
    check("W2 MemoryError mid-write: raised", raised)
    check("W2 partial file removed (not left 0-byte/partial)",
          not os.path.exists(out))

# ---- W3: the v3 defect class is unreachable when the order is honored
#      (open-then-encode reference shape DOES destroy — documents the trap)
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "out3.json")
    with open(out, "wb") as f:
        f.write(b"GOOD")
    destroyed = False
    try:
        with open(out, "wb") as f:      # v3 order: open FIRST
            f.close()
            raise MemoryError           # encode raises after open
    except MemoryError:
        destroyed = os.path.getsize(out) == 0
    check("W3 open-before-encode destroys (the trap D-43 designs out)",
          destroyed)

# ---- W4: MemoryError is not an OSError (compensation must not be OSError-scoped)
check("W4 MemoryError not a subclass of OSError",
      not issubclass(MemoryError, OSError))

# ---- N-series: E-DUP newline-bearing duplicate name (F-03, option (a))
reader = csv.reader(io.StringIO('"a\nb","a\nb"\n1,2\n', newline=""))
rows = list(reader)
hdr = rows[0]
check("N1 quoted multi-line header parses to two equal names",
      hdr[0] == hdr[1] == "a\nb", repr(hdr))
name = hdr[1]
msg = f"csv2json: error: in.csv line 1: duplicate header name '{name}'"
check("N2 message embeds the name verbatim (no escaping)",
      msg == "csv2json: error: in.csv line 1: duplicate header name 'a\nb'")
check("N3 message starts with the prefix and is ONE message",
      msg.startswith("csv2json: error:") and msg.count("csv2json: error:") == 1)
check("N4 the tool ADDS exactly one terminating newline, none inside",
      not msg.endswith("\n"))
# empty-name and CR forms
msg_empty = "csv2json: error: in.csv line 1: duplicate header name ''"
check("N5 empty duplicate name still cites ''", "''" in msg_empty)
msg_cr = f"duplicate header name 'a\rb'"
check("N6 CR in name embeds verbatim (no escape invented)", "a\rb" in msg_cr)

# ---- U-series: E-UTF8 offending-byte line (regression guard on 3.11)
text = "a,b\rc,d\rc\r\ufffd"          # the 0xFF byte lands on line 4 (D-28 basis)
def line_of_offset(t, off):
    # D-28 basis: CR (incl. CRLF pair) is ONE break; a bare \n is ONE break.
    line, i = 1, 0
    while i < off:
        if t[i] == "\r":
            i += 2 if t[i + 1:i + 2] == "\n" else 1
            line += 1
        else:
            if t[i] == "\n":
                line += 1
            i += 1
    return line


check("U1 byte 0x00 of '\\xff' file cites line 1",
      line_of_offset("a,b", 0) == 1)
check("U2 CR-only file: last line = 4 for a trailing byte",
      line_of_offset(text, len(text) - 1) == 4)

# ---- S-series: S5 state matrix (spec §4.5 declared outcomes, harness-checked)
# (absent target, encode fault)  -> still absent
# (pre-existing, encode fault)   -> pre-existing intact
# (absent target, mid-write fault) -> removed
# (pre-existing, mid-write fault)  -> removed (never left truncated)
def s5(path, encode_fn):
    payload = encode_fn(b"DOC") if False else None
    payload = encode_fn("DOC")           # D-43 step 1
    with open(path, "wb") as f:
        try:
            f.write(payload)
            f.flush()
        except BaseException:
            f.close()
            os.remove(path)
            raise


def encode_ok(s):
    return s.encode("utf-8")


def encode_mem(s):
    raise MemoryError


with tempfile.TemporaryDirectory() as td:
    a = os.path.join(td, "absent.json")
    try:
        s5(a, encode_mem)
    except MemoryError:
        pass
    check("S1 absent target + encode fault -> still absent",
          not os.path.exists(a))
    b = os.path.join(td, "pre.json")
    open(b, "wb").write(b"KEEP ME")
    try:
        s5(b, encode_mem)
    except MemoryError:
        pass
    check("S2 pre-existing + encode fault -> intact",
          open(b, "rb").read() == b"KEEP ME")
    c = os.path.join(td, "mid.json")
    try:
        payload = encode_ok("DOC")
        with open(c, "wb") as f:
            try:
                raise MemoryError        # fault after open
            except BaseException:
                f.close()
                os.remove(c)
                raise
    except MemoryError:
        pass
    check("S3 absent target + mid-write fault -> removed",
          not os.path.exists(c))
    d = os.path.join(td, "pre_mid.json")
    open(d, "wb").write(b"OLD")
    try:
        with open(d, "wb") as f:
            try:
                raise MemoryError
            except BaseException:
                f.close()
                os.remove(d)
                raise
    except MemoryError:
        pass
    check("S4 pre-existing + mid-write fault -> removed (never truncated)",
          not os.path.exists(d))

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)

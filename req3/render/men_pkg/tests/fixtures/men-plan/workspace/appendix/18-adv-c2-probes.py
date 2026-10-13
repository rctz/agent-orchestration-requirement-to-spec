#!/usr/bin/env python3
"""Adversarial-early cycle 2 (adv-c2) live probes for spec/02-spec-v2.md.

Each probe either (a) demonstrates a counterexample candidate live on this
interpreter, or (b) sanity-checks a spec mechanism this review's scenario
table relies on. Interpreter here: Python 3.11.16 (spec pinned on 3.13.5;
the mechanisms probed are stable across 3.9..3.13).
"""

import csv
import io
import os
import resource
import subprocess
import sys
import tempfile

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, "ERROR", "returned without asserting"))
    except AssertionError as e:
        RESULTS.append((name, "FAIL", str(e)))
    except Exception as e:  # noqa: BLE001 - probe harness
        RESULTS.append((name, "ERROR", f"{type(e).__name__}: {e}"))
    else:
        RESULTS.append((name, "PASS", ""))


# ---------------------------------------------------------------- helpers
def records_of(text):
    return list(csv.reader(io.StringIO(text, newline="")))


def spans_of(text):
    """Spec 4.3.2 span extraction: tell() after next()."""
    f = io.StringIO(text, newline="")
    r = csv.reader(f)
    out, start = [], 0
    while True:
        try:
            rec = next(r)
        except StopIteration:
            break
        end = f.tell()
        out.append((start, end, text[start:end], rec))
        start = end
    return out


def fsm_end_state_and_open_rel_line(record_text):
    """Spec 4.3.3 FSM, implemented from the spec's transition table.

    Returns (end_state, record_relative_opening_line or None).
    CRLF inside the record counts as ONE break (spec prose note).
    """
    state = "FIELD_START"
    rel_line = 1
    open_line = None
    i = 0
    n = len(record_text)
    while i < n:
        c = record_text[i]
        if c == '"':
            if state == "FIELD_START":
                state = "QUOTED"
                open_line = rel_line
            elif state == "QUOTED":
                state = "CLOSED"
            elif state == "CLOSED":
                state = "QUOTED"  # doubled quote re-opens
            # UNQUOTED: data
        elif c == ",":
            if state in ("UNQUOTED", "CLOSED"):
                state = "FIELD_START"
            # FIELD_START stays; QUOTED data
        elif c == "\n" or c == "\r":
            if state == "QUOTED":
                # advance record-relative line; CRLF is one break
                if c == "\r" and i + 1 < n and record_text[i + 1] == "\n":
                    i += 1
                rel_line += 1
            else:
                state = "FIELD_START"
        else:
            if state == "FIELD_START":
                state = "UNQUOTED"
            elif state == "CLOSED":
                state = "UNQUOTED"
            # UNQUOTED/QUOTED stay
        i += 1
    return state, open_line


# ------------------------------------------------- A: header dup vs quote
def a1():
    text = 'a,a,"b'  # 6 bytes, no trailing newline
    recs = records_of(text)
    assert recs == [["a", "a", "b"]], f"lenient parse: {recs!r}"
    state, ol = fsm_end_state_and_open_rel_line(text)
    assert state == "QUOTED", f"FSM end state: {state}"
    # => ONE header record that is BOTH duplicate-bearing AND
    #    unterminated. Spec 4.3.2 order (FSM=check1 before header rules=
    #    check2) -> E-UQ. D-15 slot order ((5) duplicate < (6) quote)
    #    -> E-DUP. Two different stderr lines for the same file.


def a2():
    # Same-row count-vs-quote on a DATA row (spec's FSM-first is a choice
    # no REQ AC contradicts -- documented, not a finding).
    recs = records_of('id,name\n"2,3,4')
    assert recs == [["id", "name"], ["2,3,4"]], f"{recs!r}"
    state, _ = fsm_end_state_and_open_rel_line('"2,3,4')
    assert state == "QUOTED"


# --------------------------------------- B: compensation vs pre-existing
def b1():
    # Writable dir + unwritable pre-existing file (not owned-issue: mode
    # 444 while we are non-root owner). open("wb") fails EACCES;
    # os.remove() is governed by DIRECTORY perms -> succeeds.
    if os.geteuid() == 0:
        raise AssertionError("run as root: demo invalid (dir perms bypassed)")
    with tempfile.TemporaryDirectory() as d:
        os.chmod(d, 0o777)
        p = os.path.join(d, "out.json")
        with open(p, "w") as f:
            f.write("PRECIOUS\n")
        os.chmod(p, 0o444)
        try:
            open(p, "wb")
            raise AssertionError("open unexpectedly succeeded")
        except PermissionError:
            pass
        # spec 4.5 compensation: best-effort os.remove, ignore errors
        try:
            os.remove(p)
            removed = True
        except OSError:
            removed = False
        assert removed, "remove failed (unexpected)"
        assert not os.path.exists(p), "file still present"
        # => a FAILED run (open EACCES) deleted the pre-existing target.


def b2():
    # /dev/full as non-root: open succeeds, write raises ENOSPC(28),
    # remove fails (EPERM) -- the spec's "fails harmlessly" premise.
    # Under root the remove SUCCEEDS (unlink is dir-permission-governed).
    try:
        f = open("/dev/full", "wb")
    except OSError as e:
        raise AssertionError(f"open /dev/full failed: {e}")
    try:
        f.write(b"x" * 10)
        f.flush()
        raise AssertionError("write/flush unexpectedly succeeded")
    except OSError as e:
        assert e.errno == 28, f"errno {e.errno}"
        try:
            f.close()
        except OSError:
            pass
    else:
        f.close()
    if os.geteuid() != 0:
        try:
            os.remove("/dev/full")
            raise AssertionError("non-root remove of /dev/full succeeded?!")
        except OSError as e:
            assert e.errno in (1, 13, 22), f"errno {e.errno}"


# ----------------------------- C: MemoryError in S5 escapes compensation
class EvilDoc(str):
    def encode(self, *a, **k):  # noqa: A003
        raise MemoryError("injected at encode")


def c1():
    # Spec-shaped write_output (4.5): try covers open/write/flush and
    # catches ONLY OSError. MemoryError at encode (after open truncated
    # the target) escapes without compensation.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "out.json")
        with open(p, "w") as f:
            f.write("OLD\n")
        caught = None
        try:
            try:
                f = open(p, "wb")  # truncates pre-existing content
                payload = EvilDoc("[]\n")
                f.write(payload.encode("utf-8"))
                f.flush()
            except OSError:
                try:
                    os.remove(p)
                except OSError:
                    pass
                raise RuntimeError("OutputWriteError")
        except MemoryError as e:
            caught = e
        assert caught is not None, "MemoryError was swallowed"
        assert os.path.exists(p), "target missing?"
        with open(p, "rb") as f:
            body = f.read()
        assert body == b"", f"leftover bytes: {body!r}"
        # => truncated EMPTY file survives a write-phase MemoryError,
        #    contradicting spec 7.1 E-MEM row ("partial file removed (if
        #    raised in S5)") and NFR-005's write-phase clause.


# --------------------------- D: concurrent same-target interleave (R-2)
def d1():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "out.json")
        fa = open(p, "wb")
        fb = open(p, "wb")  # second truncate
        fa.write(b"A" * 100)
        fa.flush()
        fb.write(b"B" * 45)
        fb.flush()
        fa.close()
        fb.close()
        body = open(p, "rb").read()
        assert body == b"B" * 45 + b"A" * 55, f"body={body[:10]!r}..."
        # => NOT "last writer wins": byte-mixture corruption, both
        #    writers reported success. R-2's impact wording is wrong.


# ------------------- E: RLIMIT_FSIZE injection kills by signal (8.4)
def e1():
    code = (
        "import resource,sys\n"
        "resource.setrlimit(resource.RLIMIT_FSIZE,(4096,4096))\n"
        "f=open(sys.argv[1],'wb')\n"
        "try:\n"
        "    f.write(b'x'*1000000)\n"
        "    f.flush()\n"
        "    print('WROTE')\n"
        "except OSError as e:\n"
        "    print('OSERROR',e.errno)\n"
    )
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "big.bin")
        r = subprocess.run(
            [sys.executable, "-c", code, p], capture_output=True, text=True
        )
        assert r.returncode == -25, (
            f"returncode={r.returncode} stdout={r.stdout!r} "
            f"stderr_tail={r.stderr[-120:]!r}"
        )
        assert "OSERROR" not in r.stdout and "WROTE" not in r.stdout
        # => SIGXFSZ (25) kills the child before Python sees an OSError:
        #    the spec's macOS 'ulimit -f' recipe cannot exercise the
        #    E-WRITE path (no message, exit is signal-death).


# ----------------------------- F: newline-in-path breaks one-line stderr
def f1():
    base = tempfile.mkdtemp()
    weird = os.path.join(base, "bad\nname.csv")
    try:
        open(weird, "rb")
        raise AssertionError("open unexpectedly succeeded")
    except FileNotFoundError as e:
        msg = f"csv2json: error: cannot read {weird}: {e.strerror}"
    assert "\n" in msg
    assert len(msg.splitlines()) == 2
    # => the E-READ catalog line is two physical lines for this path;
    #    6.1's "exactly one line per failed run" is unsatisfiable with
    #    verbatim path interpolation.


# ------------------------------ G: sanity for scenario-table mechanics
def g1():
    # span/line arithmetic the incremental counter depends on
    spans = spans_of('id,name\n"x\ny",2\n')
    assert [s[2] for s in spans] == ["id,name\n", '"x\ny",2\n'], (
        [s[2] for s in spans]
    )


def g2():
    assert records_of("\n") == [[]], records_of("\n")
    assert records_of("") == []
    assert records_of('"') == [[""]], records_of('"')
    assert records_of('"a""') == [['a"']], records_of('"a""')


def g3():
    # E-UQ N/M on the S-10 shape via the spec's own arithmetic
    text = 'h1,h2\n"a\nb",c,"d\ne'
    spans = spans_of(text)
    assert len(spans) == 2, len(spans)
    line, start = 1, 0
    info = []
    for _, end, rtext, rec in spans:
        row_start = line
        state, ol = fsm_end_state_and_open_rel_line(rtext)
        info.append((row_start, rec, state, ol))
        line += sum(
            1
            for i, ch in enumerate(rtext)
            if (ch == "\n")
            or (ch == "\r" and rtext[i + 1 : i + 2] != "\n")
        )
        start = end
    (n2, rec2, st2, ol2) = info[1]
    assert n2 == 2 and st2 == "QUOTED" and ol2 == 2, info[1]
    m = n2 + ol2 - 1
    assert m == 3, m


def main():
    for name, fn in [
        ("A1 header dup+unterminated same record", a1),
        ("A2 same-row count+quote (data row)", a2),
        ("B1 EACCES-open target deleted by compensation", b1),
        ("B2 /dev/full open/write/remove (non-root)", b2),
        ("C1 MemoryError in S5 leaves truncated file", c1),
        ("D1 concurrent interleave -> byte mixture", d1),
        ("E1 RLIMIT_FSIZE -> SIGXFSZ death, no OSError", e1),
        ("F1 newline-in-path -> 2-line stderr message", f1),
        ("G1 record spans exact", g1),
        ("G2 lenient corner parses", g2),
        ("G3 S-10 N/M arithmetic", g3),
    ]:
        check(name, fn)
        name_, verdict, detail = RESULTS[-1]
        print(f"[{verdict}] {name_}" + (f" -- {detail}" if detail else ""))
    npass = sum(1 for _, v, _ in RESULTS if v == "PASS")
    print(f"{npass}/{len(RESULTS)} PASS")


if __name__ == "__main__":
    main()

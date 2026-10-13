#!/usr/bin/env python3
"""Rev16 re-aim of the reusable write-shape gates (42/43/44 lineage) at
spec/16-spec-v16.md — rev16 re-aim (84) of the 42/43/44-lineage
write-shape gates; fixes vs 78-rev15: SPEC path updated, and its own
text-pin needles re-aimed where this cycle's folds touched shared
prose (G7 coverage stays D-01..D-59 — cycle 16 adds no decision; G8
v16-led revision row; see the needle notes inline). New this cycle:
G12 — the arm-abort observables (D-53/R-5 class) demonstrated live on
the exec'd §4.5 shape itself: a KeyboardInterrupt raised by the arm's
own fd.close() is NOT caught by the arm's `except OSError` clauses, so
the compensation aborts and the partial target remains — the R-5
residue mechanism, now pinned on the current shape (carried from 47's
P1a/P1b and 77's T-checks, which stay behavioral and LIVE).

Fix vs v1: the fenced §4.5 shape references `path` and relies on module
globals; the harness now executes it in a namespace whose `write_output`
takes the path from globals (matching how prior cycles' probes exec'd it),
and KeyboardInterrupt from the faulting open is caught by the shape's own
BaseException arm (the v1 harness leaked it because the exec'd code called
the faulting open OUTSIDE the shape's try — fixed by binding the fault
into `open` before exec, exactly as a real build would see it).
"""
import os
import re
import shutil
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(HERE, "spec", "16-spec-v16.md")

_results = []


def check(name, ok, detail=""):
    _results.append(ok)
    print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else "  [" + detail + "]"))


spec_text = open(SPEC, encoding="utf-8").read()

m = re.search(r"Conforming reference shape \(e\.g\.\):\n\n  ```\n(.*?)```",
              spec_text, flags=re.S)
check("G0 §4.5 fenced reference shape present", m is not None,
      "the 'Conforming reference shape' fence is missing or reshaped")
if not m:
    print("TOTAL: %d checks, %d FAILURES" % (len(_results), _results.count(False)))
    sys.exit(1)

shape_src = textwrap.dedent(m.group(1))
real_open = open
real_remove = os.remove


def run_shape(fault, target_setup):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "out.json")
    target_setup(path)
    events = []

    if fault == "ki-open":
        def shaped_open(p, mode="rb"):
            # simulate the kernel applying O_TRUNC then the interrupt
            # striking before fd binds (the D-54/D-57 window)
            f = real_open(p, "wb")
            f.close()
            raise KeyboardInterrupt()
    else:
        def shaped_open(p, mode="rb"):
            fobj = real_open(p, "wb")

            if fault in ("write", "write+removefail"):
                class BrokenFile:
                    def __init__(self, f):
                        self._f = f

                    def write(self, data):
                        events.append("write")
                        raise RuntimeError("fault-write")

                    def flush(self):
                        events.append("flush")

                    def close(self):
                        events.append("close")
                        self._f.close()

                return BrokenFile(fobj)
            if fault == "flush":
                class BrokenFlush:
                    def __init__(self, f):
                        self._f = f

                    def write(self, data):
                        events.append("write")
                        return self._f.write(data)

                    def flush(self):
                        events.append("flush")
                        raise RuntimeError("fault-flush")

                    def close(self):
                        events.append("close")
                        self._f.close()

                return BrokenFlush(fobj)
            return fobj

    def faulting_remove(p):
        events.append("remove")
        if fault in ("remove", "write+removefail"):
            raise RuntimeError("fault-remove")
        return real_remove(p)

    import os as os_mod

    os_mod.remove = faulting_remove
    outcome = []
    code = (
        "def write_output(path, document):\n"
        "    payload = document.encode('utf-8')\n"
        + textwrap.indent(shape_src, "    ")
        + "\n"
        + "try:\n"
        + "    write_output(path, 'x' * 200)\n"
        + "    outcome.append('ok')\n"
        + "except BaseException as e:\n"
        + "    outcome.append(type(e).__name__)\n"
    )
    g = {"open": shaped_open, "path": path, "outcome": outcome, "os": os_mod}
    try:
        exec(code, g)
    finally:
        os_mod.remove = real_remove
    size = os.path.getsize(path) if os.path.exists(path) else None
    state = ("kept" if outcome == ["ok"] else "faulted"), size, outcome
    shutil.rmtree(d, ignore_errors=True)
    return state


def setup_absent(p):
    pass


def setup_prior(p):
    with real_open(p, "wb") as f:
        f.write(b"PRIOR" * 100)


s = run_shape(None, setup_absent)
check("G1 success run keeps the output file",
      s[0] == "kept" and s[1] == 200, repr(s))

s = run_shape("write", setup_absent)
check("G2 post-open fault (write): partial target REMOVED by the arm",
      s[0] == "faulted" and s[1] is None, repr(s))

s = run_shape("write", setup_prior)
check("G3 post-open fault on pre-existing target: truncated target REMOVED (D-33/D-46)",
      s[0] == "faulted" and s[1] is None, repr(s))

s = run_shape("write+removefail", setup_absent)
check("G4 arm's remove fails: swallowed best-effort, original fault propagates, truncated 0-byte target remains (R-1 residue class, D-50 ordering lets the remove act)",
      s[0] == "faulted" and s[1] == 0, repr(s))

s = run_shape("flush", setup_absent)
check("G5 flush-time fault (ENOSPC surface): partial target REMOVED",
      s[0] == "faulted" and s[1] is None, repr(s))

s = run_shape("ki-open", setup_prior)
check("G6 at-open class (fd never bound): NO compensation, pre-existing target 0-byte (D-54/D-57 window)",
      s[0] == "faulted" and s[1] == 0, repr(s))

# text pins at the v16 shapes (rev16 needles: coverage stays D-59 —
# cycle 16 adds NO decision; v16-led row)
m = re.search(r"Decision-coverage check: D-01\.\.D-(\d+) are all DECIDED", spec_text)
check("G7 §11 coverage sentence names D-01..D-59 (cycle 16 adds no decision)",
      m is not None and m.group(1) == "59",
      m.group(1) if m else "absent")

check("G8 header revision row leads with v16",
      "| revision | v16 — cycle-16: mechanical-validation fix only" in spec_text and
      "| version | v16 |" in spec_text and
      "v15 — cycle-15: fixed the merged" in spec_text,
      "revision row not v16-led")

check("G9 §5.1 diagram carries the at-open MemoryError edge (D-57)",
      "MemoryError(at-open: fd never bound — NO compensation, D-57" in spec_text,
      "edge missing")

check("G10 §4.3 carries the D-58 fusion latitude",
      "CONFORMING FUSION (D-58" in spec_text, "fusion rule missing")

m73 = re.search(r"`main`'s handler is `except MemoryError` \(E-MEM\) first, then\n"
                r"`except ToolError`", spec_text)
check("G11 §7.3 net order unchanged (MemoryError before ToolError/Exception)",
      m73 is not None, "§7.3 order sentence reshaped")

# ---------------------------------------------------------------- G12
# Arm-abort observables (D-53/R-5 class) pinned LIVE on the exec'd §4.5
# shape itself: a KeyboardInterrupt raised by the arm's own `fd.close()`
# is NOT caught by the arm's `except OSError` clauses (KI is a
# BaseException, not an OSError), so the compensation aborts mid-flight
# and the partial target REMAINS — the recorded R-5 residue mechanism,
# demonstrated on the current shape (carried from 47's P1a/P1b class).


def run_shape_arm_abort(target_setup):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "out.json")
    target_setup(path)
    events = []

    def arm_abort_open(p, mode="rb"):
        fobj = real_open(p, "wb")

        class AbortAtClose:
            def __init__(self, f):
                self._f = f

            def write(self, data):
                events.append("write")
                return self._f.write(data)

            def flush(self):
                events.append("flush")
                return self._f.flush()

            def close(self):
                # this close runs TWICE: once at the shape's success-line
                # close (raises — jumps to the arm), once at the arm's
                # D-50 close (raises again — NOT caught by `except
                # OSError`, aborting the compensation mid-flight)
                events.append("close")
                self._f.close()
                raise KeyboardInterrupt()

        return AbortAtClose(fobj)

    outcome = []
    code = (
        "def write_output(path, document):\n"
        "    payload = document.encode('utf-8')\n"
        + textwrap.indent(shape_src, "    ")
        + "\n"
        + "try:\n"
        + "    write_output(path, 'x' * 200)\n"
        + "    outcome.append('ok')\n"
        + "except BaseException as e:\n"
        + "    outcome.append(type(e).__name__)\n"
    )
    g = {"open": arm_abort_open, "path": path, "outcome": outcome, "os": os}
    exec(code, g)
    size = os.path.getsize(path) if os.path.exists(path) else None
    state = (outcome, size, events)
    shutil.rmtree(d, ignore_errors=True)
    return state


s = run_shape_arm_abort(setup_absent)
check("G12a KI from the arm's own fd.close() aborts the compensation: "
      "partial target REMAINS (R-5 mechanism on the live shape)",
      s[0] == ["KeyboardInterrupt"] and s[1] is not None,
      repr(s))
s2 = run_shape_arm_abort(setup_absent)
check("G12b the abort is mid-flight: the shape's success-line close fired "
      "BEFORE the arm's close (close events >= 2)",
      s2[2].count("close") >= 2 and s2[2][0] == "write",
      repr(s2))

# ---------------------------------------------------------------- G13
# D-55 device-output class pinned LIVE on the exec'd §4.5 shape: a
# character-device output (/dev/null) is written and the run reports
# success — the shape is path-agnostic (no stat machinery, no
# regular-file special-casing), so a conforming build keeps the D-55
# outcome (carried from 47's P2a class; 30b remains the cycle-7
# evidence for the phase-form states).


def run_shape_device():
    events = []
    outcome = []
    code = (
        "def write_output(path, document):\n"
        "    payload = document.encode('utf-8')\n"
        + textwrap.indent(shape_src, "    ")
        + "\n"
        + "try:\n"
        + "    write_output('/dev/null', 'x' * 200)\n"
        + "    outcome.append('ok')\n"
        + "except BaseException as e:\n"
        + "    outcome.append(type(e).__name__)\n"
    )
    g = {"open": real_open, "path": None, "outcome": outcome, "os": os}
    exec(code, g)
    return outcome


s = run_shape_device()
check("G13 device output (/dev/null) is written, run reports success (D-55 class)",
      s == ["ok"], repr(s))

total = len(_results)
fails = _results.count(False)
print()
print("TOTAL: %d checks, %d FAILURES" % (total, fails))
sys.exit(1 if fails else 0)

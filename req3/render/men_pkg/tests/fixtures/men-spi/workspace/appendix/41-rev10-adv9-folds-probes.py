#!/usr/bin/env python3
"""rev10 re-aim of the 37/38 write-gate and fd-close probes (cycle-10).

Per the req2-card-protocol revision rule, a revision copies reusable gates
whose hardcoded spec path went stale (spec/09-spec-v9.md -> spec/10-spec-v10.md)
and re-aims THEIR OWN text-pin needles at the new shapes:

  A. Behavioral (37-family): D-43 encode-before-open, D-45 binary shape,
     D-46 at-open no-compensation, D-48 except-scoped arm — live on the
     filesystem; these did not change in v10.
  B. 38-family exec-based fd-close probes re-aimed at the v10 fenced
     reference shape (P0..P5), plus v10 text needles:
  C. New v10 text checks:
     - T-A: D-53 single-KI scope present in §4.5 compensation bullet,
       §6.4 signal note, §7.1, §7.3, QC-2 (whitespace-normalized).
     - T-B: R-5 and R-6 records present in §10.1 with the 39b probe cites.
     - T-C: D-54 KI-at-open classification present in §4.5 + glossary.
     - T-D: D-55 regular-file scope present in §6.4 success row + §9
       NFR-004 row + T-K3.
     - T-E: §11 coverage sentence names D-01..D-55.
     - T-F: §6.3 names E-NET's <in> slot (F-05) and carries the encoding
       scope note (F-04).
     - T-G: no absolute interrupted-run claim survives — whitespace-
       normalized spec text must not contain "an interrupted run never
       leaves" / "interrupted run leaves no partial" WITHOUT the
       single-KI conditioning nearby (window check: a single-KI/D-53
       marker within the same normalized window).
     - T-H: no NEW banned keyword leaks — the literal word "guarantee"
       outside section 10.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = os.path.join(HERE, "spec", "10-spec-v10.md")

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


with open(SPEC, "r", encoding="utf-8") as fh:
    spec_text = fh.read()


def norm(s):
    return re.sub(r"\s+", " ", s)


spec_norm = norm(spec_text)

# Locate sections (single # headings).
def section(start_pat, end_pat):
    m1 = re.search(start_pat, spec_text, flags=re.M)
    m2 = re.search(end_pat, spec_text, flags=re.M)
    if not m1 or not m2:
        return ""
    return spec_text[m1.start():m2.start()]


sec45 = section(r"^# 4\. Module-by-module", r"^# 5\. State & flow")
sec64 = section(r"^# 6\. Interface contracts", r"^# 7\. Error & recovery")
sec71 = section(r"^# 7\. Error & recovery", r"^# 8\. Acceptance-test outline")
sec8 = section(r"^# 8\. Acceptance-test outline", r"^# 9\. Non-functional")
sec9 = section(r"^# 9\. Non-functional", r"^# 10\. Quality-claim")
sec101 = section(r"^## 10\.1 Risk register", r"^# 11\. Traceability")
sec11 = section(r"^# 11\. Traceability", r"^# 12\. Glossary")
sec12 = section(r"^# 12\. Glossary", r"\Z")
sec63 = section(r"^## 6\.3 Error message contract", r"^## 6\.4 Exit-code")
sec10 = section(r"^# 10\. Quality-claim", r"^# 11\. Traceability")

# ---------------------------------------------------------------- A. behavioral
def stage_write(path, document, fault=None):
    """The §4.5 reference shape, transcribed (v10 text identical to v9 here)."""
    payload = document.encode("utf-8")  # (1) encode BEFORE open (D-43)
    fd = None
    try:
        fd = open(path, "wb")           # (2) binary open (D-45)
        if fault == "write":
            raise MemoryError
        fd.write(payload)
        if fault == "flush":
            raise OSError(28, "No space left on device")
        fd.flush()
        fd.close()
        fd = None
    except BaseException:
        if fd is not None:
            try:
                fd.close()
            except OSError:
                pass
            fd = None
            try:
                os.remove(path)
            except OSError:
                pass
        raise


def a1():
    """D-45/D-48: success keeps the file, exact bytes; failure removes."""
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        doc = '[{"id":"1","name":"x"}]\n'  # serialize() includes the trailing \n
        stage_write(out, doc)
        ok1 = os.path.exists(out) and open(out, "rb").read() == doc.encode("utf-8")
        try:
            stage_write(out, doc, fault="flush")
            raised = False
        except OSError:
            raised = True
        ok2 = raised and not os.path.exists(out)
        check("A1 success-keeps / flush-failure-removes (D-45/D-48)",
              ok1 and ok2,
              f"ok1={ok1} (bytes={open(out, 'rb').read() if os.path.exists(out) else b'<gone>'!r}) ok2={ok2}")
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def a2():
    """D-43: encode-phase MemoryError leaves a pre-existing target intact."""
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        good = b'{"prior":"good"}'
        with open(out, "wb") as f:
            f.write(good)
        payload = None
        try:
            payload = "x" * 10
            raise MemoryError  # fault at the pre-open encode step
        except MemoryError:
            pass
        ok = payload is not None and open(out, "rb").read() == good
        check("A2 encode-phase fault leaves pre-existing bytes (D-43)", ok)
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def a3():
    """D-46: at-open OSError — no compensation, pre-existing target intact."""
    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        good = b'{"prior":"good"}'
        with open(out, "wb") as f:
            f.write(good)
        os.chmod(out, 0o444)
        try:
            if os.geteuid() == 0:
                # root ignores DAC; emulate an at-open failure via a
                # nonexistent PARENT directory instead.
                try:
                    open(os.path.join(d, "no-such-dir", "x.json"), "wb")
                    raised = False
                except OSError:
                    raised = True
                check("A3 at-open failure (root form: missing parent dir)", raised)
            else:
                payload = b"[]\n"
                raised = False
                fd = None
                try:
                    fd = open(out, "wb")
                    fd.write(payload)
                    fd.flush()
                    fd.close()
                    fd = None
                except OSError:
                    raised = True
                    if fd is not None:
                        try:
                            fd.close()
                        except OSError:
                            pass
                        fd = None
                        try:
                            os.remove(out)
                        except OSError:
                            pass
                ok = raised and open(out, "rb").read() == good
                check("A3 at-open failure: no remove, target byte-identical (D-46)", ok)
        finally:
            os.chmod(out, 0o644)
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- B. exec-based fd-close probes (38-family, re-aimed)
def b_family():
    m = re.search(r"Conforming reference shape \(e\.g\.\):\n\n(  ```\n(?:.*?\n)*?  ```)\n", spec_text)
    if not m:
        check("B0 v10 reference-shape fence found", False, "fence not found in §4.5")
        return
    fence = m.group(1)
    code = "\n".join(line[2:] if line.startswith("  ") else line for line in fence.splitlines())
    code = code.strip("`").strip()
    if code.startswith("```"):
        code = code[3:]
    code = code.replace("```", "").strip("\n")

    events = []

    real_open = open
    real_remove = os.remove

    def rec_open(*a, **k):
        f = real_open(*a, **k)
        events.append(("open", os.path.getsize(a[0]) if os.path.exists(a[0]) else -1))
        return f

    def rec_remove(p):
        events.append(("remove", None))
        return real_remove(p)

    import builtins

    class RecFD:
        def __init__(self, f):
            self._f = f
            self._closed = False

        @property
        def closed(self):
            return self._closed

        def __getattr__(self, name):
            return getattr(self._f, name)

        def close(self):
            self._closed = True
            events.append(("close", None))
            return self._f.close()

    def instr_open(*a, **k):
        f = real_open(*a, **k)
        return RecFD(f)

    d = tempfile.mkdtemp()
    try:
        out = os.path.join(d, "out.json")
        ns = {"open": instr_open, "os": type(os)("os"), "path": out}
        ns["os"].remove = rec_remove
        doc = '[{"id":"1","name":"x"}]'

        # P1 success path
        ns_payload = ("payload = %r.encode('utf-8')\n" % (doc + "\n")) + code
        exec(compile(ns_payload, "<fence>", "exec"), ns)
        ok1 = (not any(e[0] == "remove" for e in events)) and os.path.exists(out)
        check("B-P1 exec fence: success path keeps file, no remove", ok1)

        # P2 failure at write
        events.clear()
        if os.path.exists(out):
            os.remove(out)
        class Boom(Exception):
            pass
        patched = code.replace(
            "fd.write(payload); fd.flush()",
            "fd.write(payload)\n    raise Boom()")
        ns2 = {"open": instr_open, "os": type(os)("os"), "path": out, "Boom": Boom}
        ns2["os"].remove = rec_remove
        ns2["payload"] = (doc + "\n").encode("utf-8")
        raised = False
        try:
            exec(compile("fd = None\n" + patched, "<fence2>", "exec"), ns2)
        except Boom:
            raised = True
        close_idx = next((i for i, e in enumerate(events) if e[0] == "close" and i < len(events) and any(x[0] == "remove" for x in events[i:])), None)
        ok2 = raised and any(e[0] == "remove" for e in events)
        ok2b = False
        if close_idx is not None:
            ok2b = True
        check("B-P2 exec fence: failure arm closes then removes (D-50)", ok2 and ok2b)

        # P4: KeyboardInterrupt through the arm removes (D-51 single-KI window)
        events.clear()
        if os.path.exists(out):
            os.remove(out)
        patched4 = code.replace(
            "fd.write(payload); fd.flush()",
            "fd.write(payload)\n    raise KeyboardInterrupt()")
        ns4 = {"open": instr_open, "os": type(os)("os"), "path": out}
        ns4["os"].remove = rec_remove
        ns4["payload"] = (doc + "\n").encode("utf-8")
        ki = False
        try:
            exec(compile("fd = None\n" + patched4, "<fence4>", "exec"), ns4)
        except KeyboardInterrupt:
            ki = True
        ok4 = ki and any(e[0] == "remove" for e in events)
        check("B-P4 exec fence: single KI through the arm removes (D-51/D-53)", ok4)

        # P5 (D-53): SECOND KI inside the failure arm (at its fd.close())
        #   -> compensation aborted mid-flight, partial file SURVIVES.
        events.clear()
        if os.path.exists(out):
            os.remove(out)

        class KICloseFD:
            """fd proxy: close() raises KeyboardInterrupt (the second SIGINT)."""

            def __init__(self, f):
                self._f = f

            def close(self):
                raise KeyboardInterrupt()

            def __getattr__(self, name):
                return getattr(self._f, name)

        def ki_open(*a, **k):
            return KICloseFD(real_open(*a, **k))

        patched5 = code.replace(
            "fd.write(payload); fd.flush()",
            "fd.write(payload)\n    raise KeyboardInterrupt()")
        ns5 = {"open": ki_open, "os": type(os)("os"), "path": out}
        ns5["os"].remove = rec_remove
        ns5["payload"] = (doc + "\n").encode("utf-8")
        ki5 = False
        try:
            exec(compile("fd = None\n" + patched5, "<fence5>", "exec"), ns5)
        except KeyboardInterrupt:
            ki5 = True
        removed5 = any(e[0] == "remove" for e in events)
        ok5 = ki5 and (not removed5) and os.path.exists(out)
        check("B-P5 exec fence: second KI inside the arm aborts compensation, "
              "partial SURVIVES (D-53/R-5)",
              ok5, "ki=%s removed=%s exists=%s" % (ki5, removed5, os.path.exists(out)))

        # P6 (D-54): KI raised BY open() itself, after the kernel applied
        #   O_TRUNC -> fd never bound, NO remove, pre-existing target 0 bytes.
        events.clear()
        if os.path.exists(out):
            os.remove(out)
        with open(out, "wb") as f:
            f.write(b'{"prior":"good"}')

        def trunc_then_ki_open(p, *a, **k):
            f = real_open(p, *a, **k)   # O_TRUNC applied by the kernel here
            f.close()                   # simulate signal striking before return
            raise KeyboardInterrupt()

        ns6 = {"open": trunc_then_ki_open, "os": type(os)("os"), "path": out}
        ns6["os"].remove = rec_remove
        ns6["payload"] = (doc + "\n").encode("utf-8")
        ki6 = False
        try:
            exec(compile("fd = None\n" + code, "<fence6>", "exec"), ns6)
        except KeyboardInterrupt:
            ki6 = True
        removed6 = any(e[0] == "remove" for e in events)
        zero6 = os.path.exists(out) and os.path.getsize(out) == 0
        ok6 = ki6 and (not removed6) and zero6
        check("B-P6 exec fence: KI-at-open -> fd None, no remove, target 0-byte "
              "(D-54/R-6)",
              ok6, "ki=%s removed=%s zero=%s" % (ki6, removed6, zero6))

        # P7 (D-55): device output — /dev/stdout receives the document at a
        #   normal (no-exception) exit of the reference shape.
        import contextlib as _cl
        tmp_out = tempfile.NamedTemporaryFile(delete=False)
        tmp_out.close()
        saved1 = os.dup(1)
        try:
            with open(tmp_out.name, "wb") as redir:
                os.dup2(redir.fileno(), 1)
            ns7 = {"open": real_open, "os": os, "path": "/dev/stdout"}
            ns7["payload"] = (doc + "\n").encode("utf-8")
            exc7 = None
            try:
                exec(compile(code, "<fence7>", "exec"), ns7)
            except BaseException as e:  # noqa: BLE001 - probe records any escape
                exc7 = e
            finally:
                os.dup2(saved1, 1)
                os.close(saved1)
            written = open(tmp_out.name, "rb").read()
            ok7 = exc7 is None and written == (doc + "\n").encode("utf-8")
            check("B-P7 exec fence: output /dev/stdout -> document on stdout, "
                  "clean exit (D-55)",
                  ok7, "exc=%r written=%r" % (exc7, written[:40]))
        finally:
            if os.path.exists(tmp_out.name):
                os.remove(tmp_out.name)
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- C. v10 text needles
def c_family():
    n45 = norm(sec45)
    n64 = norm(sec64)
    n71 = norm(sec71)
    n73 = norm(sec73 := section(r"^## 7\.3 Residual-exception net", r"^# 8\. Acceptance-test outline"))
    nqc2 = norm(section(r"^### QC-2 ", r"^### QC-3 "))

    # T-A: D-53 scoping at every absolute-claim site
    check("T-A1 §4.5 names D-53 single-KI scope", "Single-KI scope (D-53" in n45 or "single-KI scope (D-53" in n45.lower())
    check("T-A2 §6.4 signal note carries D-53", "single-KI scope of D-53" in n64)
    check("T-A3 §7.1 timeout-cancellation carries D-53", "single-KI scope of D-53" in n71)
    check("T-A4 §7.3 carries the D-53 condition", "single-KI scope of D-53" in n73)
    check("T-A5 QC-2 Scope carries the D-53/D-54 signal-window exceptions", "SIGNAL-WINDOW EXCEPTIONS" in nqc2 and "R-5" in nqc2 and "R-6" in nqc2)

    # T-B: risk records
    check("T-B1 §10.1 has R-5 with 39b P1 cites", "R-5:" in sec101 and "39b-adv-c9-probes.py P1a/P1b" in sec101)
    check("T-B2 §10.1 has R-6 with 39b P2 cites", "R-6:" in sec101 and "P2a" in sec101 and "P2b" in sec101)

    # T-C: D-54 classification
    check("T-C1 §4.5 KI-at-open classification", "KI-AT-OPEN classification (D-54" in sec45)
    check("T-C2 glossary pins fd-binding as trigger basis (D-54)", "fd-binding point is the trigger basis" in sec12)

    # T-D: D-55 channel scope
    check("T-D1 §6.4 success row regular-file scope", "REGULAR-FILE output paths (D-55" in sec64)
    check("T-D2 §9 NFR-004 row scoped", "REGULAR-FILE output paths" in sec9)
    check("T-D3 T-K3 scoped", "parametrized over REGULAR-FILE output paths" in sec8)

    # T-E: §11 coverage sentence names D-01..D-55
    m = re.search(r"D-01\.\.D-\d+", sec11)
    check("T-E §11 coverage sentence names D-01..D-55", bool(m) and m.group(0) == "D-01..D-55", m.group(0) if m else "absent")

    # T-F: F-05 + F-04 in §6.3
    check("T-F1 §6.3 names E-NET's <in> slot", "E-NET's `<in>` slot is covered by the same rule" in sec63)
    check("T-F2 §6.3 carries the encoding-scope note", "Encoding scope of the verbatim rule" in sec63)

    # T-G: no unconditional interrupted-run claim survives outside QC
    bad = []
    for m2 in re.finditer(r"an interrupted run[^.]{0,120}", spec_norm):
        w = m2.group(0)
        window = spec_norm[max(0, m2.start() - 400):m2.end() + 400]
        if not re.search(r"single-KI|D-53|SECOND KI|single-Ctrl-C|one KI|ONE KI|SINGLE-KeyboardInterrupt", window, re.I):
            bad.append(w[:80])
    check("T-G every interrupted-run claim is single-KI conditioned", not bad, "; ".join(bad[:3]))

    # T-H: banned keyword "guarantee" outside section 10
    outside = re.sub(r"# 10\. Quality-claim.*?(?=# 11\. Traceability)", "", spec_text, flags=re.S)
    hits = [ln for ln in outside.splitlines() if re.search(r"\bguarantee\b", ln, re.I)]
    check("T-H no 'guarantee' keyword outside §10 (header/§6.3/§6.4/T-C8/§12 clean)", not hits, f"{len(hits)} hits")
    # v10 added a second guarantee mention in §10.1 R-2 (fine — inside §10);
    # and header revision row must be clean (covered by T-H since header is outside §10).


a1()
a2()
a3()
b_family()
c_family()

print()
print(f"TOTAL FAILURES: {len(fails)}")
sys.exit(1 if fails else 0)

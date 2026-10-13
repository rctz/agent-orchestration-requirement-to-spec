#!/usr/bin/env python3
"""appendix/32-rev8-fdclose-probes.py — rev8 (cycle-8) live probes.

Subject: the D-50 close-before-remove ordering in spec/08-spec-v8.md §4.5's
except-scoped reference shape (closes SR6-F-01).

Method: the probe execs the spec's OWN fenced code block (found after
"Conforming reference shape (e.g.):") with an instrumented `open` that
returns a recording proxy and an instrumented `os` whose remove() records
the event. The proxy's `closed` property reads the real file object, so
before the arm's fd.close() runs, `fd.closed` is observably False — a live
handle — and the OS-level Windows behavior cited by SR6-F-01
(os.remove-on-open-handle raises PermissionError there, documented platform
behavior) is exactly the state the P3 control replays.

  P0  structural: in the spec's fenced block the failure arm contains
      fd.close() BEFORE os.remove(path), and the D-50 close-before-remove
      sentence follows the block.
  P1  success path (D-50 shape): no remove event, file exists, exact bytes.
  P2  failure at write (D-50 shape): event ordering close -> remove; at the
      last close before the remove the handle was OPEN (closed=False — the
      state Windows rejects for removal); file removed; OSError propagated.
  P3  control — the superseded v7 shape (arm without the close): the arm
      removes with NO close event before it — the remove-while-open state
      SR6-F-01 named; on POSIX it silently succeeds (why the v7 defect was
      invisible on Linux CI), on Windows it raises PermissionError and the
      partial file survives.
  P4  KeyboardInterrupt through the D-50 arm (D-48's BaseException scope):
      file removed, KI propagated.
  P5  P2/P3 delta: the D-50 shape emits a close event inside the failure
      arm before the remove; the v7 control emits none — the ordering IS
      the difference.
"""
import os, sys, tempfile, textwrap

SPEC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "spec", "08-spec-v8.md")
RESULTS = []


def record(pid, ok, detail):
    RESULTS.append(ok)
    print("%-4s %-5s %s" % (pid, "PASS" if ok else "FAIL", detail))


class ProxyFile:
    """Wraps a real file object; records lifecycle events, forwards all."""
    def __init__(self, real, events):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_events", events)
        events.append(("open", False))          # (event, handle_open_at_event)
    def write(self, *a, **k):
        events = self._events
        events.append(("write", True))
        return self._real.write(*a, **k)
    def flush(self):
        self._events.append(("flush", True))
        return self._real.flush()
    def close(self):
        self._events.append(("close", True))    # handle OPEN when close fires
        r = self._real.close()
        self._events.append(("closed", False))  # handle GONE after close
        return r
    @property
    def closed(self):
        return self._real.closed
    def __getattr__(self, name):
        return getattr(self._real, name)


class ShimOS:
    """os shim whose remove() records the event, then really removes.

    The fd state is read LIVE from the shape's own namespace at remove
    time: None -> fd cleared (the shape closed it and set fd = None);
    False -> proxy.closed False = LIVE OPEN HANDLE (the state Windows
    rejects). The real removal is delegated to the genuine os.remove so
    the filesystem outcome matches a conforming run.
    """
    def __init__(self, events, ns, real_remove):
        self._events, self._ns, self._real = events, ns, real_remove
    def remove(self, path):
        fd = self._ns.get("fd")
        self._events.append(("remove", None if fd is None else fd.closed))
        self._real(path)


def load_spec_shape():
    text = open(SPEC, encoding="utf-8").read()
    marker = "Conforming reference shape (e.g.):"
    i = text.index(marker)
    j = text.index("```", i)
    k = text.index("```", j + 3)
    return textwrap.dedent(text[j + 3:k]).strip("\n")


def run_shape(code, fail_at=None, exc=None):
    """Exec the shape in an instrumented namespace.

    Returns (events, error, path). Each event is (name, handle_open flag);
    `remove` events carry the fd state read from the shape's namespace at
    remove time (None = cleared/absent, False = LIVE OPEN HANDLE, True =
    n/a — a closed fd is cleared to None by the shape itself).
    """
    events = []
    tmpdir = tempfile.mkdtemp(prefix="rev8-fdclose-")
    path = os.path.join(tmpdir, "out.json")
    ns = {"payload": b'[{"a":"1"}]\n', "path": path}
    ns["os"] = ShimOS(events, ns, os.remove)
    real_open = open

    def instrumented_open(p, mode="r", *a, **k):
        if p == path:
            return ProxyFile(real_open(p, mode, *a, **k), events)
        return real_open(p, mode, *a, **k)

    ns["open"] = instrumented_open

    real_write = ProxyFile.write

    def write_hook(self, *a, **k):
        if fail_at == "write":
            self._events.append(("write", True))
            raise exc if exc is not None else OSError(28, "No space left on device")
        return real_write(self, *a, **k)

    ProxyFile.write = write_hook
    try:
        try:
            exec(compile(code, "<spec-shape>", "exec"), ns)
            err = None
        except BaseException as e:      # noqa: BLE001 - the probe IS the net
            err = e
    finally:
        ProxyFile.write = real_write
    return events, err, path, ns


def main():
    code = load_spec_shape()

    # P0 — structural: ordering in the spec's own block + D-50 sentence.
    body, arm = code.split("except BaseException:")
    ci, ri = arm.index("fd.close()"), arm.index("os.remove(path)")
    full = open(SPEC, encoding="utf-8").read()
    tail = full.split("Conforming reference shape (e.g.):")[1]
    tail = tail.split("```")[2][:900]      # prose between this fence and the next
    has_sentence = "CLOSES the fd" in tail or ("close" in tail and "D-50" in tail)
    record("P0", ci < ri and has_sentence,
           "failure arm: fd.close() at +%d < os.remove(path) at +%d; "
           "D-50 close-before-remove sentence after the block=%s"
           % (ci, ri, has_sentence))

    # P1 — success path: file kept, exact bytes, no remove.
    events, err, path, _ = run_shape(code)
    existed = os.path.exists(path)
    data = open(path, "rb").read() if existed else b""
    ok = (err is None and existed and data == b'[{"a":"1"}]\n'
          and not any(e[0] == "remove" for e in events))
    record("P1", ok, "success: no remove event, file kept, bytes exact "
           "(events=%s)" % [e[0] for e in events])
    if existed:
        os.remove(path)

    # P2 — failure at write: close ran BEFORE the remove; at remove time fd
    # is None (the shape's closed+cleared convention) — never a live proxy.
    events, err, path, ns = run_shape(code, fail_at="write")
    removes = [e for e in events if e[0] == "remove"]
    ridx = events.index(removes[0]) if removes else -1
    closed_before = any(e[0] == "closed" for e in events[:ridx])
    ok = (isinstance(err, OSError) and bool(removes) and closed_before
          and removes[0][1] is None               # closed + cleared, never OPEN
          and not os.path.exists(path))
    record("P2", ok, "fault-at-write: events %s — close completed BEFORE the "
           "remove, fd at remove=%s (None = closed+cleared, never a live "
           "handle), file removed, OSError propagated"
           % ([e[0] for e in events], removes[0][1] if removes else None))

    # P3 — control: the superseded v7 shape (arm WITHOUT the close).
    v7_shape = code.replace(
        "        try: fd.close()              # D-50: close BEFORE the remove (Windows: os.remove on an open handle raises)\n"
        "        except OSError: pass         #   close errors are ignored too (best-effort)\n"
        "        fd = None\n", "")
    assert v7_shape != code, "v7 control strip did not match the spec block"
    events, err, path, ns7 = run_shape(v7_shape, fail_at="write")
    removes = [e for e in events if e[0] == "remove"]
    fd7 = ns7.get("fd")
    ok = (removes and not any(e[0] in ("close", "closed") for e in events)
          and fd7 is not None and fd7.closed is False
          and not os.path.exists(path) and isinstance(err, OSError))
    record("P3", ok, "v7 control: NO close before the remove; fd at remove is "
           "the LIVE proxy (closed=%s — the exact handle state Windows "
           "rejects); POSIX succeeds silently (why the defect was invisible "
           "on Linux CI); Windows raises PermissionError -> partial file "
           "survives (SR6-F-01)" % (fd7.closed if fd7 is not None else None))

    # P4 — KeyboardInterrupt through the D-50 arm (BaseException scope).
    events, err, path, _ = run_shape(code, fail_at="write", exc=KeyboardInterrupt())
    removes = [e for e in events if e[0] == "remove"]
    ridx = events.index(removes[0]) if removes else -1
    closed_before = any(e[0] == "closed" for e in events[:ridx])
    ok = (isinstance(err, KeyboardInterrupt) and bool(removes) and closed_before
          and removes[0][1] is None and not os.path.exists(path))
    record("P4", ok, "KeyboardInterrupt: events %s — close-before-remove "
           "held, fd at remove=%s (never a live handle), KI propagated (D-48 "
           "every-exception scope intact)"
           % ([e[0] for e in events], removes[0][1] if removes else None))

    # P5 — the delta: D-50 shape closes inside the arm, v7 does not.
    _, _, _, ns8 = run_shape(code, fail_at="write")
    _, _, _, ns7 = run_shape(v7_shape, fail_at="write")
    ok = ns8.get("fd") is None and ns7.get("fd") is not None \
        and ns7["fd"].closed is False
    record("P5", ok, "delta after the failed run: D-50 shape fd is None "
           "(closed+cleared); v7 control fd is the proxy with closed=False "
           "(handle never released by the arm)")

    print("%d probes, %d failures" % (len(RESULTS), RESULTS.count(False)))
    return 1 if RESULTS.count(False) else 0


if __name__ == "__main__":
    print("target: %s  host: %s" % (SPEC, sys.platform))
    sys.exit(main())

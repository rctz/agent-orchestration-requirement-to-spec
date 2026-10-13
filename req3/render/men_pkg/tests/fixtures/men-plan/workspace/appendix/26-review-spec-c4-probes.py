#!/usr/bin/env python3
"""Spec-review cycle-4 probes (evidence for appendix/26-review-spec-c4.md).

Independent live verification of load-bearing claims in spec/05-spec-v5.md
at boundaries NOT already covered by probe suites 13/20/22/23/25:

P-a  S-9b premise: the lenient parse of `id,"id` yields fields ['id','id']
     so the duplicate scan (slot 5) genuinely trips before the quote scan
     (slot 6) on the combined-defect header.
P-b  FSM FIELD_START-on-terminator reachability: a trailing empty field
     (`a,\n`) and a blank record (`\n`) both hand a terminator to the FSM
     in FIELD_START state — the state row's claim that this happens "only
     for a record-internal empty line" under-reads its own reachability.
P-c  S-9(c) vs S-9b citation: line 699 of the spec (§5.2) cites S-9(c)
     for the combined-defect duplicate-wins outcome; the combined-defect
     scenario is S-9b — S-9(c) is the no-duplicate `"id,name` case.
P-d  D-28 line arithmetic at a fresh mixed-terminator boundary
     (CRLF + CR before an invalid byte) plus regression of the pinned
     CR-only line-4 case.
P-e  Revision-note cross-reference: the v5 revision line says
     "§4.4/§5.3 S-4/§6.3/§7.1/T-C16 aligned" but §5.3's write-phase
     scenario is S-14, not S-4 (S-4 is Invalid UTF-8).
"""
import csv
import io
import re

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = open(HERE + "/spec/05-spec-v5.md", encoding="utf-8").read()

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# --- P-a: S-9b premise -------------------------------------------------------
rows = list(csv.reader(io.StringIO('id,"id', newline="")))
check("P-a1 `id,\"id` lenient parse -> ['id','id'] (dup detectable)",
      rows == [["id", "id"]], repr(rows))

# --- P-b: FSM FIELD_START-terminator reachability ----------------------------
text = "a,\n"
f = io.StringIO(text, newline="")
rec = next(csv.reader(f))
end = f.tell()
check("P-b1 span of `a,\\n` includes the terminator ('a,\\n')",
      text[0:end] == "a,\n", repr(text[0:end]))
check("P-b2 `a,\\n` parses to ['a',''] (trailing empty field)",
      rec == ["a", ""], repr(rec))
f2 = io.StringIO("\n", newline="")
rec2 = next(csv.reader(f2))
end2 = f2.tell()
check("P-b3 blank record: span '\\n', 0 fields",
      "\n"[0:end2] == "\n" and rec2 == [], (repr("\n"[0:end2]), rec2))
# the spec's §4.3.3 FIELD_START row says the terminator transition is
# "only possible for a record-internal empty line, never across records"
spec_row = ("FIELD_START | → QUOTED, remember current record-relative line as "
            "the opening line | stay FIELD_START | → FIELD_START "
            "(record-internal terminator; only possible for a "
            "record-internal empty line, never across records)")
sn = re.sub(r"\s+", " ", SPEC)
check("P-b4 §4.3.3 FIELD_START row carries the 'record-internal only' gloss",
      "record-internal terminator; only possible for a record-internal "
      "empty line, never across records" in sn)
# ...but a TERMINATOR-ENDING record (`a,\n`) also ends with the FSM in
# FIELD_START holding a terminator inside the record's own span, so the
# gloss under-reads reachability; behavior is still unambiguous (advance
# once, stay FIELD_START), which is what the counting rule pins.
check("P-b5 trailing-comma span fact (the under-read case is real)",
      end == len("a,\n") and rec == ["a", ""])

# --- P-c: §5.2 S-9(c) miscite ------------------------------------------------
# §5.2 (line ~699): "on a combined defect the duplicate error wins, S-9(c)"
# The combined-defect scenario is S-9b; S-9(c) is the plain header-quote case.
m = re.search(r"on a combined defect the duplicate error wins,\s*S-9\(c\)",
              SPEC)
check("P-c1 §5.2 cites S-9(c) for the combined defect (miscite present)",
      m is not None)
check("P-c2 S-9b is titled 'Combined header defects'",
      "**S-9b Combined header defects" in SPEC)
check("P-c3 S-9(c) is the plain-header-quote form (`\"id,name`)",
      re.search(r"\(c\) header-line form `\"id,name`", SPEC) is not None)

# --- P-d: D-28 arithmetic at a fresh boundary --------------------------------
def line_of_offset(text, offset):
    line, i = 1, 0
    while i < offset:
        if text[i] == "\r":
            i += 2 if text[i + 1:i + 2] == "\n" else 1
            line += 1
        else:
            if text[i] == "\n":
                line += 1
            i += 1
    return line


data = b"a,b\r\nc\r\xff"
prefix = data[: data.index(0xFF)].decode("utf-8")
check("P-d1 fresh mixed CRLF+CR `a,b\\r\\nc\\r\\xff` -> line 3",
      line_of_offset(prefix, len(prefix)) == 3,
      str(line_of_offset(prefix, len(prefix))))
prefix2 = "a,b\rc,d\rc\r"
check("P-d2 pinned CR-only case stays line 4",
      line_of_offset(prefix2, len(prefix2)) == 4,
      str(line_of_offset(prefix2, len(prefix2))))

# --- P-e: revision-note S-4 miscite ------------------------------------------
check("P-e1 revision line cites '§5.3 S-4' for the serialize align set",
      "§4.4/§5.3 S-4/§6.3/§7.1/T-C16 aligned" in SPEC)
check("P-e2 §5.3 write-phase scenario is S-14 (not S-4)",
      "**S-14 Write-phase failure**" in SPEC and "**S-4 Invalid UTF-8**" in SPEC)

print()
print("TOTAL FAILURES:", len(fails))
raise SystemExit(1 if fails else 0)

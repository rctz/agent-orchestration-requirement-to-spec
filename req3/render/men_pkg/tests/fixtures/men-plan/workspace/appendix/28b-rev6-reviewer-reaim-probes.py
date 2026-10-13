#!/usr/bin/env python3
"""rev6 re-aim of the cycle-4 reviewer probes (appendix/26-review-spec-c4-probes.py).

The reviewer's file stays untouched as evidence for its verdict on v5.
This copy re-aims the same load-bearing claims at spec/06-spec-v6.md:

P-a  S-9b premise: unchanged live behavior (lenient parse of `id,"id`).
P-b  FSM FIELD_START-terminator reachability: the v6 gloss now STATES the
     full reachable set (record-internal empty line, trailing empty field,
     empty record) — the reviewer's under-read finding is folded.
P-c  §5.2 now cites S-9b (SR4-F-01 folded; S-9(c) miscite gone).
P-d  D-28 arithmetic regression (fresh mixed boundary + CR-only line 4).
P-e  The v5 revision-note S-4 miscite is moot (the v5 revision row was
     replaced by the v6 row, which cites S-14 correctly).
"""
import csv
import io
import re

HERE = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"
SPEC = open(HERE + "/spec/06-spec-v6.md", encoding="utf-8").read()

fails = []


def check(name, cond, detail=""):
    print(("PASS" if cond else "FAIL"), name, "" if cond else detail)
    if not cond:
        fails.append(name)


# --- P-a: S-9b premise --------------------------------------------------------
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
# v6 wording (the folded SR4-F-03 gloss):
sn = re.sub(r"\s+", " ", SPEC)
check("P-b4 v6 FIELD_START gloss states the full reachable set",
      "reachable for a record-internal empty line, a trailing empty field "
      "such as `a,\\n`, or the empty record itself" in sn)
check("P-b5 the v5 'only possible' under-read gloss is gone",
      "only possible for a record-internal empty line" not in sn)

# --- P-c: §5.2 S-9b cite (SR4-F-01 folded) ------------------------------------
check("P-c1 §5.2 now cites S-9b for the combined defect",
      re.search(r"on a combined defect the duplicate error wins,\s*S-9b",
                SPEC) is not None)
check("P-c2 the S-9(c) miscite is gone",
      "the duplicate error wins, S-9(c)" not in sn)
check("P-c3 S-9b is titled 'Combined header defects'",
      "**S-9b Combined header defects" in SPEC)
check("P-c4 S-9(c) plain-header-quote form still correctly cited at S-9",
      re.search(r"\(c\) header-line form `\"id,name`", SPEC) is not None)

# --- P-d: D-28 arithmetic regression ------------------------------------------
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

# --- P-e: revision-note pointer (moot in v6; the v6 row cites S-14) ----------
check("P-e1 the v5 '§5.3 S-4' miscite is gone from the live revision row",
      "§4.4/§5.3 S-4/§6.3/§7.1/T-C16 aligned" not in SPEC)
check("P-e2 §5.3 write-phase scenario is S-14 (unchanged, correct)",
      "**S-14 Write-phase failure**" in SPEC and "**S-4 Invalid UTF-8**" in SPEC)
check("P-e3 v6 revision row cites the D-44 align set with S-14",
      "§5.3 S-14" in SPEC)

print()
print("TOTAL FAILURES:", len(fails))
raise SystemExit(1 if fails else 0)

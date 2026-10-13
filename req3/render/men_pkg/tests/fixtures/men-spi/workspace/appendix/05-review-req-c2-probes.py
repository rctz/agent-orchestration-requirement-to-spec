"""Consolidated cycle-2 review probes (evidence for appendix/06-review-req-c2.md).

Re-verifies every stdlib-behavior claim in requirements/04-requirements-v4.md
and probes the newline-handling corner the document leaves unspecified.

Run: python3 appendix/05-review-req-c2-probes.py
Interpreter used for review: Python 3.13.5 (this workspace).
"""
import csv, io, json, sys, os, tempfile

print("python:", sys.version.split()[0])
p = lambda label, val: print(f"{label}: {val!r}")

print("=== batch 1: claims pinned in v4 ===")
# csv.reader row model (D-18 / REQ-009)
p("blank-only-file '\\n\\n'", list(csv.reader(io.StringIO("\n\n"))))
p("blank-between", list(csv.reader(io.StringIO("a,b\n\nc,d\n"))))
p("empty-string-input", list(csv.reader(io.StringIO(""))))
p("one-trailing-NL", list(csv.reader(io.StringIO("a,b\n"))))
p("two-trailing-NL", list(csv.reader(io.StringIO("a,b\n\n"))))
p("trailing-CR", list(csv.reader(io.StringIO("a,b\r"))))
p("trailing-CRLF", list(csv.reader(io.StringIO("a,b\r\n"))))
p("a-nl-nl-1-nl", list(csv.reader(io.StringIO("a\n\n1\n"))))

# unterminated quote (D-19 / REQ-013)
p("unclosed-data-2col", list(csv.reader(io.StringIO('id,name\n"1,2'))))
p("unclosed-1col", list(csv.reader(io.StringIO('a\n"1'))))
p("unclosed-in-header", list(csv.reader(io.StringIO('"id,name'))))

# field size limit (D-21 / NFR-005)
p("field_size_limit() default", csv.field_size_limit())
big = "x" * 200000
try:
    list(csv.reader(io.StringIO('"' + big + '"')))
    print("200k-field: parsed (unexpected)")
except Exception as e:
    print("200k-field raises:", type(e).__name__, e)
csv.field_size_limit(sys.maxsize)
rows = list(csv.reader(io.StringIO('"' + big + '"')))
print("after-field_size_limit(sys.maxsize):", len(rows), "row(s), field len", len(rows[0][0]))

# json.dumps escape contract (D-20 / section 5.2)
p("FF-0x0C", json.dumps("\x0c", ensure_ascii=False))
p("VT-0x0B", json.dumps("\x0b", ensure_ascii=False))
p("NUL-0x00", json.dumps("\x00", ensure_ascii=False))
p("BS-0x08", json.dumps("\x08", ensure_ascii=False))
p("TAB-0x09", json.dumps("\x09", ensure_ascii=False))
p("DEL-0x7F", json.dumps("\x7f", ensure_ascii=False))
p("U+2028", json.dumps("\u2028", ensure_ascii=False))
p("quote-backslash", json.dumps('a"b\\c', ensure_ascii=False))
p("0x1F", json.dumps("\x1f", ensure_ascii=False))
p("U+0085", json.dumps("\u0085", ensure_ascii=False))
p("U+FEFF-mid-doc", json.dumps("\ufeff", ensure_ascii=False))

# BOM decode (D-16 / REQ-012)
p("BOM-bytes-decode", b"\xef\xbb\xbf".decode("utf-8"))

print()
print("=== batch 2: newline-mode matrix (cycle-2 finding) ===")
CRFILE = "a,b\rc,d\r"          # CR-only line endings
QCR = 'h,k\n"x\r\ny",2\n'      # CRLF inside a quoted field (data per REQ-004)
QCRONLY = 'h,k\n"x\ry",2\r'    # bare CR inside a quoted field

def via_stringio_default(text):
    return list(csv.reader(io.StringIO(text)))

def via_realfile_newline_empty(text):
    # the documented csv idiom: open(..., newline='')
    with tempfile.NamedTemporaryFile("w", newline="", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        with open(path, newline="") as f:
            return list(csv.reader(f))
    finally:
        os.unlink(path)

for name, fn in [("StringIO-default", via_stringio_default),
                 ("StringIO-newline=None", lambda t: list(csv.reader(io.StringIO(t, newline=None)))),
                 ("realfile-newline=''", via_realfile_newline_empty)]:
    print(f"--- {name} ---")
    for label, text in [("CR-only-file", CRFILE), ("CRLF-in-quotes", QCR), ("CR-in-quotes", QCRONLY)]:
        try:
            p(label, fn(text))
        except Exception as e:
            print(f"{label}: RAISES {type(e).__name__}: {e}")

print()
print("=== batch 2b: REQ-004 acceptance probes ===")
p("quoted-comma '\"a,b\",c'", list(csv.reader(io.StringIO('"a,b",c\n'))))
p("doubled-quote '\"say \"\"hi\"\"\"'", [r[0] for r in csv.reader(io.StringIO('"say ""hi"""\n'))])
p("multiline-quoted", list(csv.reader(io.StringIO('a,b\n"l1\nl2",2\n'))))

print()
print("=== batch 3: strict=True / other corners ===")
for label, text in [("unclosed-2col", 'id,name\n"1,2'), ("unclosed-1col", 'a\n"1'),
                    ("unclosed-header", '"id,name'), ("junk-after-quote", 'a,"b"c"')]:
    try:
        p(f"strict:{label}", list(csv.reader(io.StringIO(text), strict=True)))
    except Exception as e:
        print(f"strict:{label}: RAISES {type(e).__name__}: {e}")
p("lenient:junk-after-quote", list(csv.reader(io.StringIO('a,"b"c"'))))
p("lenient:quote-mid-unquoted", list(csv.reader(io.StringIO('a"b,c'))))
try:
    csv.field_size_limit(2**64)
    print("field_size_limit(2^64): accepted")
except OverflowError as e:
    print("field_size_limit(2^64): RAISES OverflowError:", e)

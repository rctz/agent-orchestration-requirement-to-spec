#!/usr/bin/env python3
"""Spec-review cycle 1, part 3: decode-prefix robustness of the spec's
line-number formula (§4.2): prefix = data[:e.start].decode("utf-8")."""
cases = [
    b"a\xc3(",          # truncated 2-byte seq then ASCII
    b"\x80",            # bare continuation byte at start
    b"a\xf0\x9f\x98",   # truncated 4-byte seq at EOF
    b"\xc0\xaf",        # overlong encoding
    b"a\xed\xa0\x80",   # surrogate (CESU-ish)
    b"h,k\n\xe0\xb8",   # Thai lead bytes at EOF (R4 shape)
    b"a\r\n\x82",       # continuation byte after CRLF
]
for data in cases:
    try:
        data.decode("utf-8")
        print(repr(data), "decoded OK?!")
    except UnicodeDecodeError as e:
        try:
            prefix = data[: e.start].decode("utf-8")
            print(repr(data), "e.start=%d reason=%s prefix_ok=%r" % (e.start, e.reason, prefix))
        except UnicodeDecodeError as e2:
            print(repr(data), "e.start=%d reason=%s PREFIX ITSELF FAILS: %s" % (e.start, e.reason, e2))

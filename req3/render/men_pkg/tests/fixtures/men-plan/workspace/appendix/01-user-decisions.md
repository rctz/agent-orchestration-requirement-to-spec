# User decisions — i-need-a-small-command-line-tool-csv2js

Every user answer, verbatim, newest last.


## Answers 2026-09-16 17:38 

Q-01: (a) all values as strings, lossless. Empty cell stays empty string, not null. Q-02: (a) compact JSON, silent stdout on success. Q-03: (a) error out on duplicate header names, with line number 1. Q-04: (a) fail with a clear error on non-UTF-8 input, never lossy conversion.

## Answers 2026-09-16 17:53 

Q-05: (a) strip the leading UTF-8 BOM so header keys come out clean (id, not \ufeffid). Q-06: (a) raw UTF-8 output, ensure_ascii=False — keep real Thai characters in the JSON file.

## User gate decision — APPROVED (2026-09-17 09:14 )

User reviewed the full requirements and approved them after req-review PASS. Gate opened; spec-design cycle 1 started.

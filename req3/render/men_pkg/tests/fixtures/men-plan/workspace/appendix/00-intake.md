# Intake — i-need-a-small-command-line-tool-csv2js

- received: 2026-09-16 17:26 
- channel: CLI (req2 new)

## Raw requirement (verbatim)

I need a small command-line tool: csv2json. It reads a CSV file (with a header row), converts each data row into a JSON object keyed by the header names, and writes the result as a JSON array to an output file. Must handle quoted fields containing commas, and report a clear error (with line number) when a row has a different number of fields than the header. Single-file Python script, stdlib only, run as: python csv2json.py input.csv output.json

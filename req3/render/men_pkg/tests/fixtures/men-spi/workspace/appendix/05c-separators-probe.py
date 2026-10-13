"""Cycle-2 micro-probe: json.dumps default separators vs explicit compact separators."""
import json

obj = [{"id": "1", "name": "x"}, {"id": "2", "name": "y"}]
print("3.13 default ensure_ascii=False :", json.dumps(obj, ensure_ascii=False))
print("3.13 explicit separators        :", json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
print("3.13 with trailing-space default:", json.dumps(obj, ensure_ascii=False, separators=(",", ": ")))

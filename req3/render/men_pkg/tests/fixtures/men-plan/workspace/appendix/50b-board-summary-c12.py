#!/usr/bin/env python3
"""Summarize the cycle-11/12 board query output to one line per card."""
import json

data = open('/tmp/c12board.txt').read()
j = data[:data.rfind('total matched')]
obj = json.loads(j)
for t in obj:
    print(t['id'], '|', t['title'][:75], '|', t['status'], '|',
          (t['result'] or 'NO-RESULT')[:110])

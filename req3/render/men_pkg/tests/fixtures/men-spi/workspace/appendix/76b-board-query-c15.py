#!/usr/bin/env python3
"""76b - rev15 board query: verify gate-card verdicts before citing them.

Pattern per 57/71: read-only sqlite against the board DB.
"""
import sqlite3
import json

DB = "/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db"
con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row

rows = con.execute(
    "SELECT id, title, status, result, completed_at FROM tasks "
    "WHERE title LIKE '%csv2js%' AND (title LIKE '%adv%' OR title LIKE '%spec-review%') "
    "ORDER BY created_at DESC LIMIT 14"
).fetchall()
for r in rows:
    d = dict(r)
    print(json.dumps(d))

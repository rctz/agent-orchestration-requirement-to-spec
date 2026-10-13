#!/usr/bin/env python3
"""Read-only board query: find review cards (any title) completed in the last 2 days."""
import sqlite3, time

con = sqlite3.connect("file:/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db?mode=ro", uri=True)
rows = con.execute(
    "SELECT id, title, assignee, status, result, completed_at FROM tasks "
    "WHERE title LIKE '%i-need-a-small-command-line-tool-csv2js%' "
    "AND created_at > 1789600000 "
    "ORDER BY created_at DESC LIMIT 20"
).fetchall()
for r in rows:
    print("==", r[0], "|", r[2], "|", r[1], "|", r[3], "| completed:", r[5])
    print("RESULT:", (r[4] or "")[:500])
    print()

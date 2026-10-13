#!/usr/bin/env python3
"""Read-only board query: recent spec-design + review-spec cards, verdicts & comments."""
import sqlite3

con = sqlite3.connect("file:/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db?mode=ro", uri=True)
rows = con.execute(
    "SELECT id, title, status, result, completed_at FROM tasks "
    "WHERE title LIKE '%i-need-a-small-command-line-tool-csv2js%' "
    "AND (title LIKE '%spec-design%' OR title LIKE '%review-spec%') "
    "ORDER BY created_at DESC LIMIT 8"
).fetchall()
for r in rows:
    print("==", r[0], "|", r[1], "|", r[2], "| completed_at:", r[4])
    print("RESULT:", (r[3] or "")[:700])
    print()

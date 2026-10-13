#!/usr/bin/env python3
"""Read-only board query: spec-design#8 (t_c1a05838) comments + result."""
import sqlite3

con = sqlite3.connect("file:/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db?mode=ro", uri=True)
tid = "t_c1a05838"
t = con.execute("SELECT title,status,result FROM tasks WHERE id=?", (tid,)).fetchone()
print("TITLE:", t[0], "| STATUS:", t[1])
print("RESULT:", (t[2] or "")[:800])
print("---- comments")
for c in con.execute("SELECT created_at, author, body FROM task_comments WHERE task_id=? ORDER BY created_at", (tid,)):
    print("==", c[0], c[1])
    print((c[2] or "")[:2000])
    print()

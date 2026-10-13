#!/usr/bin/env python3
"""Board query for cycle 13 (read-only), v4: correct DB path (50's pattern).
Prints id/title/status/result for cycle-10..13 gate cards + my card."""
import json
import sqlite3

DB = "/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

rows = conn.execute(
    "SELECT id, title, status, result, completed_at FROM tasks "
    "ORDER BY created_at"
).fetchall()

report = []
for r in rows:
    title = r["title"] or ""
    if "csv2js" in title and any(
            k in title for k in ("spec-review", "adv-early", "spec-design",
                                 "mechval")):
        if any("#%d]" % n in title for n in (10, 11, 12, 13)):
            report.append({
                "id": r["id"],
                "title": title,
                "status": r["status"],
                "result": (r["result"] or "")[:160],
                "completed_at": r["completed_at"],
            })

print(json.dumps(report, indent=1))
print(f"total matched: {len(report)}")

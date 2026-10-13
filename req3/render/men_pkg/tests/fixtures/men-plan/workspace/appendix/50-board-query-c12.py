#!/usr/bin/env python3
"""Read-only board query: which cycle-11 gate cards have REAL verdicts?

Pattern per appendix/35c/46. Prints task id, title, status, result (verdict
line) for every card whose title mentions csv2js cycle-11 gates (spec-review,
adv-early). A card with NULL result and no findings artifact must NEVER be
cited (SR7-F-01 phantom-cite rule).
"""
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
    if any(k in title for k in ("spec-review", "adv-early", "adv-review", "spec-design", "mechval")):
        if "#11]" in title or "#12]" in title or "#10]" in title:
            report.append({
                "id": r["id"],
                "title": title,
                "status": r["status"],
                "result": r["result"],
                "completed_at": r["completed_at"],
            })

print(json.dumps(report, indent=1))
print(f"total matched: {len(report)}")

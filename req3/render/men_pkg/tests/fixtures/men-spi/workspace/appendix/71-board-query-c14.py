#!/usr/bin/env python3
"""Board query for cycle 14 (read-only), 57's pattern at the v14 cycle.
Prints id/title/status/result for the cycle-12..14 gate cards + my card,
so the v14 revision row cites only verdicts with a board result."""
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
        if any("#%d]" % n in title for n in (12, 13, 14)):
            report.append({
                "id": r["id"],
                "title": title,
                "status": r["status"],
                "result": (r["result"] or "")[:200],
                "completed_at": r["completed_at"],
            })

print(json.dumps(report, indent=1))
print(f"total matched: {len(report)}")

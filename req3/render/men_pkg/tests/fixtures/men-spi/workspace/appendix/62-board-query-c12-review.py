#!/usr/bin/env python3
"""62-board-query-c12-review.py — spec-review cycle-12 board check (read-only).

Verifies (a) the spec-design#13 card's completion record mentions the
designer re-run timings the v13 header cites (25.8 / 24.9 / 9.1 s), and
(b) the gate-verdict statuses the v13 header relies on:
spec-review#11 done FAIL; adv-early#12 archived no-result.
"""
import sqlite3

DB = "/home/pi/.hermes/kanban/boards/req-lab-v2/kanban.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

r = conn.execute("SELECT result FROM tasks WHERE id='t_6d826436'").fetchone()
print("spec-design#13 RESULT:", (r["result"] or "")[:2000])
print()

rows = conn.execute(
    "SELECT created_at, body FROM comments WHERE task_id='t_6d826436' "
    "ORDER BY created_at"
).fetchall()
print(f"comments on spec-design#13: {len(rows)}")
for c in rows:
    b = c["body"] or ""
    if any(k in b for k in ("24.9", "9.1", "55h", "25.8")):
        print("--- comment", c["created_at"], "---")
        print(b[:2500])
        print()

# Gate cards the v13 header cites
for tid, label in (("t_d2017123", "spec-review#11"), ("t_df9f3379", "adv-early#12")):
    row = conn.execute(
        "SELECT status, result FROM tasks WHERE id=?", (tid,)
    ).fetchone()
    print(f"{label} ({tid}): status={row['status']} result={(row['result'] or '')[:120]!r}")

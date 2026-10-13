"""92-sr14-board-query-c14.py — read-only board verification for spec-review c14.

Confirms (per the SR7-F-01 phantom-cite rule): mechval c15/c16 results,
the gate cards cited by the v16 revision row (adv-early#14 t_e2856728,
spec-review#13 t_d7903f01), and the parallel twin adv-early#16 t_e9d477b9.
"""
import json
import os
import sqlite3

WS = "/home/pi/hermes-workspaces/req-lab-v2/i-need-a-small-command-line-tool-csv2js"

# locate the board DB the way prior cycles' board queries did
cands = []
for root in ("/home/pi/.hermes", os.path.expanduser("~/.hermes")):
    for dirpath, _dirs, files in os.walk(root):
        if "kanban.db" in files and "req-lab" in dirpath:
            cands.append(os.path.join(dirpath, "kanban.db"))
        if len(cands) > 4:
            break
print("candidates:", cands)
db = cands[0]
con = sqlite3.connect("file:{}?mode=ro".format(db), uri=True)
cur = con.cursor()
cur.execute(
    "select id, title, status, result from tasks where id in "
    "('t_e2856728','t_d7903f01','t_e9d477b9','t_b7379694','t_15693023',"
    "'t_cf6fdf1b')"
)
for row in cur.fetchall():
    print(row)
con.close()

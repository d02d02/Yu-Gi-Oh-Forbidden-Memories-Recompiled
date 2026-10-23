#!/usr/bin/env python3
"""What the agent actually did, step by step, from OpenCode's session database (WSL).

    job-trace.py <id> [--full]

One line per tool call (session, tool, target, status, output size), then a summary: files read more than once,
failed/aborted calls, and the agent's own text between calls. --full also prints the agent's text in full.
"""
import collections
import json
import os
import sqlite3
import sys

job = sys.argv[1]
full = "--full" in sys.argv
db = sqlite3.connect(os.path.expanduser("~/.local/share/opencode/opencode.db"))
sessions = [r[0] for r in db.execute(
    "select id from session where directory like ? order by time_created", (f"%/work/{job}",))]
reads = collections.Counter()
bad = []
for n, sid in enumerate(sessions, 1):
    print(f"== session {n}/{len(sessions)} {sid[-8:]}")
    for (data,) in db.execute("select data from part where session_id=? order by time_created, id", (sid,)):
        p = json.loads(data)
        kind = p.get("type")
        if kind == "text" and p.get("text", "").strip():
            t = p["text"].strip().replace("\n", " ")
            print("   say:", t if full else t[:140])
        elif kind == "tool":
            st = p.get("state", {})
            inp = st.get("input", {}) or {}
            target = inp.get("filePath") or inp.get("pattern") or inp.get("command") or inp.get("path") or ""
            target = str(target).replace("\n", " ")[:90]
            status = st.get("status", "?")
            out = len(str(st.get("output", "")))
            print(f"   {p.get('tool', '?'):6} {status:9} out={out:6} {target}")
            if p.get("tool") == "read":
                reads[inp.get("filePath", "?")] += 1
            if status != "completed":
                bad.append((p.get("tool"), target, status))
print("\nread more than once:", ", ".join(f"{f.split('/')[-1]} x{c}" for f, c in reads.most_common() if c > 1) or "none")
print("not completed:", len(bad), *(f"\n   {t} {s}: {x}" for t, x, s in bad[:10]))

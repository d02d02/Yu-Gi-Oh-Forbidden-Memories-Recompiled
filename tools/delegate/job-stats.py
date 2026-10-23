#!/usr/bin/env python3
"""What a job cost and where it went, from OpenCode's own session database (WSL).

    job-stats.py <id>

Counts model steps, tool calls by kind and tokens for the sessions run in ~/work/<id>.
Exploration shows as glob/grep/list/read calls; fixed per-request overhead as tokens per step.
"""
import collections
import json
import os
import sqlite3
import sys

job = sys.argv[1]
db = sqlite3.connect(os.path.expanduser("~/.local/share/opencode/opencode.db"))
sessions = [r[0] for r in db.execute("select id from session where directory like ?", (f"%/work/{job}",))]
tools = collections.Counter()
steps = 0
tokens = {"input": 0, "output": 0}
for sid in sessions:
    for (data,) in db.execute("select data from part where session_id=?", (sid,)):
        part = json.loads(data)
        if part.get("type") == "step-finish":
            steps += 1
            t = part.get("tokens", {})
            tokens["input"] += t.get("input", 0)
            tokens["output"] += t.get("output", 0)
        elif part.get("type") == "tool":
            tools[part.get("tool", "?")] += 1
explore = sum(tools[k] for k in ("glob", "grep", "list", "read"))
print(f"sessions {len(sessions)}, model steps {steps}, tokens in {tokens['input']} out {tokens['output']}"
      f" ({(tokens['input'] + tokens['output']) // max(steps, 1)} per step)")
print("tools:", ", ".join(f"{k} {v}" for k, v in tools.most_common()) or "none", f"| explore-type calls {explore}")

#!/usr/bin/env python3
"""Live monitor for a delegated job: prints ONE line per event, nothing otherwise. Costs no model tokens while it runs.

    job-pulse.py <id> [--idle MIN=4] [--every SEC=20]

Events: START, SESSION (new iteration began), TOOL-ERROR (call failed/aborted), ITEM (checklist count changed),
COMMIT, IDLE (no activity for MIN minutes, repeated every MIN), STUCK-LOOP (same file edited 4+ times in one
session), END (loop process gone; says DONE/BLOCKED/STOPPED). Exits after END.
Run through the Monitor tool (each line becomes a notification to the supervisor) or as a background command.
"""
import collections
import json
import os
import sqlite3
import subprocess
import sys
import time

job = sys.argv[1]
arg = lambda k, d: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
idle_s = arg("--idle", 4) * 60
every = arg("--every", 20)
W = os.path.expanduser(f"~/work/{job}")
LL = "/mnt/c/Users/mda/llm-router"
db = sqlite3.connect(os.path.expanduser("~/.local/share/opencode/opencode.db"))


primed = False  # the first pass only records history silently


def say(msg):
    if primed:
        print(f"[{job} {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def alive():
    try:
        pid = int(open(f"{LL}/logs/ralph-{job}.pid").read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def items():
    t = open(f"{W}/progress.md").read()
    return t.count("\n- [x]"), t.count("\n- [ ]")


def commits():
    base = open(os.path.expanduser(f"~/work/{job}.base")).read().strip()
    out = subprocess.run(["git", "-C", W, "rev-list", "--count", f"{base}..HEAD"], capture_output=True, text=True)
    return int(out.stdout.strip() or 0)


seen_parts, seen_sessions = set(), set()
last_items, last_commits = items(), commits()
last_activity, last_idle_say = time.time(), 0
edits = collections.Counter()
while True:
    for sid, in db.execute("select id from session where directory like ? order by time_created", (f"%/work/{job}",)):
        if sid not in seen_sessions:
            seen_sessions.add(sid)
            say(f"SESSION {len(seen_sessions)} started")
        for pid, data in db.execute("select id, data from part where session_id=? order by time_created", (sid,)):
            if pid in seen_parts:
                continue
            p = json.loads(data)
            if p.get("type") == "tool" and p.get("state", {}).get("status") in ("completed", "error"):
                seen_parts.add(pid)
                last_activity = time.time()
                st = p["state"]
                inp = st.get("input") or {}
                tgt = str(inp.get("filePath") or inp.get("command") or inp.get("pattern") or "")[:70].replace("\n", " ")
                if st.get("status") == "error":
                    say(f"TOOL-ERROR {p.get('tool')} {tgt}")
                if p.get("tool") == "edit":
                    edits[(sid, tgt)] += 1
                    if edits[(sid, tgt)] == 4:
                        say(f"STUCK-LOOP 4 edits of {tgt.split('/')[-1]} in one session")
            elif p.get("type") in ("text", "step-finish"):
                seen_parts.add(pid)
                last_activity = time.time()
    it, cm = items(), commits()
    if it != last_items:
        say(f"ITEM {it[0]} done/{it[1]} left")
        last_items = it
    if cm != last_commits:
        say(f"COMMIT total {cm}")
        last_commits = cm
    if not primed:
        primed = True
        say(f"START {len(seen_sessions)} sessions so far, items {it[0]} done/{it[1]} left, commits {cm}")
        last_activity = time.time()
    if not alive():
        state = "DONE" if os.path.exists(f"{W}/RALPH_DONE") else "BLOCKED" if os.path.exists(f"{W}/BLOCKED") else "STOPPED"
        say(f"END {state}; items {it[0]} done/{it[1]} left, commits {cm}")
        break
    if time.time() - last_activity > idle_s and time.time() - last_idle_say > idle_s:
        say(f"IDLE {int((time.time() - last_activity) / 60)} min with the loop alive (rate limit sleep or hung model call)")
        last_idle_say = time.time()
    time.sleep(every)

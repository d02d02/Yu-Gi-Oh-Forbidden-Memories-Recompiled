#!/usr/bin/env python3
"""Live monitor for a delegated job: prints ONE line per event, nothing otherwise. Costs no model tokens while it runs.

    job-pulse.py <id> [--idle MIN=4] [--every SEC=20] [--iter-timeout SEC=900] [--verbose]

Default output is terse: ALERT lines (act now: ABORT-RUN, STUCK-LOOP, TIMEOUT-NEAR, IDLE, END, PROVIDER with zero successes) and
progress lines (START, ITEM). Everything else (SESSION, COMMIT, TOOL-ERROR, TEST-FAIL, REREAD, TOKENS, single PROVIDER) only with --verbose.

Events (grep-able prefix):
  SESSION     a new iteration (OpenCode session) started
  ITEM        checklist count changed
  COMMIT      commit count changed
  TOOL-ERROR  a tool call failed; the error text is shown (aborted = model sent a malformed/empty call)
  ABORT-RUN   3 aborted calls in one session: the model is emitting broken tool calls
  TEST-FAIL   a bash call's output shows a failing test (FAIL/Traceback/Error)
  STUCK-LOOP  4 edits of one file in one session
  REREAD      the same file read 3 times in one session (context is not being kept)
  TIMEOUT-NEAR  the session is at 80% of the iteration timeout without a commit: the iteration will be killed
  PROVIDER    3+ failed router calls since the last report (429, timeouts), with the last reason
  IDLE        no activity for MIN minutes (repeated every MIN); rate-limit sleep or a hung model call
  TOKENS      every 100k input tokens: running total and tokens per tick-off item
  END         loop gone; DONE/BLOCKED/STOPPED, items, commits, total tokens
Run it through the Monitor tool (each line becomes a notification) or as a background command. Exits after END.
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
iter_timeout = arg("--iter-timeout", 900)
W = os.path.expanduser(f"~/work/{job}")
LL = "/mnt/c/Users/mda/llm-router"
db = sqlite3.connect(os.path.expanduser("~/.local/share/opencode/opencode.db"))
try:
    ledger = sqlite3.connect(f"{LL}/data/ledger.sqlite")
except sqlite3.Error:
    ledger = None
primed = False  # the first pass only records history silently
VERBOSE = "--verbose" in sys.argv
bad_windows = 0


def say(msg, lvl=0):  # lvl 2 = act now, 1 = progress, 0 = noise (only with --verbose)
    if primed and (lvl >= 1 or VERBOSE):
        print(f"[{job} {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def alive():
    try:
        os.kill(int(open(f"{LL}/logs/ralph-{job}.pid").read().strip()), 0)
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


def ledger_failures(since):
    if not ledger:
        return 0, ""
    rows = ledger.execute("select status, substr(err,1,60) from calls where ok=0 and source='ralph' and ts>? order by ts",
                          (since,)).fetchall()
    return len(rows), (f"{rows[-1][0]} {rows[-1][1]}" if rows else "")


seen_parts, seen_sessions = set(), {}
last_items, last_commits = items(), commits()
last_activity, last_idle_say = time.time(), 0
edits, reads, aborts = collections.Counter(), collections.Counter(), collections.Counter()
warned = set()
tok_in = tok_out = next_tok_say = 0
ledger_since = time.time()
first_items = 0  # a job starts with nothing ticked; tokens are counted from the first session
commits_at = {}  # commit count when each session started
while True:
    for sid, created in db.execute("select id, time_created from session where directory like ? order by time_created",
                                   (f"%/work/{job}",)):
        if sid not in seen_sessions:
            seen_sessions[sid] = created / 1000
            commits_at[sid] = commits()
            say(f"SESSION {len(seen_sessions)} started")
        for pid, data in db.execute("select id, data from part where session_id=? order by time_created", (sid,)):
            if pid in seen_parts:
                continue
            p = json.loads(data)
            kind = p.get("type")
            if kind == "tool" and p.get("state", {}).get("status") in ("completed", "error"):
                seen_parts.add(pid)
                last_activity = time.time()
                st = p["state"]
                inp = st.get("input") or {}
                tool = p.get("tool")
                tgt = str(inp.get("filePath") or inp.get("command") or inp.get("pattern") or "")[:70].replace("\n", " ")
                if st.get("status") == "error":
                    err = str(st.get("error", "")).replace("\n", " ")[:110]
                    say(f"TOOL-ERROR {tool} {tgt} :: {err}")
                    if "aborted" in err:
                        aborts[sid] += 1
                        if aborts[sid] == 3:
                            say("ABORT-RUN 3 aborted calls in one session: broken tool calls from the model", 2)
                elif tool == "bash":
                    out = str(st.get("output", ""))
                    if any(k in out for k in ("FAILED", "Traceback", "AssertionError", "FAIL:")):
                        line = next((l for l in out.splitlines() if any(k in l for k in ("FAIL", "Error", "Traceback"))), "")
                        say(f"TEST-FAIL {tgt[:40]} :: {line.strip()[:90]}")
                elif tool == "edit":
                    edits[(sid, tgt)] += 1
                    if edits[(sid, tgt)] == 4:
                        say(f"STUCK-LOOP 4 edits of {tgt.split('/')[-1]} in one session", 2)
                elif tool == "read":
                    reads[(sid, tgt)] += 1
                    if reads[(sid, tgt)] == 3:
                        say(f"REREAD {tgt.split('/')[-1]} read 3 times in one session")
            elif kind == "step-finish":
                seen_parts.add(pid)
                last_activity = time.time()
                t = p.get("tokens", {})
                tok_in += t.get("input", 0)
                tok_out += t.get("output", 0)
            elif kind in ("text", "reasoning", "step-start", "patch"):
                seen_parts.add(pid)
                last_activity = time.time()
    it, cm = items(), commits()
    if it != last_items:
        say(f"ITEM {it[0]} done/{it[1]} left", 1)
        last_items = it
    if cm != last_commits:
        say(f"COMMIT total {cm}")
        last_commits = cm
    if tok_in >= next_tok_say + 100_000:
        next_tok_say = tok_in - tok_in % 100_000
        per = f", {tok_in // (it[0] - first_items):,} per item ticked" if it[0] > first_items else ", no item ticked yet"
        say(f"TOKENS in {tok_in:,} out {tok_out:,}{per}")
    if seen_sessions and cm == commits_at[list(seen_sessions)[-1]]:
        sid = list(seen_sessions)[-1]
        age = time.time() - seen_sessions[sid]
        if age > 0.8 * iter_timeout and sid not in warned and alive():
            warned.add(sid)
            say(f"TIMEOUT-NEAR session {len(seen_sessions)} is {int(age)} s old (limit {int(iter_timeout)} s); uncommitted work will be killed", 2)
    n, why = ledger_failures(ledger_since)
    if n >= 3:
        ok_n = ledger.execute("select count(*) from calls where ok=1 and source='ralph' and ts>?", (ledger_since,)).fetchone()[0]
        # failures with fallbacks answering are routine; alert only when nothing succeeded in the window
        say(f"PROVIDER {n} failed, {ok_n} ok, last: {why}", 2 if ok_n == 0 else 0)
        ledger_since = time.time()
    elif time.time() - ledger_since > 300:
        bad_windows, ledger_since = 0, time.time()
    if not primed:
        primed = True
        say(f"START {len(seen_sessions)} sessions so far, items {it[0]} done/{it[1]} left, commits {cm}", 1)
        last_activity = time.time()
        ledger_since = time.time()
    if not alive():
        state = "DONE" if os.path.exists(f"{W}/RALPH_DONE") else "BLOCKED" if os.path.exists(f"{W}/BLOCKED") else "STOPPED"
        say(f"END {state}; items {it[0]} done/{it[1]} left, commits {cm}, tokens in {tok_in:,} out {tok_out:,}", 2)
        break
    if time.time() - last_activity > idle_s and time.time() - last_idle_say > idle_s:
        say(f"IDLE {int((time.time() - last_activity) / 60)} min with the loop alive (rate limit sleep or hung model call)", 2)
        last_idle_say = time.time()
    time.sleep(every)

#!/usr/bin/env python3
"""PreToolUse guard: blocks token-heavy habits. Whole-file reads over 150 lines, repeat reads, flooding listings, root searches, bare cat.
Warns every 30 tool calls of a session (proxy for the 20k side-task cap). State: ~/.claude/hooks/state.json."""
import json, os, re, sys, time

LIMIT, WARN_EVERY = 150, 30
STATE = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "state.json")
call = json.load(sys.stdin)
tool, args, sid = call.get("tool_name", ""), call.get("tool_input", {}), call.get("session_id", "?")


def load():
    try:
        with open(STATE) as f:
            s = json.load(f)
    except Exception:
        s = {}
    return {k: v for k, v in s.items() if time.time() - v.get("t", 0) < 86400}


def out(**kw):
    print(json.dumps({"hookSpecificOutput": dict(hookEventName="PreToolUse", **kw)}))
    sys.exit(0)


def deny(why):
    out(permissionDecision="deny", permissionDecisionReason=why)


state = load()
me = state.setdefault(sid, {"n": 0, "reads": {}})
me["t"] = time.time()
me["n"] += 1
note = f"{me['n']} tool calls this session: check the 20k side-task cap, report if reached." if me["n"] % WARN_EVERY == 0 else ""

if tool == "Read":
    path = args.get("file_path", "")
    if os.path.isfile(path):
        mtime = os.path.getmtime(path)
        key = f"{path}|{args.get('offset')}|{args.get('limit')}|{args.get('pages')}"
        if me["reads"].get(key) == mtime:
            deny(f"Already read {path} this session, unchanged. Use what you have or Grep.")
        if not args.get("limit") and not args.get("pages") and not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf")):
            with open(path, "rb") as f:
                n = sum(1 for _ in f)
            if n > LIMIT:
                deny(f"{path} has {n} lines. Grep the target first, then Read with offset and limit (max {LIMIT} lines).")
        me["reads"][key] = mtime
elif tool in ("Bash", "PowerShell"):
    cmd = args.get("command", "")
    if re.search(r"\bfind\s+/(\s|$)", cmd) or re.search(r"Get-ChildItem\s+(-Path\s+)?[\"']?[A-Z]:\?[\"']?\s+-Recurse", cmd):
        deny("Filesystem-wide search is banned. Search a named directory.")
    if re.match(r"\s*cat\s+[^|;&]+$", cmd) and "<<" not in cmd:
        deny("cat dumps whole files. Use Grep, or Read with offset and limit.")
    limited = re.search(r"\|\s*(head|tail|wc|sort\s.*\|\s*head|grep|rg|awk|sed|cut|uniq)\b|>\s*\S|\s-(l|c|m\s*\d+|q)\b|--stat|--oneline|-n\s*\d|Select-Object\s+-First|-First\s+\d", cmd)
    if re.search(r"(^|[;&|]\s*)(find\s|ls\s+-\w*R|grep\s+-\w*r|rg\s|git\s+log\s|git\s+diff\s|dir\s.*/s|Get-ChildItem\s.*-Recurse)", cmd) and not limited:
        deny("Unbounded listing. Add head/tail, grep, a count or a redirect to a file.")

try:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f)
except Exception:
    pass
if note:
    out(permissionDecision="allow", additionalContext=note)

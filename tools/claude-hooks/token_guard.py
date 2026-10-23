#!/usr/bin/env python3
"""PreToolUse guard: blocks the token-heavy habits (whole-file reads over 150 lines, find from /, unbounded dumps)."""
import json, os, re, sys

LIMIT = 150
call = json.load(sys.stdin)
tool, args = call.get("tool_name", ""), call.get("tool_input", {})


def deny(why):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": why}}))
    sys.exit(0)


if tool == "Read":
    path = args.get("file_path", "")
    if not args.get("limit") and not args.get("pages") and os.path.isfile(path) and not path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf")):
        with open(path, "rb") as f:
            n = sum(1 for _ in f)
        if n > LIMIT:
            deny(f"{path} has {n} lines. Grep the target first, then Read with offset and limit (max {LIMIT} lines).")
elif tool in ("Bash", "PowerShell"):
    cmd = args.get("command", "")
    if re.search(r"\bfind\s+/(\s|$)", cmd) or re.search(r"Get-ChildItem\s+(-Path\s+)?[\"']?[A-Z]:\?[\"']?\s+-Recurse", cmd):
        deny("Filesystem-wide search is banned. Search a named directory.")
    if re.match(r"\s*cat\s+[^|;&]+$", cmd) and not re.search(r"<<", cmd):
        deny("cat dumps whole files. Use Grep, or Read with offset and limit.")

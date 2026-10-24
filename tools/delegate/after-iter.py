#!/usr/bin/env python3
"""Runs after every Ralph iteration (also a killed one): verify items independently, tick, snapshot-commit.

    after-iter.py <iteration> <exit-code>      (cwd = the job clone; set via RALPH_AFTER_ITER in job-run.sh)

1. Every ticked item ("- [x]") has its `check:` command re-run; one that no longer passes is unticked with a "Failed:" line.
2. The first unchecked item whose check passes is ticked (and so on while the next ones pass): work the agent finished
   but did not get to tick, or was killed before ticking, is not lost.
3. Whatever changed is committed ("items 4,5 verified" or "wip: iteration N snapshot"), so a kill never leaves
   uncommitted work and the stall counter sees progress.
The agent never decides alone that an item is done: the check command does.
"""
import os
import re
import subprocess
import sys

it, rc = sys.argv[1], sys.argv[2]
LINE = re.compile(r"^- \[( |x)\] (\d+)\.")
lines = open("progress.md", encoding="utf-8").read().split("\n")


def items():
    out = []
    for i, ln in enumerate(lines):
        m = LINE.match(ln)
        if m:
            out.append({"line": i, "done": m.group(1) == "x", "n": m.group(2), "check": None})
        elif out and ln.strip().startswith("check:"):
            out[-1]["check"] = ln.strip()[len("check:"):].strip()
    return out


def passes(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=240)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def untick(item, reason):
    lines[item["line"]] = lines[item["line"]].replace("- [x]", "- [ ]", 1)
    lines.insert(item["line"] + 1, f"  Failed: {reason}")


def repair_tests():
    """The agent sometimes drops an existing test class or the `if __name__` tail while growing a test file; put them back."""
    r = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
    for f in [x for x in r.stdout.split() if re.search(r"(^|/)test_[^/]*\.py$", x) and os.path.exists(x)]:
        old = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, text=True).stdout
        new = open(f, encoding="utf-8").read()
        tail = "\nif __name__ == \"__main__\":\n    unittest.main()\n"
        body = new.split("\nif __name__")[0].rstrip("\n") + "\n"
        lost = [b for b in re.split(r"(?m)^(?=class )", old.split("\nif __name__")[0])[1:]
                if re.match(r"class (\w+)", b).group(1) not in new]
        if lost or "\nif __name__" not in new:
            open(f, "w", encoding="utf-8").write(body + "".join("\n\n" + b.rstrip("\n") + "\n" for b in lost) + tail)
            print(f"[after-iter] repaired {f}: restored {len(lost)} dropped class(es)/tail")


repair_tests()


ticked, unticked = [], []
for item in reversed(items()):  # reversed so inserted lines do not shift the ones still to process
    if item["done"] and item["check"] and not passes(item["check"]):
        untick(item, f"re-check after iteration {it} did not pass")
        unticked.append(item["n"])
while True:  # items() is re-read each pass because inserted lines shift positions
    todo = next((x for x in items() if not x["done"]), None)
    if not todo or not todo["check"] or not passes(todo["check"]):
        break
    lines[todo["line"]] = lines[todo["line"]].replace("- [ ]", "- [x]", 1)
    lines.insert(todo["line"] + 1, f"  Result: verified by the loop after iteration {it}")
    ticked.append(todo["n"])

open("progress.md", "w", encoding="utf-8").write("\n".join(lines))

git = ["git", "-c", "user.name=ralph", "-c", "user.email=ralph@local"]
subprocess.run(["git", "add", "-A", "--", ".", ":(exclude,glob)**/__pycache__/**", ":(exclude)RALPH_DONE", ":(exclude)BLOCKED"], capture_output=True)
staged = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
if staged:
    msg = f"items {','.join(ticked)} verified" if ticked else f"wip: iteration {it} snapshot (exit {rc})"
    subprocess.run(git + ["commit", "-q", "-m", msg], capture_output=True)
    print(f"[after-iter] committed: {msg}" + (f"; unticked {','.join(unticked)}" if unticked else ""))
else:
    print("[after-iter] nothing to commit")

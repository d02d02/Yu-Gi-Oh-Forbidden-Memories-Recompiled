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
            out.append({"line": i, "done": m.group(1) == "x", "n": m.group(2), "check": None, "symbols": [], "min_tests": 0})
        elif out and ln.strip().startswith("check:"):
            out[-1]["check"] = ln.strip()[len("check:"):].strip()
        elif out and ln.strip().startswith("symbols:"):  # symbols: path::name, name, path2::name
            out[-1]["symbols"] = [x.strip() for x in ln.strip()[len("symbols:"):].split(",") if x.strip()]
        elif out and ln.strip().startswith("min_tests:"):
            out[-1]["min_tests"] = int(ln.strip()[len("min_tests:"):].strip() or 0)
    return out


def missing_symbols(item):
    """`path::name` entries of a `symbols:` line: each needs a `def name` or `class name` in that file (the last path repeats)."""
    path, miss = None, []
    for ent in item["symbols"]:
        if "::" in ent:
            path, ent = ent.split("::", 1)
        try:
            src = open(path, encoding="utf-8").read() if path else ""
        except OSError:
            src = ""
        if not re.search(rf"^\s*(def|class)\s+{re.escape(ent.strip())}\b", src, re.M):
            miss.append(f"{path}::{ent.strip()}")
    return miss


def passes(item):
    """True only on positive evidence: exit 0, and for a test command that tests ran (and at least min_tests), and symbols exist."""
    cmd = item["check"]
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        item["why"] = "check timed out"
        return False
    out = r.stdout + r.stderr
    if "test_" in cmd:
        m = re.search(r"Ran (\d+) test", out)
        if not m or int(m.group(1)) == 0 or int(m.group(1)) < item["min_tests"]:
            item["why"] = "no tests ran (or fewer than min_tests)"
            item["harness_fault"] = not m or int(m.group(1)) == 0
            return False
    if r.returncode != 0:
        item["why"] = (out.strip().splitlines() or ["check failed"])[-1][:120]
        return False
    miss = missing_symbols(item)
    if miss:
        item["why"] = "missing " + ", ".join(miss)
        return False
    return True


def untick(item, reason):
    lines[item["line"]] = lines[item["line"]].replace("- [x]", "- [ ]", 1)
    lines.insert(item["line"] + 1, f"  Failed: {reason}")


def repair_tests():
    """The agent sometimes drops an existing test class or the `if __name__` tail while growing a test file; put them back."""
    r = subprocess.run(["git", "ls-files", "-m", "-o", "--exclude-standard", "--", "*test_*.py"], capture_output=True, text=True)
    r2 = subprocess.run(["git", "ls-files", "--", "*test_*.py"], capture_output=True, text=True)
    for f in sorted(set(r.stdout.split()) | set(r2.stdout.split())):
        if not os.path.exists(f):
            continue
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
    if item["done"] and item["check"] and not passes(item):
        untick(item, f"re-check after iteration {it} did not pass: {item.get('why', '')}")
        unticked.append(item["n"])
while True:  # items() is re-read each pass because inserted lines shift positions
    todo = next((x for x in items() if not x["done"]), None)
    if not todo or not todo["check"] or not passes(todo):
        break
    lines[todo["line"]] = lines[todo["line"]].replace("- [ ]", "- [x]", 1)
    lines.insert(todo["line"] + 1, f"  Result: verified by the loop after iteration {it}")
    ticked.append(todo["n"])

open("progress.md", "w", encoding="utf-8").write("\n".join(lines))
# RALPH_DONE and BLOCKED are written by the agent only (ralph.sh removes them at start): validate, never trust.
def drop(name, why):
    os.remove(name)
    subprocess.run(["git", "rm", "-q", "--cached", "--ignore-unmatch", name], capture_output=True)
    print(f"[after-iter] rejected {name}: {why}")


if os.path.exists("RALPH_DONE"):
    todo = [x for x in items() if not x["done"]]
    if todo:
        drop("RALPH_DONE", f"{len(todo)} item(s) still open")
    elif os.path.exists("verify.sh") and subprocess.run(["bash", "verify.sh"], capture_output=True, timeout=600).returncode != 0:
        drop("RALPH_DONE", "verify.sh fails")
if os.path.exists("BLOCKED"):
    first = next((x for x in items() if not x["done"]), None)
    if first is None:
        drop("BLOCKED", "no open item")
    else:
        nfail = 0
        for ln in lines[first["line"] + 1:]:
            if LINE.match(ln):
                break
            nfail += ln.strip().startswith("Failed:")
        passes(first)
        if first.get("harness_fault"):
            drop("BLOCKED", "the check ran no tests: a harness or test-file fault, not the item; fix the tests and retry")
        elif nfail < 2:
            drop("BLOCKED", f"only {nfail} Failed: line(s) on item {first['n']}; needs 2 real attempts")

git = ["git", "-c", "user.name=ralph", "-c", "user.email=ralph@local"]
subprocess.run(["git", "add", "-A", "--", ".", ":(exclude,glob)**/__pycache__/**", ":(exclude)RALPH_DONE", ":(exclude)BLOCKED"], capture_output=True)
staged = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
if staged:
    msg = f"items {','.join(ticked)} verified" if ticked else f"wip: iteration {it} snapshot (exit {rc})"
    subprocess.run(git + ["commit", "-q", "-m", msg], capture_output=True)
    print(f"[after-iter] committed: {msg}" + (f"; unticked {','.join(unticked)}" if unticked else ""))
else:
    print("[after-iter] nothing to commit")

#!/usr/bin/env bash
# Bring a finished job's files into the project working tree (NOT committed) and run the tests there.
#   MSYS_NO_PATHCONV=1 bash tools/delegate/job-land.sh <id> [test command run from the project root]
# Copies every file the job changed or added since its base, except the spec files and loop markers, from the WSL clone's
# working tree (not the branch: it is the state that passed the checks). Prints the file list with line counts, then runs the
# test command (default: none). The supervisor then reads the diff, and commits specific paths.
set -eu
id="${1:?job id}"; shift || true
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
files="$(wsl bash -c "cd ~/work/$id && { git diff --name-only \$(cat ~/work/$id.base); git ls-files --others --exclude-standard; } | sort -u | grep -v -E '^(progress\.md|JOB\.md|verify\.sh|paths\.txt|RALPH_DONE|BLOCKED)\$' | grep -v __pycache__")"
[ -n "$files" ] || { echo "no changed files"; exit 1; }
wsl bash -c "cd ~/work/$id && tar c $(echo $files | tr '\n' ' ')" | tar x -C "$ROOT"
echo "landed (uncommitted) into $ROOT:"
for f in $files; do printf '  %6s lines  %s\n' "$(wc -l < "$ROOT/$f")" "$f"; done
if [ $# -gt 0 ]; then echo "--- $*"; (cd "$ROOT" && "$@") && echo "TESTS PASS" || { echo "TESTS FAIL"; exit 2; }; fi

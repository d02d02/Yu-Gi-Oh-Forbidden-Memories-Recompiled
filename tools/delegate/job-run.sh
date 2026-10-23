#!/usr/bin/env bash
# Run the Ralph loop on a job until RALPH_DONE / BLOCKED / stall / max iterations. Blocks; run it in the background.
#   wsl bash .../tools/delegate/job-run.sh <id> [max_iters]
# After every iteration (killed ones too) after-iter.py re-runs each item's check, ticks what passes, unticks what no
# longer passes, and commits the working tree, so nothing is lost to a kill and the agent cannot tick on its own word.
set -eu
id="${1:?job id}"; max="${2:-20}"
HERE="$(cd "$(dirname "$0")" && pwd)"
export RALPH_ITER_TIMEOUT="${RALPH_ITER_TIMEOUT:-1800}"
export RALPH_AFTER_ITER="$HERE/after-iter.py"
python3 /mnt/c/Users/mda/llm-router/scripts/budget.py 2>&1 | sed -n 1,8p   # quota left before starting
exec bash /mnt/c/Users/mda/llm-router/scripts/ralph.sh "$HOME/work/$id" "$HERE/delegate-prompt.txt" "$max"

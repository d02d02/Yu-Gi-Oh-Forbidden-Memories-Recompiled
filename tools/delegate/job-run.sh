#!/usr/bin/env bash
# Run the Ralph loop on a job until RALPH_DONE / BLOCKED / stall / max iterations. Blocks; run it in the background.
#   wsl bash .../tools/delegate/job-run.sh <id> [max_iters]
set -eu
id="${1:?job id}"; max="${2:-20}"
HERE="$(cd "$(dirname "$0")" && pwd)"
export RALPH_ITER_TIMEOUT="${RALPH_ITER_TIMEOUT:-900}"
exec bash /mnt/c/Users/mda/llm-router/scripts/ralph.sh "$HOME/work/$id" "$HERE/delegate-prompt.txt" "$max"

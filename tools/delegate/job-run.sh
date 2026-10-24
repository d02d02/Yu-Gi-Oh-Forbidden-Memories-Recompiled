#!/usr/bin/env bash
# Run the Ralph loop on a job until RALPH_DONE / BLOCKED / stall / max iterations. Blocks; run it in the background.
#   wsl bash .../tools/delegate/job-run.sh <id> [max_iters]
# After every iteration (killed ones too) after-iter.py re-runs each item's check, ticks what passes, unticks what no
# longer passes, and commits the working tree, so nothing is lost to a kill and the agent cannot tick on its own word.
set -eu
id="${1:?job id}"; max="${2:-20}"
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/env.sh"
export RALPH_ITER_TIMEOUT="${RALPH_ITER_TIMEOUT:-1800}"
export RALPH_AFTER_ITER="$HERE/after-iter.py"
"$DG_PY" "$DG_LL/scripts/budget.py" 2>&1 | sed -n 1,8p   # quota left before starting
# The pulse monitor runs inside this command, so one background call is the whole job. On a wake alert (STUCK-LOOP,
# ABORT-RUN, STALLED-ITEM) the loop is stopped and the alert is printed: this command ends and re-invokes the supervisor.
bash "$DG_LL/scripts/ralph.sh" "$HOME/work/$id" "$HERE/delegate-prompt.txt" "$max" & rp=$!
"$DG_PY" "$HERE/job-pulse.py" "$id" --exit-on-alert --kill-idle 8 >"$HOME/work/$id.alerts" 2>&1 & pp=$!
wait -n "$rp" "$pp" && rc=0 || rc=$?
if [ "$rc" = 3 ] && kill -0 "$rp" 2>/dev/null; then   # pulse ended first with a wake alert
  kill "$rp" 2>/dev/null; pkill -P "$rp" 2>/dev/null || true; echo "ALERT, loop stopped:"; tail -5 "$HOME/work/$id.alerts"; exit 3
fi
kill "$pp" 2>/dev/null || true
wait "$rp" 2>/dev/null || true; exit "$rc"

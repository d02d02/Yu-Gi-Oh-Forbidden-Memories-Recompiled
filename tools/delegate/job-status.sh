#!/usr/bin/env bash
# Compact job state (about 8 lines): the only thing the supervisor reads while a job runs.
#   wsl bash .../tools/delegate/job-status.sh <id>
id="${1:?job id}"; W="$HOME/work/$id"; . "$(dirname "$0")/env.sh"; LL="$DG_LL"
base="$(cat "$HOME/work/$id.base" 2>/dev/null)"
pid="$(cat "$LL/logs/ralph-$id.pid" 2>/dev/null)"
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then st="RUNNING pid=$pid"
elif [ -e "$W/RALPH_DONE" ]; then st="DONE"
elif [ -e "$W/BLOCKED" ]; then st="BLOCKED: $(head -c 200 "$W/BLOCKED" | tr '\n' ' ')"
else st="STOPPED"; fi
log="$(ls -t "$LL"/logs/ralph-"$id"-*.log 2>/dev/null | head -1)"
echo "state:   $st"
echo "items:   $(grep -c '^- \[x\]' "$W/progress.md") done, $(grep -c '^- \[ \]' "$W/progress.md") left; commits: $(git -C "$W" rev-list --count "$base"..HEAD 2>/dev/null); dirty files: $(git -C "$W" status --porcelain | wc -l)"
echo "next:    $(grep -m1 '^- \[ \]' "$W/progress.md" | cut -c1-110)"
grep -E '^  (Result|Failed):' "$W/progress.md" | tail -2 | cut -c1-170 | sed 's/^/last:    /'
[ -n "$log" ] && grep '^\[ralph\]' "$log" | tail -2 | cut -c1-150 | sed 's/^/ralph:   /'

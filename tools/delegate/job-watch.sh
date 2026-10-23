#!/usr/bin/env bash
# Watchdog for a running job: wait N minutes, then print the compact status once. Run it as a BACKGROUND command; Claude Code
# is re-invoked when it ends. Covers the one case the loop cannot report itself: the loop script hanging (router down,
# sleeping on a quota reset) instead of exiting.
#   wsl bash .../tools/delegate/job-watch.sh <id> [minutes=25]
id="${1:?job id}"; mins="${2:-25}"
sleep $((mins * 60))
exec bash "$(cd "$(dirname "$0")" && pwd)/job-status.sh" "$id"

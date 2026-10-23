#!/usr/bin/env bash
# Run the job's own acceptance (verify.sh) independently of what the agent claims. Prints PASS or FAIL + the last lines.
#   wsl bash .../tools/delegate/job-verify.sh <id>
id="${1:?job id}"; W="$HOME/work/$id"
out="$(cd "$W" && bash verify.sh 2>&1)"; rc=$?
if [ $rc = 0 ]; then echo "PASS"; else echo "FAIL rc=$rc"; echo "$out" | tail -15; fi
git -C "$W" diff --stat "$(cat "$HOME/work/$id.base")"..HEAD -- . ':!progress.md' ':!JOB.md' ':!verify.sh' | tail -12
exit $rc

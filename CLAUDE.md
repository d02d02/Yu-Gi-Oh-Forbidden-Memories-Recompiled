# Project rules for Claude

## Delegated jobs (harness)
- Starting a job = TWO calls in the same turn, never one: `job-run.sh <id> 30` (Bash, background) AND Monitor on `wsl bash -c 'python3 .../tools/delegate/job-pulse.py <id> --exit-on-alert --kill-idle 8'` (timeout 1800000; re-arm on expiry). After /clear, load Monitor first: `ToolSearch select:Monitor`.
- Before landing: `grep -n "^def "` shows every spec'd function; land code + test file only; README row by hand.
- Method: `notes/delegation.md` (Supervisor playbook), alerts: `notes/delegation-audit.md`, router health: `llm-router/scripts/obs.py`.

# Project rules for Claude

## Delegated jobs (harness)
- Starting a job: `job-run.sh <id> 30` as ONE Bash background call; it runs the pulse monitor inside, stops the loop and ends on a wake alert (STUCK-LOOP, ABORT-RUN, STALLED-ITEM). No separate Monitor needed (only for jobs started by an older job-run).
- Before landing: `grep -n "^def "` shows every spec'd function; land code + test file only; README row by hand.
- Method: `notes/delegation.md` (Supervisor playbook), alerts: `notes/delegation-audit.md`, router health: `llm-router/scripts/obs.py`.

# Project rules for Claude

## Delegated jobs (harness)
- Starting a job: `job-run.sh <id> 30` as ONE Bash background call; it runs the pulse monitor inside, stops the loop and ends on a wake alert (STUCK-LOOP, ABORT-RUN, STALLED-ITEM). No separate Monitor needed (only for jobs started by an older job-run).
- Before landing: `grep -n "^def "` shows every spec'd function; land code + test file only; README row by hand.
- Method: `notes/delegation.md` (Supervisor playbook), alerts: `notes/delegation-audit.md`, router health: `llm-router/scripts/obs.py`.

## Disc
- `MEMORIES_DISC=C:\Users\mda\games\iso\ygofm-us.bin` (not set in the shell by default; set it per command). Never ask the user for it.
- Screen checks: the user watches the desktop from a phone. Open one check at a time, leave it running, wait for "checked" before the next. Studio tab launcher pattern: App(ask=False, autostart=False), select `app.studio`, `Session.open(glb, recipe)`; use `C:\Users\mda\AppData\Local\Programs\Python\Python312\python.exe` (has Tk, numpy, Pillow; the project python has no Tk).

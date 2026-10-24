# tools/delegate: hand bounded jobs to the local free-tier harness

## Why
Claude Code (the supervisor) costs Anthropic tokens; the user's local harness (`C:\Users\mda\llm-router`: a LiteLLM router in WSL plus OpenCode and a Ralph loop over free-tier providers) gives a daily quantity of free requests. This kit lets Claude Code write a precise job, let the harness do the typing, and spend its own tokens only on the brief, a few status lines and the final check. Full reasoning, measurements and rules of thumb: `notes/delegation.md`. The harness side (why it is cheaper now): `C:\Users\mda\llm-router\notes\token-optimization.md`.

## What a job is
A shallow WSL-native clone of this repo (`~/work/<id>`, branch `ralph/<id>`) holding three spec files on top:

| File | Role |
|---|---|
| `progress.md` | short: goal, pointer to `JOB.md`, a checklist; each item has a `check:` command. The harness digest reads only its head and Status. |
| `JOB.md` | the full brief: goal, files to read (paths and line ranges), files allowed to change, constraints, acceptance |
| `verify.sh` | exits 0 only when the whole job is done; run by the supervisor, not trusted from the agent |
| `paths.txt` (optional) | gitignore-style patterns; limits the checkout to those paths (plus the three files above) |

Templates: `spec-template/`.

## Scripts (run through WSL; in Git Bash set `MSYS_NO_PATHCONV=1`)
| Script | Does |
|---|---|
| `job-new.sh <id> <spec-dir> [base-ref]` | clone, branch, copy the spec, commit "plan"; base defaults to `feat/native-models-plug-and-play` |
| `job-run.sh <id> [max-iters]` | runs `llm-router/scripts/ralph.sh` on the job until `RALPH_DONE`, `BLOCKED`, a stall or the cap; iteration limit 1800 s; prints the quota first; sets `RALPH_AFTER_ITER` = `after-iter.py`. Start it as a **background** command so there is no polling |
| `after-iter.py` | runs after EVERY iteration (killed ones too): re-runs each item's `check:`, ticks what passes, unticks what no longer passes, commits the working tree. The agent cannot tick on its own word and a kill loses nothing |
| `job-land.sh <id> [test cmd]` | copies the job's changed files (not specs) from the clone's working tree into the project, uncommitted, lists them with line counts and runs the test command; the supervisor then reads the diff and commits specific paths |
| `job-status.sh <id>` | about 8 lines: state, items done/left, commits, next item, last Result/Failed lines |
| `job-verify.sh <id>` | runs the job's `verify.sh` and prints PASS, or FAIL plus 15 lines, then the diffstat |
| `job-watch.sh <id> [min=25]` | watchdog: waits, then prints the status once; run it as a second background command so a hung loop is noticed |
| `job-stats.py <id>` | cost breakdown from OpenCode's own database: model steps, tool calls by kind, tokens |
| `job-trace.py <id> [--full]` | audit: every tool call per session with target and status, the agent's own remarks, files re-read, aborted calls | See `notes/delegation-audit.md`. |
| `job-pulse.py <id> [--idle MIN] [--every SEC] [--exit-on-alert] [--kill-idle MIN] [--verbose]` | live monitor, terse (alerts and ITEM only). `--exit-on-alert`: exits on the first alert so a plain background command wakes the supervisor (no 30-minute Monitor re-arm); `--kill-idle MIN`: kills the hung `opencode run` so the loop restarts a session; full event log in `~/work/<id>.pulse.log`; no model tokens |
| `delegate-prompt.txt` | the prompt every iteration gets: read `JOB.md`, do the first unchecked item, run its check, tick it or write `Failed:`; two failures on one item = `BLOCKED` |

## How, step by step
1. Write the spec directory (copy `spec-template/`): small items, one exact check each, `JOB.md` with exact paths.
2. `job-new.sh <id> <spec-dir>`.
3. `job-run.sh <id> 12` in the background, plus `job-pulse.py <id> --exit-on-alert --kill-idle 8` in the background as the monitor (wakes the supervisor on the first alert or the end; `job-watch.sh` is the older fixed-time watchdog). Full method: "Supervisor playbook" in `notes/delegation.md`; OpenCode usage: "OpenCode quick reference" there; monitoring: `notes/delegation-audit.md`.
4. `job-status.sh <id>`, then `job-verify.sh <id>`; read `job-stats.py <id>` for cost.
5. Land: `MSYS_NO_PATHCONV=1 bash tools/delegate/job-land.sh <id> <python> <tests>` (copies the working tree files, excludes the specs, runs the tests), read the diff, commit the specific paths. Never merge the job branch as is.

## Good and bad jobs
Good: pure-Python modules with a written spec and tests, mechanical refactors with tests as the safety net, golden-file and corpus plumbing, docs conversion. Not for: `src/` C code, anything needing the Windows build, a GL window or the disc, design decisions.

## Safety and limits
The loop commits to its own branch and never pushes; the Windows checkout is never touched. It runs in WSL (Python 3.12 with numpy and Pillow; no GPU, no disc). A job is 3 to 12 items. Budget before starting: `python3 llm-router/scripts/budget.py`; expect roughly 13 requests per iteration after the harness tuning (the first, untuned smoke run cost about 18 requests and 86k tokens per iteration).

## Measured (smoke job, same spec)
Before tuning 54 requests / 258k tokens / 22 failed / 3 iterations; after (Groq `reasoning_content` fix, lean OpenCode config for the loop) 26 requests / 121k tokens / 3 failed / 2 iterations. See `notes/delegation.md` for the causes.

## Harness guards (2026-10-24)
| Guard | Where | Stops |
|---|---|---|
| `write-guard.js` (OpenCode plugin, installed in `llm-router/opencode/plugins/`) | before every agent edit/write | edits of `JOB.md`, `verify.sh`, `protected.txt` and its paths; touching a test file's `__main__` tail; dropping an existing test class |
| `after-iter.py` `passes()` | after every iteration | a pass without tests having run (`Ran N`, N>0, >= `min_tests`), or with a `symbols:` entry missing |
| `after-iter.py` control files | after every iteration | `RALPH_DONE` while items are open or `verify.sh` fails; `BLOCKED` with fewer than 2 `Failed:` lines or when the check ran no tests |
| `after-iter.py` `repair_tests()` | after every iteration | restores a dropped test class or the `__main__` tail |

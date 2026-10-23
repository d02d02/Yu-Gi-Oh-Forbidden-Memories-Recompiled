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
| `job-run.sh <id> [max-iters]` | runs `llm-router/scripts/ralph.sh` on the job until `RALPH_DONE`, `BLOCKED`, a stall or the cap. Start it as a **background** command so there is no polling |
| `job-status.sh <id>` | about 8 lines: state, items done/left, commits, next item, last Result/Failed lines |
| `job-verify.sh <id>` | runs the job's `verify.sh` and prints PASS, or FAIL plus 15 lines, then the diffstat |
| `job-watch.sh <id> [min=25]` | watchdog: waits, then prints the status once; run it as a second background command so a hung loop is noticed |
| `job-stats.py <id>` | cost breakdown from OpenCode's own database: model steps, tool calls by kind, tokens |
| `job-trace.py <id> [--full]` | audit: every tool call per session with target and status, the agent's own remarks, files re-read, aborted calls |
| `delegate-prompt.txt` | the prompt every iteration gets: read `JOB.md`, do the first unchecked item, run its check, tick it or write `Failed:`; two failures on one item = `BLOCKED` |

## How, step by step
1. Write the spec directory (copy `spec-template/`): small items, one exact check each, `JOB.md` with exact paths.
2. `job-new.sh <id> <spec-dir>`.
3. `job-run.sh <id> 12` in the background, plus `job-watch.sh <id> 25` in the background as a watchdog; Claude Code is re-invoked when either ends. Full method: "Supervisor playbook" in `notes/delegation.md`; OpenCode usage: "OpenCode quick reference" there.
4. `job-status.sh <id>`, then `job-verify.sh <id>`; read `job-stats.py <id>` for cost.
5. Land: `git fetch //wsl.localhost/Ubuntu-24.04/home/mda/work/<id> ralph/<id>:ralph/<id>`, read the diff of the files that carry logic, apply the code commits **excluding** `progress.md`, `JOB.md`, `verify.sh`, run the project's own checks on Windows, commit on the working branch. Never merge the job branch as is.

## Good and bad jobs
Good: pure-Python modules with a written spec and tests, mechanical refactors with tests as the safety net, golden-file and corpus plumbing, docs conversion. Not for: `src/` C code, anything needing the Windows build, a GL window or the disc, design decisions.

## Safety and limits
The loop commits to its own branch and never pushes; the Windows checkout is never touched. It runs in WSL (Python 3.12 with numpy and Pillow; no GPU, no disc). A job is 3 to 12 items. Budget before starting: `python3 llm-router/scripts/budget.py`; expect roughly 13 requests per iteration after the harness tuning (the first, untuned smoke run cost about 18 requests and 86k tokens per iteration).

## Measured (smoke job, same spec)
Before tuning 54 requests / 258k tokens / 22 failed / 3 iterations; after (Groq `reasoning_content` fix, lean OpenCode config for the loop) 26 requests / 121k tokens / 3 failed / 2 iterations. See `notes/delegation.md` for the causes.

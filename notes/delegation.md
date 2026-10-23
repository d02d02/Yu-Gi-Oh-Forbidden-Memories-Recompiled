# Delegating work to the local harness (llm-router + OpenCode Ralph loop)

Goal: Claude Code writes a precise job, a free-tier model does the typing in a loop, Claude Code spends tokens only on the brief, a few status lines and the final check. The harness is `C:\Users\mda\llm-router` (see its `HOWTO.md`); this note covers only how this project uses it. Kit: `tools/delegate/`.

## Shape of a job
* A job is a **shallow WSL-native clone** of this repo (`~/work/<id>`, branch `ralph/<id>`), not a worktree: a Windows worktree's `.git` pointer cannot be read from WSL, and the harness commits to whatever branch is current. The Windows checkout and the working branch are never touched while a job runs.
* The job is three files, committed first: `progress.md` (short: goal, pointer, checklist; the harness digest reads only its head and Status), `JOB.md` (the full brief: goal, files to read with line ranges, files allowed to change, constraints, acceptance), `verify.sh` (exit 0 only when the whole job is done).
* Each checklist item is one unit an iteration can finish, with a **check command** under it. The agent may tick an item only when its check passes (`delegate-prompt.txt`).
* Everything the agent needs is in the repo files it can read (docs paths and line ranges in `JOB.md`); the brief points to them instead of pasting them.

## Token-cheap supervision
| Step | Command (run from Git Bash with `MSYS_NO_PATHCONV=1`) | Cost to Claude |
|---|---|---|
| Create | `wsl bash /mnt/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled/tools/delegate/job-new.sh <id> <spec-dir>` | the brief (written once) |
| Run | `wsl bash .../tools/delegate/job-run.sh <id> [max]` as a **background** command | none while it runs: Claude is re-invoked when the loop exits (done, blocked, stalled, max) |
| Look | `wsl bash .../tools/delegate/job-status.sh <id>` | about 8 lines |
| Verify | `wsl bash .../tools/delegate/job-verify.sh <id>` | PASS, or FAIL plus 15 lines, plus a diffstat |
| Land | see below | the diff of the files that matter only |

Do not poll. Do not read the Ralph log except its tail when the state is not DONE. Steer by editing the job's `progress.md` or `JOB.md` inside `~/work/<id>` (the next iteration reads them) or by stopping the loop (`kill` the pid in `logs/ralph-<id>.pid`).

## Landing the result
1. `job-verify.sh <id>` must print PASS (the supervisor's own run, not the agent's claim).
2. In the Windows repo, on the working branch: `git fetch //wsl.localhost/Ubuntu-24.04/home/mda/work/<id> ralph/<id>:ralph/<id>`, then `git diff <base>..ralph/<id> --stat -- . ':!progress.md' ':!JOB.md' ':!verify.sh'`.
3. Read the diff of the files that carry logic (skip generated files and test fixtures), run the project's own checks on Windows, then `git cherry-pick`/apply the code commits excluding `progress.md`, `JOB.md`, `verify.sh`, and commit on the working branch. Never merge `ralph/<id>` as is.

## What to delegate, what not
| Good for the free models | Keep with Claude Code or the user |
|---|---|
| Pure-Python modules with a written spec and tests (recipe reader/validator, state machine, check functions, report JSON) | Anything in `src/` C code, the engine, shaders (needs the Windows build, GL window, disc) |
| Mechanical refactors with tests as the safety net (extract detection from `convert`, make `native_check` return data) | UX judgement, naming, schema decisions |
| Test corpus plumbing, golden-file tests, docs conversions | Disc measurements (SM0), anything that needs `MEMORIES_DISC` |
| Tk widgets from a precise wireframe line list, one widget per item | Reviewing the final diff, running the real editor |

Limits to respect: the loop runs in WSL (no Windows-only build, no GL, no disc); free-tier request budgets are small (`budget.py` before starting; Gemini is usually spent early in the day); a job should be 3 to 12 items; two `Failed:` lines on one item make the agent write `BLOCKED`; the loop never pushes.

## First real job (proposed, waits for the user's go on SM1)
SM1 slice 1 from `notes/studio/build-plan.md`: `tools/hd-models/recipe.py` reader/validator for `recipe-schema.md` with unit tests (pure Python, no disc). Spec draft goes in `tools/delegate/specs/` when started.

## Measured (smoke job, 2026-10-23)
End to end works: create, background run, status, independent verify, fetch back with Windows git (`//wsl.localhost/Ubuntu-24.04/home/mda/work/<id>`). A trivial 2-item job took 3 iterations and cost **54 requests (22 failed, 2 of them 429s) and 258k tokens**, about 18 requests per iteration, far above the harness's "about 5" estimate: the agent explores a 2,800-file repo. Consequences: keep `JOB.md` precise (exact paths and line ranges so it does not wander), give each item an exact check, expect ~15-20 requests per iteration when budgeting (`budget.py` first; about 830 Ralph requests were left, so roughly 40-50 iterations a day), and prefer small jobs. Gemini was already at 0 that day; the work ran on groq, ollama and nvidia.

## Where the cost went (measured from OpenCode's session database, `tools/delegate/job-stats.py <id>`)
The smoke job's 3 sessions made 29 model steps and 26 tool calls: 12 reads (all of them the job's own files: `JOB.md`, `progress.md`, `verify.sh`), 8 bash, 3 write, 3 edit, **no glob, grep or list**. So the agent did not explore the repo, and a code graph (or an index) would not have saved anything here. The 54 requests and 258k tokens are the router's count: about 2 requests per model step (22 failed and were retried, plus helper calls) and about 8k tokens per request, which is the fixed prompt (system prompt, tool definitions, progress digest, history) sent every time. The levers are therefore: fewer steps per item (small items, exact checks), fewer failed requests (provider order in `config.yaml`, see the harness HOWTO), and a short `progress.md` head.

Sparse checkout is available anyway: a `paths.txt` next to the spec (gitignore-style patterns, one per line) limits the clone to those paths plus the three spec files. Tested: 12 files checked out of 2,836. It does not change cost much for jobs that already name their files, but it removes any chance of wandering and shrinks the clone.

## After the harness tuning (llm-router, 2026-10-23)
Cause of the failed requests found: OpenCode echoes `reasoning_content` on assistant messages and Groq answers 400 to it on every turn after the first. Fixed in the router (`ledger_callback.py`, groq only). The Ralph loop now runs OpenCode with `opencode-ralph.json` (7 tools -> 6 without webfetch/todo/task, short system prompt): about 3k tokens per request instead of 6.4k. Same smoke job, before -> after: **54 -> 26 requests, 258k -> 121k tokens, 22 -> 3 failed (all quota 429s), 3 -> 2 iterations, verify PASS**. Details and how to see failures: `C:\Users\mda\llm-router\HOWTO.md`, section "Token cost".

# Delegation audit: watching what a delegated agent does

Why: status lines and token totals say a job is slow or costly, not why. The trace says why. Added 2026-10-23 after `recipe-v1` showed 486k input tokens for little progress. Method of delegating: `notes/delegation.md`. Kit: `tools/delegate/README.md`.

## Source
OpenCode keeps every message and tool call of every session in WSL: `~/.local/share/opencode/opencode.db` (tables `session`, `part`). Sessions of a job are the rows whose `directory` ends in `/work/<id>`. Nothing is sent anywhere; reading costs no model tokens.

## Tools
| Tool | Answers | Cost to read |
|---|---|---|
| `job-pulse.py <id>` | **live**: one line per event, silent otherwise: SESSION, ITEM, COMMIT, TOOL-ERROR (with error text), ABORT-RUN (3 aborted calls), TEST-FAIL, STUCK-LOOP (4 edits of a file), REREAD (3 reads), TIMEOUT-NEAR (80% of iteration limit, no commit), PROVIDER (3+ router failures, with reason), TOKENS (per 100k, per item), IDLE (default 4 min), END (with totals). Start with the Monitor tool (max 30 min per arm, re-arm); 0 model tokens while quiet | 1 line per event |
| `job-status.sh <id>` | running? items done? commits? | ~8 lines |
| `job-stats.py <id>` | sessions, model steps, tokens, tool counts | 2 lines |
| `job-trace.py <id>` | every call: tool, target, status, output size; the agent's remarks; files re-read; aborted calls | ~100 lines; read the last session only |
| `job-trace.py <id> --full` | same, remarks in full | more; use on a suspect session |
| log `llm-router/logs/ralph-<id>-*.log` | loop-level events: iterations, stalls, provider errors | tail 25 |

Run via WSL with `MSYS_NO_PATHCONV=1`. Router view: `python3 llm-router/scripts/budget.py run <project>`; per-call detail: `llm-router/data/ledger.sqlite`.

## When to audit
1. Watchdog fires and the job is still RUNNING with 0 items done.
2. Tokens per item above 100k.
3. A stall counter above 0.
4. Before landing: confirm the diff matches what the trace says was done.
5. After every job: record the findings in the table below.

## What to read in a trace
| Sign | Meaning | Fix |
|---|---|---|
| `error` / `pending` as the last call of a session | iteration killed (timeout) | raise `RALPH_ITER_TIMEOUT`; commit per item |
| same files read 3+ times across sessions | cold start each iteration | put facts in `JOB.md`; smaller items |
| many glob/grep, no write | agent exploring | name exact paths in `JOB.md` |
| edit, test fails, edit loop | spec unclear or item too big | split item; add the expected value to the spec |
| remarks contradict the spec | model ignores `JOB.md` | pin a stronger model for the job |
| "changed nothing" with files on disk | work uncommitted; stall counter misleading | commit per item (prompt rule) |

## Findings log
| Job | Date | Finding | Action |
|---|---|---|---|
| `recipe-v1` | 2026-10-23 | Sessions 1 and 2 ended on pending calls (900 s timeout). Work was on disk, uncommitted, counted as "changed nothing". 25 KB of the same sources re-read 3 to 5 times. 53 steps, 486k tokens in, by the time item 1 was ticked. | Proposed, not yet applied: timeout 1800 s; commit-per-item rule in `delegate-prompt.txt`; known-facts section in `JOB.md`; smaller items; stall counter to count working-tree changes. |

## Open
Apply the proposed changes after `recipe-v1` ends, rerun a comparable job, add the measured result here.

## Monitor gaps found 2026-10-23 (v1 -> v2)
v1 showed `TOOL-ERROR read` with no text. The trace showed the errors were model-side (`Tool execution aborted`, empty input; `read` called without `filePath`), not test failures, which v1 could not tell apart. v2 adds the error text, abort streaks, test failures, re-reads, the timeout warning, router failures and token totals.

Still not covered: a hung model call looks like IDLE only (no view inside the call); the monitor cannot steer (to steer, edit `progress.md` in the job clone or kill the loop); the ledger `source='ralph'` is not per job, so PROVIDER assumes one job at a time; no automatic landing.

## Terse mode (default since 2026-10-23)
`job-pulse.py` prints only: ALERT (ABORT-RUN, STUCK-LOOP, TIMEOUT-NEAR, IDLE, END, PROVIDER with zero successes in the window) and progress (START, ITEM). SESSION, COMMIT, TOOL-ERROR, TEST-FAIL, REREAD, TOKENS and a single PROVIDER need `--verbose`. Reason: the supervisor pays tokens per notification, and a failed test or a provider timeout is routine; the loop recovers by itself.

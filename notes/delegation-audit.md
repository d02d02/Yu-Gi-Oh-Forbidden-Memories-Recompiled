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
| `recipe-v1` result | 2026-10-23 | DONE: 7 of 7 items, 9 sessions, 194 steps, 2.21M input / 37k output tokens (about 316k per item), about 2 h wall clock. Output: recipe.py 573 lines, 132 tests, all pass on Windows Python; review found it matches `recipe-schema.md`. Tool calls: 97 read, 62 bash, 33 edit; 116 explore-type. The agent committed late (two items landed uncommitted), so I copied the working tree and not the branch. | Landed as `ef52520b5`. Review cost (estimate): reading about 700 lines of code plus the schema. Apply the planned fixes before the next job. |

## Open
Apply the proposed changes after `recipe-v1` ends, rerun a comparable job, add the measured result here.

## Monitor gaps found 2026-10-23 (v1 -> v2)
v1 showed `TOOL-ERROR read` with no text. The trace showed the errors were model-side (`Tool execution aborted`, empty input; `read` called without `filePath`), not test failures, which v1 could not tell apart. v2 adds the error text, abort streaks, test failures, re-reads, the timeout warning, router failures and token totals.

Still not covered: a hung model call looks like IDLE only (no view inside the call); the monitor cannot steer (to steer, edit `progress.md` in the job clone or kill the loop); the ledger `source='ralph'` is not per job, so PROVIDER assumes one job at a time; no automatic landing.

## Terse mode (default since 2026-10-23)
`job-pulse.py` prints only: ALERT (ABORT-RUN, STUCK-LOOP, TIMEOUT-NEAR, IDLE, END, PROVIDER with zero successes in the window) and progress (START, ITEM). SESSION, COMMIT, TOOL-ERROR, TEST-FAIL, REREAD, TOKENS and a single PROVIDER need `--verbose`. Reason: the supervisor pays tokens per notification, and a failed test or a provider timeout is routine; the loop recovers by itself.

## Round-2 changes applied (2026-10-23)
From the `recipe-v1` findings: (1) `after-iter.py` runs after every iteration through `RALPH_AFTER_ITER` (new env in `llm-router/scripts/ralph.sh`): re-runs each item's check, ticks, unticks, commits the working tree; (2) the prompt says one item per session, commit, stop; the iteration limit is 1800 s; (3) `spec-template/JOB.md` has "Facts and excerpts" (paste, do not point) and "Given" (read-only tests) sections; (4) `job-land.sh` lands the working tree and runs the tests; (5) `job-pulse.py` has `--exit-on-alert`, `--kill-idle`, a per-job event log and per-item tokens at END; (6) `job-run.sh` prints the quota before starting. Not done: conformance script (goes into the SM2 spec), model pinning, parallel jobs. To confirm with the next job: tokens per item below the 316k of `recipe-v1`, zero killed-with-uncommitted-work iterations.

## Router analysis during `sm2-audit` (2026-10-23, after 5 sessions, 79 steps, 1.47M input tokens)
Source: `llm-router/data/ledger.sqlite` (161 calls since 14:39) plus `~/work/sm2-audit.pulse.log`.

| Provider / model | Calls | OK | Cause |
|---|---|---|---|
| gemini (order 1) | 0 | | daily budget 20/20 spent earlier in the day |
| groq gpt-oss-120b (order 2) | 45 | 3 | free tier 8,000 tokens/min; an agent request is 20-27k tokens, so it cannot succeed |
| ollama (order 3) | 0 | | 140/140 of the loop's share spent |
| nvidia laguna-xs (order 4) | 73 | 39 | 27 "Worker local total request limit reached", 6 read timeouts, 1 decode timeout |
| nvidia nemotron-ultra (order 6) | 38 | 38 | reliable but slow; carried 1.07M of the 1.5M tokens |

Patterns: (1) one provider (Groq) that can never serve the workload adds a failed hop to every call and drives the PROVIDER alert (42 of 45 failures); (2) Gemini and Ollama are spent early, so later iterations of the day run on NVIDIA alone; (3) each failure puts a model in the 120 s cooldown and a started stream cannot fail over, which shows up as IDLE 4+ min and sessions running to the 1800 s timeout; (4) each step sends about 18.8k tokens and sessions re-read the 35 KB `audit.py`; (5) the supervisor was woken about ten times for routine alerts (IDLE, TIMEOUT-NEAR, PROVIDER), each a turn of tokens.

Applied the same day:
- R1 `llm-router/config.yaml`: Groq gpt-oss-120b removed from `plan` and `build` (kept on `chore`). Not committed in llm-router (out of scope for this repo); `git diff` there shows it.
- R2 same file: `build` order is now gemini, ollama, nemotron-ultra, laguna-xs, openrouter, cohere (nemotron 38/38 ahead of laguna 39/73). `plan` unchanged. Revisit when Gemini/Ollama quotas are fresh each morning: laguna is faster when it answers.
- R3 `JOB.md` of `sm2-audit`: a worked recipe for item 4 (which joint to shift, how to compute the expected percent, why to clear the animations), after two sessions ran to the timeout without a commit. Rule: when an item times out twice, add such a recipe, do not wait for a third.
- R4 `tools/delegate/job-pulse.py`: `--exit-on-alert` now wakes the supervisor only for END, STUCK-LOOP, ABORT-RUN and the new STALLED-ITEM (2 sessions in a row hit the timeout with no item ticked). IDLE, TIMEOUT-NEAR and PROVIDER are printed and logged only, and `--kill-idle` handles the hung call in the same process. Arm it with `--kill-idle 8`.
- Not done, your call (R5): a paid tier (Groq Dev, Gemini billing) if free tiers stay this tight.

Result to record: after `sm2-audit` ends, compare tokens per item and sessions per item against `recipe-v1` (316k input per item, 9 sessions for 7 items) and note whether R1/R2 changed the PROVIDER count.

### `sm2-audit` result (2026-10-23)
DONE: 7 of 7 items, 7 sessions, 165 steps, 2.68M input / 34k output tokens (383k input per item, against 316k for `recipe-v1`), about 2 h 40 min wall clock (14:39 to 17:21). Output: `tests/test_studio_audit.py` 702 lines, one real fix in `studio/audit.py` (a skin index of 0 in the recipe counted as "no skin"). Two things I corrected after landing: the agent's README edit had replaced the `split_model` row instead of adding a line (restored), and its audit fix dropped the `or {}` guard (restored). Items 1-3 took one session each; item 4 took two sessions to the timeout with no commit, then ticked in session 6 right after the `JOB.md` recipe (R3); items 5-7 followed in 12 minutes. The real-model corpus (UAL, dragon, angel) runs without error; S0 fails on the empty recipe as it should, the dragon shows S2.chains 68 and S2.root-side 31, the angel S3.dropped. Cost went up against `recipe-v1` despite the smaller task, which points at the free-tier state of the day (see the router analysis above), not at the spec.

## Restarting the harness mid-job (observed 2026-10-23, `sm3-model`)
Questions: does a restart lose the job? Does quitting Claude Code kill background jobs? What happens to the Ralph loop when OpenCode / the router is rebooted?
Observed:
- **Rebooting the router / OpenCode does not stop the Ralph loop.** `ralph.sh` (PID 455493, up ~3 h) stayed alive, but no `opencode` process existed any more: the pulse log read "IDLE ... KILLED 0 opencode process(es)" every 4 to 8 min. The loop waited on a model call that never started and would not recover on its own. `job-status.sh` still printed RUNNING. A reboot of the harness therefore needs the old loop stopped too (`wsl kill <pid>`; PID in `job-status.sh`).
- **Restart = resume, not scratch.** `job-run.sh <id> 12` on the existing clone keeps ticked items and commits (`after-iter.py` re-checks every item and unticks what no longer passes); only the unfinished item restarts as a fresh cold-start session. Scratch only if the clone is deleted and `job-new.sh` rerun. A killed iteration leaves a `wip: iteration N snapshot` commit.
- **Never run two loops on one clone.** Kill the old loop first.
- `/exit` in Claude Code with a running session printed "Session keeps running. Use /stop to end it": the jobs were not affected. `/stop` was not tried; its effect on background jobs is unknown.
- The classifier denied Claude's first process-kill and file-delete attempts; the user ran them. After the user said "do whatever you need", `wsl kill <pid>` of the harness's own loop was allowed.
Rule: before restarting a job run `wsl pgrep -af ralph.sh`; if a loop for the job exists and shows IDLE with 0 opencode processes, kill it, then `job-run.sh` and the monitor.

### Router report: `sm3-model` (2026-10-23 23:48)
206 calls over 99 min, 190 ok (92%), 5,411,072 tokens, 0 wasted (0%).

| model | calls | ok | p50 | p95 |
|---|---|---|---|---|
| openrouter/poolside/laguna-s-2.1:free | 197 | 182 | 8.8s | 122.9s |
| cohere/command-a-plus-05-2026 | 8 | 8 | 4.8s | 8.0s |
| build/build | 1 | 0 | - | - |

Failures: 429 15, other 1

Request size (mean chars) by quarter: 98,615 -> 93,889 -> 68,916 -> 65,684

### Router report: `sm5-placement` (2026-10-24 00:46)
112 calls over 24 min, 112 ok (100%), 2,431,237 tokens, 0 wasted (0%).

| model | calls | ok | p50 | p95 |
|---|---|---|---|---|
| openrouter/poolside/laguna-s-2.1:free | 112 | 112 | 4.8s | 44.3s |

Request size (mean chars) by quarter: 31,543 -> 28,978 -> 34,228 -> 141,388

### Read guard result (2026-10-24)
`sm5-placement` (6 items, specs with pasted facts, "write small" rule, OpenCode plugin `tools/delegate/opencode-plugin/token-guard.js` + the reading rule in `delegate-prompt.txt`): 833k input tokens, 139k per item, 20 minutes, one pass. Earlier jobs: recipe-v1 316k, sm2-audit 383k, sm3-model 691k per item. Also noted: the agent mangled one README row (stray leading space) — always diff the README after landing.

## TODO: false BLOCKED and STUCK-LOOP (observed 2026-10-24, `sm6-timemap`)
- [x] (fixed 2026-10-24: after-iter.py repair_tests restores dropped test classes and the `__main__` tail; spec-template rule added) **Self-inflicted BLOCKED.** The agent deleted the `if __name__ == "__main__":` line of the test file while growing it; `unittest.main()` ended up inside a class, so the item check ran 0 tests ("NO TESTS RAN"). The agent blamed `-k` ("a pytest option", false: unittest supports it), wrote `BLOCKED`, and the loop stopped after 3 iterations with 1/7 items. Fix by hand: restore the line, delete `BLOCKED`, rerun.
  - after-iter.py: treat "Ran 0 tests" / "NO TESTS RAN" as a harness fault, not an item failure; restore the test file tail from the last good commit; do not let the agent's BLOCKED stand if the cause is a zero-test run (delete it and rerun once).
  - spec template: add the rule "never edit or move the tail of the test file (`if __name__ ...` + `unittest.main()`); new classes go above it" (added to sm6-timemap JOB.md only).
  - verify.sh / checks: fail when the test count is 0.
- [x] (fixed: threshold 12) **STUCK-LOOP false alarm.** `job-pulse.py` fires on 7 edits of one file in a session, but specs tell the agent to grow a file by edits of at most 60 lines, so 7 edits is normal. Raise the threshold, or count only edits that do not change the file's size/pass state.
- [x] Monitor armed before the loop exited at once with END (fixed: waits up to 180 s for the loop to start).

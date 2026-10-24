# VIP delegation (highest-quality models)

Two classes of delegation. Pick by the table; the supervisor (Claude Code) writes the brief either way and verifies the result itself.

| | Standard | VIP |
|---|---|---|
| Who works | free-tier models in the llm-router + OpenCode Ralph loop (`notes/delegation.md`) | the best models available (Agent tool, strongest `model`, own git worktree) |
| Work | pure-Python modules with a spec and tests, mechanical refactors, Tk widgets from wireframes | anything in `src/` (C engine, render, control channel), anything that needs the Windows build, GL window or disc, anything that modifies upstream code |
| Where | WSL clone `~/work/<id>`, no build, no GL, no disc | Windows worktree of this repo, full toolchain, `MEMORIES_DISC` per command |
| Cost | free, many iterations | paid; few, large, well-briefed jobs |
| Brief | spec dir + checklist + `verify.sh` | `JOB.md` (goal, files, constraints, acceptance) + a verify command the supervisor runs |

## Two phases for engine work
1. **Make it work.** Smallest change that does the thing, gated so normal play is untouched. No polish.
2. **Harden (the bar for anything that edits existing upstream code).** Only after phase 1 works end to end and the user has seen it:
   * parity: with the feature off, output is byte-identical to before (frame hashes of the existing scenes);
   * tests for every new command and error path, malformed and hostile input to the control channel, bounds and overflow review;
   * sanitizer / warnings-as-errors build of the touched files;
   * independent review by a second VIP agent that did not write the code (`agent-skills:code-reviewer`, plus `security-auditor` on the socket), findings fixed or answered in writing;
   * soak: long scrub/pause/seek runs, no leaks or crashes;
   * diff kept small and commented where it touches existing functions; every touch of an existing function listed in the job's final report.

## Rules
* VIP jobs never push, never edit files outside the brief's list, never touch the main checkout (worktree only).
* The supervisor lands: read the diff of logic files, run the project's own checks, cherry-pick.
* The user gets a heads-up before each start (a `/clear` ends a running agent).

## Actions a VIP agent owns (delegate all of them; the supervisor only briefs, verifies and lands)
Everything between brief and verified result: read the code, design within the brief, write code and tests, build (Windows toolchain), run the game and demos with the disc, capture and judge its own frames, debug and iterate to green, commit in small steps on its branch, update the notes it affects (`notes/*`, README rows), append its own `progress.md` entry, run the hardening list of phase 2, run its own review pass before handing over, and write the final report (files, existing functions touched, how to run, open problems, measured numbers).
Not delegated: the user's eye checks (the agent prepares them: launcher, expected result, one check at a time), the decision to land, push, and anything outward-facing.
Brief template: goal, read-list, allowed files, constraints, acceptance command, report format, plus "you own build, run, tests, docs, progress, commits".

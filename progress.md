# Native models: plug-and-play content + 3D Monsters field attack

Branch `feat/native-models-plug-and-play`, rebased onto upstream master (`e64b91f9c`) 2026-10-22; `native_models` = mod API 19. Pre-rebase history: `backup/native-pre-rebase`. Never a PR; push only to this branch.
This file = resume point (status + open work). `history.md` = what was done, phase by phase. Older long checklists: git history of this file.

## Docs map (read only what the task needs)
| File | Read for |
|---|---|
| `notes/native-models-feasibility.md` | **the current direction**: verdict, stages S0-S9, categories C1-C8, studio design, engine gaps (sec. 8), UX-first (sec. 7) |
| `notes/studio/README.md` | **the studio UX/GUI design set** (decisions, screens, per-stage detail, Tk mapping, engine needs, open questions, clickable mock) |
| `notes/delegation.md` | **delegating work (method: "Supervisor playbook"; OpenCode usage: "OpenCode quick reference") to the user's local llm-router/OpenCode Ralph harness**: kit `tools/delegate/`, token-cheap supervision, landing, measured cost, what to delegate |
| `notes/delegation-audit.md` | **auditing / live-monitoring a delegated job** (what the agent did call by call, event stream instead of waiting for timeouts): tools `job-pulse/trace/stats/status`, when to audit, how to read a trace, findings log |
| `notes/native-models-fit-problem.md` | why the dragon/angel look wrong: the hypotheses and evidence to collect |
| `notes/native-models.md` | modder's how-to: manifest, `model.json`, acts, look, limits, troubleshooting |
| `notes/native-models-dev.md` | engine internals: capture/replay/draw, HDM4 format, coordinates, director, shaders, camera, test traps |
| `notes/adding-a-model.md` | procedure to add a model + the dragon worked example (I) |
| `tools/hd-models/README.md` | the tools |

## Objectives
1. **Plug-and-play content.** Rigged glTF -> working mod in one command, no C/disc/our Blender script: `mod.json`, hand-editable `model.json`, generated binary, PNG textures. Animations, strike timing, size, look, camera shots = data. Errors = notes in the Mods window, never a crash. **Re-scoped 2026-10-23** (feasibility note): reliable for rigged humanoids, guided for creatures.
2. **3D Monsters field attack** (`mod.3d-monsters.attack` = field): native model on its card, attacks, reacts, guards, dies, fades; right depth, no pose mixing, strike on the defender's reaction. Done (M5, M7).

## Decisions
D1 converter to validated package, no new C lib | D2 animation sampling pure C, render side, captured inputs only | D3 native size NOT fed back (`field_DD0`/`field_DC8`; console timing/save-state parity) | D4 arena cinematics = camera on view copy + clip choice, no length change | D5 model key = card id | D6 HDM4 only.
**J (2026-10-23, user):** studio viewport = the real engine over `yfm_control`; one `recipe.json` drives a deterministic `glb + recipe -> package`; Blender stays the hand-off for mesh/weight fixes (not a modeller); **the project starts from the UX and the GUI, only then code**; the user will supply skills for drawing the UX.

## Rules for every change
* `src/game`: `#ifdef MEMORIES_PC` only, no libc/libm (each adds an outside_resident_image stub; must stay "12"), `make match` unaffected. Engine code in `src/pc`.
* Code-mod surface: new exports only, structs have `size`, never change exported layout; 3D Monsters binds new entries with `host->symbol()`.
* Before each push: game build, ctest, 3D Monsters build, Python tests, re-read diff. Small commits.
* Verification: here = Windows, disc via `MEMORIES_DISC`, real GL window. Laptop results come on orphan `test-results` (read-only for me). Milestones = frozen `milestone/native-mN`, failures fixed forward.

## Milestones (all PASS, the user, 2026-10-22; phases A-I detail in `history.md`)
| M | Branch | Covers | Fixes |
|---|---|---|---|
| M1 | `native-m1` (0191bde7) | A | |
| M2 | `native-m2` (5cfc2168) | B | |
| M3 | `native-m3` (afc069ea) | C | |
| M4 | `native-m4` (194aeba1) | D | M4-1 `18ac4081` converter wrote non-whole numbers the game's JSON reader refuses; M4-8 `876c6c85` Windows-path package |
| M5 | `native-m5` (d8bb6a29), `m5.1` (ac43731b) | E1, E4, F | M5-1 `e59e543c` marker packet overwritten; M5-5 `68c85ac1` stray draw at monster load; test build = m5.1 |
| M6 / M7 | | E2/E3 arena / G | PASS |

Placement standard (converter, no engine code): scaled to 373 tall (disc BLS), origin on the vertical axis 159 above the soles, horizontally at the idle feet; `model.json` `scale` (percent about the soles), `offset [x,y,z]`. Mannequin idle = `Idle_Loop`, not `Sword_Idle` (a lunge). Not done, not needed: G3 extra field frames, G4 sounds, F5 fit-to-disc-bounds, E2/E3 (disc contact table; optional, needs disc).

## Status
A-H done and PASS (H1 Library shows the native model on card 364; H3 FM Editor "Native models" tab, suite 506 OK, Tk tab test not run here). ctest 163/163 after rebase (`pc_sdk_launchers` needs a real `python3` on PATH; bash `python` is the Store stub; `pc_user_dir` fails only as root). Dragon: first pass plays in the Library; angel parked. **J: UX design first full pass DONE 2026-10-23 (docs in `notes/studio/`, clickable mock, artifact https://claude.ai/artifact/PYmbyvZJX5LpqU98VYX4rk, copy `notes/studio/wireframes-v1.html`); no studio code yet. Delegation kit and llm-router tuning done (see Local environment).**

## Open work (in order)
1. **J, studio build** (UX done; `notes/studio/README.md` is the map, `build-plan.md` the order). Q1 confirmed by the user 2026-10-23 (structure is final). Next: **SM1 recipe + converter entry** and **SM2 audit/state model** (no disc, no engine needed) and **SM0 reference pack** (disc, this machine). Decided so far: nine-entry rail (S1+S2 = Skeleton), stream low-res frames + pop-out window, no guessed disc reference, per-card scale/offset on the mod entry, attack2 dropped, undo linear per recipe. Skills used for the UX: `vectorlab-ux-skills:*` (web-oriented; the editor is Tk, mapping in `tk-mapping.md`).
2. **I5 dragon worked example** waits on the studio (SM5+); state and facts are in `adding-a-model.md` (dragon section). Goku: user has no model yet.
3. **Delegation (working rule from the user, 2026-10-23: Claude supervises, the harness does the work; Claude spends tokens on briefs, monitoring and review only)**. recipe-v1 landed (`ef52520b5`). Round-2 fixes done (`2d2e73a64`). **SM2 state**: state machine DONE by Claude (`tools/hd-models/studio/state.py`, 29 tests, `ee1c332ab`; written by hand by mistake, the user wanted it delegated) and `studio/audit.py` S0-S3 draft (runs on the corpus: mannequin C1 92%, dragon C2 40% with warnings; untested). **Job `sm2-audit` is CREATED, NOT STARTED**: spec `tools/delegate/specs/sm2-audit/` (7 items: tests for every S0-S3 check, bug fixes only, thresholds frozen), clone `~/work/sm2-audit`. **To start (next step)**: from Git Bash with `MSYS_NO_PATHCONV=1`: `wsl bash /mnt/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled/tools/delegate/job-run.sh sm2-audit 12` as a background command, and `wsl python3 .../tools/delegate/job-pulse.py sm2-audit --exit-on-alert --kill-idle 8` as a second background command. Do nothing else while it runs. This is the first real run of `after-iter.py` and the 1800 s limit: check `job-trace.py` once at the first alert. When END DONE: `MSYS_NO_PATHCONV=1 bash tools/delegate/job-land.sh sm2-audit tmp/pc/tools/python/python.exe tools/hd-models/tests/test_studio_audit.py`, read the diff of `studio/audit.py` only, run the corpus (`tmp/agent/dl-ual/ual.glb` -> C1, `tmp/agent/dragon/dragon.glb`, `tmp/agent/angel/work/angel_rigged.glb` with clips from the UAL glb), commit specific paths, push. Record cost vs recipe-v1 (316k input tokens per item) in `notes/delegation-audit.md`. Then SM0 (disc pack, user machine) and SM3.
4. Not mine: user's LLM model-pipeline draft (`notes/prompt-model-pipeline.md`; `C:\Users\mda\llm-router\pipeline`; review in `...\notes\REVIEW-model-pipeline-plan.md`: not accepted, redo asked).

## Local environment (this machine)
* Python: `tmp/pc/tools/python/python.exe` (3.14, numpy 2.5.4, Pillow 13.0.0). Game build `tmp/pc/game32/memories-pc.exe`; ctest dir `tmp/agent/ct`. PATH needs llvm-mingw+ninja+cmake from `tmp/pc/tools`.
* Capture harness: origin/dev `tools/pc` copied to `tmp/agent/dev` (via `_paths.py`); needs `MEMORIES_DISC`. `field_attack.py` (`--native`, `--arena`, `--clip`, `--start/--every/--frames`) -> `tmp/agent/fx/*`; field attack ~230 frames. Library capture: yfm_control `goto library`, `library_all_cards=1`, r1, right x10, down x6, right x5 (card 364), cross, triangle, square.
* Per run: `MEMORIES_MOD_3D_MONSTERS_<SETTING>=<value>`; `play-bls.ps1` makes its own profile, native via `-NativeModel PKG\model.json`.
* Blender 4.5.10 (winget) for the angel/dragon scripts; inputs under `tmp/agent/angel/`, `tmp/agent/dragon/`.
* **Delegation harness** (user's local llm-router in WSL, `C:\Users\mda\llm-router`, router on 127.0.0.1:4000, OpenCode + Ralph loop on free tiers): kit `tools/delegate/` (README there), protocol and measured cost `notes/delegation.md`. Smoke job passed end to end twice. Run jobs as Bash background commands with `MSYS_NO_PATHCONV=1`; never poll. First real job proposed: SM1 slice 1 (`recipe.py` + tests), waits for the user's go on the studio docs.
* **llm-router tuning done 2026-10-23, STAGED BUT NOT COMMITTED** in its repo (no git identity there; user must set `user.name`/`user.email` and commit): Groq `reasoning_content` 400 fixed in `ledger_callback.py`, ledger columns `err/req_chars/n_tools`, lean `opencode/opencode.json` (interactive, also copied to WSL `~/.config/opencode/`) and `opencode/opencode-ralph.json` (used by `ralph.sh`), `prompts/ralph-system.txt`, notes in its `HOWTO.md` and `notes/token-optimization.md`. Same smoke job 54 req/258k tok -> 26 req/121k tok. The short Ralph system prompt is untested on real jobs.
* **JOB FINISHED (ran 2026-10-23 11:35 to 13:37): `recipe-v1`** = SM1 slice 1, `tools/hd-models/recipe.py` + tests, spec in `tools/delegate/specs/recipe-v1/`, work clone `~/work/recipe-v1` (WSL), branch `ralph/recipe-v1`, log `llm-router/logs/ralph-recipe-v1-*.log`. The user authorized it ("only you have authority on tasks"; the other `llm-router` session's `sm1-recipe` spec was removed). **DONE and LANDED 2026-10-23 (commit `ef52520b5`): recipe.py + 132 tests (SM1 slice 1). Result and cost in `notes/delegation-audit.md` findings log. Monitor `job-pulse.py` (terse; re-arm after /clear), trace `job-trace.py`. **Next, in order**: (1) apply the planned delegation fixes (RALPH_ITER_TIMEOUT 1800, commit-per-item rule in `delegate-prompt.txt`, known-facts section in JOB.md, smaller items, stall counter on working-tree changes), (2) write the SM2 spec (audit/state model, UI-free) and run it as a job with the monitor, (3) SM0 disc reference pack on the user machine, before SM5. Studio Q1 confirmed.

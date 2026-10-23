# Native models: plug-and-play content + 3D Monsters field attack

Branch `feat/native-models-plug-and-play`, rebased onto upstream master (`e64b91f9c`) 2026-10-22; `native_models` = mod API 19. Pre-rebase history: `backup/native-pre-rebase`. Never a PR; push only to this branch.
This file = resume point (status + open work). `history.md` = what was done, phase by phase. Older long checklists: git history of this file.

## Docs map (read only what the task needs)
| File | Read for |
|---|---|
| `notes/native-models-feasibility.md` | **the current direction**: verdict, stages S0-S9, categories C1-C8, studio design, engine gaps (sec. 8), UX-first (sec. 7) |
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
A-H done and PASS (H1 Library shows the native model on card 364; H3 FM Editor "Native models" tab, suite 506 OK, Tk tab test not run here). ctest 163/163 after rebase (`pc_sdk_launchers` needs a real `python3` on PATH; bash `python` is the Store stub; `pc_user_dir` fails only as root). Dragon: first pass plays in the Library; angel parked. **J: documented, nothing built; UX design is next.**

## Open work (in order)
1. **J, UX first**: design the studio (screens, flow per category C1-C8, knobs per stage S0-S9, wireframes, click-through) as an add-on to the FM Editor, using the skills the user will provide. Inputs: feasibility note sec. 2-5, 8; FM Editor facts in sec. 9 there. Code (recipe schema, converter entry, engine viewer commands) is derived from the screens afterwards.
2. **I5 dragon worked example** waits on J; state and facts are in `adding-a-model.md` (dragon section). Goku: user has no model yet.
3. Optional: E2/E3 (disc); delete spare `merge-prep/upstream-master`.
4. Not mine: user's LLM model-pipeline draft (`notes/prompt-model-pipeline.md`; `C:\Users\mda\llm-router\pipeline`; review in `...\notes\REVIEW-model-pipeline-plan.md`: not accepted, redo asked).

## Local environment (this machine)
* Python: `tmp/pc/tools/python/python.exe` (3.14, numpy 2.5.4, Pillow 13.0.0). Game build `tmp/pc/game32/memories-pc.exe`; ctest dir `tmp/agent/ct`. PATH needs llvm-mingw+ninja+cmake from `tmp/pc/tools`.
* Capture harness: origin/dev `tools/pc` copied to `tmp/agent/dev` (via `_paths.py`); needs `MEMORIES_DISC`. `field_attack.py` (`--native`, `--arena`, `--clip`, `--start/--every/--frames`) -> `tmp/agent/fx/*`; field attack ~230 frames. Library capture: yfm_control `goto library`, `library_all_cards=1`, r1, right x10, down x6, right x5 (card 364), cross, triangle, square.
* Per run: `MEMORIES_MOD_3D_MONSTERS_<SETTING>=<value>`; `play-bls.ps1` makes its own profile, native via `-NativeModel PKG\model.json`.
* Blender 4.5.10 (winget) for the angel/dragon scripts; inputs under `tmp/agent/angel/`, `tmp/agent/dragon/`.

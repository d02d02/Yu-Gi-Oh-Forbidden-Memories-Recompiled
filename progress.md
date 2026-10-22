# Native models: plug-and-play content + 3D Monsters field attack

Branch `feat/native-models-plug-and-play`, rebased onto upstream master (`e64b91f9c`) 2026-10-22; `native_models` = mod API 19 (upstream took 17, 18). Pre-rebase history: `backup/native-pre-rebase`. Never a PR; push only to this branch.
This file = action plan + status board. `history.md` = what is done. Full M3-M5 checklists and the long local log are in git history of this file (before the 2026-10-22 compaction).

## Objectives
1. **Plug-and-play content.** Rigged glTF -> working mod in one command, no C/disc/our Blender script: folder with `mod.json`, `model.json` (hand-editable), generated model binary, PNG textures (swap by replacing a PNG). Animations, strike timing, size, look, camera shots = data. Errors = notes in the Mods window, never a crash.
2. **3D Monsters field attack** (`mod.3d-monsters.attack` = field): native model stands on its card, attacks, reacts, guards, dies, fades; right depth vs cards/monsters, no pose mixing, strike on the defender's reaction, the mod's fades.

## Decisions (defaults)
D1 converter to validated package, no new C lib | D2 animation sampling pure C, render side, captured inputs only | D3 native size NOT fed back (`field_DD0`/`field_DC8`; keeps console timing/save-state parity) | D4 arena cinematics = camera on view copy + clip choice, no length change | D5 model key = card id (per draw) | D6 HDM1-3 removed, HDM4 only (old HDM4 files load).

## Verification
* Here (Windows, disc via `MEMORIES_DISC`, real GL window): game build, ctest, mod builds, Python tests, field/arena captures (`tools/hd-models/field_attack.py`).
* Laptop results come on orphan `test-results` (`mN.md`; read-only for me). Milestones = frozen `milestone/native-mN` branches, never pushed again; failures fixed forward (`Fix M<N>-<item>: ...`, unit test, `milestone/native-m<N>.<k>` if needed).

## Rules for every change
* `src/game`: `#ifdef MEMORIES_PC` only, no libc/libm (each adds an outside_resident_image stub; must stay "12"), `make match` unaffected. Engine code in `src/pc`.
* Code-mod surface: new exports only, structs have `size`, never change exported layout; 3D Monsters binds new entries with `host->symbol()`.
* Before each push: game build, ctest, 3D Monsters build, Python tests, re-read diff. Small commits.

## Milestones (all PASS, the user, 2026-10-22)
| M | Branch | Covers | Notes |
|---|---|---|---|
| M1 | `milestone/native-m1` (0191bde7) | A | |
| M2 | `native-m2` (5cfc2168) | B | |
| M3 | `native-m3` (afc069ea) | C | |
| M4 | `native-m4` (194aeba1) | D | fixes M4-1 `18ac4081` (converter wrote non-whole numbers the game's JSON reader refuses), M4-8 `876c6c85` (Windows-path package didn't find model.hdm) |
| M5 | `native-m5` (d8bb6a29), `m5.1` (ac43731b) | E1, E4, F | fixes M5-1 `e59e543c` (marker packet overwritten: monster/glow dropped out), M5-5 `68c85ac1` (stray draw at monster load); test build = m5.1 |
| M6 | | E2/E3 arena | PASS |
| M7 | | G | PASS |

## Phases (A-G done)
* **A** (A1-A7): GlReady only when pass draws; arena camera push only for native slot in arena scene; HDM4 parser hardened; `field_DFE` capture; test switch fixes; `native_model.c` uses `pc/compat/fs.h`; FM Editor API compat.
* **B**: `native_anim.c` (pure C: director, sampling, cross-fade, FK -> bone rows); HDM1-3 removed; GL code stays in `gl_picture.c`; widescreen checked.
* **C** (C1-C7): `NativeState`/`NativeInstance` (`NativeModel_SetInstance`: size, card, context ARENA/FIELD/BIG_CARD/LIBRARY/MEASURE, key, fade, contact_frame), nearest-OT-entry marker, per-key anim state, 24 draws/frame, event log `MEMORIES_TRACE=native|model`.
* **D** (D1-D9): HDM4 binary + `model.json` format 1 (spec: `src/pc/render/native_registry.h`, `notes/native-models.md`); manifest `"native_models": [{"cards":[364],"package":"x/model.json"}]` (mod order = priority); lazy loader, PNG via libpng, texture cap 2048; `tools/hd-models/native_convert.py`, `new_native_mod.py MODEL.glb --card N --out mods/x`, `native_check.py`; round-trip tests.
* **E**: E1 state->clip from `clips` + fallbacks; E4 warp strike frames <-> contact (field done; arena uses BLS's measured warp). E2/E3 (disc contact table `data/native/contact.json`, measure all disc models) = optional, needs disc.
* **F**: 3D Monsters `sort_monster` sets instance (`field_models.c`); depth via marker at nearest entry; fade in composite; optional bind through `host->symbol`. F5 (fit to disc bounds) not wanted: converter standard instead.
* **G**: `model.json` `"shots"` (<=8: yaw/pitch/height/distance%, ease, `from`..`to` frames, `other`), `native_cinematic.c`, `NativeModel_ArenaShot`/`FieldShot`, `fight_shot_orbit` in 3D Monsters. Not done, not needed: G3 extra field frames, G4 sounds (`host->sound_play`); no `shots.json` (shots live in `model.json`).
* **Placement standard** (converter, at source, no engine change): scaled to 373 tall (disc BLS), origin on vertical axis 159 above soles, horizontally at middle of the idle pose's feet (`--height`, `--origin-height`, `--no-center`). `model.json` `scale` (about soles) and optional `offset [x,y,z]` (whole numbers, before scale). Mannequin idle must be `Idle_Loop`, not `Sword_Idle` (a lunge).

## Open work (in order)
1. **H3 DONE (tab test needs Tk: not run here; fm_editor suite 506 OK, 56 skipped)**: FM Editor "Native models" tab** (`tools/pc/fm_editor`): add/remove/pick a package and its cards in a mod's `native_models`; checks from `native_models.py` (exists, with entry checks in validation); register tab in `app.py` like `ArtTab` (`art_tab.py`); copy files into the mod like the Art tab does for PNGs (`project.files`, `validate.py` `has_file`); test; README section; line in `history.md`.
2. H1: Library viewer preview as deliberate option (context LIBRARY): needs the user's call on what the Library shows.
3. **I** (last; gate: A-H stable): written procedure for adding any model (dragon, Goku). I1 draft done: `notes/adding-a-model.md` (untested steps marked). Open: I2 rigging when source has none (humanoid Mixamo/Rigify + `--clips-from` UAL; non-humanoid dragon rig and clips; generic Blender scripts), I3 converter profiles for quadruped/winged/multi-material/hair/cape, I4 sizing/placement checklist "looks wrong -> change what", I5 two worked examples (dragon, Goku) with exact commands + pictures, I6 validation (native_check 0 errors, field+arena captures, tests untouched, no engine change; any needed engine change = pipeline bug fixed first). Needs rigged dragon and Goku glb from the user. Models are third-party fan-made with proper licence: author/licence in package (`--author`, `--license`), no private-use caveat.
4. E2/E3 optional (disc). Angel parked (asset: raised arm/sword, needs `"scale": 65`). Delete spare `merge-prep/upstream-master`.
5. Not mine: user's LLM model-pipeline draft (`notes/prompt-model-pipeline.md`; `C:\Users\mda\llm-router\pipeline`, review in `...\notes\REVIEW-model-pipeline-plan.md`: not accepted, redo asked).

## Status
A-G done (M1-M7 PASS, placement/size PASS). H: H2 done, H3 checks done (`pc_fm_editor_native_models`), H3 picker done, H1 waiting, H4 docs current. I planned. ctest 163/163 after rebase (`pc_sdk_launchers` needs a real `python3` on PATH; bash `python` here is the Store stub). `pc_user_dir` fails only as root (container).

## Local environment (this machine)
* Python: `tmp/pc/tools/python/python.exe`. Game build `tmp/pc/game32/memories-pc.exe`; ctest dir `tmp/agent/ct`. PATH needs llvm-mingw+ninja+cmake from `tmp/pc/tools`.
* Capture harness: origin/dev `tools/pc` copied to `tmp/agent/dev` (found via `_paths.py`); needs `MEMORIES_DISC`. `field_attack.py` (`--native`, `--arena`, `--clip`, `--start/--every/--frames`); outputs `tmp/agent/fx/*`. Field attack plays in ~230 frames.
* Settings per run: `MEMORIES_MOD_3D_MONSTERS_<SETTING>=<value>`; `play-bls.ps1` makes its own profile, native via `-NativeModel PKG\model.json`.
* Blender 4.5.10 (winget) for the angel scripts; inputs under `tmp/agent/angel/`.

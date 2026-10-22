# Native models: plug-and-play content + 3D Monsters field attack

Branch `feat/native-models-plug-and-play`, from `feat/battle-events-log` at `96cd1c3a`
(itself `feat/hd-model-bls` + upstream master). Never a PR. Pushed only to this branch.
This file is the action plan the agent follows, and its status board; `history.md` keeps what is done.

## Objectives and what "done" means

1. **Plug-and-play content.** A modder with a rigged glTF (any common rig) makes a working mod with one
   command and no C, no disc image, no Blender script of ours: a folder with `mod.json`, `model.json`
   (hand-editable metadata), the generated model binary and PNG textures. Textures can be swapped by
   replacing a PNG. Animations, strike timing, size, look and camera shots ("cinematics") are data.
   Errors are notes in the Mods window, never a crash.
2. **3D Monsters field attack.** With `mod.3d-monsters.attack` = field, a native model stands on its card,
   attacks, reacts, guards, dies and fades on the field correctly: right depth against cards and other
   monsters, no pose mixing between monsters, strike on the defender's reaction, the mod's fades.

## Defaults taken (from the analysis; any can be overridden)

| # | Decision | Default |
|---|---|---|
| D1 | Runtime glTF loader or converter | Converter to a validated package; no new C library |
| D2 | Where animation sampling runs | Pure-C module, called where it is now (render side); inputs only from captured data |
| D3 | Native model size fed back into the game (`field_DD0`/`field_DC8`) | No (keeps console timing and save-state parity) |
| D4 | Arena cinematics | Camera (on the view copy) + clip choice; no change of length |
| D5 | Model key | Card id (resolved per draw), not disc model id |
| D6 | Legacy HDM1-3 paths | Removed (HDM4 is the path; HDM4 files keep loading) |

## What the agent can verify here, and what needs the laptop

* Here (cloud container, no disc, no GPU/window): `python3 tools/pc/build_game32.py` (45 s, must keep
  "12 outside_resident_image stubs"), the CMake unit tests (`ctest`), `tools/pc/build_mod.py mods/3d-monsters`,
  Python tests of the converter, pure-C unit tests of the loader/director/pose.
* Laptop (disc + real GL window): every picture. At each milestone (M1..M7) the agent pushes, says so, and
  lists exactly what to run and what to look at. Work continues on the next phase meanwhile only where it does
  not depend on the result.

## Milestones, results and fixes (how work goes on while tests run)

* Each milestone is a frozen branch, `milestone/native-mN` (the session cannot push tags), that the agent never pushes
  to again. Testing it tests exactly that build while development goes on here.
* Results come back on the orphan branch `test-results` (`mN.md` checklists, files under `mN/`; its README says how).
  The agent created it once and only reads it.
* A failed item is fixed forward on this branch: commit `Fix M<N>-<item>: ...`, a unit test where the bug can be
  tested here, a line in the table below; a milestone branch `milestone/native-m<N>.<k>` when the fix needs testing on
  its own.
* Only work a pending result cannot invalidate goes ahead of it: the event layer and the package tooling are tested
  here; visual tuning and the deep field-attack work (F) wait for the milestone that shows them.

| Milestone | Tag | Item | Result | Fix |
|---|---|---|---|---|
| M1 | `milestone/native-m1` (0191bde7) | 1-7 | awaiting | |
| M2 | `milestone/native-m2` (5cfc2168) | 1-3 | awaiting | |
| M3 | `milestone/native-m3` (afc069ea) | 1-5 | awaiting | |
| M4 | `milestone/native-m4` (194aeba1) | 1-8 | items 1 and 8 failed, the rest awaiting | M4-1 `18ac4081` (the converter wrote non-whole numbers the game's JSON reader refuses); M4-8 `876c6c85` (a package named by a Windows path did not find its model.hdm) |
| M5 | `milestone/native-m5` (d8bb6a29) | 1-7 | awaiting | |

## Rules for every change

* Game units (`src/game`): `#ifdef MEMORIES_PC` only, no libc/libm (each adds an outside_resident_image stub),
  `make match` unaffected. Engine code in `src/pc`.
* Code-mod surface: new exports only, structs carry a `size` field, never change an exported layout;
  3D Monsters binds the new entry with `host->symbol()` so it still loads on a game without it.
* Mod API: `native_models` is not released yet; its final shape lands with this work (API number checked
  against upstream at merge time).
* Before each push: game build, ctest, 3D Monsters build, Python tests; diff re-read. Small commits.

## Phases

### A. Correctness fixes (small, first) -> M1

| ID | Change | Files |
|---|---|---|
| A1 | `NativeModel_GlReady` = "the pass will draw this frame": cleared when the picture drops below 2x (`resync`, `native_ready` returning 0) and when the GL picture stops; suppression only then. Fixes the invisible monster at 1x | `gl_picture.c`, `native_model.c` |
| A2 | Arena camera push only when the GL pass is ready AND slot 0 or 1 of the current arena scene (`D_8009AF94 == 15`) has a native mesh. Credits and other battles untouched | `native_model.c`, `model_scene_states.c` |
| A3 | HDM4 parser: 64-bit size arithmetic, every offset checked before it is read, parent < bone and acyclic, joint ids < bones, indices < vertices, clip sizes; malformed = note + disc model | `native_model.c` (+ unit test) |
| A4 | Capture `field_DFE`; the attack is row `field_DFE + 3` (guardian star 2 plays row 4) | `func_800540B4.c`, `native_model.h`, director |
| A5 | Test switch: `MEMORIES_NATIVE_MODEL` without `_ID` = model 363, not 364; every `getenv` read once | `native_model.c`, `gl_picture.c` |
| A6 | `pc_utf8_paths` fails on this branch: `native_model.c` opens files and reads the environment without `pc/compat/fs.h` (mod folders with accents break on Windows) | `native_model.c` |
| A7 | `pc_fm_editor_compat` fails on this branch: the API went to 17 without the FM Editor; teach `tools/pc/fm_editor` API 17 and the `native_models` key | `tools/pc/fm_editor/compat.py` (+ its key lists) |

### B. Factoring, no visible change -> M2

| ID | Change |
|---|---|
| B1 | Revised: the GL code stays in `gl_picture.c` (its OpenGL functions, shader conversion for GLES, picture targets and replay state are that file's own; moving them out means exporting its loader). Everything that is not GL leaves it instead (B3), so the native section there is GL-only |
| B2 | `native_format.c` done in A3; the registry split goes with its rewrite in D (D2/D3) |
| B3 | `native_anim.c` (pure C): director + clip sampling + cross-fade + forward kinematics -> bone rows. Unit tests: sampling, FK, quaternion blend, warp |
| B4 | Remove HDM1-3 (part-posed CPU/GPU paths, retarget, their shaders) |
| B5 | Switches read once (A5), `MEMORIES_NATIVE_CPU` gone with B4; the trace channel goes with the event log (C7), tuning settings with the package `look` (D) |
| B6 | Widescreen: check whether the arena/field draw into the widescreen target; if so composite there too |

### C. Instance + event layer (shared by both objectives) -> M3

| ID | Change |
|---|---|
| C1 | `NativeSlotInfo` -> `NativeState` (versioned): `key`, `card`, `context` (ARENA, FIELD, BIG_CARD, LIBRARY, MEASURE), semantic `state` (IDLE, ENTER, ATTACK, CONTACT, HIT, GUARD, DESTROYED, WIN, RECOVER), row, clock, length, speed, attack row, defence, `fade`, `contact_frames[]`, nearest OT entry |
| C2 | Arena source: key = slot; card from `D_801A7AD8[D_800E9EF0[slot]->field_6A]`; contact from `func_800559D4` (handler returns 3/1/4, or the midpoint fallback), destroyed/win from the rows; contact frames for the attack row from the timing table (E2) |
| C3 | Export for code mods: `void NativeModel_SetInstance(const NativeInstance *)` (`size`, `card`, `context`, `key`, `fade`, `contact_frame`); NULL clears; MEASURE = capture nothing, suppress nothing |
| C4 | The polygon drivers record the nearest entry they would have linked while suppressing; `NativeModel_Link` puts the marker there instead of entry 0 |
| C5 | Cross-fade/animation state per instance key (small table, least-recently-used) |
| C6 | More native draws per frame (24); overflow = disc model, as today |
| C7 | Event log, one line per semantic event (`MEMORIES_TRACE=native`); capture runs without GL when tracing, so it is checkable headless |

### D. Package format + loader + tools (objective 1 core) -> M4

| ID | Change |
|---|---|
| D1 | Revised: the binary stays HDM4 (no `FMNM`: one texture set per model is all the GL pass draws, so the converter packs several materials into one atlas instead of submeshes). `model.json` format 1 (model, textures, clips per act, strike frames, scale, look, name/author/license/source) is specified in `src/pc/render/native_registry.h` and `notes/native-models.md`; sockets wait for a need, cinematics are G's `shots.json` |
| D2 | Manifest: `"native_models": [{"cards": [364], "package": "angel/model.json"}]` (`card`/`cards`; `model` kept as an alias for disc model ids). Several mods, priority = mod order |
| D3 | Loader: lazy (first need, not first frame), PNG through libpng (as `src/pc/cards/art.c`), texture cap (default 2048, a setting), memory budget for the 32-bit build; HDM4 files still load (defaults for the metadata). Revised: nothing to free when a mod is turned off, a `native_models` mod already needs a restart (`mods.c`) |
| D4 | Revised: the converter sizes the model without the disc (the root `--root-height` 300 above the soles, Black Luster Soldier's; or `--height` / `--scale`) and `model.json` `scale` adjusts it about the soles at run time. A run-time fit from the disc model's extents waits for the M4 result (reading them is possible; feeding a size back is not, D3) |
| D5 | Converter `tools/hd-models/native_convert.py`: glTF/glb -> package; rig profiles (Unreal/Quaternius, Mixamo, generic with `--root/--feet`), multi-material, PNG textures (resized to the cap), clip list + semantic guesses by name, strike frame estimate (hand/weapon speed peak), report |
| D6 | `tools/hd-models/new_native_mod.py MODEL.glb --card 364 --out mods/my-mod`: the whole mod folder |
| D7 | Validator `native_check.py` = the engine's checks, offline |
| D8 | Tests: a synthetic rigged glTF made by the test -> package -> C loader unit test (round trip) |
| D9 | `notes/native-models.md` rewritten as the modder's how-to (glb to playing in five steps, limits, licences, troubleshooting) |

### E. Data-driven director -> M5 (E1, E4 on the field) and M6 (E2, E3: the arena)

| ID | Change |
|---|---|
| E1 | Done: state -> clip from `model.json` `clips` (D), the default names, then the fallback chain (guard, destroyed -> hit -> idle; win, enter, the others -> idle) |
| E2 | Disc timing table `data/native/contact.json`: per disc model, attack row -> contact frames (BLS row 3: 29, 61, 95) |
| E3 | Tool to measure E2 for every disc model with the rigkit arena (origin/dev) and the event log; run on the laptop (needs the disc), result committed |
| E4 | Warp: package strike frames <-> contact frames of the instance (arena: table; field: the mod's contact frame); piecewise linear inside the row; no table entry = no warp. Done for the field (the first strike on the instance's contact frame); the arena keeps BLS's measured warp until E2/E3 |

### F. 3D Monsters field attack (objective 2) -> M5

| ID | Change | Files |
|---|---|---|
| F1 | Done: `sort_monster`: instance before `func_800540B4(0)` (FIELD or BIG_CARD, key = the monster's cache entry, which owns its slot state; card, `monster->fade`, contact = attack row midpoint unless the attacker's module decides); `sort_aside`: MEASURE. Nothing to clear: an instance is used by the next slot draw only | `mods/3d-monsters/field_models.c` |
| F2 | Depth: the mod's `nearest` now sees the real entry (C4); check the explicit `at` of `draw_battle`. Read: with the packets left out the scratch table holds the marker alone, at the model's nearest entry, so `nearest` is its depth; `draw_battle`'s `at` puts the whole run, marker included, over the big card. To see on the laptop (M5) | same |
| F3 | Done in C: fade in the composite (`SOFT_GPU_FADE` meaning: 0 opaque .. 255 gone) | `gl_picture.c` |
| F4 | Done: optional binding through `host->symbol("NativeModel_SetInstance")` (mod API 4) | mod |
| F5 | Field size: keep the mod's fit from the disc model; option later to fit the native bounds | - |

### G. Cinematics -> M7

| ID | Change |
|---|---|
| G1 | Spec `shots.json`: shots keyed to events (attack.start, attack.contact, hit, destroyed, win, enter), subject/target (attacker, defender), camera {orbit yaw/pitch, distance, height, look-at}, duration, ease, clip override |
| G2 | `native_cinematic.c`: `NativeCinematic_View(GsRVIEW2 *view, context)` on a copy of the view; arena via `Model_SetArenaView`; field via one call where the mod sets its camera |
| G3 | Field length: the mod already holds step 7 (up to 1200 frames); a shot may ask for extra frames there; arena never changes length |
| G4 | (later) Sounds of a shot on the field through `host->sound_play` |

### H. Ecosystem

H1 Library viewer preview as a deliberate option (context LIBRARY). H2 Angel-specific Blender scripts to
`tools/hd-models/examples/`, no workspace path assumptions. H3 FM Editor (`tools/pc/fm_editor`): the final
`native_models` shape (D2; done: `native_models.py`, the port's entry checks in the editor's validation) and a package picker (open). H4 `history.md` and the developer notes updated per phase.

## Milestones for laptop tests

| M | After | Run | Look for |
|---|---|---|---|
| M1 | A | `play-bls.ps1 -Attack 0 -NativeModel angel.hdm`; toggle Internal 1x/2x in the arena; a battle of two other monsters; the credits | Angel as before; at 1x the disc BLS (not nothing); other battles and credits with the console camera |
| M2 | B | `attack_clip.py` over the same frames as an M1 run | Same pictures (any difference = report) |
| M3 | C | arena attack and field attack (`-Attack 2`) with `MEMORIES_TRACE=native` | The event log (the agent gives the expected sequence); field monster no longer over every card |
| M4 | D | Convert the angel with `native_convert.py` (no disc), install with `new_native_mod.py`; swap `base.png` | Same look; texture swap works without converting again |
| M5 | F, E1, E4 (field) | `-Attack 2`: angel vs disc monster, angel vs angel, guard, destroyed, summon/withdraw fades | Depth right, no pose mixing, strike on the reaction, fades |
| M6 | E2, E3 (+E3 run) | Arena: BLS, BLS with guardian star 2, a second monster with the angel | Strike on the hit each time |
| M7 | G | One `shots.json` in arena and field | Shots play, game timing unchanged in the arena |

## M3 checklist (copy into `test-results/m3.md`)

Build `milestone/native-m3`; the M1 and M2 items hold on it too.

| # | Check | Expected |
|---|---|---|
| 1 | Arena attack with the angel (`play-bls.ps1 -Attack 0`) | as in M1, except that where the arena's effects pass in front of the angel they can now be drawn over it (the model sorts at its own depth); the ground shadow stays under it (a shadow over its feet = report) |
| 2 | The same with `MEMORIES_TRACE=model`; send the log | `evt native ... context=0 key=0 card=364` for BLS and `key=1 card=<the defender>`; at the blow an `evt row slot=1 row=6` (or 5 / 8) with `other_row=3 other_clock=<n>` |
| 3 | Field attack (`play-bls.ps1 -Attack 2`) with the angel | the angel stands on its card at the card's depth, no longer over every card and monster. Not yet right (phase F): two native monsters mix their poses, no fades, strike timing |
| 4 | The Library's model view of Black Luster Soldier, if you reach it | say what shows (the angel or the disc model): it decides H1 |
| 5 | 1x/2x and widescreen as in M1 | as in M1 |

## M4 checklist (copy into `test-results/m4.md`)

Build `milestone/native-m4`; the M1-M3 items hold on it too. `pip install numpy pillow` once for the converter (the checker needs nothing).
The old angel mod can stay applied: an entry for the card wins over its entry for the disc model.

| # | Check | Expected |
|---|---|---|
| 1 | `python tools/hd-models/new_native_mod.py ANGEL.glb --card 364 --out mods/angel-m4 -- --clips-from UAL1_Standard.glb --clips Sword_Attack,Sword_Idle,Hit_Chest,Death01,Idle_Loop` (no `--disc`); send its output | no error; the acts as before (idle Sword_Idle, enter Idle_Loop, attack Sword_Attack, hit Hit_Chest, destroyed Death01, win and guard Sword_Idle); blows near frame 11 (and 30) |
| 2 | `python tools/hd-models/native_check.py OLD_ANGEL.hdm mods/angel-m4`; send its output | 0 errors; the two "bind pose" lines (height, soles below the root) within about 10% of each other. Both numbers decide the default root height if not |
| 3 | Apply "angel-m4" in Mods, restart, Internal 2x, `play-bls.ps1 -Attack 0` without `-NativeModel` | the angel as in M1: size, feet on the ground, lighting, the strike on the hit (any difference = report, with item 2's numbers) |
| 4 | Change `mods/angel-m4/models/<name>/base.png` (tint it in any editor), restart | the tint shows; nothing converted again |
| 5 | Rename `normal.png` away, restart; open the Mods window | the angel still draws (flatter); beside the mod: `textures.normal: normal.png: it cannot be read (the model's own is used)` |
| 6 | The same command as 1 with `--card 1` and the same `--out`; a battle Blue-Eyes White Dragon vs Black Luster Soldier | `mod.json` has one entry with cards [1, 364]; two angels fight, both drawn, the frame rate as with one |
| 7 | Item 3 with `MEMORIES_TRACE=model`; send the log | `evt native ... mesh=<n> ... card=364` for the attacker and the defender's card |
| 8 | `MEMORIES_NATIVE_MODEL=mods/angel-m4/models/<name>/model.json` with the mod off | the angel, as in 3 (the test switch reads packages too) |

## M5 checklist (copy into `test-results/m5.md`)

Build `milestone/native-m5`; the M1-M4 items hold on it too. `play-bls.ps1` makes its own profile (Test scenes, 3D Monsters, HD only),
so the angel comes in through the test switch: `-NativeModel <the M4 package>\model.json` (a package works there since M4).
`MEMORIES_MOD_3D_MONSTERS_<SETTING>=<value>` sets one of the mod's settings for a run.

| # | Check | Expected |
|---|---|---|
| 1 | `play-bls.ps1 -NativeModel PKG\model.json` (attack on the field, the default) | the angel on BLS's card, the Kuriboh the disc's; it crosses, strikes, goes home; depth right against the cards and the Kuriboh |
| 2 | 1 with `MEMORIES_MOD_3D_MONSTERS_EFFECTS=0` | the angel's swing lands as the Kuriboh reacts (the clip's strike on the mod's contact, half the attack row), not early or late |
| 3 | 1 with `-NativeId -2` (every monster an angel) | each keeps its own pose: the attacker attacks, the others idle, none twitches into another's pose; the destroyed one fades away; nearer angels over farther ones |
| 4 | 3 with `-Attack 3` (field, then the attack cards) | the angels on the big cards play their own rows, not the field ones' |
| 5 | 1 with `MEMORIES_TRACE=model`; send the log | `evt native ... context=1 key=<n> card=364` on the field (`context=2` on big cards), `contact=<half the row>` while the attack row plays (-1 with effects on), no `evt native` while a monster loads (its measuring draws) |
| 6 | Summon on (`MEMORIES_MOD_3D_MONSTERS_SUMMON=1`) with 3 | the angels grow from their cards and fade in |
| 7 | `-Attack 0` and Internal 1x | the arena as in M4; at 1x the disc models everywhere |

## Status

| Phase | State |
|---|---|
| M0 setup (branch, plan, build check) | done: game build (12 stubs) + 3D Monsters build pass here; ctest 146/149: `pc_utf8_paths` and `pc_fm_editor_compat` fail because of this branch (A6, A7), `pc_user_dir` fails only because the container runs as root (its chmod test cannot deny root) |
| A | done (A1-A7), awaiting M1 on the laptop; checks here: game build (12 stubs), ctest 149/150 (`pc_user_dir` = root container), 3D Monsters build, new `pc_native_format` under ASan/UBSan 32+64-bit |
| B | done (B1 revised, B3, B4, B6; B2/B5 folded into C/D), awaiting M2; checks here: game build (12 stubs), `gl_picture.c` strict (-Wall -Wextra -Werror), ctest 151 with `pc_native_anim` new, only `pc_user_dir` fails (root container) |
| C | done (C1-C7), awaiting M3; checks here: game build (12 stubs), `gl_picture.c` strict, ctest with `pc_native_capture` new (instances, suppression, marker entry, camera) and `pc_native_anim` extended (acts, per-monster memory), only `pc_user_dir` fails (root container) |
| D | done (D1, D3, D4 revised; D2, D5-D9), awaiting M4; checks here: game build (12 stubs), `gl_picture.c` strict, ctest with `pc_native_registry` and `pc_native_tools` new (a rigged glb made by the test, converted without the disc, checked, made into a mod, read back by the game's loader), `pc_native_capture` / `pc_native_anim` updated, only `pc_user_dir` fails (root container); registry and capture tests under ASan/UBSan 32+64-bit |
| E | E1 done, E4 done for the field, in M5; E2/E3 (the arena's contact frames) wait for the measurement on the laptop (M3's event log shows them for BLS) |
| F | F1, F2 (read), F3 (in C), F4 done, in M5; F5 waits for M5's pictures; checks here: game build (12 stubs) with the 3D Monsters mod, `native_anim.c` strict, ctest with `pc_native_anim` extended (fallbacks, the warp on a contact frame, guardian star 2, the arena unchanged), only `pc_user_dir` fails (root container) |
| G | planned (waits for M1's camera results: shots build on the arena camera) |
| H | H3's checks done (`pc_fm_editor_native_models`); H1 waits for M3 item 4; H2 done (the Blender scripts hold no path; the capture scripts find the dev tools and the game by `_paths.py`); H3's picker open |

## Local log (this machine, Windows; newest last)

* 2026-10-22: `tools/hd-models/field_attack.py` (new): the field attack (3D Monsters attack=2) in a real GL window, one frame per run,
  with a contact sheet; `--native` turns on the `native-test` mod (a package for card 364). Needs `MEMORIES_DISC` set to the .bin and the
  dev tools in `tmp/agent/dev` (see `_paths.py`). The fa-* runs of the earlier session sat at step 2 because of their setup; this setup
  plays the whole attack in about 230 frames (steps 1, 2, then the field). Vanilla sheet: `tmp/agent/fx/van/sheet.png`.
* 2026-10-22: field attack with the native model, seen here (`tmp/agent/fx/{van,nat,natc}/sheet.png`): both monsters stand on their cards, the
  attacker crosses, strikes and goes home, the depth is right, no pose mixing. One bug found and fixed (M5 item 1 would have shown it): a
  monster's packets the drivers make but do not link while a native model draws (`model_polygon_drivers.c`) had no tag word, so the 3D
  Monsters mod's `stamp_bank` (which walks a monster's packets in memory) read garbage lengths and wrote over the marker packet now and then:
  the standing monster vanished on some frames and the disc model's glow went with it. The drivers now write the tag's length. Trace lines
  added (`MEMORIES_TRACE=model`): `evt walk` (the markers the frame's list holds) and `evt pass` (what the GL pass did with each marker).
  ctest 152/152 here. Still open for M5: the strike's timing against the defender's reaction (stills cannot show it), other monsters, fades.
* 2026-10-22, M5 checks here (mannequin, `tmp/agent/fx/`): item 1 ok (`nat`, `natc`); item 2 ok (effects off: contact=75, the blow at row frame 75, the swing at full reach as the flash lands, `fx0`); item 3 ok (`all`: attacker and defender keep their own poses, the defender falls and is gone, no mixing); item 5: `contact=-1` with effects on and 75 with them off, as expected, but ONE stray draw (context 0, key 0, card 0) is captured and drawn on the frame each monster loads (f=7, f=13): the game's own slot draw during the mod's load, open; item 4: attack=3 shows only the flat big cards with and without native models (same as vanilla), nothing to compare; items 6 (summon) and 7 (arena at 1x) not run yet.
* 2026-10-22, the angel: Blender 4.5.10 installed (winget); rigged with the repo's scripts (inputs rebuilt under `tmp/agent/angel/`: the UAL as UE-named glb from its FBX, a decimated Angel; `angel_swords_and_islands.py` copy picks the largest island instead of asserting one), 69 bones, `native_check` 0 errors; plays the field attack (`tmp/agent/fx/ang2/sheet.png`) at `"scale": 65` (at 100 the wings overlap the neighbour). Open: the left arm and sword stay raised (the sword-carry pose does not follow the clips).
* 2026-10-22: Fix M5-5: the game's own draw of a slot with no packets and no battle (the slot a code mod is loading a monster into) is no longer captured (`NativeModel_EndSlot`), so the one stray native draw at each monster's load is gone (`pc_native_capture` updated). The angel stays parked: its raised arm and sword are the asset's (the sword-carry pose of the Blender step), not the engine's; M5 goes on with the mannequin. `field_attack.py` now plays the first turn's card face down on the far zone so only the attacker stands in view.
* 2026-10-22, M5 item 7 ok here (`field_attack.py --arena`, `tmp/agent/fx/ar1`, `ar2`): the arena attack at 1x shows the disc Black Luster Soldier and Key Mace throughout; at 2x the native model replaces BLS only. Item 6: the fade-in reaches the pass (`fade` 255 -> 0 over the first frames of a monster in the log, a half-transparent model in the 2x frames); the summon's own growth from the card is not captured separately. The end of the field attack (the attacker walking back, the board returning to the 2D field) is clean. All M5 items that stills and logs can show are done here; what is left of M5 is the laptop's: the strike's timing in motion and the look on a real GPU. G waits for M1's camera results, E2/E3 for the disc measurement on the laptop, H3's picker is a GUI change.
* 2026-10-22: `model.json` `"offset": [x, y, z]` (whole numbers, game units, the model's own axes, before `scale`): a nudge for where the model stands on its card (the user saw the mannequin a little behind and right of the card). Parsed in `native_registry.c`, applied in `native_anim.c`, checked by `native_check.py`, tests in `pc_native_registry` / `pc_native_anim`. On the field camera, for the attacker: -x toward the viewer, +z to the left (`[-60,0,40]` tried; `tmp/agent/fx/o2_cmp.png`). The value for the mannequin and for the angel is the user's to pick by eye.
* 2026-10-22: the mannequin "standing a little behind" is not the origin: its pelvis (the root) lands on the card's centre (compare `tmp/agent/fx/by_cmp.png`: Black Luster Soldier, the mannequin with idle = Sword_Idle, the mannequin with idle = Idle_Loop). The UAL's Sword_Idle is a deep lunge whose feet sit well forward of the pelvis, so the body looks behind its feet; with `clips.idle` = Idle_Loop (upright) it stands on the card like the disc model. So the fix is the clip choice (data), not a placement change. `offset` stays as an optional nudge (default none).

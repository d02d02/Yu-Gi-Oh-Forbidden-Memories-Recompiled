# 03 Playbook per use case

Conventions: `R` = `python -I C:\Users\mdahh\.claude\shared\yfm-notes\dev-tools\recipes\rigkit.py`; `Game` = `tools/pc/yfm_control.py`.
Always look at **1x first**, then 2x/4x from the saved state. Use `--exe` / `$YFM_EXECUTABLE` to aim at an official install or a PR build,
`--repo` at another checkout. Determinism: **D1** = same inputs, same frames (virtual clock, channel); **D0** = needs eyes/real window.

## U1 Card frame / card layout (anime style, frame slots)  [D1]
- Hand + viewer: `R hand --deck <ids> --press triangle --steps 2 --scale 2 --settings mod.anime-art=1 mod.anime-art.full_bleed=1 --out <dir>`.
- Trap beside attacker, attack timing: legacy `..\rigs\trap_rig.py / attack_rig.py` (fix the `sys.path` line first) until P1 #5.
- Stage log: `--env MEMORIES_TRACE=card_layout MEMORIES_LOG=<file>`; `slot_for / image_for / bank_read` timings.
- Evidence: old|new sheet at 1x+2x, timing (attack: plain 17-24 s; a Slifer > 150 s means eviction thrash).
- Traps: the mod applies only with its own enable key (+ `full_bleed`); Internal 2x/4x needs `MEMORIES_DUMP_PICTURE=1` (rigkit sets it).

## U2 HD overhaul / static assets / HD text  [D1 at 1x, 4x via state]
- One screen at a time, picture per step (user's rule). `goto("library"|"options"|"password"|"build_deck"|"map")` then `shot` at 4x with `MEMORIES_DUMP_PICTURE=1`.
- Reach the screen at 1x, `save`, load into 4x game (rigkit's two-stage pattern; add a `goto` kind when needed).
- HD pack path (textures at Internal > 1x): `hd_shot.py` (feat/hd-overhaul). Retest the "black frame at 4x" claim with the channel `load` route before trusting a manual-only rule.
- No automated HD text check yet: smoke case at 4x on name entry (`MODE_AT` 9) is the planned one.

## U3 3D Monsters / field art / Duel Links 2D Arts / 2D Monsters  [D1 for placement, D0 for GL polish]
- Scene: `R scene --set <plain|trap|equip|magic|ritual|modified|mixed|trapritual> --scale 2`, or set zones via `MEMORIES_MOD_TEST_SCENES_P1..5/O1..5`.
- Mods conflict: `3d-monsters` vs `duel-links`/`2d-monsters`: set the other off (`mod.3d-monsters=0`).
- Cutout sizing/clipping: scene at 1x and 2x with art mod on; compare to vanilla (`mod.<id>=0`).
- GL-path pictures in a real window: `MEMORIES_WINDOW_SHOT` (D0). HD pack at 4x is the known weak spot: add to the mod QA matrix (02 #9).
- `MEMORIES_MOD_3D_MONSTERS_TEST=<id>` fills every zone; model cache 8 < 10 zones thrashes: one-frame dumps only.

## U4 Duel logic, effects, AI  [D1; assert on data, not pixels]
- `Game`: `goto("duel", opponent=n, deck=...)`, `duel_ready(before_deal=lambda g: g.arrange_deck(0, [...]))`, then `play_card/fuse/attack/end_turn`, and assert on `state()`/`field()`/`duel()` (LP, hand, flags).
- Pattern to copy: `tools/pc/test_duel_effects.py` (20 scenarios, native vs interpreter). AI: `smoke_ai_hard_mode.py`, `test_ai_hard_mode.py` (Linux/mac prebuilt tools).
- Keep a failing scenario as a `scripted` replay in `tests/pc/replays/` (`replay.py record OUT --scripted file.py`): it survives timing changes.

## U5 PGXP / precise geometry / rendering correctness  [D1]
- `scene_measure.py state` (redo after every rebuild) -> `controls` (must print "controls: pass") -> `compare --scales 2,4` -> `trace` (fork-only `MEMORIES_PGXP_MEASURE`) -> `bench --pgxp 0,1 --scale 4 --speed -1 --repeat 5`.
- Evidence: measured numbers (M1 texel shift, M2 mixed triangles, M4 vertex offset, M5 gaps, M6 wobble A/B) vs "seen by eye": mark which.
- PR text: observed problem -> fix -> observed result; ask the user for Off vs Textures of one frame at his internal resolution.

## U6 Performance / slowdowns / hangs  [D1 for work done, wall time varies]
- Time a fixed scenario on A and B exe (attack scenario, scene bench); compare vblanks (deterministic) and wall seconds (noisy, repeat 3).
- Slowness at scale: expected ~40x per doubling headless; a state-from-1x shot is the cheap probe.
- Hangs: `tmp/pc/hang-*.txt/.dmp` (crash monitor), `MEMORIES_TRACE` timings. Kill orphans after every timeout.

## U7 Other screens (build deck, library, password, map, trade, credits, options)  [D1 except trade]
- `goto(...)` then `shot`/`state()`. Trade needs a live session with an owned deck (route: escape Simon's duel to the shop, save, Circle to title, Trade); `MODE_AT` leaves inventories empty.
- Own cards without a save: `MEMORIES_DEBUG_DECK` / `DEBUG_CHEST` need `Cheats_SaveLoaded()` (`goto("duel")` path satisfies it); otherwise `poke` owned cards.
- Library has its own state machine; test first/last card, empty rows, sorted lists.

## U8 Data mods / FM Editor / Kuriboh ROM-hack port  [D1 data asserts]
- `python tools/pc/fm_editor import <iso> --game game\ygofm-orig-usa.bin --id kuriboh`; assertions in `tools/pc/kuriboh/test_*.py`; editor tests `cd tools/pc; python -m unittest discover -s fm_editor/tests -t .` in background to a file (492 tests, minutes). Never run the editor GUI or `test_gui` headless.
- In game: `Game(mods_dir=...)` with the imported mod, `goto("duel", opponent=40..55)` for extra duelists (they start from dialogue scripts, not menus), assert on `state()`.

## U9 Fresh-install / compatibility with the official release  [D0, scripted where possible]
- Official v0.3.0 vs fix pack vs PR: `C:\YFM-fresh\v030-official\{official,fixpack,pr}`, `run-fresh.bat <install> <set>`, own `MEMORIES_USER_DIR`. Scripted equivalent: `R scene --exe <install>\memories-pc.exe --set <set>` with the install's mods (`mods_dir`).
- Fresh profile: `tools/pc/reset_fresh_user.py`; mods linked only on opt-in (`hacking\CLAUDE.md`).
- v0.3.0's `portable.txt` does not work ("cannot create user"); use `MEMORIES_USER_DIR`.

## U10 Engine PR to upstream (Unchiga)  [mixed]
- Branch directly on `upstream/master` (`origin/master` on the fork is stale); small increments, one screen, A/B picture each step.
- Gate (see `05` R1): 1x A/B on every affected scenario, timing, vanilla run unchanged (pixel-identical when the feature is off), `make check-pc` where possible, list what is NOT verified (Linux/mac/Android, CTests on Windows).

## U11 A player's bug report -> repro  [manual until phase 2]
- Ask for: build/version, settings.txt, active mods + order, language, internal scale, steps. Reproduce on the fresh official install first (U9), then in a scenario; once reproduced, keep it as a scripted replay or a scenario with an assertion.

## U12 Save/settings/user-folder behaviour  [D1]
- Always a throwaway `MEMORIES_USER_DIR` (`Game` does this); `test_state_resume.py` for state resume; never point two builds at `shared\user\states`.

## U13 The game's own 3D models (native animated battle, not the 3D Monsters mod)  [D1]
- Scene = debug menu entry `3D` -> `MAIN_MODE_ANIMATED_BATTLE` (1): colosseum, summoning circle, two 3D monsters, attack. `rigkit.py arena --models <idA>,<idB> --stage 0-6 --vb 900,1300,1900 --scale 4`.
- Choose the pair by writing the scene's records before it starts (`rigkit.enter_arena`); ids = card ids; the scene uses id-1. Stage = terrain 0-6 (random when the debug controller rerolls).
- For model/texture work (HD models, model replace): A/B two builds on the same pair/stage/vb with `pxkit diff`; shots at 4x cost ~21 s from the saved state.
- Not covered yet: model ids the controller refuses (300-349, 650-699, 720 are excluded by its random draw but pokes bypass it: check it renders), per-model animation names, camera control in this scene.

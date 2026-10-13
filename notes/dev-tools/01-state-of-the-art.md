# 01 State of the art (2026-10-13)

## A. Layers, from cheapest to most human

| # | Layer | Where | What it gives | Status |
|---|---|---|---|---|
| 1 | **Env vars** (`MEMORIES_*`) | `..\pc-headless-testing.md`, `src/pc/platform/settings.c` | Headless/deterministic run, scripted pad (`INPUT`, raw PSX bits), `MODE_AT`, `DEBUG_DECK/CHEST/STARCHIPS`, `DUMP_FRAME/PATH/PICTURE`, `SAVE_STATE/LOAD_STATE`, `FRAME_HASHES`, `INTERNAL_SCALE`, `SCALE_AT`, `MOD_<ID>_<KEY>`, `SETTINGS`, `USER_DIR`, `TRACE`, `LOG`, `WINDOW_SHOT`, `RECORD/PLAY`, `CONTROL` | Works; blunt (see traps) |
| 2 | **Control channel + `Game` client** | `tools/pc/yfm_control.py`, `src/pc/debug/control*.c`, `notes/agent-control.md` | TCP lockstep: `step`, `pad`, `shot`, `hash`, `peek/poke`, `save/load`, `info`, `jump`. Python: `goto(target, opponent, deck)`, `duel_ready(before_deal)`, `arrange_deck`, `play_card`, `fuse`, `attack`, `end_turn`, `wait_until`, `state()`, `field()`, `duel()` | **Works well (measured below).** Foundation of everything else |
| 3 | **Recorder / replays** | `src/pc/debug/recorder.c`, `tools/pc/replay.py`, `tests/pc/replays/` (10: build-deck-add, credits, dark-hole, first-duel, full-duel, menus, spellbinding, state-load-cpu, state-load-rng, x64-data-mods) | Per-VBlank pad stream + frame-hash checkpoints; `recorded` (exact) and `scripted` (survives timing changes) kinds | Exists upstream; **`replay.py run` printed nothing in 280 s here** (recordings carry `scale=4`, built on other builds): not a proven gate on this machine |
| 4 | **Smoke / CTests** | `tools/pc/smoke.py`, `tests/pc/smoke/*.json` (10 cases), `make check-pc`, CMake CTests | Frame-hash cases (need the disc); portable C tests | CTests run in CI, **not on Windows**; smoke needs disc, local gate only |
| 5 | **test-scenes mod** (v1.1) | dev `mods/test-scenes/` (`sets/*.json`: plain trap equip magic ritual modified mixed trapritual; `run-set.ps1`), backup `..\test-scenes-env\` | Duel vs Simon Muran with 5+5 chosen monsters face up (hold L1 + confirm Option on title); env `MEMORIES_MOD_TEST_SCENES_P1..5/O1..5` | Works, **now fully scriptable through the channel (measured, ~7-9 s)**. Monsters only; set `hand` keys ignored by 1.1 |
| 6 | **Measurement harness** | `tools/pc/scene_measure.py` (branch feat/test-scenes / dev) | `state`, `controls`, `compare --scales`, `trace` (needs fork-only `MEMORIES_PGXP_MEASURE`), `bench` (ms/frame, state hash) | PGXP-specific but the pattern (state -> compare -> bench) is the model for generic A/B |
| 7 | **One-off rigs** | `..\rigs\` (`trap_rig`, `view_rig`, `attack_rig`, `compare_sheet`, `setcard_seq`, `edge_track`, `size_track`, `migrate_hd_json`) | Card-frame bug filming, attack timing, old|new sheets | Worked for the anime-frame investigation; **hardcode `...-anime\tools\pc` (worktree gone) and a dead job tmp**; superseded by `recipes/rigkit.py` for hand/scene |
| 8 | **HD A/B** | `hd_shot.py` (branch feat/hd-overhaul): headless A/B at 4x in ~25 s; `hd_auto_pack.py`, `hd_sprite_pack.py` | One screen, picture per step | Branch-local, not on dev |
| 9 | **Fresh-install matrix** | `C:\YFM-fresh\v030-official\{official,fixpack,pr}` (`run-fresh.bat <install> <set>`), `C:\YFM-fresh\v23fresh`, `hacking\yfm-v0.3.0-fresh`, `tools/pc/reset_fresh_user.py`, `shared\new-worktree.ps1`, `play.bat` | Official release vs fix pack vs PR build, own `MEMORIES_USER_DIR` each | Works; manual (human plays) |
| 10 | **Diagnostics** | `MEMORIES_TRACE=card_layout,mods` + `MEMORIES_LOG`, crash/hang reports (`tmp/pc/hang-*.txt/.dmp`, ~16 present), Help > System info, `profile_report.py`, `bench_board.py` | Stage-by-stage logs, timings, hang dumps | Works; recipe "submitted but not drawn" in `worktree-lessons.md` |
| 11 | **Data / editor tests** | `tools/pc/fm_editor/tests` (492, minutes, run in background), `tools/pc/kuriboh/test_*.py`, `test_duel_effects.py` (20 scenarios, native vs interpreter, 1 min 41 s upstream) | Rules/data assertions | Many `tools/pc/test_*.py` need prebuilt guest tools / macOS arm64: **not on Windows** |
| 12 | **Mod build + package** | `tools/pc/build_mod.py`, llvm-mingw, `package.py`, `test_package.py`, zips by Python `zipfile` | Mod `.o` per target, release zips, fix packs | Works; recipe in `worktree-lessons.md` / `..\duel-links-mod.md` |
| 13 | **Release plumbing** | `.github/workflows/pc-release.yml` (draft release on tag), fork releases via API with `git credential fill` token (no `gh`), Discord post text `..\duel-links-discord-post.md` | Upstream release flow; fork mod releases | See `05` |

## B. Measured on 2026-10-13 (dev `tmp/pc/game32`, build id a6dddcda, Windows, headless, virtual clock)

| Action | Time |
|---|---|
| `Game()` boot + connect | 0.5 s |
| `goto("duel", opponent=3, deck=...)` + `duel_ready()` -> dealt hand, `state()` shows deck/hand/LP | **2.4-2.7 s** at Internal 1x |
| Same at Internal 2x / 4x (with `MEMORIES_DUMP_PICTURE=1`) | **30 s / 100 s** (finishes; the "hang" in old notes is ~40x slowness) |
| `save` / `load` through the channel | instant (<0.1 s) |
| Load a 1x-made state into a **4x** game via the channel, `step 30`, `shot` | **~1 s**, real 1280x960 picture |
| Same load via `MEMORIES_LOAD_STATE` at startup | **black frame** (do not use) |
| Cold boot -> title -> Start -> 4x Down -> L1+Cross on OPTION -> test-scenes duel (mode 3, 5+5 monsters) | 7-9 s |
| `rigkit.py hand --scale 4` end to end | 4.7 s; `rigkit.py scene --scale 2` 8.3 s |
| `replay.py run` (10 replays) | no output in 280 s: unproven |

`shot()` is 320x240 VRAM unless the game is launched with `MEMORIES_DUMP_PICTURE=1`; then it is the scaled picture (640x480 at 2x, 1280x960 at 4x).

## C. What the control client can already do (so do not rewrite it)
`goto` targets: debug, duel, free_duel, build_deck, library, password, map, credits, options, title. Duel actions:
`arrange_deck(side, ids)` before the deal (`duel_ready(before_deal=...)`), `play_card(slot, face_up, star)`, `fuse([slots])`,
`attack(column, target)`, `end_turn()`, `wait_turn()`. Reads: `state()` (mode, starchips, deck, chest, LP, hand with ATK/DEF/flags),
`field()` (4x5 grid), `peek/poke/u8/u16/u32` by address or name from `config/pc/guest_addresses.txt`. Harness button names
(`cross`, `triangle`, `l1`, `down`, `start`...) are translated; use them, not raw hex. Hex bits are the raw PSX SIO layout (not `input.h`).

| 14 | **camera-pin mod + rigkit `attack`** (2026-10-13) | dev `mods/camera-pin/`, `tools/pc/rigs/rigkit.py` | Pin the duel camera (pad-2 mailbox), shoot at named battle sub-steps | New, tested on clean upstream |

| 16 | **`rigkit ab`** (2026-10-13) | `recipes/rigkit.py` | A/B of a situation across two builds or a setting | New; PASS and FAIL cases both verified |

## D. Facts that are easy to forget (each cost time once)
- States are tied to the exact exe (build id in the name); a `game32` state does not load in `game32dbg`. Redo after every rebuild.
- `goto("title")` from boot returns during the Konami logo; the menu needs ~1800 vblanks. Menu order: NEW GAME, LOAD, 2P DUEL, TRADE, OPTION.
- Mod settings in a run: `MEMORIES_MOD_<ID>_<KEY>`; a fresh profile's bool reads 0, not the manifest default; `mod.<id>=1` in the settings file enables a mod.
- test-scenes: every zone card must be a monster or the scene falls back to Options; the `.o` must be rebuilt after source changes.
- A live `memories-pc.exe` locks the exe link ("Permission denied" in play.bat); `Game` kills its own game; killed scripts leave orphans (`taskkill /F /IM memories-pc.exe`).
- Windowed `Game` freezes unless stepped (virtual clock); GL-path pictures in a real window: `MEMORIES_WINDOW_SHOT`, not `DUMP_PATH`.
- Trade needs a live session (empty inventories under `MODE_AT`); Library has its own state machine; `MODE_AT` skips real setup.

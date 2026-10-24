# tools/hd-models: make and test native models (HDM4)

Background and the full explanation: [`notes/native-models-dev.md`](../../notes/native-models-dev.md) (what and why), [`notes/native-models.md`](../../notes/native-models.md) (the mod side).
Python needs numpy + pillow for the converters (+ imageio-ffmpeg for videos; `native_check.py` needs nothing); run with `python -I`. Blender 4.5 for the `blender/` scripts (`blender -b FILE.blend --python SCRIPT.py`; some read environment variables, see each header).

The modder's path (no disc, no Blender script): `new_native_mod.py` -> edit `model.json` -> `native_check.py`; the how-to is
[`notes/native-models.md`](../../notes/native-models.md). Tests: `tests/test_native_tools.py` (CTest `pc_native_tools`).

| Tool | What it does |
|---|---|
| `recipe.py` | reads and validates a studio `recipe.json`, maps it to converter arguments and model.json members |
| `studio/audit.py` | S0-S3 checks over a glTF (licence, mesh/skin, skeleton mapping, materials); `studio/state.py` stage machine |
| `studio/timemap.py` | S6 time map: default_map, monotonic/stretch/strike checks, row<->clip mapping, suggest_point, run_s6 |
| `studio/look.py` | S7 look defaults and camera-move list: default_look, normalize_look, move count/range/values/extreme checks, brightness check, run_s7 |
| `studio/runs.py` | S8 run list and marks: run_rows, make_mark, owning_stage, row_status, status_table, coverage/problem/stale/disc checks, run_s8 |
| `studio/package.py` | S9 package checks: parse_native_check, native/budget/identical/provenance checks, valid_package_name, run_s9 |
| `studio/placement.py` | S4 (size and placement) maths: `fit`, `footprint_ratio`, `check_footprint`, `check_ground`, `check_uniform_scale`, `run_s4` over a glb, headless |
| `studio/rail.py`, `knobs.py`, `checkrows.py`, `studio/session.py`, `run_audit.py` | the Model Studio's UI-free view layer for S0-S3: rail rows, knob tables, check rows, editing/undo/debounce session and the `run_audit.py` CLI |
| `new_native_mod.py MODEL.glb --card 364 --out mods/my-mod [-- converter options]` | the whole mod: converts into `models/<model>/` and writes or updates `mod.json`'s `native_models`, then checks it |
| `native_convert.py MODEL.glb OUT_DIR [--clips-from X.glb] [--root-height 300] ...` | a rigged glTF -> a package: `model.hdm` (own skeleton + clips), `base.png` (+ normal, metal/roughness), `model.json` (clips per act guessed by name, strike frames from the hand's speed). Rig profiles ue / mixamo / generic; several materials packed into one texture; unskinned props follow the bone above them |
| `native_check.py PATH...` | a mod folder, a `model.json` or an `.hdm` checked as the game checks it (plain Python): the same reasons, then each model's size, clips per act, strike frames, textures, memory. Also measures an older `.hdm` (its height and soles) |
| `native_spec.py` | the formats and limits the three share (plain Python) |
| `rigged_to_hdm4.py MODEL.glb OUT.hdm --card 364 --clips-from CLIPS.glb` | the first converter (superseded by `native_convert.py`): fits the model to the disc model's legs, so it needs the disc image (`--disc`, default `game/ygofm-orig-usa.bin` of the main checkout) |
| `gltf_to_hdm.py`, `hmd_export.py`, `vendor/` | helpers the converters import (glTF reader, disc model reader; `gltf_to_hdm.py`'s own HDM2 output is no longer drawn by the game); `hmd_export.py CARD OUT` also exports a disc monster's model to glTF |
| `vendor/split_model.py RECORD.bin OUT_DIR`, `vendor/reassemble_model.py OUT_DIR RECORD.bin` | for tinkering with a disc model record: split it into its 17 phase files (one `.bin` per phase, named as in `model_record.PHASES`) and glue them back; the round trip is byte-identical (`tests/test_record_tools.py`). Small helpers, not part of the native-model path |
| `blender/angel_on_mannequin_weights.py` + `common.py` | Blender: dress the mannequin's rig with another mesh (weight transfer, rigid props, wing bones, bridge-face cut) |
| `blender/angel_swords_and_islands.py` | Blender: reassemble/carry the swords, drop floating pieces |
| `blender/export_rigged_glb.py` | Blender: export the skinned glb the converter reads |
| `blender/debug_*.py` | Blender: colour islands, zoomed views, locate sword fragments |
| `attack_window_gpu.py OUT --exe EXE --native X.hdm [--env K=V]` | creates `OUT/attack.state` (needs the dev checkout's `tools/pc` rigkit/yfm_control) and takes frame-exact GL window shots of the arena attack |
| `watch_attack.py STATEDIR --native X.hdm [--speed 100]` | replays the saved attack in a real window at normal speed |
| `attack_clip.py`, `make_video.py` | every frame of a stretch from one run -> mp4/gif |
| `attack_window_evlog.py` | the event log run (rows, phases) with `MEMORIES_TRACE=model` |
| `camera_distance_from_log.py` | eye-to-look-at distance per frame from a `cam` log (see its docstring) |
| `play-bls.ps1` | start the BLS test duel (Test scenes mod linked + rebuild needed); `-Attack 0` = the game's own arena attack |

Paths: the capture scripts (`attack_*.py`, `watch_attack.py`, `save_moment.py`) take `yfm_control.py` and `rigs/` from origin/dev's `tools/pc` and the game from `tmp/pc/game32/memories-pc.exe` (see `_paths.py`); `YGO_DEV_TOOLS` and `YGO_EXE` override, `--exe` too. `attack_clip.py --state` still defaults to the old workspace's saved state.
Assets (models, textures, the Quaternius pack) are NOT in the repo: the Quaternius Universal Animation Library is CC0; the AI-made angel's licence is unknown (private test asset).

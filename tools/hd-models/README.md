# tools/hd-models: make and test native models (HDM4)

Background and the full explanation: [`notes/native-models-dev.md`](../../notes/native-models-dev.md) (what and why), [`notes/native-models.md`](../../notes/native-models.md) (the mod side).
Python needs numpy + pillow (+ imageio-ffmpeg for videos); run with `python -I`. Blender 4.5 for the `blender/` scripts (`blender -b FILE.blend --python SCRIPT.py`; some read environment variables, see each header).

| Tool | What it does |
|---|---|
| `rigged_to_hdm4.py MODEL.glb OUT.hdm --card 364 --clips-from CLIPS.glb` | a rigged glTF -> an HDM4 file (own skeleton + clips + optional normal/metal-roughness maps). The converter. Needs the disc image (`--disc`, default `game/ygofm-orig-usa.bin` of the main checkout) for the disc skeleton it fits to |
| `gltf_to_hdm.py`, `hmd_export.py`, `vendor/` | helpers the converter imports (glTF reader, disc model reader; `gltf_to_hdm.py`'s own HDM2 output is no longer drawn by the game); `hmd_export.py CARD OUT` also exports a disc monster's model to glTF |
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

Paths: several scripts locate the dev checkout's `tools/pc` and the disc image relative to a workspace layout (`hacking/<checkout>/...`); pass `--exe`, `--disc` or edit the constants at their top.
Assets (models, textures, the Quaternius pack) are NOT in the repo: the Quaternius Universal Animation Library is CC0; the AI-made angel's licence is unknown (private test asset).

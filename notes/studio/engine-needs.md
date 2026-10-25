# What the screens ask of the engine and converter

Deduplicated from `studio-view.md` (S4-S6 so far). Baseline today: `../native-models-feasibility.md` sec. 8. Each item cites the screen that needs it.

## Engine / control channel (`yfm_control`)
| id | Need | Used by | Today |
|---|---|---|---|
| E1 | Load a package or recipe result at runtime, with replace (no restart) | all engine stages | **partly done** (E1 reload): `native reload` re-reads all packages (registry reset, env kept), `native get` replies `entries=N bytes=M` over `yfm_control`; still no load of a new path at runtime |
| E2 | Draw a model without a captured disc slot (synthetic injection point) | viewer without game state | none |
| E3 | Commands: set act, set clip by name, set phase/row phase, pause, speed, scrub | S4-S8 transport, S5, S6 | **done** (E3 transport): `anim clip|pause|resume|speed|phase|frame|get` over `yfm_control`; phase/frame feed the normal `anim_frame` path, inactive = unchanged |
| E4 | Camera presets (field, arena, side, top, free orbit) | S4, S7 | **done**: `cam preset front|side|top|three-quarter|close`, `cam set yaw pitch dist height`, `cam off`, `cam get` |
| E5 | Line/wire drawing in the 3D pass: bones, footprint grid, ghost outline, markers, bbox | S2, S4, S6 | **done** (not pixel-tested: `shot`/`hash` read VRAM, the GL pass is only in the window): `ov bbox\|grid\|bones on\|off`, `ov off`, `ov get`; lines go through the model\'s own skinning program, drawn over the model |
| E6 | Read back data: bounding boxes, lowest point, joint positions per frame | S4 checks, S6 | **partly done**: `ov bounds` (bind-pose box and lowest point of the last drawn model); joint positions per frame stay on the Python side (clipdata) |
| E7 | Frame capture of the GL pass to the editor (window shot or stream) | all | **phase 1 done**: `studio/stream.py` `FrameStream` polls `shot`+`hash`, yields changed frames at a capped rate; measured rate from `stream_demo.py --selftest` only, real rate to be measured by the user (phase 2 = C command if too slow); `MEMORIES_WINDOW_SHOT` glReadPixels, windowed only |
| E8 | Disc-model compare: play the disc's BLS same act beside the native one | S6, S7 | **done as A/B toggle** (window only): `native show disc\|native` draws the disc monster or the model in the same frame; no side-by-side |
| E9 | Time map consumed by the render-side sampler (data, not logic; D2/D3 hold) | S6 | **done** (E9): `timemaps` in model.json -> `NativeAnim_TimeMapClip` in `NativeAnim_Choose`; recipe `acts.<act>.timemap` -> package via `recipe.py` |

## Converter / Python
| id | Need | Used by |
|---|---|---|
| C1 | Dict entry point `convert(recipe)`, findings returned as data (not printed) | all |
| C2 | Clip statistics: loop gap, root drift, joint speed peak, bone stretch, per-clip bbox | S5 |
| C3 | Retarget with rest-pose correction (library clips) | S5 |
| C4 | Procedural clip generators (recoil, collapse, brace, lunge, rise) | S5 |
| C5 | Time-map and strike-joint writing into the package | S6 |
| C6 | Writes `scale`, `offset`, `look`, `shots`, `ground_offset` into `model.json` | S4, S7 |
| C7 | Byte-identical output (pinned libs, one JSON formatter, glb hash) | S9 |
| C8 | Bind-vs-rest report | S1 |

| C9 | Category detection (skeleton shape, humanoid profile, wing chains) extracted from `convert` as data with evidence | S0 |
| C10 | Python-side skinning for a bind-vs-rest overlay and region report, no engine needed | S1, S2 |
| C11 | Blender round trip: convert .blend/.fbx, open-and-return with re-read | S0, S1 |
| C12 | Atlas builder returning materials, density and drops as data | S3 |
| C13 | Engine facts to confirm by reading `gl_picture.c`: emissive, vertex colour, alpha handling | S3 |

## Data not in the repo
| id | Need | Used by |
|---|---|---|
| D1 | Disc ground truth: row length per act per monster class, contact frame per attack, camera shots | S6, S7 |
| D2 | BLS outline and the card footprint dimensions | S4 |
| D3 | A test corpus (one glb per category) | all |

## Decision 2026-10-24: two engine routes, both validated, decide at the end
* **Route A, no game changes:** the studio launches the game per preview with env vars (`MEMORIES_NATIVE_MODEL`, `_CLIP`, `MEMORIES_MOD_3D_MONSTERS_*`) and captures frames with `MEMORIES_WINDOW_SHOT` / `field_attack.py`. No live scrub; slower. Built first (`studio/preview.py`).
* **Route B, engine hooks E1-E9:** live control channel in the recompiled game. Built only after A is measured.
* Both get the same acceptance test (same model, same act, same frames); pick on speed, robustness and maintenance cost.
* **Route A status 2026-10-24:** `studio/preview.py` (command builder, disc check, frame list; 4 tests). NOT yet run against the game: no disc on this machine. Validation to do on the disc machine: run `preview.start("field", out, <pkg>/model.json, 364)`, time it, compare frames with a plain `field_attack.py --native` run (must match), measure launch-to-first-frame seconds. Record numbers here for the A-vs-B decision.
* **Route A measured 2026-10-24 (dragon package, card 364, disc on this machine):** field attack, 3 shots (frames 60/120/180): **17 s** total, dragon drawn on the field, textured, animating, much larger than a normal monster (S4 says 871% wider than the footprint). Arena: 6 shots (300-500, ~25 s) show the arena with a panning camera and NO monster in frame; frames 30-150 are the card display. Arena framing/timing for the model is NOT yet found (`frames` is the last frame, not a count). Cost of route A: about 6 s per extra shot, no live scrubbing.
* **Route A, arena resolved 2026-10-24:** frames 1250-1650 (every 80, ~40 s) show the arena fight (from `notes/adding-a-model.md`). Dragon is drawn, textured and animating but FILLS the screen (far too large, camera too close): matches S4's 871% footprint finding, so size fit, not the preview, is the open problem. `preview.WINDOW` holds the measured windows.
* **CORRECTION 2026-10-24 (route A):** the earlier "route A measured" lines above were INVALID. The game ignores `MEMORIES_NATIVE_MODEL` for a package that is not an installed mod; a bogus package path still drew the dragon, because `game32/mods/dragon-test` was installed and on. Three different packages gave byte-identical frames. Fixed: `preview.install(mod_dir, game_mods())` copies the built mod to `game32/mods/studio-preview`, `preview.command` switches it on and the other test mods off (`mod.<id>=1/0`). Verified: a scale 0.3 build draws a tiny dragon, default and `--height 320` builds differ. Cost: install is a file copy, run 24 s (arena, 3 shots) to 40 s (6 shots). Dragon is still far too large with the defaults and with `--height 320`; the right size options are still to find (S4's job).
* **Size search 2026-10-24 (dragon, arena, installed mod):** `--extent 600` looks right next to the opponent (frames in job tmp, cmp-ext.png); 400 and 250 look small; default and `--height 320` are huge (height mode sizes a flying pose by its height, wrong for a wide creature). BUT S4's footprint check (`placement.check_footprint`, proxy box not yet measured) fails extent 600 ("214% wider") and only passes ~250. The check compares the wingspan with the card footprint; for winged models it is too strict. To decide: measure the footprint on the body (feet/torso, not wings), or make the check a warn for category wings. Recommended S4 default for C2 (wide creatures): mode extent.

## Route A vs B, scoping 2026-10-24 (dragon, card 364, disc on this machine)
* **A works end to end** through the Studio tab: Build package (S9, ~1 min, byte-identical twice) -> Run installs `studio-preview` and runs `field_attack.py`. Field 17-55 s, arena 25-40 s; frames judged from the sheet (dragon textured, animating, normal size at extent 600, camera unchanged). Gaps: no live scrub or pause, one scene per launch, library turntable not built, no wire overlays (E5), no disc-beside-native compare (E8).
* **Minimum B worth building if A feels slow:** E3 (set act/clip, pause, speed, scrub) + E7 (stream frames to the editor). E1 (hot reload) follows from E3. E2/E4/E5/E6/E8 only if the viewer needs ghost, bone overlay or disc compare; S4-S9 checks do not need them (placement and S6 run in Python on the glb and the reference pack).
* **Not decided.** The user has not judged A. Do not start C work until they say A is too slow or lacks scrub.

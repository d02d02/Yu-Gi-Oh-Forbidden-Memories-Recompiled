# What the screens ask of the engine and converter

Deduplicated from `studio-view.md` (S4-S6 so far). Baseline today: `../native-models-feasibility.md` sec. 8. Each item cites the screen that needs it.

## Engine / control channel (`yfm_control`)
| id | Need | Used by | Today |
|---|---|---|---|
| E1 | Load a package or recipe result at runtime, with replace (no restart) | all engine stages | restart needed; `MEMORIES_NATIVE_MODEL` forces one package |
| E2 | Draw a model without a captured disc slot (synthetic injection point) | viewer without game state | none |
| E3 | Commands: set act, set clip by name, set phase/row phase, pause, speed, scrub | S4-S8 transport, S5, S6 | clip is an env var read once, free-running clock |
| E4 | Camera presets (field, arena, side, top, free orbit) | S4, S7 | game camera; `NativeShot` is the nearest hook |
| E5 | Line/wire drawing in the 3D pass: bones, footprint grid, ghost outline, markers, bbox | S2, S4, S6 | none; overlay API draws text and rectangles only |
| E6 | Read back data: bounding boxes, lowest point, joint positions per frame | S4 checks, S6 | none |
| E7 | Frame capture of the GL pass to the editor (window shot or stream) | all | `MEMORIES_WINDOW_SHOT` glReadPixels, windowed only |
| E8 | Disc-model compare: play the disc's BLS same act beside the native one | S6, S7 | none |
| E9 | Time map consumed by the render-side sampler (data, not logic; D2/D3 hold) | S6 | strike warp only |

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

# Build plan (draft, 2026-10-23)

UX is designed to a first full pass (`studio-view.md`, `recipe-schema.md`). This plan orders the code. Rules from `progress.md` apply to every step: `src/game` only under `#ifdef MEMORIES_PC` and no libc/libm, `make match` unaffected, engine code in `src/pc`, code-mod surface additive, small commits, push only to this branch, the user verifies on their machine and milestones are frozen as `milestone/studio-sN`.

The order puts everything that needs no engine first, so the studio is useful (S0-S3, recipe, converter) before the engine viewer exists.

| Step | Delivers | Needs | Verified by |
|---|---|---|---|
| **SM0 Reference pack** | Measurements from the disc, stored in `native-studio/reference/` so later steps do not need the disc: BLS outline, card footprint dimensions, row length per act per monster class, BLS contact frame (attack), camera shots. Closes Q4, enables Q7's answer. | disc (`MEMORIES_DISC`), capture harness | the numbers match two independent runs; a README says how each was measured |
| **SM1 Recipe + converter entry** | `recipe.json` v1 reader/validator; `convert(recipe) -> package` dict entry point over today's `native_convert`; findings returned as data; `native_check` returns findings; deterministic output (sorted keys, one JSON formatter, source hash); migration stub. CLI wrapper keeps today's flags working. | `recipe-schema.md` | Python tests: dragon, angel and mannequin build twice to identical bytes; every flag maps to a recipe key and back |
| **SM2 Audit + state model (UI-free)** | Module with the stage state machine (todo/pass/warn/fail/stale, dependencies, acknowledgements, autosave, undo history); S0-S3 checks as functions (category detection with evidence, bind-vs-rest, bone merge report, weights, atlas); report JSON. Corpus started: mannequin (C1), dragon (C5), angel (C3). | SM1 | Python tests with golden reports; the angel fails `S1.bind-vs-rest` and names the region |
| **SM3 Tk shell, S0-S3** | Studio tab in the FM Editor: Models list, rail with groups, panel, knobs, checks, footer, recipe autosave, undo/redo, Blender hand-off buttons (launch and re-read), subprocess polling. Works end to end for S0-S3 with a static preview (no engine). | SM2, `tk-mapping.md` | GuiCase tests where a display exists; logic tests headless; the user opens a glb and walks S0-S3 |
| **SM4 Engine viewer** | `yfm_control` commands and engine changes for E1-E7: load package/recipe result with replace, set act/clip/phase, pause/speed/scrub, camera presets, minimal line overlays (bones, grid, markers), frame capture to the editor; "Pop out game window". Hot reload of a package. | SM3, `engine-needs.md` E1-E7 | scripted run loads the dragon, plays each act, captures frames; no change to `make match`; ctest |
| **SM5 S4 + S5** | Size/placement with ghost, footprint and origin drag; act table, clip statistics, loop closing, root-motion removal; procedural clips (recoil, collapse, brace, lunge, rise); library retarget for humanoids. | SM0, SM4, C2-C4 | dragon and mannequin fit and play every act in the viewer |
| **SM6 S6 timing** | Time-map editor, strike joints, stretch factors; the render-side sampler reads a time map (data only, D2/D3 hold); BLS compare overlay. | SM0 ground truth, SM5 | dragon attack strike lands within 3 frames of the contact frame |
| **SM7 S7-S9** | Look and camera-move list; S8 run list with scripted scenes; S9 build panel with `native_check` data and the twice-built identity check. Per-card overrides in `mod.json` (Q11) and loader sharing. | SM6 (sm7-look landed: look.py, 37 tests; UI, S8, S9 remain) | a model goes glb to packaged mod in the studio; the user plays it |
| **SM8 Corpus + docs** | One glb per category C1-C8 with expected reports; regression run; modder's how-to updated; laptop and macOS pass. | all | corpus run in CI-like script; laptop results |

Order notes
* SM1 and SM2 can start now; they need neither the disc nor the engine.
* SM0 is the only step that must run on this machine with the disc; do it before SM5.
* If time is short, SM0-SM3 already give a usable "recipe + audit + guided conversion" without any engine work.

## Decisions taken while writing this plan (2026-10-23, delegated to Claude)
* **Q7**: S0-S3 never need the disc. S4-S7 use the reference pack from SM0 when the disc is absent. S8 field and arena scenes need the disc; the library turntable does not.
* **Q4**: the BLS outline and footprint come from measurement (SM0), not from guesses.
* **Q8**: undo is one linear history per recipe, one entry per knob change or per completed viewport gesture, Ctrl+Z / Ctrl+Y, restores values and marks later stages stale.
* **Q9**: both: "Reset to auto" per stage, and a small back-to-auto control on every knob changed from its auto value.

## SM3 split (2026-10-23)
The delegation harness has no display, so a Tk check would skip and pass vacuously. SM3 is therefore two parts. **SM3a** (delegated, job `sm3-model`, spec `tools/delegate/specs/sm3-model`): the UI-free layer in `tools/hd-models/studio/`: `rail.py` (rail rows, footer gating), `knobs.py` (S0-S3 knob tables as data), `checkrows.py` (check rows with fix targets), `session.py` (open a glb, run stages on a cached model, inputs digest and silent return of unchanged stale stages, 300 ms debounce, autosave, undo), `run_audit.py` (the subprocess the tab polls). **SM3b** (not delegated): the thin Tk tab on those modules in `tools/pc/fm_editor/`, written and checked on the Windows machine.

## Status (2026-10-25, end of day)
| Step | State |
|---|---|
| SM0-SM2 | done |
| SM3 | done (Tk shell S0-S9, resolutions R1-R7 with buttons, S0 Choose card, S1/S2 Open a rigged glb) |
| SM4 | engine side done: E1 reload, E3 transport, E4 camera presets (`cam`), E5/E6 overlays and bounds (`ov`), E8 A/B toggle (`native show`), E9 time map in the sampler. Studio window: S8 "Scrub the attack live..." with slider, Play/Pause, shot, camera presets, bbox/grid/bones, show disc model. Window-only parts (overlays, A/B) cannot be pixel-tested headless: `shot`/`hash` read VRAM |
| SM5-SM7 | knobs and checks done for S4, S6, S7 (text controls, time map `pairs`); a recipe edit reaches the engine on the next live scrub (preview rebuild) |
| SM8 | corpus C1-C8 golden clean; how-to updated; laptop and macOS pass not done (needs those machines) |

Open: only the user's visual checks (list in `notes/studio/screen-checks.md`) and the laptop/macOS pass.

## Status (2026-10-26)
| Item | State |
|---|---|
| Model preview panel (`fm_editor/model_view.py`, math in `studio/view3d.py`, 16 tests) | done: mesh, bones, per-bone weight heat, unweighted bones red, bounding box, camera presets, clip playback on the skinned mesh (own and library clips). Screen checks 16-17 |
| `S2.mapped-unweighted` audit warn | done (angel: foot_l carries no weights) |
| Preview overlays per stage (S4 footprint and ghost, S6 strike joint) | not built |
| New 3D model for a card with no model (beyond replace) | not verified: `mod.json` entries key on existing card ids; whether the engine accepts an id without a disc model is unchecked (read `src/pc/mods/mods.c` native_models parse and `NativeMesh_Choose`) |
| Laptop and macOS passes | need those machines |
| Your visual checks | rows 10-17 of `screen-checks.md` |

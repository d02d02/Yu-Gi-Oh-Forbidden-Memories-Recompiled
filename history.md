# History: feat/native-models-plug-and-play

* 2026-10-17: branch made from `feat/battle-events-log` at `96cd1c3a` (native HDM4 models in the arena:
  own skeleton and clips, GPU skinning, PBR-lite, `native_models` manifest key, tools in `tools/hd-models`).
  Plan in `progress.md`. Baseline here: `tools/pc/build_game32.py` builds (610 game units, 12
  outside_resident_image stubs) and builds the bundled 3D Monsters mod.
* Phase A (correctness):
  - A1: `NativeModel_GlReady` now means "the pass draws": cleared below 2x (`resync`), when the pass is not ready, when
    the skinning program is refused and when the GL context is lost (`native_forget`); the game leaves a model's packets
    out only when `GlReady` and the software GPU records at 2x or more. Before, a switch to 1x hid the monster entirely.
  - A2: the arena camera push only in scene mode 15 when slot 0 or 1 is drawn natively (`NativeModel_WillDraw`); before,
    any loaded model pushed every battle's and the credits' camera.
  - A3: `src/pc/render/native_format.c`: the HDM4 file checked whole (64-bit counts, every offset, parents, cycles,
    joints, indices, clips) with the reason in the Mods window; test `pc_native_format` (every truncation, each
    corruption, heap copies of the exact size so a sanitizer sees an over-read).
  - A4: the attack is row `field_DFE + 3` (`NativeSlotInfo.attack_row`): the second guardian star's attack (row 4) plays
    the attack clip (no time warp yet: only row 3 of Black Luster Soldier is measured).
  - A5: the test switch defaults to model 363 (was 364, card 365's model); the pass reads its switches once.
  - A6: `native_model.c` goes through `pc/compat/fs.h` (`pc_utf8_paths`).
  - A7: FM Editor knows API 17 and `native_models` (`pc_fm_editor_compat`); modding.md lists the key.
  - The converter refuses more than 16 clips (the game's limit) instead of writing a file the game refuses.
* Phase B (factoring):
  - B3: `src/pc/render/native_anim.c`: the director (`NativeAnim_Choose`) and the pose (`NativeAnim_Rows`: clip sampling,
    cross-fade, forward kinematics, the skinning rows) moved out of `gl_picture.c` unchanged but for their inputs
    (`NativeAnimFrame`: picture offset, scale, lit, tuning); test `pc_native_anim` (rows -> clips incl. the second guardian
    star, Black Luster Soldier's warp, a forced clip, forward kinematics, row 128, the cross-fade and a replayed draw).
  - B4: HDM1-3 removed (the part-posed CPU and GPU paths, the retarget, their shaders, buffers and switch
    `MEMORIES_NATIVE_CPU`, the legacy loader): about 730 lines; such a file is refused with a note naming HDM4.
  - B6: widescreen: the model was laid into the 4:3 picture only, so with widescreen on (shown from the wider target)
    neither it nor the disc model showed; it is now copied into the wide target's centre (`wide_mirror`). A part past the
    4:3 edges does not reach the margins.
  - B1 kept the GL code in `gl_picture.c` (its loader, GLES shader conversion and targets are that file's own).
* Phase C (instances and events, shared by both objectives):
  - `NativeModel_SetInstance` (exported for code mods, `NativeInstance` with a `size` for later fields): a draw's context
    (ARENA, FIELD, BIG_CARD, MEASURE), key, card, fade and contact frame, for the next slot draw only; MEASURE captures
    nothing. The game's own draws: key = slot, card from `NativeModel_SetBattleCards` (battle step 5; cleared when the
    arena ends).
  - The marker goes to the nearest ordering-table entry the slot's packets would have taken (`NativeModel_Nearest`,
    kept by the polygon and the outline drivers; the outline drivers now honour the suppression too), not entry 0.
  - `native_anim.c`: `NativeAnim_Act` (row -> idle / enter / attack / hit / destroyed / win / guard); the cross-fade's
    memory is kept per key (16, least recently drawn replaced) and starts afresh when a key's mesh changes.
  - The composite takes the instance's fade (`opacity`; `glUniform1f` added to the picture's functions).
  - 16 native draws a frame (ring 32); `evt native` and `evt row ... other_row other_clock` log lines.
  - Tests: `pc_native_capture` (new: the game stood in for), `pc_native_anim` (acts, per-monster memory, mesh change).
* Phase D (the modder's package and tools):
  - `src/pc/render/native_registry.c`: the mods' `native_models` by card (`cards` / `card`) or disc model (`model`), a bare
    HDM4 (`file`) or a package (`package`: `model.json` format 1 with PNG textures, clips per act, strike frames, scale about
    the soles, look), an entry `setting` as other rule lists; read when a slot first needs it; the later mod's for the same
    card, a refused one falls back to the earlier; texture cap (`MEMORIES_NATIVE_TEXTURE_MAX`) and memory budget
    (`MEMORIES_NATIVE_BUDGET_MB`); the test switch reads packages too. The look (camera, light, normal map) is per model
    now: package `look` < the mod's settings < the environment.
  - The capture chooses the model from the draw's card (`NativeModel_BeginSlot(model, slot)`, `NativeDraw.mesh_id`);
    the arena camera takes the drawn model's look; `NativeAnim_ActClip` plays the package's clip for an act.
  - The GL pass keeps each model's textures and buffers (`NativeGlMesh`, 16): two different native monsters no longer
    upload again every frame.
  - Tools (`tools/hd-models`): `native_convert.py` (no disc: root height fit, rig profiles ue/mixamo/generic, materials
    packed into one texture, unskinned props on their bone, cubic/step keys, clips per act guessed by name, strike frames
    from the hand's speed), `new_native_mod.py` (the mod folder, entries merged on a second run), `native_check.py` and
    `native_spec.py` (the game's checks in plain Python); `rigged_to_hdm4.py` kept for comparison.
  - Tests: `pc_native_registry`, `pc_native_tools` (a rigged glb made by the test, converted, checked, made into a mod and
    read back by the game's loader), `pc_native_capture` and `pc_native_anim` updated. `notes/native-models.md` is the
    modder's how-to (five steps, the package, acts, look, limits, troubleshooting).
* Phase F (3D Monsters field attack, first part) and E (director):
  - 3D Monsters names every draw of slot 0 to the native pass (`native_say`, bound with `host->symbol`): field or big
    card, its cache entry as the key (two monsters drawn through the one slot no longer share a pose), the model's card,
    its fade, and half its attack row as the blow's frame (unknown, -1, while the attacker's control module decides);
    the measuring draws (`sort_aside`) are MEASURE and capture nothing.
  - `NativeAnim_ActClip`: an act with no clip plays the hit's (guard, destroyed) or the idle's. The attack with a known
    contact frame and package strike frames is warped so the first strike lands on it; the arena keeps the measured
    BLS warp until its contact frames are measured (E2/E3).
  - Milestones re-sequenced: M5 is the field (F, E1, E4), M6 the arena's measured timing (E2, E3).
* H3 (first part): the FM Editor checks a mod's `native_models` as the port reads them (`tools/pc/fm_editor/native_models.py`:
  package or file inside the mod and present, cards, disc model, setting, duplicates, the 64-entry limit); test
  `pc_fm_editor_native_models`.

* Checks of the phases on the laptop (the user, 2026-10-22): M1 to M7 all PASS (M5 and M7 from videos made here with
  `tools/hd-models/field_attack.py --clip`; the mannequin stands in for Black Luster Soldier).
* Fixes found on the way: M4-1 (the converter wrote fractions the game's JSON reader refuses), M4-8 (a Windows path to a
  package), M5-1 (a monster's unlinked packets had no tag length: the 3D Monsters mod's `stamp_bank` wrote over the native
  marker, so the model and the disc model's glow dropped out of some frames), M5-5 (a stray native draw while a monster
  loads).
* Phase G, the camera: `shots` in `model.json` (yaw, pitch, distance, height, eased, while a monster or the other one plays
  an act) in the arena (`NativeModel_ArenaShot` on the copy of the arena view) and on the field fight
  (`NativeModel_FieldShot`, the mod's orbit); `native_cinematic.c`, tested.
* `offset` in `model.json` (a nudge along the model's axes), kept optional: the placement problem it was made for was not an
  offset.
* Placement and size from first principles: measured on the disc Black Luster Soldier (373 game units tall, hips 159 above
  the soles); the converter now makes every model to that standard (`--height`, `--origin-height`, the idle pose's feet
  centred, `--no-center`); the size of a creature that is big or small by nature is declared with `--height`.
* Tools: `tools/hd-models/field_attack.py` (the field attack, the arena attack, a still of the field with `--idle`, an mp4 with
  `--clip`), `_paths.py` (no workspace layout assumed), a rigged angel from the Blender scripts (parked: its raised arm and
  sword).
* Rebased onto upstream/master: mod API 19 for `native_models` (upstream took 17, duelist busts, and 18, frame styles).
* Phase I started: `notes/adding-a-model.md`, the draft of the procedure to add a new model.
* H3: FM Editor "Native models" tab (`native_models_tab.py`, editing in `native_models.py`): add a package (copied into `models/<folder>/`), set its cards, remove; tests in `test_native_models.py` (the tab test needs Tk, skipped here).
* H1: the Library's model view shows the native model of the card (it did not: a slot with no battle card and no packet kept was dropped as "empty" before the pass could become ready; now a slot that draws a part is a model). Checked in the real window on card 364 (`pc_native_capture` extended).
* 2026-10-23 (J, docs only): dragon and angel looked wrong, so the plug-and-play promise was re-scoped: `notes/native-models-fit-problem.md` (hypotheses), `notes/native-models-feasibility.md` (verdict, stages S0-S9, categories C1-C8, studio design, engine viewport gaps, FM Editor/converter facts). Decided: real engine as the studio viewport; UX and GUI first, code after. `progress.md` rewritten as a short resume point with a docs map; duplicate sections merged in the native-models notes.

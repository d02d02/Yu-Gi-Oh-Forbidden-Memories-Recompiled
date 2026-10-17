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

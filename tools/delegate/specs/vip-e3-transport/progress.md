# Job vip-e3-transport: live act/clip/pause/speed/scrub for the native model preview (Route B, E3)

Read JOB.md first. One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Status
Not started.

## Items
- [ ] 1. Baseline: the game builds in this clone into tmp/pc/e3-build (junction tmp/pc/tools to the main checkout first, see JOB.md)
  check: bash verify.sh build
- [ ] 2. native_anim transport state: struct + setters/getters in native_anim.c/.h, gated (inactive = unchanged), unit test in the existing C test setup
  check: bash verify.sh c
- [ ] 3. NativeAnim_Choose honours the transport: forced clip name, pause, speed, phase override that feeds the same anim_frame path (strike_warp and the BLS warp included)
  check: bash verify.sh c
- [ ] 4. control.c commands `anim clip|pause|resume|speed|phase|frame|get`, errors on bad input, no effect when no client
  check: bash verify.sh c
- [ ] 5. yfm_control.py methods (anim_clip, anim_pause, anim_resume, anim_speed, anim_phase, anim_frame, anim_get) + python tests with a fake socket
  check: bash verify.sh py
- [ ] 6. Demo tools/hd-models/transport_demo.py: pause the dragon attack, scrub 5 phases, shot each, free-run capture at the same phases, print hashes (needs the disc)
  check: python tools/hd-models/transport_demo.py --selftest
- [ ] 7. Notes: engine-needs.md E3 row done, adding-a-model.md how-to, progress.md entry
  check: grep -q "E3.*done" notes/studio/engine-needs.md

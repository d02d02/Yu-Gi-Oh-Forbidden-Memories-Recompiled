# Job vip-e5-overlay: bbox/grid/bone line overlays and bounds read-back (E5, E6)

Read JOB.md first. One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Status
Not started.

## Items
- [ ] 1. Baseline: the game builds in this clone (junction tmp/pc/tools to the main checkout, see verify.sh)
  check: bash verify.sh build
- [ ] 2. native_overlay.c/.h pure part: flags, NativeOverlay_Command (incl. ov bounds reply), NativeOverlay_Record, NativeOverlay_BoxLines, NativeOverlay_GridLines, with tests/pc/native_overlay_test.c
  check: bash verify.sh c
- [ ] 3. native_overlay.c in the build lists; control.c forwards `ov ` lines
  check: bash verify.sh build
- [ ] 4. native_draw records the bounds and draws the bbox lines when the flag is set (flags off = nothing changes)
  check: bash verify.sh build
- [ ] 5. native_draw draws the grid and the bones when their flags are set
  check: bash verify.sh build
- [ ] 6. yfm_control.py ov_* methods + test_yfm_overlay.py with a fake socket
  check: bash verify.sh py
- [ ] 7. engine-needs.md E5 and E6 rows marked done with the command list; `bash verify.sh all` passes
  check: bash verify.sh all

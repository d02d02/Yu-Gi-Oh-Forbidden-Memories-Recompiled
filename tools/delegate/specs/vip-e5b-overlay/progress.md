# Job vip-e5b-overlay: wire the overlays into the game (E5, E6), retry

Read JOB.md first (including the retry note). One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Items
- [ ] 1. native_overlay.c added to the game build lists (CMakeLists.txt and tools/pc/build_game32.py, beside native_anim.c) and control.c forwards `ov ` lines to NativeOverlay_Command (forwarding only)
  check: grep -q NativeOverlay_Command src/pc/debug/control.c && grep -q native_overlay tools/pc/build_game32.py && bash verify.sh build
- [ ] 2. native_draw (gl_picture.c) calls NativeOverlay_Record with the mesh's model-space bounds and draws the bbox lines when the bbox flag is set (flags off = unchanged)
  check: grep -q NativeOverlay_Record src/pc/render/gl_picture.c && grep -q NativeOverlay_BoxLines src/pc/render/gl_picture.c && bash verify.sh build
- [ ] 3. native_draw draws the grid and the bones when their flags are set
  check: grep -q NativeOverlay_GridLines src/pc/render/gl_picture.c && bash verify.sh build
- [ ] 4. engine-needs.md E5 and E6 rows marked done with the command list; `bash verify.sh all` passes
  check: bash verify.sh all

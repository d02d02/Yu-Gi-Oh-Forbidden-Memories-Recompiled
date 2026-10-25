# Job vip-e4-camera: camera presets and override over the control channel (E4)

Read JOB.md first. One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Status
Not started.

## Items
- [ ] 1. Baseline: the game builds in this clone (junction tmp/pc/tools to the main checkout, see verify.sh)
  check: bash verify.sh build
- [ ] 2. Pure part in native_cinematic.c/.h: override state, NativeCinematic_Override, NativeCinematic_Command with presets and range errors; cases in native_cinematic_test.c (every preset, set in range, set out of range, off, get, garbage)
  check: bash verify.sh c
- [ ] 3. NativeModel_ArenaShot and NativeModel_FieldShot honour the override (inactive = unchanged); the game still builds
  check: bash verify.sh build
- [ ] 4. control.c forwards `cam ` lines to NativeCinematic_Command (forwarding only)
  check: bash verify.sh build
- [ ] 5. yfm_control.py cam_preset/cam_set/cam_off/cam_get + test_yfm_cam.py with a fake socket
  check: bash verify.sh py
- [ ] 6. engine-needs.md E4 row marked done with the command list; `bash verify.sh all` passes
  check: bash verify.sh all

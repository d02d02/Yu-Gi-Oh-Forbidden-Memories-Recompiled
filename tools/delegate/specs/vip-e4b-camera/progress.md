# Job vip-e4b-camera: camera presets and override over the control channel (E4), retry

Read JOB.md first (including the retry note). One item per session; the check is the line under the item. Run with RALPH_MODEL=vip on Windows.

## Items
- [ ] 1. Pure part in native_cinematic.c/.h: NativeCinematic_Override and NativeCinematic_Command (presets, set with range errors, off, get); cases in tests/pc/native_cinematic_test.c for every preset, set in range, out of range, off, get, garbage
  check: grep -q NativeCinematic_Command src/pc/render/native_cinematic.c && grep -q NativeCinematic_Command tests/pc/native_cinematic_test.c && bash verify.sh c
- [ ] 2. NativeModel_ArenaShot and NativeModel_FieldShot honour the override (inactive = unchanged)
  check: grep -q NativeCinematic_Override src/pc/render/native_model.c && bash verify.sh build
- [ ] 3. control.c forwards `cam ` lines to NativeCinematic_Command (forwarding only)
  check: grep -q NativeCinematic_Command src/pc/debug/control.c && bash verify.sh build
- [ ] 4. yfm_control.py cam_preset/cam_set/cam_off/cam_get + tools/pc/tests/test_yfm_cam.py with a fake socket (CREATE the file)
  check: grep -q "def cam_preset" tools/pc/yfm_control.py && test -f tools/pc/tests/test_yfm_cam.py && bash verify.sh py
- [ ] 5. engine-needs.md E4 row marked done with the command list; `bash verify.sh all` passes
  check: bash verify.sh all

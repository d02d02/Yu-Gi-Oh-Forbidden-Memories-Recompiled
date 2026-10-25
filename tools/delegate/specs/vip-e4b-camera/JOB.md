# Job vip-e4b-camera

## Goal
Live camera control for the native model preview (Studio need E4): named presets and a free yaw/pitch/distance/height override, driven over the control channel (`src/pc/debug/control.c`, client `tools/pc/yfm_control.py`). Gated: inactive means the game's camera and the package shots behave byte-for-byte as before. Phase 1 = make it work, small. Nothing else (no overlays, no readback).

## Facts (pasted; read other code only by `grep -n` then at most 40 lines)
- `src/pc/render/native_cinematic.h/.c` are pure (no game memory, no GL). `NativeCamera {float yaw, pitch, distance, height;}`: the eye turned `yaw` degrees about the look-at point, raised `pitch` degrees and `height` units, distance times `distance` (1 = as is). `NativeCinematic_Orbit(look, eye, &camera, out)` applies it. Existing test: `tests/pc/native_cinematic_test.c` (prints `native_cinematic_test: ok`).
- Two places pick a camera, both in `src/pc/render/native_model.c`: `int NativeModel_ArenaShot(int model0, int model1, const float look[3], float eye[3])` (picks `chosen`, returns 0 early when no model has shots, else calls `NativeCinematic_Orbit(look, eye, &chosen, eye)` and returns 1) and `int NativeModel_FieldShot(NativeFieldShot *shot)` (fills `shot->yaw/pitch/distance/height` from `chosen`, returns `best > 0`). `grep -n "NativeModel_ArenaShot\|NativeModel_FieldShot" -r src` shows the callers.
- Override rule: when the override is active, ArenaShot orbits by the override camera and returns 1 even if no model has shots; FieldShot fills the override into `*shot` and returns 1. Inactive: no change at all.
- Put everything testable in `native_cinematic.c`: `typedef struct { int active; NativeCamera cam; } NativeCamOverride;` process-global with `NativeCinematic_Override(NativeCamera *out)` (returns 1 when active), and `int NativeCinematic_Command(const char *line, char *reply, size_t n)` parsing: `cam preset NAME` (names: front yaw0 pitch0 dist1 h0; side yaw90 pitch0 dist1 h0; top yaw0 pitch75 dist1 h0; three-quarter yaw35 pitch15 dist1 h0; close yaw0 pitch5 dist0.6 h0), `cam set YAW PITCH DIST HEIGHT` (yaw -180..180, pitch -89..89, dist 0.2..5, height -2000..2000, errors otherwise), `cam off`, `cam get` (reply `ok cam off` or `ok cam yaw=.. pitch=.. dist=.. height=..`). Return 0 and an `ok ...` reply, or nonzero and an `err ...` reply (same convention as `NativeAnim_Command` in native_anim.c; look at it for the exact reply/err handling and how control.c forwards `anim ...` lines, `grep -n "NativeAnim_Command" src/pc/debug/control.c`). control.c only forwards lines starting with `cam ` and sends the reply.
- Build: `bash verify.sh build` (about 35 s, output tmp/pc/vip-e4-camera-build/memories-pc.exe). C test: `bash verify.sh c`. Python test: `bash verify.sh py`. `verify.sh` is protected; do not edit it. Run with RALPH_MODEL=vip.
- Client: `tools/pc/yfm_control.py`, class `Game`, `command(line) -> reply`. Model the new methods on the existing `anim_*` ones (`grep -n "def anim_" tools/pc/yfm_control.py`) and the fake-socket test `tools/pc/tests/test_yfm_anim.py`: add `cam_preset(name)`, `cam_set(yaw, pitch, dist, height)`, `cam_off()`, `cam_get()` (returns a dict, or None when off) and `tools/pc/tests/test_yfm_cam.py`.
- Python is `python` (not python3). LF endings. Do not push.

## Limits
Edit only: `src/pc/render/native_cinematic.c`, `native_cinematic.h`, `src/pc/render/native_model.c` (the two shot functions only), `src/pc/debug/control.c` (forwarding only), `tests/pc/native_cinematic_test.c` (add cases above the end, keep existing), `tools/pc/yfm_control.py`, `tools/pc/tests/test_yfm_cam.py`, `notes/studio/engine-needs.md` (E4 row). Anything else: write BLOCKED with the reason.

## Acceptance
`bash verify.sh all` passes. Final message: files changed, every existing function touched (name + why), open problems.

## Retry note (e4 failed vacuously)
A first run ticked all items but wrote no C code: `NativeCinematic_Command`, `NativeCinematic_Override`, the `cam ` forwarding in control.c and the override in the two shot functions did not exist. The checks below grep for them. Write the code; do not tick an item whose grep check you have not made pass.

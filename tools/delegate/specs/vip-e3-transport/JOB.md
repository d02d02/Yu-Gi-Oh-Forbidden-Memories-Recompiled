# Job vip-e3-transport

## Goal
Live control of the native model preview in the recompiled game (Studio Route B, need E3): set act or clip by name, pause/resume, speed, scrub to a phase (0..1 of the act row) or a clip frame, report the state. Driven over the existing control channel (`src/pc/debug/control.c`, client `tools/pc/yfm_control.py`). Phase 1 = make it work, small, gated. No hardening, no E4-E9.

## Facts (pasted; read other code only by `grep -n` then at most 40 lines)
- Hook point: `float NativeAnim_Choose(const NativeDraw *d, const NativeMesh *mesh, const char *forced, const NativeClip **clip_out)` in `src/pc/render/native_anim.c` (~line 109). It returns the clip time `t`. `forced` = MEMORIES_NATIVE_CLIP (free clock `d->id/30`). Otherwise phase = `d->info.anim_frame / (16 * d->info.anim_length)` clamped 0..1; attack rows go through `strike_warp(...)` and a Black-Luster-only piecewise warp keyed on `anim_frame/16`; else `phase*(frames-1)/fps`. The caller is `gl_picture.c` ~2383: `t = NativeAnim_Choose(d, mesh, nat_env.clip, &clip);`.
- Scrub rule: a scrubbed phase must feed the SAME inputs the game uses. Implement the phase override by computing a substitute `anim_frame` (phase*16*anim_length) and running the normal path, so a scrubbed frame equals the same frame in real play. Do not return `phase*(frames-1)/fps` directly for attack rows.
- Transport state is process-global, default inactive: inactive means NativeAnim_Choose behaves byte-for-byte as before. Pause = freeze the current inputs (hold last t / last anim_frame). Speed scales the free clock only (a free-running clip); for row-driven play pause + phase are the controls.
- Put the command parsing in a pure function in native_anim.c, e.g. `int NativeAnim_Command(const char *line, char *reply, size_t n)` ("anim clip NAME|auto", "anim pause", "anim resume", "anim speed X" (0.05..8), "anim phase P" (0..1), "anim frame N", "anim get"), so it is unit-testable without the engine. control.c only forwards lines starting with "anim " to it and sends the reply (`ok ...` / `err ...`, see `send_error` in control.c). Keep control.c edits minimal and list each in your report.
- C unit test: `tests/pc/native_anim_test.c` (exists; compiled with `src/pc/render/native_anim.c`, `-Wall -Wextra -Wpedantic -Werror`). Add cases there. Run: `bash verify.sh c`. Build the whole game: `bash verify.sh build` (35 s, output `tmp/pc/e3-build/memories-pc.exe`). `verify.sh` is protected; do not edit it.
- Client: `tools/pc/yfm_control.py`, class `Game`, `command(line) -> reply`, `shot(path)`, `hash()`. Add `anim_clip/anim_pause/anim_resume/anim_speed/anim_phase/anim_frame/anim_get`. Test with a fake socket in `tools/pc/tests/test_yfm_anim.py` (stdlib unittest, run `python tools/pc/tests/test_yfm_anim.py`).
- Demo (item 6): `tools/hd-models/transport_demo.py` modelled on `tools/hd-models/field_attack.py` (read its header and `grep -n "def "`). Needs the disc (`MEMORIES_DISC` is set by the caller) and the installed mod `studio-preview`; `--selftest` must run WITHOUT the disc (checks argument handling and the hash-compare helper on synthetic data). Without the selftest flag it pauses the dragon attack, scrubs phases 0, .25, .5, .75, 1, shots each, free-runs to the same phase, prints hashes.
- Python is `python` (not python3) on this machine. Use LF endings. Do not push.

## Limits
Edit only: `src/pc/render/native_anim.c`, `native_anim.h`, `src/pc/debug/control.c` (forwarding only), `tests/pc/native_anim_test.c`, `tools/pc/yfm_control.py`, `tools/pc/tests/test_yfm_anim.py`, `tools/hd-models/transport_demo.py`, `notes/studio/engine-needs.md`, `notes/adding-a-model.md`. Anything else: write BLOCKED with the reason.

## Acceptance
All checks green; `bash verify.sh all` passes. Final message: files changed, every existing function touched (name + why), how to run the demo, open problems.

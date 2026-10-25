# Job vip-e3-harden

## Goal
Harden the landed E3 transport (commit 5e404489a: `NativeAnim_Transport*` and `NativeAnim_Command` in `src/pc/render/native_anim.c`, forwarding in `src/pc/debug/control.c` ~line 309, test `tests/pc/native_anim_test.c`). Test and fix only; no new features. Findings that need a design decision go in the report, not into code.

## Facts
- Command grammar: "anim clip NAME|auto", "anim pause", "anim resume", "anim speed X" (0.05..8), "anim phase P" (0..1), "anim frame N", "anim get". Reply `ok ...` or `err ...`. `int NativeAnim_Command(const char *line, char *reply, size_t n)`.
- Transport is process-global, default inactive; inactive must behave byte-for-byte as before E3.
- Scrub rule: a scrubbed phase P must give the same clip time as the normal path with `anim_frame = P*16*anim_length` (strike_warp and the Black-Luster warp included).
- Pre-E3 source of native_anim.c for differential tests: `git show 5e404489a^:src/pc/render/native_anim.c`. The clone is shallow: if that object is missing, `git fetch --depth 50 origin` is not allowed; use `git log` in the MAIN checkout instead (`/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled`, read-only) to write the old file to `tests/pc/native_anim_old.c` once. If impossible, drop item 3 and say so.
- Test build: `bash verify.sh c`; UBSan build: `bash verify.sh san`; everything: `bash verify.sh all` (the build step takes 35 s). `verify.sh` is protected. Read a file with `grep -n` then at most 40 lines; do not re-read whole files. Python is `python`. LF endings only, no bulk reformat. Do not push.

## Hard rules
- An item is done only when its new tests exist AND pass. Do not weaken existing tests.
- A bug a test finds: fix it in native_anim.c (smallest change) and keep the test.

## Limits
Edit only: `src/pc/render/native_anim.c`, `native_anim.h`, `src/pc/debug/control.c`, `tests/pc/native_anim_test.c`, `tests/pc/native_anim_old.c` (new), `notes/studio/e3-review.md` (new). Anything else: write BLOCKED with the reason.

## Acceptance
`bash verify.sh all` passes. Final message: bugs found and fixed (or none), files changed, open questions for the supervisor.

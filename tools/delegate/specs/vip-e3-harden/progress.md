# Job vip-e3-harden: tests, sanitizer, review of the E3 transport

Read JOB.md first. One item per session; the check is the line under the item.

## Status
Not started.

## Items
- [ ] 1. Parser torture tests: empty, "anim", "anim ", 4000-char line, speed nan/inf/-1/0/9/1e99/"0x10"/"1,5", phase 1.0000001/-0.0001/"abc", frame -5/99999999999/"1.5", tabs and trailing garbage; reply buffer n = 0, 1, 2, 8, 64 with a canary byte after the buffer (never written, always NUL-terminated when n>0); an `err` reply leaves the transport state unchanged (compare "anim get" before and after)
  check: bash verify.sh c && grep -q "canary" tests/pc/native_anim_test.c
- [ ] 2. Scrub parity: on a synthetic mesh/clip set (reuse the test file's setup), for attack and non-attack rows and several anim_length values, `NativeAnim_Choose` with transport phase P equals `NativeAnim_Choose` inactive with anim_frame = P*16*anim_length, at P = 0, .1, .25, .5, .75, .9, 1
  check: bash verify.sh c && grep -q "parity" tests/pc/native_anim_test.c
- [ ] 3. Inactive is unchanged: differential test of `NativeAnim_Choose` against the pre-E3 source (see Facts) over a grid of rows, attack rows, anim_frame, anim_length and contact values, forced clip NULL; also after `anim` commands followed by `NativeAnim_TransportInit()` (reset)
  check: bash verify.sh c && grep -q "differential" tests/pc/native_anim_test.c
- [ ] 4. UBSan: the whole test runs clean under `bash verify.sh san`
  check: bash verify.sh san
- [ ] 5. Review note `notes/studio/e3-review.md`: which thread runs `NativeAnim_Command` (control.c) and which runs `NativeAnim_Choose` (render), whether the transport globals race (name each shared variable), and what pause/speed do when the clip changes under them; a risk list, no code change unless a test proves a bug
  check: test -s notes/studio/e3-review.md && grep -q "thread" notes/studio/e3-review.md
- [ ] 6. Full gate: `bash verify.sh all` passes (game builds, C tests, UBSan, Python tests, gl_picture.c and yfm_control.py unchanged)
  check: bash verify.sh all

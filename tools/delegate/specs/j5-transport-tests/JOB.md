# Job j5-transport-tests

## Goal
Test-only hardening of `tools/hd-models/studio/transport.py` (Route B transport, headless) and the S2.map resolution. Tests that expose a real bug may fix `transport.py`.

## Facts and excerpts
`Transport(game, state, max_steps=600)`: `start()` loads state, `anim_resume`, steps 1 until `anim_get()["al"]>0`, then `anim_pause`, `step(1)`, sets `paused=ready=True`, returns True; returns False after max_steps. `scrub(phase)` raises RuntimeError before start, pauses if playing, clamps to 0..1, `anim_phase`, `step(1)`, returns `current()`. `current()` returns float of `anim_get()["at"]` or None on TypeError/ValueError. `play()` raises before start. `shot(path)` creates parent dirs, calls `game.shot`, returns Path.
Existing tests: `tests/test_studio_transport.py` (FakeGame; do not edit). Resolutions: `studio/resolutions.py` has a map of check id to offered resolutions; `"S2.map": ["provide.file"]`, `"S1.skin"`, `"S2.skin"` likewise. Test style: unittest, `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`, `from studio import ...`.

## Given
`tests/test_studio_transport.py` read-only.

## Read first
- tools/hd-models/studio/transport.py (whole, ~70 lines)
- tools/hd-models/studio/resolutions.py (grep "S2.map")

## You may change
tools/hd-models/tests/test_j5_transport_1.py, test_j5_transport_2.py, tools/hd-models/studio/transport.py (bug fixes only)

## You must not touch
Everything else.

## Constraints
- One new test file per item. Python 3.12, no game, no disc, no Tk.
- Test tails: end each file with `if __name__ == "__main__": unittest.main()`.

## Acceptance
`bash verify.sh` exits 0.

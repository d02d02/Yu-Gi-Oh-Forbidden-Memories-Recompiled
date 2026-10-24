# Job sm6-timemap

## Goal
One UI-free module `tools/hd-models/studio/timemap.py` and tests: the S6 (timing) maths and checks of the Model Studio, headless. Pure Python 3.12, stdlib `unittest`, no tkinter, no numpy needed. Tests: `tools/hd-models/tests/test_studio_timemap.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_timemap.py -k TestStretch` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, timemap`.
- Findings: `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`.
- A time map is a list of points `[[clip_frame, row_phase], ...]`: `clip_frame` = frame of the native clip (0..M), `row_phase` = position on the disc row (0..N disc frames). Default (two points): `[[0, 0], [M, N]]` = uniform stretch. Valid when both columns are strictly increasing.
- Segment stretch = (row_phase delta) / (clip_frame delta) between neighbouring points (disc frames per clip frame; >1 slows the clip down). Allowed range default `(0.6, 1.8)`, hard limits 0.3 and 3.0.
- Disc ground truth: `tools/hd-models/studio/reference/arena_rows.json`: `{"cards": {"<card id>": {"model": int, "rows": {...}, "contact": {"attack_row": 3, "contact_frame": 166, "row_length": 270, "suspect": false}}}}`. `contact` may be missing or null for a card. Contact frame is in disc frames on the attack row.
- Recipe keys (act `a`): `acts.a.timemap`, `acts.a.strike` (list of up to 4 clip frames, ints), `acts.a.strike_joints` (list of up to 4 bone names), `acts.a.hold` (int, default 0), `timing.stretch_range` (`[lo, hi]`).

## Items (see progress.md)
1. `default_map(clip_frames, row_length)` returns `[[0, 0], [clip_frames, row_length]]`; `segments(points)` returns a list of `{"clip": (c0, c1), "row": (r0, r1), "stretch": float}`; raises `ValueError` on fewer than 2 points.
2. `check_monotonic(points)` finding `S6.monotonic` fail when either column is not strictly increasing (message "Time-map points are not in order.", fix "Move a point."), else none.
3. `check_stretch(points, rng=(0.6, 1.8))` finding `S6.stretch`: warn when any segment stretch is outside `rng`, fail when outside 0.3..3.0 (message names the worst segment and its factor, one decimal; fix "Trim the clip or add a time-map point."), else none. Value = worst factor.
4. `row_to_clip(points, row_phase)` and `clip_to_row(points, clip_frame)`: piecewise-linear, clamped to the ends; exact inverse of each other inside the range.
5. `contact_for(arena_rows, card_id, act="attack")` returns `{"contact_frame": int, "row_length": int}` or `None` (missing card, null contact, `suspect` true, or act other than attack).
6. `check_strike(points, strike_frame, contact)` : `strike_row = clip_to_row(points, strike_frame)`; `contact` None gives finding `S6.no-reference` info (message "No disc reference for this act.", fix "Strike timing is unchecked here; measure this act on the disc to enable the check."); gap = abs(strike_row - contact_frame); warn id `S6.strike-vs-contact` when gap > 3, fail when gap > 10 (message "Strike lands N frames from the disc contact.", fix "Drag the red marker onto the green line, or add a time-map point."), none otherwise.
7. `suggest_point(points, strike_frame, contact)` returns a new points list with one point inserted (or moved) so that clip `strike_frame` maps to `contact_frame`, keeping order valid; returns the input unchanged when `contact` is None or the result would break monotonic order. Then `run_s6(recipe, act, clip_frames, card_id, arena_rows)` returning `{"points": ..., "findings": [...]}` (default map if the recipe has none; runs items 2, 3, 6); test with a tiny inline arena_rows dict and one test against the real file for card "1" (contact_frame 166, row_length 270). One README row in `tools/hd-models/README.md` mentioning `studio/timemap.py`.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/timemap.py`, `tests/test_studio_timemap.py`, and one row in `tools/hd-models/README.md`. Never change `audit.py`, `state.py`, `recipe.py`.

## Acceptance
`bash verify.sh` exits 0.

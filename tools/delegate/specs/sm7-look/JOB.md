# Job sm7-look

## Goal
One UI-free module `tools/hd-models/studio/look.py` and tests: the S7 (look and camera moves) data rules and checks of the Model Studio, headless. Pure Python 3.12, stdlib `unittest`, no tkinter, no numpy. Tests: `tools/hd-models/tests/test_studio_look.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_look.py -k TestDefaults` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, look`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- Findings: `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`.
- Look keys and defaults (percent unless noted): `ambient` 20, `light_gain` 100, `normal_strength` 180, `highlight` 100, `flip_green` true (bool), `camera_near` 1000 (game units), `camera_keep` 50, `camera_scale` 100. All ints except `flip_green`.
- A camera move (shot) is a dict `{"act": str, "from": int, "to": int, "yaw": int, "pitch": int, "distance": int, "height": int, "ease": str, "other": bool}`. `distance` is percent (100 = unchanged). Eases allowed: `"linear"`, `"in"`, `"out"`, `"inout"`. At most 8 moves. `from`/`to` are frames of that act's disc row.
- Row lengths come as a dict `{act_name: row_length_int}`.

## Items (see progress.md)
1. `default_look()` returns the eight defaults above (a new dict each call); `normalize_look(d)` returns a full dict: missing keys filled from defaults, unknown keys dropped, values coerced to int (`flip_green` to bool); raises `ValueError` on a non-numeric value.
2. `check_move_count(shots)` finding `S7.move-count` fail when more than 8 (message "Too many camera moves: N of 8.", fix "Delete or merge a move."), else none.
3. `check_move_range(shots, row_lengths)` finding `S7.move-range` fail per bad move: `from >= to`, a negative `from`, `to` past the act's row length, or an act missing from `row_lengths` (message "Move N: <reason>.", N is 1-based; fix "Set from below to, inside the row."), else none.
4. `check_move_values(shots)` finding `S7.move-values` fail when `ease` not allowed, or distance outside 20..400, or yaw outside -180..180, or pitch outside -89..89 (message "Move N: <field> out of range.", fix "Use a value inside the allowed range."); none otherwise.
5. `check_move_extreme(shots)` finding `S7.move-extreme` warn per move where `abs(yaw) > 90` or `abs(pitch) > 60` or `distance < 50` (message "Move N ends far from the arena view.", fix "Lower yaw or raise distance."), else none.
6. `check_brightness(model_lum, bls_lum)` finding `S7.brightness` warn when `abs(model_lum - bls_lum) / bls_lum > 0.15` (message "Model brightness differs from the disc by N%.", N whole number; fix "Adjust light gain or ambient."), value = the ratio; none when within range or `bls_lum` <= 0.
7. `run_s7(recipe, row_lengths, model_lum=None, bls_lum=None)` returns `{"look": normalize_look(recipe.get("look", {})), "shots": recipe.get("shots", []), "findings": [...]}` running items 2-6 (brightness only when both luminances are given). Tests: one clean recipe gives no findings, one bad recipe gives the expected ids. One README row for `studio/look.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/look.py` and `tests/test_studio_look.py`. Never change `audit.py`, `state.py`, `recipe.py`, `timemap.py`, README.

## Acceptance
`bash verify.sh` exits 0.

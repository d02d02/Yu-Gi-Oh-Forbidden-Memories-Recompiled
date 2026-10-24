# Job sm5-clips

## Goal
One UI-free module `tools/hd-models/studio/clips.py` and tests: the S5 (animation) clip statistics and checks of the Model Studio, headless. Pure Python 3.12, stdlib `unittest`, no tkinter, no numpy, no glTF. Tests: `tools/hd-models/tests/test_studio_clips.py`, one class per item.

## Facts (pasted: do NOT read other studio modules in full; `grep -n "def "` then read at most 30 lines)
- Run: `python3 tools/hd-models/tests/test_studio_clips.py -k TestLoopGap` from the repo root. Test header: `HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))`, then `from studio import audit, clips`. The file MUST end with `if __name__ == "__main__":\n    unittest.main()`.
- Findings: `audit.finding(check, level, message, fix="", value=None)`; levels `"fail" "warn" "info"`. EVERY check here returns a LIST of findings (empty when fine).
- A clip is `{"positions": P, "fps": float, "loop": bool}`. `P[f][j]` is the world position `(x, y, z)` of joint j at frame f (a list of frames, each a list of joints, each a 3-tuple of floats, game units). Joint 0 is the root. `parents[j]` is the parent joint index, -1 for the root.
- Thresholds: loop gap warn above 20 units; root drift warn above 100 units; speed peak warn above 4000 units per second; bone stretch warn when a bone's length leaves 0.8..1.25 of its length in frame 0.

## Items (see progress.md)
1. `loop_gap(P)` returns the largest distance any joint moves between the last and the first frame (float); 0.0 for fewer than 2 frames.
2. `root_drift(P)` returns `{"distance": float, "axis": (dx, dy, dz)}` for joint 0 from first to last frame; zeros for fewer than 2 frames.
3. `speed_peak(P, fps)` returns `{"speed": float, "joint": int, "frame": int}`: the fastest joint step (distance between frame f-1 and f times fps), frame is f; `{"speed": 0.0, "joint": 0, "frame": 0}` for fewer than 2 frames.
4. `bone_stretch(P, parents)` returns `{"ratio_min": float, "ratio_max": float, "joint": int}` comparing each non-root bone's length (joint to parent) in every frame with frame 0; `joint` is the bone with the largest deviation from 1.0; bones of zero length in frame 0 are skipped; 1.0/1.0/0 when there are none.
5. `clip_bbox(P)` returns `{"lo": (x, y, z), "hi": (x, y, z)}` over all frames and joints; zeros for an empty clip.
6. Checks `check_loop(name, clip)` (only when `clip["loop"]`, id `S5.loop-gap`, message "Clip <name>: the last frame is N units from the first.", fix "Close the loop or turn Loop off."), `check_drift(name, clip)` (id `S5.root-drift`, "Clip <name>: the root drifts N units.", fix "Remove the root motion or accept it."), `check_speed(name, clip)` (id `S5.speed`, "Clip <name>: a joint moves N units per second.", fix "Retime the clip or cut the pop."), `check_stretch(name, clip, parents)` (id `S5.bone-stretch`, "Clip <name>: bone J changes length to N times its rest length.", fix "Check the retarget."); N whole numbers, level warn, value = the measured number.
7. `run_s5(clips, parents)` returns `{"stats": {name: {"loop_gap", "root_drift", "speed_peak", "bone_stretch", "bbox"}}, "findings": [...]}` running items 1-6 for every clip in sorted name order. Tests: one clean clip set gives no findings; one bad set gives the expected ids. One README row for `studio/clips.py` is added by the supervisor: do NOT touch README.

## Constraints
One item per session; WRITE small: a new file at most 60 lines per write, grow it by edits of at most 60 lines. Do not edit anything except `studio/clips.py` and `tests/test_studio_clips.py`. Never edit any other file, in particular not `tests/test_studio_audit.py`, `audit.py`, `state.py`, `recipe.py`, `timemap.py`, `look.py`, `runs.py`, `package.py`, README.

## Acceptance
`bash verify.sh` exits 0.

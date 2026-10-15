"""Camera distance (eye to look-at) per arena frame, from a game.log that has one `cam phase=... eye=... ref=...` line per frame.

That log line was a temporary LOG(LOG_MODEL, ...) in Model_UpdateScene (src/game/model_scene_states.c, MEMORIES_PC); add it again to
re-measure the scripted camera, run the game with MEMORIES_TRACE=model, then:

    python -I camera_distance_from_log.py RUN_DIR      (RUN_DIR contains a watch/game.log)

Measured on the BLS-vs-191 arena battle (2026-10-16): the opening orbit is 1800 away, every close shot of the attack 460-660, which is
why `native_models` settings push the shots closer than 1000 outward (notes/native-models.md).
"""
import glob
import math
import re
import sys

base = sys.argv[1]
rows = []
for path in glob.glob(base + "/**/game.log", recursive=True):
    if "watch" not in path:
        continue
    for line in open(path, errors="ignore"):
        m = re.search(r"frame (\d+) vb (\d+) model\] cam phase=(-?\d+) eye=(-?\d+),(-?\d+),(-?\d+) ref=(-?\d+),(-?\d+),(-?\d+)", line)
        if m:
            frame, vb, phase, ex, ey, ez, rx, ry, rz = map(int, m.groups())
            rows.append((frame, phase, math.dist((ex, ey, ez), (rx, ry, rz)), (ex, ey, ez), (rx, ry, rz)))
if not rows:
    sys.exit("no cam lines found")
print(len(rows), "lines; frames", rows[0][0], "-", rows[-1][0])
for frame, phase, d, eye, ref in rows[::6]:
    print(frame, phase, round(d), eye, ref)
ds = sorted(r[2] for r in rows)
print("distance min/10%/median/90%/max", [round(ds[int(q * (len(ds) - 1))]) for q in (0, 0.1, 0.5, 0.9, 1)])

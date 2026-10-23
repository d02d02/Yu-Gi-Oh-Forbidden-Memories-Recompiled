#!/usr/bin/env python3
"""SM0: the arena's scripted camera per phase, from game.log files that carry `cam f= phase= eye= ref=` lines (Model_UpdateScene).

    python -I studio/build_camera.py OUT.json CARD=game.log [CARD=game.log ...]

Per card and phase: first/last presented frame, count, eye-to-look-at distance min/max, and the eye/ref at the first and last frame (game units)."""
import json, math, re, sys
from pathlib import Path

CAM = re.compile(r"cam f=(\d+) phase=(-?\d+) eye=(-?\d+),(-?\d+),(-?\d+) ref=(-?\d+),(-?\d+),(-?\d+)")


def phases(log: str) -> dict:
    out = {}
    for m in CAM.finditer(log):
        f, ph, *v = map(int, m.groups())
        eye, ref = v[:3], v[3:]
        d = round(math.dist(eye, ref))
        p = out.setdefault(str(ph), {"first": f, "last": f, "count": 0, "dist_min": d, "dist_max": d, "eye_first": eye, "ref_first": ref})
        p["last"], p["count"] = f, p["count"] + 1
        p["dist_min"], p["dist_max"] = min(p["dist_min"], d), max(p["dist_max"], d)
        p["eye_last"], p["ref_last"] = eye, ref
    return out


if __name__ == "__main__":
    data = {c: phases(Path(p).read_text(errors="replace")) for c, p in (a.split("=", 1) for a in sys.argv[2:])}
    Path(sys.argv[1]).parent.mkdir(parents=True, exist_ok=True)
    Path(sys.argv[1]).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    for c, d in data.items():
        print(c, {k: (v["count"], v["dist_min"], v["dist_max"]) for k, v in d.items()})

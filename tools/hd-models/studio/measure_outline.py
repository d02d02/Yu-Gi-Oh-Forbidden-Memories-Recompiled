#!/usr/bin/env python3
"""SM0: the disc model's outline (bounding box and front/side convex hulls, game units) from `hmd_export.py CARD OUT`'s model.gltf.

    python -I studio/measure_outline.py EXPORT_DIR CARD OUT.json

Pose = the one the model data stores (the disc's rest pose), y up, 100 game units per glTF unit, feet at y = 0."""
import json, sys
from pathlib import Path

import numpy as np


def hull(points):
    pts = sorted({(round(float(x)), round(float(y))) for x, y in points})
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0]-h[-2][0])*(p[1]-h[-2][1]) - (h[-1][1]-h[-2][1])*(p[0]-h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h[:-1]
    return half(pts) + half(pts[::-1])


def main(export: Path, card: str, out: Path):
    g = json.loads((export / "model.gltf").read_text())
    acc = g["accessors"][g["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    view = g["bufferViews"][acc["bufferView"]]
    raw = (export / "model.bin").read_bytes()
    stride = view.get("byteStride", 12)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    pos = np.ndarray((acc["count"], 3), "<f4", raw, base, (stride, 4)) * 100.0
    pos = pos - np.array([0, pos[:, 1].min(), 0])
    lo, hi = pos.min(0), pos.max(0)
    data = {"card": int(card), "unit": "game units, y up, feet at 0, disc rest pose", "vertices": int(acc["count"]),
            "bbox_min": [round(float(v)) for v in lo], "bbox_max": [round(float(v)) for v in hi], "height": round(float(hi[1])),
            "front_hull_xy": hull(pos[:, [0, 1]]), "side_hull_zy": hull(pos[:, [2, 1]])}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1) + "\n")
    print({k: data[k] for k in ("vertices", "bbox_min", "bbox_max", "height")})


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))

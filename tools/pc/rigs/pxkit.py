#!/usr/bin/env python3
"""pxkit: pixel checks on game screenshots (runs are bit-identical, so counts are exact).

  python -I pxkit.py diff A.png B.png [--region x,y,w,h] [--thresh 8] [--out diff.png]
  python -I pxkit.py count IMG.png --color r,g,b [--tol 0] [--region x,y,w,h]
  python -I pxkit.py golden check|record IMG.png GOLDEN_DIR [--max-pct 0]

Regions are in the image's own pixels. Library use: from pxkit import diff, count_color, golden.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def _crop(a, region):
    if not region:
        return a
    x, y, w, h = region
    return a[y:y + h, x:x + w]


def diff(a, b, region=None, thresh=8):
    """Pixels whose largest channel difference exceeds thresh: {count, pct, bbox:(x0,y0,x1,y1)|None, same_size}."""
    A, B = _crop(load(a), region), _crop(load(b), region)
    if A.shape != B.shape:
        return {"count": None, "pct": 100.0, "bbox": None, "same_size": False}
    m = np.abs(A - B).max(axis=2) > thresh
    ys, xs = np.nonzero(m)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else None
    return {"count": int(m.sum()), "pct": round(100.0 * m.sum() / m.size, 4), "bbox": box, "same_size": True}


def count_color(img, rgb, tol=0, region=None):
    """Pixels within tol (per channel) of rgb."""
    A = _crop(load(img), region)
    return int((np.abs(A - np.array(rgb, dtype=np.int16)).max(axis=2) <= tol).sum())


def diff_image(a, b, out, thresh=8):
    A, B = load(a), load(b)
    m = (np.abs(A - B).max(axis=2) > thresh)
    Image.fromarray((m * 255).astype(np.uint8)).save(out)


def golden(img, gold_dir, mode="check", max_pct=0.0):
    """record: store img as gold_dir/<name>; check: diff against it. Returns (ok, detail)."""
    g = Path(gold_dir) / Path(img).name
    if mode == "record":
        g.parent.mkdir(parents=True, exist_ok=True)
        Image.open(img).save(g)
        return True, "recorded"
    if not g.is_file():
        return False, "no golden"
    d = diff(img, g)
    return d["pct"] <= max_pct, d


def _region(s):
    return tuple(int(v) for v in s.split(",")) if s else None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diff"); d.add_argument("a"); d.add_argument("b"); d.add_argument("--region"); d.add_argument("--thresh", type=int, default=8); d.add_argument("--out")
    c = sub.add_parser("count"); c.add_argument("img"); c.add_argument("--color", required=True); c.add_argument("--tol", type=int, default=0); c.add_argument("--region")
    g = sub.add_parser("golden"); g.add_argument("mode", choices=["check", "record"]); g.add_argument("img"); g.add_argument("dir"); g.add_argument("--max-pct", type=float, default=0.0)
    a = ap.parse_args()
    if a.cmd == "diff":
        r = diff(a.a, a.b, _region(a.region), a.thresh)
        if a.out: diff_image(a.a, a.b, a.out, a.thresh)
        print(json.dumps(r)); return 0 if r["count"] == 0 else 1
    if a.cmd == "count":
        print(count_color(a.img, [int(v) for v in a.color.split(",")], a.tol, _region(a.region))); return 0
    ok, detail = golden(a.img, a.dir, a.mode, a.max_pct)
    print(json.dumps({"ok": ok, "detail": detail})); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

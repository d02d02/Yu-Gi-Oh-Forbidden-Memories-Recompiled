"""PGXP level 2: check a frame's logged GL triangles ("gltri:" lines, MEMORIES_PGXP_PROBE=160,120,1000) against
the magenta-clear capture of the same frame (MEMORIES_PGXP_CLEAR_MAGENTA). Written 2026-10-14.

  python -I gltri_check.py <log> <L2 magenta .ppm> [scale] [frame]

Without `frame` it picks the log frame whose triangles best match the capture (the log's frame counter
ran one ahead: capture "frame 40" = log frame 39). Prints per frame:
  - triangles, how many have all / some / no precise vertices (some = lost vertex identity);
  - "dropped": fully precise triangles that gl_picture.c triangle() skips because the ROUNDED area is 0
    (the gltri line is written before that return), and the pixels only they would paint;
  - unpainted pixels inside a drawn triangle, split by depth (on-edge = within 0.1 px: cracks / fill rule).
"""
import re, sys
import numpy as np

RX = re.compile(r"frame (\d+) .*gltri: flags (\d+) int area (-?\d+) \| "
                r"a (-?\d+),(-?\d+) ([P-]) (-?[\d.]+),(-?[\d.]+) uv \d+,\d+ \| "
                r"b (-?\d+),(-?\d+) ([P-]) (-?[\d.]+),(-?[\d.]+) uv \d+,\d+ \| "
                r"c (-?\d+),(-?\d+) ([P-]) (-?[\d.]+),(-?[\d.]+) uv \d+,\d+ \| offset (-?\d+),(-?\d+)")


def ppm(path):
    data = open(path, "rb").read()
    parts, at = [], 0
    while len(parts) < 4:
        while data[at:at + 1].isspace():
            at += 1
        end = at
        while not data[end:end + 1].isspace():
            end += 1
        parts.append(data[at:end])
        at = end
    w, h = int(parts[1]), int(parts[2])
    return np.frombuffer(data[at + 1:at + 1 + w * h * 3], np.uint8).reshape(h, w, 3)


def raster(mask, p, scale, margin=0.0):
    """Picture pixel X's centre is console X / scale (triangle() adds half a pixel to every vertex)."""
    H, W = mask.shape
    (ax, ay), (bx, by), (cx, cy) = p
    area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if abs(area) < 1e-12:
        return
    s = 1 if area > 0 else -1
    x0, x1 = max(0, int(np.floor(min(ax, bx, cx) * scale))), min(W - 1, int(np.ceil(max(ax, bx, cx) * scale)))
    y0, y1 = max(0, int(np.floor(min(ay, by, cy) * scale))), min(H - 1, int(np.ceil(max(ay, by, cy) * scale)))
    if x1 < x0 or y1 < y0:
        return
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) / scale, np.arange(y0, y1 + 1) / scale)
    e = [((bx - ax) * (Y - ay) - (by - ay) * (X - ax)) * s / max(np.hypot(bx - ax, by - ay), 1e-9),
         ((cx - bx) * (Y - by) - (cy - by) * (X - bx)) * s / max(np.hypot(cx - bx, cy - by), 1e-9),
         ((ax - cx) * (Y - cy) - (ay - cy) * (X - cx)) * s / max(np.hypot(ax - cx, ay - cy), 1e-9)]
    mask[y0:y1 + 1, x0:x1 + 1] |= (e[0] >= margin) & (e[1] >= margin) & (e[2] >= margin)


def frame_masks(lines, shape, scale):
    drawn, deep, dropped = (np.zeros(shape, bool) for _ in range(3))
    counts = {"triangles": 0, "all precise": 0, "some precise (MIXED)": 0, "none precise": 0, "dropped": 0}
    for g in lines:
        ox, oy = int(g[18]), int(g[19])
        marks = [g[5 + 5 * k] for k in range(3)]
        pts = []
        for k in range(3):
            ix, iy, mark, fx, fy = g[3 + 5 * k: 8 + 5 * k]
            x, y = (float(fx), float(fy)) if mark == "P" else (float(ix), float(iy))
            pts.append((x - ox, y - oy))
        counts["triangles"] += 1
        n = marks.count("P")
        counts["all precise" if n == 3 else "none precise" if n == 0 else "some precise (MIXED)"] += 1
        if int(g[2]) == 0:
            if n == 3:
                counts["dropped"] += 1
                raster(dropped, pts, scale)
        else:
            raster(drawn, pts, scale)
            raster(deep, pts, scale, 0.1 / scale)
    return counts, drawn, deep, dropped


def main():
    log, capture = sys.argv[1], sys.argv[2]
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    want = int(sys.argv[4]) if len(sys.argv) > 4 else None
    image = ppm(capture)
    magenta = (image[..., 0] == 255) & (image[..., 1] == 0) & (image[..., 2] == 255)
    frames = {}
    with open(log, errors="replace") as f:
        for line in f:
            m = RX.search(line)
            if m:
                frames.setdefault(int(m.group(1)), []).append(m.groups())
    candidates = [want] if want is not None else sorted(frames)
    best = None
    for frame in candidates:
        result = frame_masks(frames[frame], magenta.shape, scale)
        stray = int((result[1] & magenta).sum())
        print(f"log frame {frame}: drawn-triangle pixels that are magenta in the capture: {stray}")
        if best is None or stray < best[0]:
            best = (stray, frame, result)
    _, frame, (counts, drawn, deep, dropped) = best
    print(f"\nmatching log frame {frame}:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    only = dropped & ~drawn
    print(f"  pixels only the dropped triangles cover: {only.sum()}, unpainted in the capture: {(only & magenta).sum()}")
    print(f"  unpainted inside a drawn triangle: {(drawn & magenta).sum()}, deeper than 0.1 px inside: {(deep & magenta).sum()}")


if __name__ == "__main__":
    main()

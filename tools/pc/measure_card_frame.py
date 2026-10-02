#!/usr/bin/env python3
"""Flood-fill src/pc/assets/card_layout_frame.png's alpha cutouts (art,
attribute circle) and colour-match its cream stat-box fills, then print the
native-WIN-box (140x196) constants for card_layout.c -- so swapping the
frame template re-derives ART_X/Y/W/H, ICON_ROW_Y, ATTR_X, ATK_X, DEF_X,
VALUES_ROW_Y instead of hand-measuring each time (WIP_NOTES.md, 2026-10-02).
Requires Pillow. Usage: python3 tools/pc/measure_card_frame.py"""
from pathlib import Path
from PIL import Image

PATH = Path(__file__).resolve().parents[2] / "src/pc/assets/card_layout_frame.png"
WIN_W, WIN_H = 140, 196


def bbox_alpha(px, w, h, sx, sy):
    if px[sx, sy][3] != 0: return None
    seen, stack = set(), [(sx, sy)]
    x0 = x1 = sx; y0 = y1 = sy
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or px[x, y][3] != 0: continue
        seen.add((x, y))
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
    return x0, y0, x1, y1


def bbox_cream(px, w, h, y, x_range):
    def cream(c):
        r, g, b = c[0], c[1], c[2]
        return r > 200 and g > 190 and b > 130 and abs(r - g) < 40
    row = [x for x in x_range if cream(px[x, y])]
    if not row: return None
    x0, x1 = min(row), max(row)
    col = [yy for yy in range(h) if cream(px[(x0 + x1) // 2, yy])]
    return x0, min(col), x1, max(col)


def main():
    im = Image.open(PATH).convert("RGB" if False else "RGBA")
    px, (w, h) = im.load(), im.size
    sx, sy = w / WIN_W, h / WIN_H

    def native(bbox):
        x0, y0, x1, y1 = bbox
        return x0 / sx, y0 / sy, x1 / sx, y1 / sy

    art = bbox_alpha(px, w, h, w // 2, h // 3)
    attr = bbox_alpha(px, w, h, int(w * 0.87), int(h * 0.78))
    left = bbox_cream(px, w, h, int(h * 0.895), range(0, w // 2))
    right = bbox_cream(px, w, h, int(h * 0.895), range(w // 2, w))

    print(f"image {w}x{h}, scale {sx:.3f}/{sy:.3f}")
    if art:
        ax0, ay0, ax1, ay1 = native(art)
        print(f"ART_X={round(ax0)} ART_Y={round(ay0)} ART_W={round(ax1-ax0)} ART_H={round(ay1-ay0)}")
    if attr:
        bx0, by0, bx1, by1 = native(attr)
        cx, cy = (bx0+bx1)/2, (by0+by1)/2
        print(f"ICON_ROW_Y={round(cy-8)} ATTR_X={round(cx-8)}")
    if left:
        lx0, ly0, lx1, ly1 = native(left)
        print(f"ATK_X={round((lx0+lx1)/2)} VALUES_ROW_Y={round((ly0+ly1)/2)}")
    if right:
        rx0, ry0, rx1, ry1 = native(right)
        print(f"DEF_X={round((rx0+rx1)/2)}")


if __name__ == "__main__":
    main()

"""Count hairline gaps in level 2 frames: pixels that are dark (luma < 40) in a level 2 frame where the level 1
frame of the same scene is bright (luma > 70) and has no edge within 3 px. Level 2 frames are shifted back by
the known 0.75 console px (3 px at 4x) bias so they line up with level 1. Lower is better.

    gap_score.py level1.png label=level2.png [label=level2.png ...]    (4x frames; area = the 3D scene)
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

BIAS = 3
AREA = (220, 580, 100, 1180)  # y0, y1, x0, x1 of the 3D scene in a 4x frame


def luma(path, shift=0):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    if shift:
        a = np.roll(a, (-shift, -shift), (0, 1))
    return ((a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) // 1000).astype(np.uint8)


def main():
    y0, y1, x0, x1 = AREA
    reference = luma(sys.argv[1])
    solid = (np.asarray(Image.fromarray(reference).filter(ImageFilter.MinFilter(7))) > 70)[y0:y1, x0:x1]
    print("interior area checked: %d px" % solid.sum())
    for item in sys.argv[2:]:
        label, _, path = item.partition("=")
        dark = luma(path, BIAS)[y0:y1, x0:x1] < 40
        print("  %-28s %5d gap pixels" % (label, int((dark & solid).sum())))


if __name__ == "__main__":
    main()

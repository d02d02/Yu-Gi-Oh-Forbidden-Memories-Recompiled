#!/usr/bin/env python3
"""Make the ATK/DEF digit picture of Anime Style with real soft edges.

    python tools/pc/anime_art_digits.py <anime_digits.png, 200x192, the Forbidden Memories HD pack's> <out.png> [--size 256]

The picture holds the ten digits in two sets, normal (rows 0-1, dark ink) and dimmed (rows 2-3, grey ink, drawn for the stat the
attack screen greys out). Its edges are anti-aliased in a way that cannot be seen on the cream plaque but can on any other
background: every pixel is either clear or opaque, and the edge pixels are opaque with the plaque's cream already blended in. When
the plaque behind the digits changes (the attack and defense screens dim the card, other frame colors), that cream shows as a
light contour around the digits, most of all around the grey ones.

This turns each set into one flat ink colour with the coverage in the alpha channel: coverage = how far a pixel is from the cream
toward the ink. On the plaque the digits look as before; over any other background the edge is a true blend of ink and background.
The result is resized to a power-of-two size (v0.3.0 draws other sizes invisibly at Internal 2x/4x on some graphics cards); the
engine reads the picture in proportion, so the stretch is undone when it is drawn.
"""
import argparse
import sys

import numpy as np
from PIL import Image

LUMA = np.array([0.299, 0.587, 0.114])


def soften(image):
    pixels = np.asarray(image.convert("RGBA")).astype(float)
    height = pixels.shape[0]
    out = np.zeros_like(pixels)
    for rows in (slice(0, height // 2), slice(height // 2, height)):
        block = pixels[rows]
        opaque = block[..., 3] > 0
        colors = block[opaque][:, :3]
        values, counts = np.unique(colors, axis=0, return_counts=True)
        ink = values[counts.argmax()]                      # the flat colour almost every inner pixel has
        luma = colors @ LUMA
        background = luma.max()                            # the cream the edge pixels were blended with
        ink_luma = ink @ LUMA
        coverage = np.clip((background - block[..., :3] @ LUMA) / (background - ink_luma), 0.0, 1.0)
        result = np.zeros_like(block)
        result[..., :3] = ink
        result[..., 3] = np.where(opaque, coverage * 255.0, 0.0)
        out[rows] = result
    return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("digits")
    parser.add_argument("out")
    parser.add_argument("--size", type=int, default=256)
    args = parser.parse_args()
    soft = soften(Image.open(args.digits))
    if args.size:
        soft = soft.resize((args.size, args.size), Image.LANCZOS)
    soft.save(args.out, optimize=True)
    print("%s -> %s %s" % (args.digits, args.out, soft.size))


if __name__ == "__main__":
    sys.exit(main())

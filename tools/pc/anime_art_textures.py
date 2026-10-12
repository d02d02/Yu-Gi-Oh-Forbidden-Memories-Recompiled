#!/usr/bin/env python3
"""Build mods/anime-art/textures/ from the supplied original anime frame art.

    python tools/pc/anime_art_textures.py <folder with the originals> [--mod mods/anime-art]

The originals are the light, uncontrasted frames (919x1319 monster frames, 600x861 spell/trap frames) and
tools/pc/hd_recipes/anime_digits.png. Each is resized, with no other change, to a power-of-two size: v0.3.0's
bank_halve (src/pc/render/texture_pack.c) rounds mip levels up where OpenGL rounds down, so a texture that ever
meets an odd size above 1 on the way down (600 -> 300 -> 150 -> 75, 861, 919, 1319) is an incomplete OpenGL texture
and the frame is invisible at Internal 2x/4x on some drivers. The engine reads a frame in proportion to its size, so
the stretch to 1024 x 2048 / 1024 x 1024 / 256 x 256 is undone when it is drawn. Remove the resize once the engine
fix is in a release.
"""
import argparse
import os
import sys

from PIL import Image

MONSTER = (1024, 2048)
SPELL = (1024, 1024)
DIGITS = (256, 256)

# texture name -> (original file name, power-of-two size)
FRAMES = {
    "anime_frame_monster.png": ("monster-animeframe.png", MONSTER),
    "anime_frame_effect.png": ("monster-effect-animeframe.png", MONSTER),
    "anime_frame_fusion.png": ("monster-fusion-animeframe.png", MONSTER),
    "anime_frame_ritual_monster.png": ("monster-ritual-animeframe.png", MONSTER),
    "anime_frame_obelisk.png": ("monster-obelisk-animeframe.png", MONSTER),
    "anime_frame_ra.png": ("monster-ra-animeframe.png", MONSTER),
    "anime_frame_slifer.png": ("monster-slifer-animeframe.png", MONSTER),
    "anime_frame_magic.png": ("magic-animeframe.png", SPELL),
    "anime_frame_trap.png": ("trap-animeframe.png", SPELL),
    "anime_frame_ritual.png": ("ritual-animeframe.png", SPELL),
}


def is_power_of_two(n):
    return n > 0 and n & (n - 1) == 0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("originals", help="folder holding the *-animeframe.png originals")
    parser.add_argument("--mod", default=os.path.join(repo, "mods", "anime-art"))
    parser.add_argument("--digits", default=os.path.join(here, "hd_recipes", "anime_digits.png"))
    args = parser.parse_args()
    out = os.path.join(args.mod, "textures")
    os.makedirs(out, exist_ok=True)
    missing = []
    for name, (original, size) in FRAMES.items():
        path = os.path.join(args.originals, original)
        if not os.path.exists(path):
            missing.append(original)
            continue
        image = Image.open(path).convert("RGBA")
        image.resize(size, Image.LANCZOS).save(os.path.join(out, name), optimize=True)
        print("%-34s %s -> %s" % (name, image.size, size))
    if os.path.exists(args.digits):
        image = Image.open(args.digits).convert("RGBA")
        image.resize(DIGITS, Image.LANCZOS).save(os.path.join(out, "anime_digits.png"), optimize=True)
        print("%-34s %s -> %s" % ("anime_digits.png", image.size, DIGITS))
    else:
        missing.append(args.digits)
    for name in sorted(os.listdir(out)):
        width, height = Image.open(os.path.join(out, name)).size
        if not (is_power_of_two(width) and is_power_of_two(height)):
            sys.exit("%s is %dx%d, not power-of-two" % (name, width, height))
    if missing:
        sys.exit("missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()

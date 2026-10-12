#!/usr/bin/env python3
"""Build a texture pack of larger card pictures for the Anime Art mod (route B of the HD-art smoothing).

    python tools/pc/anime_art_card_art.py <HD pack folder, the one holding textures/> --out mods/anime-art/art [--scale 1.5]

The Forbidden Memories HD pack paints each card's picture at 408x384 (4x the console's 102x96). The anime layout shows
it over about 536x556 pixels at Internal 4x (1.31x / 1.45x), and the renderer picks the nearest texel of a pack image, so
every edge becomes a stair-step. This writes the same pictures, enlarged with Lanczos, so that a pixel spans a whole
texel or less: nothing is magnified any more. The pack's manifest.json entries for the card pictures are copied, only the
file size differs (a pack image may be any size, notes/modding.md "Texture packs"), and each entry is tied to the mod's own
`smooth_card_art` setting. The mod orders itself after Forbidden Memories HD, so its pack wins for the same pictures.

The pictures are the HD pack's, enlarged: credit Forbidden Memories HD (Unchiga, X@nder) where this pack is shared.
"""
import argparse
import json
import os
import sys

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("hd_pack", help="the Forbidden Memories HD folder (it holds textures/manifest.json)")
    parser.add_argument("--out", required=True, help="the folder to write (the mod's art folder)")
    parser.add_argument("--scale", type=float, default=1.5, help="enlargement of each picture (default 1.5: 612x576)")
    parser.add_argument("--colors", type=int, default=0, help="reduce to this many palette colors (0: keep full color)")
    parser.add_argument("--only", default="", help="comma-separated card ids, to test on a few")
    parser.add_argument("--setting", default="smooth_card_art")
    args = parser.parse_args()
    textures = os.path.join(args.hd_pack, "textures")
    manifest = json.load(open(os.path.join(textures, "manifest.json"), encoding="utf-8"))
    only = {int(x) for x in args.only.split(",") if x}
    os.makedirs(args.out, exist_ok=True)
    entries = []
    for entry in manifest:
        name = str(entry.get("file", ""))
        if not (name.startswith("card-") and name.endswith(".png")):
            continue
        if only and int(name[5:-4]) not in only:
            continue
        image = Image.open(os.path.join(textures, name)).convert("RGBA")
        size = (round(image.width * args.scale), round(image.height * args.scale))
        big = image.resize(size, Image.LANCZOS)
        if args.colors:
            big = big.convert("RGB").quantize(args.colors, Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        big.save(os.path.join(args.out, name), optimize=True)
        copy = dict(entry)
        copy["setting"] = args.setting
        entries.append(copy)
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(entries, handle, indent=1)
    total = sum(os.path.getsize(os.path.join(args.out, f)) for f in os.listdir(args.out))
    print("%d pictures, %dx%d each, %.1f MB" % (len(entries), size[0], size[1], total / 1048576))


if __name__ == "__main__":
    sys.exit(main())

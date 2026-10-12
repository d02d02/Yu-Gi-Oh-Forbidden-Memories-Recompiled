#!/usr/bin/env python3
"""Build the HD asset pack that the Anime Style mod carries (mods/anime-art/hd).

    python tools/pc/anime_art_hd_assets.py <Forbidden Memories HD folder, the one holding textures/> [--out mods/anime-art/hd]

The folder is the official Forbidden Memories HD pack (Unchiga, X@nder). Anime Style shows its pictures itself, so a player needs
only this mod: card pictures, thumbnails, card frames, stars and attribute balls, the Build Deck screen, the duel arena and
HUD, the portraits. Every picture is the HD pack's, byte for byte, except the card pictures, which are enlarged (Lanczos,
x1.5 = 612x576, 256 colors): the anime layout stretches a 408x384 card picture over about 536x556 pixels at Internal 4x, and the
renderer picks the nearest texel of a pack image, so an unenlarged picture shows stair-steps. The manifest is the HD pack's;
only each entry's `setting` is changed, to the mod's one `hd_assets` option: on (the default) shows these pictures, off shows
the game's own.

Credit Forbidden Memories HD (Unchiga, X@nder) wherever this pack is shared.
"""
import argparse
import json
import os
import shutil
import sys

from PIL import Image

SETTING = "hd_assets"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("hd_pack", help="the Forbidden Memories HD folder (it holds textures/manifest.json)")
    parser.add_argument("--out", default=os.path.join(repo, "mods", "anime-art", "hd"))
    parser.add_argument("--scale", type=float, default=1.5, help="enlargement of the card pictures (default 1.5)")
    args = parser.parse_args()
    textures = os.path.join(args.hd_pack, "textures")
    manifest = json.load(open(os.path.join(textures, "manifest.json"), encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    done = set()
    entries = []
    for entry in manifest:
        name = str(entry["file"])
        if name not in done:
            done.add(name)
            source = os.path.join(textures, name)
            if name.startswith("card-"):
                image = Image.open(source).convert("RGBA")
                size = (round(image.width * args.scale), round(image.height * args.scale))
                big = image.resize(size, Image.LANCZOS).convert("RGB").quantize(256, Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
                big.save(os.path.join(args.out, name), optimize=True)
            else:
                shutil.copyfile(source, os.path.join(args.out, name))
        copy = dict(entry)
        copy["setting"] = SETTING
        entries.append(copy)
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(entries, handle, indent=1)
    total = sum(os.path.getsize(os.path.join(args.out, f)) for f in os.listdir(args.out))
    cards = sum(1 for f in done if f.startswith("card-"))
    print("%d manifest entries, %d pictures (%d card pictures enlarged), %.0f MB" % (len(entries), len(done), cards, total / 1048576))


if __name__ == "__main__":
    sys.exit(main())

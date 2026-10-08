#!/usr/bin/env python3
"""Bring an already built Forbidden Memories HD mod up to the current anime frame layout.

For trying the anime frame's kinds and digits without rebuilding the whole mod
(which needs the redrawn art folder): edits the mod's mod.json in place and adds
textures/anime_digits.png, the same things hd_assets_pack.py writes.

    python tools/pc/anime_frame_patch.py <mod folder> [--digit-font <.ttf>] [--digit-stretch 1.4]

- card_layout.kinds: ritual -> magic, orange -> monster, purple -> monster for each
  of them with no frame image of its own (a ritual frame that is magic's file is no
  frame of its own and is dropped).
- card_layout.atk / def: the stat boxes' centres, measured from textures/anime_frame_monster.png.
- card_layout.digits and textures/anime_digits.png: tools/pc/hd_recipes/anime_digits.png,
  or drawn from --digit-font.
A copy of the old mod.json is kept as mod.json.bak.
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_digits  # noqa: E402
import card_frame_window as W  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mod")
    parser.add_argument("--digit-font")
    parser.add_argument("--digit-stretch", type=float, default=card_digits.STRETCH)
    args = parser.parse_args()
    path = os.path.join(args.mod, "mod.json")
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    layout = manifest.get("card_layout")
    if not layout or "frame" not in layout:
        sys.exit(f"{path}: no card_layout.frame -- this mod has no anime frame to patch")
    shutil.copyfile(path, path + ".bak")
    frame = layout["frame"]
    magic = frame.get("magic", {}).get("image")
    if "ritual" in frame and frame["ritual"].get("image") == magic:
        del frame["ritual"]
    layout["kinds"] = {kind: wears for kind, wears in (("ritual", "magic"), ("orange", "monster"), ("purple", "monster"))
                       if kind not in frame}
    monster = os.path.join(args.mod, frame["monster"]["image"])
    centres = W.stat_box_centres(monster)
    if centres:
        layout.update(centres)
    digits = os.path.join(args.mod, "textures", "anime_digits.png")
    if args.digit_font:
        card_digits.render(args.digit_font, digits, args.digit_stretch)
    else:
        shutil.copyfile(os.path.join(HERE, "hd_recipes", "anime_digits.png"), digits)
    layout["digits"] = {"image": "textures/anime_digits.png", "width": 10, "height": 11, "step": 10}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=4, ensure_ascii=False)
    print(f"{path}: kinds {layout['kinds']}, atk {layout['atk']}, def {layout['def']}, digits {digits}")


if __name__ == "__main__":
    main()

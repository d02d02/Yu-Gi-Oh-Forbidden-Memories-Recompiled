#!/usr/bin/env python3
"""Give a built Forbidden Memories HD mod the anime frames for ritual monsters and the three gods.

    python tools/pc/kuriboh/add_monster_frames.py <mod folder> <folder holding monster-ritual-animeframe.png,
        monster-obelisk-animeframe.png, monster-ra-animeframe.png, monster-slifer-animeframe.png> [--game <retail .bin>]

Each picture becomes a frame style, picked by a card TAG (notes/more-cards.md "Tags"): "ritual" (purple), "obelisk"
(blue), "ra" (gold), "slifer" (pink); a mod's god monsters only need the tag. The retail ritual monsters (what each
ritual card summons, from the disc's table) get "ritual" through a tags-only `cards` entry of the HD mod.
The pictures are the player's own files and are not committed."""
import json, os, shutil, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from fm_editor import disc, gamedata as g

STYLES = (("ritual", "monster-ritual-animeframe.png", "purple"), ("obelisk", "monster-obelisk-animeframe.png", "blue"),
          ("ra", "monster-ra-animeframe.png", "gold"), ("slifer", "monster-slifer-animeframe.png", "pink"))

mod, frames = sys.argv[1], sys.argv[2]
game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "game/ygofm-orig-usa.bin"
path = os.path.join(mod, "mod.json")
data = json.load(open(path, encoding="utf-8"))
layout = data["card_layout"]
base = layout["frame_styles"]["gold"]
for tag, filename, color in STYLES:
    shutil.copy(os.path.join(frames, filename), os.path.join(mod, "textures", f"anime_frame_{tag}_monster.png"))
    layout["frame_styles"][f"{tag}-monster"] = {**base, "image": f"textures/anime_frame_{tag}_monster.png", "hand_colour": color}
tags = {t for t, _, _ in STYLES}
layout["frame_for"] = [r for r in layout["frame_for"] if r.get("tag") not in tags]
at = next((i for i, r in enumerate(layout["frame_for"]) if r.get("class")), len(layout["frame_for"]))
layout["frame_for"][at:at] = [{"tag": t, "style": f"{t}-monster"} for t, _, _ in STYLES]
files = disc.load(game)
rituals = g.read_game(files.slus, files.wa).rituals
results = sorted({record[-1] for record in rituals.values()})
data["cards"] = [c for c in data.get("cards", []) if c.get("replace") not in results] + \
    [{"replace": cid, "tags": ["ritual"]} for cid in results]
json.dump(data, open(path, "w", encoding="utf-8"), indent=4)
print("ok", mod, len(results), "ritual monsters tagged")

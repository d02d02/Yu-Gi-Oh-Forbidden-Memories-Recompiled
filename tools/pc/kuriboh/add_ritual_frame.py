#!/usr/bin/env python3
"""Give a built Forbidden Memories HD mod the blue ritual frame (the retail ritual color) in its anime layout.

    python tools/pc/kuriboh/add_ritual_frame.py <mod folder>

Copies tools/pc/hd_recipes/anime_frame_ritual.png (the magic frame turned blue) to textures/, adds the "blue"
frame style and the rule that makes ritual spells and any card whose own frame color is blue (the Kuriboh mod's
ritual-like cards) wear it, and the sub-option "Ritual spells: own frame" (on by default).
A new build (hd_assets_pack.py) does this by itself: it picks the PNG up from hd_recipes."""
import json, os, shutil, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import anime_frame_layout as L

mod = sys.argv[1]
path = os.path.join(mod, "mod.json")
data = json.load(open(path, encoding="utf-8"))
layout = data["card_layout"]
shutil.copy(os.path.join(os.path.dirname(L.__file__), "hd_recipes", "anime_frame_ritual.png"),
            os.path.join(mod, "textures", "anime_frame_ritual.png"))
green = layout["frame_styles"]["green"]
layout["frame_styles"]["blue"] = {**green, "image": "textures/anime_frame_ritual.png", "hand_colour": "blue"}
rule = {"class": "ritual_spell", "style": "blue", "setting": L.RITUAL_SETTING["key"]}
layout["frame_for"] = [r for r in layout["frame_for"] if r.get("style") != "blue"]
layout["frame_for"].insert(0, rule)
data["settings"] = [s for s in data["settings"] if s["key"] != L.RITUAL_SETTING["key"]] + [dict(L.RITUAL_SETTING)]
json.dump(data, open(path, "w", encoding="utf-8"), indent=4)
print("ok", mod)

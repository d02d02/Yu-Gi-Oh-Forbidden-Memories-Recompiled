#!/usr/bin/env python3
"""Check the Anime Style mod folder before it is zipped and released.

    python tools/pc/anime_art_check.py [mods/anime-art]

Exit status 1 and a line per problem when anything below is wrong:
  - mod.json loads, is called Anime Style, id anime-art, and every frame style's picture and every rule's style/setting exist;
  - every picture under textures/ has power-of-two sides (v0.3.0 draws other sizes invisibly at Internal 2x/4x on some cards);
  - the ATK/DEF digit picture has real soft edges: partial alpha, and no opaque light pixels around the ink. Edge pixels that are
    opaque and light show as a pale contour whenever the plaque behind them is not the same cream (the greyed digits of the attack
    screen, the flash of an attack) -- this was a release bug, hence the check;
  - hd/manifest.json lists only pictures that are in hd/, all under the mod's `hd_assets` setting;
  - HOWTO.txt exists, README.md does not, and CREDITS.txt is the two credit lines.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

LUMA = np.array([0.299, 0.587, 0.114])


def power_of_two(n):
    return n > 0 and n & (n - 1) == 0


def check(root):
    problems = []
    manifest = json.load(open(os.path.join(root, "mod.json"), encoding="utf-8"))
    if manifest.get("id") != "anime-art":
        problems.append("mod.json id is not anime-art")
    if manifest.get("name") != "Anime Style":
        problems.append("mod.json name is %r, not 'Anime Style'" % manifest.get("name"))
    layout = manifest.get("card_layout", {})
    styles = layout.get("frame_styles", {})
    settings = {s["key"] for s in manifest.get("settings", [])}
    for name, style in styles.items():
        if not os.path.exists(os.path.join(root, style["image"])):
            problems.append("style %s: %s is missing" % (name, style["image"]))
    for rule in layout.get("frame_for", []):
        if rule["style"] not in styles:
            problems.append("a frame_for rule names the unknown style %s" % rule["style"])
        if "setting" in rule and rule["setting"] not in settings:
            problems.append("a frame_for rule uses the undeclared setting %s" % rule["setting"])
    tags = {r["tag"] for r in layout.get("frame_for", []) if "tag" in r}
    for card in manifest.get("cards", []):
        for tag in card.get("tags", []):
            if tag not in tags:
                problems.append("card %s has the tag %s that no rule uses" % (card.get("replace"), tag))

    textures = os.path.join(root, "textures")
    for f in sorted(os.listdir(textures)):
        w, h = Image.open(os.path.join(textures, f)).size
        if not (power_of_two(w) and power_of_two(h)):
            problems.append("textures/%s is %dx%d, not power-of-two" % (f, w, h))

    digits = np.asarray(Image.open(os.path.join(textures, "anime_digits.png")).convert("RGBA")).astype(float)
    alpha = digits[..., 3]
    opaque = alpha > 250
    partial = (alpha > 8) & (alpha < 247)
    if partial.sum() < 0.03 * (alpha > 8).sum():
        problems.append("anime_digits.png has hard edges (only %.1f%% partial alpha)" % (100 * partial.sum() / max((alpha > 8).sum(), 1)))
    half = digits.shape[0] // 2
    for label, rows in (("normal", slice(0, half)), ("dimmed", slice(half, digits.shape[0]))):
        block, op = digits[rows], opaque[rows]
        luma = block[..., :3] @ LUMA
        ink = np.median(luma[op]) if op.any() else 0
        pale = (luma[op] > ink + 60).mean() if op.any() else 0
        if pale > 0.005:
            problems.append("anime_digits.png (%s set): %.1f%% of the opaque pixels are pale, a baked light edge" % (label, 100 * pale))

    hd = os.path.join(root, "hd")
    entries = json.load(open(os.path.join(hd, "manifest.json"), encoding="utf-8"))
    missing = sorted({e["file"] for e in entries if not os.path.exists(os.path.join(hd, e["file"]))})
    if missing:
        problems.append("hd/manifest.json lists %d missing pictures, e.g. %s" % (len(missing), missing[:3]))
    wrong = {e.get("setting") for e in entries} - {"hd_assets"}
    if wrong:
        problems.append("hd/manifest.json has entries under other settings: %s" % sorted(map(str, wrong)))

    if not os.path.exists(os.path.join(root, "HOWTO.txt")):
        problems.append("HOWTO.txt is missing")
    if os.path.exists(os.path.join(root, "README.md")):
        problems.append("README.md should not be shipped (HOWTO.txt is the guide)")
    credits = open(os.path.join(root, "CREDITS.txt"), encoding="utf-8").read().strip().splitlines()
    if credits != ["HD pictures - Forbidden Memories HD by Unchiga and X@nder.", "Anime/Frame Art - d02d02 and Hræzlyr."]:
        problems.append("CREDITS.txt is not the two credit lines")
    return problems, manifest


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(here)), "mods", "anime-art")
    problems, manifest = check(root)
    for p in problems:
        print("PROBLEM:", p)
    print("Anime Style %s: %s" % (manifest.get("version"), "%d problem(s)" % len(problems) if problems else "all checks passed"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

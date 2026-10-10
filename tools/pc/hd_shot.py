#!/usr/bin/env python3
"""Headless A/B pictures of a screen with and without an HD pack, at Internal 4x (yfm_control.py).

    python tools/pc/hd_shot.py --pack tmp/pc/packs/p1b-menu --screen title --out tmp/pc/shots/menu

Each run is a game of its own with a mods folder holding only the pack (on) or nothing (off), so no
other mod of the user's is in the picture. Writes <out>-off.png, <out>-on.png and <out>-both.png (side by side).
`--screen`: a yfm_control `goto` target (title, library, password, options, free_duel, build_deck...);
`--press start,cross` presses buttons after it, `--wait N` steps N frames before the picture.
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yfm_control import Game  # noqa: E402


def take(mods: Path, screen: str, presses: list, wait: int, scale: int, target: Path) -> Path:
    with Game(mods_dir=mods, settings={"internal_scale": scale}, env={"MEMORIES_DUMP_PICTURE": "1"}) as game:
        game.goto(screen)
        game.step(300)
        for key in presses:
            game.press(key)
            game.step(150)
        game.step(wait)
        return Path(shutil.copyfile(game.shot("shot.png"), target))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", action="append", default=[], help="a mod folder (mod.json inside) to test")
    parser.add_argument("--screen", default="title")
    parser.add_argument("--press", default="")
    parser.add_argument("--wait", type=int, default=120)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    presses = [k for k in args.press.split(",") if k]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, packs in (("off", []), ("on", args.pack)):
        with tempfile.TemporaryDirectory() as mods:
            for pack in packs:
                shutil.copytree(pack, Path(mods) / Path(pack).name)
            paths[name] = take(Path(mods), args.screen, presses, args.wait, args.scale, Path(f"{out}-{name}.png"))
    from PIL import Image
    a, b = Image.open(paths["off"]), Image.open(paths["on"])
    both = Image.new("RGB", (a.width + b.width + 8, a.height), (255, 0, 255))
    both.paste(a, (0, 0))
    both.paste(b, (a.width + 8, 0))
    both.save(f"{out}-both.png")
    print(f"{out}-both.png", a.size)


if __name__ == "__main__":
    main()

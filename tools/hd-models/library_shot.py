"""The Library's model view of one card, a few frames apart: the studio's turntable scene (route A).

    python library_shot.py OUT [--card 364] [--start 0] [--every 20] [--frames 120] [--scale 2] [--setting NAME=VALUE] [--env NAME=VALUE]

Opens View > Library with every card shown, walks to the card (R1, right x10, down x6, right x5 reach
card 366; other cards by left/right presses from there), opens its model view (Cross, Triangle, Square) and writes one frame per step into
OUT/gl-NNNN-lib/ and OUT/sheet.png. Needs MEMORIES_DISC. Same capture path as field_attack.py.
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent)); from _paths import DEV, EXE
sys.path.insert(0, str(DEV))
import yfm_control as yc   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--card", type=int, default=364)
ap.add_argument("--start", type=int, default=0)
ap.add_argument("--every", type=int, default=20)
ap.add_argument("--frames", type=int, default=120)
ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--setting", action="append", default=[], help="NAME=VALUE game setting")
ap.add_argument("--env", action="append", default=[], help="NAME=VALUE passed to the game")
ap.add_argument("--exe", default=str(EXE))
a = ap.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
ANCHOR_CARD = 366   # right x10, down x6, right x5 after R1 lands on card 366 (measured)
settings = {"mod.3d-monsters": 1, "mod.camera-pin": 1, "library_all_cards": 1}
settings.update(dict(x.split("=", 1) for x in a.setting))
env = {"MEMORIES_FPS": "-1", "MEMORIES_WINDOW_HIDDEN": "1"}   # the game window is never shown
env.update(dict(e.split("=", 1) for e in a.env))
state = out / "library.state"

if not state.exists():
    with yc.Game(executable=a.exe, out=out / "make", settings={**settings, "internal_scale": 1}, env=env) as g:
        g.goto("library")
        g.step(60)
        g.press("r1", after=30)
        delta = a.card - ANCHOR_CARD     # the cursor walks one card per right/left press
        keys = ["right"] * 10 + ["down"] * 6 + ["right"] * 5 + (["right"] * delta if delta > 0 else ["left"] * -delta)
        for key in keys:
            g.press(key, hold=6, after=14)
        g.step(30)
        g.save(out / "cursor.state")
        for key in ("cross", "triangle", "square"):
            g.press(key, hold=6, after=30)
        g.step(30)
        g.save(state)

ks = list(range(a.start, a.frames + 1, a.every))
shots = []
for k in ks:
    d = out / f"gl-{k:04d}-lib"; d.mkdir(exist_ok=True)
    with yc.Game(executable=a.exe, out=out / f"look-{k:04d}", settings=dict(settings, internal_scale=a.scale), env=env, headless=False) as g:
        g.load(state)
        g.step(k)
        f = g.info()["frame"]
    e = dict(env, MEMORIES_WINDOW_SHOT=str(f), MEMORIES_SCREENSHOT_DIR=str(d))
    with yc.Game(executable=a.exe, out=out / f"shot-{k:04d}", settings=dict(settings, internal_scale=a.scale), env=e, headless=False) as g:
        g.load(state)
        for _ in range(k + 60):
            g.step(1)
            if list(d.glob("*.bmp")): break
    got = sorted(d.glob("*.bmp"))
    print(k, f, [p.name for p in got], flush=True)
    if got:
        shots.append((str(k), got[0]))

from PIL import Image, ImageDraw   # noqa: E402
if shots:
    w = 480
    tiles = []
    for label, path in shots:
        im = Image.open(path).convert("RGB"); im = im.resize((w, int(im.height * w / im.width)))
        ImageDraw.Draw(im).text((6, 4), label, fill=(255, 255, 0)); tiles.append(im)
    cols = 4; rows = (len(tiles) + cols - 1) // cols; h = tiles[0].height
    sheet = Image.new("RGB", (cols * w, rows * h))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out / "sheet.png"); print("sheet", out / "sheet.png")

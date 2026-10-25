#!/usr/bin/env python3
"""A field attack (3D Monsters' attack=2) in a REAL window, GL pictures of chosen frames, and a contact sheet.

    python -I field_attack.py OUTDIR [--native] [--scale 2] [--start 0] [--every 12] [--frames 240] [--cards 364,364,364] [--attack 1,4]

Setup is rigkit's driver: the first monster face up on column 3, a turn, the second on column 1, then the attack
(Cross, the game's own). The state is saved at the commit; a windowed game loads it and is stepped, one run per shot
(MEMORIES_WINDOW_SHOT), as attack_window_gpu.py does. --native turns the "native-test" mod on (a package for card 364 in the
game's mods folder). The disc comes from MEMORIES_DISC. Set MEMORIES_TRACE=model through --env for the event log."""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent)); from _paths import DEV, EXE
sys.path.insert(0, str(DEV)); sys.path.insert(0, str(DEV / "rigs"))
import yfm_control as yc   # noqa: E402
import rigkit              # noqa: E402

BATTLE_STEP = 0x8009B174   # the battle sub-step in its low nibble (scene phase 9)

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--native", action="store_true"); ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--start", type=int, default=0); ap.add_argument("--every", type=int, default=12); ap.add_argument("--frames", type=int, default=240)
ap.add_argument("--cards", default="58,364,364,332,683", help="the player's hand (the first two are played: the filler of the first turn, then the attacker)")
ap.add_argument("--filler-column", type=int, default=4, help="where the first turn's card stands (column 0 does not take the second card)")
ap.add_argument("--filler-up", action="store_true", help="the first turn's card face up (a 3D model that can stand in the view); face down it is a flat card back")
ap.add_argument("--attack", default="1,4", help="column of the attacker, column of the target")
ap.add_argument("--clip", action="store_true", help="every frame of the attack from one run (frames in OUT/clip/bmp), then OUT/clip.mp4 and .gif (make_video.py; needs imageio-ffmpeg)")
ap.add_argument("--fps", type=int, default=30, help="the clip's frame rate (the field runs at 60, the arena at 30)")
ap.add_argument("--idle", action="store_true", help="the state after the second card is placed, no attack: the field with its monsters standing (--start/--every/--frames count from it)")
ap.add_argument("--arena", action="store_true", help="the game's own arena attack (the commit is Square, not Cross; with --setting mod.3d-monsters.attack=0)")
ap.add_argument("--setting", action="append", default=[], help="NAME=VALUE game setting")
ap.add_argument("--env", action="append", default=[], help="NAME=VALUE passed to the game")
ap.add_argument("--exe", default=str(EXE))
a = ap.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
settings = {"mod.3d-monsters": 1, "mod.3d-monsters.attack": 2, "mod.camera-pin": 1, "mod.native-test": int(a.native)}
settings.update(dict(s.split("=", 1) for s in a.setting))
env = {"MEMORIES_FPS": "-1", "MEMORIES_WINDOW_HIDDEN": "1"}   # the game window is never shown
env.update(dict(e.split("=", 1) for e in a.env))
hand = [int(c) for c in a.cards.split(",")]
column, target = (int(x) for x in a.attack.split(","))
state = out / "attack.state"


def step_of(g):
    return g.u8(BATTLE_STEP) & 15 if g.phase() == 9 else None


if not state.exists():
    with yc.Game(executable=a.exe, out=out / "make", settings={**settings, "internal_scale": 1}, env=env) as g:
        g.goto("duel", opponent=1, deck=",".join(map(str, hand)))
        g.duel_ready(before_deal=lambda gg: gg.arrange_deck(0, hand))
        rigkit.play_at(g, 0, a.filler_column, face_up=a.filler_up)
        g.end_turn(); g.wait_turn(("hand",))
        rigkit.play_at(g, 0, 1, face_up=True)
        print("field", g.field(), flush=True)
        if a.arena:
            crosses, real_press = [], g.press
            def press(keys, *k, **kw):
                if keys == "cross":
                    crosses.append(1)
                    if len(crosses) == 2:
                        keys = "square"
                return real_press(keys, *k, **kw)
            g.press = press
        if a.idle:
            g.step(30)   # the second card has been placed: its monster stands
            g.save(state)
        else:
            g._settle = lambda *x, **k: g.save(state)
            g.attack(column, target)

if a.clip:
    d = out / "clip" / "bmp"; d.mkdir(parents=True, exist_ok=True)
    e = dict(env, MEMORIES_WINDOW_SHOT=f"{a.start + 2}-{a.frames + 2}", MEMORIES_SCREENSHOT_DIR=str(d))
    with yc.Game(executable=a.exe, out=out / "clip-run", settings=dict(settings, internal_scale=a.scale), env=e, headless=False) as g:
        g.load(state)
        for _ in range(a.frames + 20):
            g.step(1)
    import subprocess
    subprocess.run([sys.executable, "-I", str(Path(__file__).resolve().parent / "make_video.py"), str(out / "clip"), str(out / "clip"), "--fps", str(a.fps)], check=True)
    sys.exit(0)

ks = list(range(a.start, a.frames + 1, a.every))
look = dict(settings, internal_scale=a.scale)
frames = {}
with yc.Game(executable=a.exe, out=out / "look-measure", settings=look, env=env, headless=False) as g:
    g.load(state)
    if a.start:
        g.step(a.start)
    for k in ks:
        frames[k] = (g.info()["frame"], step_of(g)); g.step(a.every if k < ks[-1] else 1)
print("frames", frames, flush=True)
shots = []
for k in ks:
    f, st = frames[k]
    d = out / f"gl-{k:04d}-s{st}"; d.mkdir(exist_ok=True)
    e = dict(env, MEMORIES_WINDOW_SHOT=str(f), MEMORIES_SCREENSHOT_DIR=str(d))
    with yc.Game(executable=a.exe, out=out / f"look-{k:04d}", settings=look, env=e, headless=False) as g:
        g.load(state)
        for _ in range(k + 60):
            g.step(1)
            if list(d.glob("*.bmp")): break
    got = sorted(d.glob("*.bmp"))
    print(k, f, st, [p.name for p in got], flush=True)
    if got:
        shots.append((f"{k}-s{st}", got[0]))

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

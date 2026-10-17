#!/usr/bin/env python3
"""BLS vanilla attack (cursor rectangle = Square) in a REAL window, pictures taken from the window itself (not VRAM).

    python -I attack_window.py OUTDIR [--native HDM] [--scale 4] [--every 15]

Setup is rigkit's driver (yfm_control.Game + rigkit.play_at): BLS on the field, then the attack with the last Cross replaced by Square.
The state is saved at the attack's commit; a second, windowed game loads it and is stepped; the window is grabbed from the desktop.
"""
import argparse, ctypes, ctypes.wintypes as wt, sys, time
from pathlib import Path

HACK = Path(__file__).resolve().parents[3]
DEV = HACK / "Yu-Gi-Oh-Forbidden-Memories-Recompiled-dev" / "tools" / "pc"
sys.path.insert(0, str(DEV)); sys.path.insert(0, str(DEV / "rigs"))
import yfm_control as yc   # noqa: E402
import rigkit              # noqa: E402
from PIL import ImageGrab  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--native", default=""); ap.add_argument("--scale", type=int, default=4)
ap.add_argument("--start", type=int, default=0); ap.add_argument("--every", type=int, default=15); ap.add_argument("--frames", type=int, default=300)
ap.add_argument("--env", action="append", default=[], help="NAME=VALUE passed to the game")
ap.add_argument("--exe", default=str(HACK / "shared/tools/hd-models/_exe/memories-pc.exe"))
a = ap.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
settings = {"mod.3d-monsters": 1, "mod.3d-monsters.attack": 0, "mod.2d-monsters": 0, "mod.camera-pin": 1}
env = {"MEMORIES_FPS": "-1"}   # every game frame is shown: a shot lands on exactly the frame asked for (else it waits for the next throttled present, a few frames later and different per run)
if a.native:
    env.update(MEMORIES_NATIVE_MODEL=str(Path(a.native).resolve()), MEMORIES_NATIVE_MODEL_ID="363", MEMORIES_NATIVE_MODEL_LOG="1")
env.update(dict(e.split("=", 1) for e in a.env))
hand = [374, 364, 100, 332, 683]
state = out / "attack.state"

if not state.exists():
  with yc.Game(executable=a.exe, out=out / "make", settings={**settings, "internal_scale": 1}, env=env) as g0:
      g0.goto("duel", opponent=1, deck=",".join(map(str, hand)))
      g0.duel_ready(before_deal=lambda g: g.arrange_deck(0, hand))
      rigkit.play_at(g0, 0, 3, face_up=True)
      g0.end_turn(); g0.wait_turn(("hand",))
      rigkit.play_at(g0, 0, 1, face_up=True)
      crosses = []
      real_press = g0.press
      def press(keys, *k, **kw):
          if keys == "cross":
              crosses.append(1)
              if len(crosses) == 2:
                  keys = "square"          # the vanilla attack: the rectangle button instead of X
                  print("pressing SQUARE to commit the attack", flush=True)
          return real_press(keys, *k, **kw)
      g0.press = press
      g0._settle = lambda *x, **k: g0.save(state)
      g0.attack(1, 4)


# GL pictures, robustly: the game itself reads its window's back buffer (MEMORIES_WINDOW_SHOT=<frame> -> glReadPixels, sdl.c),
# no desktop grab (all-black / occluded). One real-window run per shot; runs are deterministic, so frame numbers repeat.
ks = list(range(0, a.frames + 1, a.every))
look = dict(settings, internal_scale=a.scale)
frames = {}
with yc.Game(executable=a.exe, out=out / "look-measure", settings=look, env=env, headless=False) as g:
    g.load(state)
    for k in ks:
        frames[k] = (g.info()["frame"], rigkit.battle_step(g)); g.step(a.every if k < ks[-1] else 1)
print("frames", frames, flush=True)
for k in [k for k in ks if k >= a.start]:
    f, st = frames[k]
    d = out / f"gl-{k:04d}-s{st}"; d.mkdir(exist_ok=True)
    e = dict(env, MEMORIES_WINDOW_SHOT=str(f), MEMORIES_SCREENSHOT_DIR=str(d))
    with yc.Game(executable=a.exe, out=out / f"look-{k:04d}", settings=look, env=e, headless=False) as g:
        g.load(state)
        for _ in range(k + 60):          # one vblank at a time: the shot lands on the same frame in every run
            g.step(1)
            if list(d.glob("*.bmp")): break
    print(k, f, st, [p.name for p in d.glob("*.bmp")], flush=True)

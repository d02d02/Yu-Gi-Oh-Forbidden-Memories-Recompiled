#!/usr/bin/env python3
"""Every frame of a stretch of the arena attack, from ONE real-window run (MEMORIES_WINDOW_SHOT=<first>-<last>, needs a build with the range).
    python attack_clip.py FRAMES_DIR --native MODEL.hdm [--from 900] [--to 1140] [--exe ...]
FRAMES_DIR: where the raw BMP frames go (keep it OUT of OneDrive: hundreds of MB). Then: make_video.py FRAMES_DIR OUT_PREFIX."""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from _paths import HACK, DEV, EXE, STATE
sys.path.insert(0, str(DEV)); sys.path.insert(0, str(DEV / "rigs"))
import yfm_control as yc   # noqa: E402
ap = argparse.ArgumentParser(); ap.add_argument("frames"); ap.add_argument("--native", default="")
ap.add_argument("--from", dest="k1", type=int, default=900); ap.add_argument("--to", dest="k2", type=int, default=1140)
ap.add_argument("--scale", type=int, default=4)
ap.add_argument("--state", default=str(STATE))
ap.add_argument("--exe", default=str(EXE))
a = ap.parse_args()
out = Path(a.frames).resolve(); out.mkdir(parents=True, exist_ok=True)
settings = {"mod.3d-monsters": 1, "mod.3d-monsters.attack": 0, "mod.2d-monsters": 0, "mod.camera-pin": 1, "internal_scale": a.scale}
env = {"MEMORIES_FPS": "-1"}
if a.native: env.update(MEMORIES_NATIVE_MODEL=str(Path(a.native).resolve()), MEMORIES_NATIVE_MODEL_ID="363")
with yc.Game(executable=a.exe, out=out / "measure", settings=settings, env=env, headless=False) as g:
    g.load(a.state); g.step(a.k1); f1 = g.info()["frame"]; g.step(a.k2 - a.k1); f2 = g.info()["frame"]
print("frames", f1, "to", f2, flush=True)
shots = out / "bmp"; shots.mkdir(exist_ok=True)
env.update(MEMORIES_WINDOW_SHOT=f"{f1}-{f2}", MEMORIES_SCREENSHOT_DIR=str(shots))
with yc.Game(executable=a.exe, out=out / "run", settings=settings, env=env, headless=False) as g:
    g.load(a.state)
    for _ in range(a.k2 + 8): g.step(1)
print(len(list(shots.glob("*.bmp"))), "frames in", shots)

#!/usr/bin/env python3
"""Replay the saved arena attack in a REAL window at normal speed (no frame-exact capture), to WATCH a native model.

    python -I watch_attack.py STATEDIR --native X.hdm [--exe EXE] [--scale 2] [--seconds 60] [--env NAME=VALUE]
STATEDIR = a folder holding attack.state (made by attack_window_gpu.py; build-specific: the state must come from the same exe).
"""
import argparse, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from _paths import HACK, DEV, EXE, STATE
sys.path.insert(0, str(DEV)); sys.path.insert(0, str(DEV / "rigs"))
import yfm_control as yc   # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("statedir"); ap.add_argument("--native", default=""); ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--seconds", type=float, default=60); ap.add_argument("--speed", type=float, default=100, help="percent of real time"); ap.add_argument("--env", action="append", default=[])
ap.add_argument("--exe", default=str(EXE))
a = ap.parse_args()
sd = Path(a.statedir).resolve(); state = sd / "attack.state"
env = {}
if a.native: env.update(MEMORIES_NATIVE_MODEL=str(Path(a.native).resolve()), MEMORIES_NATIVE_MODEL_ID="363")
env.update(dict(e.split("=", 1) for e in a.env))
settings = {"mod.3d-monsters": 1, "mod.3d-monsters.attack": 0, "mod.2d-monsters": 0, "mod.camera-pin": 1, "internal_scale": a.scale}
with yc.Game(executable=a.exe, out=sd / "watch", settings=settings, env=env, headless=False) as g:
    g.load(state)
    t0 = time.time(); n = 0
    while time.time() - t0 < a.seconds:
        g.step(1); n += 1
        wait = t0 + n / (60.0 * a.speed / 100.0) - time.time()   # the control channel steps unthrottled: pace it (100 = real time, 60 vblanks/s)
        if wait > 0: time.sleep(wait)
    print(f"{n} steps in {time.time() - t0:.1f} s", flush=True)

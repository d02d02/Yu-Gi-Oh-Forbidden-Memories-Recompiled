"""Route A of the live preview (notes/studio/engine-needs.md): launch the game per run, no game-code change.

Builds the `field_attack.py` command for a package and a scene, runs it as a subprocess and lists the frames it wrote. Needs the
disc (MEMORIES_DISC) and a windowed game; `command()` and `frames()` are pure and testable without either.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELD_ATTACK = HERE.parent / "field_attack.py"
SCENES = ("field", "arena")
WINDOW = {"field": (60, 12, 240), "arena": (1250, 80, 1650)}   # (start, every, last frame) that show the fight (measured)        # the library turntable is a separate recipe (progress.md), not built here


def env_for(package, card_id, clip=None, extra=None):
    """Environment that forces one package onto one card: MEMORIES_NATIVE_MODEL(+_ID) and the clip name."""
    env = {"MEMORIES_NATIVE_MODEL": str(package), "MEMORIES_NATIVE_MODEL_ID": str(card_id)}
    if clip:
        env["MEMORIES_NATIVE_CLIP"] = str(clip)
    env.update(extra or {})
    return env


def command(scene, out_dir, package, card_id, *, clip=None, start=None, every=None, frames=None, scale=2, settings=(), extra_env=None):
    """argv for one scene run; `frames` is the LAST frame (shots at start, start+every ... up to it), not a count.
    Raises ValueError on an unknown scene or a bad frame range."""
    if scene not in SCENES:
        raise ValueError(f"scene must be one of {SCENES}, not {scene!r}")
    d_start, d_every, d_frames = WINDOW[scene]
    start, every, frames = d_start if start is None else start, d_every if every is None else every, d_frames if frames is None else frames
    if frames < 1 or every < 1 or start < 0:
        raise ValueError("frames and every must be at least 1, start at least 0")
    argv = [sys.executable, "-I", str(FIELD_ATTACK), str(out_dir), "--cards", f"58,{card_id},{card_id},332,683",
            "--scale", str(scale), "--start", str(start), "--every", str(every), "--frames", str(frames)]
    if scene == "arena":
        argv += ["--arena", "--setting", "mod.3d-monsters.attack=0"]
    for s in settings:
        argv += ["--setting", s]
    for name, value in env_for(package, card_id, clip, extra_env).items():
        argv += ["--env", f"{name}={value}"]
    return argv


def disc_available(environ=None):
    return bool((environ or os.environ).get("MEMORIES_DISC"))


def start(scene, out_dir, package, card_id, **kw):
    """Start the run; returns the Popen (poll it, kill it to cancel). Refuses when there is no disc."""
    if not disc_available():
        raise RuntimeError("Field and arena scenes need the disc: set MEMORIES_DISC.")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(command(scene, out_dir, package, card_id, **kw), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def frames(out_dir):
    """Frames written so far, in shot order: the per-shot gl-* folders hold one image each."""
    out = Path(out_dir)
    return sorted(p for p in out.glob("gl-*/*.bmp")) if out.is_dir() else []

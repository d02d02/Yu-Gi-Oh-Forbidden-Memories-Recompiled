#!/usr/bin/env python3
"""The Black Dragon (3DHaupt.com, "BGE Dragon", Dragon_Baked_Actions.blend) as a native model package.

    python make_dragon.py DRAGON_FOLDER OUT_PACKAGE [--blender PATH] [--height 450]

DRAGON_FOLDER is the extracted download (it holds blender/Dragon_Baked_Actions.blend and blender/textures/).
Blender 4.5 exports a glb (blender/export_dragon_blend.py: the skeleton cut to 120 bones, one material from the colour atlas),
native_convert.py makes OUT_PACKAGE (model.json, model.hdm, base.png) and its clips are mapped: idle Idel_New, enter and win
Fly_New, attack Run_New, hit/guard/destroyed Idel_New (the asset has no others). Not committed anywhere: its licence is unknown."""
import argparse, json, os, subprocess, sys
from pathlib import Path

here = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("folder"); ap.add_argument("out")
ap.add_argument("--blender", default=r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe")
ap.add_argument("--height", type=int, default=450, help="game units tall (Black Luster Soldier is 373)")
a = ap.parse_args()
folder = Path(a.folder).resolve(); out = Path(a.out).resolve()
blend = next(folder.rglob("Dragon_Baked_Actions.blend")); tex = next(folder.rglob("Dragon_Bump_Col2.jpg"))
glb = out.parent / (out.name + ".glb"); out.parent.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, OUT=str(glb), TEX=str(tex))
subprocess.run([a.blender, "-b", str(blend), "--python", str(here / "blender" / "export_dragon_blend.py")], env=env, check=True)
subprocess.run([sys.executable, "-I", str(here / "native_convert.py"), str(glb), str(out), "--rig", "generic", "--root", "pelvic_2",
                "--clips", "all", "--height", str(a.height), "--name", "Black Dragon", "--author", "3DHaupt.com",
                "--license", "unknown"], check=True)
mj = out / "model.json"; m = json.loads(mj.read_text())
m["clips"] = {"idle": "Idel_New", "enter": "Fly_New", "attack": "Run_New", "hit": "Idel_New", "guard": "Idel_New",
              "destroyed": "Idel_New", "win": "Fly_New"}
m["strike"] = {"attack": [25]}
mj.write_text(json.dumps(m, indent=2))
print("package:", mj)

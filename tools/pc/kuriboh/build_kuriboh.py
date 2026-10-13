"""Build the Kuriboh mod and its HD layer from the player's discs, and install them.

    python tools/pc/kuriboh/build_kuriboh.py <Kuriboh .bin/.iso> [--game <retail .bin>] [--id kuriboh] [--sources <folder>] [--install] [--scale 4]

Writes tmp/kuriboh/<id> (the mod, by the FM Editor's importer) and tmp/kuriboh/<id>-hd (its HD layer: tools/pc/kuriboh/make_hd.py),
and with --install copies both into the game's user mods folder (Documents\My Games\YFM Re-Decomp\mods on Windows,
~/.local/share/YFM Re-Decomp/mods on Linux), replacing what was there. Nothing of the ROM hack is committed.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def mods_folder() -> Path:
    """The game's own user mods folder (Documents may be moved, to OneDrive say): the editor's disc.user_dir()."""
    sys.path.insert(0, str(ROOT / "tools" / "pc"))
    from fm_editor import disc
    return disc.user_dir() / "mods"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("disc")
    p.add_argument("--game", default=str(ROOT / "game" / "ygofm-orig-usa.bin"))
    p.add_argument("--id", default="kuriboh")
    p.add_argument("--scale", default="4")
    p.add_argument("--sources", help="a folder of better card pictures, <card id>.png (make_hd.py --sources)")
    p.add_argument("--install", action="store_true")
    a = p.parse_args()
    out = ROOT / "tmp" / "kuriboh" / a.id
    hd = ROOT / "tmp" / "kuriboh" / f"{a.id}-hd"
    shutil.rmtree(out, ignore_errors=True)
    run = lambda *c: subprocess.run([sys.executable, *map(str, c)], cwd=ROOT, check=True)
    run("tools/pc/fm_editor", "import", a.disc, "--game", a.game, "--id", a.id, "-o", out)
    run("tools/pc/kuriboh/make_hd.py", out, hd, "--scale", a.scale, "--portraits", *(["--sources", a.sources] if a.sources else []))
    if a.install:
        folder = mods_folder()
        for source, name in ((out, a.id), (hd, f"{a.id}-hd")):
            shutil.rmtree(folder / name, ignore_errors=True)
            shutil.copytree(source, folder / name)
        print(f"installed {a.id} and {a.id}-hd in {folder}")


main()

#!/usr/bin/env python3
"""A rigged glTF / glb -> a whole mod that draws it in place of a card's monster.

    new_native_mod.py MODEL.glb --card 364 [--card 365 ...] --out mods/my-angel [--id my-angel] [--name "My angel"]
                      [--author A] [--license L] [-- native_convert.py options: --clips-from X.glb --root-height 320 ...]

Writes OUT/models/<model>/ (native_convert.py: model.hdm, base.png ..., model.json) and OUT/mod.json with its
"native_models" entry, then checks the mod as the game will (native_check.py). Run it again with another model (or
the same one, other cards) and the same --out: the entry is added, or the model's entry gets the new cards.
To play: copy OUT into the game's mods folder (or the mods folder of your user directory), apply the mod in Mods
and restart the game; at View > Internal 1x the disc's own model is drawn (the native pass needs Internal 2x or more)."""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_check  # noqa: E402
import native_spec as spec  # noqa: E402


def slug(text):
    s = re.sub(r"[^a-z0-9_-]+", "-", text.lower()).strip("-")
    return s[:63] or "native-model"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    passed = []
    if "--" in argv:
        at = argv.index("--")
        argv, passed = argv[:at], argv[at + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gltf", type=Path)
    ap.add_argument("--card", type=int, action="append", required=True, help="a card the model stands for (repeat for more)")
    ap.add_argument("--out", type=Path, required=True, help="the mod folder")
    ap.add_argument("--id", help="the mod's id (default: the folder's name)")
    ap.add_argument("--name", help="what the Mods window shows")
    ap.add_argument("--author", default="")
    ap.add_argument("--license", default="", help="the model's licence (CC-BY-4.0, CC0 ...): say what you may share")
    a = ap.parse_args(argv)
    for card in a.card:
        if not 1 <= card <= 65535:
            print(f"new_native_mod: --card {card}: a card id (1 to 65535)", file=sys.stderr)
            return 1
    mod_id = a.id or slug(a.out.resolve().name)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,63}", mod_id):
        print(f"new_native_mod: --id {mod_id}: 1-63 letters, digits, hyphens or underscores", file=sys.stderr)
        return 1
    folder = f"models/{slug(a.gltf.stem)}"
    try:
        import native_convert  # numpy and Pillow: only the conversion needs them
    except ImportError as e:
        print(f"new_native_mod: {e.name} is missing: pip install numpy pillow", file=sys.stderr)
        return 1
    convert_args = [str(a.gltf), str(a.out / folder), "--name", a.name or a.gltf.stem, "--author", a.author,
                    "--license", a.license, *passed]
    if native_convert.main(convert_args):
        return 1

    manifest_path = a.out / "mod.json"
    if manifest_path.exists():
        manifest = spec.read_json(manifest_path)
    else:
        manifest = {"id": mod_id, "name": a.name or a.gltf.stem, "version": "1.0", "author": a.author,
                    "description": f"Draws {a.gltf.stem} in place of the monster of card {', '.join(map(str, a.card))} "
                                   "(View > Internal 2x or more).",
                    "enabled": True}
    entries = manifest.setdefault("native_models", [])
    package = f"{folder}/model.json"
    for entry in entries:  # another card never stays on two entries of this mod
        if entry.get("package") != package and isinstance(entry.get("cards"), list):
            entry["cards"] = [c for c in entry["cards"] if c not in a.card]
    entries[:] = [e for e in entries if e.get("package") == package or e.get("cards") or "card" in e or "model" in e]
    mine = next((e for e in entries if e.get("package") == package), None)
    if mine is None:
        entries.append({"cards": sorted(set(a.card)), "package": package})
    else:
        mine["cards"] = sorted(set(mine.get("cards", [])) | set(a.card))
    manifest_path.write_text(json.dumps(manifest, indent=4) + "\n", encoding="utf-8")
    print(f"{manifest_path}: native_models has {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    print()
    status = native_check.main([str(a.out)])
    print()
    print(f"To play: copy {a.out} into the game's mods folder (or your user directory's), apply \"{manifest['name']}\" in Mods, "
          "restart, and set View > Internal 2x or more.")
    return status


if __name__ == "__main__":
    sys.exit(main())

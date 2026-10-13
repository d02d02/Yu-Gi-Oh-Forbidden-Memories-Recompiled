"""An HD layer for an imported Kuriboh mod: its changed card pictures and thumbnails at 4x, as a texture pack of its own.

    python tools/pc/kuriboh/make_hd.py <imported mod folder> <out folder> [--scale 4] [--portraits]

`out` becomes the mod `kuriboh-hd` (requires `kuriboh`, loads after `assets-hd` and `kuriboh`): the same pack entries the
import wrote, so it is drawn for exactly the slots the mod changed, over `assets-hd`'s picture of the retail card, with a
larger image (the game stretches a pack image to the texture, and Internal 2x and 4x draw all of it). The images are the mod's
own pictures enlarged (Lanczos and a light unsharp mask): no ROM hack art is committed, the folder is built from the user's disc.
`--portraits` also enlarges the mod's portraits/ PNGs in place (a roster face is kept whole for the scaled picture).
`--sources <folder>` takes better pictures than the enlargement: a card's `<id>.png` (or `.jpg`, `.webp`; the id with or without
leading zeros) in that folder is fitted to the card's picture frame (102:96, cropped from the middle, a little high) and becomes its
4x picture; its thumbnail is cut from it where the game cuts the card's own (tools/pc/hd_recipes/thumb_crops.json). The pictures
are the user's own files (found anywhere, for instance a card's official artwork); nothing is committed.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageFilter


def enlarge(path: Path, target: Path, scale: int):
    image = Image.open(path).convert("RGBA")
    big = image.resize((image.width * scale, image.height * scale), Image.LANCZOS)
    rgb = big.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
    rgb.putalpha(big.getchannel("A"))
    target.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(target)


def enlarge_portrait(path: Path, scale: int):
    """A portrait enlarged in place: by Real-ESRGAN (the anime model) when realesrgan-ncnn-vulkan is installed, else Lanczos."""
    import os
    import subprocess
    exe = Path(os.environ.get("REALESRGAN") or Path(__file__).resolve().parents[3] / "tmp" / "pc" / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe")
    if scale == 4 and exe.exists():
        target = path.with_name(path.stem + "-ai.png")
        done = subprocess.run([str(exe), "-i", str(path.resolve()), "-o", str(target.resolve()), "-n", "realesrgan-x4plus-anime",
                               "-s", "4", "-m", str(exe.parent / "models")], capture_output=True)
        if done.returncode == 0 and target.exists():
            target.replace(path)
            return
    enlarge(path, path, scale)


def find_source(folder: Path, cid: int):
    for name in (f"{cid}", f"{cid:03d}", f"{cid:04d}"):
        for extension in (".png", ".jpg", ".jpeg", ".webp"):
            path = folder / (name + extension)
            if path.exists():
                return path
    return None


def fit_art(path: Path, scale: int) -> Image.Image:
    """The picture cropped to the frame's 102:96 (from the middle, a little high) and sized 102*scale x 96*scale."""
    image = Image.open(path).convert("RGBA")
    ratio = 102 / 96
    if image.width / image.height > ratio:
        width = round(image.height * ratio)
        left = (image.width - width) // 2
        box = (left, 0, left + width, image.height)
    else:
        height = round(image.width / ratio)
        top = round((image.height - height) * 0.4)
        box = (0, top, image.width, top + height)
    return image.crop(box).resize((102 * scale, 96 * scale), Image.LANCZOS)


def thumbnail_of(art: Image.Image, cid: int, scale: int) -> Image.Image:
    """The card's thumbnail cut from its picture where the game cuts its own (a middle 40:32 otherwise)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from fm_editor import art as editor_art
    crop = editor_art.thumb_crops().get(cid)
    if crop:
        x, y, w, h = crop
        box = (x * scale, y * scale, (x + w) * scale, (y + h) * scale)
    else:
        w, h = art.width, round(art.width * 32 / 40)
        top = (art.height - h) // 2
        box = (0, top, w, top + h)
    return art.crop(tuple(round(v) for v in box)).resize((40 * scale, 32 * scale), Image.LANCZOS)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("out")
    p.add_argument("--scale", type=int, default=4)
    p.add_argument("--portraits", action="store_true")
    p.add_argument("--sources", help="a folder of better pictures, <card id>.png")
    a = p.parse_args()
    source, out = Path(a.source), Path(a.out)
    manifest = json.loads((source / "textures" / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest if isinstance(manifest, list) else manifest["entries"]
    shutil.rmtree(out, ignore_errors=True)
    sources = Path(a.sources) if a.sources else None
    used = {}
    for entry in entries:
        import re
        cid = int(re.search(r"card (\d+)", entry["alias"]).group(1))
        found = find_source(sources, cid) if sources else None
        target = out / "textures" / entry["file"]
        if found:
            art = fit_art(found, a.scale)
            image = art if "thumbnail" not in entry["alias"] else thumbnail_of(art, cid, a.scale)
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target)
            used[cid] = found.name
        else:
            enlarge(source / "textures" / entry["file"], target, a.scale)
    (out / "textures" / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    mod = {"id": "kuriboh-hd", "name": "Kuriboh HD", "version": "1.0",
           "description": f"The Kuriboh mod's changed card pictures and thumbnails at {a.scale}x.",
           "requires": ["kuriboh"], "after": ["forbidden-memories-hd", "kuriboh"], "textures": "textures"}
    (out / "mod.json").write_text(json.dumps(mod, indent=2), encoding="utf-8")
    if a.portraits:
        for png in sorted((source / "portraits").glob("*.png")):
            enlarge_portrait(png, a.scale)
    if used:
        print(f"better pictures used for {len(used)} cards: " + ", ".join(f"{c} ({n})" for c, n in sorted(used.items())))
    print(f"{len(entries)} images at {a.scale}x in {out}" + (", portraits enlarged" if a.portraits else ""))


main()

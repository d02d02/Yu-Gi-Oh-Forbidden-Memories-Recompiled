#!/usr/bin/env python3
"""Enlarge every static image the extractor reads from the disc by the Forbidden Memories HD method, no recipe.

hd_screen_pack.py makes one screen's pack from a recipe that says which pieces the game draws and how to
enlarge each. This does the rest of the game without one: each image extract_images.py wrote (its
manifest.json) goes through the same scalers and the same back-projection (each 4x4 block's average is
the texel it came from, so the colors stay the game's):

  few colors (up to --pixel-colors opaque colors: menus, icons, glyphs)  -> xBR (ffmpeg), each opaque region alone
  painted art (everything else: backgrounds, story pictures, effects)     -> Real-ESRGAN mixed with Lanczos
                                                                           (--model-share), the whole image at once

A story picture ("scenes") is several 64-word columns of one picture: they are joined for the scaler and cut
apart after, so no seam shows. Images the HD mod already holds (--exclude <its textures/manifest.json>, matched
by archive, offset, depth and palette) are left to it. Without a recipe nothing knows which pieces of a sheet the
game cuts out on their own, so a sprite sheet's neighbours can bleed into each other's edges; add a recipe for a
screen where that shows (hd_screen_pack.py), its images take precedence in the mods' load order.

    python tools/pc/extract_images.py --data game/DATA --out tmp/pc/images sheets scenes
    python tools/pc/hd_auto_pack.py --images tmp/pc/images --out tmp/pc/packs/hd-auto \
        --exclude <mods>/forbidden-memories-hd/textures/manifest.json [--only sheets/menu] [--limit N]

Needs ffmpeg (xBR) and realesrgan-ncnn-vulkan (or Upscayl's upscayl-bin), as hd_screen_pack.py does. The images
are made from the game's: for your own use, never commit or share them.
"""
import argparse
import collections
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hd_screen_pack as hs  # noqa: E402

CHUNK_PIXELS = 400_000   # pixels per batch of readings (the 16x outputs are held until written)


def identity(entry):
    return (entry["archive"], entry["offset"], entry["bpp"], entry.get("clut_offset"))


def load_exclusions(paths):
    done = set()
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        done |= {identity(e) for e in (data if isinstance(data, list) else data["entries"])}
    return done


def classify(rgba, pixel_colors):
    """'skip', 'pixel' or 'model' for a RGBA picture."""
    opaque = rgba[..., 3] >= 128
    if opaque.sum() < 16:
        return "skip"
    colors = np.unique(rgba[..., :3][opaque].reshape(-1, 3), axis=0)
    return "pixel" if len(colors) <= pixel_colors else "model"


class Made:
    def __init__(self, out):
        self.out = out


def xbr_whole(rgba):
    """hd_screen_pack's xBR path for a whole picture in three ffmpeg runs instead of two per region: the
    colors enlarged and pulled back to the texels, the outline smoothed (regions up to SMOOTH_MAX across; a
    bigger one keeps its texels' hard edge, so a box does not grow past its corners)."""
    rgb, mask = rgba[..., :3], rgba[..., 3] >= 128
    filled = hs.fill_transparent(rgb, mask)
    big = hs.back_project(hs.SCALER.xbr(filled), filled, mask)
    alpha = hs.xbr_alpha(mask)
    labels, count = hs.regions(mask)
    ys, xs = np.nonzero(mask)
    lab = labels[ys, xs]
    top, left = np.full(count + 1, 1 << 30), np.full(count + 1, 1 << 30)
    bottom, right = np.full(count + 1, -1), np.full(count + 1, -1)
    np.minimum.at(top, lab, ys)
    np.minimum.at(left, lab, xs)
    np.maximum.at(bottom, lab, ys)
    np.maximum.at(right, lab, xs)
    big_regions = np.maximum(bottom - top, right - left) + 1 > hs.SMOOTH_MAX
    hard = hs.blocks(mask).astype(np.uint8) * 255
    use_hard = hs.blocks(big_regions[labels])
    alpha = np.where(use_hard, hard, alpha)
    out = np.dstack([big, alpha]).astype(np.uint8)
    out[alpha == 0, :3] = hs.blocks(rgba)[alpha == 0][:, :3]
    return out


def groups_of(entries):
    """Entries to make together: a story picture's columns (one palette) side by side, everything else alone."""
    joined = collections.OrderedDict()
    for entry in entries:
        key = (entry["sheet"], entry["clut_offset"], entry["bpp"]) if entry["file"].startswith("scenes/") else entry["file"]
        joined.setdefault(key, []).append(entry)
    return [sorted(g, key=lambda e: e["column"]) for g in joined.values()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images", default="tmp/pc/images")
    parser.add_argument("--out", default="tmp/pc/packs/hd-auto")
    parser.add_argument("--exclude", action="append", default=[], help="a mod's textures/manifest.json whose images are skipped")
    parser.add_argument("--only", action="append", default=[], help="keep entries whose file contains this text")
    parser.add_argument("--limit", type=int, help="stop after this many groups (a trial run)")
    parser.add_argument("--upscaler")
    parser.add_argument("--model", default="realesrgan-x4plus")
    parser.add_argument("--model-share", type=float, default=0.6)
    parser.add_argument("--pixel-colors", type=int, default=24)
    parser.add_argument("--id", default="hd-auto")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found: it makes the xBR enlargements")
    upscaler, models = hs.find_upscaler(args.upscaler)
    with open(os.path.join(args.images, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    entries = manifest if isinstance(manifest, list) else manifest["entries"]
    done = load_exclusions(args.exclude)
    # one entry per identity (the manifest may list the same picture under two aliases)
    seen, todo = set(), []
    for entry in entries:
        if identity(entry) in done or identity(entry) in seen:
            continue
        if args.only and not any(text in entry["file"] for text in args.only):
            continue
        seen.add(identity(entry))
        todo.append(entry)
    groups = groups_of(todo)
    if args.limit:
        groups = groups[:args.limit]
    print(f"{len(entries)} entries, {len(done)} held by other mods, {len(todo)} to do in {len(groups)} groups")
    out = args.out
    textures = os.path.join(out, "textures")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(textures)
    written, skipped, counts = [], 0, collections.Counter()
    started = time.time()
    with tempfile.TemporaryDirectory() as work:
        hs.SCALER = hs.Scaler(upscaler, models, args.model, args.model_share, work)
        batch, pixels = [], 0

        def flush():
            nonlocal batch, pixels
            if not batch:
                return
            hs.build([reading for _, reading in batch if isinstance(reading, hs.Reading)])
            for members, reading in batch:
                at = 0
                for entry in members:
                    w = entry["width"]
                    name = entry["file"].replace("/", "-")
                    Image.fromarray(reading.out[:, at * hs.S:(at + w) * hs.S]).save(os.path.join(textures, name))
                    written.append(dict(entry, file=name, alias="auto: " + entry["alias"], setting=args.id))
                    at += w
            batch, pixels = [], 0
            print(f"  {len(written)} images, {time.time() - started:.0f}s", flush=True)

        for members in groups:
            pictures = [np.array(Image.open(os.path.join(args.images, e["file"])).convert("RGBA")) for e in members]
            rgba = np.concatenate(pictures, 1)
            method = classify(rgba, args.pixel_colors)
            if method == "skip":
                skipped += len(members)
                continue
            h, w = rgba.shape[:2]
            if method == "pixel":
                reading = Made(xbr_whole(rgba))
            else:
                joined = os.path.join(work, "joined.png")
                Image.fromarray(rgba).save(joined)
                reading = hs.Reading(joined, {"method": method, "rects": [[0, 0, w, h]]})
            counts[method] += len(members)
            batch.append((members, reading))
            pixels += w * h
            if pixels >= CHUNK_PIXELS:
                flush()
        flush()
    for entry in written:
        entry.pop("sheet", None)
        entry.pop("column", None)
    with open(os.path.join(textures, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(written, handle, indent=1)
    with open(os.path.join(out, "mod.json"), "w", encoding="utf-8") as handle:
        json.dump({"id": args.id, "name": "Forbidden Memories HD, the rest of the game",
                   "version": "0.1", "author": "tools/pc/hd_auto_pack.py",
                   "description": "Menus, story pictures, effects and the other screens enlarged 4x by the HD mod's method "
                                  "(Real-ESRGAN mixed with Lanczos, xBR for few-color art, back-projected).",
                   "enabled": True, "textures": "textures"}, handle, indent=4)
    print(f"{out}: {len(written)} images ({counts['model']} model, {counts['pixel']} xBR, {skipped} empty skipped)")


if __name__ == "__main__":
    main()

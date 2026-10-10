#!/usr/bin/env python3
"""Redo the sprites a screen assembles from sheet pieces, as the game assembles them.

The game draws a button, a box or a label as several parts cut from a sheet, laid at offsets (a frame of the
screen's sprite bank, sprite_bank.py). Enlarged piece by piece (or as the whole sheet) the parts disagree at
the places they meet. Here each frame is composed from its parts in draw order, the composite is enlarged
once (the same model + Lanczos mix and back-projection as hd_screen_pack.py), and each part takes back its
own area of it. A piece used by several frames takes the average of what they gave. Only opaque texels are
replaced: a part's soft edges (a glow) keep the base pack's own enlargement.

    python tools/pc/hd_sprite_pack.py --images tmp/pc/images --pack tmp/pc/packs/p1b-menu \
        --bank tmp/pc/disc/DATA/SU.MRG:114 --cuts tmp/pc/dump-menu/assets.txt --only sheets/menu/a

`--pack` is a hd_auto_pack.py result, edited in place. A part is matched to its sheet by the rectangles a texture
dump saw the game cut (--cuts); a frame with a part that matches no sheet is left alone.
"""
import argparse
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hd_screen_pack as hs  # noqa: E402
import sprite_bank  # noqa: E402
from upscale_pack import read_cuts  # noqa: E402

S = hs.S


def redraw_label(big, text, font_file):
    """The grey (inactive) button label set anew in a serif italic: the old letters erased from the enlarged
    composite (its grain carried over them), the word set at the old letters' height and across their width
    (the letters' spacing taken up by tracking), light with a thin dark outline."""
    from PIL import ImageDraw, ImageFilter, ImageFont
    from scipy import ndimage as ndi
    h, w = big.shape[:2]
    zone = np.zeros((h, w), bool)
    zone[9 * S:24 * S, 5 * S:w - 5 * S] = True
    lum = big.astype(float).mean(2)
    tophat = lum - ndi.grey_opening(lum, size=(5 * S, 5 * S))   # bright marks narrower than 5 texels, whatever their level
    letters = zone & (tophat > 28)
    letters = ndi.binary_opening(letters, iterations=2)
    ys, xs = np.nonzero(letters)
    rows, cols = letters.sum(1), letters.sum(0)
    ry, rx = np.nonzero(rows > 0.3 * rows.max())[0], np.nonzero(cols > 0.12 * cols.max())[0]
    x0, x1, y0, y1 = int(rx.min()), int(rx.max()) + 1, int(ry.min()), int(ry.max()) + 1
    strokes = ndi.binary_dilation(zone & (tophat > 18), iterations=4) & zone
    keep = ~strokes
    est = np.stack([ndi.gaussian_filter(np.where(keep, big[..., c], 0).astype(float), 6) for c in range(3)], -1)
    est /= np.maximum(ndi.gaussian_filter(keep.astype(float), 6), 1e-3)[..., None]
    clean = np.where(strokes[..., None], est, big)
    # the word: capitals of the old letters' height, tracked out to their width
    size = 400
    font = ImageFont.truetype(font_file, size)
    cap = font.getbbox("H")
    scale = (y1 - y0) / (cap[3] - cap[1])
    font = ImageFont.truetype(font_file, max(8, round(size * scale)))
    cap = font.getbbox("H")
    glyphs = []
    for ch in text:
        if ch == " ":
            glyphs.append((None, font.getlength(" ") * 0.9))
            continue
        left, top, right, bottom = font.getbbox(ch)
        g = Image.new("L", (right - left + 8, bottom - top + 8))
        ImageDraw.Draw(g).text((4 - left, 4 - top), ch, font=font, fill=255)
        glyphs.append(((g, top), right - left))
    natural = sum(adv for _, adv in glyphs)
    gaps = max(1, len(glyphs) - 1)
    track = max(0.0, ((x1 - x0) - natural) / gaps)
    cover = Image.new("L", (w, h))
    baseline = y0 - cap[1] * 0 - 0
    pen = float(x0)
    cap_top = cap[1]
    for item, adv in glyphs:
        if item is not None:
            g, top = item
            cover.paste(g, (int(round(pen)) - 4, y0 + (top - cap_top) - 4), g)
        pen += adv + track
    if pen - track > x1 + 2 * S:   # too wide even untracked: squeeze to the old width
        cover = cover.crop((x0, 0, int(pen - track), h)).resize((x1 - x0, h), Image.LANCZOS)
        full = Image.new("L", (w, h)); full.paste(cover, (x0, 0)); cover = full
    if os.environ.get('HD_LABEL_DEBUG'):
        viz = np.dstack([letters * 255, strokes * 255, np.zeros_like(letters, dtype=np.uint8)]).astype(np.uint8)
        Image.fromarray(np.vstack([big, viz])).save(os.path.join(os.environ['HD_LABEL_DEBUG'], text.replace(' ', '_') + '.png'))
        print('label', text, 'box', x0, x1, y0, y1, 'scale', round(scale, 3), 'cover', cover.getbbox(), 'natural', natural, 'track', round(track, 1), 'glyphs', [a for _, a in glyphs])
    out = Image.fromarray(clean.round().astype(np.uint8))
    grow = cover.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    out.paste(Image.new("RGB", out.size, (10, 8, 12)), mask=grow.point(lambda v: int(v * 0.8)))
    fill = np.linspace(232, 180, h)[:, None, None] * np.ones((1, w, 3))
    out.paste(Image.fromarray(fill.astype(np.uint8)), mask=cover)
    return np.array(out)


def column_of(file):
    return int(file.split("-c")[1].split("-")[0])


def resolve(part, by_column, cuts):
    """The sheet file a part is cut from, and its rectangle in that sheet's pixels, or None."""
    dx, dy, u, v, w, h, cell, size = part
    if cell & 0x2000:
        return None   # mirrored: not handled
    page = (cell >> 10) & 7
    for column in (2 * page + u // 128, u // 128):
        x = u % 128
        for file in by_column.get(column, []):
            if (x, v, w, h) in cuts.get(file, []):
                return file, (x, v, w, h)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images", default="tmp/pc/images")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--bank", required=True, help="<MRG file>:<sector of the one-sector bank>")
    parser.add_argument("--cuts", action="append", required=True)
    parser.add_argument("--only", default="sheets/menu/a", help="the sheet family the bank's parts are cut from")
    parser.add_argument("--labels", help='JSON file {"<frame offset hex>": "WORD"}: grey button labels redrawn in --font')
    parser.add_argument("--font", default=r"C:\Windows\Fonts\timesi.ttf")
    parser.add_argument("--upscaler")
    parser.add_argument("--model", default="realesrgan-x4plus")
    args = parser.parse_args()
    labels = json.load(open(args.labels, encoding="utf-8")) if args.labels else {}
    path, sector = args.bank.rsplit(":", 1)
    with open(path, "rb") as handle:
        handle.seek(int(sector) * 2048)
        bank = handle.read(2048)
    with open(os.path.join(args.images, "manifest.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    entries = [e for e in (manifest if isinstance(manifest, list) else manifest["entries"]) if e["file"].startswith(args.only)]
    cuts = read_cuts(args.cuts, entries)
    by_column = {}
    for entry in entries:
        by_column.setdefault(column_of(entry["file"]), []).append(entry["file"])
    flat = lambda file: file.replace("/", "-")  # noqa: E731
    sheets = {}

    def sheet(file):
        if file not in sheets:
            sheets[file] = np.array(Image.open(os.path.join(args.images, file)).convert("RGBA"))
        return sheets[file]

    frames = []
    for offset, (count, flags, tpage, clut, parts) in sorted(sprite_bank.candidate_frames(bank).items()):
        if count < 2:
            continue
        found = [resolve(p, by_column, cuts) for p in parts]
        if all(found):
            frames.append((offset, parts, found))
    print(f"{len(frames)} frames of the bank assemble from {args.only}")
    upscaler, models = hs.find_upscaler(args.upscaler)
    total = {}
    with tempfile.TemporaryDirectory() as work:
        scaler = hs.hs_scaler = hs.Scaler(upscaler, models, args.model, 0.6, work)
        hs.SCALER = scaler
        jobs, canvases = [], []
        for offset, parts, found in frames:
            x0 = min(p[0] for p in parts)
            y0 = min(p[1] for p in parts)
            x1 = max(p[0] + p[4] for p in parts)
            y1 = max(p[1] + p[5] for p in parts)
            canvas = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
            for part, (file, (x, y, w, h)) in reversed(list(zip(parts, found))):   # the first part is on top
                piece = sheet(file)[y:y + h, x:x + w]
                at = canvas[part[1] - y0:part[1] - y0 + h, part[0] - x0:part[0] - x0 + w]
                solid = piece[..., 3] >= 128
                at[solid] = piece[solid]
            canvases.append((x0, y0, canvas))
            mask = canvas[..., 3] >= 128
            jobs.append((hs.fill_transparent(canvas[..., :3], mask), "symmetric"))
        for (offset, parts, found), (x0, y0, canvas), big in zip(frames, canvases, scaler.models_run(jobs)):
            mask = canvas[..., 3] >= 128
            rgb = hs.fill_transparent(canvas[..., :3], mask)
            big = hs.back_project(big, rgb, mask)
            plain = big
            if labels.get(f"{offset:04x}"):
                big = redraw_label(big, labels[f"{offset:04x}"], args.font)
            for index, (part, (file, (x, y, w, h))) in enumerate(zip(parts, found)):
                piece = sheet(file)[y:y + h, x:x + w]
                opaque = piece[..., 3] == 255
                # the last part is the frame, shared by every button: it never takes a label's letters
                source = plain if index == len(parts) - 1 else big
                region = source[(part[1] - y0) * S:(part[1] - y0 + h) * S, (part[0] - x0) * S:(part[0] - x0 + w) * S]
                acc, count = total.setdefault(file, (np.zeros((256 * S, 128 * S, 3)), np.zeros((256 * S, 128 * S))))
                keep = hs.blocks(opaque)
                acc[y * S:(y + h) * S, x * S:(x + w) * S][keep] += region[keep]
                count[y * S:(y + h) * S, x * S:(x + w) * S][keep] += 1
    changed = 0
    for file, (acc, count) in total.items():
        target = os.path.join(args.pack, "textures", flat(file))
        if not os.path.isfile(target):
            continue
        out = np.array(Image.open(target).convert("RGBA"))
        done = count > 0
        out[..., :3][done] = (acc[done] / count[done][:, None]).round().astype(np.uint8)
        Image.fromarray(out).save(target)
        changed += 1
    print(f"{changed} sheet images of {args.pack} redone from assembled frames")


if __name__ == "__main__":
    main()

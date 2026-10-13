"""Contact sheets that compare, per card, the candidates for the HD layer, so the user can choose.

    python tools/pc/kuriboh/compare_art.py <imported mod folder> <ai candidates folder> <net sources folder> <out folder> [--cell 204]

Columns: the mod's own picture, a plain enlargement (Lanczos + unsharp: what the layer used by default), the HD mod's own AI method
(ai_upscale.py "project"), the anime model alone, the real artwork fitted to the frame, and that artwork through the model. One PNG per six cards.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))


def fit(path: Path, size) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = 102 / 96
    if image.width / image.height > ratio:
        width = round(image.height * ratio)
        left = (image.width - width) // 2
        box = (left, 0, left + width, image.height)
    else:
        height = round(image.width / ratio)
        top = round((image.height - height) * 0.4)
        box = (0, top, image.width, top + height)
    return image.crop(box).resize(size, Image.LANCZOS)


def main():
    p = argparse.ArgumentParser()
    for name in ("mod", "ai", "net", "out"):
        p.add_argument(name)
    p.add_argument("--cell", type=int, default=204)
    a = p.parse_args()
    cw = a.cell
    ch = round(cw * 96 / 102)
    manifest = json.loads((Path(a.mod) / "textures" / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest if isinstance(manifest, list) else manifest["entries"]
    cards = sorted(int(re.search(r"card (\d+)", e["alias"]).group(1)) for e in entries if e["alias"].endswith(" art"))
    names = {}
    for e in entries:
        pass
    labels = ("mod art", "enlarged", "AI: HD mod method", "AI: anime model", "net art", "net art + AI")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for page in range(0, len(cards), 6):
        group = cards[page:page + 6]
        sheet = Image.new("RGB", (len(labels) * (cw + 6), len(group) * (ch + 18) + 18), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for c, label in enumerate(labels):
            d.text((c * (cw + 6) + 2, 2), label, fill=(120, 220, 255))
        for r, cid in enumerate(group):
            y = 18 + r * (ch + 18)
            d.text((2, y), str(cid), fill=(255, 255, 0))
            base = Image.open(Path(a.mod) / "textures" / f"cards/{cid:04d}.png").convert("RGB")
            small = base.resize((cw, ch), Image.NEAREST)
            enl = base.resize((base.width * 4, base.height * 4), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2)).resize((cw, ch), Image.LANCZOS)
            raw = Image.open(Path(a.ai) / "raw" / f"{cid}.png").convert("RGB").resize((cw, ch), Image.LANCZOS)
            mix = Image.open(Path(a.ai) / "project" / f"{cid}.png").convert("RGB").resize((cw, ch), Image.LANCZOS)
            net_ai_file = Path(a.ai) / "net_ai" / f"{cid}.png"
            net_ai = Image.open(net_ai_file).convert("RGB").resize((cw, ch), Image.LANCZOS) if net_ai_file.exists() else Image.new("RGB", (cw, ch), (60, 20, 20))
            net_file = next((Path(a.net) / f"{cid}{ext}" for ext in (".png", ".jpg", ".webp") if (Path(a.net) / f"{cid}{ext}").exists()), None)
            net = fit(net_file, (cw, ch)) if net_file else Image.new("RGB", (cw, ch), (60, 20, 20))
            for c, im in enumerate((small, enl, mix, raw, net, net_ai)):
                sheet.paste(im, (c * (cw + 6), y + 14))
        sheet.save(out / f"compare_{page // 6 + 1}.png")
        print(out / f"compare_{page // 6 + 1}.png")


main()

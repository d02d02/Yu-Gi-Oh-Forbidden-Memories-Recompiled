"""AI-upscale the Kuriboh mod's own card pictures (Real-ESRGAN, realesrgan-ncnn-vulkan) into candidates for the HD layer.

    python tools/pc/kuriboh/ai_upscale.py <imported mod folder> <out folder> [--model realesrgan-x4plus-anime]

Writes, for each card picture the mod changed (textures/manifest.json "card N art"):
    <out>/raw/<N>.png   the model's 4x output as it is
    <out>/project/<N>.png  the HD mod's own method (tools/pc/hd_screen_pack.py: model realesrgan-x4plus on the picture padded by a mirrored
                        border, 60 % model + 40 % Lanczos, six rounds of back-projection): what its Build Deck screen got
    <out>/mix/<N>.png   60 % model + 40 % Lanczos (the project's own mix for painted art, tools/pc/hd_screen_pack.py), then back-projected
                        so every 4x4 block averages to the mod's texel: the colors stay the mod's
Either folder can be used as `make_hd.py --sources`. Needs realesrgan-ncnn-vulkan (a Vulkan GPU): path in $REALESRGAN or
tmp/pc/tools/realesrgan/realesrgan-ncnn-vulkan.exe.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]


def model_up(exe: Path, source: Path, target: Path, model: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(exe), "-i", str(source.resolve()), "-o", str(target.resolve()), "-n", model, "-s", "4",
                    "-m", str(exe.parent / "models")], check=True, capture_output=True)


def back_project(big: np.ndarray, small: np.ndarray, scale: int) -> np.ndarray:
    """Adjust `big` so that each scale x scale block averages to the pixel of `small` it covers."""
    h, w = small.shape[:2]
    blocks = big.reshape(h, scale, w, scale, -1).mean(axis=(1, 3))
    delta = small - blocks
    return np.clip(big + np.repeat(np.repeat(delta, scale, axis=0), scale, axis=1), 0, 255)


def project_method(exe: Path, picture: Path, work: Path) -> np.ndarray:
    """hd_screen_pack.py's Scaler.models_run + back_project for one opaque picture, with its constants."""
    sys.path.insert(0, str(ROOT / "tools" / "pc"))
    import hd_screen_pack as hs
    rgb = np.asarray(Image.open(picture).convert("RGB"))
    padded = np.pad(rgb, ((hs.PAD, hs.PAD), (hs.PAD, hs.PAD), (0, 0)), mode="symmetric")
    source, big_path = work / "padded.png", work / "padded_4x.png"
    work.mkdir(parents=True, exist_ok=True)
    Image.fromarray(padded).save(source)
    model_up(exe, source, big_path, "realesrgan-x4plus")
    model = np.asarray(Image.open(big_path).convert("RGB"), dtype=np.float64)
    lanczos = np.asarray(Image.fromarray(padded).resize((padded.shape[1] * hs.S, padded.shape[0] * hs.S), Image.LANCZOS), dtype=np.float64)
    mixed = np.clip(model * 0.6 + lanczos * 0.4, 0, 255).round().astype(np.uint8)
    big = mixed[hs.PAD * hs.S:-hs.PAD * hs.S, hs.PAD * hs.S:-hs.PAD * hs.S]
    mask = np.ones(rgb.shape[:2], dtype=bool)
    return hs.back_project(big, rgb, mask)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("out")
    p.add_argument("--model", default="realesrgan-x4plus-anime")
    a = p.parse_args()
    exe = Path(os.environ.get("REALESRGAN") or ROOT / "tmp" / "pc" / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe")
    source, out = Path(a.source), Path(a.out)
    manifest = json.loads((source / "textures" / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest if isinstance(manifest, list) else manifest["entries"]
    for entry in entries:
        if not entry["alias"].endswith(" art"):
            continue
        cid = int(re.search(r"card (\d+)", entry["alias"]).group(1))
        picture = source / "textures" / entry["file"]
        raw = out / "raw" / f"{cid}.png"
        model_up(exe, picture, raw, a.model)
        small = np.asarray(Image.open(picture).convert("RGB"), dtype=float)
        model = np.asarray(Image.open(raw).convert("RGB"), dtype=float)
        lanczos = np.asarray(Image.open(picture).convert("RGB").resize((small.shape[1] * 4, small.shape[0] * 4), Image.LANCZOS), dtype=float)
        mixed = back_project(0.6 * model + 0.4 * lanczos, small, 4)
        (out / "mix").mkdir(parents=True, exist_ok=True)
        Image.fromarray(mixed.round().astype("uint8")).save(out / "mix" / f"{cid}.png")
        (out / "project").mkdir(parents=True, exist_ok=True)
        Image.fromarray(project_method(exe, picture, out / "work")).save(out / "project" / f"{cid}.png")
        print(cid, "ok")


main()

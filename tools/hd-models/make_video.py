#!/usr/bin/env python3
"""BMP frames (attack_clip.py) -> MP4 (H.264, Discord-friendly) + GIF.   make_video.py FRAMES_DIR OUT_PREFIX [--fps 30] [--width 960]
Crops the window's menu bar, orders by the frame number in the file name. Needs: pip install imageio-ffmpeg pillow."""
import argparse, re, subprocess
from pathlib import Path
from PIL import Image
import imageio_ffmpeg
ap = argparse.ArgumentParser(); ap.add_argument("frames"); ap.add_argument("out"); ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--width", type=int, default=960); ap.add_argument("--gif-width", type=int, default=480); ap.add_argument("--gif-step", type=int, default=2)
a = ap.parse_args()
files = sorted(Path(a.frames, "bmp").glob("*.bmp"), key=lambda p: int(re.search(r"-(\d+)\.bmp$", p.name).group(1)))
def load(p, w):
    im = Image.open(p).convert("RGB"); im = im.crop((0, 26, im.width, im.height))
    h = int(w * im.height / im.width) // 2 * 2; return im.resize((w, h), Image.LANCZOS)
first = load(files[0], a.width); W, H = first.size
ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(a.fps),
                       "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow", f"{a.out}.mp4"], stdin=subprocess.PIPE)
for p in files: ff.stdin.write(load(p, a.width).tobytes())
ff.stdin.close(); ff.wait()
g = [load(p, a.gif_width) for p in files[::a.gif_step]]
g[0].save(f"{a.out}.gif", save_all=True, append_images=g[1:], duration=int(1000 * a.gif_step / a.fps), loop=0, optimize=True)
for ext in ("mp4", "gif"): print(ext, round(Path(f"{a.out}.{ext}").stat().st_size / 1e6, 2), "MB")
print(len(files), "frames,", round(len(files) / a.fps, 1), "s")

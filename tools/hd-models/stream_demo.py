#!/usr/bin/env python3
"""Stream frames from the game over the control channel (Route B, E7), phase 1.

    python stream_demo.py --selftest          # fake game, no disc, no display
    python stream_demo.py                     # real game (needs MEMORIES_DISC)

The selftest checks the PNG maker and prints the stream stats. The real mode
streams for 3 s into tmp/pc/stream/ as numbered PNGs and prints the stats."""
import argparse
import struct
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from studio.stream import FrameStream  # noqa: E402

ROOT = HERE.parents[1]
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def tiny_png(rgb=(255, 0, 0)):
    """A valid 1x1 RGB PNG, stdlib only."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00" + bytes(rgb)
    return PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class FakeGame:
    """Hash changes every 3rd poll; shot writes a tiny valid PNG."""

    def __init__(self):
        self.polls = 0
        self.shots = 0
        self.png = tiny_png()

    def hash(self):
        self.polls += 1
        return self.polls // 3

    def shot(self, path):
        self.shots += 1
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.png)
        return path


def show_stats(stats):
    print("frames %d polls %d skipped %d mean_ms %.2f fps %.2f" % (
        stats["frames"], stats["polls"], stats["skipped"],
        stats["mean_ms"], stats["fps"]))


def selftest():
    assert tiny_png().startswith(PNG_SIG)
    game = FakeGame()
    fs = FrameStream(game, fps=100.0, max_frames=10)
    got = list(fs.frames())
    assert [f.seq for f in got] == list(range(10)), [f.seq for f in got]
    assert all(f.png_bytes.startswith(PNG_SIG) for f in got)
    assert fs.latest() is got[-1]
    stats = fs.stats()
    assert stats["frames"] == 10 and stats["polls"] >= 10
    print("selftest ok:", end=" ")
    show_stats(stats)
    return 0


def real():
    import os

    if not os.environ.get("MEMORIES_DISC"):
        sys.exit("MEMORIES_DISC is not set: point it at the disc image")
    sys.path.insert(0, str(HERE))
    from _paths import DEV, EXE
    sys.path.insert(0, str(DEV))
    import yfm_control as yc

    out = ROOT / "tmp" / "pc" / "stream"
    out.mkdir(parents=True, exist_ok=True)
    with yc.Game(executable=EXE, out=out / "run", settings={"internal_scale": 1},
                 env={"MEMORIES_FPS": "-1"}, headless=False) as game:
        fs = FrameStream(game, fps=10.0, out_dir=out / "work")
        start = time.monotonic()
        saved = 0
        for frame in fs.frames():
            (out / f"f{frame.seq:04d}.png").write_bytes(frame.png_bytes)
            saved += 1
            if time.monotonic() - start >= 3.0:
                break
        fs.close()
        print("saved", saved, "png to", out)
        show_stats(fs.stats())
        if fs.error:
            print("error:", fs.error)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="fake game, no disc")
    a = ap.parse_args()
    return selftest() if a.selftest else real()


if __name__ == "__main__":
    sys.exit(main())

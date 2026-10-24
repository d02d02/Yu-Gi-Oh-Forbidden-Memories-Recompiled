"""Frame stream over the control channel (Route B, E7), phase 1."""
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from yfm_control import ControlError
except ImportError:  # tools/pc not on sys.path (tests, fake games)
    class ControlError(RuntimeError):
        pass


@dataclass
class Frame:
    seq: int
    hash: int
    png_bytes: bytes
    t: float


class FrameStream:
    def __init__(self, game, fps=10.0, max_frames=None, out_dir=None,
                 clock=None, sleep=None):
        self.game = game
        self.fps = fps
        self.max_frames = max_frames
        self.out_dir = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="e7-stream-"))
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.error = None
        self._latest = None
        self._closed = False
        self._frames = 0
        self._polls = 0
        self._skipped = 0
        self._shot_s = 0.0
        self._start = None
        self._end = None

    def close(self):
        self._closed = True

    def latest(self):
        return self._latest

    def stats(self):
        elapsed = 0.0
        if self._start is not None:
            elapsed = (self._end if self._end is not None else self.clock()) - self._start
        return {
            "frames": self._frames,
            "polls": self._polls,
            "skipped": self._skipped,
            "mean_ms": (self._shot_s / self._frames * 1000.0) if self._frames else 0.0,
            "fps": (self._frames / elapsed) if elapsed > 0 else 0.0,
        }

    def frames(self):
        seq = 0
        last_hash = None
        interval = 1.0 / self.fps if self.fps > 0 else 0.0
        self._start = self.clock()
        try:
            while not self._closed and (self.max_frames is None or seq < self.max_frames):
                if self._polls:
                    self.sleep(interval)
                    if self._closed:
                        return
                self._polls += 1
                try:
                    h = self.game.hash()
                    if h == last_hash:
                        self._skipped += 1
                        continue
                    path = self.out_dir / f"f{seq}.png"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    t0 = self.clock()
                    self.game.shot(path)
                    self._shot_s += self.clock() - t0
                    png = path.read_bytes()
                    path.unlink()
                    frame = Frame(seq, h, png, self.clock())
                    last_hash = h
                    self._latest = frame
                    self._frames += 1
                    yield frame
                    seq += 1
                except ControlError as exc:
                    self.error = exc
                    return
        finally:
            self._end = self.clock()

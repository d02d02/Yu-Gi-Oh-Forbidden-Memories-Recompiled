"""Frame stream over the control channel, fake game only (no disc)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import stream


class FakeGame:
    def __init__(self, hashes):
        self.hashes = list(hashes)
        self.polls = 0
        self.shots = []

    def hash(self):
        h = self.hashes[min(self.polls, len(self.hashes) - 1)]
        self.polls += 1
        return h

    def shot(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png:" + str(self.polls).encode())
        self.shots.append(path)
        return path


class TestFrames(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_poll_always_yields(self):
        game = FakeGame([7, 7])
        fs = stream.FrameStream(game, fps=1000, max_frames=1, out_dir=self.out)
        frames = list(fs.frames())
        self.assertEqual([(f.seq, f.hash) for f in frames], [(0, 7)])
        self.assertEqual(game.polls, 1)

    def test_yields_only_changed_frames(self):
        game = FakeGame([5, 5, 6, 6, 7])
        fs = stream.FrameStream(game, fps=1000, max_frames=3, out_dir=self.out)
        frames = list(fs.frames())
        self.assertEqual([f.seq for f in frames], [0, 1, 2])
        self.assertEqual([f.hash for f in frames], [5, 6, 7])
        self.assertEqual(game.polls, 5)

    def test_max_frames_stops(self):
        game = FakeGame([1, 2, 3, 4])
        fs = stream.FrameStream(game, fps=1000, max_frames=2, out_dir=self.out)
        frames = list(fs.frames())
        self.assertEqual(len(frames), 2)
        self.assertEqual(game.polls, 2)

    def test_injected_sleep_caps_rate(self):
        game = FakeGame([1, 2])
        sleeps = []
        fs = stream.FrameStream(game, fps=2, max_frames=2, out_dir=self.out,
                                clock=lambda: 0.0, sleep=sleeps.append)
        list(fs.frames())
        self.assertEqual(sleeps, [0.5])

    def test_close_stops_the_stream(self):
        game = FakeGame([1, 2, 3])
        fs = stream.FrameStream(game, fps=1000, out_dir=self.out, sleep=lambda _: None)
        gen = fs.frames()
        first = next(gen)
        self.assertEqual(first.seq, 0)
        fs.close()
        self.assertEqual(list(gen), [])
        self.assertEqual(game.polls, 1)

    def test_control_error_ends_stream_and_is_stored(self):
        class BrokenGame(FakeGame):
            def hash(self):
                self.polls += 1
                if self.polls == 1:
                    return 1
                raise stream.ControlError("lost the game")

        game = BrokenGame([1])
        fs = stream.FrameStream(game, fps=1000, out_dir=self.out, sleep=lambda _: None)
        frames = list(fs.frames())
        self.assertEqual([f.seq for f in frames], [0])
        self.assertIsInstance(fs.error, stream.ControlError)
        self.assertEqual(str(fs.error), "lost the game")
        self.assertEqual(game.polls, 2)

    def test_png_bytes_read_and_file_deleted(self):
        game = FakeGame([1, 2])
        fs = stream.FrameStream(game, fps=1000, max_frames=2, out_dir=self.out)
        frames = list(fs.frames())
        self.assertEqual(frames[0].png_bytes, b"png:1")
        self.assertEqual(frames[1].png_bytes, b"png:2")
        self.assertEqual(list(self.out.glob("f*.png")), [])


if __name__ == "__main__":
    unittest.main()

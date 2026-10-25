import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio import transport  # noqa: E402


class FakeGame:
    def __init__(self, draw_after=3):
        self.calls, self.at, self.al, self.steps, self.draw_after = [], 0.0, 0, 0, draw_after

    def load(self, state): self.calls.append(("load", state))
    def anim_resume(self): self.calls.append(("resume",))
    def anim_pause(self): self.calls.append(("pause",))
    def anim_phase(self, p): self.calls.append(("phase", p)); self.at = p

    def step(self, n):
        self.steps += n
        if self.steps >= self.draw_after:
            self.al = 1

    def anim_get(self): return {"al": self.al, "at": self.at}

    def shot(self, path): Path(path).write_bytes(b"png")


class TransportTest(unittest.TestCase):
    def test_start_pauses_once_the_scene_draws(self):
        game = FakeGame()
        t = transport.Transport(game, "s.state")
        self.assertTrue(t.start())
        self.assertTrue(t.paused and t.ready)
        self.assertEqual(game.calls[0], ("load", "s.state"))
        self.assertIn(("pause",), game.calls)

    def test_start_fails_if_the_scene_never_draws(self):
        t = transport.Transport(FakeGame(draw_after=10**6), "s", max_steps=5)
        self.assertFalse(t.start())
        self.assertFalse(t.ready)

    def test_scrub_clamps_and_reports(self):
        t = transport.Transport(FakeGame(), "s")
        t.start()
        self.assertEqual(t.scrub(0.5), 0.5)
        self.assertEqual(t.scrub(7), 1.0)
        self.assertEqual(t.scrub(-1), 0.0)

    def test_scrub_before_start_raises(self):
        with self.assertRaises(RuntimeError):
            transport.Transport(FakeGame(), "s").scrub(0.5)

    def test_play_then_scrub_pauses_again(self):
        t = transport.Transport(FakeGame(), "s")
        t.start()
        t.play()
        self.assertFalse(t.paused)
        t.scrub(0.25)
        self.assertTrue(t.paused)

    def test_shot_writes_file(self):
        t = transport.Transport(FakeGame(), "s")
        t.start()
        with tempfile.TemporaryDirectory() as d:
            self.assertTrue(t.shot(Path(d) / "a" / "p.png").is_file())


if __name__ == "__main__":
    unittest.main()

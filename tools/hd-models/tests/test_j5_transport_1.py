import unittest
from pathlib import Path

import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('transport', str(Path(__file__).parents[1] / 'studio' / 'transport.py'))
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
Transport = transport.Transport

class FakeGame:
    def __init__(self):
        self.loaded = False
        self.step_calls = 0
        self.al = 0
        self.at = 0.0
        self.shot_paths = []
    def load(self, state):
        self.loaded = True
    def anim_resume(self):
        pass
    def anim_pause(self):
        pass
    def step(self, n):
        self.step_calls += n
        # after first step, simulate attack layer ready
        if self.step_calls == 1:
            self.al = 1
            self.at = 0.5
    def anim_get(self):
        return {"al": self.al, "at": self.at}
    def anim_phase(self, phase):
        self.at = phase
    def shot(self, path):
        self.shot_paths.append(Path(path))

class TestTransportEdgeCases(unittest.TestCase):
    def test_double_start(self):
        game = FakeGame()
        t = Transport(game, "state", max_steps=10)
        self.assertTrue(t.start())
        # second start should still work and return True
        self.assertTrue(t.start())

    def test_play_pause_scrub_order(self):
        game = FakeGame()
        t = Transport(game, "state", max_steps=10)
        with self.assertRaises(RuntimeError):
            t.play()
        with self.assertRaises(RuntimeError):
            t.scrub(0.3)
        t.start()
        t.play()
        self.assertFalse(t.paused)
        t.pause()
        self.assertTrue(t.paused)
        phase = t.scrub(0.8)
        self.assertTrue(0.0 <= phase <= 1.0)

    def test_current_none_cases(self):
        class BadGame(FakeGame):
            def anim_get(self):
                return {"at": "not-a-number"}
        game = BadGame()
        t = Transport(game, "state", max_steps=10)
        t.start()
        self.assertIsNone(t.current())
        class MissingAt(FakeGame):
            def anim_get(self):
                return {}
        game2 = MissingAt()
        t2 = Transport(game2, "state", max_steps=10)
        t2.start()
        self.assertEqual(t2.current(), 0.0)

    def test_shot_path_creation(self):
        game = FakeGame()
        t = Transport(game, "state", max_steps=10)
        t.start()
        out = t.shot(Path("tmp/output/shot.png"))
        self.assertTrue(out.parent.exists())
        self.assertIn(out, game.shot_paths)

    def test_max_steps_zero(self):
        game = FakeGame()
        t = Transport(game, "state", max_steps=0)
        self.assertFalse(t.start())

    def test_state_path(self):
        game = FakeGame()
        t = Transport(game, Path("statefile"), max_steps=10)
        self.assertTrue(t.start())

if __name__ == "__main__":
    unittest.main()

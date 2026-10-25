import unittest, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import procedural

class TestIdleInKinds(unittest.TestCase):
    def test_idle_in_kinds(self):
        self.assertIn('idle', procedural.KINDS)

class TestIdleSample(unittest.TestCase):
    def test_sample_idle_valid(self):
        frames = 5
        height = 2.0
        track = procedural.sample('idle', frames, height)
        # should have correct length
        self.assertEqual(len(track), frames)
        # check_track should return empty list (valid track)
        self.assertEqual(procedural.check_track(track, frames), [])

if __name__ == '__main__':
    unittest.main()

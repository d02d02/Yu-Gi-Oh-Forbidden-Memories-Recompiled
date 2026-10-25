import unittest, math, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import procedural

class TestIdle(unittest.TestCase):
    def test_shape(self):
        frames = 5
        height = 2.0
        track = procedural.idle(frames, height)
        self.assertEqual(len(track), frames)
        for f in track:
            self.assertIn('pos', f)
            self.assertIn('rot', f)
            self.assertIn('scale', f)

    def test_loop_equality(self):
        frames = 4
        track = procedural.idle(frames, 1.0)
        self.assertAlmostEqual(track[0]['pos'][1], track[-1]['pos'][1], delta=1e-9)
        self.assertEqual(track[0]['rot'], track[-1]['rot'])
        self.assertEqual(track[0]['scale'], track[-1]['scale'])

    def test_errors(self):
        with self.assertRaises(ValueError):
            procedural.idle(1, 1.0)
        with self.assertRaises(ValueError):
            procedural.idle(2, 1.0, cycles=0)

    def test_check_track_clean(self):
        frames = 6
        track = procedural.idle(frames, 1.0)
        self.assertEqual(procedural.check_track(track, frames), [])

    def test_values(self):
        frames = 3
        height = 1.0
        bob = 0.01
        sway = 0.02
        cycles = 1
        track = procedural.idle(frames, height, bob=bob, sway=sway, cycles=cycles)
        middle = track[1]
        expected_y = bob * height * math.sin(2 * math.pi * cycles * 0.5)  # sin(pi)=0
        self.assertAlmostEqual(middle['pos'][1], expected_y, places=7)
        # rotation should not be identity for middle frame
        self.assertNotEqual(middle['rot'], (0.0, 0.0, 0.0, 1.0))

if __name__ == '__main__':
    unittest.main()

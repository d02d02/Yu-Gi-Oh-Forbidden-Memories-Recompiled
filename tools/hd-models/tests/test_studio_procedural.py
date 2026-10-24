"""Tests for studio.procedural."""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import procedural


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class TestEase(unittest.TestCase):
    def test_linear_endpoints_and_clamp(self):
        self.assertEqual(procedural.ease(0.0, "linear"), 0.0)
        self.assertEqual(procedural.ease(1.0, "linear"), 1.0)
        self.assertAlmostEqual(procedural.ease(0.5, "linear"), 0.5)
        # t is clamped to [0, 1]
        self.assertEqual(procedural.ease(-0.2, "linear"), 0.0)
        self.assertEqual(procedural.ease(1.5, "linear"), 1.0)

    def test_in_out_inout(self):
        self.assertAlmostEqual(procedural.ease(0.5, "in"), 0.25)
        self.assertAlmostEqual(procedural.ease(0.5, "out"), 0.75)
        self.assertAlmostEqual(procedural.ease(0.0, "inout"), 0.0)
        self.assertAlmostEqual(procedural.ease(1.0, "inout"), 1.0)
        self.assertAlmostEqual(procedural.ease(0.5, "inout"), 0.5)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            procedural.ease(0.5, "bogus")

    def test_identity(self):
        self.assertEqual(procedural.IDENTITY, (0.0, 0.0, 0.0, 1.0))

    def test_quat_axis_angle_zero_axis_raises(self):
        with self.assertRaises(ValueError):
            procedural.quat_axis_angle((0.0, 0.0, 0.0), 0.5)

    def test_quat_axis_angle_unit_and_zero_angle(self):
        q = procedural.quat_axis_angle((0.0, 1.0, 0.0), 0.0)
        self.assertAlmostEqual(_dot(q, q), 1.0)
        self.assertEqual(q, (0.0, 0.0, 0.0, 1.0))

    def test_quat_mul_identity(self):
        a = (1.0, 2.0, 3.0, 4.0)
        self.assertEqual(procedural.quat_mul(a, procedural.IDENTITY), a)

    def test_quat_rotate_roundtrip(self):
        # rotate (1,0,0) by +90deg about +y -> (0,0,-1) for Hamilton, right-hand rule
        q = procedural.quat_axis_angle((0.0, 1.0, 0.0), math.pi / 2.0)
        r = procedural.quat_rotate(q, (1.0, 0.0, 0.0))
        self.assertAlmostEqual(_dot(r, r), 1.0, places=6)
        self.assertAlmostEqual(r[2], -1.0, places=6)

    def test_tip_moves_top_away_from_forward(self):
        # forward=(0,1) faces +z in 3D = (0,0,1); tipping back should push
        # the head point (0,1,0) onto the opposite side of forward.
        forward = (0.0, 1.0)
        fwd3 = (forward[0], 0.0, forward[1])
        top = procedural.quat_rotate(procedural.tip(forward, 0.3), (0.0, 1.0, 0.0))
        self.assertLess(_dot(top, fwd3), 0.0)

    def test_tip_zero_angle_is_identity(self):
        self.assertEqual(procedural.tip((0.0, 1.0), 0.0), procedural.IDENTITY)


class TestRecoil(unittest.TestCase):
    def test_length_and_endpoints_identity(self):
        track = procedural.recoil(11, 1.8)
        self.assertEqual(len(track), 11)
        for frame in (track[0], track[-1]):
            self.assertEqual(frame["pos"], (0.0, 0.0, 0.0))
            self.assertEqual(frame["rot"], procedural.IDENTITY)
            self.assertEqual(frame["scale"], 1.0)

    def test_peak_at_30_percent(self):
        frames, height, strength = 11, 2.0, 0.08
        track = procedural.recoil(frames, height, strength=strength)
        i = round(0.3 * (frames - 1))
        self.assertAlmostEqual(track[i]["pos"][2], -strength * height, places=9)
        q = track[i]["rot"]
        self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
        top = procedural.quat_rotate(q, (0.0, 1.0, 0.0))
        self.assertLess(_dot(top, (0.0, 0.0, 1.0)), 0.0)

    def test_all_frames_wellformed(self):
        track = procedural.recoil(20, 1.7)
        for f in track:
            q = f["rot"]
            self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
            self.assertGreater(f["scale"], 0.0)
            for v in f["pos"] + f["rot"] + (f["scale"],):
                self.assertTrue(math.isfinite(v))


class TestCollapse(unittest.TestCase):
    def test_length_and_first_frame_identity(self):
        track = procedural.collapse(11, 1.8)
        self.assertEqual(len(track), 11)
        frame = track[0]
        self.assertEqual(frame["pos"], (0.0, 0.0, 0.0))
        self.assertEqual(frame["rot"], procedural.IDENTITY)
        self.assertEqual(frame["scale"], 1.0)

    def test_final_frame_sinks_and_pose_held(self):
        frames, height, sink = 11, 2.0, 0.35
        track = procedural.collapse(frames, height, sink=sink)
        # final frame y == -sink * height
        self.assertAlmostEqual(track[-1]["pos"][1], -sink * height, places=9)
        # final pose held from 60% (peak) to the end
        peak_i = round(0.6 * (frames - 1))
        for i in range(peak_i, frames):
            self.assertEqual(track[i]["pos"], track[peak_i]["pos"])
            self.assertEqual(track[i]["rot"], track[peak_i]["rot"])

    def test_all_frames_wellformed(self):
        track = procedural.collapse(20, 1.7)
        for f in track:
            q = f["rot"]
            self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
            self.assertGreater(f["scale"], 0.0)
            for v in f["pos"] + f["rot"] + (f["scale"],):
                self.assertTrue(math.isfinite(v))


class TestBrace(unittest.TestCase):
    def test_length_and_endpoints_identity(self):
        track = procedural.brace(11, 1.8)
        self.assertEqual(len(track), 11)
        for frame in (track[0], track[-1]):
            self.assertEqual(frame["pos"], (0.0, 0.0, 0.0))
            self.assertEqual(frame["rot"], procedural.IDENTITY)
            self.assertEqual(frame["scale"], 1.0)

    def test_crouch_and_lean_forward_reach_by_40_percent(self):
        frames, height, crouch = 11, 2.0, 0.12
        track = procedural.brace(frames, height, crouch=crouch)
        i = round(0.4 * (frames - 1))
        # crouch peak: pos y == -crouch * height
        self.assertAlmostEqual(track[i]["pos"][1], -crouch * height, places=9)
        # lean forward == negative tip: rotating top (0,1,0) gives a vector
        # whose dot with forward (0,0,1) is positive (top moved forward).
        q = track[i]["rot"]
        self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
        top = procedural.quat_rotate(q, (0.0, 1.0, 0.0))
        self.assertGreater(_dot(top, (0.0, 0.0, 1.0)), 0.0)

    def test_pose_held_until_80_percent(self):
        frames, height = 11, 1.7
        track = procedural.brace(frames, height)
        peak_i = round(0.4 * (frames - 1))
        i_hold = round(0.8 * (frames - 1))
        # from the 40% peak to 80%, the pose is constant
        for i in range(peak_i, i_hold + 1):
            self.assertEqual(track[i]["pos"], track[peak_i]["pos"])
            self.assertEqual(track[i]["rot"], track[peak_i]["rot"])

    def test_all_frames_wellformed(self):
        track = procedural.brace(20, 1.7)
        for f in track:
            q = f["rot"]
            self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
            self.assertGreater(f["scale"], 0.0)
            for v in f["pos"] + f["rot"] + (f["scale"],):
                self.assertTrue(math.isfinite(v))


class TestLunge(unittest.TestCase):
    def test_length_and_endpoints_identity(self):
        track = procedural.lunge(11, 1.8, 6)
        self.assertEqual(len(track), 11)
        for frame in (track[0], track[-1]):
            self.assertEqual(frame["pos"], (0.0, 0.0, 0.0))
            self.assertEqual(frame["rot"], procedural.IDENTITY)
            self.assertEqual(frame["scale"], 1.0)

    def test_strike_frame_pos_along_forward(self):
        frames, height, reach = 11, 2.0, 0.3
        strike_frame = 6
        track = procedural.lunge(frames, height, strike_frame, reach=reach)
        fwd3 = (0.0, 0.0, 1.0)  # forward=(0,1) -> +z
        pos = track[strike_frame]["pos"]
        self.assertAlmostEqual(_dot(pos, fwd3), reach * height, places=6)
        q = track[strike_frame]["rot"]
        self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
        top = procedural.quat_rotate(q, (0.0, 1.0, 0.0))
        self.assertGreater(_dot(top, fwd3), 0.0)

    def test_anticipation_moves_back(self):
        frames, height = 11, 2.0
        strike_frame = 6
        track = procedural.lunge(frames, height, strike_frame)
        mid = round(strike_frame * 0.5)
        pos = track[mid]["pos"]
        self.assertLess(_dot(pos, (0.0, 0.0, 1.0)), 0.0)
        self.assertAlmostEqual(pos[1], 0.0, places=9)

    def test_invalid_strike_frame(self):
        for bad in (0, 10, 11):
            with self.assertRaises(ValueError):
                procedural.lunge(11, 1.8, bad)

    def test_all_frames_wellformed(self):
        track = procedural.lunge(20, 1.7, 10)
        for f in track:
            q = f["rot"]
            self.assertAlmostEqual(_dot(q, q), 1.0, places=9)
            self.assertGreater(f["scale"], 0.0)
            for v in f["pos"] + f["rot"] + (f["scale"],):
                self.assertTrue(math.isfinite(v))


class TestSampleAndCheck(unittest.TestCase):
    def test_rise_shape_and_endpoints(self):
        frames, height, bob = 11, 2.0, 0.05
        track = procedural.rise(frames, height, bob=bob)
        self.assertEqual(len(track), frames)
        for frame in (track[0], track[-1]):
            self.assertEqual(frame["pos"], (0.0, 0.0, 0.0))
            self.assertEqual(frame["rot"], procedural.IDENTITY)
            self.assertEqual(frame["scale"], 1.0)
        mid = round(0.5 * (frames - 1))
        self.assertAlmostEqual(track[mid]["pos"][1], bob * height, places=9)
        self.assertAlmostEqual(track[mid]["scale"], 1.0 + 0.02, places=9)

    def test_sample_dispatches_every_kind(self):
        for kind in procedural.KINDS:
            kw = {"lunge": {"strike_frame": 6}}.get(kind, {})
            track = procedural.sample(kind, 11, 1.8, **kw)
            self.assertEqual(len(track), 11)
            self.assertEqual(procedural.check_track(track, 11), [])

    def test_sample_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            procedural.sample("nope", 11, 1.8)

    def test_check_track_empty_for_valid_track(self):
        track = procedural.rise(11, 1.8)
        self.assertEqual(procedural.check_track(track, 11), [])

    def test_check_track_detects_length(self):
        track = procedural.rise(11, 1.8)[:-1]
        problems = procedural.check_track(track, 11)
        self.assertTrue(any("length" in p for p in problems))

    def test_check_track_detects_nonfinite(self):
        track = procedural.rise(11, 1.8)
        track = list(track)
        bad = dict(track[5])
        bad["pos"] = (0.0, float("inf"), 0.0)
        track[5] = bad
        problems = procedural.check_track(track, 11)
        self.assertTrue(any("finite" in p for p in problems))

    def test_check_track_detects_non_unit_rot(self):
        track = procedural.rise(11, 1.8)
        track = list(track)
        bad = dict(track[5])
        bad["rot"] = (2.0, 0.0, 0.0, 0.0)
        track[5] = bad
        problems = procedural.check_track(track, 11)
        self.assertTrue(any("unit" in p for p in problems))

    def test_check_track_detects_scale(self):
        track = procedural.rise(11, 1.8)
        track = list(track)
        bad = dict(track[5])
        bad["scale"] = 0.0
        track[5] = bad
        problems = procedural.check_track(track, 11)
        self.assertTrue(any("scale" in p for p in problems))


if __name__ == "__main__":
    unittest.main()

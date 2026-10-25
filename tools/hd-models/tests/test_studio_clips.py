"""Tests for studio/clips.py (S5 animation clip statistics and checks)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import audit, clips


class TestLoopGap(unittest.TestCase):
    def test_empty_and_single_frame(self):
        self.assertEqual(clips.loop_gap([]), 0.0)
        self.assertEqual(clips.loop_gap([[(0.0, 0.0, 0.0)]]), 0.0)

    def test_identical_frames(self):
        P = [[(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)],
             [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)]]
        self.assertEqual(clips.loop_gap(P), 0.0)

    def test_largest_joint_move(self):
        P = [[(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
             [(0.0, 0.0, 0.0), (3.0, 4.0, 0.0)]]
        self.assertAlmostEqual(clips.loop_gap(P), 5.0)

    def test_ignores_intermediate_motion(self):
        P = [[(0.0, 0.0, 0.0)],
             [(100.0, 0.0, 0.0)],
             [(0.0, 0.0, 0.0)]]
        self.assertAlmostEqual(clips.loop_gap(P), 0.0)


class TestRootDrift(unittest.TestCase):
    def test_empty_and_single_frame(self):
        self.assertEqual(clips.root_drift([]),
                         {"distance": 0.0, "axis": (0.0, 0.0, 0.0)})
        self.assertEqual(clips.root_drift([[(0.0, 0.0, 0.0)]]),
                         {"distance": 0.0, "axis": (0.0, 0.0, 0.0)})

    def test_drift_vector_and_magnitude(self):
        P = [[(0.0, 0.0, 0.0)],
             [(3.0, 4.0, 0.0)]]
        self.assertEqual(clips.root_drift(P),
                         {"distance": 5.0, "axis": (3.0, 4.0, 0.0)})

    def test_uses_first_and_last_frame_only(self):
        P = [[(0.0, 0.0, 0.0)],
             [(100.0, 0.0, 0.0)],
             [(6.0, 8.0, 0.0)]]
        self.assertEqual(clips.root_drift(P),
                         {"distance": 10.0, "axis": (6.0, 8.0, 0.0)})


class TestSpeedPeak(unittest.TestCase):
    def test_fewer_than_two_frames(self):
        self.assertEqual(clips.speed_peak([], 30.0),
                         {"speed": 0.0, "joint": 0, "frame": 0})
        self.assertEqual(clips.speed_peak([[(0.0, 0.0, 0.0)]], 30.0),
                         {"speed": 0.0, "joint": 0, "frame": 0})

    def test_no_motion(self):
        P = [[(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)],
             [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)]]
        self.assertEqual(clips.speed_peak(P, 24.0),
                         {"speed": 0.0, "joint": 0, "frame": 0})

    def test_fastest_step(self):
        P = [[(0.0, 0.0, 0.0)], [(0.0, 0.0, 0.0)], [(3.0, 4.0, 0.0)]]
        self.assertEqual(clips.speed_peak(P, 2.0),
                         {"speed": 10.0, "joint": 0, "frame": 2})

    def test_returns_later_frame_and_correct_speed(self):
        P = [[(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
             [(1.0, 0.0, 0.0), (2.0, 2.0, 0.0)]]
        res = clips.speed_peak(P, 3.0)
        self.assertAlmostEqual(res["speed"], (8 ** 0.5) * 3.0)
        self.assertEqual(res["joint"], 1)
        self.assertEqual(res["frame"], 1)


class TestBoneStretch(unittest.TestCase):
    def test_empty_or_root_only(self):
        self.assertEqual(clips.bone_stretch([], [-1]),
                         {"ratio_min": 1.0, "ratio_max": 1.0, "joint": 0})
        P = [[(0.0, 0.0, 0.0)], [(1.0, 0.0, 0.0)]]
        self.assertEqual(clips.bone_stretch(P, [-1]),
                         {"ratio_min": 1.0, "ratio_max": 1.0, "joint": 0})

    def test_consistent_lengths(self):
        P = [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
             [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]]
        parents = [-1, 0]
        res = clips.bone_stretch(P, parents)
        self.assertAlmostEqual(res["ratio_min"], 1.0)
        self.assertAlmostEqual(res["ratio_max"], 1.0)
        self.assertEqual(res["joint"], 1)

    def test_stretch_detected(self):
        P = [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
             [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (1.5, 0.0, 0.0)]]
        parents = [-1, 0, 1]
        res = clips.bone_stretch(P, parents)
        self.assertAlmostEqual(res["ratio_max"], 2.0)
        self.assertAlmostEqual(res["ratio_min"], 0.5)
        self.assertEqual(res["joint"], 1)

    def test_skips_zero_length_bone(self):
        P = [[(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
             [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 2.0, 0.0)]]
        parents = [-1, 0, 1]
        res = clips.bone_stretch(P, parents)
        self.assertAlmostEqual(res["ratio_min"], 1.0)
        self.assertAlmostEqual(res["ratio_max"], 2.0)
        self.assertEqual(res["joint"], 2)


class TestBbox(unittest.TestCase):
    def test_empty_clip(self):
        self.assertEqual(clips.clip_bbox([]),
                         {"lo": (0.0, 0.0, 0.0), "hi": (0.0, 0.0, 0.0)})

    def test_single_position(self):
        P = [[(1.0, -2.0, 3.0)]]
        self.assertEqual(clips.clip_bbox(P),
                         {"lo": (1.0, -2.0, 3.0), "hi": (1.0, -2.0, 3.0)})

    def test_bbox_over_frames_and_joints(self):
        P = [[(0.0, 0.0, 0.0), (5.0, -1.0, 2.0)],
             [(-2.0, 4.0, 6.0), (3.0, 3.0, 0.0)]]
        res = clips.clip_bbox(P)
        self.assertEqual(res, {"lo": (-2.0, -1.0, 0.0), "hi": (5.0, 4.0, 6.0)})

    def test_uses_all_axes(self):
        P = [[(10.0, 0.0, 0.0)], [(-10.0, 0.0, 0.0)]]
        res = clips.clip_bbox(P)
        self.assertEqual(res["lo"], (-10.0, 0.0, 0.0))
        self.assertEqual(res["hi"], (10.0, 0.0, 0.0))


class TestChecks(unittest.TestCase):
    def setUp(self):
        self.clean_clip = {
            "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                         [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]],
            "fps": 30.0,
            "loop": True,
        }
        self.parents = [-1, 0]

    def test_check_loop_clean(self):
        findings = clips.check_loop("clean", self.clean_clip)
        self.assertEqual(findings, [])

    def test_check_loop_warn(self):
        clip = {"positions": [[(0.0, 0.0, 0.0)], [(25.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        findings = clips.check_loop("test", clip)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S5.loop-gap")
        self.assertEqual(f["level"], "warn")
        self.assertIn("25 units", f["message"])
        self.assertEqual(f["fix"], "Close the loop or turn Loop off.")
        self.assertAlmostEqual(f["value"], 25.0)

    def test_check_loop_ignored_when_not_looping(self):
        clip = {"positions": [[(0.0, 0.0, 0.0)], [(25.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": False}
        findings = clips.check_loop("test", clip)
        self.assertEqual(findings, [])

    def test_check_drift_clean(self):
        findings = clips.check_drift("clean", self.clean_clip)
        self.assertEqual(findings, [])

    def test_check_drift_warn(self):
        clip = {"positions": [[(0.0, 0.0, 0.0)], [(150.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        findings = clips.check_drift("test", clip)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S5.root-drift")
        self.assertEqual(f["level"], "warn")
        self.assertIn("150 units", f["message"])
        self.assertEqual(f["fix"], "Remove the root motion or accept it.")
        self.assertAlmostEqual(f["value"], 150.0)

    def test_check_speed_clean(self):
        findings = clips.check_speed("clean", self.clean_clip)
        self.assertEqual(findings, [])

    def test_check_speed_warn(self):
        clip = {"positions": [[(0.0, 0.0, 0.0)], [(200.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        findings = clips.check_speed("test", clip)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S5.speed")
        self.assertEqual(f["level"], "warn")
        self.assertIn("6000 units per second", f["message"])
        self.assertEqual(f["fix"], "Retime the clip or cut the pop.")
        self.assertAlmostEqual(f["value"], 6000.0)

    def test_check_stretch_clean(self):
        findings = clips.check_stretch("clean", self.clean_clip, self.parents)
        self.assertEqual(findings, [])

    def test_check_stretch_warn_max(self):
        clip = {"positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        findings = clips.check_stretch("test", clip, self.parents)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S5.bone-stretch")
        self.assertEqual(f["level"], "warn")
        self.assertIn("bone 1 changes length to 2.00 times", f["message"])
        self.assertEqual(f["fix"], "Check the retarget.")
        self.assertAlmostEqual(f["value"], 2.0)

    def test_check_stretch_names_the_bone(self):
        clip = {"positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        f = clips.check_stretch("test", clip, self.parents, ["Hips", "Hand_R"])[0]
        self.assertIn("bone 1 (Hand_R) changes length to 2.00 times", f["message"])

    def test_check_stretch_warn_min(self):
        clip = {"positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(0.0, 0.0, 0.0), (0.5, 0.0, 0.0)]],
                "fps": 30.0, "loop": True}
        findings = clips.check_stretch("test", clip, self.parents)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S5.bone-stretch")
        self.assertEqual(f["level"], "warn")
        self.assertIn("bone 1 changes length to 0.50 times", f["message"])
        self.assertEqual(f["fix"], "Check the retarget.")
        self.assertAlmostEqual(f["value"], 0.5)



class TestRunS5(unittest.TestCase):
    def setUp(self):
        self.parents = [-1, 0, 1]

    def test_clean_clips_no_findings(self):
        clips_dict = {
            "walk": {
                "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.0)],
                             [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.0)]],
                "fps": 30.0,
                "loop": True,
            },
            "idle": {
                "positions": [[(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.5, 0.0)]],
                "fps": 30.0,
                "loop": False,
            },
        }
        res = clips.run_s5(clips_dict, self.parents)
        self.assertEqual(res["findings"], [])
        self.assertIn("idle", res["stats"])
        self.assertIn("walk", res["stats"])
        for name in ["idle", "walk"]:
            s = res["stats"][name]
            self.assertIn("loop_gap", s)
            self.assertIn("root_drift", s)
            self.assertIn("speed_peak", s)
            self.assertIn("bone_stretch", s)
            self.assertIn("bbox", s)

    def test_bad_clips_produce_expected_ids(self):
        clips_dict = {
            "bad_loop": {
                "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(25.0, 0.0, 0.0), (26.0, 0.0, 0.0)]],
                "fps": 30.0,
                "loop": True,
            },
            "bad_drift": {
                "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(200.0, 0.0, 0.0), (201.0, 0.0, 0.0)]],
                "fps": 30.0,
                "loop": False,
            },
            "bad_speed": {
                "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
                             [(200.0, 0.0, 0.0), (201.0, 0.0, 0.0)]],
                "fps": 30.0,
                "loop": True,
            },
            "bad_stretch": {
                "positions": [[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
                             [(0.0, 0.0, 0.0), (2.5, 0.0, 0.0), (3.5, 0.0, 0.0)]],
                "fps": 30.0,
                "loop": True,
            },
        }
        res = clips.run_s5(clips_dict, self.parents)
        ids = {f["id"] for f in res["findings"]}
        self.assertEqual(ids, {"S5.loop-gap", "S5.root-drift", "S5.speed", "S5.bone-stretch"})
        # Ensure sorted name order in stats
        self.assertEqual(list(res["stats"].keys()), sorted(clips_dict.keys()))

class TestStretchFloor(unittest.TestCase):
    def test_tiny_bones_are_ignored(self):
        parents = [-1, 0, 1]
        P = [[(0, 0, 0), (10, 0, 0), (10.001, 0, 0)], [(0, 0, 0), (10, 0, 0), (10.5, 0, 0)]]
        self.assertEqual(clips.bone_stretch(P, parents)["ratio_max"], 1.0)


if __name__ == "__main__":
    unittest.main()
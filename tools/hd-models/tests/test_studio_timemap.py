"""Tests for studio/timemap.py (S6 time‑map maths).
Each test mirrors the specification in JOB.md.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # add tools/hd-models
sys.path.insert(0, str(HERE))

from studio import timemap

class TestSegments(unittest.TestCase):
    def test_default_map(self):
        self.assertEqual(timemap.default_map(100, 270), [[0, 0], [100, 270]])

    def test_segments_two_points(self):
        pts = [[0, 0], [100, 270]]
        segs = timemap.segments(pts)
        self.assertEqual(len(segs), 1)
        seg = segs[0]
        self.assertEqual(seg["clip"], (0, 100))
        self.assertEqual(seg["row"], (0, 270))
        self.assertAlmostEqual(seg["stretch"], 2.7)

    def test_segments_multiple(self):
        pts = [[0, 0], [50, 130], [100, 270]]
        segs = timemap.segments(pts)
        self.assertEqual(len(segs), 2)
        # first segment stretch = 130/50 = 2.6
        self.assertAlmostEqual(segs[0]["stretch"], 2.6)
        # second segment stretch = (270-130)/(100-50) = 140/50 = 2.8
        self.assertAlmostEqual(segs[1]["stretch"], 2.8)

    def test_segments_error_one_point(self):
        with self.assertRaises(ValueError):
            timemap.segments([[0, 0]])

class TestMonotonic(unittest.TestCase):
    def test_monotonic_pass(self):
        pts = [[0, 0], [10, 20], [20, 30]]
        findings = timemap.check_monotonic(pts)
        self.assertEqual(findings, [])

    def test_monotonic_fail_clip(self):
        pts = [[10, 0], [5, 10]]
        findings = timemap.check_monotonic(pts)
        self.assertTrue(any(f["id"] == "S6.monotonic" for f in findings))

    def test_monotonic_fail_row(self):
        pts = [[0, 10], [5, 5]]
        findings = timemap.check_monotonic(pts)
        self.assertTrue(any(f["id"] == "S6.monotonic" for f in findings))


class TestStretch(unittest.TestCase):
    def test_stretch_pass(self):
        pts = [[0, 0], [10, 10]]  # stretch 1.0 within default rng
        findings = timemap.check_stretch(pts)
        self.assertEqual(findings, [])

    def test_stretch_warn(self):
        pts = [[0, 0], [10, 5]]  # stretch 0.5 below rng low 0.6, above hard low 0.3
        findings = timemap.check_stretch(pts)
        self.assertTrue(any(f["id"] == "S6.stretch" and f["level"] == "warn" for f in findings))
        # worst factor should be 0.5
        self.assertEqual(findings[0]["value"], 0.5)

    def test_stretch_fail(self):
        pts = [[0, 0], [10, 2]]  # stretch 0.2 below hard low 0.3
        findings = timemap.check_stretch(pts)
        self.assertTrue(any(f["id"] == "S6.stretch" and f["level"] == "fail" for f in findings))
        self.assertEqual(findings[0]["value"], 0.2)


class TestMapping(unittest.TestCase):
    def test_row_to_clip_default(self):
        pts = [[0, 0], [100, 270]]
        self.assertAlmostEqual(timemap.row_to_clip(pts, 0), 0)
        self.assertAlmostEqual(timemap.row_to_clip(pts, 270), 100)
        self.assertAlmostEqual(timemap.row_to_clip(pts, 135), 50)
        # clamped below
        self.assertAlmostEqual(timemap.row_to_clip(pts, -10), 0)
        # clamped above
        self.assertAlmostEqual(timemap.row_to_clip(pts, 300), 100)

    def test_clip_to_row_default(self):
        pts = [[0, 0], [100, 270]]
        self.assertAlmostEqual(timemap.clip_to_row(pts, 0), 0)
        self.assertAlmostEqual(timemap.clip_to_row(pts, 100), 270)
        self.assertAlmostEqual(timemap.clip_to_row(pts, 50), 135)
        # clamped below
        self.assertAlmostEqual(timemap.clip_to_row(pts, -5), 0)
        # clamped above
        self.assertAlmostEqual(timemap.clip_to_row(pts, 150), 270)

class TestContactFor(unittest.TestCase):
    def test_contact_valid(self):
        arena = {"cards": {"1": {"contact": {"attack_row": 3, "contact_frame": 166, "row_length": 270, "suspect": False}}}}
        result = timemap.contact_for(arena, "1")
        self.assertEqual(result, {"contact_frame": 166, "row_length": 270})

    def test_missing_card(self):
        arena = {"cards": {}}
        self.assertIsNone(timemap.contact_for(arena, "99"))

    def test_wrong_act(self):
        arena = {"cards": {"1": {"contact": {"attack_row": 3, "contact_frame": 166, "row_length": 270, "suspect": False}}}}
        self.assertIsNone(timemap.contact_for(arena, "1", act="defend"))

    def test_missing_contact(self):
        arena = {"cards": {"1": {"model": 0}}}
        self.assertIsNone(timemap.contact_for(arena, "1"))

    def test_suspect_true(self):
        arena = {"cards": {"1": {"contact": {"attack_row": 3, "contact_frame": 166, "row_length": 270, "suspect": True}}}}
        self.assertIsNone(timemap.contact_for(arena, "1"))


class TestCheckStrike(unittest.TestCase):
    def setUp(self):
        self.pts = [[0, 0], [100, 270]]

    def test_no_contact(self):
        findings = timemap.check_strike(self.pts, 50, None)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S6.no-reference")
        self.assertEqual(findings[0]["level"], "info")

    def test_within_tolerance(self):
        contact = {"contact_frame": 135, "row_length": 270}
        findings = timemap.check_strike(self.pts, 50, contact)
        self.assertEqual(findings, [])

    def test_warn(self):
        contact = {"contact_frame": 140, "row_length": 270}
        findings = timemap.check_strike(self.pts, 50, contact)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S6.strike-vs-contact")
        self.assertEqual(findings[0]["level"], "warn")

    def test_fail(self):
        contact = {"contact_frame": 155, "row_length": 270}
        findings = timemap.check_strike(self.pts, 50, contact)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S6.strike-vs-contact")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertEqual(findings[0]["value"], 20)


class TestRunS6(unittest.TestCase):
    def test_inline_arena(self):
        """Test run_s6 with a tiny inline arena_rows dict."""
        arena = {
            "cards": {
                "42": {
                    "contact": {
                        "attack_row": 3,
                        "contact_frame": 120,
                        "row_length": 200,
                        "suspect": False
                    }
                }
            }
        }
        recipe = {
            "acts": {
                "attack": {
                    "strike": [50]
                }
            }
        }
        result = timemap.run_s6(recipe, "attack", 100, "42", arena)
        self.assertIn("points", result)
        self.assertIn("findings", result)
        # strike_frame 50 should map to contact_frame 120
        pts = result["points"]
        # Verify the point was inserted/moved
        self.assertTrue(any(p[0] == 50 and p[1] == 120 for p in pts))
        # Findings should include stretch/monotonic/strike
        finding_ids = [f["id"] for f in result["findings"]]
        # Since default map was used and point inserted, monotonic should pass
        self.assertFalse(any(f["id"] == "S6.monotonic" and f["level"] == "fail" for f in result["findings"]))
        # strike check should pass (exact match)
        self.assertFalse(any(f["id"] == "S6.strike-vs-contact" and f["level"] == "fail" for f in result["findings"]))

    def test_real_arena_card_1(self):
        """Test run_s6 against the real arena_rows.json for card '1'."""
        import json
        from pathlib import Path
        ref = Path(__file__).resolve().parent.parent / "studio" / "reference" / "arena_rows.json"
        with ref.open() as f:
            arena = json.load(f)
        recipe = {
            "acts": {
                "attack": {
                    "strike": [80]
                }
            }
        }
        # clip_frames = 100, card "1" has contact_frame=166, row_length=270
        result = timemap.run_s6(recipe, "attack", 100, "1", arena)
        pts = result["points"]
        # The point for clip 80 should map to row 166
        self.assertTrue(any(p[0] == 80 and p[1] == 166 for p in pts))
        # No monotonic failure
        self.assertFalse(any(f["id"] == "S6.monotonic" and f["level"] == "fail" for f in result["findings"]))
        # Strike check: clip 80 with default map (stretch 2.7) -> row 216; gap=50 => fail
        # but after suggest_point, it should map exactly to 166 -> pass
        self.assertFalse(any(f["id"] == "S6.strike-vs-contact" and f["level"] == "fail" for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()

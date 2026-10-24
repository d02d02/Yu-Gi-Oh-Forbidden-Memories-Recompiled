"""Tests for studio/look.py (S7 look and camera-move rules)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import audit, look


class TestDefaults(unittest.TestCase):
    def test_default_look_has_the_eight_defaults(self):
        d = look.default_look()
        self.assertEqual(set(d.keys()), {
            "ambient", "light_gain", "normal_strength", "highlight",
            "flip_green", "camera_near", "camera_keep", "camera_scale",
        })
        self.assertEqual(d["ambient"], 20)
        self.assertEqual(d["light_gain"], 100)
        self.assertEqual(d["normal_strength"], 180)
        self.assertEqual(d["highlight"], 100)
        self.assertIs(d["flip_green"], True)
        self.assertEqual(d["camera_near"], 1000)
        self.assertEqual(d["camera_keep"], 50)
        self.assertEqual(d["camera_scale"], 100)

    def test_default_look_returns_new_dict_each_call(self):
        d1 = look.default_look()
        d2 = look.default_look()
        self.assertIsNot(d1, d2)

    def test_normalize_look_fills_missing_keys(self):
        out = look.normalize_look({"ambient": 30})
        self.assertEqual(out["ambient"], 30)
        self.assertEqual(out["light_gain"], 100)
        self.assertEqual(out["normal_strength"], 180)
        self.assertEqual(out["highlight"], 100)
        self.assertIs(out["flip_green"], True)
        self.assertEqual(out["camera_near"], 1000)
        self.assertEqual(out["camera_keep"], 50)
        self.assertEqual(out["camera_scale"], 100)

    def test_normalize_look_coerces_int_values(self):
        out = look.normalize_look({"ambient": "40", "light_gain": 150.7})
        self.assertEqual(out["ambient"], 40)
        self.assertEqual(out["light_gain"], 150)

    def test_normalize_look_coerces_flip_green_to_bool(self):
        out = look.normalize_look({"flip_green": 0})
        self.assertIs(out["flip_green"], False)
        out = look.normalize_look({"flip_green": 1})
        self.assertIs(out["flip_green"], True)

    def test_normalize_look_drops_unknown_keys(self):
        out = look.normalize_look({"unknown": 123})
        self.assertNotIn("unknown", out)

    def test_normalize_look_raises_on_non_numeric(self):
        with self.assertRaises(ValueError):
            look.normalize_look({"ambient": "abc"})
        with self.assertRaises(ValueError):
            look.normalize_look({"light_gain": None})


class TestMoveCount(unittest.TestCase):
    def test_check_move_count_none_when_empty(self):
        self.assertIsNone(look.check_move_count([]))

    def test_check_move_count_none_when_eight(self):
        shots = [{} for _ in range(8)]
        self.assertIsNone(look.check_move_count(shots))

    def test_check_move_count_finding_when_nine(self):
        shots = [{} for _ in range(9)]
        f = look.check_move_count(shots)
        self.assertIsNotNone(f)
        self.assertEqual(f["id"], "S7.move-count")
        self.assertEqual(f["level"], "fail")
        self.assertEqual(f["message"], "Too many camera moves: 9 of 8.")
        self.assertEqual(f["fix"], "Delete or merge a move.")


class TestMoveRange(unittest.TestCase):
    def test_check_move_range_none_when_empty(self):
        self.assertIsNone(look.check_move_range([], {}))

    def test_check_move_range_none_when_all_ok(self):
        shots = [{"act": "attack", "from": 10, "to": 20}]
        row_lengths = {"attack": 100}
        self.assertIsNone(look.check_move_range(shots, row_lengths))

    def test_check_move_range_act_missing(self):
        shots = [{"act": "idle", "from": 0, "to": 10}]
        row_lengths = {"attack": 50}
        findings = look.check_move_range(shots, row_lengths)
        self.assertIsNotNone(findings)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S7.move-range")
        self.assertEqual(f["level"], "fail")
        self.assertIn("Move 1:", f["message"])
        self.assertIn("missing from row lengths", f["message"])
        self.assertEqual(f["fix"], "Set from below to, inside the row.")

    def test_check_move_range_negative_from(self):
        shots = [{"act": "attack", "from": -5, "to": 10}]
        row_lengths = {"attack": 100}
        findings = look.check_move_range(shots, row_lengths)
        self.assertEqual(len(findings), 1)
        self.assertIn("negative from -5", findings[0]["message"])

    def test_check_move_range_from_not_below_to(self):
        shots = [{"act": "attack", "from": 20, "to": 15}]
        row_lengths = {"attack": 100}
        findings = look.check_move_range(shots, row_lengths)
        self.assertEqual(len(findings), 1)
        self.assertIn("from 20 is not below to 15", findings[0]["message"])

    def test_check_move_range_to_past_length(self):
        shots = [{"act": "attack", "from": 10, "to": 110}]
        row_lengths = {"attack": 100}
        findings = look.check_move_range(shots, row_lengths)
        self.assertEqual(len(findings), 1)
        self.assertIn("to 110 is past the row length 100", findings[0]["message"])

    def test_check_move_range_multiple_bad_moves(self):
        shots = [
            {"act": "a", "from": -1, "to": 5},
            {"act": "b", "from": 10, "to": 5},
        ]
        row_lengths = {"a": 20, "b": 30}
        findings = look.check_move_range(shots, row_lengths)
        self.assertEqual(len(findings), 2)
        self.assertIn("Move 1:", findings[0]["message"])
        self.assertIn("Move 2:", findings[1]["message"])


class TestMoveValues(unittest.TestCase):
    def test_check_move_values_none_when_empty(self):
        self.assertIsNone(look.check_move_values([]))

    def test_check_move_values_none_when_valid(self):
        shots = [{
            "act": "attack", "from": 0, "to": 10,
            "yaw": 0, "pitch": 0, "distance": 100, "ease": "linear"
        }]
        self.assertIsNone(look.check_move_values(shots))

    def test_check_move_values_invalid_ease(self):
        shots = [{
            "act": "attack", "from": 0, "to": 10,
            "yaw": 0, "pitch": 0, "distance": 100, "ease": "bounce"
        }]
        findings = look.check_move_values(shots)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S7.move-values")
        self.assertEqual(f["level"], "fail")
        self.assertEqual(f["message"], "Move 1: ease out of range.")
        self.assertEqual(f["fix"], "Use a value inside the allowed range.")

    def test_check_move_values_invalid_distance(self):
        shots = [{
            "act": "attack", "from": 0, "to": 10,
            "yaw": 0, "pitch": 0, "distance": 10, "ease": "linear"
        }]
        findings = look.check_move_values(shots)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Move 1: distance out of range.")

    def test_check_move_values_invalid_yaw(self):
        shots = [{
            "act": "attack", "from": 0, "to": 10,
            "yaw": 200, "pitch": 0, "distance": 100, "ease": "in"
        }]
        findings = look.check_move_values(shots)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Move 1: yaw out of range.")

    def test_check_move_values_invalid_pitch(self):
        shots = [{
            "act": "attack", "from": 0, "to": 10,
            "yaw": 0, "pitch": -90, "distance": 100, "ease": "out"
        }]
        findings = look.check_move_values(shots)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Move 1: pitch out of range.")


class TestMoveExtreme(unittest.TestCase):
    def _shot(self, **over):
        shot = {
            "act": "attack", "from": 0, "to": 10,
            "yaw": 0, "pitch": 0, "distance": 100, "ease": "linear"
        }
        shot.update(over)
        return shot

    def test_check_move_extreme_none_when_empty(self):
        self.assertIsNone(look.check_move_extreme([]))

    def test_check_move_extreme_none_when_normal(self):
        self.assertIsNone(look.check_move_extreme([self._shot()]))

    def test_check_move_extreme_large_yaw(self):
        findings = look.check_move_extreme([self._shot(yaw=120)])
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S7.move-extreme")
        self.assertEqual(f["level"], "warn")
        self.assertEqual(f["message"], "Move 1 ends far from the arena view.")
        self.assertEqual(f["fix"], "Lower yaw or raise distance.")

    def test_check_move_extreme_negative_yaw(self):
        findings = look.check_move_extreme([self._shot(yaw=-120)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["level"], "warn")

    def test_check_move_extreme_large_pitch(self):
        findings = look.check_move_extreme([self._shot(pitch=75)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Move 1 ends far from the arena view.")

    def test_check_move_extreme_small_distance(self):
        findings = look.check_move_extreme([self._shot(distance=40)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Move 1 ends far from the arena view.")

    def test_check_move_extreme_at_thresholds_is_ok(self):
        findings = look.check_move_extreme([
            self._shot(yaw=90, pitch=60, distance=50)
        ])
        self.assertIsNone(findings)

    def test_check_move_extreme_one_finding_per_bad_move(self):
        findings = look.check_move_extreme([
            self._shot(yaw=120), self._shot(), self._shot(distance=10)
        ])
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["message"], "Move 1 ends far from the arena view.")
        self.assertEqual(findings[1]["message"], "Move 3 ends far from the arena view.")


class TestBrightness(unittest.TestCase):
    def test_check_brightness_none_when_bls_lum_zero(self):
        self.assertIsNone(look.check_brightness(100, 0))
        self.assertIsNone(look.check_brightness(100, -10))

    def test_check_brightness_none_when_bls_lum_none(self):
        self.assertIsNone(look.check_brightness(100, None))

    def test_check_brightness_none_when_model_lum_none(self):
        self.assertIsNone(look.check_brightness(None, 100))

    def test_check_brightness_none_when_within_15_percent(self):
        self.assertIsNone(look.check_brightness(100, 100))
        self.assertIsNone(look.check_brightness(110, 100))
        self.assertIsNone(look.check_brightness(85, 100))

    def test_check_brightness_warn_when_over_15_percent(self):
        finding = look.check_brightness(130, 100)
        self.assertIsNotNone(finding)
        self.assertEqual(finding["id"], "S7.brightness")
        self.assertEqual(finding["level"], "warn")
        self.assertEqual(finding["message"], "Model brightness differs from the disc by 30%.")
        self.assertEqual(finding["fix"], "Adjust light gain or ambient.")
        self.assertAlmostEqual(finding["value"], 0.3)

    def test_check_brightness_rounds_percentage(self):
        finding = look.check_brightness(116, 100)
        self.assertIsNotNone(finding)
        self.assertEqual(finding["message"], "Model brightness differs from the disc by 16%.")


if __name__ == "__main__":
    unittest.main()
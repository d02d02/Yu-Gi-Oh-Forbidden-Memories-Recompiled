"""Tests for studio/placement.py (S4 size and placement maths), UI-free."""
import json
import struct
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import audit, placement  # noqa: E402
import synthetic_gltf  # noqa: E402


def _write_boxes(path, boxes):
    """Write a minimal glb with one node/mesh per axis-aligned box."""
    b = synthetic_gltf.Builder()
    nodes, meshes = [], []
    for i, (x0, x1, y0, y1, z0, z1) in enumerate(boxes):
        p, n, _uv, idx = synthetic_gltf.box(x0, x1, y0, y1, z0, z1)
        pos = b.accessor(p, "VEC3")
        nor = b.accessor(n, "VEC3")
        indices = b.accessor(idx, "SCALAR", 5125)
        nodes.append({"name": f"Box{i}", "mesh": i})
        meshes.append({"primitives": [{"attributes": {"POSITION": pos, "NORMAL": nor},
                                       "indices": indices}]})
    doc = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}],
           "nodes": nodes, "meshes": meshes,
           "buffers": [{"byteLength": 0}], "bufferViews": b.views, "accessors": b.accessors}
    while len(b.buf) % 4:
        b.buf.append(0)
    doc["buffers"][0]["byteLength"] = len(b.buf)
    text = json.dumps(doc).encode()
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text
    body += struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)



class TestFit(unittest.TestCase):
    def test_height_default(self):
        r = placement.fit([0, 0, 0], [10, 20, 30], mode="height")
        self.assertAlmostEqual(r["scale"], 373 / 20)
        self.assertAlmostEqual(r["height"], 373)
        self.assertAlmostEqual(r["extent_x"], 10 * 373 / 20)
        self.assertAlmostEqual(r["extent_z"], 30 * 373 / 20)

    def test_height_value(self):
        r = placement.fit([2, 0, 0], [4, 4, 6], mode="height", value=100)
        self.assertAlmostEqual(r["scale"], 25)
        self.assertAlmostEqual(r["height"], 100)
        self.assertAlmostEqual(r["extent_x"], 50)
        self.assertAlmostEqual(r["extent_z"], 150)

    def test_extent_default(self):
        r = placement.fit([0, 0, 0], [10, 20, 30], mode="extent")
        self.assertAlmostEqual(r["scale"], 191 / 30)
        self.assertAlmostEqual(r["extent_z"], 191)
        self.assertAlmostEqual(r["height"], 20 * 191 / 30)

    def test_extent_picks_max(self):
        r = placement.fit([0, 0, 0], [30, 20, 3], mode="extent", value=95.5)
        self.assertAlmostEqual(r["scale"], 95.5 / 30)
        self.assertAlmostEqual(r["extent_x"], 95.5)

    def test_percent_default(self):
        r = placement.fit([0, 0, 0], [10, 20, 30], mode="percent")
        self.assertAlmostEqual(r["scale"], 1.0)
        self.assertAlmostEqual(r["height"], 20)
        self.assertAlmostEqual(r["extent_z"], 30)

    def test_percent_value(self):
        r = placement.fit([0, 0, 0], [2, 4, 6], mode="percent", value=150)
        self.assertAlmostEqual(r["scale"], 1.5)
        self.assertAlmostEqual(r["height"], 6)

    def test_numpy_arrays(self):
        r = placement.fit(np.array([0, 0, 0]), np.array([2, 4, 6]), mode="height", value=200)
        self.assertAlmostEqual(r["scale"], 50)
        self.assertAlmostEqual(r["extent_x"], 100)

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            placement.fit([0, 0, 0], [1, 1, 1], mode="bogus")


class TestBodyExtents(unittest.TestCase):
    def test_lower_half_excludes_wings(self):
        glb = HERE / "synthetic_winged.glb"
        # Body x -0.2..0.2, y 0..1, z -0.1..0.1; thin wings y 0.6..0.8, x -3..3.
        _write_boxes(glb, [(-0.2, 0.2, 0.0, 1.0, -0.1, 0.1),
                           (-3.0, 3.0, 0.6, 0.8, -0.05, 0.05)])
        try:
            model = audit.Model(glb)
            fitting = placement.fit(model.lo, model.hi, mode="percent")
            extents = placement.body_extents(model, fitting)
            self.assertAlmostEqual(fitting["extent_x"], 6.0)
            self.assertAlmostEqual(extents["extent_x"], 0.4)
            self.assertAlmostEqual(extents["extent_z"], 0.2)
        finally:
            glb.unlink(missing_ok=True)

    def test_applies_fit_scale(self):
        glb = HERE / "synthetic_winged_scale.glb"
        _write_boxes(glb, [(-0.2, 0.2, 0.0, 1.0, -0.1, 0.1),
                           (-3.0, 3.0, 0.6, 0.8, -0.05, 0.05)])
        try:
            model = audit.Model(glb)
            fitting = placement.fit(model.lo, model.hi, mode="percent", value=200)
            extents = placement.body_extents(model, fitting)
            self.assertAlmostEqual(extents["extent_x"], 0.8)
            self.assertAlmostEqual(extents["extent_z"], 0.4)
        finally:
            glb.unlink(missing_ok=True)

    def test_fallback_to_full_extent_without_vertices(self):
        class Empty:
            lo = np.array([0.0, 0.0, 0.0])
            hi = np.array([10.0, 20.0, 30.0])
            prims = []

        fitting = placement.fit(Empty.lo, Empty.hi, mode="percent", value=150)
        extents = placement.body_extents(Empty(), fitting)
        self.assertAlmostEqual(extents["extent_x"], 15.0)
        self.assertAlmostEqual(extents["extent_z"], 45.0)


class TestFootprintRatio(unittest.TestCase):
    def test_fits_within_proxy(self):
        r = placement.footprint_ratio(191, 236)
        self.assertAlmostEqual(r["ratio"], 1.0)
        self.assertTrue(r["proxy"])

    def test_within_limits(self):
        # 50% of each proxy dimension -> ratio 0.5
        r = placement.footprint_ratio(191 / 2, 236 / 2)
        self.assertAlmostEqual(r["ratio"], 0.5)

    def test_x_dominant(self):
        # x extent drives the ratio when x/191 > z/236
        r = placement.footprint_ratio(191 * 2, 0)
        self.assertAlmostEqual(r["ratio"], 2.0)

    def test_z_dominant(self):
        # z extent drives the ratio when z/236 > x/191
        r = placement.footprint_ratio(0, 236 * 1.5)
        self.assertAlmostEqual(r["ratio"], 1.5)

    def test_mixed_extents(self):
        r = placement.footprint_ratio(191 * 1.1, 236 * 0.9)
        self.assertAlmostEqual(r["ratio"], 1.1)

    def test_proxy_flag(self):
        r = placement.footprint_ratio(100, 100)
        self.assertIs(r["proxy"], True)


class TestCheckFootprint(unittest.TestCase):
    def test_within_proxy_is_none(self):
        # r = 1.0 -> no finding
        self.assertIsNone(placement.check_footprint(191, 236))

    def test_just_under_threshold_is_none(self):
        # r = 1.05 -> still within 1.10
        self.assertIsNone(placement.check_footprint(191 * 1.05, 236))

    def test_warn(self):
        r = placement.check_footprint(191 * 1.15, 236)  # r ~ 1.15
        self.assertEqual(r["id"], "S4.footprint")
        self.assertEqual(r["level"], "warn")
        self.assertEqual(r["message"], "Model is 15% wider than the card footprint.")
        self.assertEqual(r["fix"], "Fit with a smaller pose, lower the scale to 87%, or switch to Extent.")
        self.assertEqual(r["value"], 15)

    def test_at_upper_warn_boundary(self):
        r = placement.check_footprint(191 * 1.60, 236)  # r ~ 1.60
        self.assertEqual(r["level"], "warn")

    def test_warn_only_above_1_60(self):
        r = placement.check_footprint(191 * 1.70, 236)  # r ~ 1.70
        self.assertEqual(r["id"], "S4.footprint")
        self.assertEqual(r["level"], "warn")
        self.assertEqual(r["message"], "Model is 70% wider than the card footprint.")
        self.assertEqual(r["fix"], "Fit with a smaller pose, lower the scale to 59%, or switch to Extent.")
        self.assertEqual(r["value"], 70)

    def test_uses_whichever_extent_is_larger(self):
        # z drives: z/236 larger
        r = placement.check_footprint(191, 236 * 1.20)  # ratio 1.20 via z
        self.assertEqual(r["level"], "warn")
        self.assertIn("20%", r["message"])

    def test_values_rounded_to_whole_numbers(self):
        r = placement.check_footprint(191 * 1.117, 236)  # ratio 1.117
        # wider = round(11.7) = 12, scale = round(100/1.117) = round(89.52) = 90
        self.assertEqual(r["message"], "Model is 12% wider than the card footprint.")
        self.assertIn("90%", r["fix"])


class TestCheckGround(unittest.TestCase):
    def test_within_tolerance_is_none(self):
        # gap 0 -> no finding
        self.assertIsNone(placement.check_ground(0, ground_offset=0))

    def test_small_gap_is_none(self):
        # gap 5 <= 8 -> no finding
        self.assertIsNone(placement.check_ground(5, ground_offset=0))

    def test_at_boundary_8_is_none(self):
        # abs(8 - 0) == 8, not > 8 -> no finding
        self.assertIsNone(placement.check_ground(8, ground_offset=0))

    def test_above_tolerance_is_warn(self):
        r = placement.check_ground(9, ground_offset=0)  # gap 9 > 8
        self.assertEqual(r["id"], "S4.ground")
        self.assertEqual(r["level"], "warn")
        self.assertTrue(r["fix"])

    def test_floating_suppresses(self):
        # even far off, floating -> no finding
        self.assertIsNone(placement.check_ground(100, ground_offset=0, floating=True))

    def test_negative_lowest(self):
        r = placement.check_ground(-10, ground_offset=0)  # gap 10 > 8
        self.assertEqual(r["id"], "S4.ground")
        self.assertEqual(r["level"], "warn")

    def test_fix_uses_ground_offset_value(self):
        r = placement.check_ground(12.6, ground_offset=0)  # N = round(12.6) = 13
        self.assertIn("Set ground offset to 13", r["fix"])
        self.assertIn("floating", r["fix"])

    def test_uses_ground_offset(self):
        # lowest_y 0, ground_offset 20 -> gap 20 > 8 -> warn
        r = placement.check_ground(0, ground_offset=20)
        self.assertEqual(r["level"], "warn")
        self.assertIn("Set ground offset to 0", r["fix"])


class TestUniform(unittest.TestCase):
    def _g(self, nodes):
        return {"nodes": nodes}

    def test_no_scale_keys_is_none(self):
        g = self._g([{"name": "a"}, {"name": "b", "translation": [0, 1, 0]}])
        self.assertIsNone(placement.check_uniform_scale(g))

    def test_uniform_scale_is_none(self):
        g = self._g([{"name": "a", "scale": [1, 1, 1]}, {"name": "b", "scale": [2, 2, 2]}])
        self.assertIsNone(placement.check_uniform_scale(g))

    def test_within_tolerance_is_none(self):
        g = self._g([{"name": "a", "scale": [1, 1 + 5e-5, 1]}])
        self.assertIsNone(placement.check_uniform_scale(g))

    def test_at_tolerance_is_none(self):
        # difference exactly 1e-4 is not "more than 1e-4" -> ok
        g = self._g([{"name": "a", "scale": [1, 1 + 1e-4, 1]}])
        self.assertIsNone(placement.check_uniform_scale(g))

    def test_above_tolerance_is_fail(self):
        g = self._g([{"name": "a", "scale": [1, 1 + 2e-4, 1]}])
        r = placement.check_uniform_scale(g)
        self.assertEqual(r["id"], "S4.uniform")
        self.assertEqual(r["level"], "fail")

    def test_lists_offending_node_names(self):
        g = self._g([{"name": "a", "scale": [1, 2, 1]}, {"name": "b", "scale": [1, 1, 1]},
                     {"name": "c", "scale": [1, 5, 1]}])
        r = placement.check_uniform_scale(g)
        self.assertIn("a", r["message"])
        self.assertNotIn("b", r["message"])
        self.assertIn("c", r["message"])
        self.assertEqual(r["value"], 2)

    def test_fix_message(self):
        g = self._g([{"name": "a", "scale": [1, 2, 1]}])
        r = placement.check_uniform_scale(g)
        self.assertEqual(r["fix"], "Re-export from Blender with applied scale.")
        self.assertIn("a", r["message"])

    def test_node_without_name_uses_index(self):
        g = self._g([{"scale": [1, 2, 1]}])
        r = placement.check_uniform_scale(g)
        self.assertIn("0", r["message"])


class TestRunS4(unittest.TestCase):
    def setUp(self):
        self.glb = HERE / "synthetic_run_s4.glb"
        synthetic_gltf.write(self.glb)

    def tearDown(self):
        self.glb.unlink(missing_ok=True)

    @staticmethod
    def _scaled_glb(path, scale):
        """A minimal glb whose single node has a non-uniform `scale`; the
        synthetic rig has no `scale` keys, so this exercises the S4.uniform path."""
        b = synthetic_gltf.Builder()
        p, n, uv, idx = synthetic_gltf.box(-0.2, 0.2, 0.0, 1.0, -0.1, 0.1)
        pos = b.accessor(p, "VEC3")
        nor = b.accessor(n, "VEC3")
        indices = b.accessor(idx, "SCALAR", 5125)
        node = {"name": "Root", "mesh": 0, "scale": list(scale)}
        doc = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
               "nodes": [node],
               "meshes": [{"primitives": [{"attributes": {"POSITION": pos, "NORMAL": nor}, "indices": indices}]}],
               "buffers": [{"byteLength": 0}], "bufferViews": b.views, "accessors": b.accessors}
        while len(b.buf) % 4:
            b.buf.append(0)
        doc["buffers"][0]["byteLength"] = len(b.buf)
        text = json.dumps(doc).encode()
        text += b" " * (-len(text) % 4)
        body = struct.pack("<II", len(text), 0x4E4F534A) + text
        body += struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)

    def test_returns_fit_and_findings(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "height"}})
        self.assertIn("fit", r)
        self.assertIsInstance(r["findings"], list)
        self.assertAlmostEqual(r["fit"]["height"], 373.0)

    def test_height_mode_body_footprint_ignores_sword(self):
        # The rig's sword sits above the body's midline, so the body footprint
        # fits the card even though the full span is 1.5x the card width.
        r = placement.run_s4(self.glb, {"size": {"mode": "height"}})
        self.assertAlmostEqual(r["fit"]["scale"], 373 / 1.75, delta=1e-3)
        self.assertAlmostEqual(r["fit"]["body_extent_x"], 0.4 * 373 / 1.75, delta=1e-3)
        self.assertAlmostEqual(r["fit"]["body_extent_z"], 0.2 * 373 / 1.75, delta=1e-3)
        fp = [f for f in r["findings"] if f["id"] == "S4.footprint"]
        self.assertEqual(fp, [])
        self.assertFalse([f for f in r["findings"] if f["id"] == "S4.ground"])
        self.assertFalse([f for f in r["findings"] if f["id"] == "S4.uniform"])

    def test_extent_mode_no_findings(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "extent"}})
        self.assertAlmostEqual(r["fit"]["extent_x"], 191.0)
        self.assertEqual(r["findings"], [])

    def test_percent_mode_defaults_to_model_scale(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "percent"}, "model": {"scale": 50}})
        self.assertAlmostEqual(r["fit"]["scale"], 0.5)

    def test_percent_mode_size_value_overrides_model_scale(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "percent", "value": 200}, "model": {"scale": 100}})
        self.assertAlmostEqual(r["fit"]["scale"], 2.0)
        self.assertAlmostEqual(r["fit"]["height"], 1.75 * 2.0)

    def test_ground_offset_warns(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "height", "ground_offset": 20}})
        self.assertAlmostEqual(r["fit"]["height"], 373.0)
        gd = [f for f in r["findings"] if f["id"] == "S4.ground"]
        self.assertEqual(len(gd), 1)
        self.assertEqual(gd[0]["level"], "warn")

    def test_floating_suppresses_ground(self):
        r = placement.run_s4(self.glb, {"size": {"mode": "height", "ground_offset": 20, "floating": True}})
        self.assertFalse([f for f in r["findings"] if f["id"] == "S4.ground"])
        fp = [f for f in r["findings"] if f["id"] == "S4.footprint"]
        self.assertEqual(fp, [])

    def test_winged_body_fits_no_footprint_warn(self):
        # A wide thin slab in the upper half (a wing) must not trigger the
        # footprint warn when the lower-half body fits the card.
        glb = HERE / "synthetic_run_s4_winged.glb"
        _write_boxes(glb, [(-0.25, 0.25, 0.0, 1.0, -0.05, 0.05),
                           (-3.0, 3.0, 0.6, 0.8, -0.05, 0.05)])
        try:
            r = placement.run_s4(glb, {"size": {"mode": "height"}})
            self.assertAlmostEqual(r["fit"]["body_extent_x"], 0.5 * 373.0, delta=1e-3)
            self.assertEqual(r["findings"], [])
        finally:
            glb.unlink(missing_ok=True)

    def test_too_wide_body_warns(self):
        glb = HERE / "synthetic_run_s4_wide.glb"
        _write_boxes(glb, [(-0.3, 0.3, 0.0, 1.0, -0.05, 0.05)])
        try:
            r = placement.run_s4(glb, {"size": {"mode": "height"}})
            fp = [f for f in r["findings"] if f["id"] == "S4.footprint"]
            self.assertEqual(len(fp), 1)
            self.assertEqual(fp[0]["level"], "warn")
            self.assertEqual(fp[0]["message"], "Model is 17% wider than the card footprint.")
            self.assertEqual(fp[0]["value"], 17)
            self.assertNotIn("Wings", fp[0]["message"])
        finally:
            glb.unlink(missing_ok=True)

    def test_wings_note_appended_when_full_span_is_wide(self):
        glb = HERE / "synthetic_run_s4_winged_wide.glb"
        _write_boxes(glb, [(-0.3, 0.3, 0.0, 1.0, -0.05, 0.05),
                           (-3.0, 3.0, 0.6, 0.8, -0.05, 0.05)])
        try:
            r = placement.run_s4(glb, {"size": {"mode": "height"}})
            fp = [f for f in r["findings"] if f["id"] == "S4.footprint"]
            self.assertEqual(len(fp), 1)
            self.assertIn("Wings or limbs excluded", fp[0]["message"])
            self.assertIn("full span is 1172% of the card footprint", fp[0]["message"])
        finally:
            glb.unlink(missing_ok=True)

    def test_uniform_finding_surfaces(self):
        glb = HERE / "synthetic_run_s4_scaled.glb"
        self._scaled_glb(glb, [2, 2, 1])
        try:
            r = placement.run_s4(glb, {"size": {"mode": "percent"}})
            uni = [f for f in r["findings"] if f["id"] == "S4.uniform"]
            self.assertEqual(len(uni), 1)
            self.assertEqual(uni[0]["level"], "fail")
            self.assertIn("Root", uni[0]["message"])
        finally:
            glb.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

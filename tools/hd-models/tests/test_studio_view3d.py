"""Tests for studio/view3d.py math functions.
Run from repo root with: python3 -m unittest discover -s . -p "test_*.py" -k TestOrbit
"""

import unittest
import numpy as np
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import view3d


class TestOrbit(unittest.TestCase):
    def test_orbit_view_identity(self):
        """Target maps to (0,0,-dist); camera position maps to origin."""
        yaw, pitch, dist = 0.0, 0.0, 10.0
        target = np.array([1.0, 2.0, 3.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        # Camera position in world space
        cam_x = np.sin(yaw) * np.cos(pitch)
        cam_y = np.sin(pitch)
        cam_z = np.cos(yaw) * np.cos(pitch)
        cam_pos = target + dist * np.array([cam_x, cam_y, cam_z])
        # Transform point
        point = np.array([cam_pos[0], cam_pos[1], cam_pos[2], 1.0])
        cam_point = M @ point
        # Should be at origin
        self.assertTrue(np.allclose(cam_point[:3], 0.0), f"Camera pos gave {cam_point[:3]}")
        # Target should map to (0,0,-dist)
        target_point = np.array([target[0], target[1], target[2], 1.0])
        cam_target = M @ target_point
        expected = np.array([0.0, 0.0, -dist])
        self.assertTrue(np.allclose(cam_target[:3], expected), f"Target gave {cam_target[:3]}, expected {expected}")

    def test_orbit_view_arbitrary(self):
        """Test with non-zero yaw/pitch.
        Target should map to (0,0,-dist) regardless of camera rotation.
        """
        yaw, pitch, dist = np.pi/4, np.pi/6, 5.0
        target = np.array([0.0, 0.0, 0.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        target_point = np.array([target[0], target[1], target[2], 1.0])
        cam_target = M @ target_point
        expected = np.array([0.0, 0.0, -dist])
        self.assertTrue(np.allclose(cam_target[:3], expected), f"Target gave {cam_target[:3]}, expected {expected}")

    def test_orbit_view_camera_direction(self):
        """Camera forward should point from camera position to target.
        """
        yaw, pitch, dist = 0.5, 0.3, 8.0
        target = np.array([4.0, 1.0, -2.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        # Compute world camera position
        cam_x = np.sin(yaw) * np.cos(pitch)
        cam_y = np.sin(pitch)
        cam_z = np.cos(yaw) * np.cos(pitch)
        cam_pos = target + dist * np.array([cam_x, cam_y, cam_z])
        # Camera space forward is -Z axis (world space forward = target - cam_pos)
        forward_world = target - cam_pos
        forward_norm = forward_world / np.linalg.norm(forward_world)
        # Transform forward vector to camera space
        forward_cam = M[:3, :3] @ forward_norm
        # Should be (0,0,-1)
        self.assertTrue(np.allclose(forward_cam, [0.0, 0.0, -1.0]), f"Forward is {forward_cam}")

class TestProject(unittest.TestCase):
    def test_project_target_center(self):
        """Target should map to image centre with correct depth."""
        yaw, pitch, dist = 0.0, 0.0, 10.0
        target = np.array([0.0, 0.0, 0.0])
        view = view3d.orbit_view(yaw, pitch, dist, target)
        points = np.array([target])
        width, height = 200, 200
        fov = 40.0
        proj = view3d.project(points, view, fov, width, height)
        self.assertAlmostEqual(proj[0,0], width/2)
        self.assertAlmostEqual(proj[0,1], height/2)
        self.assertAlmostEqual(proj[0,2], dist)

    def test_project_right_of_center(self):
        """Point right of target should appear right of centre."""
        yaw, pitch, dist = 0.0, 0.0, 10.0
        target = np.array([0.0, 0.0, 0.0])
        view = view3d.orbit_view(yaw, pitch, dist, target)
        points = np.array([target, [1.0, 0.0, 0.0]])
        width, height = 200, 200
        fov = 40.0
        proj = view3d.project(points, view, fov, width, height)
        self.assertGreater(proj[1,0], proj[0,0])
        self.assertAlmostEqual(proj[1,1], height/2)

    def test_orbit_view_identity(self):
        """Target maps to (0,0,-dist); camera position maps to origin."""
        yaw, pitch, dist = 0.0, 0.0, 10.0
        target = np.array([1.0, 2.0, 3.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        # Camera position in world space
        cam_x = np.sin(yaw) * np.cos(pitch)
        cam_y = np.sin(pitch)
        cam_z = np.cos(yaw) * np.cos(pitch)
        cam_pos = target + dist * np.array([cam_x, cam_y, cam_z])
        # Transform point
        point = np.array([cam_pos[0], cam_pos[1], cam_pos[2], 1.0])
        cam_point = M @ point
        # Should be at origin
        self.assertTrue(np.allclose(cam_point[:3], 0.0), f"Camera pos gave {cam_point[:3]}")
        # Target should map to (0,0,-dist)
        target_point = np.array([target[0], target[1], target[2], 1.0])
        cam_target = M @ target_point
        expected = np.array([0.0, 0.0, -dist])
        self.assertTrue(np.allclose(cam_target[:3], expected), f"Target gave {cam_target[:3]}, expected {expected}")

    def test_orbit_view_arbitrary(self):
        """Test with non-zero yaw/pitch.
        Target should map to (0,0,-dist) regardless of camera rotation.
        """
        yaw, pitch, dist = np.pi/4, np.pi/6, 5.0
        target = np.array([0.0, 0.0, 0.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        target_point = np.array([target[0], target[1], target[2], 1.0])
        cam_target = M @ target_point
        expected = np.array([0.0, 0.0, -dist])
        self.assertTrue(np.allclose(cam_target[:3], expected), f"Target gave {cam_target[:3]}, expected {expected}")

    def test_orbit_view_camera_direction(self):
        """Camera forward should point from camera position to target.
        """
        yaw, pitch, dist = 0.5, 0.3, 8.0
        target = np.array([4.0, 1.0, -2.0])
        M = view3d.orbit_view(yaw, pitch, dist, target)
        # Compute world camera position
        cam_x = np.sin(yaw) * np.cos(pitch)
        cam_y = np.sin(pitch)
        cam_z = np.cos(yaw) * np.cos(pitch)
        cam_pos = target + dist * np.array([cam_x, cam_y, cam_z])
        # Camera space forward is -Z axis (world space forward = target - cam_pos)
        forward_world = target - cam_pos
        forward_norm = forward_world / np.linalg.norm(forward_world)
        # Transform forward vector to camera space
        forward_cam = M[:3, :3] @ forward_norm
        # Should be (0,0,-1)
        self.assertTrue(np.allclose(forward_cam, [0.0, 0.0, -1.0]), f"Forward is {forward_cam}")

class TestFit(unittest.TestCase):
    def test_fit_camera_basic(self):
        lo = np.array([0.0, 0.0, 0.0])
        hi = np.array([2.0, 2.0, 2.0])
        target, dist = view3d.fit_camera(lo, hi)
        expected_target = np.array([1.0, 1.0, 1.0])
        self.assertTrue(np.allclose(target, expected_target))
        radius = np.linalg.norm((hi - lo) / 2.0)
        fov = 40.0
        expected_dist = radius / (0.9 * np.tan(np.radians(fov) / 2.0))
        self.assertAlmostEqual(dist, expected_dist, places=5)

    def test_fit_larger_box(self):
        lo = np.array([-1.0, -1.0, -1.0])
        hi = np.array([1.0, 1.0, 1.0])
        _, dist1 = view3d.fit_camera(lo, hi)
        lo2 = np.array([-2.0, -2.0, -2.0])
        hi2 = np.array([2.0, 2.0, 2.0])
        _, dist2 = view3d.fit_camera(lo2, hi2)
        self.assertGreater(dist2, dist1)


class TestWire(unittest.TestCase):
    def test_shared_edge(self):
        self.assertEqual(len(view3d.wire_edges([0, 1, 2, 1, 3, 2])), 5)


class TestBones(unittest.TestCase):
    def test_chain_and_roots(self):
        self.assertEqual(view3d.bone_segments(np.zeros((3, 3)), [-1, 0, 1]).tolist(), [[0, 1], [1, 2]])
        self.assertEqual(len(view3d.bone_segments(np.zeros((2, 3)), [-1, -1])), 0)


class TestWeights(unittest.TestCase):
    def test_weight_and_colors(self):
        j = np.array([[0, 1, 2, 3], [4, 4, 4, 4]])
        w = np.array([[0.1, 0.2, 0.3, 0.4], [0.25, 0.25, 0.25, 0.25]])
        self.assertTrue(np.allclose(view3d.vertex_weight(j, w, 2), [0.3, 0.0]))
        self.assertEqual(view3d.heat_color([0, 0.5, 1]).tolist(), [[0, 0, 255], [0, 255, 0], [255, 0, 0]])


class TestDepth(unittest.TestCase):
    def test_far_first(self):
        proj = np.array([[0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 5], [0, 0, 5], [0, 0, 5]], dtype=float)
        self.assertEqual(view3d.depth_order(proj, [0, 1, 2, 3, 4, 5]).tolist(), [1, 0])


class _Model:
    prims = [{"pos": np.zeros((3, 3)), "idx": np.array([0, 1, 2]), "skinned": True,
              "joints": np.array([[0, 0, 0, 0]] * 3), "weights": np.array([[1.0, 0, 0, 0]] * 3)}]
    bind = np.tile(np.eye(4), (3, 1, 1))
    parents = [-1, 0, 1]
    names = ["a", "b", "c"]
    lo = np.zeros(3)
    hi = np.ones(3)


class TestArrays(unittest.TestCase):
    def test_arrays_and_unweighted(self):
        a = view3d.model_arrays(_Model)
        self.assertEqual(a["pos"].shape, (3, 3))
        self.assertEqual(a["bones"].shape, (3, 3))
        self.assertEqual(view3d.unweighted_bones(a["joints"], a["weights"], 3), [1, 2])


if __name__ == "__main__":
    unittest.main()

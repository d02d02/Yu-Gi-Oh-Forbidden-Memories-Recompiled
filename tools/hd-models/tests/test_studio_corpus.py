"""Tests for the synthetic corpus generation functions.

Only the first item (TestWriteGlb) is required for the initial iteration.
"""

import unittest
from pathlib import Path
import sys

# Add the repository root to sys.path as described in JOB.md
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # add /tools/hd-models to path
sys.path.insert(0, str(HERE.parent.parent.parent))  # add repo root

from studio import corpus
from studio import audit

class TestWriteGlb(unittest.TestCase):
    def test_skinned(self):
        out = Path("temp_skinned.glb")
        bones = [
            ("pelvis", None, (0, 1, 0)),
            ("spine_01", 0, (0, 0.4, 0)),
        ]
        corpus.write_glb(out, bones, skinned=True, clips=True, meshes=1)
        model = audit.load_model(str(out))
        # Expect joints for each bone
        self.assertEqual(len(model.joints), len(bones))
        out.unlink()

    def test_unskinned(self):
        out = Path("temp_unskinned.glb")
        bones = []
        corpus.write_glb(out, bones, skinned=False, clips=False, meshes=1)
        model = audit.load_model(str(out))
        # No skin → no joints
        self.assertEqual(len(model.joints), 0)
        out.unlink()

    def test_clips_animation(self):
        out = Path("temp_clips.glb")
        bones = [
            ("pelvis", None, (0, 1, 0)),
        ]
        corpus.write_glb(out, bones, skinned=True, clips=True, meshes=1)
        model = audit.load_model(str(out))
        # Expect at least one animation
        self.assertTrue(model.doc.get("animations"))
        out.unlink()

class TestHumanoids(unittest.TestCase):
    def test_c1(self):
        out = Path("temp_c1.glb")
        corpus.build("C1", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C1")
        out.unlink()

    def test_c2(self):
        out = Path("temp_c2.glb")
        corpus.build("C2", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C2")
        out.unlink()

class TestStatic(unittest.TestCase):
    def test_c3(self):
        out = Path("temp_c3.glb")
        corpus.build("C3", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C3")
        out.unlink()

    def test_c8(self):
        out = Path("temp_c8.glb")
        corpus.build("C8", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C8")
        out.unlink()

class TestCreatures(unittest.TestCase):
    def test_c4(self):
        out = Path("temp_c4.glb")
        corpus.build("C4", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C4")
        out.unlink()

    def test_c5(self):
        out = Path("temp_c5.glb")
        corpus.build("C5", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C5")
        out.unlink()

    def test_c6(self):
        out = Path("temp_c6.glb")
        corpus.build("C6", out)
        model = audit.load_model(str(out))
        cat = audit.detect_category(model)["category"]
        self.assertEqual(cat, "C6")
        out.unlink()

class TestMulti(unittest.TestCase):
    def test_all_categories(self):
        for cat in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]:
            out = Path(f"temp_{cat.lower()}.glb")
            corpus.build(cat, out)
            model = audit.load_model(str(out))
            detected = audit.detect_category(model)["category"]
            expected = corpus.EXPECTED_DETECTED[cat]
            self.assertEqual(detected, expected, f"{cat} detected as {detected}, expected {expected}")
            out.unlink()
    def test_dummy(self):
        # simple sanity check
        self.assertTrue(True)
        for cat in ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]:
            out = Path(f"temp_{cat.lower()}.glb")
            corpus.build(cat, out)
            model = audit.load_model(str(out))
            detected = audit.detect_category(model)["category"]
            expected = corpus.EXPECTED_DETECTED[cat]
            self.assertEqual(detected, expected, f"{cat} detected as {detected}, expected {expected}")
            out.unlink()

if __name__ == "__main__":
    unittest.main()

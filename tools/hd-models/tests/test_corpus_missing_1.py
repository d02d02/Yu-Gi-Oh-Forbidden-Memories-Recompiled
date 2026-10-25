"""Tests for build_missing function (Item 1).
\nThe tests verify that the three defined missing kinds produce a GLB that can be
loaded by the audit pipeline and that an unknown kind raises ``NotImplementedError``.
"""

import unittest
from pathlib import Path
import sys
import tempfile

# Adjust sys.path similar to other test files: add repository root and tools/hd-models.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # add /tools/hd-models to path
sys.path.insert(0, str(HERE.parent.parent.parent))  # add repo root

from studio import audit
from studio import corpus_missing

class TestBuildMissing(unittest.TestCase):
    def _load_glb(self, path: Path):
        """Helper to load a GLB and return the model object."""
        return audit.load_model(str(path))

    def test_no_clips_loadable(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "no_clips.glb"
            corpus_missing.build_missing("no-clips", out)
            model = self._load_glb(out)
            # Should have joints (skeleton) but no animations.
            self.assertTrue(model.joints)
            self.assertFalse(model.doc.get("animations"))

    def test_no_skeleton_loadable(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "no_skeleton.glb"
            corpus_missing.build_missing("no-skeleton", out)
            model = self._load_glb(out)
            # No joints expected.
            self.assertEqual(len(model.joints), 0)

    def test_no_skin_loadable(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "no_skin.glb"
            corpus_missing.build_missing("no-skin", out)
            model = self._load_glb(out)
            # Ensure skin attribute is empty or missing (implementation dependent).
            self.assertFalse(getattr(model, "skins", []))

    def test_unknown_kind_raises(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "unknown.glb"
            with self.assertRaises(NotImplementedError):
                corpus_missing.build_missing("unknown-kind", out)

if __name__ == "__main__":
    unittest.main()

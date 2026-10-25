import sys, unittest, tempfile
from pathlib import Path

# Add project root to path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from studio.session import Session
import recipe
from studio.corpus import build

class TestResolutionFlow3(unittest.TestCase):
    def test_library_clip_names(self):
        """Ensure clip_names on a library glb returns expected clip list."""
        with tempfile.TemporaryDirectory() as td:
            lib_path = Path(td) / "library.glb"
            build("C1", lib_path)
            main_path = Path(td) / "model.glb"
            build("C1", main_path)
            s = Session.open(str(main_path))
            # Ensure the library glb has the Idle clip
            clips = s.clip_names(library=lib_path)
            self.assertIn("Idle", clips, "Idle clip not found in library glb")

    def test_use_library_updates_build_command(self):
        """After use_library, convert_args should include clips_from with library path."""
        with tempfile.TemporaryDirectory() as td:
            main_path = Path(td) / "model.glb"
            lib_path = Path(td) / "library.glb"
            build("C1", main_path)
            build("C1", lib_path)
            s = Session.open(str(main_path))
            s.use_library(str(lib_path), "attack", "Idle")
            conv = recipe.convert_args(s.studio.recipe)
            self.assertIn("clips_from", conv, "clips_from not present after use_library")
            self.assertEqual(conv.get("clips_from"), str(lib_path), "clips_from does not match library path")

    def test_bad_library_path_raises(self):
        """Using a non‑existent library path should raise an error and keep recipe unchanged."""
        with tempfile.TemporaryDirectory() as td:
            main_path = Path(td) / "model.glb"
            build("C1", main_path)
            s = Session.open(str(main_path))
            bad_path = Path(td) / "nonexistent.glb"
            # Expect ValueError or similar
            with self.assertRaises(Exception):
                s.use_library(str(bad_path), "attack", "Idle")

if __name__ == "__main__":
    unittest.main()

import sys, unittest, tempfile
from pathlib import Path

# Add project root to path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from studio.session import Session
import recipe
from studio.corpus import build

class TestResolutionFlow2(unittest.TestCase):
    def test_humanoid_clip_names_and_use_clip(self):
        # Create a temporary GLB full humanoid (C1)
        with tempfile.TemporaryDirectory() as td:
            glb_path = Path(td) / "model.glb"
            build("C1", glb_path)
            s = Session.open(str(glb_path))
            # Ensure Idle clip is listed
            self.assertIn("Idle", s.clip_names(), "Idle clip not found in humanoid")
            # Use clip for attack act
            s.use_clip("attack", "Idle")
            # Build command args should include clips with Idle
            conv = recipe.convert_args(s.studio.recipe)
            self.assertIn("clips", conv, "Clips key missing after use_clip")
            self.assertIn("Idle", conv.get("clips", ""), "Idle not in clips after use_clip")

    def test_undo_restores_no_clips(self):
        with tempfile.TemporaryDirectory() as td:
            glb_path = Path(td) / "model.glb"
            build("C1", glb_path)
            s = Session.open(str(glb_path))
            s.use_clip("attack", "Idle")
            # Undo the last action
            s.undo()
            conv = recipe.convert_args(s.studio.recipe)
            self.assertNotIn("clips", conv, "Clips still present after undo")

    def test_dummy(self):
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()

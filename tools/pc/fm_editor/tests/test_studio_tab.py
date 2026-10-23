"""The Studio tab walks S0 on the synthetic glb (skips without a display)."""
import sys
import tempfile
import unittest
from pathlib import Path

from fm_editor.tests.test_gui import GuiCase

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "hd-models" / "tests"))
import synthetic_gltf  # noqa: E402


class StudioTabTest(GuiCase):
    def test_open_edit_undo(self):
        from fm_editor import studio_tab
        from tkinter import messagebox
        if studio_tab.session_module is None:
            self.skipTest("studio tools not found")
        tab = self.app.studio
        with tempfile.TemporaryDirectory() as folder:
            glb = Path(folder) / "m.glb"
            synthetic_gltf.write(str(glb))
            from unittest import mock
            with mock.patch("fm_editor.file_dialogs.askopenfilename", return_value=str(glb)):
                tab.open_glb()
            self.assertIsNotNone(tab.session)
            self.assertEqual(tab.current(), "S0")
            self.assertEqual(tab.session.studio.state("S0"), "fail")
            self.assertTrue(tab.checks.winfo_children())          # check rows are drawn
            self.assertTrue(tab.form.winfo_children())            # knobs are drawn
            self.assertIn("disabled", tab.next_button.state())    # S0 fails: Next is off
            licence = next(k for k in studio_tab.knobs.knobs("S0") if k["path"] == "meta.license")
            tab.commit(licence, "CC-BY-4.0")
            self.assertEqual(tab.session.studio.recipe["meta"]["license"], "CC-BY-4.0")
            tab.history("undo")
            self.assertNotIn("license", tab.session.studio.recipe.get("meta", {}))


if __name__ == "__main__":
    unittest.main()

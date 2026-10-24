"""Route A command building and frame listing (no game, no disc)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import preview


class TestCommand(unittest.TestCase):
    def test_library_scene(self):
        c = preview.command("library", "out", 364)
        self.assertIn("library_shot.py", c[2])
        self.assertEqual(c[c.index("--card") + 1], "364")
        self.assertNotIn("--cards", c)
        self.assertIn("mod.studio-preview=1", c)

    def test_field_and_arena(self):
        f = preview.command("field", "out", 364)
        self.assertNotIn("--arena", f)
        self.assertIn("mod.studio-preview=1", f)
        self.assertIn("mod.dragon-test=0", f)
        a = preview.command("arena", "out", 364, mod_id="dragon-test")
        self.assertIn("--arena", a)
        self.assertIn("mod.dragon-test=1", a)
        self.assertNotIn("mod.dragon-test=0", a)

    def test_default_windows(self):
        a = preview.command("arena", "o", 1)
        self.assertEqual(a[a.index("--start") + 1], "1250")
        self.assertEqual(a[a.index("--frames") + 1], "1650")

    def test_bad_input(self):
        for kw in ({"frames": 0}, {"every": 0}, {"start": -1}):
            with self.assertRaises(ValueError):
                preview.command("field", "o", 1, **kw)
        with self.assertRaises(ValueError):
            preview.command("turntable", "o", 1)

    def test_no_disc_refuses(self):
        self.assertFalse(preview.disc_available({}))
        self.assertTrue(preview.disc_available({"MEMORIES_DISC": "x.bin"}))


class TestInstall(unittest.TestCase):
    def test_copies_and_renames(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            src, mods = Path(d) / "src", Path(d) / "mods"
            (src / "models").mkdir(parents=True); (src / "models" / "m.hdm").write_bytes(b"x")
            (src / "mod.json").write_text(json.dumps({"id": "old", "native_models": []}))
            dest = preview.install(src, mods)
            self.assertEqual(json.loads((dest / "mod.json").read_text())["id"], "studio-preview")
            self.assertTrue((dest / "models" / "m.hdm").exists())
            preview.install(src, mods)    # a second install replaces, does not nest
            self.assertEqual(sorted(p.name for p in (mods / "studio-preview").iterdir()), ["mod.json", "models"])


class TestFrames(unittest.TestCase):
    def test_lists_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            for k in (12, 0):
                (Path(d) / f"gl-{k:04d}-s2").mkdir()
                (Path(d) / f"gl-{k:04d}-s2" / "a.bmp").write_bytes(b"x")
            names = [p.parent.name for p in preview.frames(d)]
            self.assertEqual(names, ["gl-0000-s2", "gl-0012-s2"])
            self.assertEqual(preview.frames(Path(d) / "none"), [])


if __name__ == "__main__":
    unittest.main()

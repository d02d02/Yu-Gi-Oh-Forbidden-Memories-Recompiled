"""Route A command building and frame listing (no game, no disc)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import preview


class TestCommand(unittest.TestCase):
    def test_field_and_arena(self):
        f = preview.command("field", "out", "pkg/model.json", 364, clip="attack")
        self.assertNotIn("--arena", f)
        self.assertIn("MEMORIES_NATIVE_MODEL=pkg/model.json", f)
        self.assertIn("MEMORIES_NATIVE_MODEL_ID=364", f)
        self.assertIn("MEMORIES_NATIVE_CLIP=attack", f)
        a = preview.command("arena", "out", "pkg/model.json", 364)
        self.assertIn("--arena", a)
        self.assertIn("mod.3d-monsters.attack=0", a)
        self.assertNotIn("MEMORIES_NATIVE_CLIP=attack", a)

    def test_default_windows(self):
        a = preview.command("arena", "o", "p", 1)
        self.assertEqual(a[a.index("--start") + 1], "1250")
        self.assertEqual(a[a.index("--frames") + 1], "1650")

    def test_bad_input(self):
        for kw in ({"frames": 0}, {"every": 0}, {"start": -1}):
            with self.assertRaises(ValueError):
                preview.command("field", "o", "p", 1, **kw)
        with self.assertRaises(ValueError):
            preview.command("library", "o", "p", 1)

    def test_no_disc_refuses(self):
        self.assertFalse(preview.disc_available({}))
        self.assertTrue(preview.disc_available({"MEMORIES_DISC": "x.bin"}))


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

"""Tests for the Run rows' single cached build (studio/build.py preview_build, preview_key)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import build


class PreviewBuildTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.code = 0

    def runner(self, argv):
        self.calls.append(argv)
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
        if out is not None and self.code == 0:
            out.mkdir(parents=True, exist_ok=True)
        return self.code, "line1\nline2"

    def build(self, d, key):
        return build.preview_build({"model": {}}, "m.glb", d, [1], key, runner=self.runner)

    def test_reuses_while_key_unchanged_and_rebuilds_when_it_moves(self):
        with tempfile.TemporaryDirectory() as d:
            a = self.build(d, "k1")
            self.assertTrue(a["ok"] and not a["cached"])
            (Path(d) / "preview").mkdir(exist_ok=True)
            b = self.build(d, "k1")
            self.assertTrue(b["cached"])
            self.assertEqual(len(self.calls), 1)
            c = self.build(d, "k2")
            self.assertFalse(c["cached"])
            self.assertEqual(len(self.calls), 2)

    def test_failed_build_is_not_cached(self):
        with tempfile.TemporaryDirectory() as d:
            self.code = 3
            self.assertFalse(self.build(d, "k")["ok"])
            self.assertFalse((Path(d) / "preview.key").exists())
            self.code = 0
            self.assertFalse(self.build(d, "k")["cached"])

    def test_key_ignores_marks_acks_and_built_path_but_not_knobs_or_model(self):
        base = {"model": {"cards": [1]}, "pkg": {"name": "x"}}
        k = build.preview_key(base, "sha")
        noisy = {**base, "runs": [{"row": "a"}], "acks": [1], "pkg": {"name": "x", "path": "/p"}}
        self.assertEqual(k, build.preview_key(noisy, "sha"))
        self.assertNotEqual(k, build.preview_key({**base, "pkg": {"name": "y"}}, "sha"))
        self.assertNotEqual(k, build.preview_key(base, "other"))


if __name__ == "__main__":
    unittest.main()

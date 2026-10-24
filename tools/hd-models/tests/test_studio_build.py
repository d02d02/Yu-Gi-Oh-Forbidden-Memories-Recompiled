"""Tests for studio/build.py."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import recipe
from studio import build, package


class TestFlags(unittest.TestCase):
    def test_known_dest_str(self):
        args = {"clips": "idle", "rig": "humanoid"}
        out = build.flags(args)
        self.assertEqual(out, ["--clips", "idle", "--rig", "humanoid"])

    def test_known_dest_bool_true(self):
        args = {"no_center": True, "no_pbr": True}
        out = build.flags(args)
        self.assertEqual(out, ["--no-center", "--no-pbr"])

    def test_known_dest_bool_false_omitted(self):
        args = {"no_center": False, "keep_root_motion": True}
        out = build.flags(args)
        self.assertEqual(out, ["--keep-root-motion"])

    def test_list_dest_repeats_flag(self):
        args = {"follow": ["hip", "spine"]}
        out = build.flags(args)
        self.assertEqual(out, ["--follow", "hip", "--follow", "spine"])

    def test_sorted_order(self):
        args = {"scale": 1.0, "clips": "walk", "rig": "humanoid"}
        out = build.flags(args)
        self.assertEqual(out, ["--clips", "walk", "--rig", "humanoid", "--scale", "1.0"])

    def test_unknown_dest_raises(self):
        args = {"clips": "walk", "foo": "bar"}
        with self.assertRaises(ValueError) as cm:
            build.flags(args)
        self.assertIn("foo", str(cm.exception))


class TestCommand(unittest.TestCase):
    def test_basic_command(self):
        rec = {"pkg": {"name": "my_model"}}
        glb = "MODEL.glb"
        out_dir = "/tmp/out"
        cards = [0, 1]
        argv = build.command(rec, glb, out_dir, cards)
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[1], "-I")
        self.assertTrue(argv[2].endswith("new_native_mod.py"))
        self.assertIn(str(glb), argv)
        # cards
        idx = argv.index("--card")
        self.assertEqual(argv[idx + 1], "0")
        idx = argv.index("--card", idx + 1)
        self.assertEqual(argv[idx + 1], "1")
        self.assertIn("--out", argv)
        self.assertIn(str(out_dir), argv)
        self.assertIn("--id", argv)
        self.assertIn("my_model", argv)

    def test_default_name_from_glb_stem(self):
        rec = {}
        glb = Path("/path/to/hero_model.glb")
        argv = build.command(rec, glb, "/tmp/out", [0])
        idx = argv.index("--id")
        self.assertEqual(argv[idx + 1], "hero_model")

    def test_empty_cards_raises(self):
        rec = {"pkg": {"name": "mymod"}}
        with self.assertRaises(ValueError):
            build.command(rec, "m.glb", "/tmp/out", [])

    def test_invalid_name_raises(self):
        rec = {"pkg": {"name": "-bad"}}
        with self.assertRaises(ValueError):
            build.command(rec, "m.glb", "/tmp/out", [0])

    def test_no_flags_omits_separator(self):
        rec = {"pkg": {"name": "mymod"}}
        argv = build.command(rec, "m.glb", "/tmp/out", [0])
        self.assertNotIn("--", argv)

    def test_with_flags(self):
        rec = {"pkg": {"name": "mymod"}, "size": {"mode": "scale", "value": 1.0}}
        argv = build.command(rec, "m.glb", "/tmp/out", [0])
        idx = argv.index("--")
        self.assertEqual(argv[idx + 1:], ["--scale", "1.0"])


class TestHashTree(unittest.TestCase):
    def test_missing_folder_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope"
            self.assertEqual(build.hash_tree(missing), [])

    def test_hashes_files_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            (root / "x").mkdir(parents=True)
            (root / "x" / "a.txt").write_text("hello")
            (root / "b.txt").write_text("world")
            pairs = build.hash_tree(root)
            paths = [p for p, _ in pairs]
            self.assertEqual(paths, ["b.txt", "x/a.txt"])
            for _, digest in pairs:
                self.assertEqual(len(digest), 64)

    def test_sha256_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "out"
            root.mkdir(parents=True)
            (root / "a.txt").write_text("hello")
            pairs = build.hash_tree(root)
            expected = hashlib.sha256(b"hello").hexdigest()
            self.assertEqual(pairs, [("a.txt", expected)])


class TestRunner(unittest.TestCase):
    def test_real_runner_runs_clean(self):
        rc, text = build.real_runner(
            [sys.executable, "-c", "print('x')"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(text.strip(), "x")


def _out_of(argv):
    return Path(argv[argv.index("--out") + 1])


class TestBuildTwice(unittest.TestCase):
    def test_both_builds_ok(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            d = _out_of(argv)
            d.mkdir(parents=True, exist_ok=True)
            (d / "f.txt").write_text("same")
            return 0, "ok"

        with tempfile.TemporaryDirectory() as tmp:
            res = build.build_twice(
                {"pkg": {"name": "mymod"}}, "m.glb",
                Path(tmp) / "out", [0], runner=runner,
            )
        self.assertTrue(res["ok"])
        self.assertEqual(res["returncode"], 0)
        self.assertEqual(len(res["build_a"]), 1)
        self.assertEqual(res["build_b"], res["build_a"])
        self.assertEqual(res["text"], "ok")
        self.assertEqual(len(calls), 2)

    def test_first_build_fails_stops(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            return 1, "boom"

        with tempfile.TemporaryDirectory() as tmp:
            res = build.build_twice(
                {"pkg": {"name": "mymod"}}, "m.glb",
                Path(tmp) / "out", [0], runner=runner,
            )
        self.assertFalse(res["ok"])
        self.assertEqual(res["returncode"], 1)
        self.assertEqual(res["build_b"], [])
        self.assertEqual(res["text"], "boom")
        self.assertEqual(len(calls), 1)

    def test_second_build_fails(self):
        def runner(argv):
            d = _out_of(argv)
            d.mkdir(parents=True, exist_ok=True)
            if d.name == "b":
                return 2, "b-bad"
            (d / "f.txt").write_text("good")
            return 0, "ok"

        with tempfile.TemporaryDirectory() as tmp:
            res = build.build_twice(
                {"pkg": {"name": "mymod"}}, "m.glb",
                Path(tmp) / "out", [0], runner=runner,
            )
        self.assertFalse(res["ok"])
        self.assertEqual(res["returncode"], 2)
        self.assertEqual(res["text"], "ok")
        self.assertEqual(len(res["build_a"]), 1)
        self.assertEqual(res["build_b"], [])


def _ok_runner_same():
    """Fake runner that writes the same file twice (once per out dir)."""
    def runner(argv):
        d = _out_of(argv)
        d.mkdir(parents=True, exist_ok=True)
        (d / "f.txt").write_text("same")
        return 0, "text"

    return runner


def _ok_runner_diff():
    """Fake runner: second build writes different bytes than the first."""
    calls = {"n": 0}

    def runner(argv):
        calls["n"] += 1
        d = _out_of(argv)
        d.mkdir(parents=True, exist_ok=True)
        (d / "f.txt").write_text("a" if calls["n"] == 1 else "b")
        return 0, "text"

    return runner


def _fail_runner():
    """Fake runner that returns a nonzero code on the first build."""
    def runner(argv):
        return 1, "boom"

    return runner


class TestRunBuildS9(unittest.TestCase):
    def test_ok_same_builds_no_identity_finding(self):
        res = build.run_build_s9(
            {"pkg": {"name": "mymod"}}, "m.glb",
            Path(tempfile.mkdtemp()) / "out", [0],
            runner=_ok_runner_same(),
        )
        self.assertIn("build", res)
        self.assertTrue(res["build"]["ok"])
        self.assertEqual(res["build"]["returncode"], 0)
        self.assertFalse(any(f.get("id") == "S9.identical" for f in res["findings"]))
        self.assertNotIn("S9.build", {f.get("id") for f in res["findings"]})

    def test_ok_same_builds_passes_build_a_b_to_s9(self):
        b = tempfile.mkdtemp()
        res = build.run_build_s9(
            {"pkg": {"name": "mymod"}, "meta": {"author": "a"}},
            "m.glb",
            Path(b) / "out", [0],
            runner=_ok_runner_same(),
        )
        self.assertTrue(res["build"]["ok"])
        # Both builds hashed and passed into package.run_s9.
        self.assertEqual(res["build"]["build_a"], res["build"]["build_b"])
        self.assertFalse(any(f.get("id") == "S9.identical" for f in res["findings"]))

    def test_second_build_diff_produces_identity_finding(self):
        res = build.run_build_s9(
            {"pkg": {"name": "mymod"}}, "m.glb",
            Path(tempfile.mkdtemp()) / "out", [0],
            runner=_ok_runner_diff(),
        )
        self.assertTrue(res["build"]["ok"])
        ids = {f.get("id") for f in res["findings"]}
        self.assertIn("S9.identical", ids)
        self.assertNotIn("S9.build", ids)

    def test_first_build_fails_yields_s9_build_finding(self):
        res = build.run_build_s9(
            {"pkg": {"name": "mymod"}}, "m.glb",
            Path(tempfile.mkdtemp()) / "out", [0],
            runner=_fail_runner(),
        )
        self.assertFalse(res["build"]["ok"])
        findings = res["findings"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S9.build")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertIn("code 1", findings[0]["message"])
        self.assertIn("Open the stage", findings[0]["fix"])


if __name__ == "__main__":
    unittest.main()

"""The native model tools (tools/hd-models: native_convert.py, native_check.py, new_native_mod.py) on a rigged glb
made by the test (synthetic_gltf.py): converted without the disc, checked as the game checks it, made into a mod,
and, when MEMORIES_NATIVE_LOADER names the C registry test (CMake sets it), read back by the game's own loader.
The conversion tests are skipped without numpy and Pillow; the checker's run without them."""
import contextlib
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import native_check  # noqa: E402
import native_spec as spec  # noqa: E402

try:
    import numpy  # noqa: F401
    from PIL import Image
    import native_convert
    import new_native_mod
    import synthetic_gltf
    HAVE_CONVERTER = True
except ImportError:
    HAVE_CONVERTER = False


def quiet(function, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = function(*args)
    return status, out.getvalue()


def one_bone_hdm(clips=()):
    """A minimal valid HDM4: one bone, one triangle, a 1x1 texture, `clips` of 2 frames each."""
    words = [0] * 8
    words[0:8] = [struct.unpack("<I", b"HDM4")[0], 3, 3, 1, 1, 1, len(clips), 0]
    bone = [0xffffffff] + [0] * 15
    for k in (1, 6, 11):
        bone[k] = struct.unpack("<I", struct.pack("<f", 1.0))[0]
    blob = struct.pack("<8I", *words) + struct.pack("<16I", *bone)
    for i in range(3):
        blob += struct.pack("<8fI4f", float(i), 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
    blob += struct.pack("<3I", 0, 1, 2) + bytes([255, 255, 255, 255])
    for name in clips:
        blob += struct.pack("<32sIfII", name.encode(), 2, 30.0, 0, 0) + struct.pack("<14f", *([0] * 6 + [1]) * 2)
    return blob


class SpecTest(unittest.TestCase):
    def test_hdm4_checks_match_the_game(self):
        good = one_bone_hdm(["Idle"])
        info = spec.parse_hdm4(good)
        self.assertEqual((info["vertices"], info["bones"], [c["name"] for c in info["clips"]]), (3, 1, ["Idle"]))
        for data, why in ((good[:-4], "cut short in clip Idle"), (good + bytes(4), "1 words left over"),
                          (b"HDM3" + good[4:], "HDM1-3"), (b"XXXX" + good[4:], "not an HDM4")):
            with self.assertRaises(spec.Hdm4Error) as caught:
                spec.parse_hdm4(data)
            self.assertIn(why, str(caught.exception))

    def test_paths_stay_inside_the_mod(self):
        for good in ("a.hdm", "models/angel/model.json"):
            self.assertTrue(spec.paths_contained(good))
        for bad in ("", "/abs", "../up.hdm", "a/../b", "a//b", "a\\b", "C:x", "./a"):
            self.assertFalse(spec.paths_contained(bad), bad)

    def test_check_a_mod_as_the_game_reads_it(self):
        with tempfile.TemporaryDirectory() as root:
            mod = Path(root, "m")
            (mod / "pkg").mkdir(parents=True)
            (mod / "pkg" / "m.hdm").write_bytes(one_bone_hdm(["Idle", "Swing"]))
            (mod / "plain.hdm").write_bytes(one_bone_hdm())
            (mod / "pkg" / "model.json").write_text(json.dumps(
                {"model": "m.hdm", "clips": {"attack": "Swing", "dance": "Idle"}, "strike": {"attack": [1]}, "extra": 1}))
            (mod / "mod.json").write_text(json.dumps({"id": "m", "native_models": [
                {"cards": [364], "package": "pkg/model.json"}, {"model": 100, "file": "plain.hdm"},
                {"card": 5, "file": "../escape.hdm"}, {"card": 6, "file": "missing.hdm"}, {"file": "plain.hdm"}]}))
            status, out = quiet(native_check.main, [str(mod)])
            self.assertEqual(status, 1, out)
            self.assertIn("error: m: native_models[2]: ../escape.hdm is not a file inside the mod", out)
            self.assertIn("error: m: native_models[3]:", out)
            self.assertIn("missing.hdm cannot be read", out)
            self.assertIn("error: m: native_models[4]: names no card", out)
            self.assertIn("warning: m: native_models[0]: clips: \"dance\" is not an act", out)
            self.assertIn("warning: m: native_models[0]: model.json: \"extra\" is not read", out)
            self.assertIn("attack    -> Swing", out)
            self.assertIn("idle      -> Idle", out)  # not mapped: no default name in the model, so the first clip
            self.assertIn("blows of the attack at frames [1]", out)
            self.assertIn("for cards [364]", out)
            self.assertIn("for disc model 100", out)


@unittest.skipUnless(HAVE_CONVERTER, "numpy and Pillow are needed to convert")
class ConvertTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.glb = self.root / "knight.glb"
        synthetic_gltf.write(self.glb)

    def tearDown(self):
        self.tmp.cleanup()

    def convert(self, *extra):
        status, out = quiet(native_convert.main, [str(self.glb), str(self.root / "pkg"), *extra])
        self.assertEqual(status, 0, out)
        package = json.loads((self.root / "pkg" / "model.json").read_text())
        data = (self.root / "pkg" / "model.hdm").read_bytes()
        return package, data, spec.parse_hdm4(data), out

    def floats(self, data, word, count):
        return struct.unpack_from(f"<{count}f", data, word * 4)

    def test_package_without_the_disc(self):
        package, data, info, out = self.convert()
        self.assertEqual(package["model"], "model.hdm")
        self.assertEqual(package["clips"], {"idle": "Idle", "enter": "Idle", "attack": "Sword_Attack", "hit": "Idle",
                                            "destroyed": "Death01", "win": "Victory", "guard": "Idle"})
        self.assertEqual(package["converter"]["rig"], "ue")
        self.assertEqual(package["converter"]["root"], "pelvis")
        self.assertTrue(9 <= package["strike"]["attack"][0] <= 12, package["strike"])  # the arm is fastest at 0.3-0.4 s
        self.assertEqual((info["bones"], len(info["clips"]), info["vertices"]), (6, 5, 51))
        self.assertAlmostEqual(info["high"][1], 300.0, places=3)  # the soles 300 below the hips, y down
        self.assertAlmostEqual(info["low"][1], -225.0, places=3)  # the sword's tip, 0.75 m above the hips
        # the walk's 1 m of travel taken out: the root (pelvis, no joint above it) ends where it stood at rest
        walk = next(c for c in info["clips"] if c["name"] == "Walk")
        idle = next(c for c in info["clips"] if c["name"] == "Idle")
        pelvis = info["parents"].index(-1)
        rest = self.floats(data, idle["offset"] + pelvis * 7, 3)
        last = self.floats(data, walk["offset"] + ((walk["frames"] - 1) * info["bones"] + pelvis) * 7, 3)
        for c in range(3):
            self.assertAlmostEqual(rest[c], last[c], places=3)
        # every UV inside the texture; the sword follows the hand only
        hand = 3
        for k in range(info["vertices"]):
            base = info["vertex_offset"] + k * 13
            u, v = self.floats(data, base + 6, 2)
            self.assertTrue(-1e-6 <= u <= 1 + 1e-6 and -1e-6 <= v <= 1 + 1e-6, (k, u, v))
        for k in range(info["vertices"] - 3, info["vertices"]):
            joints = struct.unpack_from("<I", data, (info["vertex_offset"] + k * 13 + 8) * 4)[0]
            self.assertEqual(joints & 255, hand)
            self.assertAlmostEqual(self.floats(data, info["vertex_offset"] + k * 13 + 9, 1)[0], 1.0)
        # one texture for two materials: the red texture and the blue colour, side by side
        colours = set(Image.open(self.root / "pkg" / "base.png").convert("RGBA").getdata())
        self.assertIn((220, 30, 30, 255), colours)
        self.assertIn((0, 0, 255, 255), colours)
        self.assertIn("2 materials packed into one", out)
        status, out = quiet(native_check.main, [str(self.root / "pkg" / "model.json")])
        self.assertEqual(status, 0, out)
        self.assertIn("0 warnings", out)

    def test_sizes_and_choices(self):
        package, _, info, _ = self.convert("--height", "560", "--clips", "Idle,Sword_Attack", "--texture-max", "16")
        self.assertAlmostEqual(info["high"][1] - info["low"][1], 560.0, places=2)
        self.assertEqual([c["name"] for c in info["clips"]], ["Idle", "Sword_Attack"])
        self.assertEqual(package["clips"]["destroyed"], "Idle")  # no death clip kept: the idle
        self.assertLessEqual(max(Image.open(self.root / "pkg" / "base.png").size), 16)
        status, out = quiet(native_convert.main, [str(self.glb), str(self.root / "x"), "--clips", "Nope"])
        self.assertEqual(status, 1)
        self.assertIn("no clip Nope", out)

    def test_new_mod_and_the_game_reads_it(self):
        mod = self.root / "my-knight"
        status, out = quiet(new_native_mod.main, [str(self.glb), "--card", "364", "--out", str(mod), "--license", "CC0-1.0"])
        self.assertEqual(status, 0, out)
        manifest = json.loads((mod / "mod.json").read_text())
        self.assertEqual(manifest["id"], "my-knight")
        self.assertEqual(manifest["native_models"], [{"cards": [364], "package": "models/knight/model.json"}])
        self.assertEqual(json.loads((mod / "models/knight/model.json").read_text())["license"], "CC0-1.0")
        status, out = quiet(new_native_mod.main, [str(self.glb), "--card", "1", "--out", str(mod)])  # more cards, one entry
        self.assertEqual(status, 0, out)
        self.assertEqual(json.loads((mod / "mod.json").read_text())["native_models"],
                         [{"cards": [1, 364], "package": "models/knight/model.json"}])
        loader = os.environ.get("MEMORIES_NATIVE_LOADER")
        if not loader:
            self.skipTest("MEMORIES_NATIVE_LOADER is not set (CMake sets it to the C registry test)")
        run = subprocess.run([loader, "--load", str(mod / "models/knight/model.json")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        fields = dict(item.split("=") for item in run.stdout.split()[1:])
        self.assertEqual((fields["vertices"], fields["bones"], fields["clips"]), ("51", "6", "5"))
        self.assertEqual((fields["attack"], fields["idle"]), ("2", "1"))  # clip index + 1: Sword_Attack, Idle
        self.assertEqual(fields["strikes"], "1")
        self.assertEqual(float(fields["ground"]), 300.0)
        size = Image.open(mod / "models/knight/base.png").size
        self.assertEqual(fields["texture"], f"{size[0]}x{size[1]}")


if __name__ == "__main__":
    unittest.main()

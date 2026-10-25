import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import unittest, json, tempfile, subprocess, struct
from synthetic_gltf import Builder



class TestProceduralNoClip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.glb = self.root / "model.glb"
        # Build a minimal glb with a skin but no animations
        b = Builder()
        # Simple triangle geometry
        positions = [(0,0,0), (1,0,0), (0,1,0)]
        normals = [(0,0,1)]*3
        uvs = [(0,0), (1,0), (0,1)]
        indices = [0,1,2]
        # dummy buffer view placeholder
        b.view(b"\x00\x00\x00\x00")
        # create accessors for geometry
        pos_acc = b.accessor(positions, "VEC3")
        n_acc = b.accessor(normals, "VEC3")
        uv_acc = b.accessor(uvs, "VEC2")
        idx_acc = b.accessor(indices, "SCALAR", 5125)
        primitive = {"attributes": {"POSITION": pos_acc, "NORMAL": n_acc, "TEXCOORD_0": uv_acc}, "indices": idx_acc, "material": 0}
        # nodes: armature with a child joint
        nodes = [{"name": "Armature", "children": [1]}, {"name": "joint", "translation": [0,0,0], "mesh": 0}]
        meshes = [{"primitives": [primitive]}]
        # skin referencing the joint
        ibm = [[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]]
        skin = {"joints": [1], "inverseBindMatrices": b.accessor(ibm, "MAT4")}
        images = []
        doc = {
            "asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
            "nodes": nodes, "meshes": meshes, "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1,1,1,1]}}],
            "skins": [skin], "textures": [], "images": images, "buffers": [{"byteLength": 0}], "bufferViews": b.views, "accessors": b.accessors,
        }
        # finalize buffer length
        while len(b.buf) % 4:
            b.buf.append(0)
        doc["buffers"][0]["byteLength"] = len(b.buf)
        text = json.dumps(doc).encode()
        text += b" " * (-len(text) % 4)
        body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(b.buf), 0x004E4942) + bytes(b.buf)
        with open(self.glb, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)


        self.out = self.root / "out"
        self.out.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_procedural_idle_creates_one_clip(self):
        # Run converter with procedural idle flag
        cmd = [sys.executable, str(Path(__file__).parent.parent / "native_convert.py"), str(self.glb), str(self.out), "--procedural", "idle=idle"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Parse generated HDM4 info
        hdm_path = self.out / "model.hdm"
        data = hdm_path.read_bytes()
        from native_spec import parse_hdm4
        info = parse_hdm4(data)
        self.assertEqual(len(info["clips"]), 1)
        # Check acts mapping in generated JSON
        pkg_path = self.out / "model.json"
        pkg = json.loads(pkg_path.read_text())
        self.assertEqual(pkg["clips"].get("idle"), "proc_idle")
        # Verify notes line contains expected description
        notes_path = self.out / ".."  # notes are not saved; they are in console output; check stdout
        self.assertIn("idle: procedural idle over bind (30 frames)", result.stdout)

if __name__ == '__main__':
    unittest.main()

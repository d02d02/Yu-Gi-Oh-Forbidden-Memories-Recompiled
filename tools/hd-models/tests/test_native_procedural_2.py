import sys
import unittest
import tempfile
import pathlib
import subprocess
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from synthetic_gltf import write as write_glb

class TestProceduralDeterminism(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.glb = self.root / "model.glb"
        write_glb(str(self.glb))
        self.out1 = self.root / "out1"
        self.out2 = self.root / "out2"
        self.out1.mkdir()
        self.out2.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _run_convert(self, out_path):
        cmd = [sys.executable, str(pathlib.Path(__file__).parent.parent / "native_convert.py"),
               str(self.glb), str(out_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_deterministic_output(self):
        # Run conversion twice and compare HDM output
        self._run_convert(self.out1)
        self._run_convert(self.out2)
        data1 = (self.out1 / "model.hdm").read_bytes()
        data2 = (self.out2 / "model.hdm").read_bytes()
        self.assertEqual(data1, data2)

if __name__ == '__main__':
    unittest.main()

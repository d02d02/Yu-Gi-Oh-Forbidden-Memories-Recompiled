import unittest
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('resolutions', str(Path(__file__).parents[1] / 'studio' / 'resolutions.py'))
resolutions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolutions)

class TestResolutionsOffered(unittest.TestCase):
    def test_known_ids(self):
        for fid in ["S2.map", "S1.skin", "S2.skin"]:
            with self.subTest(fid=fid):
                finding = {"id": fid}
                self.assertEqual(resolutions.offered(finding), ["provide.file"])
    def test_unknown_id(self):
        finding = {"id": "X.unknown"}
        self.assertEqual(resolutions.offered(finding), [])
    def test_stable_across_calls(self):
        finding = {"id": "S2.map"}
        first = resolutions.offered(finding)
        second = resolutions.offered(finding)
        self.assertEqual(first, second)

if __name__ == "__main__":
    unittest.main()

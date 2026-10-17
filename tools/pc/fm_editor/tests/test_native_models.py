"""A mod's "native_models" (native_models.py, src/pc/render/native_registry.c): the entries' checks the port makes,
through validate().

    python -m unittest discover -s tools/pc/fm_editor/tests -t tools/pc -p test_native_models.py
"""
import unittest

from fm_editor import validate
from fm_editor.model import Project
from fm_editor.tests.test_data import fixture


def issues(entries, files=(), settings=()):
    project = Project(fixture().game())
    project.other["native_models"] = entries
    project.info.settings = [{"key": key, "type": "bool", "default": 1} for key in settings]
    for name in files:
        project.files[name] = b""
    return [str(i) for i in validate.validate(project) if "native_models" in i.where]


class NativeModelsTest(unittest.TestCase):
    def test_good_entries(self):
        self.assertEqual(issues([{"cards": [1, 2], "package": "angel/model.json"}, {"model": 363, "file": "a.hdm"},
                                 {"card": 3, "file": "a.hdm", "setting": "dragon"}],
                                files=("angel/model.json", "a.hdm"), settings=("dragon",)), [])

    def test_what_the_port_refuses(self):
        found = issues([{"cards": [1]}, {"cards": [1], "package": "p/model.json", "file": "a.hdm"},
                        {"card": 1, "file": "../a.hdm"}, {"file": "a.hdm"}, {"card": 1, "file": "missing.hdm"}, 7],
                       files=("a.hdm", "p/model.json"))
        self.assertIn("error: Mod info: native_models[0]: needs a \"package\" (a model.json) or a \"file\" (an .hdm model), "
                      "one of the two", found)
        self.assertTrue(any(f.startswith("error: Mod info: native_models[1]: needs") for f in found))
        self.assertIn("error: Mod info: native_models[2]: ../a.hdm is not a file inside the mod", found)
        self.assertTrue(any(f.startswith("error: Mod info: native_models[3]: names no card") for f in found))
        self.assertIn("error: Mod info: native_models[4]: missing.hdm is not in the mod: the monster keeps its disc model", found)
        self.assertTrue(any(f.startswith("error: Mod info: native_models[5]: needs") for f in found))
        self.assertIn("error: Mod info: native_models: native_models is a list: [{\"cards\": [364], \"package\": "
                      "\"angel/model.json\"}]", issues({"cards": [1]}))
        self.assertTrue(any("at most 64 native models" in f for f in issues([{"card": 1, "file": "a.hdm"}] * 65, files=("a.hdm",))))

    def test_what_the_port_notes(self):
        found = issues([{"cards": [0, True, 2], "file": "a.hdm"}, {"card": 2, "file": "a.hdm", "setting": "nope"},
                        {"card": 60000, "file": "a.hdm"}, {"cards": [1], "model": -4, "file": "a.hdm"}], files=("a.hdm",))
        self.assertIn("warning: Mod info: native_models[0]: 0 is not a card id (1 to 65535): left out", found)
        self.assertIn("warning: Mod info: native_models[0]: True is not a card id (1 to 65535): left out", found)
        self.assertIn("warning: Mod info: native_models[1]: \"setting\" 'nope' is not one of the mod's settings: the entry is "
                      "always used", found)
        self.assertIn("warning: Mod info: native_models[1]: card 2 is also in native_models[0]: this later one is drawn", found)
        self.assertIn("warning: Mod info: native_models[2]: card 60000 is neither a card of the game nor one this mod adds", found)
        self.assertIn("warning: Mod info: native_models[3]: \"model\" is a disc model id (the card id - 1): left out", found)
        self.assertFalse(any(f.startswith("error") for f in found), found)


if __name__ == "__main__":
    unittest.main()

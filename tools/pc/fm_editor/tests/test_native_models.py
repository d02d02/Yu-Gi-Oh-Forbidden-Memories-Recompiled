"""A mod's "native_models" (native_models.py, src/pc/render/native_registry.c): the entries' checks the port makes,
through validate().

    python -m unittest discover -s tools/pc/fm_editor/tests -t tools/pc -p test_native_models.py
"""
import json
import tempfile
import unittest
from pathlib import Path

from fm_editor import native_models, validate
from fm_editor.model import Project
from fm_editor.tests.test_data import fixture
from fm_editor.tests.test_gui import GuiCase


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


def make_package(root, name="angel", meta=None):
    folder = Path(root) / name
    folder.mkdir(parents=True)
    meta = {"format": 1, "model": "model.hdm", "name": "Angel", "author": "A. Modeller", "license": "CC-BY 4.0"}         if meta is None else meta
    (folder / "model.json").write_text(json.dumps(meta), encoding="utf-8")
    (folder / "model.hdm").write_bytes(b"HDM4")
    (folder / "base.png").write_bytes(b"png")
    (folder / "notes.txt").write_bytes(b"left out")
    return folder / "model.json"


class EditingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Project(fixture().game())

    def test_parse_cards(self):
        self.assertEqual(native_models.parse_cards("364, 1 2;364"), [364, 1, 2])
        self.assertEqual(native_models.parse_cards(""), [])
        for bad in ("0", "65536", "x", "-3", "1.5"):
            with self.assertRaises(ValueError, msg=bad):
                native_models.parse_cards(bad)

    def test_add_set_remove(self):
        p = self.project
        index = native_models.add_package(p, make_package(self.tmp.name), [364])
        self.assertEqual(index, 0)
        self.assertEqual(p.other["native_models"], [{"cards": [364], "package": "models/angel/model.json"}])
        self.assertEqual(sorted(p.files), ["models/angel/base.png", "models/angel/model.hdm", "models/angel/model.json"])
        self.assertEqual(native_models.about(p, p.other["native_models"][0])["license"], "CC-BY 4.0")
        self.assertEqual(issues_of(p), [])
        # The same folder name again does not overwrite the first.
        second = native_models.add_package(p, make_package(Path(self.tmp.name) / "b"), [1])
        self.assertEqual(p.other["native_models"][second]["package"], "models/angel-2/model.json")
        native_models.set_cards(p, 0, [2, 3])
        self.assertEqual(p.other["native_models"][0], {"cards": [2, 3], "package": "models/angel/model.json"})
        native_models.remove_entry(p, 0)
        self.assertFalse(any(n.startswith("models/angel/") for n in p.files))
        self.assertTrue(any(n.startswith("models/angel-2/") for n in p.files))
        native_models.remove_entry(p, 0)
        self.assertNotIn("native_models", p.other)
        self.assertEqual(p.files, {})

    def test_bad_packages(self):
        p = self.project
        root = Path(self.tmp.name)
        for meta in ({"format": 1}, {"model": "gone.hdm"}, []):
            with self.assertRaises(ValueError, msg=meta):
                native_models.add_package(p, make_package(root, f"p{len(str(meta))}", meta))
        with self.assertRaises(ValueError):
            native_models.add_package(p, root / "nothing" / "model.json")
        self.assertEqual((p.other.get("native_models"), p.files), (None, {}))


def issues_of(project):
    return [str(i) for i in validate.validate(project) if "native_models" in i.where]


class NativeModelsTabTest(GuiCase):
    def test_tab_adds_edits_and_removes(self):
        app, tab = self.app, self.app.native
        with tempfile.TemporaryDirectory() as tmp:
            package = make_package(tmp)
            app.notebook.select(tab)
            app.update()
            self.assertEqual(tab.tree.get_children(), ())
            self.assertTrue(tab.use_package(package, [364]))
            self.assertEqual(tab.tree.get_children(), ("0",))
            self.assertEqual(tab.tree.item("0", "values")[2], "364")
            self.assertEqual(tab.heading.cget("text"), "Angel")
            self.assertIn("CC-BY 4.0", tab.about.cget("text"))
            self.assertTrue(app.dirty)
            tab.cards.set("1, 364")
            tab.apply()
            self.assertEqual(app.project.other["native_models"][0]["cards"], [1, 364])
            tab.cards.set("nope")
            tab.apply()
            self.assertEqual(app.project.other["native_models"][0]["cards"], [1, 364])
            self.assertIn("not a card id", tab.status.cget("text"))
            tab.remove()
            self.assertEqual(tab.tree.get_children(), ())
            self.assertNotIn("native_models", app.project.other)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recipe   # noqa: E402
from studio import resolutions, state   # noqa: E402
from studio.session import Session   # noqa: E402


class Holder:
    STAND_IN_KIND = Session.STAND_IN_KIND

    def __init__(self):
        self.studio = state.Studio()


class UseStandIn(unittest.TestCase):
    def test_idle_goes_to_the_converter_and_the_report(self):
        h = Holder()
        Session.use_stand_in(h, "idle")
        self.assertEqual(recipe.convert_args(h.studio.recipe)["procedural"], ["idle=idle"])
        self.assertEqual([e["kind"] for e in resolutions.stand_ins(h.studio.recipe)], ["fallback"])

    def test_attack_is_a_lunge_with_its_own_value(self):
        h = Holder()
        Session.use_stand_in(h, "attack")
        self.assertEqual(recipe.convert_args(h.studio.recipe)["procedural"], ["attack=lunge"])
        self.assertEqual(h.studio.recipe["resolutions"][0]["value"], "attack")

    def test_every_act_has_a_kind(self):
        import native_convert
        self.assertEqual(set(Session.STAND_IN_KIND), set(native_convert.spec.ACTS))


if __name__ == "__main__":
    unittest.main()

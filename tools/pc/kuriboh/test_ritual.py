"""Does a ritual spell fuse with a monster of its set into the ritual monster? (the Kuriboh mod's rituals)

    python tools/pc/kuriboh/test_ritual.py <mods dir> [spell monster result]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yfm_control import Game  # noqa: E402

mods = sys.argv[1]
spell, monster, result = (int(x) for x in sys.argv[2:5]) if len(sys.argv) > 4 else (671, 5, 360)   # Zera Ritual + Ryu-kishin = Zera the Mant
with Game(mods_dir=mods, settings={"mod.kuriboh": 1}) as g:
    g.goto("duel", opponent=1, deck=[monster, spell])
    g.duel_ready(before_deal=lambda game: game.arrange_deck(0, [monster, spell]))
    g.step(120)
    hand = [c and c["id"] for c in g.duel()[0]["hand"]]
    print("hand:", hand)
    slots = [hand.index(monster), hand.index(spell)]
    g.fuse(slots, face_up=True)
    g.step(120)
    print("monsters:", [c and c["id"] for c in g.duel()[0]["monsters"]], "hand now:", [c and c["id"] for c in g.duel()[0]["hand"]], "expected", result)

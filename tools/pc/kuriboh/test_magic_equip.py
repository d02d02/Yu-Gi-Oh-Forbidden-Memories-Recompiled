"""A magic card the mod lets equip: combined with its monster in the hand, the monster gets its bonus.

    python tools/pc/kuriboh/test_magic_equip.py <mods dir> [magic monster bonus]     (default 338 58 2500)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yfm_control import Game, RECORD_SIZE  # noqa: E402

mods = sys.argv[1]
magic, monster, bonus = (int(x) for x in sys.argv[2:5]) if len(sys.argv) > 4 else (338, 58, 2500)
with Game(mods_dir=mods, settings={"mod.kuriboh": 1}) as g:
    g.goto("duel", opponent=1, deck=[monster, magic])
    g.duel_ready(before_deal=lambda game: game.arrange_deck(0, [monster, magic]))
    g.step(120)
    hand = [c and c["id"] for c in g.duel()[0]["hand"]]
    print("hand:", hand)
    g.fuse([hand.index(magic), hand.index(monster)], face_up=True)
    g.step(300)
    raw = g.peek("D_801A7AD8", 30 * RECORD_SIZE)
    for i in range(30):
        cid, atk, dfd, mod, terr, flags = struct.unpack_from("<hhhhhH", raw, i * RECORD_SIZE + 0x0C)
        if cid == monster and flags & 0x8000:
            print(f"record {i}: card {cid} attack {atk} stat_modifier {mod} (expected +{bonus})")
    print("monsters:", [c and c["id"] for c in g.duel()[0]["monsters"]], "hand now:", [c and c["id"] for c in g.duel()[0]["hand"]])

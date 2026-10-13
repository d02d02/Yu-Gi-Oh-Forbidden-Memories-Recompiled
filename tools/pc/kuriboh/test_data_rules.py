"""The Kuriboh rules that are data in the port: a card's own terrain bonus and the deck limit per card.

    python tools/pc/kuriboh/test_data_rules.py <mods dir holding the import as "kuriboh">

Terrain: a duel on terrain 1 with a deck of Pumpking (listed on Forest) and on terrain 2 with Summoned Skull (listed on
Wasteland) and a card that is not listed; the record's terrain_modifier is read, with the mod off and on.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yfm_control import Game, RECORD_SIZE  # noqa: E402

mods = sys.argv[1]


def modifier(card, terrain, enabled):
    with Game(mods_dir=mods, settings={"mod.kuriboh": enabled}) as g:
        g.goto("duel", opponent=1, deck=[card])
        g.duel_ready(before_deal=lambda game: game.poke("gDuel_bTerrain", bytes([terrain])))
        g.step(60)
        raw = g.peek("D_801A7AD8", 30 * RECORD_SIZE)
        found = set()
        for i in range(30):
            cid, atk, dfd, mod, terr, flags = struct.unpack_from("<hhhhhH", raw, i * RECORD_SIZE + 0x0C)
            if cid == card and flags & 0x8000:
                found.add(terr)
        return sorted(found)


for card, terrain, name in ((99, 1, "Pumpking on Forest"), (22, 2, "Summoned Skull on Wasteland"), (4, 2, "card 4 on Wasteland (not listed)")):
    print(f"{name}: mod off {modifier(card, terrain, 0)}, on {modifier(card, terrain, 1)}")

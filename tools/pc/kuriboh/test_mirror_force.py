"""Mirror Force (card 681): when it springs, the attacker's other monsters leave the field with it.

    python tools/pc/kuriboh/test_mirror_force.py <mods dir holding the import as kuriboh>

The player sets Mountain (332, a harmless magic card, face down) for two turns so the opponent's AI builds a field of several monsters, then sets 681 and ends
turns. Prints both rows each turn: the opponent's row empties on the turn the trap springs (and not without the effect)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yfm_control import Game, RECORD_SIZE  # noqa: E402


def rows(g):
    raw = g.peek("D_801A7AD8", 30 * RECORD_SIZE)
    mine, theirs, traps = [], [], []
    for i in range(30):
        card, _, _, _, _, flags = struct.unpack_from("<hhhhhH", raw, i * RECORD_SIZE + 0x0C)
        if not flags & 0x8000:
            continue
        side, at = divmod(i, 15)
        if 5 <= at < 10:
            (theirs if side else mine).append(card)
        elif at >= 10 and not side:
            traps.append(card)
    return mine, theirs, traps


mods = sys.argv[1]
with Game(mods_dir=mods, settings={"mod.kuriboh": 1}) as g:
    g.goto("duel", opponent=1, deck=[681, 332])
    g.duel_ready()
    g.step(120)
    best = 0
    swept = False
    for turn in range(8):
        hand = [c and c["id"] for c in g.duel()[0]["hand"]]
        want = 332 if turn < 2 else 681
        g.play_card(hand.index(want) if want in hand else 0, face_up=False)
        before = rows(g)
        g.end_turn()
        after = rows(g)
        print(f"turn {turn}: before {before} -> after {after}")
        best = max(best, len(after[1]))
        if len(before[2]) and not after[1] and best > 1:
            swept = True
        print("   lp", [s["lp"] for s in g.duel()], "over", g.duel_over(), "phase", g.phase())
        if g.duel_over():
            break
    print("swept a row of several monsters:", swept)

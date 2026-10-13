"""Write GameShark cheats for DuckStation that set up the Kuriboh test scenarios (notes/kuriboh-test-plan.md).

    python tools/pc/kuriboh/make_cheats.py <out folder> [card ids for "deck of one card" cheats...]

Writes <out>/cheats.txt (name, then its codes: paste into DuckStation's cheat editor) and
<out>/SLUS-01411.cht (the same in DuckStation's cheat file format, best effort).
Addresses are PS1 RAM addresses; a GameShark code writes at "30aaaaaa 00vv" (8 bit) or "80aaaaaa vvvv" (16 bit),
"50..." repeats the next code.
"""
import sys
from pathlib import Path

CHEST = 0x801D0250          # gLibrary_abCardChest: one byte a card id - 1
PLAYER_DECK = 0x801D0200    # gDuel_awPlayerDeck: 40 u16
SHUFFLED = 0x80177F94       # gDuel_awPlayerDeckShuffle: the order the duel deals
TERRAIN = 0x8009B364        # gDuel_bTerrain
UNLOCKED = 0x801D06F4       # gFreeDuel_dwUnlockedDuelists

cheats = []


def byte(address, value):
    return f"30{address & 0xFFFFFF:06X} {value:04X}"


def half(address, value):
    return f"80{address & 0xFFFFFF:06X} {value:04X}"


# every card x3 in the chest: slide codes, 240 cards a block
lines = []
for start in range(0, 722, 240):
    count = min(240, 722 - start)
    lines += [f"5000{count:02X}01 0000", byte(CHEST + start, 3)]
cheats.append(("Chest: every card x3", lines))
cheats.append(("Chest: card 679 (Novox's Prayer Ritual) x3", [byte(CHEST + 679 - 1, 3)]))
cheats.append(("Chest: Exodia pieces x1", [byte(CHEST + c - 1, 1) for c in range(17, 22)]))
for number, name in enumerate(("Forest", "Wasteland", "Mountain", "Sogen", "Umi", "Yami"), 1):
    cheats.append((f"Terrain {number}: {name} (turn on before the duel starts)", [byte(TERRAIN, number)]))
cheats.append(("Hand: the five Exodia pieces (turn on during the shuffle, off after the deal)",
               [half(SHUFFLED + 2 * i, 17 + i) for i in range(5)]))
cheats.append(("Free Duel: first eight duelists not unlocked (turn on after the duel has started)", [byte(UNLOCKED, 0)]))
# the campaign's extra duelists: the mode byte and the opponent id the dialogue's id 39 + k becomes (Text_StartCampaignDuel)
MODE = 0x801CF310
OPPONENT = 0x8009B361
for k in range(1, 16):
    cheats.append((f"Extra duelist {39 + k}: mode {k}, opponent {k} (on before the duel starts)", [byte(MODE, k), byte(OPPONENT, k)]))
for card in [int(a) for a in sys.argv[2:]] or [99, 22, 4]:
    cheats.append((f"Deck: forty of card {card}", [half(PLAYER_DECK + 2 * i, card) for i in range(40)]))

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
text, cht = [], []
for name, codes in cheats:
    text.append(f"# {name}")
    text += codes
    text.append("")
    cht.append(f"[{name}]")
    cht.append("Type = Gameshark")
    cht.append("Activation = EndFrame")
    cht += [f"Code = {c}" for c in codes]
    cht.append("")
(out / "cheats.txt").write_text("\n".join(text), encoding="utf-8")
(out / "SLUS-01411.cht").write_text("\n".join(cht), encoding="utf-8")
print(f"{len(cheats)} cheats in {out}")

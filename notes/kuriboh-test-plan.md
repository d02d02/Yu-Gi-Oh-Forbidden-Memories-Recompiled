# Kuriboh reproduction: test plan (what to run, what to capture)

Oracle = the real Kuriboh ISO in DuckStation. Subject = the port with `kuriboh` (data, imported) and
`kuriboh-rules` (code) enabled. For each rule, read the same memory value in both and compare.
Dumps go in `C:\Users\mdahh\OneDrive\Desktop\Perso\hacking\ygo\dumps\` (outside the repo).

## Port side (PowerShell, from the kuriboh worktree)

    cd C:\Users\mdahh\OneDrive\Desktop\Perso\hacking\Yu-Gi-Oh-Forbidden-Memories-Recompiled-kuriboh
    python tools/pc/fm_editor import "C:\Users\mdahh\OneDrive\Desktop\Perso\YGOFM\YFM MOD Kuriboh\YFM MOD Kuriboh\YFM MOD KURIBOH.iso" --game game\ygofm-orig-usa.bin --id kuriboh -o tmp\kuriboh\port
    python tools/pc/kuriboh/gen_rules.py "C:\Users\mdahh\OneDrive\Desktop\Perso\YGOFM\YFM MOD Kuriboh\YFM MOD Kuriboh\YFM MOD KURIBOH.iso"
    python tools/pc/build_game32.py
    python tools/pc/kuriboh/test_terrain.py 99 1
    .\play.bat        # F10 > Game > Mods: tick kuriboh and kuriboh-rules, restart

Copy `tmp\kuriboh\port` to `Documents\My Games\YFM Re-Decomp\mods\kuriboh` to install the data mod.

## DuckStation side (Kuriboh ISO)

Memory: Debug > CPU Debugger > Memory tab (or Memory Editor); addresses below are PS1 addresses.
RAM dump: Debug > Dump RAM (2 MB). Save a save state at every setup so it can be repeated.

| id | Setup | Capture |
|---|---|---|
| T1 terrain | a duel on a Forest, Wasteland, Mountain, Meadow, Sogen or Umi field (the field art tells), with a monster from the list on your side (Forest: Pumpking, B. Dragon Jungle King, Crab Turtle; Wasteland: Summoned Skull, Curse of Dragon, Tri-horned Dragon). Summon it face up | RAM dump `T1_<terrain>_<card>.bin`; note the terrain and the card |
| T2 yami | a duel on a Yami field (dark) with any monster face up (note which types lose attack: the -500 to -700 change applies to the field's penalised types) | RAM dump `T2_yami.bin` (the penalty -500 to -700) |
| T3 deck limit | Build Deck with card 679 (Novox's Prayer Ritual) in the chest: write 3 to `801D04F6` first; try to add it | screenshot of the attempt + RAM dump `T3_deck_limit.bin`; say whether it was added |
| T4 copy display | the same screen, a normal card at 3 copies | screenshot (count colour) |
| T5 exodia | a duel with Exodia pieces: write 17,18,19,20,21 (u16 each) into `801D0200`..., 40 entries, before the duel starts | RAM dump when the hand shows the pieces `T5_exodia_hand.bin`, and a dump on the result screen `T5_exodia_result.bin` |
| T6 drops | win a duel (any), at the drop screen | screenshot of the card won; dump `T6_drop.bin`; repeat 3 times if you can and list the cards |
| T7 frame colours | Library or Build Deck viewing cards of each class (Effect, Union, Ritual...) | screenshots of one card per class |
| T8 modes | (only if the variant ISOs matter) the same dumps as before on `YFM KURIBOH GOD (IMPOSIBLE).iso` and the two Hard ISOs: a Free Duel against Simon Muran | `GOD_1.bin`, `HARD_1.bin`, `HARD5_1.bin` |

## What I read from each

T1/T2: the 30 card records at `801A7AD8` (28 bytes each; `+0x0C` card id, `+0x0E` attack, `+0x14`
terrain modifier, `+0x18..` flags) and the terrain byte `8009B364`. T3: deck counts at the Build Deck
state and the chest at `801D0250` (+card id - 1). T5: the Exodia result entries (their address comes from the hook at `0x801CFF3C`; I will work it out from the dump).

## DuckStation setup with cheats (no cards needed)

`python tools/pc/kuriboh/make_cheats.py <out> 99 22 4 217` writes GameShark cheats (`cheats.txt` to paste,
`SLUS-01411.cht` for DuckStation's cheat folder) into `ygo/cheats/`. Cheats: every card x3 in the chest,
card 679 x3, terrain 1-6 forced, "Deck: forty of card N" (any N), the five Exodia pieces dealt as the hand,
and "first eight duelists not unlocked".

Scenarios (Free Duel against Simon Muran, any duelist works), each ends with Debug > Dump RAM:

| File | Turn on | Do | Expect |
|---|---|---|---|
| `T1_forest_99.bin` | Deck: forty of card 99, Terrain 1 (before the duel starts) | start the duel, summon a card face up | terrain_modifier +500 |
| `T1_wasteland_22.bin` | Deck: forty of 22, Terrain 2 | the same | +500 |
| `T1_wasteland_4.bin` | Deck: forty of 4, Terrain 2 | the same | the type bonus only |
| `T2_yami_217.bin` | Deck: forty of 217, Terrain 6 | the same | Yami bonus or penalty |
| `T3_deck_limit.bin` | Chest: card 679 x3 | Build Deck, try to add 679 | refused; screenshot too |
| `T5_exodia_*.bin` | Hand: the five Exodia pieces (on at the deck screen, off once dealt) | the duel ends by Exodia; dump on the result screen | the mod's changed Exodia result |
| `T6_unique_drop.bin` | Free Duel: first eight duelists not unlocked, after the duel has started | win (Exodia is quickest) | the drop is Kuriboh (card 58) for Simon |

Install: copy `SLUS-01411.cht` into DuckStation's `cheats` folder (Settings or Tools > Open Data Directory),
restart the game and tick the cheats in the Cheats menu; or paste a cheat's lines in Cheats > Add Cheat.
Written from memory of the format: if a cheat does nothing, write the same value in the Memory tab.

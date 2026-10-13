# Kuriboh reproduction: test plan (compacted 2026-10-13)

Oracle = the real Kuriboh ISO in DuckStation; subject = the port with `kuriboh` (imported data). Compare the same memory value in both. Dumps in `...\hacking\ygo\dumps\` (outside the repo).

Port side (from the worktree): `python tools/pc/fm_editor import "<iso>" --game game\ygofm-orig-usa.bin --id kuriboh -o tmp\kuriboh\port`; `python tools/pc/build_game32.py`; `python tools/pc/kuriboh/test_data_rules.py <mods dir>` (the old `gen_rules.py`/`test_terrain.py` went with `kuriboh-rules`); copy `tmp\kuriboh\port` to `Documents\My Games\YFM Re-Decomp\mods\kuriboh`; `.\play.bat`, F10 > Game > Mods.

DuckStation: Debug > CPU Debugger > Memory, Debug > Dump RAM (2 MB); save a state at each setup. Cheats without owning cards: `python tools/pc/kuriboh/make_cheats.py <out> 99 22 4 217` writes `cheats.txt` + `SLUS-01411.cht` (copy to DuckStation's `cheats` folder, tick in the Cheats menu; written from memory of the format: if one does nothing, write the value in the Memory tab). Cheats: every card x3 in the chest, card 679 x3, terrain 1-6 forced, "Deck: forty of card N", the five Exodia pieces as hand, first eight duelists not unlocked.

| Id | Setup (Free Duel vs Simon Muran) | Expect |
|---|---|---|
| T1 terrain | deck forty of 99 + Terrain 1 (Forest: Pumpking, B. Dragon Jungle King, Crab Turtle); forty of 22 + Terrain 2 (Wasteland: Summoned Skull, Curse of Dragon, Tri-horned Dragon); forty of 4 + Terrain 2; summon face up; dump | +500 `terrain_modifier` for listed cards, type bonus only for 4 |
| T2 yami | forty of 217, Terrain 6 | Yami bonus/penalty (-500 -> -700) |
| T3/T4 deck limit | chest: card 679 x3 (write 3 to `801D04F6`), Build Deck, try to add; also a normal card at 3 copies | 679 refused; screenshot of the count colour |
| T5 exodia | hand = five Exodia pieces (cheat on at the deck screen, off once dealt; or write 17-21 u16 to `801D0200`..., 40 entries); win by Exodia; dump on the result screen | S-TEC, retail animation (the user already confirmed from the original) |
| T6 drops | first eight duelists not unlocked after the duel starts; win (Exodia is quickest) | drop is Kuriboh (card 58) for Simon; repeat 3x and list |
| T7 frame colours | Library/Build Deck, one card per class (Effect, Union, Ritual...) | screenshots |
| T8 variants | the same on the GOD, Pharaoh Hard and Hard Drop 5 ISOs | `GOD_1.bin`, `HARD_1.bin`, `HARD5_1.bin` |

Read from dumps: the 30 card records at `801A7AD8` (28 bytes: `+0x0C` card id, `+0x0E` attack, `+0x14` terrain modifier, `+0x18..` flags), terrain byte `8009B364`, deck counts at the Build Deck state, chest at `801D0250` (+id-1).

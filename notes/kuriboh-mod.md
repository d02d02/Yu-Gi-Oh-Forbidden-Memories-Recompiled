# Kuriboh mod: reproducing it in the port

Goal: the "YFM MOD Kuriboh" ROM hack (and its three harder variants) as port mods, with
HD art and 3D Monsters support. Branch `feat/kuriboh-mod`, worktree
`...-kuriboh`. The mod's disc images are the player's own files: they stay outside the
repo, and anything derived from them lives under `tmp/kuriboh/` (git-ignored).

## LATEST STATE (written at the user's request just before a context clear; read this first, it is newer than the text below it)

**Installed in the user's mods folder** (`Documents\My Games\YFM Re-Decomp\mods`, found by `disc.user_dir()`): `kuriboh` (the mod, 1.5 MB, `after`
the HD mod), `kuriboh-hd` (the HD layer), next to the user's `assets-hd` folder whose **mod id is `forbidden-memories-hd`** (settings and
`after`/`requires` use the id: `mod.forbidden-memories-hd.full_bleed=1` is the anime frame). Rebuild/refresh everything in one command from the
Kuriboh worktree:

    python tools/pc/kuriboh/build_kuriboh.py "C:\Users\mdahh\OneDrive\Desktop\Perso\YGOFM\YFM MOD Kuriboh\YFM MOD Kuriboh\YFM MOD KURIBOH.iso" --game ..\Yu-Gi-Oh-Forbidden-Memories-Recompiled-dev\game\ygofm-orig-usa.bin --sources tmp\kuriboh\hd-chosen --install

**HD art is done and chosen by the user:** real Yugipedia artwork through Real-ESRGAN for 16 cards, the anime model on the mod's own art for 343 and 666
(`tmp/kuriboh/hd-chosen/`, made by `fetch_artwork.py` + `ai_upscale.py` + the net+AI step described in `notes/kuriboh-hd-plan.md`; `tmp/` is
git-ignored: if it is gone, rerun `fetch_artwork.py tmp/kuriboh/hd-source`, `ai_upscale.py tmp/kuriboh/kuriboh tmp/kuriboh/ai-candidates` and redo
`net_ai` as in the plan: the real artwork fitted to 204x192, the anime model x4, reduced to 408x384). Real-ESRGAN is installed in
`tmp/pc/tools/realesrgan/` (dev's tmp via a junction). The anime frame was checked (Internal 2x): new monsters get the gold anime frame with the
layer's picture, new spells and the ritual-like equips the green frame. Portraits: Kaiba and the Yugi in the Duel Master K slot are the mod's faces
enlarged by the anime model (192 px); Yami Bakura and Heishin 2nd stay retail's (their HD portrait stands). Candidate face art (Duel Links
portraits from Yugipedia) is in `tmp/kuriboh/portrait-src/` (not used).

**Open, in the order I would take them:**
1. 3D Monsters models for the new monsters (slots 393, 394, 402, 484, 499, 674, 676, 682, 683, 684, 693): a card's `model` key.
2. Mirror Force (681) effect: the hook at `0x801CE00C` ("destroy all the opponent's monsters" per its text); not reproduced; and the attack-trap ids 681-686.
3. Duel Master K's deck roll (mode 11), the AI script variable for modes 10-13 and 15, Free Duel music per opponent (`func_80024DC8`), duelist 0's AI row.
4. The harder discs as small mods requiring `kuriboh` (AI code, counted starter decks, drops x5/x10, affinity fields), then Millennium Challenge.
5. The user's DuckStation tests: low priority now (the user confirmed from the original disc that Exodia gives S-TEC with the same animation and that
   the other rules behave); cheats stay in `ygo/cheats/` (`make_cheats.py`).
6. Optional polish: HD portraits for Kaiba/Yugi from Duel Links art (needs a face crop and the frame composited), redrawn art, an editor-test pass
   (`python -m unittest` the non-GUI modules in the background; never `test_gui`).

## RESUME HERE (current as of 2026-10-10, late; this replaces the older resume text)

**Goal (user):** reproduce the Kuriboh ROM hack exactly (its behaviour, not its sloppy bytes) on top of Unchiga's recomp, with
clean data/code; then HD art for the mod's new assets in the Forbidden Memories HD mod (the FM editor's art tools do the work,
reuse them) and 3D Monsters adapted to it. Worktree `...\Yu-Gi-Oh-Forbidden-Memories-Recompiled-kuriboh`, branch `feat/kuriboh-mod`
(from `dev`; nothing pushed). The main folder is the upstream test checkout (detached master); `dev` is the other work branch.

**How to rebuild everything from the disc (the only way anything is produced; none of the ROM hack is committed):**

    python tools/pc/fm_editor import "<...>\YFM MOD KURIBOH.iso" --game game\ygofm-orig-usa.bin --id kuriboh -o tmp\kuriboh\port
    (variants: the same on the GOD / Pharaoh / Pharaoh drop-5 ISOs, ids kuriboh-god/-pharaoh/-drop5)
    copy tmp\kuriboh\port to Documents\My Games\YFM Re-Decomp\mods\kuriboh   (already done for the base mod)
    python tools/pc/build_game32.py                         (needs tmp/pc/tools, tmp/pc/win32-deps, game/ junctioned to dev's)

ISOs: `C:\Users\mdahh\OneDrive\Desktop\Perso\YGOFM\YFM MOD Kuriboh\YFM MOD Kuriboh\` (base `YFM MOD KURIBOH.iso`, variants in subfolders;
the author's own feature list `Bienvenido..txt` is the spec, summarised in "THE SPEC" below). DuckStation RAM dumps: `...\hacking\ygo\dumps\`.
Cheats for the user's DuckStation tests: `python tools/pc/kuriboh/make_cheats.py ..\ygo\cheats 99 22 4 217 681` (see `notes/kuriboh-test-plan.md`).

**State of the port after this session (all committed unless noted; see git log):**
- Importer (`tools/pc/fm_editor/importer.py`, `kit.py`) now produces: cards, fusions (rituals are fusions), equips incl. three magic cards that
  equip (`any_card`, engine change), deck/drop pools (byte pools of duelists 1-15), the 15 extra campaign duelists (ids 40-54, real names,
  own pools/AI rows), the disc duelists' AI rows (replacements), terrain bonus per type AND per card, Spellbinding Circle 700, Exodia
  rank, trap threshold, frame colors, `limits.card_copies`, `unique_drops`, dialogue, passwords, card art/thumbnails/name plates as editor art
  files (textures/ and art/), four portraits. The mod folder is 1.5 MB; no WA_MRG blob.
- Engine (port) changes, all generic and documented in `notes/gameplay-tables.md`: `equips` `any_card`; `terrain_bonus` `cards`;
  `limits.card_copies`; `unique_drops`; and the placement step treats a first-chosen magic card as the equip.
- `mods/kuriboh-rules` (the code mod) no longer exists: its three jobs became those features.
- Tests: `tools/pc/kuriboh/test_data_rules.py` (terrain), `test_ritual.py`, `test_magic_equip.py`; `tmp/kuriboh/extra_test.py` (extra duelists'
  decks). The editor's own suite: `cd tools/pc; python -m unittest discover -s fm_editor/tests -t .` (takes minutes; run it in the background to a file).
  **The last full run was started after the art/portrait importer change and its result was not read yet: read `tmp/editor_tests.log` first,
  fix what is mine, then commit/install.** (The last code commit before it: "Terrain bonus per card...". The art and portrait importer code,
  the `values.py` `card_copies` key, and the changed `test_importer.py` may be uncommitted: `git status`.)

**Reproduced 2026-10-10 (night):** Mirror Force (`trap_effects` "destroy_all", `tools/pc/kuriboh/test_mirror_force.py`); AI variable 15 (a duelist's `ai.mode`, set for modes 10-13 and 15; the base id already equals the mode, so no visible change); Free Duel music per disc duelist (`music`, table at 0x801DB010; checked: Mai song 29, Duel Master K 43); duelist 0's AI row (`replace` 0; not run in a duel); Yugi Moto in Free Duel (copy of Duel Master K with the mod's Yugi face, open after Pegasus).
**Not reproduced yet (Step 12 has the caves):** Duel Master K's deck roll (mode 11): the cave rolls 0-39 and for a roll under 16 deals the base pool through the byte-pool shuffle, else runs the *unpatched* shuffle over the byte pool, which reads it as u16 and could not deal 40 cards (needs the user's observation of K in the original); the Exodia result screen (cosmetic, the user confirmed the original matches retail); the harder discs; Millennium Challenge. Unverified in a duel: copies per card (card 679 refused), unique drop, Exodia S-TEC, rituals-by-fusion in a real campaign, Yugi Moto's unlock.

**Editor tests: done** (492 non-window tests pass; the window tests `test_gui` need a screen and hang headless: never run them; run the rest as
`python -m unittest fm_editor.tests.<module> ...` in the background). The mod in the user's Documents mods folder is the latest import.
**HD decision pending: read `notes/kuriboh-hd-plan.md` first** (keep the ids + a small second HD pack, recommended, or move the mod's 18
different cards past id 722; measured on the data). **Answered: option A** (keep ids, `kuriboh-hd` second mod); the HD layer exists (see `notes/kuriboh-hd-plan.md` "Decision and progress").

**Next, in order:** (1) [done] editor tests; (2) [HD layer: real artwork installed for 16 cards; AI candidates and comparison sheets in tmp/kuriboh/compare waiting for the user's choice (hd-plan "AI candidates"); left: redrawn art if wanted, the anime-frame check, 3D Monsters models] HD art for the 18 different cards and 4 portraits through the
editor's art tools into the HD mod, then 3D Monsters entries for the new monsters; (3) the user's DuckStation tests (cheats above; the
important one is House of Adhesive Tape: deck of card 681 cheat, set it face down, let the AI attack, say what happens); (4) hooks for what
remains, one small documented hook each; (5) variants as small mods that require `kuriboh` (`notes/kuriboh-audit.md` has the plan).

**Gotchas:** the auto-mode classifier blocks `rm` of untracked files and force pushes: ask the user. `python tools/pc/fm_editor/__main__.py`
opens the GUI: never run it. The headless Build Deck chest list renders empty. `peek` cannot read host pointers. Long test runs: background them.

## THE SPEC: the author's own feature list (translated from `Bienvenido..txt`) and where each lives

Correction (2026-10-10): the earlier "modes are unused" reading was wrong. Extra duelists (ids 40-55,
mode = id - 39) are started by campaign **dialogue scripts** (`{f8 0D 2C 2D 2D ...}` = start a duel against
duelist 0x2C/0x2D...), e.g. text `[0571]`: "Keep focused, Yugi... Now, what do you want to do?"
`<<Shop>> <<Duel>>` (`{choose 80 L714D L73B0}`; `Duel!` then `{f8 0D 2C 2D 2D 00 70 72}`). The dialogue is
already imported (283 strings in `text.txt`); the duelists it names (ids 40+) do not exist in the port yet.
My dumps never reached them because they were taken in Free Duel and one ordinary campaign duel.

Base ("moderate") mod, per the author:
1. 2 extra unlockable characters in the campaign (one is Yugi Moto as an adversary).
2. 15 extra characters, not unlockable for Free Duel, met in the campaign. (ids 40-55 = 16-17 in all.)
3. Decks closer to the anime, harder. Imported as pools (byte pools for duelists 1-15, fixed in the importer).
4. Drop is one card (retail). Unique "iconic" card the first time you beat each duelist in the campaign
   (except the campaign-only characters): `kuriboh-rules` `select_drop`.
5. 17 new cards (balance the High Mages, differentiate duelists). Imported (cards).
6. More fusions, including rituals with their monsters. Imported (fusions, rituals).
7. Fields give new bonuses, e.g. Yami raises Heishin's monsters so he is no weaker than the Mages:
   per-card terrain lists. `kuriboh-rules` `frame`.
8. Winning with Exodia gives an S-TEC rank. NOT YET LOCATED (probably the Exodia hooks `0x801CFF3C`...).
9. All 722 cards obtainable by drop or password. Passwords imported as data.
10. New campaign events (explore; very hard hidden enemies). Dialogue scripts imported; the enemies are the extra duelists.
11. Three difficulties = three discs (Pharaoh: opponents fuse/equip from the start and change guardian stars,
    iconic Yugi/Atem starter deck, better unique drops, easier S-A POW, S-A TEC only with Exodia, five cards
    limited to 1 copy for the player; alt disc: drop x5 and Yugi/Joey/Kaiba starter decks. GOD: six type-based
    starter decks, maximum stats and difficulty, no unique drops, 10 cards a win, every opponent has an
    affinity field, same 1-copy limits). Millennium Challenge is a separate disc (zip) played on a finished
    campaign save: 55 opponents, no saving, no banlist, opponents go first, 15 cards a win.
12. Source of the exact data: the TEA database (https://www.basededatostea.xyz/extend), same data for all three.

So also to reproduce: the 1-copy limits of Raigeki, Crush Card, Dark Hole, Swords of Revealing Light and
Mirror Force (Pharaoh and GOD; the base table has only card 679 at 0 and the Exodia pieces at 1: check
whether the base disc limits them), the opponent AI changes, and the starter-deck choosers.

## Step 8: the campaign's extra duelists (decoded statically from the dialogue scripts; `tools/pc/kuriboh/campaign_duels.py`)

`{f8 0D opp b370 b372 terrain bgm_lo bgm_hi}` starts a campaign duel (`Text_StartCampaignDuel`): the opponent id,
two story-string ids (before/after), the terrain, the music. Retail has 59 such starts, Kuriboh 88. The new ones
start opponents **40-54** (15 extras = modes 1-15; the hook maps id 40+k to base slot k and sets the mode byte
`0x801CF310` = k) and opponent 0 ("Unused": the Yugi-and-Atem final duel, strings `[056A]` and `[0524]`).

| id | mode | string | what the script says |
|---|---|---|---|
| 40 | 1 | `[05AD]` | the old man at the start: "Run / Stay", a forced duel when you stay |
| 41 | 2 | `[0505]` | Simon Muran: "If I beat you in a duel you come back... " Duel / Pass |
| 42 | 3 | `[053C]` | the guards of Heishin's halls (sets flag 404D) |
| 43 | 4 | `[05A8]` | "You couldn't win. This is your destiny." Run / Duel |
| 44 | 5 | `[055F]` | after a game over: Shop / Duel (the "duel or shop" choice, `{choose 80 L714D L73B0}`) |
| 45 | 6 | `[0553]` | "That was easy... You want a duel" |
| 46 | 7 | `[0543]` | beside Heishin's duel |
| 47 | 8 | `[0585]` | Valley of the Kings guard (flags 0051/0052/0053, sets 4050 4052) |
| 48 | 9 | `[05F0]` | Teana/Jono: "Go on ahead / Ignore the chance" (sets 40FD) |
| 49 | 10 | `[0548]` | the dream: "Hey! Yugi! Wake up" |
| 50 | 11 | `[0557]` | Joey's "Hiya Yugi" (flag 00FC / sets 40FC) |
| 51 | 12 | `[05D2]` | Heishin's DarkNite scene: Watch / Help Heishin |
| 52 | 13 | `[0558]` | "This is my mind... you are me" (terrain 3) |
| 53 | 14 | `[05CF]` | "Are you my next victim?" Duel / Pass (sets 40EF) |
| 54 | 15 | `[0524]` | "Let's begin..." (same strings as the opponent-0 final duel) |
| 0  | - | `[056A]` | "Now you can go back to your world... we haven't faced each other yet" |

What each extra duelist is made of (verified in the data): the base slot k (1-15: Simon Muran ... Pegasus) keeps TWO
byte pools in each of its four pool regions (deck, pow, bcd, tec): `[0:722]` for the duelist and `[722:1444]` for
its mode-k twin, each adding up to 2048; and a second AI row at `0x801CF3F7 + 9k` (the first fifteen rows
look like retail's AI parameter rows). The names of the 15 extras are in the names table's entries `0x8360-0x83FF`
(past the ones the text listing reads). The terrain is in the script (the F8 0D byte), so "home fields" are script data.
The port's `duelists` feature has what this needs: `copy` the base, `slot` = 39+k (the id the script uses),
its own `decks`, `drops`, `ai` row, `name`, and an `unlock` that never holds (not for Free Duel).

## Layout (keep it this way)

| Where | What |
|---|---|
| `tools/pc/kuriboh/` | analysis tools (read the discs, write only where `-o` says) |
| `notes/kuriboh-mod.md` | this file: findings and status (committed) |
| `tmp/kuriboh/` | local only: diff reports, the imported mod (`port/`), dumps |
| `mods/` | only finished, shippable mods (nothing from the ROM hack's own assets unless licensing is settled) |

## Step 0: where the mod changes the executable

`python tools/pc/kuriboh/exe_diff.py <retail .bin> <modified .bin> -o tmp/kuriboh/exe_diff.txt`
places every changed byte run of `SLUS_014.11` in a decompiled function or symbol.

Base mod: 38 functions/symbols; the code is only ~30 functions, mostly 1 to 18 bytes,
plus these larger ones: `func_80024DC8` (80 B), `func_8002BFCC` (112 B). Tables:
`gDuel_aTerrainBoost`, `gDuelEffect_abGroupByEffectId`, `gDuel_aOpponentData` (303 B),
`gDuel_abTrapAttackThresholds`, `gDuel_adwCardStats`, `gDuel_abCardLevelAttr`,
`gLibrary_aPasswordCardData`; the dialog/text banks (`tail_data_start`, `gText_abColorSlots`).

Variants (GOD, Pharaoh Hard, Hard Drop 5) have different executables again (47 to 48
symbols): they also change `AiScript_FindWeakest`, `AiScript_FindKiller`,
`Ai_CompleteFusion`, `AiScript_FindBestAttack`, `func_80027DF8`, `func_80037DA4`.
Do the base mod first, then express each variant as a delta on it.

## Step 2: the executable's changes, read (tools: `exe_dis.py`, `cave_dis.py`)

The base mod is a **code-cave patch**, not just table edits:

- About 30 decompiled functions get a `j`/`jal` into the mod's own code, which lives in
  trailing data of the executable: cave A `0x801CEFEC-0x801CFF87` (~2 KB: entry points
  `0x801CF320`...`0x801CF840`, a per-card copy-limit table from `0x801CF030`, per-mode tables
  at `0x801CF400`...) and cave B `0x801DB010-0x801DBA08` (~2.5 KB, not read yet), plus
  `0x801CE00C`. The port runs the retail functions natively, so each hook needs a C
  equivalent (a native code mod hooking that function), not a patch.
- Hooked: `func_80016784`, `Duel_InitScene` (x2), `DuelScene_UpdateStartup`,
  `DuelScene_UpdateDrawResolution` (x2), `DuelScene_UpdateExodiaResult`,
  `DuelScene_UpdateCardPlacement` (x2), `Duel_SelectAttackTrap`, `Duel_SelectCardDrop` (x2),
  `DuelScene_UpdateResultRewards`, `Duel_ShuffleDeck`, `Duel_SetupCardRecord` (x2),
  `DuelEffect_ApplyTerrain`, `func_800291E0`, `func_80031874`,
  `BuildDeck_UpdateChestPaneInput` (copy limit per card), `func_800383DC`,
  `Text_StartCampaignDuel`, `Ai_GetHandSize`, `AiScript_LoadOpponentData` (x2), `AiScript_Store`.
- Plain constant edits: card count `0x2D0 -> 0x2D2/0x2D3` (`Duel_ShuffleDeck`,
  `func_8002BFCC`, `Duel_InitScene` `slti 0x27 -> 0x127`), `0x28 -> -0x7F` (x3),
  stat penalty `-500 -> -700` (`DuelEffect_ApplyStatPenalty`), a flag mask `0x80 -> 0`
  (`DuelScene_UpdateFieldActions`), `blez -> bltz` (`Text_UnlockDuelist`), and a rewritten
  per-card loop in `func_8002BFCC` (frame/colour per card, 112 B) and `func_80024DC8`.
- A mode byte at `0x801CF310` (read through `lui $x,0x801D / lb -0xCF0`) and a halfword at
  `0x801CF312` gate the cave code: the mod behaves differently per selected mode.

Not yet done: read cave A's code body and all of cave B, then write the C for each hook.
Run `PYTHONPATH=tmp/kuriboh/pylib python tools/pc/kuriboh/cave_dis.py <disc> <from> <to>`
(capstone installed with `pip install --target tmp/kuriboh/pylib capstone`).

## Step 3: what the cave code does (read from the disassembly; not yet checked in a running game)

**Modes are extra duelist ids.** Cave A `0x801CF320` (hook in `Text_StartCampaignDuel`): if
the duelist id is above `0x27` (39), the mod stores `id - 0x27` in a **mode byte** at
`0x801CF310` and uses that value as the duelist. So the mod adds a second, third... version of
each campaign duelist; mode 0 is retail. Everything else is keyed on that byte
(`0x801CF312` is a signed halfword beside it, `-1` when unset; `0x2D2` is the card count it
treats as "no card").

Hooks that read the mode byte and pick a per-mode value:
- `Ai_GetHandSize` (`0x801CF570`) and `AiScript_LoadOpponentData` (`0x801CF5A0`): hand size
  `n*9` becomes a byte from a per-mode table (`0x801CF3F7 + ...`).
- `Duel_InitScene` (`0x801CF600`, `0x801CF770`), `func_800383DC` (`0x801CF640`, a per-mode row
  of 24 bytes at `0x801E-0x4C58`) and `AiScript_Store` (`0x801CF6B0`).
- The per-mode tables at `0x801CF400-0x801CF5FF` (5, 2, 25, 75, 15, 10... per opponent) look
  like the AI/duelist parameters the importer reports.
- `Duel_SelectCardDrop` (`0x801CF394`, `0x801DB2B0`): drops use per-mode sources (a
  per-card bit table at `0x801D06F4` marks cards that cannot drop), tied to the drop pool
  imported as `drops`.
- `Duel_ShuffleDeck` (`0x801CF344`): in mode > 0 (and < 0x10), the deck uses `0x2D2` and writes
  two bytes into the executable's own code (`0x80024477`, `0x800244D4`...): the mod patches
  `Duel_ShuffleDeck` at runtime depending on the mode.

**Card frames and colours (cave B).** `func_800291E0`, `func_8002BFCC` and `0x801DB840`
read a nibble per card from a table at `0x801DB8A0` (two cards per byte) and add `0x100`/`0xF1`:
that is the "card frame colour by class" the importer reports. The nibble values 0 to 5 select
a frame variant (`slti 6`), others fall back to 0.

**Per-card copy limit.** `BuildDeck_UpdateChestPaneInput` (`0x801CF000`): the table at
`0x801CF030` (3 by default, 1 for chosen cards) replaces retail's fixed limit of three.

**The rest** (`DuelScene_UpdateStartup` `0x801CF828`, `Duel_SetupCardRecord` `0x801CFED8`,
`0x801CFB50`, `0x801CFEC0`...`0x801CFF3C`, `DuelEffect_ApplyTerrain` `0x801CFB00`,
`DuelScene_UpdateCardPlacement` `0x801AAC00/0x801AAC30` in the password table) not read yet.

Consequences for the port: the mode byte is the key piece. A first native code mod would
add the extra duelist ids, hold the mode byte, and expose per-mode tables; the hooks above
then read it. The AI-side hooks (`AiScript_*`) and the self-modifying `Duel_ShuffleDeck` are
the risky ones.

More hooks read: `DuelEffect_ApplyTerrain` (`0x801CFB00`) and `Duel_SetupCardRecord`
(`0x801CFB50`) look a card up in a per-terrain list at `0x801CFA20` (32-byte rows, indexed by the
terrain byte at `0x800AB364`: card ids as halfwords up to a 0 end, the bonus at +0x1E) and use
that bonus instead of retail's: a per-card, per-terrain bonus. The Exodia hooks (`0x801CFEC0`,
`0x801CFED8`, `0x801CFF10`, `0x801CFF3C`) watch card `0x2A7` and rewrite the five Exodia result
entries to ids `0x11`-`0x15` (a changed Exodia win condition or result).

## Step 4: what the port already gives us (read from the docs, not yet tried)

- **Code hooks exist:** `host->hook(host, <game function>, <mine>, &original)` replaces any game
  function by name, chained, removable (`notes/modding.md`, "Code hooks"). `mods/ai-hard-mode` and
  `mods/yamyi-mods` are working examples. So each cave hook becomes a small C function in a mod.
- **Extra duelists are data** (`notes/more-duelists.md`): a `duelists/<id>.json` that `copy`s a
  retail duelist, with its own `decks/`, `drops/`, portrait, name and an AI row
  (`values`, nine bytes; `sight`). That is the shape of Kuriboh's modes (duelist ids above 39 =
  base duelist + mode). Most of the "modes" need no C at all.
- **Values the cave patched that are already moddable:** `deck_copies` (a single number, not
  Kuriboh's per-card table), stat penalty and terrain (`rules`), starting decks, card drops,
  `limits` (chest, attack, life points), card frame colours (`card_text_colors` and the frame
  colour work; check what exists).
- **Probably needs C hooks:** the per-card copy limit table, a per-card drop exclusion bit table,
  and `Duel_ShuffleDeck`'s runtime self-patching (find what it changes and express that as a rule
  or a hook).

Unknown: where the mode versions' decks, drops and AI rows live on the disc (the importer wrote
only the 40 base duelists' pools). Needs a DuckStation look at a duelist in mode 1+, or a read
of how `Duel_SetupCardRecord`/`0x801CF5A0` index `WA_MRG.MRG`.

## Step 5: RAM dumps from DuckStation (in `ygo/dumps`, outside the repo)

Four dumps of the base mod: before a Free Duel (Simon Muran), in that duel, a Free Duel against
another duelist, and a campaign duel. Duelist byte (`0x8009B361`): 1, 7 and 3; terrain byte
(`0x8009B364`): 0 in all. **The mode byte `0x801CF310` is 0 in all four.** The halfword at
`0x801CF312` is `-1` before the duel and `0` during it.

So in the base mod the "modes" (duelist id above `0x27`) are never entered by normal play, and
every mode-gated hook (`Ai_GetHandSize`, `AiScript_LoadOpponentData`, `Duel_InitScene`,
`func_800383DC`, `AiScript_Store`, `Duel_SetupCardRecord`'s mode part) takes its retail path in
mode 0. The three harder variants may use the modes; check their dumps before building any of it.

What the base mod does that retail does not (everything else is retail or already imported):
1. **Terrain bonus per card, not per type**: terrains 1-6 each list 14 card ids (a table at
   `0x801CFA20`, 32-byte rows) that get +500 on that terrain (Forest: Pumpking, B. Dragon
   Jungle King, Crab Turtle...; Wasteland: Summoned Skull, Curse of Dragon...). `gameplay-tables.md`
   says a per-card terrain rule needs code: a hook of the terrain function (`DuelEffect_ApplyTerrain`
   / `Duel_GetTerrainBoost`).
2. **Copy limits per card**: the table (`0x801CF02F + id`) is 3 everywhere except the five
   Exodia pieces (1) and card 679, Novox's Prayer Ritual (0: cannot be put in a deck).
   The port can set a global `deck_copies` and keeps the Exodia pieces at one; card 679 at zero
   needs a hook (or a card-level rule if one exists).
3. **Card ids up to 722 count** (`0x2D0` to `0x2D2`/`0x2D3` in the loops): retail's last two ids
   are skipped by some loops; the mod includes them.
4. **Stat penalty -500 becomes -700** (`DuelEffect_ApplyStatPenalty`): a `rules` value? check.
5. **A drop exclusion bit per card** (`0x801D06F4`), **frame colour by class** (nibble per card at
   `0x801DB8A0`), the **Exodia result** (card `0x2A7`), and a `0x80` flag mask removed in
   `DuelScene_UpdateFieldActions`: each needs reading in context.

## Step 6: first code mod works (`mods/kuriboh-rules`, deleted since: see Step 13)

Terrain bonus per named card is reproduced and verified in a headless duel
(`python tools/pc/kuriboh/test_terrain.py <card> <terrain>`): Pumpking (99) on terrain 1 and
Summoned Skull (22) on terrain 2 get `terrain_modifier` 500 with the mod on, 0 off; card 4 (not
listed) is 0 either way. The tables come from the player's disc through
`tools/pc/kuriboh/gen_rules.py` into the git-ignored `mods/kuriboh-rules/tables.h`.

Build recipe in this worktree: junction `tmp/pc/tools`, `tmp/pc/win32-deps` and `game` to the `dev`
worktree's, `python tools/pc/build_game32.py`, and for a mod alone put llvm-mingw's `bin` on PATH and
set `MEMORIES_MOD_CC` to its `i686-w64-mingw32-clang.exe` before `python tools/pc/build_mod.py`.

Deck limit (card 679 at 0 copies): `kuriboh-rules` hooks `BuildDeck_UpdateChestPaneInput` and refuses
a confirm on a card whose limit (`kCopies`, from `gen_rules.py`) is reached. It compiles and loads;
**not verified**: a headless Build Deck test (`goto("build_deck")` with the chest poked) showed an
unreadable chest list, and the deck state cannot be read live (`gBuildDeck_pState` is a host
pointer). Verify by hand in the real game with card 679 in the chest, or find another probe.
The red count display (`func_80031874`) is not reproduced.

## Step 7: importer corrections found by reading the hooks (committed, importer rewritten)

- **Deck and drop pools of the first fifteen duelists are stored as one byte a card.** The Duel_ShuffleDeck hook
  (`0x801CF344`) exits for duelist id 0 or 16+; for 1-15 it patches the shuffle at run time (`lhu` to `lbu`
  at `0x80024474`, stride 2 to 1 at `0x800244D4`, loop to 722 cards). Read as bytes, all 60 pools (15 duelists x
  deck/pow/bcd/tec) add up to exactly 2048; read as halfwords they gave 495226 and the like. The draw is the
  game's own weighted draw (a card's share is its weight, three copies at most), so the byte weights are the
  pool. The importer (`read_byte_pools`) now reads them; the earlier "40 fixed decks" (signature A4) were a
  false positive (`deals_by_count` fired on any change to the loop, retail already ends at `slti 40`) and are gone.
  The "card ids 721 and 722" loop item is covered by this: the port's edited-pool draw runs over every card.
- **Spellbinding Circle takes 700, not 500** (`0x80025E60`/`0x80025E6C`): `limits.spellbinding_circle: 700`
  (`kit.stat_penalties`); Shadow Spell stays 1000.

## Step 9: names, and what the per-mode hooks do (read from the caves; the port's roster entries cover most)

- **Names** of the 15 extras (`0x801DB3A8 + 24*mode`, glyph bytes, 0xFF ends; shown by `func_800383DC`'s hook): 40 Simon Muran 2nd,
  41 Lady Palace, 42 Dark Shrine Guardian, 43 Guardian Palace, 44 Card Shop Owner, 45 Tea Gardner, 46 Joey Wheeler,
  47 Sadin, 48 Jono 3rd, 49 Pharaoh Atem, 50 Duel Master K, 51 Heishin 3rd, 52 Pharaoh Seto, 53 Yami Bakura 2nd,
  54 Undefeated Yugi. The importer now names the roster entries from this table.
- **Mode-specific tables:** `Duel_InitScene` (`0x801CF600`): only mode 5 (Card Shop Owner) sets the drop-pool shift to
  722 and lets ids up to 0x126 through; (`0x801CF770`) mode 11 (Duel Master K) rolls a random value 0-39 into the byte
  `0x801D0708`, others set it to -1; `Duel_ShuffleDeck`'s patch then plays the base pool for a roll under 16
  and the mode's own pool (second half) otherwise (on the first duel after an unpatched call, see the cave); `AiScript_Store`
  (`0x801CF6B0`): modes 10-13 and 15 give the AI script the mode number as its variable 15, so the mod's scripts in
  the opponent records branch on it. NOT reproduced: the mode 11 roll, the AI variable.
- **Unsupported equip rules:** the mod's equip table lists three magic cards as equips (Multiply 338: Kuriboh 58, 343;
  Spellbinding Circle 349: 35, 693, 722; Shadow Spell 669: 693). The port's editor says "not an equip card" and leaves
  them out. Needs a hook of `Duel_CheckEquip` or the rule allowed for magic cards.

## Step 10: rituals and Exodia

- **Rituals are fusions.** The mod keeps one entry in the ritual table (retail 24) and instead makes each ritual spell
  fuse with each monster of its set into the ritual monster (644 such pairs in the fusion table). Verified in the port
  (`tools/pc/kuriboh/test_ritual.py <mods dir>`): Zera Ritual + Ryu-kishin gives Zera the Mant. Imported as `fusions`.
- **Exodia gives S-TEC.** The Exodia win adds -127 to the rank sum instead of +40 (three immediates:
  `0x800215F4`, `0x800183D0`, `0x800193DC`), so the sum ends below 50 (technique) at the best letter. Imported as
  `limits.rank_score.exodia` = -99 (the port's floor; the same result). The odd Exodia hooks around card 679 (`0x2A7`,
  flag `0x801CFEB7`/`0x801CFEB8`) rewrite the five cards shown on the Exodia result screen to ids 17-21; not reproduced.

## Step 11: copy limits and the magic cards used as equips (read, not yet reproduced)

- **Copy limits per disc** (table `0x801CF02F + card id`; the port's `kuriboh-rules` takes it from any disc with `gen_rules.py`):
  base = 3 everywhere, 1 for the five Exodia pieces, 0 for card 679 (Novox's Prayer). Pharaoh, Pharaoh drop-5 and GOD add 1 copy for
  Dark Hole (336), Raigeki (337), Swords of Revealing Light (348), Crush Card (661) and House of Adhesive Tape (681).
- **Magic cards as equips.** The equip table has rows for three magic cards (editor names: 338 Multiply -> Kuriboh, Sparks; 349
  Spellbinding Circle -> Dark Magician, Construct of Mask, Magician of Black Chaos; 669 Shadow Spell -> Construct of Mask). The disc's
  placement code asks `Duel_CheckEquip` for any card, so these work in the mod. The bonus they give is in the placement hook
  (`0x801AAC30`, called from `DuelScene_UpdateCardPlacement` at `0x8001A814`): 338: +2500, 669: +2000, 349: +1000, and 668 (an equip
  card, Bright Castle): +700; every other card keeps retail's (+500, Megamorph +1000). A second hook (`0x801AAC00`, at `0x8001AAA0`)
  treats a card of kind 0x14 as kind 0x17 there. The port refuses an `equips` rule for a card that is not an equip card
  (`src/pc/cards/tables.c`), so the importer leaves the three out. To reproduce: an `MEMORIES_EVENT_EQUIP` handler answering yes for
  these pairs, and the bonus (record `stat_modifier`) added once the equip is placed.

## Step 12: where the reproduction stands (2026-10-10, end of the implementation pass)

Reproduced and imported (`tools/pc/fm_editor` importer; checked headless where marked):
cards, fusions (rituals are fusions; checked), equips incl. three magic cards that equip (`any_card`; engine change in
`tables.c` and the placement step; checked: +1000 and +2000 land), deck and drop pools (byte pools of duelists 1-15), the 15 extra
campaign duelists with names/pools/AI rows (checked: own deck), the disc duelists' AI rows (replacements), terrain bonus per type
(table) and per card (`kuriboh-rules`; checked), Spellbinding Circle 700, Exodia rank, the House of Adhesive Tape threshold (25500),
card frame colors (19 ritual-like cards keep blue), the dialogue (campaign events, Shop/Duel), passwords and art as data, the unique
first-win drop and the deck limit per card (`kuriboh-rules`; built, not run in a duel).

NOT reproduced (each with where to read it):
1. House of Adhesive Tape's effect: its hook at `0x8001F2A8` jumps to `0x801CE00C`; when the effect card is 0x2A9 (681) it clears byte +0x0B of
   five card records of a row (`0x801A7D14` or `0x801A7B70` + 0x1C each) before the normal threshold test: a Mirror-Force-like effect. Meaning unconfirmed.
2. Duel Master K (mode 11) rolls 0-39 each duel and plays the base pool for a roll under 16, else the unpatched shuffle; AiScript_Store gives modes
   10-13, 15 their mode number as AI variable 15 (the mod's AI scripts branch on it).
3. The Exodia result screen showing ids 17-21 (flag `0x801CFEB7`, halfword `0x801CFEB8`, card 679).
4. Free Duel music per opponent (`func_80024DC8` rewritten: BGM `0x7000 + 16 * table[opponent]`, table `0x801DB010`).
5. Duelist 0's AI row (the port has no duelist 0 to set it on); opponent 0's pools are imported.
6. The "magic effect classes" table (`gDuelEffect_abGroupByEffectId`, 25 bytes) and `Duel_SetupCardRecord`/`DuelScene_UpdateFieldActions`
   small edits (a flag mask `0x80` -> 0 at `0x8001E3BC`).
7. Variants: AI code (`AiScript_FindWeakest`, `FindKiller`, `Ai_CompleteFusion`, `FindBestAttack`, 11 script commands), counted starter decks
   (six decks of 40 cards, a chooser after the name entry), drops x5/x10 (Game > Card drops), per-opponent affinity fields; Millennium Challenge disc.
All three variant discs import with the same pipeline (`tmp/kuriboh/port-god`, `port-pharaoh`, `port-drop5`).

## Step 13: the three code-mod workarounds are now data (2026-10-10, second pass, first part)

`mods/kuriboh-rules` is gone. Its three jobs are engine features of the port, documented in `notes/gameplay-tables.md`, and the importer
writes them from the disc: `terrain_bonus` entries with `"cards"` (84 cards; `Duel_GetTerrainBoostCard` at the four places a terrain bonus is
worked out), `limits.card_copies` (`Tables_CardCopies`; also fixes the red count), `unique_drops` (`CardDrops_Roll`). Checked headless:
`python tools/pc/kuriboh/test_data_rules.py <mods dir holding the import as kuriboh>`: Pumpking on Forest and Summoned Skull on Wasteland get
+500, an unlisted card 0. The deck limit and the unique drop are built and not yet run in a duel; the user's DuckStation tests will check them.
`tools/pc/kuriboh/make_cheats.py` still writes the cheats for those tests.

## Step 14: what the user confirmed from the original disc (2026-10-10)

The behaviours the code could not tell me work in the original and need no DuckStation test: Exodia triggers the same animation as retail (the
five-pieces rewrite around card 679 is cosmetic or unused: do not reproduce it) and gives S-TEC. The House of Adhesive Tape test is not a priority:
the card is now Mirror Force and its text says "Destroy all your opponent's monsters" when a monster declares an attack (the hook at
`0x801CE00C` is that effect: it clears a byte of the five monster records of the row; not reproduced). Art: 16 of the 18 changed cards have real
Master Duel artwork fetched for the HD layer (`notes/kuriboh-hd-plan.md`).

## Not imported by the FM Editor yet (from `import-report.txt`)

The AI's 4 added script
commands, per-opponent home fields, card frame colour by class, magic effect classes,
AI parameters, trap/heal ceilings, 45 draw pools that do not sum to 2048 (the mod changes the draw).

Dialogue is imported (283 strings). Its reader failed because a string pointer sits inside another
string's op (`0x7af0`, inside the op at `0x7aef`); the reader now drops that one op and reports it.

## Next (an older list; RESUME HERE is the current one)

1. ~~Dialog bank reader~~ done (d8b79af3c).
2. Read each changed function against the decomp source; classify table-only vs code.
3. Reproduce the tables as mod keys, the code as native code mods.
4. DuckStation traces of a scripted duel (retail vs mod) to confirm the AI and draw.
5. HD art for the mod's new pictures into the HD mod; 3D Monsters entries.

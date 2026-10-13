# Kuriboh in the port: how it is built now, and how it could be cleaner

Written 2026-10-10 after the first full implementation pass (`notes/kuriboh-mod.md` has the findings; this file
is the design review the user asked for). Nothing here has been done yet: it is the plan for the second pass.

## Status (2026-10-10, late)

Done from the plan below: items 1, 2, 3 (terrain per card, copies per card, unique first-win drop are port features and data;
`kuriboh-rules` is deleted) and 7 (the 36 MB archive blob is gone: card art, thumbnails and name plates ride as editor art files,
four portraits as `portraits/*.png`; the mod folder is 1.5 MB). Still ahead: HD art and 3D Monsters, the five unread hooks (needs the
user's DuckStation tests), and the variants as small mods requiring `kuriboh`. `notes/kuriboh-mod.md` "RESUME HERE" is the working list.

## The shape today

The importer (`tools/pc/fm_editor`, run on the player's disc) writes one mod folder; two more pieces sit beside it.

| Layer | What it holds | Cleanliness |
|---|---|---|
| Data mod (`mod.json`, `duelists/`, `decks/`, `drops/`, `text.txt`) | cards, fusions, equips, limits, terrain by type, trap thresholds, frame colors, 15 added + 38 replaced duelists, 283 dialogue strings | good: all of it is the port's own vocabulary and can be read, edited and diffed |
| `WA_MRG.MRG` (36 MB) carried as a `data` replacement | card art and name plates, small card pictures, passwords, portraits, the duel package (7 copies), duelist records | poor: one binary blob replaces the whole archive. It is the ROM hack's art and scripts, not ours, and cannot be edited or HD-upgraded piece by piece |
| `mods/kuriboh-rules` (C) | terrain bonus per card, deck limit per card, unique first-win drop | works, but each is a workaround (below) |
| Engine changes | `any_card` equips (`tables.c`), the combination step treats a first-chosen magic card as the equip | small, generic, documented in `notes/gameplay-tables.md` |

## Feature by feature: what is ugly, what is the clean version

1. **Terrain bonus per card** (`kuriboh-rules`, a `frame` callback that rewrites every card record's `terrain_modifier` each frame).
   Ugly: it fights the game's own writes every frame, runs even outside duels, and the 84 card ids live in a git-ignored header.
   Clean: extend `terrain_bonus` with an entry naming cards, `{"terrain": "Yami", "cards": ["Heishin's cards..."], "bonus": 500}`,
   read in `Tables_TerrainBonus` (which `Duel_GetTerrainBoost` already asks, keyed on the card type) by passing the card id as well.
   Pure data afterwards; no code mod. Needs the card id at the two call sites (`Duel_SetupCardRecord`, `DuelEffect_ApplyTerrain`),
   which both have it.
2. **Deck limit per card** (hook of `BuildDeck_UpdateChestPaneInput`; the red count in the list is not reproduced).
   Ugly: replaces an input function's confirm path and misses the count color. Clean: `limits.deck_copies` accepting an object,
   `{"default": 3, "Raigeki": 1, "Novox's Prayer": 0}`, read where the two existing `Tables_Value(DECK_COPIES)` calls are
   (`build_deck_pane_input.c`, `func_80031874.c`), which fixes the color too. Pure data.
3. **Unique first-win drop** (hook of `Duel_SelectCardDrop`, reading the unlocked-duelists bitmap through an export added to
   `build_game32.py`). Ugly: one more export just for this. Clean: `drops` gets `"first_win": "Kuriboh"` on a duelist
   (`duelists/<id>.json` and `drops/<id>.json` already exist), applied by `drops.c` when the duelist is not yet unlocked.
4. **Extra campaign duelists**: clean already (the port's roster). The one wart: their ids 40-54 are what the dialogue scripts say,
   so the mod depends on being the first mod to add duelists (`slot` pins them; the docs say a clash moves the later mod).
5. **Magic cards as equips** (`any_card`): fine, generic. The bonuses ride on the same entries.
6. **Rituals as fusions, Exodia rank, Spellbinding 700, trap threshold, frame colors**: data only. Nothing to clean.
7. **The 36 MB `WA_MRG.MRG`**: the real mess. Split it into what it is: (a) card pictures and name plates (108 + 18 runs) as
   per-card art the port already loads (`art` overrides, as `assets-hd` does), (b) portraits as `portraits/*.png`, (c) the
   duel package edits (7 copies x 4 runs, 9 KB) as a few `data` patches, (d) duelist records (120 sectors: AI scripts and rank
   tables) as `data` patches or, for the AI, the roster's `ai` keys. Once split, the HD pass can upscale (a) and (b) like `assets-hd`,
   and nothing of the ROM hack's own art has to ship in one block.
8. **What stays code**: the mode 11 roll, the AI variable for modes 10-13/15, the Exodia result screen, House of Adhesive Tape's
   effect, music per opponent, the harder discs' AI. None is data-shaped. Put them in one small, documented `kuriboh-rules` with one
   hook each, each with its test, and no frame callbacks.

## Order for the second pass

1. Land engine features 1-3 (generic, small, in the port's own docs), then delete the three workarounds from `kuriboh-rules`.
2. Split `WA_MRG.MRG` (7), then HD art for the mod's new cards and portraits, then the 3D Monsters entries for its new monsters.
3. Read the five not-yet-understood hooks with the user's DuckStation help, then write their hooks.
4. Variants as deltas: one `kuriboh-pharaoh` and one `kuriboh-god` mod requiring `kuriboh`, holding only what differs
   (limits, AI rows, drops count, starter decks, the AI hooks).

Every step keeps `python tools/pc/fm_editor import <disc>` the single way to produce the mod, so nothing of the ROM hack is committed.

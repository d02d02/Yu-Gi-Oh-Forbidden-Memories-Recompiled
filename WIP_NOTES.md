# WIP notes: feat/assets-hd-anime-frame

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed; this file is only what's still in flight.

## Goal

Fold the full-bleed "anime card frame" presentation into **Forbidden
Memories HD** (`mods/assets-hd`) as one of its togglable parts, instead of
shipping it as its own standalone mod (`mods/anime-card-frame`, now
deleted from this branch -- that was rejected, not approved for release).
Extended along the way to support a different frame image *per card kind*
(monster/magic/trap/ritual), since the HD pack already ships distinct
monster/magic/trap/ritual frame art for the retail-style presentation and
a single universal frame would have thrown that distinction away.

Branched from `feat/anime-card-frame-mod` (keeps its engine-side
`card_layout.c` reader/tests, which are mod-agnostic and fine; only the
packaging decision -- which mod ships the data -- changed).

## Done (uncommitted -- working tree only, not yet committed or pushed)

- `src/pc/cards/card_layout.{c,h}`: `CardLayout_SetCard`/`IsSpell`/
  `TypeIconCell` added. `"frame"` is now keyed per `cards.h`'s
  `CARD_FRAME_*` (monster/magic/trap/ritual/purple/orange), falling back
  to `monster`'s when a kind has none of its own. Magic/trap/ritual read
  `"spell"."art"`/`"icon"` instead of `"art"`/`"attribute"` (no ATK/DEF/
  stars/elemental attribute to draw for those three).
- `src/game/func_80028B08.c`: calls `CardLayout_SetCard` per card before
  asking for placements; for spell kinds, draws the *existing* Build Deck
  card-kind badge (`duel_card_type_icon.c`/`trade_screen_helpers.c`'s own
  tpage-0xB sheet, formula reused, no new art) into the icon slot instead
  of the elemental attribute ball.
- `src/game/duel_effect_resource_setup.c`: same `SetCard` call, for
  consistency (not strictly needed by its one `CardLayout_Get` call today).
- `tools/pc/hd_assets_pack.py`: `--anime-frame-monster/-magic/-trap/-ritual`
  flags build the new per-kind manifest block.
- `tools/pc/hd_recipes/anime_frame_{monster,magic,trap}.png` added
  (tracked -- small enough to not fall under "keep HD art out of git").
  **Ritual has no art yet**: `hd_assets_pack.py` defaults
  `--anime-frame-ritual` to `--anime-frame-magic`'s PNG, a deliberate,
  temporary content choice (not an engine fallback) until real ritual art
  exists. User is having it made.
- `tests/pc/card_layout_test.c`: 6 new cases (kind bucketing, monster
  fallback, equip->magic, `Cards_FrameColor` override, spell gating).
- `notes/modding.md` "Card layout" section rewritten for the new schema.
- Build verified clean: `python tools/pc/build_game32.py` exits 0
  (2026-10-04). Live-tested in the real game -- the frame now renders
  (confirmed via `MEMORIES_TRACE=card_layout,mods` + a screenshot): art
  stretch, per-kind frame image, and the type-icon badge all work.

### Local test rig (NOT part of the branch/PR)

`...\Documents\My Games\YFM Re-Decomp\mods\assets-hd\mod.json` has been
hand-patched with the `card_layout` block + the three PNGs copied into its
`textures/`, so the user's installed HD pack can be toggled/tested without
re-running the real `hd_assets_pack.py` pipeline (which needs real disc
data). Diverges from the repo's `hd_assets_pack.py` output in exactly one
value right now (see below) -- keep these in sync once the live value is
confirmed.

## In flight: monster's "attribute" (elemental ball) position

Even restored to the **original shipped values** (`x:114, y:149, width:17,
height:17`, from the old standalone mod -- confirmed correct per the user,
do not re-derive these from the art), the user still sees a very slight
misalignment ("maybe 1/4 of a pixel... a cut underneath mismatched").

- Tried: measuring the hole directly from `animeframe-complete.png`'s
  alpha channel (`x:115, y:150, width:13, height:14`) -- **rejected**:
  user reported this made it worse (pixelated, wrong fit/size). Do not
  retry shrinking width/height; the user is confident 17x17 is the right
  *size*, only position may need a nudge.
- Tried: `x:114 -> 115` (1px right) -- user then said they'd meant left,
  not right; untested as given.
- **Current state in the live test copy**: `x:113` (1px left of original),
  `y:149, width:17, height:17` unchanged. Not yet confirmed by the user --
  they're testing now. Not yet ported to `hd_assets_pack.py`/
  `notes/modding.md` (still `114` there) -- only land it in the repo once
  confirmed live.
- If `x:113` is still wrong, the user's own fallback plan (stated, not yet
  tried): a tiny *enlarge* instead of a translate.

## Resolved 2026-10-04: dropped the "card-kind badge" idea for magic/trap/ritual

Tried two different badge resources for the `spell.icon` slot (replacing
retail's elemental-attribute texture, which is meaningless for non-monster
cards): Build Deck's own badge sheet (tpage `0xB`) and the duel hand's own
card-kind word (tpage `0x1E`, `src/game/duel_card_frame_draw.c`). Both
backed out:

- `0xB` isn't reliably resident from `func_80028B08.c` (the duel's own
  card view, not Build Deck) -- read as whatever else was in that VRAM
  page, which came out looking like a stray card thumbnail.
- `0x1E` is resident through a duel, but what it holds is a 16x32 *word*
  graphic ("MAGIC"/"TRAP"/...), not a square badge -- came out as a flat
  black blob stretched into the roughly-square hole, not a bug exactly
  (the clut/tpage math checked out) but visually wrong for the art.
- User's actual ask, restated: don't introduce a new resource at all --
  just take retail's own existing attribute-texture draw (the one that
  already works for monster) and give it `spell.icon`'s position for
  magic/trap/ritual instead of `attribute`'s. `CARD_LAYOUT_ATTRIBUTE`
  already resolves a different *position* per kind (`spell.icon` vs
  `attribute`), so this needed no new logic -- just removing the kind
  branch in `func_80028B08.c` that swapped the *texture*. Done:
  `CardLayout_TypeIconCell` deleted (card_layout.c/.h), `CardLayout_
  DrawCell` kept (still backs `CardLayout_DrawFrame`, which does work).
  `func_80028B08.c`'s attribute block is back to one unconditional
  `CardLayout_DrawArt(PRM, ...)` call, position-only difference by kind.
  Tests/docs updated to match. **Not yet rebuilt/tested as of this entry.**

What retail's `rec->field_3B`-indexed attribute texture actually contains
for a non-monster card (blank? some other card's leftover data?) is still
unknown -- worth checking live once this positioning-only version is
confirmed to look reasonable.

## Known, deprioritized: the frame doesn't render in the duel's own card
viewer (z-order, not data)

Confirmed via a real headless-scripted duel (MEMORIES_DEBUG_DECK=337 Raigeki,
tests/pc/smoke/duel-hand-camera.json's input + Circle then Triangle to open
the big viewer -- see "Self-testing method" below): art, type box and
description all render correctly for a magic card, but the gold/anime frame
backdrop itself is pure black -- same complaint as the user's earlier "frame
going to background".

Ruled out (confirmed via MEMORIES_TRACE=card_layout + a temporary LOG in
CardLayoutArt_FrameCell and another at the DrawFrame call site, both since
left in card_layout_art.c/func_80028B08.c -- remove before PR):
- Decode/path: succeeds every frame (made=1, correct tpage/clut/w/h).
- Draw-call params: x=2 y=24 w=140 h=196, sane, matches the card position.
- func_800283F4.c's description backdrop (D_8009B240, its own explicit
  DisplayObject_SetDepthOffset(obj, 0x14)): does not overlap in X at all
  (it's the right-side panel; the frame is x=2..142, entirely on the left),
  so it cannot be the direct occluder.

Real remaining theory: CardLayout_DrawFrame (via the new CardLayout_DrawCell)
submits through a raw DisplayObject_SubmitPacket(..., ot, ...) call, bypassing
this codebase's normal DisplayObject_SetDepthOffset mechanism entirely --
every other element with explicit depth control (including that backdrop)
goes through SetDepthOffset; the frame has none, and ot turns out to be a
genuine pointer-sized value (logged as e.g. -2146826804), not a small depth
index, so blindly nudging it is a real crash risk, not just a misrender risk.
User flagged this class of bug as familiar from previous work -- possibly
related to feat/custom-card-art's own backdrop/depth findings (its
WIP_NOTES.md, "Resolved 2026-10-02: art/backdrop alignment" -- a different
symptom, position not visibility, but same D_8009B240/depth neighbourhood),
not yet cross-checked.

Deprioritized by the user (2026-10-04): the art/type/description render
correctly for magic already, which is the functional core; the decorative
frame border specifically is cosmetic polish, left for later.

## Self-testing method (headless-scripted, no live player needed)

Real campaign duel, deterministic, reusable for any card by id:
```
BASE=$(python -c "import json;print(json.load(open('tests/pc/smoke/duel-hand-camera.json'))['input'])")
INPUT="${BASE},6600:2000,6606:0000,6650:1000,6656:0000"   # Circle then Triangle: open the big viewer on the selected hand card
MEMORIES_DEBUG_DECK=<card id>   # forces the whole 40-card deck to one id
MEMORIES_INPUT="$INPUT" MEMORIES_DUMP_FRAME=6750 MEMORIES_DUMP_PATH=<out.ppm> tmp/pc/game32/memories-pc.exe
```
Real-time, ~115s wall-clock per run (MEMORIES_HEADLESS=1 + MEMORIES_SPEED=-1
should make this near-instant but hung/crashed both times tried -- root
cause not investigated, dropped in favour of the slow-but-reliable windowed
path). MEMORIES_LOAD_STATE does not work post-rebuild (symbol table changes
every build) -- do not use it; this method does not need it, since
MEMORIES_DEBUG_DECK/MEMORIES_DEBUG_CHEST populate a fresh boot's save
in-memory once Cheats_SaveLoaded() is true, which the normal title ->
campaign flow reaches fine on its own. Card ids: notes/card-catalog.csv
(e.g. 337 = Raigeki, Magic).

## Known, not yet done

- Temporary diagnostic `LOG(LOG_CARD_LAYOUT, "FrameCell: ...")` lines are
  still in `src/pc/cards/card_layout_art.c`'s `CardLayoutArt_FrameCell`
  (added to debug the frame-not-rendering report, which turned out to be a
  stale-binary issue, not a real bug -- decode/path resolution were fine
  all along). **Remove these before this branch is PR-ready.**
- Monster's `art`/`atk`/`def`/`stars` positions are still the old
  standalone mod's numbers, reused as-is against `animeframe-complete.png`
  -- only `attribute` has actually been live-iterated on so far. Worth a
  pass once the attribute question is settled.
- Not committed, not pushed.

## Found along the way: a related, separate branch exists

`feat/custom-card-art` (local + `origin/`) has its **own**, different
implementation of this same "full-bleed card" idea -- a `SET_CARD_LAYOUT`
*setting* (not a mod-manifest `"card_layout"` key), with its own careful
live-pixel-measured alignment work already done for the art/backdrop
relationship (see its `WIP_NOTES.md`, and
`MEMORIES_LOAD_STATE`+`MEMORIES_INPUT`+`MEMORIES_DUMP_FRAME`+
`MEMORIES_DUMP_PATH` for headless pixel-exact verification -- a much
better technique than screenshots for this kind of alignment work, worth
reusing next time instead of asking for live screenshots). Not reconciled
with this branch; worth being aware of before either one goes up for
review, since they overlap in intent.

## Handy for testing

```
MEMORIES_TRACE=card_layout,mods tmp/pc/game32/memories-pc.exe 2> trace.log
```
prints every `card_layout.c` placement decision (kind, visible, x/y/w/h)
live, no screenshot needed. F12 in-game drops a `.bmp` into
`...\YFM Re-Decomp\screenshots\`.

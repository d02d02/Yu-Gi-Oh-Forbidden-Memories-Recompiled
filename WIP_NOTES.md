# WIP notes: feat/assets-hd-anime-frame

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed; this file is only what's still in flight.

## Goal

Fold the full-bleed "anime card frame" presentation into **Forbidden
Memories HD** (`mods/assets-hd`) as one of its togglable parts, with a
different frame image *per card kind* (monster/magic/trap/ritual/orange),
since the HD pack already ships distinct frame art per kind for the
retail-style presentation and a single universal frame would have thrown
that distinction away.

`card_layout.{c,h}`/`func_80028B08.c`/`duel_effect_resource_setup.c`/
`hd_assets_pack.py`'s per-kind scheme (`CardLayout_SetCard`/`IsSpell`,
`"frame"` keyed by `cards.h`'s `CARD_FRAME_*`, `"spell"` for magic/trap/
ritual's own art/icon placement) landed in `6df9a4be9`/`a3cd5f8eb`
(committed, pushed) -- see those commit messages for the mechanism, not
repeated here.

## Done 2026-10-06: hole-free frame art, per-kind orange, attribute fix

The user redrew all frame art with **no cutout hole** for the attribute
ball / spell icon (`hacking/asset/frame/*-animeframe.png`, outside this
repo) -- only `art`'s window is still a real alpha cutout; the old
hole-measured `attribute`/`icon` `width`/`height` overrides are gone,
replaced in `hd_assets_pack.py`'s `ANIME_FRAME_MONSTER_LAYOUT`/
`ANIME_FRAME_SPELL_LAYOUT` with position-only entries (native texel size,
no stretch). `tools/pc/hd_recipes/anime_frame_{monster,magic,trap}.png`
replaced with the new art; `anime_frame_orange.png` added (new) for
`CARD_FRAME_ORANGE` -- automatic for any monster with its own effects
(`Cards_FrameColor`, no manifest wiring needed), wired via a new
`--anime-frame-orange` flag, defaulting to `--anime-frame-monster`'s PNG
like the other optional kinds. `notes/modding.md`'s "Card layout" section
updated to match.

**Found and fixed live**: dropping `attribute`/`icon`'s position entirely
(not just their `width`/`height`) hid the ball completely -- retail's own
default position for it (`card_layout.c`'s fallback, `0x6E,0xD`) sits in
the title plate *above* the art, which full-bleed's stretched art rect now
covers; the ball was being drawn, just underneath the now-much-bigger art.
Fix: kept the position in the stat band below the art (`114,149` monster /
`62,163` spell, the old hole-measured spot, clear of `art`'s rect), only
dropped the `width`/`height` stretch. `hd_assets_pack.py`/`notes/modding.md`
both carry an explanation now so this isn't rediscovered blind next time.

**Verified live** (self-testing method below), all five kinds, attribute/
icon now visible and correctly positioned in each: Blue-Eyes White Dragon
(monster, id 1), Raigeki (magic, id 337), Bear Trap (trap, id 683), Black
Luster Ritual (ritual spell, id 670, correctly falls back to magic's
frame), Sangan (effect monster -> automatic orange frame, id 48).

**Not yet committed** -- working tree only:
- `tools/pc/hd_recipes/anime_frame_{monster,magic,trap}.png` (replaced),
  `anime_frame_orange.png` (new)
- `tools/pc/hd_assets_pack.py`, `notes/modding.md`

**Local test rig** (NOT part of the branch/PR, lives outside the repo at
`...\Documents\My Games\YFM Re-Decomp\mods\assets-hd`, actually a symlink
to `tmp/pc/shared-mods/assets-hd` -- a real, already-built HD pack with
live disc data, not a hand-stub): its `textures/anime_frame_*.png` and
`mod.json`'s `card_layout` block were hand-patched to match the above, so
it could be tested without re-running the real `hd_assets_pack.py`
pipeline (needs a real disc dump this environment doesn't have at
`game/DATA`). In sync with the repo's intended output as of this entry --
re-patch both together if either changes.

## Known, deprioritized (unchanged, not touched this entry): the frame
backdrop doesn't render in the duel's own card viewer

Still reproduces with the new art (confirmed again 2026-10-06, same method
as before): art, type box, description, stats and now the attribute/icon
all render correctly; the gold/anime frame *backdrop* texture itself does
not -- flat retail-default colours show instead (green/pink/gold solid
fill, no marble texture, no dark outer border). Root cause and full
derivation unchanged from the previous entry (now rolled out of this file
-- see `a3cd5f8eb`'s diff/message and `git log -p` on this file's prior
revisions if needed): `CardLayout_DrawFrame` submits through a raw `ot`
that bypasses this codebase's normal depth-offset mechanism. User
deprioritized this (cosmetic polish, the functional core already works);
unchanged this entry, not investigated further.

## Self-testing method (headless-scripted, no live player needed)

Real campaign duel, deterministic, reusable for any card by id:
```
BASE=$(python -c "import json;print(json.load(open('tests/pc/smoke/duel-hand-camera.json'))['input'])")
INPUT="${BASE},6600:2000,6606:0000,6650:1000,6656:0000"   # Circle then Triangle: open the big viewer on the selected hand card
MEMORIES_DEBUG_DECK=<card id>   # forces the whole 40-card deck to one id
MEMORIES_INPUT="$INPUT" MEMORIES_DUMP_FRAME=6750 MEMORIES_DUMP_PATH=<out.ppm> tmp/pc/game32/memories-pc.exe
```
Real-time, ~115s wall-clock per run. `MEMORIES_LOAD_STATE` does not work
post-rebuild (symbol table changes every build) -- do not use it; this
method doesn't need it, `MEMORIES_DEBUG_DECK` populates a fresh boot's
save in-memory once `Cheats_SaveLoaded()` is true, which the normal title
-> campaign flow reaches fine on its own. Card ids: `notes/card-catalog.csv`.
Dump is a raw `.ppm` -- convert with PIL (`Image.open(...).resize(...,
Image.NEAREST)`) before sharing/viewing.

## Known, not yet done

- Temporary diagnostic `LOG(LOG_CARD_LAYOUT, ...)` lines are still in
  `src/pc/cards/card_layout_art.c`'s `CardLayoutArt_FrameCell` and
  `src/game/func_80028B08.c`'s `DrawFrame` call site (both predate this
  entry). **Remove before this branch is PR-ready.**
- Monster's `art`/`atk`/`def`/`stars` positions are still the old
  standalone mod's numbers -- confirmed by pixel-measuring the *new* art's
  own art-hole and ATK/DEF plaque-box bounds (2026-10-06): they already
  match the new art closely (within ~2px), so no change was needed, but
  they haven't been independently re-derived from scratch.
- `monster-ritual-animeframe.png`/`monster-obelisk-animeframe.png`
  (`hacking/asset/frame/`, outside this repo) are drawn but **intentionally
  unused**: the engine's `CARD_FRAME_*` enum has exactly one free slot
  (`purple`) and neither ritual monsters nor the three God cards are
  auto-detected today (unlike effect monsters' automatic `orange`) --
  wiring either in needs per-card `Cards_FrameColor` overrides added to
  the HD pack's card data, deferred by user decision (2026-10-06) rather
  than picking one arbitrarily.
- Not committed, not pushed.

## Found along the way: a related, separate branch exists

`feat/custom-card-art` (local + `origin/`) has its **own**, different
implementation of this same "full-bleed card" idea -- a `SET_CARD_LAYOUT`
*setting* (not a mod-manifest `"card_layout"` key), with its own careful
live-pixel-measured alignment work already done for the art/backdrop
relationship (see its `WIP_NOTES.md`, and
`MEMORIES_LOAD_STATE`+`MEMORIES_INPUT`+`MEMORIES_DUMP_FRAME`+
`MEMORIES_DUMP_PATH` for headless pixel-exact verification against a real
save state -- not usable on *this* branch, see above, but good technique
if this branch ever gets a stable rebuild-surviving state). Not reconciled
with this branch; worth being aware of before either one goes up for
review, since they overlap in intent.

## Handy for testing

```
MEMORIES_TRACE=card_layout,mods tmp/pc/game32/memories-pc.exe 2> trace.log
```
prints every `card_layout.c` placement decision (kind, visible, x/y/w/h)
live, no screenshot needed. F12 in-game drops a `.bmp` into
`...\YFM Re-Decomp\screenshots\`.

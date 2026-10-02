# WIP notes: feat/custom-card-art

Scratch progress/status file for the current feature branch. Tracked and
pushed so work can resume in a fresh session or on another machine, but it
is **not meant to reach upstream** -- when preparing a PR, cherry-pick the
real code commits onto a clean branch and leave the commit(s) touching this
file behind (see repo convention: never PR a branch with personal/WIP
commits mixed in). Content gets replaced wholesale each time a new feature
branch starts this cycle.

## Goal

A Duel-Links-style full-bleed card presentation (hide frame/title/
description, enlarge art, reposition stats) behind a new `SET_CARD_LAYOUT`
setting (off by default), fully additive via `#ifdef MEMORIES_PC` --
retail's own byte-matched path is untouched throughout.

Tip as of 2026-10-02: `f781688e0` (pushed to origin).

**Why:** user-driven visual mod, not a decompilation-accuracy task. Worked
iteratively with live in-game verification each step -- this is a
UI/rendering feature where "looks right live" is the actual spec, not a
secondary check. Ask the user to drive live verification or tell you what
to press; don't blind-guess controls.

## Architecture: `src/pc/cards/card_layout.c`/`.h`

One module is the single source of truth for every full-bleed element's
visibility and position: `CardLayoutPlacement CardLayout_Get(CardLayoutElement)`
(FRAME/TITLE/DESCRIPTION/LEVEL_STARS/ATTRIBUTE/ATK/DEF/ART) and
`int CardLayout_FullBleed(void)`. Call sites read it instead of each
repeating `Settings_Get(SET_CARD_LAYOUT)` and their own magic numbers:
`duel_effect_resource_setup.c` (frame's DisplayObject list membership,
0=hidden/2=drawn), `func_800283F4.c` (card viewer's description text box),
`func_80028B08.c` (the shared "big card" draw path reached by all 8 "show
one full card" screens -- title plate, ATK/DEF digits, level stars,
attribute icon, ATK/DFD labels, the plaque, and the art stretch).

A `card_layout` log channel exists (`src/pc/debug/log.h`/`log.c`) --
`MEMORIES_TRACE=card_layout MEMORIES_LOG=<path>` logs each element's
visibility/x/y/w/h on change (deduped, not per-frame spam). Use this to
verify what's actually happening live instead of guessing from a
screenshot alone.

## Key findings (hard-won, non-obvious -- read before redoing this work)

1. **Retail's ATK/DEF digits use a semi-transparent "Back-Front"
   (subtractive) blend** (`PRM->attribute` bit 0x40000000 + ABR-mode bits),
   designed to read as an engraved look against the frame's lighter plate.
   Forcing it opaque exposes real garbage: the shared digit-font atlas
   (tpage 0x1F) packs glyphs with unclean inter-glyph padding the blend was
   hiding. Confirmed live -- a forced-white digit still showed scratch
   artifacts, because the garbage is baked into neighboring texels, not a
   color problem.

2. **"ATK"/"DFD" word labels are NOT baked into the (hidden) frame bitmap.**
   They're drawn by their own `DisplayObject_SubmitPacket` calls in
   `func_80028B08.c`, right before the ATK/DEF digit block, positioned via
   `obj->field_30` (a fixed per-screen offset, never touched by
   `card_layout.c`). Suppressed outright via `!CardLayout_FullBleed()`
   rather than repositioned, since the target reference image reads
   ATK/DEF by box position alone, no text labels.

3. **`GsSortFastSprite`'s native implementation**
   (`src/pc/sdk/libgs.c`'s `sort_plain_sprite`) **bakes color-depth and
   semi-trans straight out of `attribute` into the final tpage.** Reusing
   a display object's own `attribute` (tailored for one texture) on a
   different texture/font produces visibly corrupted output -- confirmed
   root cause, not guessed. Any reuse of a different texture/font in this
   function must build a clean `attribute` value, not inherit it from
   `obj`.

4. **A second, plain-opaque digit font already exists in retail**:
   `card_list_render_deck_box_stats.c`'s deck-box list ATK/DEF (tpage 0xB,
   CLUT cx=0x290/cy=0xFA, 8x8 glyphs, `u = digit*8-0x80`, via
   `GsSortFastSprite`, no blend trick). Explored as a font-swap alternative
   to the plaque, abandoned in favor of the plaque (closer to the
   reference image) -- documented here if ever useful.

5. **`DisplayObject_SubmitPacket`'s shared dispatch has case-4/5 branches
   purpose-built for adding a new projected primitive.** (`display_object_
   helpers.c`): case 4 takes a prepared `POLY_G4` (flat Gouraud quad), case
   5 a `POLY_GT4` (textured Gouraud quad); both project through
   `RotAverageNclip4` against `EXT`'s origin when the packed attribute's
   bit `0x04000000` is set, then submit via `GsSortPoly` (or
   `func_8005B260` for semi-trans) either way -- the SAME dispatch
   `DisplayObject_RenderGouraudQuadList`/`RenderTexturedGouraudQuadList`
   use elsewhere for screen-space UI quads, just invoked directly instead
   of through that list renderer. The first arg's static type in a given
   TU (e.g. `SpritePrim *` here) is irrelevant to case 4/5 -- they only
   test its raw bit pattern, never dereference it (per the dispatcher's
   own header comment: "the Gouraud-quad renderers pass the display
   object's raw attribute word"). This solved both remaining problems:
   - **The plaque** (`CardLayout_DrawPlaque`) builds a `POLY_G4` and goes
     through case 4 instead of a raw `GsSortPoly` bypass -- confirmed
     live, it now rotates with the card's turn/reveal animation like
     everything else.
   - **The art stretch** (`CardLayout_DrawArt`) builds its own `POLY_GT4`
     through case 5, with UV/clut/tpage pinned to the original 0x66x0x60
     texel footprint but vertex x/y/w/h set independently to a bigger
     target rect -- the decoupling a bigger `PRM->extent` can't give
     (extent ties vertex size AND texel-read size together; enlarging it
     samples past the real texture block, same class of bug as finding 1's
     digit garbage). `POLY_FT4`/`POLY_GT4` share byte-identical layout for
     `clut`/`tpage` (standard PSX GPU packet format), so the default
     case's own encoding formula was reused directly.

6. **The art rect's target size comes from the frame's own geometry, not a
   guess**: `duel_effect_resource_setup.c` sets the frame object's
   `field_18`/`field_1A` to `(0x46,0x62)`, read by `func_80028B08.c`'s
   clip test as a centre-point offset from `win`'s own origin -- so the
   frame's box, in the same win-relative coordinate neighbourhood every
   element here uses, is `2*(0x46,0x62) = (0x8C,0xC4)` starting at
   `(0,0)`. Confirmed against retail's own picture placement: its inset
   (19,50) sized (102,96) leaves matching 19px/50px margins on the far
   side, which only happens if this really is the frame's box.

## What's confirmed solid

"Shutting down" (hiding) a card part in full-bleed mode, and "adding a
part" (plaque, art) through the real projected pipeline, are both proven,
repeatable patterns now: frame (list 0 vs 2), title plate, description box,
and ATK/DFD labels are cleanly suppressible via
`CardLayout_FullBleed()`/`CardLayout_Get(...).visible` gates; plaque and
art both rotate correctly via case-4/5 dispatch. Zero effect on the retail
path throughout.

## Open issue (known, deferred on purpose -- user's call, 2026-10-02)

The art's bottom edge is capped at `ICON_ROW_Y` (not the frame's full
`0xC4`) so it doesn't bleed behind the icon/ATK/DEF row -- confirmed live
this widened that row's look when it went all the way down. Matches the
Duel Links reference art's own proportions reasonably well (measured off a
reference screenshot: art spans ~56% of card height, stops ~79% down;
`ICON_ROW_Y` is 77% of this frame's height).

But on the right, the art (`ART_W = 0x8C` derived from the frame) falls
short of the card-viewer's own *wider* backdrop -- the one that also
covers where description text normally sits, further right -- by roughly
15-20px, exposing the duel field's stone-textured background through the
gap. Confirmed by pixel-measuring a live screenshot, not a simple
left/right translation bug (the left edge has no matching gap, just its
own ~8px bezel). **Explicit instruction: leave this for later** -- don't
patch with a quick nudge. The real fix is to rethink the art/icon-row rect
dimensions as ratios that account for that wider right-hand area, once
everything else is working, not as an isolated tweak.

## Next steps

1. ~~Re-verify the "shut down a part" capability~~ -- done, confirmed live.
2. ~~Build "add a part to the card" properly~~ -- done (case-4/5 dispatch,
   finding 5 above), both plaque and art now go through it.
3. ~~Stretch/enlarge the card's own art to fill the full card area~~ --
   done, capped bottom at `ICON_ROW_Y`. Right-edge gap vs. the wider
   backdrop is the known open issue above.
4. **Rethink the art/stat-row rect as ratios that include the right-hand
   text area** (explicitly deferred until "everything works" first) --
   likely means the card-viewer's wider backdrop width needs to be
   derived the same evidence-based way `CARD_LAYOUT_ART`'s current box
   was (not guessed), then the art and icon/ATK-DEF row re-proportioned
   against *that* width instead of just the narrower frame box.
5. Build a gold/olive backdrop bar for the icon/ATK-DEF row to sit on (per
   the Duel Links reference) -- still not built, stars/attribute/ATK/DEF
   currently float with no backdrop of their own.

## Workflow notes

- Build: `python tools/pc/build_game32.py --build tmp/pc/game32dbg` (from
  repo root). Exe locks if still running -- ask the user to close it
  before rebuilding.
- Test: `MEMORIES_USER_DIR=../game32dbg-user` (own profile), `MEMORIES_
  CARD_LAYOUT=1` to force full-bleed on, `MEMORIES_TRACE=card_layout
  MEMORIES_LOG=card_layout.log` for the log channel above.
- Reference images: a Duel Links screenshot (Wattkid card,
  `maxresdefault.png` at repo root, untracked) gave the art-height ratio
  used for finding 6 / the ICON_ROW_Y cap. A live screenshot (`game/
  pixels.png`, untracked/ignored) was pixel-measured to find the right-
  edge gap described above.
- Three parallel forked sub-agents (isolation: worktree) worked well
  earlier in this branch's history for "try N approaches, compare live"
  work -- but isolated worktrees branch from the *current commit*, not
  uncommitted changes, so commit a clean checkpoint first or the agents
  lose in-progress work.

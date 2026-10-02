# WIP notes: feat/custom-card-art

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed (git log + the commit message + code comments are the history;
this file is only what's still in flight). Replace wholesale when a new
feature branch starts.

## Goal

Duel-Links-style full-bleed card presentation (hide frame/title/
description, enlarge art, reposition stats) behind `SET_CARD_LAYOUT`
(off by default), additive via `#ifdef MEMORIES_PC` -- retail's
byte-matched path untouched. Tip as of 2026-10-02: `44e4d0145` (origin).

Architecture, resolved findings, and the mechanism used throughout
(`DisplayObject_SubmitPacket`'s case-4/5 dispatch for projected quads) are
documented in `src/pc/cards/card_layout.c`/`.h` and `src/game/
func_80028B08.c`'s own comments, and in the commit messages for `93f5032dc`
/ `f781688e0` -- read those rather than expecting a duplicate here.

## Resolved 2026-10-02: art/backdrop alignment, both axes

The art (`CARD_LAYOUT_ART`, `card_layout.c`) used to be sized only against
win's own frame, with no relationship to the card-viewer's separate
backdrop object (`func_800283F4.c`'s `D_8009B240`, the description
TextBox's own panel -- created unconditionally, never gated by
`CARD_LAYOUT_DESCRIPTION`, so it's on screen in full-bleed mode too, just
empty). That caused two visible mismatches: a horizontal gap on the right
(old, since-disproven note below) and the art poking above the backdrop's
own top edge (user observation).

Root cause and fix are now documented in `card_layout.c` itself (the
comment above `CARD_LAYOUT_WIN_ORIGIN_X`): the backdrop's anchor sits at
an exact, source-derived offset from win's own origin
(`CARD_LAYOUT_BACKDROP_DX`/`DY`), and its own *visible* art starts some
bezel margin past that anchor (`CARD_LAYOUT_BACKDROP_INSET_X`/`_Y`),
measured live rather than guessed. Method: a headless run of the real
save state (`MEMORIES_LOAD_STATE=1` against `tmp/pc/game32dbg-user/states/
slot1.state`), a scripted Triangle press to open the viewer
(`MEMORIES_INPUT="40:1000,46:0000"`), and a native 320x240 frame dump
(`MEMORIES_DUMP_FRAME=200`, `MEMORIES_DUMP_PATH=...ppm`) read back pixel
by pixel. Found: horizontal was already exact (zero gap, `ART_W`
unchanged) -- the old "~15-20px" note came from `game/pixels.png`, which
turned out to be cropped before ever reaching the backdrop's edge, so
that number was never real. Vertical had a real 2px gap, now closed:
`ART_Y`/`ART_H` are derived from `BACKDROP_DY`/`INSET_Y` instead of the
old flat `0`. Verified live post-fix: art top and backdrop top both at
native y=26, exact match.

## Known, left alone on purpose: backdrop's own left edge isn't straight

Confirmed live (2026-10-02, same headless method as above, row-by-row
scan): the backdrop's own left edge sits at win-relative x=140 for its
full height *except* the bottom (biggest) of its three stacked
text-line rows, which is 2px wider on the left (x=138), stepping in
starting the exact row the art's own last pixel row ends. No frame ever
has both the art and that wider row drawn on the same row -- it's a seam
in the backdrop's own texture (retail's own, shared with Library/Build
Deck), not a pixel collision -- but scanning down the edge by eye it
reads as the panel cutting into the art's own corner, which is exactly
what prompted this investigation. Full derivation and the decision are in
`card_layout.c`'s comment above `CARD_LAYOUT_BACKDROP_DX`. **User's call
(2026-10-02): leave it, document it** -- not a bug this branch
introduced; retail's own layout never exposed it (description text
covered that row); the parked real-texture plan below is the right place
to actually mask it, if that's ever wanted.

## Done 2026-10-02: real textures for the plaque and row backdrop

Shipped: `CardLayout_DrawPlaque`'s flat parchment-beige `POLY_G4` and the
icon/ATK-DEF row's own empty background (next-steps item, previously) are
now real art, following `src/pc/cards/star_icons.c`/`src/pc/text/glyphs.c`'s
own precedent for putting a disc-less PNG onto a texture the duel's
pipeline samples:

- `src/pc/cards/card_layout_art.c`/`.h`: a small per-asset table
  (`CardLayoutArtAsset`: `CARD_LAYOUT_ART_PLAQUE`, `CARD_LAYOUT_ART_ROW`),
  each decoded once (`CardArt_IndexedImageFromMemory`, `art.c` -- a new
  from-memory sibling of the existing mod-art decoder, added for this)
  and stored into a shared `SoftGpu_Bank` (13 -- 1-12 the 3D Monsters mod,
  14 star icons, 15 glyphs, 0 is real VRAM). 8bpp, two texels a word, tpage
  depth field 1 -- no existing 8bpp bank user to copy, derived from
  `getTPage`'s own encoding (`psyq/libgpu.h`) instead. Stored at half each
  source PNG's own resolution (the most that still fits `POLY_GT4`'s u8
  UV coordinates, <=255 either axis), not the tiny on-screen box size, for
  headroom at Internal 2x/4x.
- `src/game/func_80028B08.c`: `CardLayout_DrawArtAsset`, shared by both --
  a textured `POLY_GT4` through the same case-5 dispatch `CardLayout_DrawArt`
  uses. The plaque falls back to its old flat fill if the asset/bank isn't
  available; the row backdrop (`CardLayout_DrawRowBackdrop`) has no
  fallback, purely decorative, submitted *last* so it ends up underneath
  the stars/attribute/plaque/digits (this port's OT prepends to its
  bucket's head, so the most recently submitted primitive at a shared
  depth draws first -- underneath -- not on top; same trick the plaque's
  own draw order already used).
- `src/pc/cards/card_layout.c`/`.h`: `CARD_LAYOUT_ROW_BACKDROP` added as a
  real layout element (`CardLayout_Get`), not an ad hoc rect -- derived
  from two new named constants, `CARD_LAYOUT_WIN_W`/`_H` (0x8C/0xC4, the
  frame's own total box, previously only inside a comment). The plaque's
  own box (`CARD_LAYOUT_PLAQUE_W`, card_layout.h) widened from 32 to 44
  native px to match the real art's own aspect (~2.57) instead of an
  independent number, and moved there from `func_80028B08.c` for
  consistency with every other layout constant. ATK/DEF digit centering
  (`func_80028B08.c`) now derives from the plaque's own width instead of a
  `-1`-for-5-digits special case, so a 4-digit row centers correctly in
  the wider box too.
- `tools/pc/embed_png_asset.py`: generalized `tools/pc/embed_controls_art.py`
  (same PNG-chunk-stripping policy) for any `src/pc/assets/<name>.png`.

Assets used: `atk-dfd-2-plaque.png` (ornate red/gold plaque, 358x142,
user-provided) and `card-background-bottom.png` (gold/olive marble row
background with real alpha cutouts for the two stat boxes and the
attribute circle, 919x348, user-provided) -> `src/pc/assets/
card_layout_plaque.png` / `card_layout_row.png`.

Confirmed live (headless, `MEMORIES_INTERNAL_SCALE=4 MEMORIES_DUMP_PICTURE=1`):
plaque renders correctly, transparency respected. Row backdrop not yet
visually confirmed live -- built against the same, already-proven path,
but the save state drifted stale (below) before it could be checked; and
it is about to be retired anyway (next section), so not chasing that
confirmation now.

## Done 2026-10-02: unified card frame, row backdrop retired

Adopted `animeframe.png` (imported as `src/pc/assets/card_layout_frame.png`
-- found at 4.86MB, re-saved with proper PNG compression first, 419KB,
pixel-identical, `zlib`/PIL `compress_level=9`; the original would have
embedded as an 11.5MB header) as the single frame for the whole WIN box,
replacing `card_layout_row.png`/`CARD_LAYOUT_ART_ROW`/
`CardLayout_DrawRowBackdrop` entirely (both removed from the repo and the
build) rather than layering both. The plaque (`atk-dfd-2-plaque.png`) is
kept, drawn inside this frame's own two rectangular holes.

**Recalibrated against the frame's own cutouts** (Python/PIL flood fill on
the alpha channel, converted at the image's own 919x1319 -> 140x196 scale,
~6.56x/6.73x a axis), replacing the original first-pass guesses in
`card_layout.c`: `ART_X/Y/W/H` (4,3,132,138 -- a real ~3.5px matted margin
on both sides of the art now, instead of edge-to-edge), `ICON_ROW_Y` (149),
`VALUES_ROW_Y` (171), `ATTR_X` (114), `ATK_X` (25), `DEF_X` (89). `STAR_X`
kept at its original value -- no cutout to measure it against, stars sit
directly on the frame's gold. Full derivation is in `card_layout.c`'s own
comments. The backdrop-flush derivation that used to size `ART_W`
(`CARD_LAYOUT_BACKDROP_DX/DY/INSET_X/_Y`) is retired -- ART no longer
reaches the description backdrop directly, the frame's own outer box
(`CARD_LAYOUT_WIN_W/H`, now public in card_layout.h) does that job instead,
unchanged from before.

**Compositing flips, as expected**: the frame is a mask, not a backdrop --
opaque border/gold, with the art/attribute/both stat boxes as real alpha
cutouts in the asset itself. `CardLayout_DrawFrame` (func_80028B08.c) is
submitted *first* (before art/digits/stars/attribute), the opposite of the
plaque's/old row backdrop's submitted-last convention, so it ends up
walked -- drawn -- last and paints over everything except its own holes.
Reuses `CardLayout_DrawArtAsset` as-is for the draw call.

**Not yet live-verified**: `slot1.state` is stale for headless
verification (drifted past the hot-reload carry-over's tolerance after
this many rebuilds since 13:17 -- `MEMORIES_LOAD_STATE` fails, falls back
to a fresh boot). Built clean, reviewed by hand against the measurements,
but needs either a fresh save state (Triangle to open the viewer at the
same spot, F5) or live user verification before trusting the numbers on
screen.

Why not a mod: this modifies retail's own byte-matched draw routine
(`func_80028B08.c`) and object setup (`duel_effect_resource_setup.c`,
`func_800283F4.c`) directly -- outside the mod system's hook surface (code
mods hook specific named extension points, e.g. the title screen's
`MainMenu_*` functions, not arbitrary mid-render internals of a decompiled
retail function). Same category as Internal 2x/4x resolution: a
`Settings_Get(SET_CARD_LAYOUT)`-gated, `#ifdef MEMORIES_PC`-additive core
port feature, not a `mods/` directory.

## Workflow notes

- Build: `python tools/pc/build_game32.py --build tmp/pc/game32dbg`. Exe
  locks if still running -- ask the user to close it first.
- Test: `MEMORIES_USER_DIR=../game32dbg-user`, `MEMORIES_CARD_LAYOUT=1`,
  `MEMORIES_TRACE=card_layout MEMORIES_LOG=card_layout.log`.
- **Headless pixel-measurement repro** (no window needed; add
  `MEMORIES_INTERNAL_SCALE=4 MEMORIES_DUMP_PICTURE=1` for a true 4x dump
  matching what the player sees -- without `MEMORIES_DUMP_PICTURE`,
  `Memories_DumpFrame` ignores the internal scale and dumps the raw
  native 320x240 buffer regardless, which is fine for exact-pixel
  measuring but not what a human should eyeball): from
  `tmp/pc/game32dbg/`, `MEMORIES_USER_DIR=../game32dbg-user
  MEMORIES_HEADLESS=1 MEMORIES_CARD_LAYOUT=1 MEMORIES_LOAD_STATE=1
  MEMORIES_INPUT="40:1000,46:0000" MEMORIES_DUMP_FRAME=200
  MEMORIES_DUMP_PATH=<path>.ppm ./memories-pc.exe` -- loads
  `states/slot1.state` (a duel with a card viewable, user-provided,
  2026-10-02), scripts a Triangle press (pad bit 0x1000) to open the card
  viewer, and dumps a frame once it's settled. Re-run after any
  `card_layout.c` change touching the art rect to verify against real
  pixels instead of re-guessing.
- Reference images used so far: `maxresdefault.png` (repo root, untracked)
  and `game/pixels.png` (untracked/ignored) -- both local-only, not in git.

## Done 2026-10-02: frame resolution bump + auto-measure tool

Frame texture (card_layout_art.c) bumped 173x248 -> 177x254 (u8 UV ceiling).
Confirmed by direct crop comparison: blur is our own downsample, not the
source PNG (sharp at full res). HD texture-pack pipeline (TexturePack_
AddMade, used by cards.c mod art) traced in full: works by content-match
on a tracked SoftGpu_Load upload into real VRAM; banks (ours, star icons,
glyphs) have no tag-array equivalent at all, so not reachable without
either claiming real VRAM (fragile, the contention problem banks exist to
avoid) or extending texture_dump.c/texture_pack.c to be bank-aware (a real
core-engine feature, out of scope here -- logged as a future direction,
not pursued this session).

tools/pc/measure_card_frame.py: flood-fills card_layout_frame.png's alpha
cutouts + colour-matches its cream stat boxes, prints ART_X/Y/W/H,
ICON_ROW_Y, ATTR_X, ATK_X, DEF_X, VALUES_ROW_Y. Run after swapping the
frame template instead of hand-measuring. Validated against current
constants (within 1px, rounding only).

Not live-verified this round (token budget) -- build is clean.

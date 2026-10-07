# WIP notes: feat/assets-hd-anime-frame

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed; this file is only what's still in flight.

## Done 2026-10-07: two real bugs found and fixed via parallel agents

User reported the frame backdrop looked "flat" AND that it wasn't showing
at all during the card viewer's open animation -- two different things.
Spun up agents in isolated worktrees to chase both in parallel (one
reviewer-style: independently re-verify, don't trust the first finding):

- **Contrast**: confirmed NOT a code bug two independent ways (a faithful
  Python reimplementation of `CardArt_IndexedImage`'s resize/quantize
  showed no fidelity loss beyond the unavoidable 919x1319->177x254
  downsample; a bold checkerboard swapped in for the real art rendered
  perfectly crisp through the same pipeline). Fixed anyway at the asset
  level: `tools/pc/hd_recipes/anime_frame_*.png` got an HSV-space contrast
  boost (unsharp mask + a small hue-neutral marbling layer, alpha/geometry
  untouched) so the real art's low-amplitude marbling survives the forced
  downsample. Verified live, stddev roughly doubled in the stat band.
- **The real "not showing" bug**: found by watching the open animation
  frame by frame (not just the settled end state) and diffing against
  retail mode at the same tick count -- full_bleed's frame/art region sat
  completely blank for the first ~10+ frames where retail already shows
  its own placeholder swirl. Root cause:
  `duel_effect_resource_setup.c`'s `func_800291E0` hid retail's small
  frame sprite the instant `CardLayout_Get(CARD_LAYOUT_FRAME).visible` was
  false, but `CardLayout_DrawFrame`'s own replacement doesn't start
  drawing until several frames later (once the object becomes
  renderable), leaving that window empty. Fix: keep retail's sprite as a
  stopgap whenever a replacement frame image exists (`CardLayout_FramePath()`
  non-empty) -- it ends up fully covered once the replacement draws, no
  seam at settle -- and only hide it immediately for a mod that
  deliberately configures no frame at all (notes/modding.md's documented
  "no backing" case). Verified live across all four kinds (monster/magic/
  trap/orange): the gap is gone, settled state unchanged.

Both fixes are in on `feat/assets-hd-anime-frame-pr` too (amended into its
single commit).

## Done 2026-10-06: a PR branch, and auto-picked-up anime frame art

`feat/assets-hd-anime-frame-pr` (pushed) is the clean branch for upstream:
this branch's real commits minus this file, one squashed commit. User will
open the PR themselves.

`--anime-frame-<kind>` now default to `tools/pc/hd_recipes/anime_frame_
<kind>.png` if present, else `<assets>/anime_frame_<kind>.png`, else
nothing (`anime_frame_default`, `hd_assets_pack.py`) -- any existing HD
pack build command picks this up with no changes, instead of silently
shipping without it until someone remembers to add the new flags. Also
trimmed several over-long comments this branch had accumulated, per
feedback.

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
frame), Sangan (effect monster -> automatic orange frame, id 48). Also
Black Luster Soldier (an actual ritual *monster*, id 364 -- plain
`monster` frame, as expected per the deferred-`purple`-slot decision
above) dealt in a real two-card deck alongside its ritual spell (id 670),
both correct.

Committed and pushed: `ff79f7dd0` (frame art/orange/attribute fix),
`c1630d72f` (stars centering, below).

## Done 2026-10-06: the anime card frame is off by default

User's call: the feature stays, but a fresh install should look like retail
until a player opts in -- the eventual plan is to move this toggle into
the FM Editor rather than the Mods window, but that is later, not now.

**The real fix is in the engine, not the manifest.** The obvious-looking
change (`hd_assets_pack.py`'s `"default": 0` on the `full_bleed` setting
entry) only changes what the Mods window *shows* a player who has never
touched the setting -- it is not read anywhere near `card_layout.c`.
What actually answers a player with no saved setting is
`full_bleed_of`'s own `Mods_Setting(..., "full_bleed", 1)` call -- a
hardcoded fallback baked into the C code, independent of any manifest.
Changed `1` -> `0` there (`src/pc/cards/card_layout.c`); since `"full_bleed"`
is a generic key any `card_layout` mod can declare (not HD-specific), this
is the right place for it regardless -- HD is just the only mod using it
today. Also fixed the manifest's `"default"` to match (so the Mods window
doesn't lie about it) and trimmed its label/description per the user
("not a lot of description in it"): `"Anime card frame"`, one short line.

Added `tests/pc/card_layout_test.c`'s `setting_unset()`: a mod applied
with *no* explicit `full_bleed` key at all (not even `0` -- the test
harness's `add_mod(..., NULL, 0)` exercises the real fallback path, unlike
every existing case here which sets the key explicitly) now asserts
`!CardLayout_FullBleed()`. Not yet run through `ctest` (no `cmake` on
this machine's PATH, see below) -- verified instead by reading the
assertion against the fallback change directly, and by two live runs
through `tools/pc/yfm_control.py` (`tmp/pc/control/default-off/` with the
mod on and no `full_bleed` override: retail's small frame; `.../explicit-on/`
with `"mod.forbidden-memories-hd.full_bleed": 1` forced on through `Game`'s
`settings=`: full-bleed, unchanged from before this entry) -- both match
what the engine-level fix should do, but the C unit test itself is unverified
by a real compiler/test run, only by inspection. **Worth running
`setting_unset` for real the next time `cmake` is reachable.**

`cmake`/`ctest` are not on PATH here (checked `which`, `shutil.which`,
common install folders -- not found), even though `tools/pc/build_game32.py`
builds fine (confirmed by `.exe` mtime moving past each source edit,
including this one). Unexplained: `build_game32.py` also just calls
`shutil.which(CC)` and would exit if it failed, with no PATH trick visible
in it or `build_process.py` -- so something resolves `i686-w64-mingw32-clang`
for that script's own process that a fresh `python -c "shutil.which(...)"`
in the same shell does not. Not chased further; the game build (the thing
actually shipped) works, which is what mattered for live verification.

## Done 2026-10-06: centre the level-stars row instead of right-anchoring it

A monster can carry up to 12 stars (Blue-eyes Ultimate Dragon; the field
is 4 bits, so a mod could reach 15), each a fixed 9px native sprite with
no gap. The stars row reused retail's own convention -- a fixed anchor for
the *first* star, walking left for the rest, unbounded -- which at the old
position (`x:80`) would put 12 stars' left edge at `x:-19`, 19px past the
frame's own left edge.

`func_80028B08.c` now centres the row the card actually has around
`star_layout.x` instead (`sa + star_layout.x + 9*count/2 - 9`), the same
convention `atk_layout.x`/`def_layout.x` already use for their own box
centre under full-bleed -- not new territory, just extended to stars.
`"stars"."x"` moved from `80` to `59` (`hd_assets_pack.py`,
`notes/modding.md`) to keep a 12-star row centred between the frame's own
left margin and the attribute ball's left edge (`x:114`) with a px or two
to spare. Verified live at 1 (Left Arm of the Forbidden One, id 20), 8
(Blue-Eyes White Dragon), 11 (Gate Guardian, id 374) and 12 stars
(Blue-Eyes Ultimate Dragon, id 380, the base game's widest) -- no
overflow at any count.

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

## Self-testing method: the control channel, not raw MEMORIES_INPUT

**Superseded 2026-10-06** -- `notes/agent-control.md` documents a proper
scripted client (`tools/pc/yfm_control.py`'s `Game`) that this entry had
been missing; the raw-`MEMORIES_INPUT`-hex method below still works but is
strictly worse (slower, no deck/hand control, frame numbers guessed by
hand) and should not be reached for first. Use this instead:

```python
import sys; sys.path.insert(0, "tools/pc")
from yfm_control import Game

with Game(mods_dir="tmp/pc/shared-mods",                    # the real, already-built HD pack (see below)
          settings={"mod.forbidden-memories-hd": 1}) as game:
    game.goto("duel", opponent=1, deck="364,670")            # any two (or more) card ids, real draw order
    game.duel_ready(before_deal=lambda g: g.arrange_deck(0, [364, 670]))  # guarantees hand slots 0/1
    game._hand_to(0)                                         # move the cursor to a known slot
    game.press("circle", hold=6, after=30)                   # select
    game.press("triangle", hold=6, after=60)                 # open the big viewer
    game.shot("card.ppm")                                    # raw .ppm; PIL to view/share
    game.press("circle", hold=6, after=30); game.press("circle", hold=6, after=30)  # back to the hand
```
Seconds per run (not ~115s), fully deterministic (`MEMORIES_DETERMINISTIC=1`,
which `Game` sets), and gives a *real* mixed deck/hand instead of
`MEMORIES_DEBUG_DECK` forcing all 40 cards to one id -- needed for anything
that depends on two specific cards coexisting (a ritual monster + its
ritual spell, tested this way 2026-10-06: `tmp/pc/control/ritual-view/`).
`mods_dir`/`settings` are needed because `Game` otherwise only loads the
mods shipped beside the executable (`tmp/pc/game32/mods/`), not the local
test rig mod at `tmp/pc/shared-mods/assets-hd` (see below) -- without
them you get retail's own small-frame view, not full-bleed, with no error.
`game._hand_to(slot)` is "private" (leading underscore) but the clean way
to reach a known hand slot; `game.duel()[0]["hand"]` confirms what's
actually there by id before relying on slot order.

### Older method (raw MEMORIES_INPUT), kept for reference only

```
BASE=$(python -c "import json;print(json.load(open('tests/pc/smoke/duel-hand-camera.json'))['input'])")
INPUT="${BASE},6600:2000,6606:0000,6650:1000,6656:0000"   # Circle then Triangle: open the big viewer on the selected hand card
MEMORIES_DEBUG_DECK=<card id>   # forces the whole 40-card deck to one id
MEMORIES_INPUT="$INPUT" MEMORIES_DUMP_FRAME=6750 MEMORIES_DUMP_PATH=<out.ppm> tmp/pc/game32/memories-pc.exe
```
Real-time, ~115s wall-clock per run. `MEMORIES_LOAD_STATE` does not work
post-rebuild (symbol table changes every build) -- the control-channel
method above doesn't need save states at all, so this limitation doesn't
carry over. Card ids: `notes/card-catalog.csv`. Dump is a raw `.ppm` --
convert with PIL (`Image.open(...).resize(..., Image.NEAREST)`) before
sharing/viewing, same as the newer method.

## Known, not yet done

- Temporary diagnostic `LOG(LOG_CARD_LAYOUT, ...)` lines are still in
  `src/pc/cards/card_layout_art.c`'s `CardLayoutArt_FrameCell` and
  `src/game/func_80028B08.c`'s `DrawFrame` call site (both predate this
  entry). **Remove before this branch is PR-ready.**
- Monster's `art`/`atk`/`def` positions are still the old standalone mod's
  numbers -- confirmed by pixel-measuring the *new* art's own art-hole and
  ATK/DEF plaque-box bounds (2026-10-06): they already match the new art
  closely (within ~2px), so no change was needed, but they haven't been
  independently re-derived from scratch. `stars` *has* been redone (centred,
  see above) -- not in this bucket anymore.
- `monster-ritual-animeframe.png`/`monster-obelisk-animeframe.png`
  (`hacking/asset/frame/`, outside this repo) are drawn but **intentionally
  unused**: the engine's `CARD_FRAME_*` enum has exactly one free slot
  (`purple`) and neither ritual monsters nor the three God cards are
  auto-detected today (unlike effect monsters' automatic `orange`) --
  wiring either in needs per-card `Cards_FrameColor` overrides added to
  the HD pack's card data, deferred by user decision (2026-10-06) rather
  than picking one arbitrarily.

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

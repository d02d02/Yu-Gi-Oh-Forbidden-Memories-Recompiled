# Progress

Replaces `TODO.md`. Committed (was git-ignored through `.git/info/exclude` until
2026-09-28, when it started being tracked so it travels across machines — see
"Switching machines" below). Research files live in `tmp/pc/todo-research/`
(not committed, `/tmp/` is gitignored). Each item below tracks what's decided,
what's done, and what's left — update in place as work continues instead of
re-deriving it next session.

## Switching machines

**2026-09-28.** Moving from this Windows machine to a native Linux install to
continue [PGXP cross-OS testing](#pgxp-unchiga-says-distortion-on-either-setting--not-documented-anywhere-needs-real-cross-os-data).
Everything needed to resume is committed and pushed to `origin` (the fork),
except the disc image (`game/*.bin`, gitignored, copyrighted, re-supply it
locally): this file, `notes/*.md`, and a copy of the real memory card
(`memcards/slot01.sav`, `memcards/README.md` — not a save state; see that
README for why). Current branch: `feat/precise-geometry`, commit 1 only
(Video menu option, Textures) — see the PGXP section below for what's next.

## How to test things

- My debug build: `tmp/pc/game32dbg`, with its own user folder `tmp/pc/game32dbg-user`
  (saves, states and settings kept apart from the real game).
- Run it (PowerShell, repo root):
  `$env:MEMORIES_USER_DIR = "tmp\pc\game32dbg-user"; tmp\pc\game32dbg\memories-pc.exe`
  (add `$env:MEMORIES_LOAD_STATE = "N"` to start from state slot N).
- Reach a screen with no save needed: the options smoke input plus `MEMORIES_MODE_AT=1000:<mode>`
  (modes in `src/game/main_modes.h`: 4 Library, 7 Build Deck, 9 Name entry, 10 Password, ...):
  `MEMORIES_INPUT="910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,1040:0040,1046:0000,1060:0040,1066:0000,1100:4000,1106:0000" MEMORIES_MODE_AT=1000:9`
- Dump a frame: `MEMORIES_DUMP_FRAME=1500 MEMORIES_DUMP_PICTURE=1 MEMORIES_DUMP_PATH=out.ppm`
  (add `MEMORIES_DUMP_VRAM=1` for VRAM; it drops bit 15 of each word).
  **Needs a real window to show anything GL-only (PGXP, HD text): with `MEMORIES_HEADLESS=1`,
  `Platform_Open` never creates a GL context at all, so the dump is the software GPU's picture
  and is byte-identical regardless of any GL-only setting.** Drop `MEMORIES_HEADLESS` (a real,
  visible window pops up) or add `MEMORIES_DETERMINISTIC=1` alongside it (same fast
  frame-stepping as headless, but a real window/GL context still gets created) to actually
  see a GL-pass effect in a dump. `MEMORIES_DUMP_FRAME`'s frame count is *this run's own*,
  starting from 0 at boot — after `MEMORIES_LOAD_STATE`, it does **not** jump to the frame
  number the state was originally saved at; the state resumes around frame 30 and the count
  keeps going from there.
- PPM to PNG, or a zoomed crop: `python tmp/pc/hd-text-split/crop.py in.ppm out.png [x y w h zoom]`.
- **`MEMORIES_INPUT`'s hex bits are the raw PSX controller (SIO) layout, *not*
  `src/game/input.h`'s `PAD_BUTTON_*` enum** — those are two different encodings in this
  codebase and it's easy to grab the wrong one (cost real time this session):
  `0001` Select, `0002` L3, `0004` R3, `0008` **Start**, `0010` Up, `0020` Right, `0040` Down,
  `0080` Left, `0100` L2, `0200` R2, `0400` L1, `0800` R1, `1000` Triangle, `2000` Circle,
  `4000` **Cross**, `8000` Square. Confirmed against `mods/hand-camera`'s own hard-coded
  defaults (`turn_right`=R1=`0x0800`, `turn_left`=L1=`0x0400`, `zoom_in`=L3=`0x0002`,
  `zoom_out`=R3=`0x0004`). A known-good deterministic path from cold boot into a real
  campaign duel with a 3D-Monsters model on the field: replay
  `tests/pc/smoke/duel-3d-monsters.json`'s own `input` field verbatim (reaches frame 6760,
  a card-placement reticle screen) with `mod.3d-monsters`/`mod.hand-camera` on; from there,
  `<frame>:4000,<frame+6>:0000` (Cross) places the highlighted card face-up in its default
  (Attack) position, `<frame>:0008,<frame+6>:0000` (Start) ends the turn.
- **A save state made by the user's real `game32` build will not load in the debug
  `game32dbg` build**, even when both report the identical `buildid` — cross-build state
  loading fails outright (`state load failed`, likely the mods' own compiled checksums
  differing between a release and a debug build). Don't try to copy the user's states over.
  Instead, **build a state from inside `game32dbg` itself**: script the input above (or drive
  it live, windowed, no `MEMORIES_DUMP_FRAME`/`MEMORIES_HEADLESS`, and press F5 by hand) with
  `MEMORIES_SAVE_STATE="<frame>:<path>"`, then reload that state as many times as needed with
  `MEMORIES_LOAD_STATE=<same path or slot>` — each reload only needs ~60 frames to resume and
  is fast, so do the slow scripted/live part once, then iterate cheaply from the saved state.
- `MEMORIES_MOD_3D_MONSTERS_TEST=<card id>` (undeclared, not in the Mods window) fills *every*
  field zone with a different monster at once (`id + zone*2 + side`), bypassing the
  face-up/occupied check entirely — good for a forced-visible stress test, bad for realism:
  with only `CACHE 8` model slots in `mods/3d-monsters/field_models.c` but up to 10 zones
  requested, it thrashes reloading models every frame and runs very slowly. Fine for a single
  frame dump; don't run it live/windowed for long, and don't read anything into the slowdown
  itself — it's a separate, pre-existing, unrelated limitation of this test tool, not of
  whatever is actually being tested.

---

## Status board

| # | Item | Status | Branch | Next step |
|---|---|---|---|---|
| **0** | **URGENT: measurement framework for 3D rendering (PGXP and models)** | **Scene `field` researched 2026-09-28, being built** | `feat/test-scenes` | Test scenes mod, scene `field` (real cards, Simon, standard field), started by L1 + Cross on Option |
| 1 | Name entry: END/arrows HD | Mostly done | `feat/hd-text-name-entry` | Guard against other slot uses (small) |
| 2 | Duel results letters HD | Not started, plan ready | — | Extend the digit `Sheet` to the alphabet |
| 3 | Lettering follow-ups (PR #107 review) | Not started, latent | — | Word-width clamp; sibling redraw |
| 4 | Tests for HD text | Not started | — | One smoke case, name entry at 4x |
| 5a | Build Deck: browse cards Up/Down | Done, tested — **check upstream first, see below** | `feat/card-viewer-browse` | Confirm not a duplicate, then open PR |
| 5b | Trade: browse cards Up/Down | Done, PR open, needs live test — **not a priority right now** | `feat/card-viewer-browse-trade` | Live session, owned deck, whenever it becomes a priority |
| 5c | Library: browse cards Up/Down | Not started, assessed (big) | — | Start with "replay retail steps" |
| 6 | Crash: title jump after cross-build state load | Cause likely found | — | Verify `state_remap.c` remaps `D_800E9DC0` |
| 7a | PGXP: menu option, Textures only | **Done, clean on Windows + Linux** | `feat/precise-geometry` (commit 1) | — |
| 7b | PGXP level 2 (positions/wobble) | **Green light, 2026-09-28** — to redo from the 7b design | `feat/precise-geometry` (commit 2) | Implement `Pgxp_DrawId` + `PGXP_VERTEX_WORDS` |
| 7c | HD model textures (`MODEL.MRG`) | Blocked: tags lost before pack lookup | — | Trace `model_texture_transfer.c` / `model_apply_texture_tint.c` |
| 7d | Duel field tile: bright diagonal sliver, intermittent | New, not started, confirmed **not** PGXP | — | See 7d below |
| — | Game > Restart | Parked | — | — |

**Superseded, 2026-09-27: the messy history.** `feat/pgxp-reenable-textures` and
`fix/pgxp-seam-identity` (the branches 7a/7b were on earlier this session) are **abandoned** —
the user asked for a clean rewrite from scratch, off `upstream/master` rather than the stale
`origin/master`, without the false starts (a menu.c mistake reverted, a signal-blocking dead
end, diagnostic logging added then removed, a self-introduced bug found and fixed same-day).
`feat/pgxp-video-option` and `fix/pgxp-snap-seams-identity` (below) are the real, current
branches — same fixes, correct from the start, no debug-logging noise, no `Claude-Session`
trailers (the user does not want those in this repo, [[no-session-trailer]]). The detailed
methodology write-ups under 7a/7b further down are still worth reading — how the bugs were
found doesn't change — just mentally substitute the new branch names.

**Also found while rewriting: `origin` (this fork) is stale relative to `upstream` (Unchiga's
real master, ~40 commits behind at the time) — always fetch and check `upstream/master`
before starting new work, not just `origin/master`.** One of those upstream commits,
`e69248c23` "Build Deck: Up and Down in the card viewer show the list's next card", looks like
it may duplicate item 5a's own feature — **check this before opening that PR**, not yet done.

### PR plan (branches ready to open, in order)

Dependency: `fix/pgxp-snap-seams-identity` is stacked on `feat/pgxp-video-option` (needs it as
a base, not `master`) — open 7a before 7b, or GitHub will show 7b's diff against master
including 7a's changes.

1. **`feat/pgxp-video-option`** (7a) → base `master` (really `upstream/master`). Tested live
   by the user. **PR open.**
2. **`fix/pgxp-snap-seams-identity`** (7b) → base `feat/pgxp-video-option`. Verified by both
   the user (live) and a deterministic stress repro (10 monsters, level 2, no gaps).
   **PR open.**
3. **`feat/card-viewer-browse`** (5a) → base `master`, but **check the e69248c23 duplicate
   concern above first.**
4. **`feat/card-viewer-browse-trade`** (5b) → base `master`. Open whenever, low priority;
   works but its live test is deprioritized, not a blocker to opening the PR itself.

---

## 0. URGENT: measure what PGXP (and later, model work) actually changes

**Why, 2026-09-28.** Level 1 and level 2 are justified by theory (affine texture
warp, whole-pixel vertex snapping), but nobody has measured how much of either is
*visible*, where, and under what conditions. "No distortion seen" on both machines
is a by-eye result and says nothing about the benefit either. The user will not
write the PR, or start the model work, on claims that aren't measured. The
framework is meant to outlive PGXP: the model work (7c, HD textures) needs the
same "same frame, two settings, a number" comparison.

### What each level does, stated as testable claims

**Level 1 (Textures).** On console, a textured triangle's UVs are interpolated
linearly in screen space (affine). Level 1 interpolates `uv / w` and `1 / w`
instead (perspective-correct, `gl_picture.c`, flag 32). The vertex stays on its
whole console pixel; only where texels land *inside* the triangle changes.
The affine error grows with the spread of the three depths and the triangle's
size. Claims to check:
- visible on **large, steeply tilted, textured** polygons near the camera (duel
  field floor, battle-animation close-up, Library model view zoomed in);
- **invisible** on small on-screen triangles (3D Monsters field figures);
- no change at 1x and on 2D screens (menus, Options).

**Level 2 (Textures and positions).** The GTE rounds each projected vertex to a
whole console pixel; at internal Nx that is up to N/2 screen pixels. Claims:
- the effect is **temporal**: a still frame looks almost the same; it shows as
  stepping ("wobble") when the camera or model moves **slowly**;
- stronger at higher internal resolution and on small models;
- known risk: gaps between a model's parts (the #83 rollback), which the
  `draw_id` design (7b) is meant to remove.

### Evaluation of the first draft (2026-09-28) — what was wrong with it

Checked against the code (`libgpu.c`, `platform_common.c`, `gl_picture.c`,
`settings.c`) before building anything:

1. **It had no controls, so no noise floor.** An image diff between two runs
   shows *a* difference, not that PGXP caused it. Needed: the same setting
   twice (must be 0 changed pixels, or determinism is broken), 1x and a 2D
   screen (must be 0: PGXP does nothing there), and the software picture's hash
   identical across levels (the notes say the game and VRAM never see PGXP;
   that makes frames line up across levels, and must be checked, not assumed).
2. **Thresholds were not fixed before looking.** "Visible" must be defined up
   front (below), or the numbers get read to fit whichever claim is wanted.
   That is exactly the "selling" to avoid.
3. **Texel error is the wrong unit on its own.** What the eye sees is how far
   the texture moves *on screen*: texel error × screen pixels per texel. A
   1-texel error on a minified texture is sub-pixel; on a magnified one at 4x
   it is several pixels. Report screen pixels as the main number.
4. **The analytic "max error" formula was hand-waved.** Replace it with direct
   sampling: at a fixed set of barycentric points per triangle (vertices' edge
   midpoints, centroid, a 4x4 grid), compute the affine UV and the perspective
   UV from the same `u, v, q` that `polygon()` already has, and take the max
   distance. Exact enough, simple, no derivation to get wrong.
5. **Level 2 "second differences of a vertex's path" is not doable as written:**
   vertices have no identity across frames. Two measurable things instead:
   (a) per frame, `|precise - rounded|` in screen pixels for every precise
   vertex, which is the wobble's *amplitude* upper bound; (b) the perceptual
   question (does it look smoother?) as a **blind A/B**: the same slow camera
   pan rendered at both levels, shown side by side in random order, the user
   picks without knowing which is which. Some things are not a single number;
   a blind test keeps them honest.
6. **The level-2 amplitude can be measured now, without commit 2.** Precise
   positions are computed at level 1 too (`find_precise` sets `fx, fy`); only
   their *use* is gated. So (a) above runs on today's branch.
7. **The #83 gaps can be measured before fixing them.** Level 2's code
   (`snap_seams`, `libgpu.c:386`) is still in the tree; only the `pgxp` clamp
   (`settings.c:117`, max 1) hides it. A measurement-only build with the clamp
   at 2 gives the *before* number for gaps; commit 2 then has to bring it to
   zero. The first draft had no baseline for the fix it wants to ship.
8. **Gaps "against a flat background" do not exist in real scenes.** Measure
   them geometrically instead: within one draw, vertices that share a rounded
   screen word (the same model point drawn by two parts) must land on the same
   final position; log the spread. A spread above 0 at level 2 is a crack of
   that width. No image mask needed.
9. **It could not find a driver bug.** Geometric metrics are the same on every
   GPU; Unchiga's distortion may be Nvidia/XWayland-only. So the capture must be
   a **single script anyone can run** (Unchiga included) that outputs the
   report and the images, so his machine produces comparable data.
10. **Unchiga's field edge has a concrete suspect the draft missed.** Flag 32
    needs all three depths; a vertex clamped off screen gets none, so its
    triangle falls back to affine while its neighbour is perspective. Along
    their shared edge the texture no longer lines up: a visible break near the
    screen edge, which is where the video shows it. Measure: count triangles
    with 1 or 2 precise vertices (mixed), their area, and whether they touch a
    fully precise triangle.
11. **Multi-frame capture does not exist.** `MEMORIES_DUMP_FRAME` writes one
    frame and calls `exit(0)` (`libgpu.c`), and deterministic timing is only on
    when it is set (`platform_common.c:216`). A pan of 60 frames would be 60
    runs. Add a frame *range* (dump every frame from A to B, then exit), kept in
    the measurement code.
12. **Answered open question:** dumps are at internal resolution
    (`MEMORIES_DUMP_PICTURE` reads the GL picture back at `SoftGpu_Scale()`), so
    sub-pixel effects are captured. `MEMORIES_SCALE_AT=<frame>:<scale>` scripts
    the resolution.
13. **Missing factor:** PS1 games often subdivide large polygons, which shrinks
    affine error on its own. This game has at least one subdivided model effect
    (`notes/model-subdivided-effect.md`); whether the field floor is subdivided
    is unknown.
    If the field floor is subdivided, level 1 may do little there. Check which
    scenes' big polygons are subdivided before predicting.

### Thresholds, fixed before measuring

- Level 1, a triangle is **visibly changed** if its max texture displacement is
  **≥ 1 screen pixel**; **clearly visible** at **≥ 2 px**. Below 0.5 px:
  invisible.
- Level 2, a vertex's rounding is **noticeable in motion** at **≥ 1 screen
  pixel** of `|precise - rounded|`.
- A crack is any seam spread **> 0** at level 2 (should be 0 after commit 2).
- A scene "shows level 1" only if clearly visible pixels are **≥ 1% of the
  frame** or form a region the blind A/B picks reliably (≥ 8 of 10).
Changing a threshold after seeing data must be written down here with the reason.

### Measurements

| # | What | Level | Needs | Output |
|---|---|---|---|---|
| M1 | Texture displacement per textured triangle (sampling, screen px) | 1 | trace in `polygon()` | histogram, % of frame ≥ 1 / 2 px |
| M2 | Mixed-precision triangles (1-2 precise vertices) and neighbours | 1 | same trace | count, area, location |
| M3 | Image diff Off vs level 1, with controls | 1 | dumps | changed px, max, crops |
| M4 | `|precise - rounded|` per vertex, screen px | 2 | same trace, works today | distribution per frame |
| M5 | Seam spread within a draw (cracks) | 2 | measurement build, clamp 2 | before (old code) / after (commit 2) |
| M6 | Blind A/B of a slow pan | 1, 2 | frame-range dump, video | picks out of 10 |
| M7 | Same script on Unchiga's machine | all | the one-command runner | his report next to ours |

### Pipeline

- **Scenes:** built by the test-scenes mod below (not save states), plus
  scripted `MEMORIES_INPUT` camera moves (hand-camera mod: L1/R1 rotate, L3/R3
  zoom). **Controls:** main menu and Options (expect zero change).
- **Runner** (`tools/pc/`, one command, reaches scenes through
  `MEMORIES_TEST_SCENE`, never through menus): for each scene × level (0, 1, and 2 in
  the measurement build) × scale (1x, 2x, 4x): run deterministic with a window,
  dump the frame range, write the trace log. Checks the controls first and
  stops if they fail.
- **Analysis:** reads logs and PPMs, applies the thresholds above, writes one
  table per scene plus crops of the largest changes and the A/B clips.
- **Branch:** measurement code on its own branch; decide later what (if
  anything) ships upstream as a trace category.

### Test scenes mod (decided 2026-09-28, the user's idea)

**Idea.** A mod that, when enabled, offers a menu entry that drops straight into
a prepared scene: a duel with chosen monsters already on the field, a battle
close-up, a model view. This replaces save states as the source of scenes.

**Why it beats save states.** States are tied to one build: the debug build
cannot load the release build's states, and Unchiga's build could not load ours.
A scene built by a mod from fixed data is the same on every build and machine,
so Unchiga can open the exact scene we measured, on his Nvidia PC (M7).

**What makes it deterministic — not the menu.** Fixed scene contents, a fixed
RNG seed (`notes/rng.md`), fixed settings, a frozen duel (the player's first
turn, the opponent never moves, so the AI cannot change the field) and
scripted camera input. The menu is how a *person* gets there; the runner uses
`MEMORIES_TEST_SCENE=<name>` and the same code path.

**Scenes, each for a measurement case:**

| Scene | Contents | Serves |
|---|---|---|
| `field` | Chosen monsters on both sides (a small, a medium, a large model), player's first turn; camera path sweeping the field's edge across the screen | M1-M5, Unchiga's field-edge video |
| `battle` | Two chosen monsters in the battle animation, close-up | M1, M3, M6 (large polygons in motion) |
| `model` | One monster filling the screen | M1 (largest triangles), level 1 at its most visible |
| `small` | Many small field figures (the 3D Monsters `test` case, bounded to the model cache) | M4, M5 (level 2 gaps on small models, #83) |
| `control` | A 2D screen | Must show zero change at every level |

**What already exists to build on:**
- The game's own debug menu (`notes/debug-menu-entry-map.md`): `DUEL`
  (`DebugMenu_EnterDuel`, `src/game/frontend_scene_states.c:157`) arms a duel
  directly; `3D` enters `Main_RunAnimatedBattle` with the game's model-ID
  editor and stage picker (`notes/model-debug-controller.md`) — a ready
  "any monster, close-up" scene.
- 3D Monsters mod test tunables: `test` (every field zone a chosen monster,
  `field_models.c:1301`) and `battle_test` (the battle's two monsters,
  `field_models.c:1119`). Models only, not real duel cards.
- The `SCENE` hook (`notes/mod-api-3.md`) wraps `Main_ApplyMenuSelection`:
  a mod can redirect a menu choice into its own scene.
- `MEMORIES_MODE_AT` already forces a main mode from a given frame.

**Menu entry — decided 2026-09-28 (final): hold L1 + Cross on Option.** With the
mod applied, confirming **Option** on the title menu while **L1** is held starts
the test duel; plain Cross still opens Options. No new menu item, no label, no
layout change. The mod wraps `MainMenu_UpdateFrontendMenu` (both title paths,
`Main_RunFrontendLoop` at boot and `Main_RunMenu` after, call it; overlay
functions are hookable, `yamyi-mods/menu_back_confirm.c` does it): when it
returns 4 (Option) with `PAD_BUTTON_L1` (0x4, the game's pad word
`gInput_wPad1Held`, not the SIO layout) held, the mod remembers it; the `SCENE`
event (selection 4) then arms the duel and is marked handled. The game's own
`Main_RunMenu` fades out and destroys the menu *before* applying the selection,
so leaving the title needs nothing extra. No `MEMORIES_TEST_SCENE` needed: the
runner replays the known Option input (see "How to test things") with L1 held.

Superseded — the earlier plan, kept for the reasoning: an entry in the **first
title menu** as a sixth item. The costliest part:
- The five entries are prebuilt label *pictures* from the menu package
  (`gMain_apMenuEntries`, 11 display objects, `src/overlays/main_menu/README.md`
  "What the menu shows"), not text: "TEST SCENES" needs a label made (port text
  rendering, or composed from the game's font).
- Layout is fixed for five: y = `i * 32 + 50`, group centred at 114; cursor wraps
  at 5. A sixth means redoing both in `MainMenu_InitFrontendMenu` /
  `MainMenu_UpdateFrontendMenu` (hookable from a mod, API 4).
- Choosing it is easy: the selection goes through `Main_ApplyMenuSelection`,
  i.e. the `SCENE` mod event; the mod handles it and arms the duel.

**Scene `field` — decided with the user 2026-09-28.** A normal duel against
**Simon Muran** on the **standard field**; at the moment it is waiting for the
player's first move, zones 1-5 on both sides already hold chosen monsters,
**real cards** (face-up, attack), whose 3D models then appear because the 3D
Monsters mod is on. Card lists in the mod's JSON, editable. No input needed:
wait for the camera to settle, measure.

**Research answers (read, not built), 2026-09-28:**
1. **Arming the duel.** `func_80024DC8(a0, a1, a2, a3)`: `a0` → `D_8009B360`
   (side 0 controller, `-1` = human), `a1` → `gDuel_bOpponentID` (**Simon Muran =
   1**, `tables.c:35`), `a2`/`a3` → `D_8009B370/72` = campaign scene to continue
   to after a win/loss (only used when the return mode is 2; irrelevant here).
   It sets `gDuel_bTerrain = 0` (standard field, no boost) and main mode 3
   (duel). `D_8009B368` = mode to return to after the duel. Debug entry:
   `func_80024DC8(-1, 1, 0x8000, 0x8000)`; Free Duel: `(-1, id, 0x6000,
   0x6000)` + `D_8009B368 = 6`.
2. **The chest screen in between.** `Main_RunDuel` sub-state 0 (opponent >= 0,
   `D_8009B369 == 0`) opens the pre-duel deck chest; the mod must skip it
   (set `D_8009B26E = 1`). Sub-state 0 also does `Fade_WaitIn/Out`,
   `SD_BGMFadeOut`, `Main_ResetFrontendRuntime` when it leaves. **Answered:**
   the skip needs none of them. 2P Duel (`main_run_two_player_duel_setup.c`)
   arms with opponent -1, which goes straight to sub-state 1 after only its
   own fade-out; from the title, `Main_RunMenu` has already faded out. So:
   wrap `Main_RunDuel`, let its first call run, then `D_8009B26E = 1`.
   After the duel: `D_8009B368 = MAIN_MODE_MENU` (8), like 2P Duel.
3. **A field card comes from the deck, not an ID.** `Duel_SetupCardRecord(zone,
   deck_index)` copies stats and the card's picture from the combined deck
   (80 = 40 + 40), whose pictures are fetched in startup (`Duel_RequestCombined
   DeckData`, first startup frame) and unpacked in startup sub-state 4
   (`Duel_PopulateCombinedDeckData`). So the chosen IDs must be in the shuffled
   lists (`gDuel_awPlayerShuffledDeck`, player 0-39, opponent 40-79) **after**
   `Duel_ShuffleBothDecks` (end of `Duel_InitScene`) and before startup's
   first frame. **Overwrite all 80:** with no save loaded the player's deck is
   zeros, and ID 0 makes the picture fetch read sector -1. Filling all 80
   also removes the shuffle's randomness from the field and the hand.
4. **Deck positions.** The draw takes from `deck_draw_cursor`, 0 upward
   (`duel_draw_resolution.c:106`), so put the field cards at 35-39 / 75-79.
5. **Records.** 15 per side: 0-4 hand, **5-9 monster zones**, 10-14 magic/trap;
   opponent +15 (zones 20-24; `SIDE_ZONE` in `field_models.c`). Place with
   `func_80024D34(zone, deck_index)`: fills the record (flags =
   `DUEL_CARD_FLAG_OCCUPIED` only = face-up attack), uploads the card art and
   name strip, creates the field display object. The 3D Monsters mod reads
   only `card_id` + flags (`field_models.c:1303`): models follow for free.
6. **When to place.** Scene states (`duel_scene_callbacks.c`): 1 startup → 3
   draw resolution (deals 5 to side 0) → 4 hand actions (player's turn,
   waiting). The first turn skips state 2 (turn reset). Place on the **first
   call of `DuelScene_UpdateHandActions`**. The deal touches hand records only.
7. **Nobody moves.** `Duel_InitScene` sets `D_8009B1D5 = 0`: the player starts;
   the opponent never acts until the player ends the turn.
8. **Hooks exist (API 4).** `host->hook` wraps any `src/game` function: wrap
   `Duel_ShuffleBothDecks` (`srand`, original, overwrite 80 IDs) and
   `DuelScene_UpdateHandActions` (place once, then original). No new event
   needed. `Main_ApplyMenuSelection` = `SCENE` event for the title entry.
9. **Placing, exactly as the game does:** `DuelScene_UpdateResume`
   (`duel_phase_entry.c:60-84`) rebuilds field cards with
   `func_80024D34(zone, deck_index)` then
   `Duel_ApplyCardObjectFlags(DUEL_CARD_DISPLAY_OBJECT_VIEW(rec->object))`.
   Deck index is the combined one (player 35-39, opponent 75-79).
10. **Seeding:** the mod SDK's `srand` is the *host* C library's
    (`src/pc/mods/sdk/stdlib.h`), not the game's; write the game's
    `gRand_dwSeed` (`src/pc/rng.h`) directly.
11. Scenes `battle` / `model` (`Main_RunAnimatedBattle`, `D_800EF658`) not
    researched yet.

### Next steps (in order)

1. **Answer the four unknowns above** (read code, no building yet), and settle
   the menu decision.
2. **Test scenes mod, first scene `model`** (likely easiest: the game already
   has the scene), reached by `MEMORIES_TEST_SCENE`. Confirm determinism:
   same setting twice → 0 changed pixels; software picture hash equal at
   levels 0 and 1.
3. **Scene `field`**, then `battle`, `small`, `control`.
4. **Trace in `polygon()`:** M1, M2 and M4 in one log line per triangle,
   behind a new trace category. Run on the scenes at 2x and 4x.
5. **Read M1/M2/M4 against the thresholds** — the first real answer to "is
   level 1 visible, where, and what does level 2 have to fix".
6. **Frame-range dump**, then M3 and the blind A/B (M6).
7. **Measurement build with the clamp at 2:** M5 before; then commit 2 and M5
   after.
8. **Package the runner** (mod + script) for Unchiga (M7), with a note on what
   to send back.
9. Menu entry for people (overlay, then title screen if still wanted).
10. Reuse for the model work (7c).

---

## 1. Name entry: END and the arrows are not HD

**Seen:** new game, "Input your NAME!": the letters and digits are HD, but the orange
**<-** **->** and **END** are still retail pixels. Screenshot: `tmp/pc/todo-research/name.png`.

**Cause (verified):** they are not characters. The game draws its own pictures in unused
Shift-JIS slots of the large (16x16) font, page 640,0:

| Cell (u, v) | Shift-JIS slot | Picture |
|---|---|---|
| 176,120 / 192,120 | `0x827B` / `0x827C` | <- and -> |
| 224,120 + 240,120 | `0x827E` + `0x827F` | END, one word across two cells ("E" + "ND") |
| 144,88 / 224,88 | `0x8259` / `0x825E` | a `:` and a `?` of the keyboard's own (bottom row, cut off) |

HD text only redraws a cell `Glyphs_CellCharacter` (`src/pc/text/glyphs.c`) maps to a
character, and that only tries `'!'..'~'` at their usual slots, so these cells return 0 and
`HdText_Cell` (`src/pc/text/hd_text.c`) leaves them as they are ("a glyph no font can set
(an icon) stays as it was", `hd_text.h`).

**Decisions / done (branch `feat/hd-text-name-entry`, not committed):**
- `:` and `?` were not pictures: a typo in `retail_cell` (`glyphs.c`) put the large font's
  `: ; < = > ?` at a negative column (`i * 16 - 0x160`; the small font's `i * 8 - 0x30`
  shows it should be `- 0x60`). The game's 8-bit u wraps it, the port's int did not, so
  those six were pixelated in the large font everywhere. Fixed.
- <- and -> now HD: `Glyphs_CellCharacter` maps the large font's cells 176,120 and 192,120
  to U+2190 / U+2192. Checked on the name entry screen.
- END done: `render_at` generalised to `render_span` (a word across a strip of cells, each
  cell keeps its slice), `Glyphs_CellWord` names END. Committed `f315bd7`, not pushed.
  Checked: name screen changes only inside END; slot 1 dialogue and slot 3 card view
  pixel-identical to before.

**Left to do:**
- **Guard against other uses of those slots:** the same Shift-JIS slots may hold other
  pictures on other screens or fonts. Identify the cells by their pixels (a checksum of the
  retail cell, as the card view's panel does with `PANEL_SUM`), not just by position.

**Check after:** the name entry screen (mode 9 above), and screens that type text:
Password (mode 10), save names, the campaign dialogue.

---

## 2. Duel results: "You" and "Simon" are not HD

**Seen:** duel results screen, the "You" / "Simon" headers (and probably "VICTORY
CONDITIONS", "OFFENSE STATISTICS", ...) are blocky retail pixels; the bars cut their feet,
as in retail. A save state was in `tmp/pc/game32dbg-user/states/slot2.state` (may have been
overwritten since).

**Cause (verified):** not the text font. `{f8 04 01}` in the results strings (0x40-0x45)
draws a separate tiny 8x8 alphabet from the menus' sheet, page 704,0, palette 656,250, as
plain 8x8 sprites (no glyph mark):

| v | row |
|---|---|
| 80 | A-P (u 128, 136, ... 248) |
| 88 | Q-Z |
| 96 | a-p |
| 104 | q-z |
| 112 | 0-9 (already HD: `sheets[1]` in `hd_text.c`) |

"You" / "Simon" are the port's own swap for YOU / COM (`translation.c`, with Video >
Opponent's name for COM), set in that alphabet; "OFFENSE / DEFENSE STATISTICS" too. HD
numbers and labels redraws that sheet's digits but not its letters, so the letters stay
blocky and uneven.

**Decided, not started:** extend the digit `Sheet` (`hd_text.c`) to that sheet's letters:
measure the alphabet's lines together (baseline, capitals, x-height, as `measure_retail` does
for the font pages: the `Lettering` principle) and set each letter with `render_at` in the
sheet's ramp, as the digits are. Only where the retail sheet is (checksum), like the digits.
Check: results pages (all three), and wherever else the menus use that alphabet.

---

## 3. Lettering follow-ups (from the review of PR #107)

Not bugs today, latent:
1. **Word width can overflow:** a label in a lettering is set in the font's proportions
   (`sx = sv` in `set_text`) with no check against its sprite's width. ATK/DFD fit; a longer
   word (a translation) would be clipped. Fix: `sx = min(sv, what fits)`.
2. **Siblings are not redrawn:** a label is only remade when its own texels change; if one
   member of a lettering changes and another does not, the other keeps the old ink/height.
   Fix: each label remembers the lettering measurement it was drawn from and is redrawn when
   that changes.

---

## 4. Tests for HD text

No automated check covers HD text; everything was checked by eye from save states. A smoke
case (`tests/pc/smoke/*.json`: input, frame, SHA-256) with HD text on at 4x on the name
entry screen (reachable with `MEMORIES_MODE_AT`, no save needed) would catch regressions.

---

## 5. Build Deck: browse cards from the card view (Up / Down)

**Wish:** in Build Deck, triangle shows a card's details; to see the next one you must close
the view, move down, and press triangle again. Up / Down inside the view should show the
previous / next card of the list.

**How it works today (read, not yet traced further):**
- `BuildDeck_UpdateChestPaneInput` / `BuildDeck_UpdateDeckPaneInput`
  (`src/game/build_deck_pane_input.c`): triangle takes `BuildDeck_GetActiveCardID(list)`
  (the card at `first + cursor`), writes it to `gDuel_wViewerCardID`, sets
  `gDuel_bCardViewerYOffset = 0x14` and `gDuel_bEffectState = DUEL_EFFECT_STATE_CARD_VIEWER`.
- The viewer is `DuelEffect_UpdateCardViewerState` (`src/game/func_800283F4.c`), shared with
  the duel, the Library and Trade: it loads the card with `func_80029164(3, id)`, shows it,
  and closes on button `0x20`. Nothing links it back to the list.
- `src/game` must stay byte-identical to retail, so the change lives in `src/pc`
  (an override or a mod hook, `src/pc/mods/hooks.c`), not in the decompiled code.

**Decided:**
- **Swap the card in place** (not replay-and-reopen) for Build Deck and Trade. An option
  under the Game menu (like "Use deck slots"), off by default, so retail behaviour is
  unchanged unless turned on.
- **Library and Trade too**, as they use the same viewer.
- ~~Wrap around~~ changed after testing: **stops at the ends** (the user did not like the
  looping). Empty rows skipped.

**Done:**
- **Build Deck: done, tested by the user, PR open** (branch `feat/card-viewer-browse`,
  pushed; not yet merged upstream). **Re-confirmed working by the user, 2026-09-27**, as
  part of testing everything shipped so far before starting new PRs. `src/pc/cards/card_browse.c`, a `MEMORIES_PC` hook in
  `func_800283F4.c`, setting `card_browse` (off by default), Game > Browse cards with
  Up/Down. A `screens[]` table maps main mode to a `move(pad, step)` function, so a screen
  is added without touching `CardBrowse_Poll`.
- **Trade: done, PR open, not yet live-tested** (branch `feat/card-viewer-browse-trade`,
  stacked on top of the Build Deck branch, pushed). `move_trade_cursor` in the same file:
  each side has its own list and pad (`trade_helpers.h`'s `D_80185C8C`/`D_80185CCA`/
  `gTrade_aInventory`/`D_801845EC`), a pad only browses the list its own cursor opened the
  viewer from, guarded the same way Build Deck's pane is
  (`DuelEffect_UpdateState() == 0`, confirmed in `main_mode_runners.c`). Checked: builds
  clean, the smoke suite still passes (no Trade fixture exists), and reached Trade mode
  headless with no crash — but that's the empty-list case.

**Left to do:**
- **Trade needs a live session with an owned deck** (ideally two pads) to confirm Up/Down
  actually works, same as Build Deck needed. **Deprioritized by the user, 2026-09-27** — not
  worth a test session right now. Manual route to a save with cards, whenever it does become
  a priority: after escaping Simon's duel to the shop, save, Circle back to the title, then
  into Trade.
- **Library: not started, assessed.** Its own card display (`library_runtime.c`,
  `func_8002ACA4`, opened with Cross from `library_grid_cursor.c`), not the shared viewer.
  Its own state machine, much more involved than Build Deck's:
  1. loads the card into slot 0 and sets up a 3D camera;
  2. the card flies out of its grid cell to the centre while spinning, the description
     panel slides in;
  3. the grid fades out, the card fades in;
  4. in parallel, once the card has loaded, and if it's a monster: loads its 3D model
     (`Model_LoadMonsterMerge`), then shows a "view model" icon;
  5. **showing**: Circle closes; Triangle/Cross on a monster goes to stage 4's 3D model
     view (camera, lights, animation) — a still bigger state, not investigated;
  6. the grid fades back, the card **flies back into its grid cell**, then everything is
     released.
  Extra problems past Build Deck's: releasing/loading a 3D model mid-swap without a crash
  or leak; the card's fly-back animation targets *the cell it came from*, so browsing to
  another card must retarget it; the grid scrolls, so the next card may be off-page; locked
  ("?") cards must be skipped like Build Deck's empty rows.

  **Two approaches, recommendation: start with 1:**
  1. **Replay the retail steps (safe, slower):** Up/Down triggers the normal close (card
     flies back), then, once the grid is back, moves the grid cursor and opens the next
     card automatically (flies out again). Every animation, the model load and the grid
     scroll are the game's own code — the same principle that already worked for Build Deck
     and Trade. Cost: ~1-2s of fly-back/fly-out animation per card.
  2. **Swap in place (nicer, much more work):** stay in stage 5, release/reload the card and
     its model, retarget the fly-back cell, keep the panel. Needs the 3D model loading and
     stage-4 view understood first. Move to this only if approach 1's animation feels too
     slow once tried.

**Check after (once live-tested):** chest pane and deck pane, empty rows, sorted lists, the
last and first card, Trade with an owned deck, and that the duel's card view (same viewer)
is unchanged.

---

## 6. Crash: jump to title after loading a state from another build

**Seen:** crash reports `tmp/pc/crash-26952.txt`, `crash-26680.txt` (and reproduced):
load a save state made by a different build ("state from build X carried over to Y: N code
addresses moved"), then Debug > Jump to > Title Screen: access violation in `Main_Init`
(+0x144 / +0x166).

**Verified (2026-09-27):** not caused by our branches. No state, or a state made by the same
build: fine, in every build. A state converted from another build, then the title jump:
crashes in the `play.bat` build too, which has no card browsing. Upstream master built fresh
passed the one test tried, but its conversion moved only 7 addresses (vs ~190).

**Likely cause, not yet verified:** the title jump longjmps to the resume point `Main_Init`
saves at boot (`D_800E9DC0`, `TitleJump_Execute` in `src/pc/overrides/title_jump.c`). The
state carries that buffer; the carry-over (`src/pc/guest/state_remap.c`) seems not to remap
the native addresses in it, so the jump lands on a stale address.

**Left to do:** confirm `state_remap.c` doesn't touch `D_800E9DC0`'s buffer, then remap it
like the ~190 other addresses the conversion already moves.

**Repro:** `MEMORIES_LOAD_STATE=<state from another build> MEMORIES_TITLE_AT=120` with the
other build's symbol table in `symbols/`.

---

## 7. 3D models look bad: three separate causes, one fixed, one designed, one blocked

The user's goal: better-looking 3D monster models (the duel field, the battle animation,
the Library's model view). Three independent causes found so far.

### 7a. Warped textures (PGXP, level 1) — done, PR open

**Now on `feat/pgxp-video-option`** (rewritten clean off `upstream/master`; the branch name
below, `feat/pgxp-reenable-textures`, is the abandoned original — see the status board note).
The bug, the fix, and the testing story described here are unchanged; only the branch is new.

**Cause:** the GTE rounds a 3D vertex to a whole console pixel and keeps no depth with it,
which bends a model's textures on tilted surfaces. A fix was already implemented
(`src/pc/compat/pgxp.c`, the HMD polygon drivers in `src/pc/overrides/model_polygon_drivers.c`)
but had **no way to turn it on**: `SET_PGXP` was clamped to 0 in every direction (saved
preferences, `MEMORIES_PGXP`, runtime writes) with no Video menu entry.

**First pass got this wrong — read below before touching this again.** Initially unclamped
the setting to 0-2 and offered both PGXP levels, having only grepped the *current* text of
`notes/pc-build.md` for context, not its *history*. Checking `git log` on that file turned up
`fix/disable-precise-geometry` (Unchiga, PR #83, the commit this branch's first attempt
silently undid) and its removed comment: *"positions too are experimental, they open gaps
in the small monster models."* Level 2 ("textures and positions", the one that also closes
the seams between a model's parts as they move) uses `snap_seams` (`libgpu.c`), which finds
a seam only by **two vertices rounding to the same screen word this frame** — it has no idea
which model or which part a vertex belongs to. On a model small enough that its whole
footprint is a handful of pixels (the 3d-monsters mod's field figures, 32 tall by default),
vertices from unrelated, non-adjacent parts coincide by chance, and forcing them together
distorts a triangle that was otherwise rendering correctly: a new gap where there was none.

**Fix (corrected):** unclamped the setting to 0-1 only (not 0-2) and added **Video > Precise
geometry** with two choices, Off and Textures — not the "positions" level. Gated the same
way as HD text (greyed out below Internal 2x or without OpenGL 3). No game-side change.
`notes/pc-build.md` and `settings.c` both record the `snap_seams` problem.

**Applies to both the field-floating models (3d-monsters mod) and the classic animated-battle
cutscene, and the Library's model view** — all three go through the same call
(`func_800540B4` → `GsSortUnit` → the HMD polygon drivers), so one fix reaches all of them.

**Checked:**
- The deterministic smoke suite (`tools/pc/smoke.py`) passes byte-exact on this branch,
  including `options` (the screen the new menu item lives on).
- `MEMORIES_TRACE=frames` (headless, deterministic): with `pgxp=1`, the 3D Monsters duel
  shows ~300 precise vertex words per frame, matching `notes/pc-build.md`.
- Live, windowed, Internal 2x, duel with a 3D monster: Off vs Textures on the same paused
  frame — no artifacts on the field. Screenshots in `tmp/pc/hd-text-compare/`.
- `tests/pc/settings_test.c` updated to the new 0-1 range, **not run locally** (this Windows
  environment lacks zlib/libpng for a full CMake configure); `pc-build.yml` runs it in CI.

**Left to do:** rename done (branch was `feat/pgxp-textures`, collided with the already-merged
upstream `pgxp-textures`/PR #67 branch name; now `feat/pgxp-reenable-textures`). **Open the
PR** — description should lead with the level-2 finding, not bury it, and link screenshots.

### 7b. PGXP level 2 (positions, closes seams, fixes wobble) — done, PR open

**Now on `fix/pgxp-snap-seams-identity`** (rewritten clean off `feat/pgxp-video-option`; the
branch name below, `fix/pgxp-seam-identity`, is the abandoned original — see the status board
note). The `draw_id` design and the arena-corruption bug it caused (7b-bug) are unchanged and
still worth reading; the rewrite folded the `PGXP_VERTEX_WORDS` fix into the *same* commit
that grows `PgxpVertex`, so that specific bug never existed on the new branch at all — nothing
to find there this time. No debug-logging diagnostics were added or needed.

**Why level 2 is off:** `snap_seams` (`src/pc/sdk/libgpu.c:386`) hashes each projected vertex
purely by its rounded screen word and treats any two colliding vertices — anywhere in the
whole frame — as a seam to close. It has no concept of which model, or even which draw call,
either vertex came from, so on a small model (or two unrelated small models near each other)
coincidence looks identical to a real seam.

**Design for the fix (from a walkthrough on 2026-09-27, not yet coded):**
1. **One shared choke point exists.** Duel monsters, the 3D-Monsters mod's field figures, and
   the Library's card viewer all draw through `func_800540B4` → `GsSortUnit`
   (`src/game/func_800540B4.c:365`, `src/pc/sdk/libgs_unit.c:154`) → the polygon drivers in
   `model_polygon_drivers.c`. Tagging at that one point covers all three screens at once.
2. **Add a `draw_id` counter**, bumped once per `GsSortUnit` call (once per model instance).
3. **Thread `draw_id` through `pgxp.c`'s tables**: `PgxpVertex`, the `Entry` table in
   `Pgxp_Project`, and the `Placed` table in `Pgxp_StoreAt` each grow a `draw_id` field,
   recorded alongside `x, y, w` exactly like `frame`/`stamp` staleness already is.
4. **Change `snap_seams`'s ambiguity check** (`libgpu.c:412`): only ever compare two vertices
   that share a `draw_id`. Cross-model / cross-draw pixel coincidences become structurally
   impossible to snap — they're never even compared. Same-model seam-closing (what
   `snap_seams` was built for, commit `79eff0378`) keeps working.
5. **Optional refinement:** also tag a part/primitive-block index and require it differs
   too, so a model's own coincidental self-overlaps (rare) aren't snapped either. Not needed
   to fix the reported bug (the small-model case), so treat as a later refinement.

**Expected result once done:** level 2 becomes safely re-enablable everywhere a model is
drawn — the wobble-fix (the actual original goal of PGXP, commit `80d4dc369`) ships fully,
not just the texture half. Below level 2, nothing changes; the smoke suite should still pass
byte-exact.

**Implemented** (commit `7e82cafce`, branch `fix/pgxp-seam-identity`, stacked on
`feat/pgxp-reenable-textures`): `Pgxp_DrawId`, threaded through `PgxpVertex`/`Entry`/`Placed`,
bumped once per `GsSortUnit` call; `snap_seams` keyed on `(word, draw_id)`. Video > Precise
geometry offers "Textures and positions" again; `SET_PGXP` range is 0-2.

**Checked, 2026-09-27:** builds clean. Live, from a state built off the
`tests/pc/smoke/duel-3d-monsters.json` fixture: level 2 on the field's own model (several
camera angles, no gaps) and, the real stress case, the field forced full of ten different
monsters at once (`mods/3d-monsters`'s own `test` tunable), several under 32px — the original
repro shape — no gaps or torn triangles on any of them.

**Left to do:**
- Re-run the deterministic smoke suite locally once a full CMake configure is possible here
  (this machine lacks zlib/libpng for it); CI covers it per PR in the meantime.
- The ten-monster stress case exposed a separate, **pre-existing, unrelated** performance bug
  while testing this: `mods/3d-monsters`'s own model cache (`CACHE 8` in `field_models.c`) is
  smaller than what its `test` tunable asks for (10), so it thrashes reloading models every
  frame. Real duels stay well under 8 monsters and never hit this — not a blocker for this PR,
  but worth its own item if `test` stays useful for future stress-testing.
- Open the PR (stacked on 7a's).

### 7b-bug. Arena corruption the seam-identity fix introduced — found live, fixed, done

**Symptom, from the user's own live testing (not caught by any of my own earlier checks):**
thin lines, flickering in and out rapidly, always originating from the screen's left/top edge
(not always the same exact point), on a real duel. Present at both "Textures" and "Textures
and positions"; gone with Precise geometry Off entirely.

**The debugging path — what was tried, what each attempt actually showed, in order:**

1. **First guess: a vertex's looked-up position far from its own word.** Added a diagnostic
   to `libgpu.c`'s `DrawOTag` (where `PgxpVertex` entries get built from `pgxp.c`'s lookups):
   log if `fabsf(precise_x - word_x) > 2px` (or same for y). Built, the user played with
   `MEMORIES_TRACE=frames MEMORIES_LOG=<path>` set so the log went to a file. **Zero hits**
   despite the artifact being visible in that exact session. Wrong guess.
2. **Second guess: a bad (near-zero/non-finite) depth**, added to the same check (the OpenGL
   pass divides by depth for perspective-correct texturing, so a bad one could stretch a
   texture without any vertex position moving, and level 1 never overwrites depth the way it
   overwrites position). Also **zero hits**, same live session, artifact still visible.
3. **Tried fixing the signal-reentrancy gap** in `DrawOTag` (see 7b's commit `14e34a1fd`
   description) as an actual fix, not just a diagnostic, reasoning it could explain
   intermittent, timing-dependent corruption. Built, the user tested: **issue still there.**
   Wrong primary cause (kept anyway as real, separate hardening — see below).
4. **Widened the net: log every precise vertex near the screen edge, unconditionally**, no
   "looks wrong" filter at all. This flooded the log (tens of thousands of lines) with
   *legitimate* off-screen geometry (a field/skybox boundary quad, `draw_id 0`, depth exactly
   `150.0` every time, precise value exactly equal to its own word) — a good reminder that
   off-screen vertices are normal in PS1 rendering and a screen-position filter alone is too
   broad. Grepping this data for `abs(precise - word) > 20px` (rather than eyeballing it)
   found **zero** genuinely large position errors anywhere in the whole log — a strong,
   *exhaustive* negative result: no individual vertex's looked-up position was ever
   meaningfully wrong. That ruled out `pgxp.c`'s lookup tables as the source, definitively,
   for the first time (attempts 1-2 only sampled one session; this scanned everything).
5. **Moved the check downstream, to where a precise position actually gets used**: added a
   log to `gl_picture.c`'s `polygon()`, right after `find_precise()` assigns `v[i].fx/fy`,
   comparing it against the vertex's own base (whole-pixel) position with an 8px threshold.
   This is a *different* comparison than attempt 1 — not "is the cached value sane" but "does
   what got handed to this specific triangle corner match where that corner actually is".
   **This found it immediately**: dozens of hits, and critically the values were not just
   "wrong" but **garbage** — `q` (`1/depth`) of `inf`, `6164539`, and
   `97222777161852910548681223518707253248` (a raw integer bit pattern read as a float, not a
   real number that ever came from any depth calculation). Garbage, not merely incorrect data,
   is the signature of reading the wrong *memory*, not the wrong *vertex*.
6. That pointed at the arena buffer `gl_picture.c` records draw commands into and replays
   them from. Checked whether replay runs on a separate thread (it would explain a memory
   race) — confirmed no (`grep`, no thread creation calls; `GlPicture_Replay` is called
   in-line from `sdl.c`'s present path). So not a cross-thread race. Re-read `record_precise`
   and the `OP_PRECISE` replay case side by side and found the actual bug (see 7b's commit):
   both hardcoded "4 words per `PgxpVertex`", stale since `draw_id` grew the struct to 5.

**Lesson for next time:** when a diagnostic at the *collection/lookup* point finds nothing
despite a live, visible bug, don't add more guesses at the same layer — move the check to
where the data is actually *consumed*. And prefer an exhaustive/unconditional log filtered
by a script over an inline "does this look wrong" condition; two hand-picked wrongness
conditions (position, depth) both missed this, while a plain "log everything here, then grep
for the real threshold afterward" approach found the true negative result that redirected
the search, and a differently-placed unconditional log then caught the bug on the first try.

**Fixed** (commit `14e34a1fd`, this branch — superseded by the from-scratch rewrite, see the
top of this item): `PGXP_VERTEX_WORDS` macro (`sizeof(PgxpVertex) / sizeof(uint32_t)`)
replaces both hardcoded `4`s.

**Checked:** builds clean. Live, over a 227k-line trace log spanning a long play session in
the user's own duel: zero "replay mismatch" fires (the diagnostic below), artifact confirmed
gone by the user.

**Decided, 2026-09-27: the attempt-5 diagnostic does not ship.** `MEMORIES_TRACE=frames`
already logs a lot in ordinary play (routine per-120-frame stats: `draws:`, `pgxp: N precise
vertex words...`, `OpenGL picture:` — all pre-existing, not from this bug hunt), and the user
doesn't want a permanent extra source added on top as part of this fix. Kept here instead, to
paste back in by hand if this class of bug ever needs hunting again (it found the actual bug
on the first try; attempts 1-2, the collection-time checks, did not):

```c
/* In gl_picture.c's polygon(), right after find_precise(&v[i], words + at); */
if (v[i].precise && (fabsf(v[i].fx - (float)v[i].x) > 8.0f || fabsf(v[i].fy - (float)v[i].y) > 8.0f)) {
    LOG(LOG_FRAMES, "pgxp: replay mismatch: base (%d,%d) got precise (%.2f,%.2f) q %.4f at %p batch %p",
        v[i].x, v[i].y, v[i].fx, v[i].fy, v[i].q, (void *)(words + at), (void *)batch_words);
}
/* needs #include <math.h> added alongside the other includes */
```

### 7c. Low-res, blurry model textures (the HD pack) — blocked, no path yet

**Cause (traced, not fixed):** the HD texture pack mechanism (`texture_pack.c`) replaces
disc pixels by *provenance*: every VRAM upload is tagged with the disc byte offset it came
from (`texture_dump.c`), and a pack image is matched to that tag plus the palette. Tested
directly: ran the `duel-3d-monsters` smoke case with `MEMORIES_DUMP_TEXTURES` on — **zero**
of the model's own textures were tagged (623 tagged from `WA_MRG.MRG`, 32 from `SU.MRG`, 0
from `MODEL.MRG`, out of the archive's 351 MB). `notes/image-remaster.md` lists `MODEL.MRG`
under "Not done" for the same reason. So an HD pack **cannot** replace model textures today,
even with redrawn art in hand — this is a separate, independent axis from PGXP (7a/7b): PGXP
never touches pixel content, only how existing textures get mapped and where vertices land.

**Leads for why the tags are lost** (not yet followed): `model_texture_transfer.c` copies
textures through work buffers (`D_801DD000` etc.) rather than a straight disc-read-to-VRAM
copy, which may be where the tag drops; `model_apply_texture_tint.c` recomputes palette
entries for a model's tint/lighting, and the pack also requires the *palette* to match the
one the image was captured through, which a computed tint palette never will.

**Once textures are taggable**, the existing pipeline (`tools/pc/extract_images.py`,
`upscale_pack.py`) applies unchanged: extract, redraw or upscale, pack. A sensible next step
after 7a/7b: pick a handful of common monsters as a pilot before committing to all ~700+.
Worth doing 7b (perspective-correct mapping) first or alongside — upscaled detail makes
affine texture warp *more* visible, not less, so shipping HD model textures without it would
look worse in places than the low-res original.

**Manual test routes the user gave me, for later sessions (not yet used):**
- After escaping Simon's duel to the shop: save, Circle back to the title, Library, click a
  card, press Right — a quick way back into a state with cards and a model to inspect.
- L1/R1 during the battle animation rotates the camera around the model (see 7b above).

### 7d. Duel field tile: a thin bright diagonal sliver, intermittent — new, not started

**Seen, 2026-09-27** (three screenshots from the user, same duel, same camera area, a few
seconds apart): a tile just past the field-card slot is clean in two of the three shots, but
in the third a thin bright yellow-white diagonal sliver cuts across its corner — a small chunk
of the tile's normal shading replaced by this streak. Comes and goes with small camera moves.

**Confirmed NOT PGXP**: the user toggled Precise geometry Textures/Off at the same spot —
"did not change much". This is on `fix/pgxp-snap-seams-identity` before any of this session's
`draw_id`/arena changes exist in the tree (only commit 1, the menu option, was applied), so it
can't be the arena-corruption class of bug either. Likely a pre-existing seam/z-fighting
artifact between the tile and the card-slot decal, or something in the base (non-PGXP)
rendering — not yet traced.

**Left to do:** get a few more repro screenshots (ideally with Precise geometry Off, to rule
out PGXP definitively rather than "did not change much"), and find what two overlapping pieces
of geometry are fighting at that seam.

---

## PGXP: Unchiga says distortion on "either setting" — not documented anywhere, needs real cross-OS data

> **GREEN LIGHT FOR LEVEL 2 (2026-09-28).** Commit 1 (level 1, Textures) is
> confirmed clean by the user on both Windows and native Linux (duel field,
> battle animation, Library model view). Commit 2 (`Pgxp_DrawId` +
> `PGXP_VERTEX_WORDS`, level 2, design in 7b) can now go on
> `feat/precise-geometry`. Still open, not blocking: Unchiga's video shows the
> distortion on the **edge of the duel field**, not on the models (Nvidia RTX
> 4090, driver 610.57.04, XWayland on KDE Wayland) — possibly related to 7d;
> asked Unchiga to retry from a Plasma (X11) session.

**PR plan (decided 2026-09-28).** `feat/precise-geometry` is the working branch and
also carries `progress.md` and `memcards/` — those must **not** go upstream. At PR
time, make a clean branch off `upstream/master` (remote `upstream` =
`Unchiga/Yu-Gi-Oh-Forbidden-Memories-Recompiled`) and cherry-pick only the code
commits (`01e0d82e5` level 1, plus the level 2 commit). Keep code and notes in
separate commits so this stays possible.

Naming — follow Unchiga's style: `Area: what the player sees`, plain words, no
jargon (e.g. #157 "3D Monsters: don't overflow the frame packet buffer (Raigeki
crash)", #147 "3D Monsters: Kaminari Attack 40% smaller"). Avoid names already
used upstream: `pgxp`, `pgxp-textures`, `pgxp-native`,
`fix/disable-precise-geometry`, and #139's `feat/pgxp-video-option`.
- Branch: `feat/precise-geometry-menu`
- Title: **not decided.** The draft "textures no longer bend, models no longer
  wobble" states the theory, not anything observed; don't claim an effect the
  measurements (item 0) haven't shown. Write the title from the numbers.
- Description: open by referencing #83 (the rollback: level 2 opened gaps in
  small monsters) and #139, say how that is fixed and what was tested on, and
  raise Unchiga's field-edge video as the open question.

PGXP history upstream: #49 `pgxp`, #67 `pgxp-textures`, #71 `pgxp-native`
(MaChInEgUn3, all merged), #83 `fix/disable-precise-geometry` (Unchiga, rollback),
#139 `feat/pgxp-video-option` (ours, closed unmerged).

**2026-09-28.** Closed PR #139 (level 1 only, no explanation) turned into this message from Unchiga:
*"it was disabled internally since it doesn't display properly with either setting. There is
visible distortion when you enable it."* Checked every prior PR in detail (#67, #71, #83) and
one issue search — **none of them document level 1 (Textures) ever showing distortion**; every
written record is specifically about level 2's seam gaps on small models (the bug already
fixed this session). #71 explicitly notes testing on Windows found no issues at either level,
and no OS-specific concern was ever written down anywhere. So either Unchiga is recalling this
imprecisely, or has private/undocumented information we don't have. Can't resolve this without
either (a) more detail from them (screenshot, OS/GPU, scene) or (b) reproducing it ourselves
cross-platform.

**Plan:** test commit 1 (Textures only) in isolation, thoroughly, on this Windows machine, then
the user reboots into a real (non-WSL) Linux install and repeats the exact same test. WSL was
considered and rejected as a stand-in for (b): WSLg routes OpenGL through a Windows-driver
translation layer (not a native Linux Mesa/Nvidia driver), so a clean WSL result wouldn't rule
out a native-Linux-driver-specific issue, though a *distorted* WSL result would still be a real
finding.

**Status.** Old branches deleted (`feat/pgxp-reenable-textures`, `fix/pgxp-seam-identity`,
`feat/pgxp-video-option`, `fix/pgxp-snap-seams-identity`, local + `origin`), fork fast-forwarded
to `upstream/master` (was 136 commits behind), fresh branch `feat/precise-geometry` created off
it. Commit 1 only (Video menu option, Off/Textures, `pgxp` clamp raised to 1) is now on that
branch and builds clean (`tmp/pc/game32dbg`) — ready to test with `play.bat` on this Windows
machine. Commit 2 (`Pgxp_DrawId`/`PGXP_VERTEX_WORDS`, level 2) is not on the branch yet; it goes
on only after commit 1 is thoroughly tested on both Windows and Linux.

**Windows test environment (this machine), for the record:**

| Component | Version |
|---|---|
| OS | Windows 11 Pro 24H2, build 10.0.26100 |
| CPU | 13th Gen Intel Core i5-1345U |
| GPU | Intel Iris Xe Graphics (integrated) |
| GPU driver | Intel, OpenGL 4.6.0 — Build 32.0.101.7088 |
| SDL | 3.4.16 |
| Compiler | clang 23.1.2, `i686-w64-mingw32` target (llvm-mingw 20260922 release, ucrt runtime) |
| Build target | 32-bit Windows binary (`i686`) |

**Linux test environment (native install, recorded 2026-09-28):**

| Component | Version |
|---|---|
| Distro | Kali GNU/Linux Rolling |
| Kernel | 6.12.25-amd64 |
| Session | X11, XFCE (no Wayland, so no XWayland in the path) |
| GPU | Intel Iris Xe Graphics (Raptor Lake-P, integrated) — same GPU family as the Windows machine |
| GPU driver (Mesa/proprietary) | Mesa 26.1.6 (`libgl1-mesa-dri`, amd64 + i386) |
| SDL | 3.4.16 (built by `build_game32.py` into `tmp/pc/sdl-m32-portable`) |
| Compiler | clang 19.1.7 / gcc 14.2.0 (host); the game links against Debian 11's i386 sysroot |

Same GPU on both machines, so this comparison isolates the OS and driver stack
(Intel's Windows driver vs Mesa), not the hardware. A clean result on both does
not rule out distortion on AMD/Nvidia.

**Linux result, 2026-09-28:** commit 1 rebuilt on this machine, Precise geometry
set to Textures in a live session: **no distortion seen** (user, by eye). Not
yet recorded here: the internal resolution used, which screens were checked
(duel field / battle animation / Library model view), and Off-vs-Textures
screenshots. **Windows: also checked by the user, no distortion.** Library
model view checked on Linux too: **level 1 confirmed clean on both machines.**

**Unchiga's setup (where the distortion was seen), 2026-09-28:**

| Component | Unchiga | Ours (Linux) | Ours (Windows) |
|---|---|---|---|
| GPU | Nvidia RTX 4090 (discrete) | Intel Iris Xe (integrated) | Intel Iris Xe (integrated) |
| Driver | Nvidia proprietary 610.57.04, OpenGL 4.6.0 | Mesa 26.1.6 | Intel 32.0.101.7088, OpenGL 4.6.0 |
| Game's log line (`MEMORIES_TRACE=window`) | — | `OpenGL renderer Mesa Intel(R) Iris(R) Xe Graphics (RPL-U), version 4.6 (Compatibility Profile) Mesa 26.1.6-1, video x11` | — |
| Display | KDE Plasma on Wayland, game through XWayland | XFCE on native X11 | Windows (no X11) |
| SDL video driver | x11 | x11 | windows |

Nothing we tested overlaps with the two variables on Unchiga's side: the Nvidia
driver and XWayland. Both are plausible causes (the per-pixel `uv / w`,
`1 / w` interpolation of flag 32 depends on the driver's float precision
and its handling of the shader; XWayland adds a copy and scaling step).
Next: ask Unchiga for a screenshot (Off vs Textures, same frame) and the internal
resolution, and test on an Nvidia and/or a Wayland session if one is available.

Setup notes: the 32-bit build needs `dpkg --add-architecture i386` and
`libgl1:i386 libgl1-mesa-dri:i386 libpulse0:i386` (otherwise `libGL.so.1: cannot
open shared object file`). The memory card goes to
`~/.local/share/YFM Re-Decomp/saves/slot01.sav`.

## Parked

- **Game > Restart** (dropped for now): `Platform_RestartGame()` already relaunches the
  game (used by the Mods window); a menu item would need to wait for a safe point like
  `TitleJump_Poll` (not while the memory card is written or the save menu is open).
  "Return to title" exists under Debug > Jump to > Title Screen.

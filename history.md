# History

Finished and superseded work, moved out of `progress.md` on 2026-09-29 so that file
stays about what is current. Each section is kept word for word as it stood; branch
names and "next steps" inside are as of when it was written (many branches named
here were later deleted or rewritten). `progress.md` keeps a short summary of each
with a pointer here. Roughly in the order the work happened.

## Precise geometry (PGXP)

### Measurement framework: why, and the claims to test (2026-09-28)

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


### Measurement framework: thresholds and planned measurements (2026-09-28)


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


### Measurement framework: evaluation of the first draft (2026-09-28)


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


### Measurement framework: the planned pipeline (2026-09-28)


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


### Scene `field`: built, tested, committed (2026-09-28, `feat/test-scenes`)

The mod (`mods/test-scenes/`: `mod.json`, `field.json`, `test_scenes.c`).
Live-tested by the user (Q = L1, X = Cross on keyboard) and scripted.

**3D Monsters cache — fixed upstream, our commit dropped (2026-09-28).** The
scene exposed that 3D Monsters kept 8 models for 10 zones: with 9-10 face-up
monsters it reloaded models every frame (`LoadModelDO(n)` without end; 110
lines = 10 models × 11 load phases once is normal), and 3 froze at their first
pose (the user saw it; a simulation of the lookup order gives the same 3, and
zones drawing another zone's model). We had a fix (cache 10), but Unchiga fixed
it the same day upstream: `59c8a065b` "3D Monsters: keep twelve models loaded,
not eight" (same diagnosis, 12 for headroom, 19.9 → 119.5 frames/s). Branches
rebased onto that `upstream/master`, our commit dropped. **Fetch upstream
before preparing a PR**: this one was already done.

**How to capture it: `tools/pc/scene_measure.py`** (committed, Windows and
Linux, Python only, no PIL):

```
python tools/pc/scene_measure.py state      # boot → scene → save state (redo after a rebuild)
python tools/pc/scene_measure.py controls   # must print "controls: pass"
python tools/pc/scene_measure.py compare [--scales 2,4]
python tools/pc/scene_measure.py capture --pgxp 1 --scale 2 out.ppm
python tools/pc/scene_measure.py diff a.ppm b.ppm --mask mask.png
```

Defaults: `--game tmp/pc/game32dbg`, `--out tmp/pc/measure` (captures, PNGs,
logs, the state, and a clean user folder `user/`: default settings, no saves,
no texture packs, update check off). What it does underneath:
1. **State:** the options input with `1100:4400` (Cross + L1, SIO layout),
   both mods on, internal 2x, `MEMORIES_SAVE_STATE=1700:<state>`; checks the
   log for "field filled" (frame ~1556).
2. **Capture:** `MEMORIES_LOAD_STATE`, `MEMORIES_DUMP_FRAME=300`, windowed and
   `MEMORIES_DETERMINISTIC=1`, `MEMORIES_PGXP` / `MEMORIES_INTERNAL_SCALE`
   pinned; rejects a dump whose size is not 320×240 × scale.

**Gotchas found (cost real time):**
- **Internal resolution is `MEMORIES_INTERNAL_SCALE`**, not `MEMORIES_SCALE`
  (that one is the *window* size). `game32dbg-user` is set to internal 4x, so
  a run that doesn't pin it measures at 4x. Check the dump's size (320×240 ×
  scale).
- **A replay from boot is not pixel-deterministic**, even deterministic and
  windowed: two runs differed by one VBlank by frame 38 (41 vs 42), before
  any input, intermittently. The field floor's shimmer and the monsters'
  animations run on VBlanks, so 12.5% of the frame differed. Not chased (the
  spin guard in `platform_common.c` did not fire in a traced run); **the
  state reload removes it** — always capture from a state.
- **Windows PowerShell 5.1 read-modify-write mangles UTF-8** (`Get-Content`
  reads it as Windows-1252, `Set-Content -Encoding utf8` adds a BOM): it broke
  every em dash in this file once. Edit files with the Edit tool, or .NET
  `ReadAllText`/`WriteAllText` with a no-BOM UTF-8 encoding.

**Controls (all pass, 2026-09-28):**

| Control | Result |
|---|---|
| Same setting, state reloaded twice (4x) | 0 changed pixels |
| 1x, Off vs Textures (PGXP disabled below 2x) | 0 changed pixels |
| 4x Off, rerun vs earlier run | 0 changed pixels |

**First measurement (M3, raw, not yet against the thresholds):** frame 300 after
the state, Off vs Textures, with `scene_measure.py compare` (clean user
folder): **2x 15.30%** of pixels changed (640×480, max delta 255), **4x
15.31%** (1280×960); `controls` pass. (With `game32dbg-user`'s settings and
HD texture pack it was 18.9% / 19.8%: the numbers depend on the user
folder, which is why the tool uses a clean one.) The mask: almost the whole
field floor and most monster bodies; cards, hand, HUD and text unchanged. Changed pixels
is not the pre-set metric (texture displacement ≥ 1 screen px, M1); many may
be a colour step. Next is M1 from `polygon()`.


### M1 / M2 / M4 trace: built, first results (2026-09-28)

`MEMORIES_PGXP_MEASURE=<prefix>` (fork-only code, commit "Measure precise
geometry per triangle and vertex"): `gl_picture.c` writes
`<prefix>.triangles.csv` (each textured triangle of the replayed frame),
`libgpu.c` writes `<prefix>.vertices.csv` (each precise vertex's offset from
its console pixel, before level 1 discards it). `scene_measure.py trace
[--scales 2,4]` captures at Textures and summarizes. **Must never go into a
PGXP PR** (cherry-pick only the PGXP commits).

Method, M1: at 15 barycentric points per perspective triangle, the texel the
perspective mapping puts at P is put by the affine one at
P + S T⁻¹ (persp(P) − affine(P)) (S screen edges, T texel edges); the
largest such distance, in picture pixels. Areas are summed over triangles
(which overlap, and include hidden ones): **a share of the frame is an upper
bound.** Coordinates are VRAM's: the second draw buffer sits one picture
width right (taken modulo the picture size).

**Scene `field`, frame 300 after the state, Textures:**

| | 2x (640×480) | 4x (1280×960) |
|---|---|---|
| Textured triangles | 2905: 2883 perspective, 16 mixed, 6 affine | same |
| M1 texel shift: max / median / 95th | 4.62 / 0.01 / 0.40 px | 9.24 / 0.02 / 0.80 px |
| M1 ≥ 2 px (clearly visible) | 42 triangles, ≤ 17.2% of frame | 107 triangles, ≤ 29.6% |
| M1 1–2 px (visibly changed) | 65 triangles, ≤ 12.4% | 24 triangles, ≤ 1.3% |
| M2 mixed triangles | 16, ≤ 2.65%, none at the picture's edge | same |
| M4 bias (mean offset) | +1.52, +1.57 px | +3.04, +3.14 px |
| M4 around the bias: median / 95th | 0.85 / 1.52 px; 37% ≥ 1 px | 1.70 / 3.04 px; 81% ≥ 1 px |

**Reading, against the thresholds fixed before measuring:**
- **Level 1 is visible in this scene, on the field floor.** The biggest
  shifts are few, large triangles near the camera (areas 8000-9400 px at 4x,
  shift 5.8-9.2 px, centres mid-low picture): the floor is *not*
  subdivided (item 13 of the draft review), so affine warp there is large.
  "Clearly visible ≥ 1% of the frame" holds by far, even as an upper bound.
  Models: median shift ~0.01 px, invisible; still 33 model-sized triangles
  (< 2000 px) at ≥ 2 px at 4x (max 6 px).
- **M2, Unchiga's suspect, not reproduced here:** the 16 mixed triangles
  (quads with a corner lacking a precise position, drawn affine beside
  perspective neighbours; 5 have 3 precise corners, their quad's 4th has
  none) are mid-picture, and this camera does not frame the field's edge.
  Needs a camera that does (hand-camera L1/R1/L3/R3 input from the state).
- **M4 has a bias, which matters for level 2:** the console pixel is
  *floored* from an approximate division (`gte.c` rtp: UNR table, IR
  truncation, `x >> 16`), the precise value is exact, so offsets average
  +0.76 / +0.78 console px. Level 2 draws at the precise positions, so it
  would move every model ~0.77 console px right and down relative to what
  the console draws and to the 2D elements (cards, HUD) that stay on whole
  pixels. **Check at level 2 (M5 stage) whether that misaligns anything,
  or whether level 2 should subtract the floor's half pixel.** The wobble
  amplitude is the spread around the bias: median 0.43 console px, 95th 0.76.


### Camera sweep and why vertices lose precision (2026-09-28)

`scene_measure.py trace --camera turn:<degrees>` (Hand camera L1/R1 from the
state, **at the duel's own distance**: the user's guidance — moving the camera
away sends the field into the duel's black fog past ~900, and moving in loses
the field's edges); `--camera near|near-half` moves in (L3). Each trace also
writes `<prefix>.overlay.png` (red: shift ≥ 2 px, yellow 1-2, blue mixed) and
`<prefix>.rejects.csv` (from `gte.c`: projections that kept a precise
position, and why the others did not).

| View (2x) | Max shift | ≥ 2 px (≤ % frame) | Mixed | Rejected projections |
|---|---|---|---|---|
| default | 4.6 px | 42 (17%) | 16 | 0 |
| turn −22 / −45 / −90 | 6.5 / 8.9 / 7.0 | 53 / 46 / 48 (29 / 29 / 33%) | 18 / 12 / 18 | 0 |
| turn +22 / +45 / +90 | 6.5 / 8.8 / 6.1 | 41 / 45 / 50 (24 / 28 / 34%) | 16 / 20 / 22 | 0 |
| near-half (450) | 13.1 | 88 (51%) | 38 | 25 outside the window (miss ≤ 2.2 console px) |
| near (300) | 15.7 | 88 (76%) | **1021** | 2466 outside the window (miss ≤ 3.5), 120 saturated |

**Reading:**
- **Level 1 is strongest at the field's edges and near the camera.** Turned a
  quarter (edge-on view of the field's side, `trace_turn-90_2x.overlay.png`),
  the floor along the edge and the mat's side face are red. Off vs Textures
  of that view for the eye: `tmp/pc/measure/edge_off_2x.png`,
  `edge_tex_2x.png`, `edge_mask_2x.png` (16.0% of pixels change).
- **At the duel's distance nothing is rejected** at any angle: the 12-22
  mixed triangles there are mostly the **monster-zone mats**, which get no
  precise corners from rtp's window test — they come from the by-value lookup
  (`Pgxp_Find`: a word two vertices of the frame round to is left alone) or a
  path that is not tagged. Not yet traced which.
- **Closer in, the window test rejects vertices** (`gte.c` rtp keeps a precise
  value only within (−1, +2) of the console's floored pixel; the GTE's
  approximate division drifts up to 3.5 console px close up), and whole
  monsters become mixed: drawn affine next to perspective neighbours, their
  textures break at shared edges. **This is the best candidate so far for
  Unchiga's distortion**, if his camera was close (or his scene has close
  geometry: the battle animation's close-ups). Next: capture Off vs Textures
  at `near` and look at the monsters' seams, and try widening the window.


### Captures were not deterministic; fixed; near camera (2026-09-28)

**Everything above was captured at real-time speed.** `MEMORIES_DETERMINISTIC`
only makes time virtual when the game speed is uncapped (`rate == -1`,
`platform_common.c` `advance`/`Platform_WaitVBlank`); `scene_measure.py` never
set `MEMORIES_SPEED=-1` (the smoke tools all do), so the log said `clocks: rate
100` and "4 VBlanks missed". Off happened to replay the same (fast frames), but
Textures did not: two identical runs differed by **10.4%** (default camera) and
**16.7%** (near), from one VBlank more or less while the 10 models load after
the state (`vb 2612` vs `2613`), so the monsters' animations were at another
frame. Fixed in `scene_measure.py` (`MEMORIES_SPEED=-1`); state redone.
Now 0 changed pixels between repeats for Off and Textures, default and near.

**Numbers that change:** the M3 compare at 2x, Off vs Textures, is **7.44%**,
not 15.30% (about half of that was animation drift). The M1/M2/M4 tables and
the camera sweep are single-frame statistics of a real frame, so their reading
holds, but they were not reproducible; redo them before quoting exact values.

**Near camera (300), Off vs Textures, 2x:** **11.9%** of pixels change, steady
over frames 120-480 (11.4-12.1%). Near trace, now reproducible: 3199 textured
triangles, **927 mixed** (1021 before), 2437 projections outside the window
(farthest miss 3.58 console px), 133 saturated; M1 max 15.7 px.
- **The monsters' seams look the same in Off and Textures** at 3x crops
  (`crop_mid_*.png`, `crop_dragon_*.png` in `tmp/pc/measure`): no break at
  shared edges, even though the overlay marks nearly every monster mixed. The
  visible change is still the field floor. So mixed triangles at this distance
  do **not** reproduce Unchiga's distortion by eye; a mixed triangle is drawn
  affine, which is exactly what Off draws, and its neighbours' shift is small
  on model-sized triangles.
- **Spikes from the monsters (a long dark shard across the top left) are the
  game's own geometry**, not PGXP: at frame 480 Off and Textures both draw it
  (a dragon's wing near the camera). They looked like a Textures-only artefact
  only because the non-deterministic Textures runs sat at another animation
  frame. The overlay's huge blue triangles at frame 300 are not in the picture
  (the overlay draws every triangle); probably near-plane polygons the GPU
  drops as too large. Not verified.

**Sweep redone uncapped** (2x): within a few tenths of the table above
(default 4.62 px max, 42 triangles ≥ 2 px, 24 mixed; turn ±22/45/90 max
6.1-8.9 px, 12-24 mixed; near-half 24 mixed, 14 rejected; near 927 mixed,
2437 rejected). The reading stands.


### rtp's window widened by the truncation it allows (2026-09-28)

Why vertices miss the (−1, +2) window up close: the GTE truncates IR1/IR2
(each lost unit moves the word by up to H / SZ3 px; always < 2, since the
division needs H < 2·SZ3) and SZ3 (moves it by up to its distance from the
centre / SZ3). `gte.c` rtp now widens the window by `(H + that distance) / SZ3`
on each side: the same window at the duel's distance, a few pixels up close.
A saturated IR or a clamped word still misses by far more and is rejected.
Test in `tests/pc/pgxp_test.c` (a vertex at view x −150.5, z 160.5: word −284,
truly −281.3; kept; a saturated IR1 rejected). It fails on the old window and
passes on the new one; built on its own with llvm-mingw (the full CMake
configure still lacks zlib/libpng here), CI runs it.

| View (2x) | Mixed before → after | Outside the window before → after | Max shift |
|---|---|---|---|
| default | 24 → 24 | 0 → 0 | 4.62 (same) |
| turn −90 | 18 → 18 | 0 → 0 | 6.11 (same) |
| near-half | 24 → **10** | 14 → **0** | 13.1 |
| near | 927 → **4** | 2437 → **0** | 15.7 → 24.6 |

At near, 133 projections still saturate the division (behind the near
plane in effect: nothing to keep). Off vs Textures at near: 16.7% (was
11.9%): the zone mat and floor quads nearest the camera, mixed before (so
drawn like Off), are now in perspective; their panels sit a little higher and
wider toward the near edge (`c_floor_{off,old,new}.png`), which is what a flat
quad seen close should do. Default view unchanged (7.44%). **Commit this on
its own: it belongs in the PGXP PR** (clean cherry-pick onto the PR branch;
the measure lines around it in `gte.c` stay behind).


### The last mixed triangles: 3D duel cards through GsSortPoly (2026-09-28)

The 24 mixed triangles at the duel's distance were **not the zone mats but
the 3D duel cards** (`func_80015EF4`: the card quad and its ground sprite).
`<prefix>.misses.csv` (new, measure-only: each vertex-like word that got no
precise values, and why) showed the missing corner of each of the 12 quads
was a word the by-value lookup refused as **ambiguous**: another vertex of
the frame, at another depth (663 vs 488), rounds to the same pixel. Why by
value at all: the card's corners are stored correctly (`RotColorDpq` and
`gte_stsxy` go through `Memories_GteStore`), but it is submitted with LIBGS
`GsSortPoly` (`src/pc/sdk/libgs.c`), which copies the primitive into the
packet area moved by the LIBGS offset and never called `Pgxp_AddPrim`.
Fix: `Pgxp_AddPrimMoved(packet, dx, dy)` (Pgxp_AddPrim is the (0, 0) case),
called by `GsSortPoly`; test in `pgxp_test.c`.

| View (2x) | Mixed before → after |
|---|---|
| default | 24 → **0** |
| turn −90 | 18 → **0** |
| near | 4 → **0** |

Off vs Textures at default: 8.06% (was 7.44%: the cards are now in
perspective too). Crops (`c_cards_{off,tex}.png`) look right. The 6 affine
triangles left have no precise corner at all (not traced; likely 2D). **PR
candidate**, commit of its own. Lesson: the by-value lookup fails on a busy
frame (238k ambiguous events over one run); every path that writes vertex
words should tag by address.


### The full-field slowdown (2026-09-28)

**Slowdown with a full field, found by the user live (2026-09-28).** With 10
monsters the game slowed down (their log: 60 ms game frames, 1.5 ms present),
fine with 6. Reproduced at 4x, real speed: game time 8 ms Off, **20.5 ms
Textures (30 fps)**. Cause: PGXP's two lookup tables (32768 slots) held ~32000
live entries (two frames × ~16000), and a miss or a new entry walked all 32
probes (expired entries can't end a chain). Fix (`a1e143b0a`): per-frame
tables, this frame's and the last's, 65536 slots each, a slot empty unless
stamped with its table's frame (probes stop there, no clearing); `DrawOTag`
skips words outside ±2048 (not a vertex) before any lookup. Now **9.4 ms vs
7.1 ms Off, 59 fps**; picture unchanged (0 mixed, 8.06%). Ported to the PR
branch by hand (without `Pgxp_Ambiguous`).

### Benchmark, behaviour check, profile and A/B, as first written (2026-09-29)

**Benchmark turn (2026-09-29): `scene_measure.py bench`.** From the field
state: Blue-Eyes from the hand, face up, to the second zone, Sun, Start as
soon as the field phase takes input, the opponent's whole turn, end at 2520
as the player's turn returns (sequence checked with the user live).
Uncapped, 4x, internal; laptop on mains, windows closed, output **outside
OneDrive** (it syncs the 7.5 MB states otherwise, and on battery the numbers
were twice as noisy: never measure that way). 5 alternating repeats each,
medians:

| Build | Setting | Game ms/frame | Draw ms/frame | Wall s (2520 frames) |
|---|---|---|---|---|
| before the fix | Off | 2.59 | 1.04 | 9.4 |
| before the fix | Textures | **5.40** (+2.81, +108%) | 1.29 | 17.2 |
| with the fix | Off | 2.76 | 1.09 | 10.0 |
| with the fix | Textures | **3.38** (+0.62, +22%) | 1.28 | 12.1 |

The fix removes ~78% of the overhead. What is left, +0.6 ms game and +0.2 ms
draw per frame, is the per-vertex precise projection and bookkeeping.

**Behaviour: precise geometry changes nothing in the game.** The state saved
at the end of each uncapped run: across all 10 runs of a build (both
settings), **0 bytes differ outside two sound regions**: the sound driver's
RAM (around `0x801E1650`, `SD_InitState`, `sound_transfer_lifecycle.h`) and
the SPU's voices, which also differ between two runs of the *same* setting
(the mixer runs on a real-time thread; `MEMORIES_NO_AUDIO` does not stop the
emulation). Same for the build before the fix.

**Where the +0.8 ms goes (profile, 2026-09-29).** `MEMORIES_PROFILE` (the
sampling profiler; it takes the interrupt clock) over the benchmark turn, 3
runs each, Textures minus Off, ~1690 extra samples a run (waiting excluded),
shares scaled to the measured +0.8 ms (game + draw). `polygon` is
`gl_picture.c`'s (by address, next to `bind_attributes`); `triangle#2` etc.
are `soft_gpu.c`'s.

| Part | Where | Share | ≈ ms/frame |
|---|---|---|---|
| Precise position per projection (doubles, a divide, the window) | `rtp` (gte.c) | 18% | 0.14 |
| Every projection into the by-value table | `Pgxp_Project` | 16% | 0.13 |
| Precise values onto packet words, by address | `Pgxp_StoreAt`, `AddPrim` | 25% | 0.20 |
| The frame's vertex words looked up | `Pgxp_FindAt`, `DrawOTag` | 9% | 0.07 |
| OpenGL: binary search per vertex, perspective setup | `polygon` (gl_picture.c) | 19% | 0.15 |
| Indirect (cache pressure from the tables, likely) | `multiply`, soft `triangle`, … | 13% | 0.11 |

**A/B: the two mixed-triangle fixes cost ~0.05 ms.** Same session, 5
alternating runs, medians: without them Off 2.62 / Textures 3.24 ms game;
with them 2.68 / 3.35 (Off runs identical code, so 0.06 of that is drift).
The overhead is precise geometry itself, not the fixes.

**Optimisations, weighed against level 2 and HD models (decided with the
user):** by-value lookups serve ~10 of ~8737 vertex words a frame, and are
what glues unrelated vertices (#83) and dropped the card corners: **drop the
by-value table** (0.13 ms) as part of level 2, after giving those ~10 words an
address path. **Direct index for the OpenGL lookup** (most of 0.15 ms): level
2 needs it too. **Not `rtp`'s math in floats:** level 2 draws those positions,
and float rounding is the wobble it removes. HD meshes drawn natively would
not go through PGXP at all; pushed through the GTE path, per-vertex cost
would scale with them. HD textures make level 1 matter more (warping shows).

### The PR branch as first built (2026-09-28)

**PR branch built, 2026-09-28 (local only, not pushed, PR not opened):**
`feat/precise-geometry-menu` off `upstream/master` (`6ad201fbf`), three
commits cherry-picked, no measure code: the Video option (level 1), rtp's
window, GsSortPoly. Builds clean, `pgxp_test` passes, all six smoke
screenshots unchanged (CTests not run here). Draft description leads with
#139's distortion and the measured table (mixed triangles 24/18/927 → 0),
asks Unchiga to retry at Textures. Waiting on the user's visual check, then
push + open.

### Level 1 cleared on both machines; the first PR plan (2026-09-28)

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


### Test environments and the by-eye cross-OS result (2026-09-28)

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

### Why Unchiga's setup could differ (2026-09-28)

Nothing we tested overlaps with the two variables on Unchiga's side: the Nvidia
driver and XWayland. Both are plausible causes (the per-pixel `uv / w`,
`1 / w` interpolation of flag 32 depends on the driver's float precision
and its handling of the shader; XWayland adds a copy and scaling step).
Next: ask Unchiga for a screenshot (Off vs Textures, same frame) and the internal
resolution, and test on an Nvidia and/or a Wayland session if one is available.

### PR #139 closed, and the cross-OS plan (2026-09-28)

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


### The branch rewrite of 2026-09-27

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

### PR plan as it stood on 2026-09-27 (branches since deleted)


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


### 7a. Warped textures: the first Video option attempt (2026-09-27)


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


### 7b. Level 2: the draw_id design and first implementation (2026-09-27)


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


### Switching machines, 2026-09-28


**2026-09-28.** Moving from this Windows machine to a native Linux install to
continue [PGXP cross-OS testing](#pgxp-unchiga-says-distortion-on-either-setting--not-documented-anywhere-needs-real-cross-os-data).
Everything needed to resume is committed and pushed to `origin` (the fork),
except the disc image (`game/*.bin`, gitignored, copyrighted, re-supply it
locally): this file, `notes/*.md`, and a copy of the real memory card
(`memcards/slot01.sav`, `memcards/README.md` — not a save state; see that
README for why). Current branch: `feat/precise-geometry`, commit 1 only
(Video menu option, Textures) — see the PGXP section below for what's next.


## Other items

### 1. Name entry: END and the arrows are not HD (merged upstream as #110)


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


### 5. Build Deck: browse cards from the card view (Build Deck merged upstream as #111)


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

## 2D Monsters mod

### Live debugging session, three bugs found and fixed (2026-09-29)

**What it is:** `mods/2d-monsters/` (`field_art.c`, `mod.json`) — an alternative to
the 3D Monsters mod: instead of a loaded battle model standing on a face-up field
card, an enlarged, camera-facing cutout of the card's own art (`WA_MRG.MRG`'s
102x96 record) floats over it. Disabled by default, `"conflicts": ["3d-monsters"]`
(same software-GPU texture-bank range, `SOFT_GPU_BANKS`). Not built on this
branch — cherry-picked here (code + `tests/pc/smoke/duel-2d-monsters.json`) from
`claude/2d-art-replace-3d-models-bbpme7`, which also has a clean copy pushed off
`origin/master` as `feat/2d-monsters-mod`, for whenever this is ready to PR
upstream. This branch's own `progress.md`/`history.md` were left alone by that
cherry-pick (same paths, unrelated content); this section is the bridge.

**How it's built, briefly** (reuses 3D Monsters' own patterns: the LRU
texture-bank cache, `duel_field_up()`'s gating, borrowing `D_800E9D90[0]`); no
model load, no arena, since there's no model: the card's art is read straight
from disc into a private bank, and both screen placement and the
ordering-table depth come from one `RotTransPers` call per corner-pair, the
same projection `func_80015EF4` uses for a field card's own ground sprite —
so it needs only the GTE/projection state the field's own draw pass already
sets up, nothing extra.

**Live-tested, 2026-09-29** (user's Windows build, real disc, a real duel reaching the
card-flip reveal / face-up field): compiles and loads clean, no crash, the card art
texture reads correctly (`WA_MRG.MRG` sectors load, log confirms). **But the cutouts
were wrong:** way too big on both sides, and the opponent's-side cutouts were getting
truncated (clipped at the screen edge) while the player's-side ones stayed fully
visible — screenshots: `2026-09-29-105213-2062.bmp` (hand-select filmstrip, not the
mod — a red herring), `2026-09-29-105353-8057.bmp` (the actual bug, behind the
card-flip animation: oversized silhouettes, one clipped by the right edge).

**Root cause found and fixed:** `draw_frame()` called `fit_height()` — which
calibrates the world-space cutout height by projecting two points and measuring the
resulting screen-pixel delta — *before* `GsSetRefView2`/`SetGeomScreen`/
`SetGeomOffset` set up the duel field's actual camera and projection scale for the
frame. So the calibration ran under whatever GTE state was left over from the
previous draw call, not the field's own camera; the resulting `world_height` was then
used to draw every cutout under the *correct* (different-scale) camera in
`draw_one()`, producing a systematic size error on every card. The opponent-side
clipping looks like a consequence of that, not a separate bug: those zones sit
higher/farther on screen, so an oversized cutout there is far more likely to run off
the top edge, while the player-side ones just spill into empty space below and stay
on-screen. Fix: moved the three camera/projection calls before the `fit_height()`
call in `draw_frame()` (`mods/2d-monsters/field_art.c`).

**Still wrong after the camera-timing fix, live-tested again 2026-09-29:** cutouts
are still way too big, and the user's description of the shape is the more useful
clue than "too big" alone — the cutout doesn't read as a card floating over its own
zone; it reads as one thing standing straight up out of the *near edge of the
field itself*, perpendicular to it, rather than starting at each card's own
position and floating just above it. That shape (a correctly-anchored bottom edge
with a wildly wrong top edge) is exactly what suspect #2 below predicts: if
`fit_height()`'s `world_height` blows out to `HEIGHT_LARGEST` (8192 — many times
the 70-166 unit spacing between field zones), `draw_one()`'s "top" point
(`wx, -lift()-world_height, wz`) is so far above the card that its projection stops
tracking the card's own screen position the way the correctly-scaled "base" point
(plain `wx, -lift(), wz`) still does — the base stays put (on the card, at the
field's near edge for the front zones), the top goes wherever a wildly-out-of-range
point happens to project, which does not vary sanely card to card. One shared-looking
"wall" rising from the field's base, rather than five distinct floating cutouts,
is what that produces.

**Root cause confirmed live, 2026-09-29** (diagnostic log added, user reproduced
the same scene on the *pre-fix* build, `tmp/pc/last-session.log`):

```
fit_height: target 40 px, got 66 px, height 128 after 6 attempt(s)
```

`attempt` reaching 5 (the loop's own cap, printed as 6) with `height` sitting
exactly on `HEIGHT_SMALLEST` means the loop never converged — it ran out its full
budget pinned to the floor. Working the ratio backwards: 128 world units already
projects to 66 px against a 40 px target, so every iteration computed `wanted`
around 77-78 (correctly smaller), but 77 is below `HEIGHT_SMALLEST` (128), so it
got clamped straight back up to 128 and the loop repeated the same losing move
five times. The cutout was never "blowing out" to `HEIGHT_LARGEST` (suspect #2
below, now ruled out) — it was being held at a floor well *above* the size the
camera's real scale needed, permanently oversized by about the 66/40 ratio (~65%
too big). That single fixed world-space size, applied to every card uniformly
regardless of the small diamond-shaped tile it sits over, reads exactly like the
"a wall rising off the field's edge, not hovering over its own card" shape the
user described — a plain size bug once the numbers are in hand, not a separate
placement one.

`HEIGHT_SMALLEST = 128` came from this file's own header comment analogy to the
3D Monsters mod's `fit()`, but the constant it was actually modeled on,
`SCALE_SMALLEST = 0x100`, is a fixed-point *scale fraction* (of `MODEL_FIXED_ONE`,
4096 = 100%), not a raw world-unit height — the same number, 128, means something
completely different in the two mods, and using it as a height floor here was
simply too high for what this camera's projection scale calls for (the real
answer converges around 60-80).

**Fix:** `HEIGHT_SMALLEST` dropped from 128 to 16 — a guard against a genuinely
degenerate `got` (near-zero or negative), not a plausible lower bound on the real
answer — so the loop can actually reach the smaller height it keeps computing.
Also (from the user's original ask): `DEFAULT_PIXELS` (and `mod.json`'s matching
`pixels` default) dropped from 40 to 32, matching the 3D Monsters mod's own
`TALL_PIXELS` target. The diagnostic `say()` in `fit_height()` is left in,
gated on the same mods log already used to confirm `WA_MRG.MRG` reads — cheap
to check again if the size still looks off.

**Fix confirmed live, 2026-09-29** (rebuilt, same scene, `tmp/pc/last-session.log`):

```
fit_height: target 40 px, got 40 px, height 189 after 3 attempt(s)
```

`got` matches `target` exactly, converged in 3 of 5 attempts, not pinned to
either `HEIGHT_SMALLEST` (16) or `HEIGHT_LARGEST` (8192) — healthy convergence.
User confirms the cutout size now looks right. (`target` reads 40, not the new
`DEFAULT_PIXELS`/`mod.json` default of 32, because the user's `pixels` setting
was already persisted at 40 from before the change — `Settings_GetNamed` returns
a persisted value over a new fallback. Harmless; 32 is only a suggested starting
point to match the 3D Monsters mod's own scale, adjustable live from the mod
menu with no rebuild either way.)

**Second bug found live, 2026-09-29** (two screenshots, camera zoomed out and in,
same scene, size now correct): every cutout in a row is cropped clean across the
bottom, at the exact same screen height, right where each zone's own small
upright field-card token sits — the token is drawing *over* the cutout's lower
half rather than under it. The flat, identical cropping line across all five
zones (not following the board's own perspective slope) was the tell: a
screen-space/ordering artifact, not a geometry or lift problem.

**Root cause:** a depth-scale mismatch, found by comparing against the 3D
Monsters mod (prompted by the user asking why 3D models don't show this same
cropping). `func_80015EF4` sorts a field card's own upright quad at an averaged,
twice-halved depth — a sixteenth of a single corner's raw projected depth, what
this file's header calls "the card's scale." The 3D Monsters mod's
`sort_monster()` explicitly converts to that same scale before reusing this
table: `at = nearest / 4 - tunable("depth", DEPTH_STEPS)` (`field_models.c:677`)
— a model's own raw depth is 4x finer than the card scale, so it has to be
divided down before the two are comparable. `field_art.c`'s `draw_one()` skipped
that conversion: it took `RotTransPers`'s raw depth straight from `project()`
and only subtracted the small `DEPTH_STEPS` bias. That left every cutout's depth
number about 4x too large for its real position — read as much farther away than
the correctly-scaled card token sitting in the very same zone, so the token
(nearer, by the numbers) drew over the cutout's bottom half. Same error at every
zone, hence the identical flat crop line. The file's own header comment had
assumed the raw depth was "already scaled the way this table's other content
is," which is the belief this bug lived in.

**First attempt (the `/4` alone) confirmed NOT enough, live, 2026-09-29:** added a
`say()` per cutout (zone, world position, projected points, size, depth at each
stage). Live log after the `/4` fix, cropping still identical:

```
zone 5:  raw_depth 126, final_depth 3
zone 20: raw_depth 171, final_depth 3
```

Different raw depths landing on the *identical* final value only happens if the
table is clamping at a ceiling — added `table->length` to the log to check:
came back **2**, i.e. a 4-slot table (indices 0-3). Every cutout's post-`/4`
value (28-45 in these samples) blew straight through that ceiling, so all ten
saturated at index 3 regardless of real position — draw order among them (and
against anything else sharing that slot) came down to insertion order, not
depth. That's why cranking the `depth` setting live did nothing: any bias small
enough not to go negative still left every value pinned at the same ceiling.

**Real root cause: the wrong table, not just the wrong scale.**
`D_800E9D90[0]` — what `draw_one()` was targeting — genuinely is that tiny
4-slot table in this state, and was never the right target: checking the 3D
Monsters mod's *field*-standing code (`draw_monster()`, not the battle-card
code compared against the first time, which targets something else again)
shows it sorts into `D_800E9D98[0]` — which `field_models.c`'s own comment
identifies as `D_800E9D90[2]`, an aliased view of the same storage. `D_800E9D90[2]`
is also exactly what `func_80015EF4` sorts a field card's own upright quad into
— a real, properly-sized table shared with the field's own geometry, which is
why 3D models layer correctly against it. This file's header comment asserting
cutouts belonged in table 0 ("the table the battle presentation draws its two
duellists into") was simply wrong from the start — a mix-up between
`D_800E9D98` (a different array) and `D_800E9D90[0]`, apparently never checked
against the 3D mod's actual field-drawing code.

**Fix:** `table = D_800E9D90[2]` (was `[0]`). The `/4` depth-scale conversion
was already correct (it matches `func_80015EF4`'s own conversion for this same
table) — it just fed the right number into the wrong table. Header comments
corrected throughout.

**Confirmed live, 2026-09-29:** rebuilt, same scene — cutouts now sit correctly on
their own card, sized right, not cropped by the card token beneath them. User
confirmed with a capture. Diagnostic `say()`s (per-cutout in `draw_one()`, and
`fit_height`'s own) removed once confirmed; the reasoning above and the comments
left in `field_art.c` are the record.

**Lesson learned:** three unrelated bugs in one mod, each found by the same
pattern — a plausible assumption, copied or reasoned by analogy from the 3D
Monsters mod, that turned out to not match what that mod's code actually does
in the equivalent situation:
- A **draw-order** assumption (calibrate then set up the camera) that just had
  two steps backwards.
- A **constant copied by name/value from another mod** (`HEIGHT_SMALLEST` from
  `SCALE_SMALLEST`) without checking that the two mods use the constant for
  different *kinds* of quantity (a raw world-unit height here, a fixed-point
  scale fraction there) — same number, unrelated meaning.
- A **borrowed resource** (an ordering table) identified by a comment's
  description ("the table the battle presentation draws its two duellists
  into") rather than by reading the reference mod's actual code for the
  *matching* situation (field-standing, not battle) — and the comment's
  description didn't even hold up when checked.

In each case, screenshots alone couldn't distinguish the real cause from
plausible-looking alternatives; what closed each one out was a live numeric
log (a calibration's own working, or a per-object depth and the target table's
actual length) checked against a specific, falsifiable prediction. Reasoning
by analogy to a sibling mod is a good way to find a *candidate* fix fast; it is
not a substitute for reading that mod's code for the same situation, or for a
number from the running game that could have come out differently if the
candidate were wrong.

### HD texture pack support: tried, broke the game, reverted (2026-09-29)

**Confirmed live** (separately from the three-bugs fix above): the size and
depth-sort fixes hold up — cutouts sit correctly on their own card, sized
right. User confirmed with a capture.

**Then asked for HD art support**: an installed texture pack's redrawn card
art should apply to the cutout automatically, the way it already does for the
retail card-detail view, without touching the PC port's shared code (the same
constraint the third-party HD pack itself respects, being a pure data mod).

First idea: reuse each field zone's already-uploaded, already-tagged 40x32
thumbnail (real VRAM, so texture-pack-compatible for free). Checked the actual
pack's thumbnail PNGs against its full-art ones for the same card and dropped
this: a thumbnail is a cropped detail (a dragon's head, not the whole dragon),
not the full card art shrunk down — true of the retail thumbnail itself, pack
or no pack, wrong for "the monster standing on its card."

Root cause of why the private bank never got HD art: a texture pack's
replacement (`soft_gpu.c`'s `shadow_on`) only ever applies to a primitive
sampling *real* VRAM (`texture_source == vram`); a mod's private software-GPU
bank is structurally excluded — the same reason HD model textures (item 7c)
are blocked. So real HD art means uploading for real, like retail's own
big-card view (`func_800289BC`) does, not through a bank.

**Fix attempted:** `field_art.c` uploaded each zone's full 102x96 art + CLUT
with a plain `LoadImage()` every frame (no cache needed, cheap at this size)
into VRAM the 3D Monsters mod's own comments call "the model area of VRAM for
slot 0/1" and treat as safe while `duel_field_up()` (no 3D model is ever shown
then, and that mod is mutually exclusive with this one). Worked out the exact
layout carefully, including a real hardware constraint: a texture page's Y
origin is only ever 0 or 256 in this software GPU, so the art was placed at
y=256 (not the 3D Monsters mod's own y=240, which would straddle that
boundary partway through a 96-row image and be unsampleable); the CLUTs, which
have no such restriction, filled the untouched 16-row sliver at y=240-249.
Shipped it and asked the user to live-test.

**That assumption was wrong.** Live-tested with the HD pack *disabled* (so
this alone, not the HD-pack code path): the opponent's card art came out as
degraded copies of the player's own cards, the fusion animation broke, and the
card-detail view's title (Triangle to examine a card) turned to garbled text —
three unrelated systems, all broken at once. That VRAM is evidently doing real
work during ordinary play, not reserved the way the 3D Monsters mod's own
comments implied; reusing it, even by the same reasoning that mod uses for its
own (much shorter-lived, load-then-evacuate) purpose, corrupted live state.

**Reverted in full** (`git revert` of the real-VRAM commit) — back to the
private-bank version already confirmed correct for sizing and depth-sort.
**Revert confirmed live:** user reports it works normally with the HD pack
both on and off.

**Status:** HD pack support for this mod is unsolved and parked, not required
for the pending PR. The next attempt needs either a VRAM region verified safe
by something stronger than reading another mod's comments, or a different
mechanism entirely — not a fresh guess at a bigger or different address range.
`progress.md`'s "How to test things" now has a headless build-and-capture
recipe (built specifically so the next attempt can be checked without risking
the user's live game again) covering the three systems this one broke: the
field view, the card-detail view, and a fusion animation.

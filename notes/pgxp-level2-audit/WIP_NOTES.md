> **RESUME HERE (2026-10-14):** read `C:\Users\mdahh\OneDrive\Desktop\Perso\hacking\shared\yfm-notes\pgxp-level2.md` first (short, ranked). This file has every number and command, in the order the work happened;
> the LAST sections ("Conservative coverage ...", "Hole anatomy", "Review round") are the current truth, earlier sections (baseline, taint, give-back) are history of what failed and why.
# feat/pgxp-level2 — status and resume notes (updated 2026-10-13, evening)

Goal: precise geometry level 2 ("Textures and positions": polygons drawn at the vertices' precise positions, no
wobble) without the gaps that made upstream disable it (#83). Level 1 (Textures) is merged upstream (#196); level 2
is not offered (settings.c SET_PGXP max 1). Branch = upstream/master e74cef21a + PR #320 (3D Monsters fights).
Shared copy of this doc: `C:\Users\mdahh\.claude\shared\yfm-notes\pgxp-level2.md`. Old plan/notes on the fork:
`git show origin/dev:progress.md` ("P. Precise geometry"), `origin/dev:history.md` (7b). Pictures for the user:
`Desktop\PGXP-level2-evidence\`.

## Setup / how to measure (Windows)
- Disc `game\ygofm-orig-usa.bin` (hardlink); `rom\ygo\*.iso` is a different image. Toolchain: `tmp\pc\tools`, `tmp\pc\win32-deps`
  are junctions to the -dev worktree. Test scenes mod linked: `hacking\shared\link.ps1 -Worktree . -Code test-scenes` (git-excluded).
- Build: `python tools\pc\build.py --target windows`. If the link says "Permission denied" retry after ~15 s (another session's
  runs start memories-pc.exe from this build folder; kill only processes whose Path is in this clone).
- Measure: `python tools\pc\scene_measure.py --game tmp\pc\game32 [--out DIR] [--cards p1..p5,o1..o5] [--seams] [--env K=V]
  state | capture --pgxp N --scale S out.ppm | diff a b | controls`. Small-monster scene: `--out tmp\pc\measure-small
  --cards 58,62,41,59,39,3,2,4,7,97`; big-monster scene: default cards, `--out tmp\pc\measure`. State must be redone after every rebuild.
  Clamp raised to 2 for measurement (settings.c, uncommitted). scene_measure.py is a patched copy of origin/dev's (untracked).
- Gaps: `hacking\shared\tools\gap_score.py level1.png label=level2.png ...` (dark pixels at L2 where L1 is solid bright, bias
  shifted back). Pictures: `hacking\shared\tools\crop_compare.py`.
- C tests DO run on Windows: cmake -S . -B tmp\pc\cmake-test -G Ninja -DCMAKE_C_COMPILER=i686-w64-mingw32-clang -DBUILD_TESTING=ON
  -DZLIB_LIBRARY=<win32-deps>\lib\libzs.a -DZLIB_INCLUDE_DIR=<win32-deps>\include (PATH: llvm-mingw bin, cmake bin, ninja);
  `cmake --build tmp\pc\cmake-test --target memories_pgxp_test memories_gte_test memories_libgpu_test`;
  `ctest --test-dir tmp\pc\cmake-test -R "pc_pgxp|pc_gte|pc_libgpu"` -> pass.

## What is in the working tree (all uncommitted)
1. `Pgxp_BeginDraw()` at GsSortUnit entry -> `PgxpVertex.draw` (one model draw). PgxpVertex also carries `view[3]` (camera space before
   the divide) and `scale` (part matrix size). Lookups (`Pgxp_Find/FindAt`) return a PgxpVertex; `Memories_GtePreciseVertex`;
   gl_picture.c records PGXP_VERTEX_WORDS (derived from sizeof). pgxp_test.c updated + new checks.
2. libgpu.c `weld_corners()` replaces `snap_seams`: vertices of one draw within WELD_TOLERANCE (1.5) model units (camera distance /
   part scale) take the first one's position/depth. Env override MEMORIES_PGXP_WELD (EXPERIMENT, remove before commit).
3. NCLIP (gte.c) keeps the game's rounded decision; where the precise facing disagrees it calls `Pgxp_Taint` for the 3 vertices;
   libgpu.c `keep_silhouettes_on_pixels()` puts tainted vertices (and those coinciding with them) back on the console's pixel.
   Env MEMORIES_PGXP_TAINT=0 turns it off (EXPERIMENT). `Pgxp_Positions` flag (level 2 active), `Memories_GteAdoptPrecise`
   (shared-vertex drivers re-attach precise values after writing SXY). THIS STEP IS UNMEASURED so far (just built, tests pass).
4. Debug (remove before commit): probe_polygons / MEMORIES_PGXP_PROBE="x,y,r" in libgpu.c; "seams:" log line; scene_measure.py patches.

## Findings (numbers per frame, level 2 unless stated)
- Baseline snap_seams (screen-word pairing): small scene 9,674 precise words, 4,579 snapped (47%), moved mean 1.14 / worst 2.21 px;
  big scene 2,634 snapped (39%). Visible cracks (Celtic Guardian boot/belt, Harpie hair). L1 vs L2 changes 18-21% of pixels, mostly a
  uniform 0.75 px shift (the +0.77 bias; best alignment (3,3) px at 4x).
- draw_id only: snapped 2,917 (30%) / 1,521 (23%); little visual change.
- Disc models mix polygon kinds: ~28-30% of vertex words are shared-vertex polygons, ~70% plain.
- Identity by camera-space coincidence (distance / part scale, in "model units"): true duplicate corners are few (~50 pairs small,
  ~12 big) and <= 0.42 console px apart; neighbouring mesh corners start at ~2 model units (sharp knee in the small scene).
  snap_seams was gluing ~50x too many vertices. Weld at 1.5: 9 / 4 vertices moved, 0.1 px mean.
- BUT gaps are not duplicate corners: interior gap pixels (small / big): snap_seams 39 / 53, draw_id 131 / 28, weld 135 / 44; weld
  tolerance 0..9 gives the same ~135 / ~44. snap_seams only hid some by accident.
- Probe of the hair hairline (console 114.7,79.3): the point lies on the shared edge of a drawn triangle and a MISSING triangle slot.
  The missing triangle was culled by the game: culling = NCLIP on the console's ROUNDED vertices; drawing at level 2 uses PRECISE ones.
  A silhouette sliver can be culled rounded but have area precise -> hairline gap (L1 draws rounded, so the culled sliver has no area).
- Making NCLIP follow the precise facing is WRONG: ~680 of ~3,890 triangles/frame (17%) flip culled->drawn, packet buffer (140,000 bytes)
  overflows and the back row of monsters vanishes; gaps 135 -> 1,797 (small).

## Experiments after the first draft of these notes (2026-10-13, late)
- Silhouette taint (vertices of triangles whose rounded vs precise facing disagree stay on console pixels): hair hairline 5 px -> 0, but total gap
  pixels unchanged (135 -> 136 small, 44 -> 40 big), ~30% of frame vertices go back to whole pixels, and a new 81 px blob appeared. REMOVED.
- Zoomed look at the largest remaining gap clusters (evidence sheet 5_remaining_gap_spots.png): they are whole MISSING TRIANGLES (black triangular holes
  in the gold monsters, shattered collar on the robed monster, black slivers between claw fingers), present with snap_seams AND with the weld, absent at L1.
- Selective precise culling (NCLIP returns "front" for a triangle culled rounded but with precise area >= MEMORIES_PGXP_CULL_MIN; Pgxp_Positions):
  min area -> extra triangles per frame (small / big): 1e6 -> 0/0, 8 -> 2/2, 4 -> 13/13, 2 -> 62/52, 1 -> 169/166, 0.5 -> 361/320.
  Gap pixels small: snap_seams 39 | none 135 | 8:135 | 4:135 | 2:190 | 1:200 | 0.5:200. big: snap 53 | all 44 (0.5: 43).
  => giving back culled triangles did NOT reduce the gap metric (it rose slightly in the small scene), although the visual holes look like culled triangles.
  UNRESOLVED CONTRADICTION: either the metric (dark interior pixels at L2 where L1 is solid) does not measure these holes well, the holes come from something
  other than the game's culling, or the given-back triangles have wrong shading/texture. Full precise culling (no minimum) vanishes the back-row monsters
  (packet buffer GRAPHICS_PACKET_BUFFER_SIZE 140,000 bytes/half is nearly full on a full field: ~3,100 triangles used of ~3,500).
- Current code state: weld_corners + draw ids + view/scale in PgxpVertex + selective precise culling (gte.c, env MEMORIES_PGXP_CULL_MIN default 2.0); taint removed.

## Next (in order)
1. Measure the silhouette-taint step: gap_score with MEMORIES_PGXP_TAINT=1 vs 0 on both scenes, look at Harpie hair / Celtic crops.
   Done when gaps <= snap_seams' 39 / 53 and no missing monsters; if not, the taint idea is wrong -> rethink (conservative expansion?).
2. Check big/other scenes (full duel with HD mod, 4x) and that level 1 / off are byte-identical to master (smoke hashes).
3. Remove debug + experiment overrides; keep tests; decide what scene_measure/gap_score belong in the repo (dev-tools notes P1 #7 A/B runner).
4. Imported/HD models (upstream feat/model-replace, shared-vertex polygons): test with the weld/taint on a branch merging it.
5. Offer level 2 in the menu only after gaps and wobble (blind A/B) pass and a second OS/GPU run; then PR.

## Cleanup before any commit
Remove: MEMORIES_PGXP_WELD / MEMORIES_PGXP_TAINT overrides, probe_polygons, "seams:" log naming, settings.c clamp (until the menu change),
untracked scene_measure.py patches (or upstream them). Check git status for WIP_NOTES.md (do not commit).

## Review round + decisive experiments (2026-10-13, night)
An independent no-context reviewer read these notes (its main points: gap metric fragile/blind; the NCLIP override might not reach drivers that reload SXY with
ldsxy3; try colour-exact hole mask, depth-off/nearest-sample toggles, a DuckStation-style threshold on the ROUNDED area; per-site counters). Results of checking them:
- NCLIP sites (counter, per frame, small scene): 6,031 NCLIPs, 5,879 (97.5%) have all three precise vertices; 3,953 culled rounded, 3,899 (98.6%) of those precise.
  => the override DOES reach (almost) every culling site; the "ldsxy3 clears precise" worry is refuted.
- Colour-exact black metric (L2 pixel exactly black where L1 is visible and not near its edge): small: snap 179 | weld, no give-back 405 | give-back min 2: 950 |
  min 1: 1,184 | min 0.5: 1,173; big flat ~169. => triangles given back are drawn BLACK/dark (genuinely edge-on/back-facing, lit from behind): give-back makes it worse.
- Perspective off (MEMORIES_PGXP_NOPERSP): 405 vs 403 black pixels: perspective UVs are not the cause.
- Probe at holes A and B: a DRAWN triangle covers each hole point (words 3831 / 5508), winding consistent with its neighbours (so not culled, not inverted).
- Magenta clear (MEMORIES_PGXP_CLEAR_MAGENTA: what no polygon paints shows magenta; evidence sheet 6_holes_in_magenta.png): at L2, 599 px (small scene) where L1 is drawn
  and not near its edge are NEVER PAINTED (triangular blobs in the gold monsters, speckled collar of the robed monster, claw fingers). The hair hairline is different:
  a thin sliver that IS drawn black.
=> Two defect classes: (1) never-painted triangles (the majority; present with snap_seams and weld, absent at L1; probe says the triangle exists in the packet list
   and covers the point) -> the OpenGL pass (gl_picture.c polygon()/triangle()/fragment shader) is not painting triangles that exist at level 2: next step is to log in
   triangle() for the probe point (early returns, push_vertices failure, find_precise mismatch, texel 0 discard/clamp); (2) drawn-black slivers (hair) = edge-on
   triangles; the game culls the true back faces and that is right.
Experiment switches still in the tree (remove before commit): MEMORIES_PGXP_WELD, MEMORIES_PGXP_CULL_MIN (selective precise culling), MEMORIES_PGXP_NOPERSP,
MEMORIES_PGXP_CLEAR_MAGENTA, MEMORIES_PGXP_PROBE, nclipsites/culling/seams logs.

## Hole anatomy (frame 40, small scene, level 2; evidence sheets 6_holes_in_magenta.png, 8_hole_classes.png)
Method: GL clear colour magenta (MEMORIES_PGXP_CLEAR_MAGENTA), cyan for transparent texel (MEMORIES_PGXP_CYAN_TRANSPARENT), every GL triangle logged (MEMORIES_PGXP_PROBE=160,120,1000, "gltri:" lines
incl. the 320 px buffer offset: subtract it; pixel X has its centre at console X/4), rasterised in numpy, compared with level 1 (solid = drawn and 2 px from its edge, L2 shifted back 3 px).
894 hole pixels where L1 is solid: 627 never painted (magenta) + 64 transparent texel (cyan, texel word 0) + (the rest drawn black).
Of the 627 never painted: 116 inside a submitted triangle's precise outline (covered but unpainted: unexplained), 324 thin cracks (within 0.5 console px of a drawn triangle),
187 "missing region" = pixels > 0.5 px from ANY drawn triangle: in the picture these are thin long spikes (the dark dragon's wing tips along the top edge), i.e. sub-pixel-wide
triangles that no pixel centre lands in at precise positions (level 1's rounding fattens them to a row of pixels).
- The rounded outlines of the same submitted triangles cover 436 of the 627 pixels, the precise ones only 116: precise positions tile worse than rounded ones.
- Giving culled triangles back does not help: unpainted 627 -> 619 (min area 2); 3,175 at 0.5 (monsters dropped by the packet budget). Culling is NOT the cause of these holes.
- Perspective UVs not involved (affine: same count). Weld/identity not involved (tolerance 0..9 same).
- Concentrations: the green robed monster's collar, the teal monster's head/shoulders, claw fingers, wing spikes; thin cracks mostly at part boundaries / small dense triangles.
IDEA (untested): conservative coverage for level 2 triangles = expand each precise triangle's edges outward by ~0.15-0.35 console px (bounded miter), the analogue of what rounding
did at level 1; measure holes and silhouette growth. Alternative: a minimum pixel width for sliver triangles. The covered-but-unpainted 116 px need their own look (GL fill-rule on exact edges?).

## Conservative coverage (2026-10-14) and the current state of the tree
gl_picture.c `grow_triangle()`: at level 2 (Settings_Get(SET_PGXP) >= 2, all three vertices precise) each triangle's edges move outward by PGXP_GROW = 0.2 console px (bounded miter,
corners keep their own attributes; MEMORIES_PGXP_GROW overrides, MEMORIES_PGXP_GROW_EXTRAP=1 extrapolates attributes: no better). Level 1 is byte-identical to before (0 px changed, small scene 4x).
Unpainted pixels where level 1 is solid (frame 40, small scene): 627 (no growth) -> 309 (0.15) -> 210 (0.25) -> 186 (0.35) -> 183 (0.5); 254 at the default 0.2 with all other defaults.
Cost: painted pixels outside level 1's outline +744 (0.15) / +1,683 (0.25) of ~1,200; interior exact-black pixels 2,298 -> 2,719 (0.15): fringe/dark edge texels. The dark-interior metric (gap_score.py)
barely moves (135 -> 117 small, 44 -> 35 big): it counts dark drawn pixels, the unpainted count is the one that improves.
Seen on the sheets (evidence 9_*, 10_*, 11_now_*): gold monster forehead hole and shoulder cracks closed at 0.25; Harpie hair/wing cracks closed; robed collar mostly whole but the headdress stays
spiky and a faint crack remains; fringe light pixels around Celtic Guardian's cuffs; at 0.15-0.25 a thin dark streak across the floor lower right (a needle triangle level 1 never showed) appeared in the earlier
extrapolating variant. Not explained: 116 pixels covered by a submitted triangle but unpainted; thin spikes (wing tips) remain thinner than level 1.
REMOVED as failed: selective precise culling (NCLIP give-back) + Memories_GteAdoptPrecise + counters; silhouette taint. Tree now: draw ids, view/scale in PgxpVertex, weld_corners, grow_triangle,
settings.c clamp 2 (measurement), probe/gltri logs and env switches (MEMORIES_PGXP_WELD/PROBE/NOPERSP/CLEAR_MAGENTA/CYAN_TRANSPARENT/GROW/GROW_EXTRAP; remove before commit).
C tests pass (pc_pgxp, pc_gte, pc_libgpu). NOT done: full duel at 2x with HD mod, other OS/GPU, imported models, a blind A/B of wobble (M6), packet-budget check on a ten-monster board with level 2 (no extra packets now).

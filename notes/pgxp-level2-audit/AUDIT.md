# PGXP level 2: audit briefing (for an independent reviewer)

Branch `feat/pgxp-level2` (fork d02d02, from upstream/master e74cef21a). **This is a WIP/audit branch, not a PR.** It contains experiments and debug switches on purpose.
Question for you: **is this approach (patching the PS1-packet path to carry precise vertices) the right strategy, or should the 3D model drawing be rewritten
(e.g. an indexed-mesh renderer for HMD models with float transforms), or something else?** Please read, verify against the code, and recommend. You may disagree with every conclusion below.

## Product context
Native PC port ("Recompiled") of Yu-Gi-Oh! Forbidden Memories (PS1). The decompiled game C runs natively; the GTE (PS1 3D coprocessor) is emulated in `src/pc/compat/gte.c`; GPU commands are
collected from the game's ordering tables and replayed through a software GPU and an OpenGL pass (`src/pc/render/gl_picture.c`) at an internal resolution of 1x/2x/4x.
"PGXP" (as in DuckStation) keeps the sub-pixel precision of GTE projections. **Level 1** ("Textures": perspective-correct textures, vertices still at the console's integer positions) is merged upstream (#196).
**Level 2** ("Textures and positions": polygons drawn at precise positions, which removes the wobble of 3D models in motion) was disabled upstream (#83: it opened gaps in small models) and is what this branch tries to deliver.
Hard constraints: the game's logic/state must not change with PGXP (determinism, save states); the game's packet buffer is 140,000 bytes per frame half and is ~90% full on a ten-monster field
(`src/game/graphics_frame.h`; a model that does not fit is dropped whole); mods (C code compiled against the headers) must keep working; Windows/Linux/macOS/Android builds.

## Data path (read these files)
1. `src/pc/compat/gte.c` `rtp()`: computes the GTE result (integer SXY) AND the precise position in double: screen x,y, depth, camera-space view position (row_sums/unit) and the part's matrix scale; calls `Pgxp_Project`.
2. `src/pc/compat/pgxp.c`: tables keyed by screen word (`Pgxp_Project/Find`), by packet address (`Pgxp_StoreAt/FindAt`, filled by the HMD polygon drivers `src/pc/overrides/model_polygon_drivers.c` and by `addPrim`
   in game units via `pgxp_game.h`), and the game's own `gte_stsxy` stores (`Pgxp_Stored`/`AddPrim`). `Pgxp_BeginDraw()` is called per `GsSortUnit` (`src/pc/sdk/libgs_unit.c`): one model draw.
3. `src/pc/sdk/libgpu.c` `DrawOTag`: collects the frame's GP0 words, looks up each word's precise vertex (`frame_precise[]`), `weld_corners()` (this branch), then hands them to the renderer
   (`SoftGpu_SetPrecise` -> recorder arena `OP_PRECISE` -> `gl_picture.c`).
4. `gl_picture.c`: `polygon()` -> `find_precise()` -> `triangle()` (+ `grow_triangle()`, this branch) -> GL vertices; fragment shader emulates PS1 texturing (CLUT, nearest, texel word 0 = transparent, UV bounds clamp), no depth buffer (painter's order from the OT).
5. Culling: the game culls back faces by `NCLIP` on the console's ROUNDED vertices (HMD drivers in `model_polygon_drivers.c`, and `src/game/func_80033DB0.c`, `func_80034830.c`).

## What this branch contains (`git diff upstream/master`)
- draw ids, `PgxpVertex.view/scale/draw`, lookups returning a PgxpVertex; `weld_corners()` (replaces `snap_seams`); `grow_triangle()` (0.2 console px edge growth, level 2 only); tests in `tests/pc/pgxp_test.c`;
  `settings.c` raises the clamp to 2 for measuring; debug: `probe_polygons`, `gltri` logs, env switches `MEMORIES_PGXP_{WELD,PROBE,NOPERSP,CLEAR_MAGENTA,CYAN_TRANSPARENT,GROW,GROW_EXTRAP}`.
- `tools/pc/scene_measure.py` (patched copy of the fork's `dev` tool: deterministic scene, state, capture, diff, `--cards`, `--seams`, `--env`), `notes/pgxp-level2-audit/tools/` (gap_score.py, crop_compare.py), evidence sheets, and the full trail in `WIP_NOTES.md` + `pgxp-level2.md` (copies here).

## Findings with evidence (all numbers per frame unless stated; "small scene" = 10 small monsters, "big" = default big monsters; 4x frames)
1. Original `snap_seams` (pair vertices by rounded screen word) moved 2,917 (47%) / 1,521 (39%) vertices by 1.1 px on average: it destroys most of the precision level 2 exists for.
2. True duplicate corners (one draw, camera-space distance / part-matrix scale <= ~1.5 "model units") are few: ~50 pairs (small) / ~12 (big), <= 0.42 px apart. Weld by that identity moves ~9 vertices 0.1 px. The 3D Monsters mod scales parts to ~0.2-0.3, so thresholds must scale with the part matrix.
3. Holes are not duplicates (weld tolerance 0..9: same count), not perspective UVs (affine: same), and not game culling: giving culled triangles back (NCLIP by precise area) leaves 627 -> 619 unpainted pixels, adds dark
   slivers, and unbounded overflows the packet buffer (monsters vanish). The NCLIP override reaches 97.5% of culling sites (counter), so the "override does not reach drivers" worry is refuted.
4. Hole anatomy (frame 40, small scene, level 2 never painted where level 1 is solid; magenta clear colour + all GL triangles logged + numpy rasterisation): 627 = 324 thin cracks (<= 0.5 px from a drawn triangle) + 187 thin long
   spikes (sub-pixel triangles, e.g. wing tips) + 116 inside a submitted triangle's precise outline yet unpainted (UNEXPLAINED), plus 64 transparent texels. Rounded outlines of the same triangles cover 436 of the 627, precise only 116:
   **precise triangles tile worse than rounded ones; level 1's rounding gave free coverage.**
5. Conservative coverage (grow each precise triangle's edges 0.15/0.25/0.35 px): unpainted 309/210/186 (from 627); silhouette fringe +744/+1,683/+2,676 painted pixels outside level 1's outline; default 0.2 -> 254. Level 1 unchanged (0 px).
6. Level 2 sits 0.75 console px (3 px at 4x) right/down of level 1 (the known +0.77 bias); the "18-21% of pixels changed" between levels is mostly that shift.
7. Visible after all this (see `evidence/11_now_*.png`): gold monster forehead hole closed, Harpie hair/wing cracks closed, robed collar mostly whole; remaining: light fringe at cuffs, spiky headdress, thin spikes thinner than level 1, hair hairline is a drawn-black edge-on triangle.

## Measurement caveats (be sceptical)
Metrics are mine and imperfect: "gap pixels" = dark at L2 where L1 is solid and 3 px from its edge (fragile; an earlier independent review called it blind), "unpainted" = magenta where L1 is solid (needs the experiment switches), L2 frames shifted back by an integer 3 px.
Only two deterministic test scenes, 4x, frames 40/300, one GPU (Intel, GL 4.6, Windows). NOT verified: other OS/GPU, a real duel with the HD mod, 2x, imported models, the wobble itself (blind A/B not done), packet budget on a full ten-monster board with level 2 (no extra packets now),
level 1/off byte-identity on the repo's smoke cases (only the small scene checked).

## Strategic options to evaluate (my own thinking; challenge it)
A. **Keep patching the packet path** (current): weld + conservative growth, explain the 116 covered-but-unpainted pixels, reduce fringe. Pro: small, no game-code changes. Con: every defect class found so far came from the packet path discarding topology
   (rounded cull decision, per-polygon vertex copies, painter's order tuned to integer geometry); fringe is an approximation; fragile to new models (imported/HD meshes).
B. **Indexed-mesh renderer for HMD models**: the HMD model data holds vertex arrays and polygons that INDEX them (plain and shared-vertex types; `model_polygon_drivers.c` documents the records). Intercept at the driver/GsSortUnit level, project each part's vertices ONCE in float
   (own matrices incl. the mod's scaling), cull and light in float, emit a mesh to the GL pass (optionally with a depth buffer instead of painter's order). Pro: exact vertex identity, watertight meshes without heuristics, no rounded-cull mismatch, natural path for HD/imported models
   (`upstream/feat/model-replace` already writes shared-vertex polygons). Con: big; must reproduce the game's lighting, fog, translucency, sort order and texture-window handling bit-exactly at level 1/off, keep packets for the software GPU/states, packet-buffer and mod interactions.
C. **Supersample or pixel-snap instead of geometric precision** (e.g. render 3D at integer positions into a higher-res target, or temporal approaches): cheaper but does not remove wobble the way level 2 does.
D. Ship level 1 only and drop level 2.
Please say which you would choose and why, what you would prototype first (cheapest decisive experiment), and what in my trail is wrong or unverified.

## Review outcome (2026-10-14): keep option A; a GL-pass bug explains the "unexplained" class
Checked against the kept triangle log and magenta capture (`tools/gltri_check.py`), no new run:
- `gl_picture.c` `triangle()` returns when the ROUNDED area is 0, also at level 2: 438 of 3,665 GL triangles per frame (12%, small scene, 4x) are fully
  precise yet never drawn; 160 px are covered only by them and 159 of those are unpainted in the capture.
- 0 mixed-precision triangles per frame (3,659 all precise, 6 none = 2D): the packet path keeps vertex identity, which was option B's main promise.
- The `gltri:` log line is written before that return, and the log's frame counter is one ahead of the capture (capture "frame 40" = log frame 39).
  On the matching frame no unpainted pixel lies more than 0.1 px inside a drawn triangle: the 116 = dropped triangles + on-edge cracks.
- The remaining classes (thin slivers, pieces without shared vertices, edge-on dark slivers, transparent texels, the 0.75 px bias) come from the model data
  at precise positions; an indexed-mesh renderer would inherit them and need the same weld and coverage. Next: fix the area test, re-measure, lower the growth.

## How to reproduce (Windows)
Disc image `game\ygofm-orig-usa.bin` (USA, SLUS-01411; not in git). Build `python tools\pc\build.py --target windows`. Test scenes mod (`mods/test-scenes`, from the fork's `dev` branch) must be linked and built for `scene_measure.py`.
Measurement commands, the C-test recipe (they DO run on Windows) and every number are in `WIP_NOTES.md` (this folder) -> sections "Setup", "Findings", "Hole anatomy", "Conservative coverage".

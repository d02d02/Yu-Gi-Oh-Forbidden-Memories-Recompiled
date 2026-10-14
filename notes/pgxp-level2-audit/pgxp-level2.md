# Precise geometry (PGXP) level 2 — RESUME HERE (rewritten 2026-10-14)

Detailed, current notes with every number and command: `hacking\Yu-Gi-Oh-Forbidden-Memories-Recompiled\WIP_NOTES.md`
(branch `feat/pgxp-level2`, ALL WORK UNCOMMITTED in that working tree: `git diff` shows it). Pictures:
`hacking\shared\yfm-notes\dev-tools\evidence\pgxp-level2\` (sheets 1-11). This file = what to know first.

## Goal and state
Level 2 ("Textures and positions") draws polygons at the vertices' precise positions (removes the wobble of 3D models). Level 1 (Textures) is merged
upstream (#196). Level 2 was disabled upstream (#83: gaps in small monsters) and is still not offered (settings.c `SET_PGXP` max 1; the working tree raises it to 2 for measuring).
Repo: main checkout re-cloned 2026-10-13 at `hacking\Yu-Gi-Oh-Forbidden-Memories-Recompiled` (remotes `upstream` = Unchiga, `origin` = d02d02 fork), branch from
upstream/master e74cef21a. PR #320 (3D Monsters fights/summon/overhead) is in it; its features are OFF by default (Game > Mods > 3D Monsters). The user tested it and likes it.
Verdict now: level 2 is clearly cleaner than the original (unpainted holes 627 -> 254 in the small-monster scene) but NOT ready to offer: fringe, open items below.

## What is in the working tree (all measured; env switches are experiments, remove before commit)
1. `Pgxp_BeginDraw()` per GsSortUnit -> `PgxpVertex.draw`; PgxpVertex also has `view[3]` (camera space before the divide) and `scale` (part matrix size); lookups return a PgxpVertex.
2. libgpu.c `weld_corners()` replaces `snap_seams`: vertices of one draw within 1.5 model units (camera distance / part scale) take the first one's position+depth. (old snap moved ~2,900 vertices/frame by 1.1 px; weld moves ~9 by 0.1 px).
3. gl_picture.c `grow_triangle()`: at level 2 only, each fully precise triangle's edges move out 0.2 console px (PGXP_GROW; corners keep their own attributes). Level 1 byte-identical (0 px changed).
4. Tests: tests/pc/pgxp_test.c updated; `pc_pgxp`, `pc_gte`, `pc_libgpu` pass (CTests DO build/run on Windows: recipe in WIP_NOTES.md, contradicting the older "CI only" note).
5. Debug/experiment (remove): probe_polygons + gltri logs (MEMORIES_PGXP_PROBE="x,y,r"), MEMORIES_PGXP_WELD / NOPERSP / CLEAR_MAGENTA / CYAN_TRANSPARENT / GROW / GROW_EXTRAP, "seams:" log, measurement tool patches.

## Findings (so nothing is retried blindly)
- Holes are NOT duplicate corners (weld tolerance 0..9 -> same count), NOT perspective UVs (affine = same), NOT the game's culling. Giving culled triangles back (precise NCLIP) adds dark slivers
  and, unbounded, overflows the 140,000-byte packet buffer (monsters vanish); the NCLIP override does reach 97.5% of culling sites. Pinning silhouette vertices to pixels (taint) did nothing.
- Hole anatomy (frame 40, small scene, level 2 never painted where level 1 is solid: 627): 324 thin cracks (<= 0.5 px from a drawn triangle), 187 thin long spikes (sub-pixel triangles, e.g. wing tips),
  116 covered by a submitted triangle yet unpainted (UNEXPLAINED), + 64 transparent texels (word 0 discard). Precise outlines tile worse than rounded ones (rounded cover 436 of the 627, precise 116).
- So level 1's rounding gave free coverage; level 2 needs conservative coverage. 0.15/0.25/0.35 px growth: unpainted 309/210/186; fringe +744/+1,683/+2,676 painted pixels outside level 1's outline.
- Remaining visible defects: light fringe at Celtic Guardian's cuffs, robed monster's headdress spiky + faint collar crack, thin spikes still thinner than level 1, hair hairline sliver is a drawn-black edge-on triangle.
- Level 2 sits +0.75 console px (3 px at 4x) right/down of level 1 (the known +0.77 bias, open decision: compare against pixel+0.5?); L1-vs-L2 "% pixels changed" (18-21%) is mostly that shift.

## Review 2026-10-14 (strategy question "rewrite the renderer?"): answer no, a GL-pass bug instead
- `gl_picture.c` `triangle()`: `if (area == 0) return;` tests the ROUNDED area, also at level 2. Small scene, 4x: 438 of 3,665
  GL triangles per frame (12%) are fully precise yet dropped; 160 px are covered only by them, 159 of those unpainted in the
  magenta capture. Fix: at level 2 with all three vertices precise, test the precise area (level 1 unchanged: fx == x there).
- 0 mixed-precision triangles per frame (3,659 all precise, 6 none = 2D): the packet path does not lose vertex identity.
- The `gltri:` line is logged BEFORE that return, and the log's frame counter is one ahead of the capture (capture "frame 40" =
  log frame 39: 179 stray px vs 2,849). On the matching frame no unpainted pixel lies deeper than 0.1 px inside a drawn
  triangle, so the "116 covered-but-unpainted" class = dropped triangles + on-edge cracks. Re-run the hole anatomy after the fix.
- Check: `python -I hacking\shared\tools\gltri_check.py <log with gltri> <L2 magenta ppm> 4` (finds the matching frame itself).

## Tools and how to measure (details in WIP_NOTES.md)
`python tools\pc\scene_measure.py --game tmp\pc\game32 [--out DIR --cards 58,62,41,59,39,3,2,4,7,97] [--seams] [--env K=V] state|capture --pgxp N --scale S [--frame F] out.ppm|diff|controls`
(patched copy of origin/dev's, untracked; needs mods/test-scenes linked: `hacking\shared\link.ps1 -Worktree <repo> -Code test-scenes`; states die with every rebuild; no other memories-pc may hold the link).
`hacking\shared\tools\gap_score.py`, `crop_compare.py`. Magenta clear colour + cyan transparent texel (env switches) classify holes; GL triangles logged with a 320 px buffer offset.
Reviewer (independent, no-context) report was folded in: metric fragile, colour-exact masks are better, NCLIP reach checked (fine), DuckStation "culling correction" idea tested (does not help here).

## Pitfalls
- Another session (automated-testing) runs memories-pc.exe from this build folder: link "Permission denied" -> retry after ~15 s; never kill games by name, only by Path. PowerShell: `"${var}:"`, no bash heredocs.
- The folder-cleanup session removes new Desktop folders: keep evidence under `shared\yfm-notes\dev-tools\evidence\`. Notes dir `~\.claude\shared\yfm-notes` is a junction to `hacking\shared\yfm-notes`.
- User wants: small increments, a before/after picture each step (saved as files + shown), honest numbers incl. what was NOT verified, no destructive actions without asking.

## Next (ranked)
1. Wobble A/B (blind, camera pan, level 1 vs 2 with the current defaults): is the wobble removal visible enough to justify the fringe? (progress notes M6; needs a frame-range dump.)
2. Real full duel at 2x/4x with the HD mod (assets-hd v0.3.0 via `shared\mods-data`), packet budget on a ten-monster board, level 1/off byte-identical on the smoke cases.
3. Reduce fringe (grow only where a hole would otherwise appear; or 0.15), explain the 116 covered-but-unpainted pixels (GL fill rule? shader discard?), thin spikes.
4. Imported/HD models (`upstream/feat/model-replace`, shared-vertex polygons, unmerged): test with weld + coverage. Second OS/GPU run. Then clean up (remove experiments), decide scene_measure/gap_score placement, menu Off/Textures/Textures+positions, PR.

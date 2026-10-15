# Native models: how it works and how it was built (for the next developer or LLM)

Read [native-models.md](native-models.md) first for the mod-facing description (manifest, settings). This file explains the
machinery, the asset pipeline, the test method, the traps and what is still open. Everything here was built on branch
`feat/battle-events-log` (from `feat/hd-model-bls`, from upstream master) between 2026-10-14 and 2026-10-16. Tools are in
[`tools/hd-models/`](../tools/hd-models/README.md).

## 1. What it is, in one paragraph

The game draws a monster in the arena battle from PS1 packets (25-30 rigid parts, 1198 triangles for Black Luster Soldier). With the
OpenGL picture on at Internal 2x or more, a monster whose model id has a *native model* is instead drawn from a modern mesh (hundreds of
thousands of triangles, 4-weight skinned, its OWN skeleton and animation clips, base colour + normal + metal/roughness maps). The game's logic
is untouched: the original model still runs out of sight (the camera, sound, effects and hit logic read its joints), the native model is
placed from the original's root, and plays its own clip chosen from the game's animation row and clock.

## 2. Data flow (follow the code in this order)

1. **Capture (game thread).** `Model_UpdateScene` -> `func_800540B4(slot)` (src/game/func_800540B4.c) draws one slot. Under `#ifdef MEMORIES_PC` it
   calls `NativeModel_BeginSlot(model)`, `NativeModel_Part(part)` per part (reads the GTE matrices the game just set), `NativeModel_SlotInfo(&info)`,
   then `NativeModel_Link(ot, NativeModel_EndSlot())` which links a one-word marker packet (GP0 command 0, a no-op for every GPU) at the nearest OT
   entry. While the GL pass can draw (`NativeModel_GlReady`) the slot's own PS1 packets are built but not linked (`NativeModel_Suppress`).
   Code: `src/pc/render/native_model.c/.h`.
2. **Replay (render thread).** `DrawOTag` -> `NativeModel_Take` -> the SoftGpu recorder carries the frame's `NativeDraw`s (OP_NATIVE) -> `gl_picture.c`
   `native_draw(id)` runs when the marker comes by in the ordered primitive stream. The GL pass cannot read game memory: everything the director needs
   is copied into `NativeDraw`/`NativeSlotInfo` (disc animation row/clock/length/speed, body root matrix `field_D1C->workm`, world-to-screen matrix
   `D_800FE148` (NOT `GsWSMATRIX`: not a pinned symbol), scale, tint, lights).
3. **Draw.** `native_draw` -> for an HDM4 mesh (`mesh->bones != 0`): `native_director` picks clip + time, `native_skin_pose` samples/cross-fades/forward-kinematics
   on the CPU and uploads one small float texture, the vertex shader skins and projects, the fragment shader lights. The model is drawn into a private
   multisampled framebuffer (4x MSAA, one shared depth buffer per frame) and composited over the picture at the marker (so it is always over PS1
   opponents/effects sorted behind it; only native-vs-native depth is right).

## 3. Model formats (the loader accepts all; only HDM4 is the current path)

* HDM1/2: the disc model's own parts re-meshed (per-part vertices, game rotations pose it); HDM3: + a joint table (own joint positions, game rotations
  retargeted by forward kinematics in `native_retarget`); both are CPU/GPU "part posed" paths kept as the reference (`MEMORIES_NATIVE_CPU=1`).
* **HDM4 (own skeleton + clips)**, little endian, 4-byte words:
  `"HDM4", nverts, nindices, nbones, tex_w, tex_h, nclips, flags` (flags bit0 normal map, bit1 metal(B)/roughness(G) map);
  bones: `nbones x 16 words` = `i32 parent, f32 ibm[12] (3x4 row major, disc-space model -> bone), 3 pad`;
  vertices: `nverts x 13 words` = `f32 pos[3], nrm[3], uv[2], u32 joints (4 x u8), f32 weights[4]`; indices `u32`;
  base texture `RGBA8`; then per flag `u32 w, u32 h, RGBA8`; clips: `12 words` (`char name[32], u32 nframes, f32 fps, 2 pad`) then
  `nframes x nbones x 7 f32` = local translation `t[3]` + rotation `q[4]` (xyzw) per bone, baked at 30 fps in DISC space. Max 128 bones, 16 clips.
* Written by `tools/hd-models/rigged_to_hdm4.py`; parsed by `parse_hdm4` (native_model.c); documented in the converter's docstring.

## 4. The coordinate and placement facts that cost the most time

* **Disc units and axes.** The disc model's space is y-down; the converter maps glTF (y up, metres) with `FLIP = diag(1,-1,-1)`, scale 100 units per metre (`SCALE
  = 0.01`) and a fit factor so the model's hip-to-ankle length equals Black Luster Soldier's (`s_fit`), so the game's camera/effects/shadow volume still make sense.
* **THE TRAP: the disc's part coordinates (`Hmd.world()`, `tb`) include the root's world position** (BLS hips = (0,-300,575) = `field_D1C->workm.t`). The native
  model must have its hips at the ORIGIN of its own space; the game's root matrix carries the position: `view = WS_rot * (root_rot * v / 4096 + root_tr) / 4096 + WS_tr`
  (GTE convention `v' = R v / 4096 + TR`). Putting the hips at `tb[1]` placed the model half a body too high.
* The lunge translation of the attack is on the root (`field_D1C->workm.t`: z 575 -> -240 in row 3), not on the pelvis; clips are made in place (the pelvis' horizontal travel is
  stripped in the converter) and the root provides motion, facing and scale (`field_DB0`).
* Lights: no need to decode `flat_lights`. For any used part: view-space light direction i = `unit(LS rot) x (light matrix row i)/4096`; colours = the light colour matrix; ambient =
  the GTE background colour `bk`; tint = the slot's polygon template colour (0x80 = neutral; the hit flash scales it).

## 5. Director (disc state -> clip)

`native_director` (gl_picture.c): disc row (`info.anim_index`) -> clip name: rows 0,1,4,7 `Sword_Idle`, 2 `Idle_Loop`, 3 `Sword_Attack`, 5 `Hit_Chest`, 6 `Death01`
(Quaternius Universal Animation Library names; another asset needs its own table). Phase = `anim_frame` (12.4 fixed point clock) / (16 x row length). The attack row is
time-warped piecewise so the clip's strike lands on the game's contact frames: disc frames {0,25,30,61,95,150} -> clip frames {0,8,11,22,30,46} (the game's contact window opens at
disc frame 29, closes at 61, second contact at 95; the clip's hand-speed peak is at frame 11). Sounds, effects and camera cuts are keyed to the disc frames, so a clip may not change the
row's length; it can only be warped inside it. Row changes cross-fade the local pose over `NATIVE_FADE` (6) game frames (state per slot, in `native_skin_pose`).
`MEMORIES_NATIVE_CLIP=<name>` plays one clip on a free clock (ignores the game).

## 6. Skinning and shading details

* One `RGBA32F` texture, 4 texels wide: rows 0-127 = bone `j`'s 3x4 matrix `(root view) x (bone world) x (inverse bind)` (texels 0-2, `.w` = translation); row 128 =
  (screen offset x/y, H, scale), (tint rgb, lit flag), (ambient rgb), (ambient lift, light gain); row 129 = three light directions in view space; row 130 = the light colour matrix rows.
  Upload by `glTexSubImage2D` per draw; the mesh is a static VBO + EBO.
* Plain shader: Lambert with the game's lights (`rgb` per vertex). PBR-lite shader (when the file has both maps): per-pixel normal from the normal map through a cotangent frame built
  from `dFdx/dFdy` of view position and uv (no stored tangents); green flipped by default (glTF green = up in the image, our v runs down); the game's three lights + Blinn-Phong
  highlights (width from roughness G, colour from metalness B) + a cheap metal "environment" term (without it metal armour was much darker than the plain path: no diffuse, too few lights).
  `MEMORIES_NATIVE_NOPBR=1` falls back to the plain shader.
* Measured: 279,407 triangles, 4x MSAA, 2048x1024 picture, Intel Iris Xe: 1.6-3.5 ms per frame GPU (`MEMORIES_NATIVE_TIME=1`); the arena runs at 30 fps.

## 7. The arena camera (why close shots needed pushing out)

The arena camera is a `GsRVIEW2` (`D_800F56F0`: eye `vpx..vpz`, look-at `vrx..vrz`) rewritten each frame by `func_80051A48` (scripted keyframes tracking the original models' body centres `field_DD0`).
Measured (BLS vs model 191): the opening orbit 1800 units out, every close shot of the attack 460-660: framed for 1198-triangle models, too tight for big ones.
`Model_SetArenaView` (src/game/model_scene_states.c) replaces BOTH `GsSetRefView2` calls in `Model_UpdateScene` with a view copy whose eye is moved along its line of sight
(`d' = near - (near - d) * keep`, then `* scale`); the game's own `D_800F56F0` is never modified (its scripted moves read and write it). **Both calls must use it**: the stage is drawn
between them, and changing only the second one shrank the models against a fixed arena. Only active while a native model is loaded. The same hook is where a custom camera shot
(for example at the coup de grace) would go: key it to the defender's row/clock.

## 8. The asset pipeline (an AI-made angel on the Quaternius mannequin's clips, as it was done)

1. Rigged source: Quaternius Universal Animation Library (`UAL1_Standard.glb`, CC0: mannequin + 43 clips, UE-style bones). The mesh to dress it with: a Tripo-generated angel
   (no rig, licence unknown: private test only).
2. `blender/angel_on_mannequin_weights.py` (run with `blender -b --python`; flags `--rigid --align`): fits the angel to the mannequin's size, transfers weights by nearest surface from a posed
   mannequin proxy, makes wings/swords RIGID (vertices far from the body, grouped by connectivity, 100% one bone), aligns swords to the arms, adds `wing_a/b_l/r` bones that follow the arms,
   deletes triangles that join different rigid classes ("bridge triangles": the root cause of every stretched slab in earlier attempts), saves a .blend.
3. `blender/angel_swords_and_islands.py` (env `BASE`, `OUTBLEND`; run on the `--align` .blend): reassembles the right sword (its hilt had been moved to the pelvis by the tabard rule: rigid transform fitted
   by Kabsch between the "rigid" and "align" blends, whose vertex indices match), carries both swords upright in the Sword_Idle pose, deletes floating islands (<= 600 faces, the left sword's loose shard).
4. `blender/export_rigged_glb.py` (env `OUTGLB`): strips constraints/animation, exports a skinned glb (JPEG textures).
5. `rigged_to_hdm4.py MODEL.glb OUT.hdm --card 364 --clips-from UAL1_Standard.glb [--clips a,b|all] [--height 0.75] [--no-pbr]`: FK/skin conversion described above; the wing bones (no constraints in glTF)
   get the arm's rotation beyond its parent at 80% in world axes (`--wing-follow`); normal and metal/roughness maps are written when their texCoord is 0 (or 1 equal to 0).
6. Drop the .hdm in a mod folder with a `mod.json` (`native_models`), see native-models.md.
Debug aids: `blender/debug_island_colours.py` (colour the mesh islands by role), `debug_zoom_views.py`, `debug_sword_fragments.py`.

## 9. How to test (and what NOT to trust)

* **Rigkit/software screenshots never show the GL pass** (they are the software picture): use the game's own window capture. `MEMORIES_WINDOW_SHOT=<frame>` (or `<first>-<last>`) with
  `MEMORIES_SCREENSHOT_DIR` writes `glReadPixels` of the window; `MEMORIES_FPS=-1` makes every game frame present so a shot lands on exactly the requested frame. Compare runs only with
  identical `--start/--every/--frames` (the step-to-frame mapping depends on the shot schedule).
* **Saved states are tied to the exact build.** After ANY rebuild an old `attack.state` hangs the game at 100% CPU right after loading (looks like a hang in new code; it is not). Recreate it:
  `attack_window_gpu.py OUT --exe <exe> --frames 0 --start 0` (it plays to the attack and saves `OUT/attack.state`).
* `watch_attack.py STATEDIR --native X.hdm [--env K=V]` replays the saved attack in a real window at 100% speed. The control channel steps unthrottled, so the script paces itself (60 vblanks/s).
* `play-bls.ps1` starts the BLS test duel (needs the Test scenes mod linked in the checkout and a rebuild); add `-Attack 0` so the game's own arena attack plays.
* Never kill games by image name; use PIDs of your own private copy (a running exe in your build folder locks your own link).
* **Game-unit code (src/game) must not call libc/libm** (`sqrtf`, `getenv`, `atof`): each adds an `outside_resident_image` stub (the build line "N outside_resident_image stubs" goes up from 12) and crashed the replay. Put such code in `src/pc/render` and call it.
* Open every picture before claiming anything; a visual bug that survives two fixes has a basic cause (debug the data first: the bridge triangles).

## 10. Decisions and why

* Own skeleton + clips (Option A) over retargeting the game's rotations onto a foreign skeleton: the retarget needed per-model fitting and kept producing artefacts (limb lengths, sword/wing rules); a clean rig with its own clips needs none.
* Vertex-shader skinning with matrices in a texture (CPU only samples clips): GLES/GL3 guarantee few uniforms; the CPU path is kept for HDM1-3.
* Do not skip the original model's draw: logic/camera/sound/effects read its joints and centre (`field_DD0`, `field_DC8`); only its packets are not linked.
* Camera changes are applied to a copy of the view, never to the game's state.

## 11. Open items

* Custom camera at the coup de grace (defender's second hit / destroyed row): feasible in `Model_SetArenaView`, keyed to the defender slot's row and clock; slow motion is not (one game clock for logic, sound, effects).
* Effects are anchored to the hidden original model's joints, not the new model's bones (no visible mismatch in the BLS-vs-191 fight: the visible effects are on the defender); re-anchoring needs the new pose on the game thread.
* Tint-flash mask per part (the hit flash is a whole-body tint now); guard/defence rows; a second monster; GLES/macOS check; fm_editor `compat.py` does not know API 17; the angel's licence (the asset must not be shared).
* The game's real "3D Monsters" option crash (user report, needs their crash-*.txt) is unrelated and unreproduced.

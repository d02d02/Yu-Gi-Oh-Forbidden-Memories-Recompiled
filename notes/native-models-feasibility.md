# Native models: what is doable, the per-category procedure, and the studio it implies

Status: written 2026-10-23. A feasibility assessment plus a design brief. **Nothing here is built.** It rests on
`notes/native-models-fit-problem.md` (what exists and the unconfirmed failure hypotheses) and on the code as read, not on new captures.
Steps and knobs marked *(new)* do not exist today.

## 1. Verdict

"Any glb in, it looks and moves fantastic, with no human" is not reachable. The engine plays baked clips on a skeleton, on a disc-owned
clock, with one uniform scale. Quality is decided by the asset (rig, rest pose, weights, clips) and by a few judgements (size, which clip is
which act, where the strike lands).

What is reachable: a **deterministic, staged procedure** per category of monster. Every stage has an automatic default, a report that says
pass/warn/fail, and a fixed set of knobs. The user walks the stages in order and the result is reproducible from one recipe file.

| Category | Plug and play | Honest expectation |
|---|---|---|
| C1 humanoid, standard skeleton | yes, near automatic | good |
| C2 humanoid, custom skeleton or extras (cape, hair, weapon) | guided | good, extras need work |
| C3 humanoid, no rig (AI or sculpted mesh) | guided, needs an auto-rig | ok, hands, props and capes are fixed by hand |
| C4 quadruped or beast, authored clips | guided | decent |
| C5 winged creature, dragon | guided | decent, wings and tails are only as good as the clips |
| C6 legless: serpent, ghost, floating orb | guided | decent |
| C7 rigid multi-part: robot, machine, no skin | guided | good if the parts are separate nodes |
| C8 static mesh, no animation, any shape | limited | rigid motion only, looks like a moving statue |

Not possible in this engine, whatever the studio does: IK, physics, cloth, hair or tail dynamics at runtime (they must be baked into the
clip offline); retargeting between unrelated skeletons; non-uniform scale; changing a disc row's length; more than 128 bones, 16 clips, 4
influences per vertex or one texture set per model.

## 2. The stages (common to every category)

Each stage has: **inputs**, **automatic default**, **check (pass/warn/fail)**, **knobs**, **exit gate**. A stage can be re-entered; the
recipe (section 4) records every choice, so the whole run is replayable.

### S0 Intake and triage
- Inputs: a `.glb`/`.gltf` (a `.blend` or `.fbx` goes through Blender first, a button *(new)*), author and licence text.
- Auto: read nodes, meshes, skins, animations, materials; classify (C1-C8) from skeleton shape and names: humanoid profile match,
  limb count, wing-like chains, no skin, no animations. Show the class with a confidence and let the user override.
- Check: file loads; at least one mesh; licence field not empty (stored in the package, `--author`, `--license`).
- Knobs: category, licence/author/source URL, which skin if there are several, which meshes to include or drop (LOD copies, helpers,
  collision proxies), card id(s).
- Gate: category chosen.

### S1 Mesh and skin audit
- Auto measurements: triangle and vertex count; units and up axis (y up expected); bounding box; bone count (max 128); influences per vertex
  (max 4 kept); count of vertices with zero weight, unnormalised weight, or weight on a bone that has no effect; flipped normals; degenerate
  triangles; scale of the node tree (an armature scaled 100 or 0.01 is common); non-uniform scale on nodes.
- **Bind pose versus rest pose** *(new)*: this is the check the angel would have failed. For a rigged asset, pose the mesh with frame 0 of
  every clip and measure how far the skinned mesh moves from the bind mesh with no animation applied (it should be near zero for the idle's
  first frame in a normal asset). Report the worst vertices by region (arm, leg, hand).
- Knobs: fix axes/units, drop bones, merge lightest bones into parents down to the limit (today this is hand-made in Blender: `export_dragon_blend.py`),
  weight smoothing, normalise, limit to 4, delete stray parts, mirror.
- Gate: no fail. A warn needs the user's acknowledgement.

### S2 Rig
- Cases: use the rig as is (C1, C4-C7); map a custom humanoid to the humanoid profile by name and by position (C2) *(new profile editor)*;
  produce a rig (C3, C8) *(new, external auto-rig)*; none needed for rigid parts (C7).
- Knobs: root bone (the body root the game places: pelvis for a biped), the humanoid bone map (hips, spine, head, arms, hands, legs, feet),
  weapon/hand attachment bone, which bones are "extras" that ride their parent (cape, hair), which bones may be cut, `--follow BONE=SOURCE`
  (a bone copies another's turn at a fraction), foot joints (for ground contact) or "none".
- Check: every bone has a parent chain to the root; the map covers the required humanoid bones; no bone with reversed scale; extras carry
  weights.
- Gate: root chosen, map complete (humanoid) or "non-humanoid" confirmed.

### S3 Materials and textures
- Auto: pack all materials into one atlas (max 2048 a side), keep normal and metal/roughness maps, report UV overlap and repeats.
- Check: UVs beyond four repeats (clamped by the engine), alpha below half (cut), vertex colours (not drawn), emissive (not drawn *(confirm)*),
  textures bigger than needed, a material that would be lost (the dragon's Blender-Internal materials were dropped).
- Knobs: atlas size, per-material texture override (replace a texture by a file), alpha cutoff, two-sided, tint, normal strength, roughness
  and metal override, double-sided cards for wings and capes.
- Gate: atlas builds, previews textured.

### S4 Size and placement
- Auto by class *(new)*: C1/C2/C3 fit to the standard monster: height 373 game units, root (hips) 159 above the soles, origin on the body's
  vertical axis. C4-C6 fit the largest horizontal extent to the card footprint (`--extent`, exists), root = pelvis or body centre, origin on the
  centre of the support area (feet, belly), not the lowest vertex. C6 floats: a ground offset instead of foot contact. C7 as C1 using the main
  body part. Show the **ghost silhouette of the disc's Black Luster Soldier** and the card footprint grid in the viewport.
- Check: fits the card footprint; head clears the arena camera; does not overlap the neighbour monster at its offset; lowest point versus the
  ground in the idle pose.
- Knobs: `--height` / `--extent` / `--scale`, `--root-height`, `--origin-height`, `--root`, `--no-center`; in `model.json`: `scale` (percent about the
  soles, integers only), `offset`. Per card: yes. Uniform scale only.
- Gate: fits footprint, no clipping with the neighbour in the field and arena camera previews.

### S5 Clips: inventory, mapping, retarget, synthesis
- Inventory: list the source clips with length, frame rate, loop closure (first-to-last pose difference), root drift, largest joint speed,
  bounding box per clip.
- The game needs these acts: idle (rows 0, 1), enter (2), attack (3, and 4 with the second guardian star), hit (5), destroyed (6), win (7),
  guard (8). Fallbacks today: guard/destroyed play the hit clip, the rest the idle.
- Mapping (auto by name, then by motion): which source clip plays each act.
- Sources for a missing act:
  1. a clip from the asset;
  2. **retargeted clip from a library** (UAL for humanoids) *(new retarget with rest-pose correction and bone map; today `--clips-from` needs identical rest poses)*;
  3. **procedural clip** *(new)* built on the root and a few joints: hit = recoil along the facing and back; destroyed = collapse (fall, sink,
     tip, fade by scale); guard = brace (crouch/flare); win = bob/raise; attack = anticipation, lunge to the strike point, recovery;
  4. author it in Blender and import it.
- Knobs per act: source clip, in/out trim, speed, ease, loop on/off, **loop closure** (blend the last frames to the first), mirror, root-motion
  policy (remove x/z travel: default; keep y), foot lock, additive layer (e.g. add a head turn), crossfade length (6 frames today).
- Check: loop closure under a threshold for the loops; no pop; root drift near zero; no bone stretch beyond a threshold; clip count at most 16.
- Gate: every act has a source; loops close.

### S6 Timing against the disc
The disc row supplies the clock; the native clip is stretched once over the row (the only exception today is the strike warp).
- Needs ground truth *(new, measured from the disc)*: the length of every act's row, per monster class, and where the disc's own hit lands.
  Only BLS's attack is measured today.
- Auto: pick strike frames from the fastest hand/weapon joint (max 4). This is wrong for locomotion clips and for non-hand strikes (a bite, a tail).
- Knobs: **time map per act** *(new)*: a list of (clip frame, row phase) points, piecewise linear, so anticipation, strike and recovery land where
  the disc's effect, hit and damage happen; strike frames chosen by hand or by the joint to track (jaw, tail tip, claw); hold frame at the end;
  per-act speed limit with a warning when the stretch factor goes outside a range (fast and jittery below it, slow above it).
- Check: the stretch factor per act; the strike lands within a tolerance of the disc's contact frame (for 3D Monsters on the field); no clip
  restart pop on the idle loop.
- Gate: strike frame set, stretch factors in range.

### S7 Look
- Knobs: `ambient`, `light_gain`, rim/outline if any exists *(confirm)*, field and arena camera `shots` (framing, height, distance), per-model
  tint. Compare against the disc's BLS under the same light.
- Gate: frames in the arena and field camera shots; not clipped by the near plane.

### S8 In-context validation
- Run the real engine on the recipe: Library view (turntable), field attack, arena attack, each act in turn, enter and destroyed. Output a
  contact sheet and a video; pass/fail from the checks above plus the user's eye.
- Gate: all acts seen, no gate in S1-S7 open.

### S9 Package
- Outputs `mods/<name>/models/<name>/model.hdm`, `base.png` (+ `normal.png`, `metal_roughness.png`), `model.json`, `mod.json` `native_models`
  entry, author/licence/source in the package. Run `native_check` (0 errors). Same recipe produces byte-identical output.

## 3. Procedure per category

Each list is the order to walk the stages, with what is typical for that category and the usual trap. "Auto" means the default is expected to
be accepted without change.

### C1 Humanoid, standard skeleton (Mixamo, Quaternius, VRM, UE mannequin, Rigify)
1. S0 profile detected. 2. S1 expect pass; check bind versus rest (A-pose versus T-pose is common and fine when the mesh matches the rig).
3. S2 auto map. 4. S3 auto. 5. S4 auto, 373/159. 6. S5 auto-fill every act from the library clips by retarget, or from the asset's own;
review attack and hit. 7. S6 library strike frames are known per library clip (no guessing). 8. S7, S8, S9.
Trap: extra props (a sword in the hand) in a library clip that expects another prop; a different foot length makes sliding.

### C2 Humanoid, custom skeleton or extras
As C1 with S2 manual: map the custom bones, mark cape/hair/wing bones as extras (ride the parent, or `--follow`). Trap: extras have no clips of
their own, so they stay rigid or copy another bone. The studio shows the extra bones' result in the preview of every act, and the user decides
"rigid", "follow a bone at a fraction", or "bake a simulation in Blender, then import the clip".

### C3 Humanoid, no rig
1. S0 mesh only. 2. S1 check the mesh is in an A- or T-pose (the pose decides everything). If not, S1 offers "re-pose" *(new, Blender button)* or rejects.
3. S2 auto-rig *(new, external: Rigify, UniRig or Mixamo upload; this is the only step that leaves the tool)*; result is verified as C1/C2.
4. Weight check *(new)*: highlight weights on the wrong side (a hand pulling a hip). Fix in Blender, return.
5. Continue as C1. Trap: the angel failed here: a raised arm and sword on a rig that rests another way. The S1 bind-pose check turns that
from "looks wrong in game" into "fail in S1" with the region named.

### C4 Quadruped or beast with authored clips
1. S2 root = pelvis (or the spine centre), no humanoid map. Foot joints: the four feet, or none. 2. S4 `--extent` fit to the footprint;
origin on the support-area centre. 3. S5 map by name and motion: idle, walk/run (for enter), attack, hit, death; missing acts are procedural
(recoil, collapse). 4. S6 strike joint = jaw or front paw, set by hand. Trap: locomotion clips as attack (the dragon's `Run_New`): the studio
warns "this clip travels, it is not an attack" from root drift and cycle shape.

### C5 Winged creature, dragon
As C4, plus: wings. Auto-bone-merge may stiffen the membrane (the dragon lost 16 bones): S1 shows which bones were merged and the weight
that moved. The fit uses the extent (wingspan about twice the height): choose "wings folded in the idle" as the fit pose *(new knob)* so the model
does not exceed the footprint at rest and spreads only while attacking. Flying: ground offset and a hover bob instead of foot contact.
Breath or tail strike: the strike joint is the head or the tail tip. Effect anchors (see section 5) are missing.

### C6 Legless: serpent, ghost, floating
S2 root = body centre. S4 floating: an explicit ground offset, no foot lock. S5 the idle is a slow sway; hit/destroyed procedural (recoil,
dissolve by scale). Trap: the centring heuristic (mesh middle seen from above) is arbitrary here; the studio shows the origin marker and the
user drags it.

### C7 Rigid multi-part: robots, machines, no skin
No skin; each part is a node. The converter makes one bone per part (exists: "unskinned meshes ride the bone above them"). S5 clips are node
animation, or procedural. Trap: parts that share one mesh cannot move separately; the studio lists "meshes with more than one logical part".

### C8 Static mesh, no animation
S2 a single root bone (or none). S5 everything procedural: idle = bob and slow turn, enter = rise or slide in, attack = lunge, hit = recoil and
flash, destroyed = tip or sink, win = rise and spin, guard = squash. Expect a moving statue; the studio says so up front and offers
nothing beyond rigid motion. It can be improved only by rigging the mesh (back to C3/C4).

## 4. The studio: a 3D editor as an add-on to the FM Editor

Makes sense, and the staging above is what makes it deterministic: each tab is a stage, each tab shows only that stage's checks and knobs, a stage
turns green when its gate passes. Design points:

1. **The viewport is the real engine.** The FM Editor is Tk (`tools/pc/fm_editor`), which cannot render the game's shader, skinning, lights and
   cameras faithfully. The studio should drive a headless/windowed engine "viewer" process over the existing control channel (`yfm_control`
   already exists), and show its window or frames inside or beside the editor. What you see is then what the game does. A three.js viewport
   would be a second renderer that will disagree with the game; if used, it is for stages S1-S3 only. **Decided (user, 2026-10-23): the real engine.**
2. **One recipe file** (`recipe.json`) holds every choice from S0 to S9: classification, bone map, size, mappings, time maps, look, licence.
   The converter takes `glb + recipe -> package`, byte-identical each time. Today the choices are spread over CLI flags, `model.json` and
   Blender scripts. The recipe is the first thing to build, with or without a GUI, because the CLI and the studio both read it.
3. **Non-destructive and undoable.** The source glb is never edited; the studio edits the recipe. Mesh and weight fixes are a round trip with
   Blender (button: open in Blender, return, re-audit); the studio is **not** a modeller or a weight painter, by decision.
4. **Overlays that make judgement cheap:** ghost silhouette of BLS; card footprint grid and neighbour monster; origin and root markers;
   bone display with the map colours; bind-versus-rest overlay; weight heat map per bone; per-act timeline showing the disc row's length, the
   stretch factor, the strike point and the disc's contact frame; foot-contact and drift graph; side-by-side with the disc's BLS playing the same act.
5. **Presets by category** fill all defaults; "Auto" fills a stage, "Next" is disabled while a stage has a fail.
6. **Reports are exportable** as a contact sheet, a short video and a text report (pass/warn/fail and measured numbers), which is also the
   acceptance record for a model.

## 5. What is missing from the plan (beyond the stages)

Things the stages assume that do not exist or are not decided:

1. **Disc ground truth** (S6): row lengths per act and per monster class, the disc's contact frame per attack, the camera shots per act. Only
   BLS's attack is measured. Without it the time map is guesswork.
2. **Effect and attachment anchors**: the disc's sparks, sword trails, breath and hit flashes are positioned by the disc model, not by the
   native one. A dragon's breath should leave the mouth; today it leaves the BLS's sword position. Needs an engine-side design (anchor bones in
   `model.json` that code mods can read); it conflicts with D3/D4 ("game logic untouched") only if the game consumes it, so keep it additive.
3. **Retargeting and procedural-clip engine** (S5). Library work in Python on the converter side.
4. **Auto-rig** integration and its quality bar (C3).
5. **Recipe schema and versioning**, with migration when the schema changes.
6. **A renderer that runs without the disc** for CI and for the studio's early stages. Today verification needs `MEMORIES_DISC` and a GL window.
7. **Test corpus and golden captures**: 5 to 8 diverse glbs (one per category) with expected reports; regression on every converter change.
8. **Budgets and cost reports**: triangles, texture memory, the 512 MB native-model total on a 32-bit game, load time.
9. **Multi-card use and variants**: one model on several cards; a texture or palette variant of the same model.
10. **Cross-platform**: Windows is the working machine; the laptop and macOS need the same flow (Tk, Blender paths, GL).
11. **Scope line for Blender**: which fixes the studio promises and which it hands off. Without it the studio grows into a modeller.
12. **Failure copy**: every fail and warn needs plain words and a suggested knob ("arm weights on the hip: re-pose in Blender, or choose
    another rig").
13. **Provenance**: author, licence, source URL, and the licence's attribution requirement captured at S0, written into the package and shown in
    the Library.
14. **Human-effort promise per category** (minutes expected), measured on the corpus, so the README does not overpromise.

## 6. Order of work (proposal, not started)

1. Recipe schema and a converter that reads it (no GUI). 2. Audit report (S1, S5 inventory) with the bind-versus-rest check, run on the
dragon, the angel and the mannequin to confirm or refute the fit-problem hypotheses. 3. Disc ground truth for S6. 4. Retarget + procedural acts.
5. Time maps and the class-based placement. 6. Corpus and regression. 7. Studio shell in the FM Editor driving the engine viewer.
8. Auto-rig and anchors last.

Acceptance for the whole effort: each category's corpus asset ends with a report with no open fail, a contact sheet and a video in the arena and
field cameras, reproduced from `recipe.json` alone.

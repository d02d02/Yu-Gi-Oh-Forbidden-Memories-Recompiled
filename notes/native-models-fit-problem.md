# Native models: how a model gets into the game, and why the dragon and the angel look wrong

Briefing for someone (a person or a stronger model) who has to propose the approach. It describes what exists, what it can and cannot do,
and the gap between a good model file and what the game does with it. It proposes nothing. Status: written 2026-10-23 from reading the
notes and the code; the failure causes in section 4 are **hypotheses, not yet confirmed on captures**.

## 1. Goal and current state

Replace a monster's battle model (the disc's PS1 model, drawn from packets) by a modern rigged glTF model, as a data mod: no C, no disc
edit, no Blender script. Objectives and decisions: `progress.md`. Mod side: `notes/native-models.md`. Internals: `notes/native-models-dev.md`.
How to add a model (draft): `notes/adding-a-model.md`.

| Model | Source | Result today |
|---|---|---|
| Humanoid (the mannequin: Quaternius Universal Animation Library rig and clips) | rigged, humanoid, clips from the same library | works well (M1-M7 PASS) |
| Black Dragon (3DHaupt.com, `Dragon_Baked_Actions.blend`) | non-humanoid, 136 bones cut to 120, 4 actions (`Idel_New`, `Fly_New`, `Run_New`, `Walk_New`), no attack/hit/death | moves awkwardly, messy movement |
| Fallen angel (AI-made mesh dressed on the mannequin rig by weight transfer) | humanoid mesh with raised arm and sword, no rig of its own | leg, sword and hand deformed |

## 2. The pipeline

```
disc model --hmd_export.py--> glTF            (reference only: rigid parts, one joint per part, y up, 100 game units = 1 unit)

rigged .glb --new_native_mod.py--> native_convert.py --> mods/x/
                                       models/x/model.hdm    mesh + skeleton + clips baked at 30 fps (HDM4)
                                       base.png (+ normal.png, metal_roughness.png)
                                       model.json            clip per act, strike frames, scale, offset, look, shots
                                   + mod.json  "native_models": [{"cards":[364], "package":"models/x/model.json"}]
```

Files: `tools/hd-models/` (`native_convert.py`, `new_native_mod.py`, `native_check.py`, `native_spec.py`, `make_dragon.py`,
`blender/*.py`), engine `src/pc/render/native_*.c` (`native_anim.c` = animation, `native_registry.c` = loading and `model.json`,
`native_model.c` = slots and instances, `native_cinematic.c` = camera shots), `gl_picture.c` (the OpenGL draw).

### Extraction

The only extraction is `hmd_export.py CARD OUT`: a disc monster to glTF. It is not part of the injection path. It was used to measure the
disc's Black Luster Soldier (BLS, card 364): 373 game units from soles to top, hips (the body root the game places) 159 above the soles.
Those two numbers are the "standard monster" the converter fits every model to.

### Injection (what the converter does)

- Reads the skin with the most joints (max 128), 4 influences per vertex (the strongest kept), unskinned meshes ride the bone above them.
- Packs all materials into one texture atlas (max 2048 a side); normal and metal/roughness maps follow.
- Moves the root bone to the origin, flips glTF's y-up to the game's y-down, scales (`--height`, default 373; or `--extent`, `--scale`,
  `--root-height`), puts the origin on the body's vertical axis `--origin-height` (159) above the lowest vertex ("the soles").
- Bakes every clip at 30 fps in glTF space with the node tree (linear/step/cubic keys), then converts each frame to bone-local
  translation + quaternion in game space. Root horizontal travel is removed (the game moves the monster); the idle pose's feet (or, with
  no foot joints, the middle of the mesh seen from above in the bind pose) are put on the origin.
- Guesses which clip plays each act by name; picks strike frames from the fastest hand/weapon joint's speed peaks (max 4).
- `--follow BONE=SOURCE` makes a bone copy another's turn at a fraction (used for the angel's wings; the only constraint-like feature).

### Runtime (what the game does with it)

The disc's own model keeps running out of sight and supplies position, animation row, row length and clock. The native model never decides
when anything happens.

1. The disc animation row selects an act: rows 0 and 1 idle, 2 enter, 3 attack (4 with the second guardian star), 5 hit, 6 destroyed,
   7 win, 8 guard.
2. The act selects a clip (`model.json` `clips`; else a default name; else guard/destroyed play the hit's, the rest the idle's).
3. Time inside the clip = row phase (`anim_frame / (16 * anim_length)`, clamped 0..1) x clip length. **The clip is stretched once over the
   row.** Only the attack is warped: when a code mod knows the contact frame (3D Monsters on the field), the first strike frame lands on it
   (piecewise linear); the arena uses a hard-coded warp measured for BLS's `Sword_Attack` only.
4. Local pose of each bone is interpolated between baked frames; when the row changes, the last pose is cross-faded in over 6 frames.
5. Forward kinematics, then per bone: root view matrix x world x inverse bind, sent to the shader (4-bone skinning).
6. `model.json` `scale` (percent, about the soles) and `offset` are applied to the root view; lighting uses the game's lights plus
   `ambient` and `light_gain`.

The game's own timing, sounds, effects, save states and logic are untouched by design (decisions D3, D4 in `progress.md`).

## 3. Modification tools and their limits

| Level | Tool | Can change | Cannot change |
|---|---|---|---|
| Data, no reconvert | `model.json`, the PNGs | clip per act, strike frames, `scale`, `offset`, light, arena/field camera `shots`, textures | mesh, weights, clip content |
| Converter flags | `--height`, `--extent`, `--scale`, `--origin-height`, `--root`, `--no-center`, `--keep-root-motion`, `--follow`, `--clips`, `--clips-from`, `--rig` | size, origin, which clips, borrowed clips (bones matched by name) | a wrong rig, wrong weights, a bind pose that disagrees with the rig |
| Blender scripts | `angel_on_mannequin_weights.py`, `angel_swords_and_islands.py`, `export_rigged_glb.py`, `export_dragon_blend.py`, `common.py` | re-skin onto the mannequin, carry props, export a glb, cut bones | they are written for those two assets; nothing is generic |

Hard limits of the format and engine:

- 128 bones, 16 clips, 4 influences per vertex, one texture set per model, 512 MB of native models in all (32-bit game).
- Clips are baked: no IK, constraints, physics, cloth, hair or tail dynamics at runtime. Anything secondary must already be in the clip.
- No retargeting between different skeletons. `--clips-from` matches by bone name and assumes the same rest pose.
- Uniform scale only. Colours per vertex are not drawn. UVs beyond four repeats are clamped. Alpha below half is cut.
- The game's JSON reader takes whole numbers only.
- Timing belongs to the disc row: the native clip cannot lengthen or shorten a row.

## 4. The structural gap: a good model versus what the game does with it

A model can be excellent (triangle count, textures, rig, animations) and still look wrong, because the game assumes a standard humanoid
monster driven by disc timing, and the converter forces any model into that shape. Candidate causes, to confirm on captures:

1. **Rest-pose contract (angel).** Skinning is correct only if the mesh's bind pose is the rig's rest pose. The angel asset is modelled
   with a raised arm and sword; the mannequin rig rests in another pose. Weight transfer between the two puts arm, hand, sword and leg
   geometry on the wrong bones, and every clip then deforms that mismatch. Nothing in the pipeline detects it. The notes say "expect to
   hand-fix capes, wings, swords and hair (the sword arm is still wrong)" and "needs `scale 65`".
2. **Time contract (dragon).** One clip stretched once over the row:
   - `Run_New` is a locomotion cycle, mapped to attack: one slow stride over about 150 frames, not an attack.
   - `Idel_New` is a short loop, mapped to idle, hit, guard and destroyed: stretched over rows of different lengths (fast and jittery in
     short rows). Row 0/1 loops, so the clip restarts each time; a clip whose last frame differs from its first pops.
   - Strike frames `[13, 48, 71, 146]` in the test mod came from hand speed on a run cycle: meaningless; the warp uses only the first.
   - The asset has no attack, hit or death animation at all.
3. **Rig contract (dragon).** 136 to 120 bones by merging the lightest leaf bones' weights into their parents: tail tips and wing
   fingers lose independent motion, the membrane is stiffer than authored. Bone names are not humanoid, so no profile helps.
4. **Size and placement contract.** The origin is forced to 159 above the lowest vertex and the size is one number (`--height` or
   `--extent`). On a dragon the lowest vertex is a claw or the tail, the pelvis is not 159 above it, a wingspan of about twice the
   height makes the model wider than the card, and the arena and field cameras are tuned for a 373-tall humanoid. Size is a declaration;
   nothing checks that the result frames, fits the card footprint or collides with the neighbour.
5. **Root motion and centring.** Root travel is removed from x and z only (y kept). The centring is arbitrary for a creature without feet
   (the middle of the bind-pose mesh seen from above), applied to every frame of every clip.
6. **Detection.** The converter and `native_check.py` report counts, names and sizes, not quality. Nothing measures bind-pose agreement,
   weight sanity, loop closure, root drift, bone stretch or per-clip bounding box. Problems are found only by running the game with the
   disc and looking.

## 5. Evidence to collect before deciding

- Bind pose of the dragon and the angel against the rig's rest pose (picture and numbers).
- For each clip of each model: length, first-to-last pose difference, root drift, largest joint speed, bounding box against the card.
- A turntable or pose sheet of frame 0 and a mid frame of each act, rendered without the game.
- The captures already in `tmp/agent/` (dragon: `tmp/agent/dragon/`, field and arena sheets in `tmp/agent/fx/`).

## 6. Fixed constraints for any plan

- `src/game` only under `#ifdef MEMORIES_PC`, no libc/libm there; engine code in `src/pc`; `make match` unaffected.
- Code-mod surface: new exports only, structs have `size`, never change exported layout.
- Decisions D1-D6 (`progress.md`): converter to validated package, no new C lib; pure-C animation sampling; native size not fed back
  to the game; arena cinematics do not change length; model key = card id; HDM4 only.
- Models are third-party fan-made with a proper licence; author and licence go into the package.
- Verification here needs the disc (`MEMORIES_DISC`) and a real GL window; laptop results come on the `test-results` branch.

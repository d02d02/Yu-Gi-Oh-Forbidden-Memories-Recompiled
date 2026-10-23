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

## 2-3. Pipeline, runtime and tool limits (moved, not repeated here)

Converter flags, package, acts and limits: `native-models.md`. Capture, replay, director, coordinates, shaders, camera, angel scripts: `native-models-dev.md`.
Tool levels and hard limits (128 bones, 16 clips, 4 influences, one texture set, 512 MB, baked clips with no IK/physics/cloth, no retargeting,
uniform scale only, vertex colours not drawn, UVs past four repeats clamped, alpha below half cut, whole numbers in JSON, timing owned by the disc row)
and the verdict per category: `native-models-feasibility.md` sec. 1-2. The one fact this file still needs: the runtime stretches ONE clip once over the
disc row (phase = `anim_frame / (16 * anim_length)`); only the attack is warped (first strike frame onto the contact frame, or BLS's measured table).

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
